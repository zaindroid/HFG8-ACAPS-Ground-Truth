"""Feature flags and the exact wording that must accompany every hardening mechanism.

MASTER_PROMPT section 6c: each mechanism is built, flagged, visible in the product, and described
*everywhere* with its "guarantee / does not" sentence from docs/sealed-signals/trust-design.md. The
sentences live here, once, so the API, the UI and the slides cannot drift into a stronger claim.
"""
from __future__ import annotations
import os
from dataclasses import dataclass

DEFAULTS = {
    "FF_PQ": True,       # post-quantum registry encryption and outcome attestations
    "FF_BLIND": True,    # blind-signed single-use credentials
    "FF_ZK": False,      # zero-knowledge group membership: off until stable (see zk.py)
    "FF_ANCHOR": True,   # timestamp anchoring, degrades to "pending"
    # The consent-gated calibration programme (section 6d). Off, and off is the point: it is
    # the only thing here that measures a person, and it does not run until an expert has read
    # the disclosure and said yes.
    "FF_CALIBRATION": False,
}
TRUE = {"1", "true", "yes", "on"}


def enabled(flag: str) -> bool:
    raw = os.environ.get(flag)
    if raw is None or not raw.strip():
        return DEFAULTS[flag]
    return raw.strip().lower() in TRUE


def flags() -> dict[str, bool]:
    return {name: enabled(name) for name in DEFAULTS}


@dataclass(frozen=True)
class Mechanism:
    number: int
    id: str
    name: str
    flag: str | None
    build: str
    shows: str
    guarantees: str
    does_not: str

    def as_dict(self) -> dict:
        return {
            "number": self.number, "id": self.id, "name": self.name, "flag": self.flag,
            "enabled": enabled(self.flag) if self.flag else True,
            "build": self.build, "where_it_shows": self.shows,
            "guarantees": self.guarantees, "does_not": self.does_not,
        }


MECHANISMS = (
    Mechanism(
        1, "pq_registry", "Post-quantum registry encryption", "FF_PQ",
        "ML-KEM-768 for key establishment, hybrid with X25519; AES-256-GCM at rest over the "
        "expert-id to identity map; the key is held by the committee service",
        "Registry page: the lock line",
        "Long-horizon confidentiality of the identity map against harvest-now-decrypt-later",
        "Confidentiality from an administrator with the key; anything about answers",
    ),
    Mechanism(
        2, "pq_attestation", "Post-quantum outcome attestations", "FF_PQ",
        "ML-DSA-65 signs each resolved ledger entry (risk_id, outcome, resolved_at, round "
        "commitment root); the public key is published on the ledger",
        "Ledger row: attested, ML-DSA-65, verify",
        "The outcome record was issued by the committee key and has not been altered since",
        "Truth of the outcome; anything about who answered",
    ),
    Mechanism(
        3, "blind_credentials", "Blind-signed single-use credentials", "FF_BLIND",
        "RSA blind signatures (RFC 9474 RSABSSA-SHA384-PSS-Deterministic): the committee signs a "
        "blinded token per pulse allowance, the expert unblinds it and spends one token per answer; "
        "the server verifies the signature and rejects reuse by nullifier",
        "Expert card under the anonymous mask; committee view: tokens issued and spent, never linked",
        "A vetted panel member answered, unlinkable by the committee to the approval",
        "Protection against timing or network-metadata correlation; re-identification by "
        "distinctive wording",
    ),
    Mechanism(
        4, "zk_membership", "Zero-knowledge group membership", "FF_ZK",
        "Semaphore-v4-shaped group per panel with a per-pulse nullifier. The group root and the "
        "nullifier registry are built and enforced; the Groth16 proof check itself is NOT "
        "implemented in this build, which is why the flag ships off",
        "Round view: the proof line, which says what was and was not checked",
        "Double-answer prevention by nullifier, enforced server-side",
        "Membership without identity -- that needs the proof verifier this build does not have; "
        "reputation portability; not required for the pilot design",
    ),
    Mechanism(
        5, "anchoring", "Timestamp anchoring", "FF_ANCHOR",
        "A daily Merkle root of that day's commitments is submitted to an OpenTimestamps calendar; "
        "the receipt is stored and the status stays pending until the calendar returns a "
        "Bitcoin-confirmed proof",
        "Ledger: anchor status per day; Verify shows the root and the receipt",
        "Independent proof the commitments existed by that time, once the status reads anchored",
        "Anything else; no tokens, no chain logic, no cost. A pending root proves nothing yet",
    ),
    Mechanism(
        6, "access_log", "Registry access log", None,
        "Every read of the identity map is logged with who, when and why",
        "Committee view: access log",
        "Committee access to identities is defined and visible",
        "Prevention of access by an authorised administrator",
    ),
)


def mechanisms() -> list[dict]:
    return [m.as_dict() for m in MECHANISMS]


def mechanism(mechanism_id: str) -> dict | None:
    for m in MECHANISMS:
        if m.id == mechanism_id:
            return m.as_dict()
    return None
