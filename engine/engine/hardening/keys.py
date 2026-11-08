"""Committee key material.

Deterministic where the algorithm allows it: ML-KEM and ML-DSA keys are derived from COMMITTEE_KEY
(or, in development, from PSEUDONYM_KEY with a domain label) so the published key id survives a
restart. RSA has no seeded keygen in `cryptography`, so the credential issuer key is generated once
per process -- and the API says so, because a credential signed by a key that no longer exists is
worth nothing and we will not pretend otherwise.
"""
from __future__ import annotations
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.asymmetric import rsa, x25519

ISSUER_KEY_BITS = 2048


def seed(label: str, length: int = 32) -> bytes:
    """HKDF-ish expansion of the committee secret under a label, so one secret yields many keys
    and no two mechanisms share key material."""
    base = (os.environ.get("COMMITTEE_KEY") or "").strip()
    derived_from = "COMMITTEE_KEY"
    if not base:
        base = (os.environ.get("PSEUDONYM_KEY") or "").strip()
        derived_from = "PSEUDONYM_KEY"
    if not base:
        raise RuntimeError(
            "neither COMMITTEE_KEY nor PSEUDONYM_KEY is set; the hardening layer refuses to "
            "invent key material"
        )
    out = b""
    counter = 0
    prk = hmac.new(b"sealed-signals/committee/v1", base.encode("utf-8"), hashlib.sha256).digest()
    while len(out) < length:
        counter += 1
        out += hmac.new(prk, label.encode("utf-8") + bytes([counter]), hashlib.sha512).digest()
    _seed_source.append(derived_from)
    return out[:length]


_seed_source: list[str] = []


def seed_source() -> str:
    return _seed_source[-1] if _seed_source else "unused"


def x25519_from_seed(label: str) -> x25519.X25519PrivateKey:
    return x25519.X25519PrivateKey.from_private_bytes(seed(label, 32))


def new_issuer_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=ISSUER_KEY_BITS)


def key_id(public_bytes: bytes) -> str:
    """A short, stable name for a public key: the first 16 hex of its SHA-256."""
    return hashlib.sha256(public_bytes).hexdigest()[:16]
