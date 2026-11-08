"""Mechanism 2: ML-DSA-65 attestations on resolved ledger entries.

What is signed is the *record*, not the truth: risk_id, outcome, resolved_at and the round
commitment root. A valid signature says the committee key issued this record and nobody changed a
byte of it. It says nothing about whether the outcome is correct, and nothing about who answered.

The signing key is derived from COMMITTEE_KEY, so the published key id survives a restart. With
FF_PQ off the fallback is an HMAC tag over the same canonical bytes, labelled `hmac-sha256` -- a
check against accidental corruption, not a signature anyone else can verify.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
from dataclasses import dataclass, field

from . import flags, keys

PQ_SCHEME = "ML-DSA-65"
FALLBACK_SCHEME = "hmac-sha256"


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass
class Attestations:
    by_risk: dict[str, list[dict]] = field(default_factory=dict)
    _vk: bytes | None = None
    _sk: bytes | None = None

    # -- keys ------------------------------------------------------------------
    def _keypair(self) -> tuple[bytes, bytes]:
        if self._vk is None or self._sk is None:
            from dilithium_py.ml_dsa import ML_DSA_65

            self._vk, self._sk = ML_DSA_65.key_derive(keys.seed("attest/ml-dsa", 32))
        return self._vk, self._sk

    @property
    def scheme(self) -> str:
        return PQ_SCHEME if flags.enabled("FF_PQ") else FALLBACK_SCHEME

    def public_key(self) -> dict:
        if not flags.enabled("FF_PQ"):
            return {
                "scheme": FALLBACK_SCHEME,
                "key_id": keys.key_id(keys.seed("attest/hmac", 32)),
                "public_key": None,
                "note": "FF_PQ is off: the tag is an HMAC, so nobody outside this service can "
                        "check it. Turn FF_PQ on for a signature with a published public key.",
            }
        vk, _ = self._keypair()
        return {
            "scheme": PQ_SCHEME,
            "key_id": keys.key_id(vk),
            "public_key": base64.b64encode(vk).decode(),
            "note": "FIPS 204 ML-DSA-65 verification key. Anyone holding it can check an "
                    "attestation without this service.",
        }

    # -- signing ---------------------------------------------------------------
    def attest(self, risk_id: str, outcome: str, resolved_at: str, commitment_root: str) -> dict:
        payload = {
            "risk_id": risk_id, "outcome": outcome, "resolved_at": resolved_at,
            "commitment_root": commitment_root, "v": 1,
        }
        message = canonical(payload)
        if flags.enabled("FF_PQ"):
            from dilithium_py.ml_dsa import ML_DSA_65

            _, sk = self._keypair()
            signature = ML_DSA_65.sign(sk, message, deterministic=True)
            scheme = PQ_SCHEME
        else:
            signature = hmac.new(keys.seed("attest/hmac", 32), message, hashlib.sha256).digest()
            scheme = FALLBACK_SCHEME
        record = {
            **payload,
            "scheme": scheme,
            "signature": base64.b64encode(signature).decode(),
            "key_id": self.public_key()["key_id"],
            "message_sha256": hashlib.sha256(message).hexdigest(),
            "anchor_receipt": None,
            "guarantees": (flags.mechanism("pq_attestation") or {}).get("guarantees"),
            "does_not": (flags.mechanism("pq_attestation") or {}).get("does_not"),
        }
        self.by_risk.setdefault(risk_id.upper(), []).append(record)
        return record

    # -- verifying -------------------------------------------------------------
    def verify(self, record: dict) -> dict:
        payload = {key: record.get(key) for key in
                   ("risk_id", "outcome", "resolved_at", "commitment_root", "v")}
        message = canonical(payload)
        signature = base64.b64decode(record.get("signature") or "")
        scheme = record.get("scheme")
        if scheme == PQ_SCHEME:
            from dilithium_py.ml_dsa import ML_DSA_65

            vk, _ = self._keypair()
            valid = bool(ML_DSA_65.verify(vk, message, signature))
        elif scheme == FALLBACK_SCHEME:
            expected = hmac.new(keys.seed("attest/hmac", 32), message, hashlib.sha256).digest()
            valid = hmac.compare_digest(expected, signature)
        else:
            return {"valid": False, "scheme": scheme,
                    "checked": "nothing: this record carries no scheme we can check"}
        return {
            "valid": valid,
            "scheme": scheme,
            "key_id": record.get("key_id"),
            "checked": f"{scheme} signature over the canonical outcome record "
                       "(risk_id, outcome, resolved_at, commitment_root)",
            "meaning": "The outcome record was issued by the committee key and has not been "
                       "altered since." if valid else
                       "This record does not match the committee signature. Treat it as altered.",
            "does_not": (flags.mechanism("pq_attestation") or {}).get("does_not"),
        }

    def for_risk(self, risk_id: str) -> list[dict]:
        return list(self.by_risk.get(risk_id.upper(), []))

    def latest(self, risk_id: str) -> dict | None:
        found = self.for_risk(risk_id)
        return found[-1] if found else None

    def reset(self) -> None:
        self.by_risk.clear()
