"""Mechanism 4: zero-knowledge group membership, Semaphore-v4 shaped.

Read this before quoting it on a slide. Two of the three parts are real and enforced here:

* the group -- one Merkle tree of identity commitments per panel, with a published root;
* the nullifier -- one per (identity, pulse), recorded on use, so a second answer is refused.

The third part, the Groth16 proof that a nullifier belongs to the tree without naming the leaf, is
NOT verified in this build. Verifying a Semaphore proof needs the circuit's verification key and a
BN254 pairing check, and the proof itself has to be generated in the browser; neither exists here.
So `verify` reports `cryptographic_verification: false` and says what it did check, and FF_ZK
ships off. With the flag off nothing accepts a proof at all.

This is the honest version of "built, flagged, default off until stable". It is not stable, and the
reason is written here rather than left for someone to discover on stage.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import flags

CLAIM = "member of panel {panel} answered pulse {pulse}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def identity_commitment(secret: str) -> str:
    """Stand-in for Semaphore's Poseidon commitment. SHA-256 here: the tree is real, the hash is
    not the one the circuit uses, so a proof from a real Semaphore client would not match."""
    return hashlib.sha256(f"sealed-signals/identity/v1:{secret}".encode()).hexdigest()


def nullifier(secret: str, pulse_id: str) -> str:
    return hashlib.sha256(
        f"sealed-signals/nullifier/v1:{secret}:{pulse_id}".encode()
    ).hexdigest()


def group_root(commitments: list[str]) -> str:
    if not commitments:
        return ""
    level = [bytes.fromhex(c) for c in sorted(commitments)]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest()
                 for i in range(0, len(level), 2)]
    return level[0].hex()


@dataclass
class Group:
    panel_id: str
    commitments: list[str] = field(default_factory=list)

    @property
    def root(self) -> str:
        return group_root(self.commitments)

    def as_dict(self) -> dict:
        return {"panel_id": self.panel_id, "root": self.root, "size": len(self.commitments)}


@dataclass
class Membership:
    groups: dict[str, Group] = field(default_factory=dict)
    used_nullifiers: dict[str, dict] = field(default_factory=dict)

    def add_group(self, panel_id: str, commitments: list[str]) -> Group:
        group = Group(panel_id=panel_id, commitments=sorted(set(commitments)))
        self.groups[panel_id] = group
        return group

    def verify(self, proof: dict, pulse_id: str) -> dict:
        """Check what can be checked, record the nullifier, and say plainly what was not checked."""
        mechanism = flags.mechanism("zk_membership") or {}
        if not flags.enabled("FF_ZK"):
            return {"accepted": False, "cryptographic_verification": False,
                    "reason": "FF_ZK is off. No proof is accepted on this build.",
                    "guarantees": mechanism.get("guarantees"),
                    "does_not": mechanism.get("does_not")}

        panel_id = (proof or {}).get("panel_id") or ""
        root = (proof or {}).get("group_root") or ""
        null = (proof or {}).get("nullifier") or ""
        points = (proof or {}).get("points")

        group = self.groups.get(panel_id)
        checks = {
            "group_known": group is not None,
            "root_matches": bool(group) and root == group.root,
            "nullifier_present": bool(null) and len(null) == 64,
            "nullifier_unused": bool(null) and null not in self.used_nullifiers,
            "proof_envelope_well_formed": isinstance(points, (list, tuple)) and len(points) == 8,
        }
        accepted = all(checks.values())
        if accepted:
            self.used_nullifiers[null] = {"pulse_id": pulse_id, "panel_id": panel_id,
                                          "at": _now()}
        return {
            "accepted": accepted,
            "cryptographic_verification": False,
            "checks": checks,
            "claim": CLAIM.format(panel=panel_id or "?", pulse=pulse_id),
            "checked": "the panel group root, the nullifier shape, and that this nullifier has "
                       "not been used before",
            "not_checked": "the Groth16 proof itself. This build has no BN254 pairing check and no "
                           "circuit verification key, so it cannot tell a real proof from a "
                           "well-formed fake. That is why FF_ZK ships off.",
            "guarantees": mechanism.get("guarantees"),
            "does_not": mechanism.get("does_not"),
        }

    def spent(self, null: str) -> dict | None:
        return self.used_nullifiers.get(null)

    def status(self) -> dict:
        mechanism = flags.mechanism("zk_membership") or {}
        return {
            "enabled": flags.enabled("FF_ZK"),
            "scheme": "semaphore-shaped (sha256 tree, per-pulse nullifier)",
            "groups": [group.as_dict() for group in self.groups.values()],
            "n_nullifiers_used": len(self.used_nullifiers),
            "proof_verifier": "not implemented in this build",
            "guarantees": mechanism.get("guarantees"),
            "does_not": mechanism.get("does_not"),
        }

    def reset(self) -> None:
        self.groups.clear()
        self.used_nullifiers.clear()
