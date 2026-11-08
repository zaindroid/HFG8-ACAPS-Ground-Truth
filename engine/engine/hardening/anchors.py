"""Mechanism 5: timestamp anchoring of the daily commitment root (OpenTimestamps).

One Merkle root per UTC day over that day's answer commitments, submitted to an OpenTimestamps
calendar over plain HTTPS -- the calendar protocol is a POST of 32 raw bytes to /digest, so this
needs no bitcoin library and costs nothing.

The status is honest by construction. A fresh submission is `pending`: the calendar has the digest
but no Bitcoin block contains it yet, so it proves nothing. It becomes `anchored` only when
GET /timestamp/<digest> returns an upgraded proof, which happens after the next block, typically in
tens of minutes to hours. We never print "anchored" off the back of a submission receipt.
"""
from __future__ import annotations
import base64
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import flags

CALENDARS = (
    "https://a.pool.opentimestamps.org",
    "https://b.pool.opentimestamps.org",
)
TIMEOUT_SECONDS = 4.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def merkle_root(leaves: list[str]) -> str:
    """SHA-256 binary Merkle root over the hex commitments, sorted so the root is reproducible.
    An odd node is paired with itself, the common convention; with one leaf the root is that leaf."""
    if not leaves:
        return ""
    level = [bytes.fromhex(leaf) for leaf in sorted(leaves)]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(level[i] + level[i + 1]).digest()
                 for i in range(0, len(level), 2)]
    return level[0].hex()


class Calendar:
    """The OpenTimestamps calendar, over httpx. Swapped for a fake in the tests."""

    def submit(self, digest: bytes) -> tuple[str, bytes] | None:
        import httpx

        for base in CALENDARS:
            try:
                response = httpx.post(f"{base}/digest", content=digest,
                                      headers={"Accept": "application/vnd.opentimestamps.v1"},
                                      timeout=TIMEOUT_SECONDS)
                if response.status_code == 200 and response.content:
                    return base, response.content
            except Exception:
                continue
        return None

    def upgrade(self, digest: bytes) -> tuple[str, bytes] | None:
        import httpx

        for base in CALENDARS:
            try:
                response = httpx.get(f"{base}/timestamp/{digest.hex()}",
                                     headers={"Accept": "application/vnd.opentimestamps.v1"},
                                     timeout=TIMEOUT_SECONDS)
                if response.status_code == 200 and response.content:
                    return base, response.content
            except Exception:
                continue
        return None


@dataclass
class Root:
    day: str
    merkle_root: str
    n_commitments: int
    submitted_at: str | None = None
    status: str = "pending"
    receipt: str | None = None
    calendar: str | None = None
    anchored_at: str | None = None
    note: str = ""
    leaves: frozenset[str] = frozenset()

    def as_dict(self) -> dict:
        mechanism = flags.mechanism("anchoring") or {}
        return {
            "day": self.day, "merkle_root": self.merkle_root,
            "n_commitments": self.n_commitments, "submitted_at": self.submitted_at,
            "status": self.status, "receipt": self.receipt, "calendar": self.calendar,
            "anchored_at": self.anchored_at,
            "note": self.note,
            "means": (
                "A Bitcoin-backed proof that these commitments existed by this time."
                if self.status == "anchored"
                else "Submitted, not yet confirmed. A pending root proves nothing on its own."
                if self.submitted_at
                else "Computed from this day's commitments and not submitted yet, so it proves "
                     "nothing outside this service."
            ),
            "guarantees": mechanism.get("guarantees"),
            "does_not": mechanism.get("does_not"),
        }


@dataclass
class Anchors:
    roots: dict[str, Root] = field(default_factory=dict)
    calendar: Calendar = field(default_factory=Calendar)

    def record(self, day: str, commitments: list[str]) -> Root:
        """Compute (or recompute) the day's root. Submission is a separate, explicit step."""
        root = Root(day=day, merkle_root=merkle_root(commitments),
                    n_commitments=len(commitments), leaves=frozenset(commitments))
        existing = self.roots.get(day)
        if existing and existing.merkle_root == root.merkle_root:
            existing.n_commitments = root.n_commitments
            return existing
        if existing and existing.status == "anchored":
            # The anchored root stands for the set it was built from; a later answer gets its own.
            existing.note = ("More commitments arrived after this root was anchored; they belong "
                             "to the next root, not this one.")
            return existing
        self.roots[day] = root
        return root

    def submit(self, day: str) -> Root:
        root = self.roots.get(day)
        if root is None:
            raise KeyError(day)
        if not root.merkle_root:
            root.note = "No commitments on this day, so there is nothing to anchor."
            return root
        if not flags.enabled("FF_ANCHOR"):
            root.status = "pending"
            root.note = "FF_ANCHOR is off: the root is computed and shown, never submitted."
            return root
        result = self.calendar.submit(bytes.fromhex(root.merkle_root))
        root.submitted_at = _now()
        if result is None:
            root.status = "pending"
            root.note = ("No calendar was reachable from this host. The root stands; the external "
                         "timestamp does not exist yet.")
            return root
        base, receipt = result
        root.calendar = base
        root.receipt = base64.b64encode(receipt).decode()
        root.status = "pending"
        root.note = ("A calendar holds this digest. It becomes anchored when the proof is upgraded "
                     "after the next Bitcoin block.")
        return root

    def upgrade(self, day: str) -> Root:
        root = self.roots.get(day)
        if root is None:
            raise KeyError(day)
        if root.status == "anchored" or not root.merkle_root:
            return root
        if not flags.enabled("FF_ANCHOR"):
            return root
        result = self.calendar.upgrade(bytes.fromhex(root.merkle_root))
        if result is None:
            root.note = ("Not confirmed yet. OpenTimestamps upgrades after the next Bitcoin block, "
                         "so this normally takes tens of minutes to a few hours.")
            return root
        base, receipt = result
        root.calendar = base
        root.receipt = base64.b64encode(receipt).decode()
        root.status = "anchored"
        root.anchored_at = _now()
        root.note = "Upgraded: the calendar returned a confirmed proof for this root."
        return root

    def all(self) -> list[dict]:
        return [self.roots[day].as_dict() for day in sorted(self.roots, reverse=True)]

    def for_day(self, day: str) -> dict | None:
        root = self.roots.get(day)
        return root.as_dict() if root else None

    def receipt_for_commitment(self, commitment: str) -> dict | None:
        """Which day's root actually covers this commitment. Used by the ledger Verify panel, so
        it has to be the root this commitment is a leaf of -- not merely the most recent one."""
        if not commitment:
            return None
        for day in sorted(self.roots, reverse=True):
            root = self.roots[day]
            if commitment in root.leaves:
                return root.as_dict()
        return None

    def reset(self) -> None:
        self.roots.clear()
        self.calendar = Calendar()
