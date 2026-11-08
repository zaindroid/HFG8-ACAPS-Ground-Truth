"""End-to-end encryption of the expert's answer, from the expert's browser to this engine.

The answer is encrypted on the expert's device to a per-deployment key pair whose private half only
this process holds, so a CDN, a reverse proxy or a tunnel in between carries a ciphertext it can
neither read nor change without the change being detected.

Key pair. ML-KEM-768 (FIPS 203) and X25519, both derived deterministically from COMMITTEE_KEY via
`keys.seed` under the labels `answers/ml-kem` and `answers/x25519`, so the key id survives a
restart. `GET /api/answer-key` publishes both public keys, the key id and the suite name.

Envelope, built by the client (ui/src/e2e.ts) and opened by `open_body` here:

    {"e2e": {"v": 1, "kid": "<key id>", "kem_ct": b64, "x25519_pub": b64, "nonce": b64, "ct": b64}}

1. ML-KEM-768 encapsulation to the published ML-KEM key gives `kem_ct` and a 32-byte secret ss_kem.
2. A fresh ephemeral X25519 key pair; `x25519_pub` is its public key and ss_x the X25519 shared
   secret with the published X25519 key.
3. key = HKDF-SHA256(ikm = ss_kem || ss_x || x25519_pub || server_x25519_pub, salt = empty,
   info = "sealed-signals/e2e-answer/v1|" + kid, length = 32). Hybrid: the key stands as long as
   either ML-KEM-768 or X25519 does.
4. `ct` = AES-256-GCM(key, nonce = 12 random bytes, plaintext = the UTF-8 JSON answer body,
   AAD = "sealed-signals/e2e/v1|" + route + "|" + token), tag appended. `route` is one of
   ROUTES, so a ciphertext sealed for one expert's link or one route fails on any other.

All base64 is standard with padding. An envelope that does not open -- wrong key id, wrong token,
wrong route, any altered byte -- is refused with 400; a body without `e2e` is used as it is, which
keeps the relay, scripts and older clients working.

What this does not do: hide the answer from the operator of this engine, which decrypts it; protect
an answer on a compromised device or browser; or stop an intermediary that can rewrite the page
itself, or block the key route so the client falls back to a plain body (the card then shows no
encryption line).
"""
from __future__ import annotations
import base64
import binascii
import json
import os
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from . import flags, keys

SUITE = "ML-KEM-768 + X25519, HKDF-SHA256, AES-256-GCM"
VERSION = 1
INFO_LABEL = b"sealed-signals/e2e-answer/v1|"
AAD_LABEL = "sealed-signals/e2e/v1"
ROUTES = {
    "draft": "POST /e/answer",
    "confirm": "POST /e/confirm",
    "correct": "PUT /e/answer",
}
_KEM_CT_BYTES = 1088
_X25519_BYTES = 32
_NONCE_BYTES = 12


class EnvelopeError(ValueError):
    """The envelope did not open. The message is safe to return to the client."""


@lru_cache(maxsize=4)
def _keypair_for(kem_seed: bytes, x_seed: bytes) -> tuple[bytes, bytes, x25519.X25519PrivateKey]:
    from kyber_py.ml_kem import ML_KEM_768

    ek, dk = ML_KEM_768.key_derive(kem_seed)
    return ek, dk, x25519.X25519PrivateKey.from_private_bytes(x_seed)


def _keypair() -> tuple[bytes, bytes, x25519.X25519PrivateKey]:
    # Cached by seed, so a change of COMMITTEE_KEY (tests do this) gives a new key pair.
    return _keypair_for(keys.seed("answers/ml-kem", 64), keys.seed("answers/x25519", 32))


def _x_pub_bytes(private: x25519.X25519PrivateKey) -> bytes:
    return private.public_key().public_bytes_raw()


def key_id() -> str:
    ek, _, x_private = _keypair()
    return keys.key_id(ek + _x_pub_bytes(x_private))


def public_key() -> dict:
    ek, _, x_private = _keypair()
    return {
        "enabled": flags.enabled("FF_E2E"),
        "v": VERSION,
        "kid": keys.key_id(ek + _x_pub_bytes(x_private)),
        "suite": SUITE,
        "ml_kem_768_pub": base64.b64encode(ek).decode(),
        "x25519_pub": base64.b64encode(_x_pub_bytes(x_private)).decode(),
        "aad": f"{AAD_LABEL}|<route>|<token>",
        "routes": dict(ROUTES),
    }


def _aad(token: str, route: str) -> bytes:
    if route not in ROUTES.values():
        raise ValueError(f"unknown route {route!r}")
    return f"{AAD_LABEL}|{route}|{token}".encode("utf-8")


def _derive(ss_kem: bytes, ss_x: bytes, eph_pub: bytes, server_x_pub: bytes, kid: str) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=INFO_LABEL + kid.encode("ascii")).derive(
        ss_kem + ss_x + eph_pub + server_x_pub)


def _b64(field: str, value, expected: int | None = None) -> bytes:
    if not isinstance(value, str):
        raise EnvelopeError(f"e2e.{field} must be a base64 string")
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise EnvelopeError(f"e2e.{field} is not valid base64") from exc
    if expected is not None and len(raw) != expected:
        raise EnvelopeError(f"e2e.{field} must be {expected} bytes")
    return raw


def seal(body: dict, token: str, route: str, published: dict | None = None) -> dict:
    """The client side, in Python: used by the tests and by scripts. The browser does the same in
    ui/src/e2e.ts."""
    from kyber_py.ml_kem import ML_KEM_768

    published = published or public_key()
    ek = base64.b64decode(published["ml_kem_768_pub"])
    server_x_pub = base64.b64decode(published["x25519_pub"])
    ss_kem, kem_ct = ML_KEM_768.encaps(ek)
    ephemeral = x25519.X25519PrivateKey.generate()
    eph_pub = _x_pub_bytes(ephemeral)
    ss_x = ephemeral.exchange(x25519.X25519PublicKey.from_public_bytes(server_x_pub))
    key = _derive(ss_kem, ss_x, eph_pub, server_x_pub, published["kid"])
    nonce = os.urandom(_NONCE_BYTES)
    ct = AESGCM(key).encrypt(nonce, json.dumps(body).encode("utf-8"), _aad(token, route))
    enc = lambda raw: base64.b64encode(raw).decode()  # noqa: E731
    return {"e2e": {"v": VERSION, "kid": published["kid"], "kem_ct": enc(kem_ct),
                    "x25519_pub": enc(eph_pub), "nonce": enc(nonce), "ct": enc(ct)}}


def open_body(body: dict, token: str, route: str) -> dict:
    """Return the answer body: decrypted if it arrived as an envelope, unchanged if it did not.
    Raises EnvelopeError for an envelope that does not open."""
    if not isinstance(body, dict) or "e2e" not in body:
        return body
    if set(body) != {"e2e"}:
        raise EnvelopeError("an encrypted body carries nothing beside e2e")
    sealed = body["e2e"]
    if not isinstance(sealed, dict):
        raise EnvelopeError("e2e must be an object")
    if sealed.get("v") != VERSION:
        raise EnvelopeError(f"e2e.v must be {VERSION}")
    ek, dk, x_private = _keypair()
    server_x_pub = _x_pub_bytes(x_private)
    kid = keys.key_id(ek + server_x_pub)
    if sealed.get("kid") != kid:
        raise EnvelopeError("e2e.kid does not name this engine's answer key; fetch "
                            "/api/answer-key again")
    kem_ct = _b64("kem_ct", sealed.get("kem_ct"), _KEM_CT_BYTES)
    eph_pub = _b64("x25519_pub", sealed.get("x25519_pub"), _X25519_BYTES)
    nonce = _b64("nonce", sealed.get("nonce"), _NONCE_BYTES)
    ct = _b64("ct", sealed.get("ct"))
    from kyber_py.ml_kem import ML_KEM_768

    try:
        # ML-KEM decapsulation never fails: an altered kem_ct yields a different secret
        # (implicit rejection), and the GCM tag check below is what catches it.
        ss_kem = ML_KEM_768.decaps(dk, kem_ct)
        ss_x = x_private.exchange(x25519.X25519PublicKey.from_public_bytes(eph_pub))
        key = _derive(ss_kem, ss_x, eph_pub, server_x_pub, kid)
        plaintext = AESGCM(key).decrypt(nonce, ct, _aad(token, route))
    except Exception as exc:  # InvalidTag, a low-order X25519 point, anything else
        raise EnvelopeError("the encrypted answer did not open: it was altered, or sealed for "
                            "another link or route") from exc
    try:
        opened = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EnvelopeError("the encrypted answer is not JSON") from exc
    if not isinstance(opened, dict):
        raise EnvelopeError("the encrypted answer must be a JSON object")
    return opened
