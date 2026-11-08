"""Mechanism 3: blind-signed single-use credentials (RFC 9474 RSABSSA, SHA-384 PSS, zero salt).

The point is unlinkability at *spend* time. The committee knows it approved eight experts and
issued each a batch of tokens. It does not learn which token came back with which answer, because
it only ever saw the blinded form, and the deterministic PSS encoding means the finished signature
is verifiable by any standard RSA-PSS verifier -- including `cryptography` itself, which is what
the tests use. That is the property worth having, and it is the one we claim.

Two issuance paths, and the response says which one ran:

* `blinded`: the client blinds, the server signs blind, the client unblinds. Unlinkable.
* `count`:   a demo convenience. The server performs the client side of the protocol itself, so it
             briefly holds the unblinded token. Marked `unlinkable: false` in the response, because
             a server that has seen the token could have written it down.

Reuse is stopped by nullifier: the token id is recorded on spend, and a second spend is refused.
"""
from __future__ import annotations
import base64
import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from . import flags, keys

SCHEME = "rsa-blind-rfc9474"
FALLBACK_SCHEME = "hmac"
HASH_NAME = "sha384"
PREFIX = "sealed-signals/credential/v1:"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def message_for(token_id: str) -> bytes:
    """What gets signed. Deliberately carries no expert id, no panel, no counter -- anything that
    narrowed the set would undo the blinding."""
    return (PREFIX + token_id).encode("utf-8")


# -- RFC 9474 pieces -----------------------------------------------------------
def _mgf1(seed: bytes, length: int) -> bytes:
    out, counter = b"", 0
    while len(out) < length:
        out += hashlib.new(HASH_NAME, seed + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]


def emsa_pss_encode(message: bytes, embits: int, salt_length: int = 0) -> bytes:
    """EMSA-PSS-ENCODE (RFC 8017 9.1.1) with a zero-length salt, which is what makes
    RSABSSA-SHA384-PSS-Deterministic deterministic. Written out here because the blinding has to
    happen on the encoded integer, and no library exposes that step."""
    digest_size = hashlib.new(HASH_NAME).digest_size
    emlen = (embits + 7) // 8
    if emlen < digest_size + salt_length + 2:
        raise ValueError("key too small for this hash")
    m_hash = hashlib.new(HASH_NAME, message).digest()
    salt = os.urandom(salt_length) if salt_length else b""
    h = hashlib.new(HASH_NAME, b"\x00" * 8 + m_hash + salt).digest()
    db = b"\x00" * (emlen - salt_length - digest_size - 2) + b"\x01" + salt
    masked = bytes(a ^ b for a, b in zip(db, _mgf1(h, emlen - digest_size - 1)))
    spare_bits = 8 * emlen - embits
    masked = bytes([masked[0] & (0xFF >> spare_bits)]) + masked[1:]
    return masked + h + b"\xbc"


def blind(message: bytes, modulus: int, exponent: int) -> tuple[int, int]:
    """Client side. Returns the blinded integer to send and the inverse to keep."""
    size = (modulus.bit_length() + 7) // 8
    encoded = emsa_pss_encode(message, modulus.bit_length() - 1)
    m = int.from_bytes(encoded, "big")
    while True:
        r = int.from_bytes(os.urandom(size), "big") % modulus
        if r < 2:
            continue
        try:
            r_inverse = pow(r, -1, modulus)
        except ValueError:
            continue
        return (m * pow(r, exponent, modulus)) % modulus, r_inverse


def unblind(blind_signature: int, r_inverse: int, modulus: int) -> bytes:
    size = (modulus.bit_length() + 7) // 8
    return ((blind_signature * r_inverse) % modulus).to_bytes(size, "big")


def _linkage_note(batches: list) -> str:
    """Say which path the tokens on this instance actually came from. Printing the unlinkability
    sentence over a set of demo-path tokens would be the exact overclaim this layer is meant to
    avoid."""
    if not batches:
        return "No credentials issued on this instance yet."
    unlinkable = sum(batch.n_issued for batch in batches if batch.unlinkable)
    total = sum(batch.n_issued for batch in batches)
    if unlinkable == total:
        return ("Counts only. No row here maps a spent token to the approval it came from, "
                "because the issuer never saw the token id.")
    if unlinkable == 0:
        return (f"All {total} tokens were issued on the demo path, where the server performed the "
                "blinding itself and so held the token id for an instant. They are single-use; "
                "they are not unlinkable. Tokens blinded by the card are.")
    return (f"{unlinkable} of {total} tokens were blinded by the card and are unlinkable to their "
            f"approval. The other {total - unlinkable} came from the demo path and are not.")


@dataclass
class Batch:
    batch_id: str
    expert_id: str
    panel_id: str
    n_issued: int
    issued_at: str
    scheme: str
    unlinkable: bool

    def as_dict(self) -> dict:
        return {
            "batch_id": self.batch_id, "expert_id": self.expert_id, "panel_id": self.panel_id,
            "n_issued": self.n_issued, "issued_at": self.issued_at, "scheme": self.scheme,
            "unlinkable": self.unlinkable,
        }


@dataclass
class Credentials:
    """Issuance records hold counts and a batch id. Nullifiers hold spends. Nothing joins them."""

    batches: list[Batch] = field(default_factory=list)
    spent: dict[str, dict] = field(default_factory=dict)
    _key: rsa.RSAPrivateKey | None = None

    # -- issuer key ------------------------------------------------------------
    def _issuer(self) -> rsa.RSAPrivateKey:
        if self._key is None:
            self._key = keys.new_issuer_key()
        return self._key

    def public_key(self) -> dict:
        numbers = self._issuer().public_key().public_numbers()
        pem = self._issuer().public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        return {
            "scheme": SCHEME if flags.enabled("FF_BLIND") else FALLBACK_SCHEME,
            "key_id": keys.key_id(pem.encode()),
            "n": hex(numbers.n), "e": numbers.e, "bits": numbers.n.bit_length(),
            "hash": "sha384", "salt_length": 0,
            "public_key_pem": pem,
            "note": "Generated at process start: `cryptography` has no seeded RSA keygen, so a "
                    "restart publishes a new issuer and retires every token signed by the old one.",
        }

    # -- issuance --------------------------------------------------------------
    def issue(self, expert_id: str, panel_id: str, blinded: list[str] | None = None,
              count: int = 0) -> dict:
        key = self._issuer()
        numbers = key.public_key().public_numbers()
        n, e = numbers.n, numbers.e
        d = key.private_numbers().d
        batch_id = f"B-{os.urandom(4).hex()}"

        if not flags.enabled("FF_BLIND"):
            # Fallback: an HMAC token. One-time use still holds; unlinkability does not, because
            # the issuer can recompute every token it ever handed out.
            tokens = []
            for _ in range(max(count, len(blinded or []))):
                token_id = os.urandom(16).hex()
                tag = hashlib.sha256(
                    keys.seed("credential/hmac", 32) + message_for(token_id)
                ).hexdigest()
                tokens.append({"token_id": token_id, "signature": tag})
            record = Batch(batch_id, expert_id, panel_id, len(tokens), _now(),
                           FALLBACK_SCHEME, False)
            self.batches.append(record)
            return {
                **record.as_dict(), "credentials": tokens,
                "note": "FF_BLIND is off. These tokens are single-use but not unlinkable: the "
                        "issuer can recompute them.",
            }

        if blinded:
            signatures = [hex(pow(int(value, 16) % n, d, n)) for value in blinded]
            record = Batch(batch_id, expert_id, panel_id, len(signatures), _now(), SCHEME, True)
            self.batches.append(record)
            return {
                **record.as_dict(),
                "blind_signatures": signatures,
                "note": "Signed blind. Unblind each with the inverse you kept; the server never "
                        "saw the token id.",
            }

        tokens = []
        for _ in range(max(count, 1)):
            token_id = os.urandom(16).hex()
            blinded_value, r_inverse = blind(message_for(token_id), n, e)
            signature = unblind(pow(blinded_value, d, n), r_inverse, n)
            tokens.append({
                "token_id": token_id,
                "signature": base64.b64encode(signature).decode(),
            })
        record = Batch(batch_id, expert_id, panel_id, len(tokens), _now(), SCHEME, False)
        self.batches.append(record)
        return {
            **record.as_dict(), "credentials": tokens,
            "note": "Demo path: the server ran the client side of the blinding, so it held the "
                    "token id for an instant. The signatures are real RFC 9474 signatures; the "
                    "unlinkability claim does not apply to this path. Send `blinded` for that.",
        }

    # -- verification and spending --------------------------------------------
    def verify(self, token_id: str, signature: str) -> bool:
        if not token_id or not signature:
            return False
        if not flags.enabled("FF_BLIND"):
            expected = hashlib.sha256(
                keys.seed("credential/hmac", 32) + message_for(token_id)
            ).hexdigest()
            return signature == expected
        try:
            raw = base64.b64decode(signature)
        except Exception:
            return False
        try:
            self._issuer().public_key().verify(
                raw, message_for(token_id),
                padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=0),
                hashes.SHA384(),
            )
            return True
        except Exception:
            return False

    def spend(self, token_id: str, signature: str, pulse_id: str) -> dict:
        """Returns the spend record. Raises ValueError on a bad signature or a reused token."""
        if not self.verify(token_id, signature):
            raise ValueError("this credential does not carry a valid committee signature")
        if token_id in self.spent:
            previous = self.spent[token_id]
            raise ValueError(
                f"this credential was already spent on {previous['pulse_id']} at {previous['at']}"
            )
        record = {"token_id": token_id, "pulse_id": pulse_id, "at": _now(),
                  "scheme": SCHEME if flags.enabled("FF_BLIND") else FALLBACK_SCHEME}
        self.spent[token_id] = record
        return record

    # -- what the committee may see -------------------------------------------
    def summary(self) -> dict:
        mechanism = flags.mechanism("blind_credentials") or {}
        return {
            "scheme": SCHEME if flags.enabled("FF_BLIND") else FALLBACK_SCHEME,
            "issuer": {k: v for k, v in self.public_key().items()
                       if k in ("key_id", "bits", "hash", "salt_length", "note")},
            "n_batches": len(self.batches),
            "n_issued": sum(batch.n_issued for batch in self.batches),
            "n_spent": len(self.spent),
            "n_unlinkable_issued": sum(b.n_issued for b in self.batches if b.unlinkable),
            "batches": [batch.as_dict() for batch in self.batches],
            "linked": False,
            "linkage_note": _linkage_note(self.batches),
            "guarantees": mechanism.get("guarantees"),
            "does_not": mechanism.get("does_not"),
        }

    def reset(self) -> None:
        self.batches.clear()
        self.spent.clear()
