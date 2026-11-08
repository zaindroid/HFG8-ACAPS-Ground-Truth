"""Mechanism 1 and 6: the identity registry, encrypted at rest, with every read logged.

Shape, exactly: one AES-256-GCM data key encrypts the expert-id to identity map. That data key is
wrapped by a hybrid KEM -- ML-KEM-768 *and* X25519, both shared secrets fed into one HKDF -- so the
wrap is no weaker than X25519 today and still stands against an adversary who stored the ciphertext
and later has a quantum computer.

What this does NOT do: hide identities from an administrator who holds the committee key. That
administrator is this process. The registry refuses to hand out a record without a `who` and a
`why`, and every read lands in the access log, which is the actual control.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import flags, keys

SUITE = "ML-KEM-768 + X25519 hybrid, AES-256-GCM"
FALLBACK_SUITE = "AES-256-GCM, data key beside the ciphertext (FF_PQ off)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hkdf(material: bytes, info: bytes, length: int = 32) -> bytes:
    prk = hmac.new(b"sealed-signals/hybrid/v1", material, hashlib.sha256).digest()
    out, counter, previous = b"", 0, b""
    while len(out) < length:
        counter += 1
        previous = hmac.new(prk, previous + info + bytes([counter]), hashlib.sha256).digest()
        out += previous
    return out[:length]


def _wrap_key(ek: bytes) -> tuple[bytes, dict]:
    """Encapsulate to the committee hybrid public key. Returns the wrapping key and its envelope."""
    from kyber_py.ml_kem import ML_KEM_768

    pq_secret, pq_ciphertext = ML_KEM_768.encaps(ek)
    committee_x = keys.x25519_from_seed("registry/x25519").public_key()
    ephemeral = x25519.X25519PrivateKey.generate()
    classical_secret = ephemeral.exchange(committee_x)
    kek = _hkdf(pq_secret + classical_secret, b"registry/kek")
    envelope = {
        "kem_ciphertext": base64.b64encode(pq_ciphertext).decode(),
        "x25519_ephemeral": base64.b64encode(ephemeral.public_key().public_bytes_raw()).decode(),
    }
    return kek, envelope


def _unwrap_key(dk: bytes, envelope: dict) -> bytes:
    from kyber_py.ml_kem import ML_KEM_768

    pq_secret = ML_KEM_768.decaps(dk, base64.b64decode(envelope["kem_ciphertext"]))
    peer = x25519.X25519PublicKey.from_public_bytes(base64.b64decode(envelope["x25519_ephemeral"]))
    classical_secret = keys.x25519_from_seed("registry/x25519").exchange(peer)
    return _hkdf(pq_secret + classical_secret, b"registry/kek")


@dataclass
class AccessEntry:
    who: str
    why: str
    expert_id: str
    at: str

    def as_dict(self) -> dict:
        return {"who": self.who, "why": self.why, "expert_id": self.expert_id, "at": self.at}


@dataclass
class Registry:
    """Holds the identity map only as ciphertext. There is no plaintext dict on this object."""

    blob: str | None = None
    nonce: str | None = None
    wrap: dict = field(default_factory=dict)
    wrapped_data_key: str | None = None
    suite: str = SUITE
    access_log: list[AccessEntry] = field(default_factory=list)
    key_holder: str = "committee service (this process, in the pilot)"
    _ek: bytes | None = None
    _dk: bytes | None = None

    # -- keys ------------------------------------------------------------------
    def _committee_kem_keys(self) -> tuple[bytes, bytes]:
        if self._ek is None or self._dk is None:
            from kyber_py.ml_kem import ML_KEM_768

            self._ek, self._dk = ML_KEM_768.key_derive(keys.seed("registry/ml-kem", 64))
        return self._ek, self._dk

    @property
    def key_id(self) -> str:
        ek, _ = self._committee_kem_keys()
        return keys.key_id(ek)

    # -- storage ---------------------------------------------------------------
    def _read_map(self) -> dict[str, dict]:
        if self.blob is None:
            return {}
        if self.wrap:
            _, dk = self._committee_kem_keys()
            data_key = AESGCM(_unwrap_key(dk, self.wrap)).decrypt(
                base64.b64decode(self.wrap["wrap_nonce"]),
                base64.b64decode(self.wrapped_data_key or ""),
                b"registry/data-key",
            )
        else:
            data_key = base64.b64decode(self.wrapped_data_key or "")
        raw = AESGCM(data_key).decrypt(
            base64.b64decode(self.nonce or ""), base64.b64decode(self.blob), b"registry/v1"
        )
        return json.loads(raw.decode("utf-8"))

    def _write_map(self, records: dict[str, dict]) -> None:
        data_key = os.urandom(32)
        nonce = os.urandom(12)
        self.blob = base64.b64encode(
            AESGCM(data_key).encrypt(
                nonce, json.dumps(records, sort_keys=True).encode("utf-8"), b"registry/v1"
            )
        ).decode()
        self.nonce = base64.b64encode(nonce).decode()
        if flags.enabled("FF_PQ"):
            ek, _ = self._committee_kem_keys()
            kek, envelope = _wrap_key(ek)
            wrap_nonce = os.urandom(12)
            self.wrapped_data_key = base64.b64encode(
                AESGCM(kek).encrypt(wrap_nonce, data_key, b"registry/data-key")
            ).decode()
            self.wrap = {**envelope, "wrap_nonce": base64.b64encode(wrap_nonce).decode()}
            self.suite = SUITE
        else:
            # Flag off: the data key sits beside the ciphertext. A real fallback, labelled as one.
            self.wrapped_data_key = base64.b64encode(data_key).decode()
            self.wrap = {}
            self.suite = FALLBACK_SUITE

    # -- api -------------------------------------------------------------------
    def put(self, expert_id: str, identity: dict) -> None:
        records = self._read_map()
        records[expert_id] = identity
        self._write_map(records)

    def read(self, expert_id: str, who: str, why: str) -> dict | None:
        """A read needs a name and a reason. Both go in the log before the record comes back."""
        who, why = (who or "").strip(), (why or "").strip()
        if not who or not why:
            raise ValueError("a registry read needs who and why; an unattributed read is refused")
        self.access_log.append(AccessEntry(who=who, why=why, expert_id=expert_id, at=_now()))
        return self._read_map().get(expert_id)

    def count(self) -> int:
        """How many identities are held. Not a read of any record, so it is not logged."""
        return len(self._read_map())

    def status(self) -> dict:
        encrypted = bool(self.wrap) or (flags.enabled("FF_PQ") and self.blob is None)
        mechanism = flags.mechanism("pq_registry") or {}
        return {
            "encryption": SUITE if encrypted else "off",
            "suite": self.suite,
            "key_id": self.key_id if encrypted else None,
            "key_holder": self.key_holder,
            "key_seed_source": keys.seed_source(),
            "n_identities": self.count(),
            "access_log_count": len(self.access_log),
            "lock_line": (
                f"Identity map encrypted with {SUITE}, key held by the committee."
                if encrypted
                else "FF_PQ is off: the identity map is encrypted with a key stored beside it."
            ),
            "guarantees": mechanism.get("guarantees"),
            "does_not": mechanism.get("does_not"),
        }

    def log(self) -> list[dict]:
        return [entry.as_dict() for entry in self.access_log]

    def reset(self) -> None:
        self.blob = self.nonce = self.wrapped_data_key = None
        self.wrap = {}
        self.access_log.clear()
