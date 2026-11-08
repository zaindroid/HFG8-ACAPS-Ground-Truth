"""Mechanism 5: a public timestamp for the daily commitment root (Sigstore Rekor).

One Merkle root per UTC day over that day's answer commitments. The root is signed with a P-256 key
derived from COMMITTEE_KEY and entered into Rekor, Sigstore's public, append-only transparency log
(run under the Linux Foundation's OpenSSF). Nothing but the 32-byte root goes in: no answer, no
name, no pseudonym.

What the entry buys: Rekor returns a log index, the time it integrated the entry, a signed entry
timestamp and an inclusion proof against its signed tree head. From then on anyone can check, with
no account and without trusting this service, that this exact root was in a public log by that
time -- so an answer revealed later either hashes back into it or was changed.

The status is honest by construction. `anchored` means Rekor returned an inclusion proof for the
entry. A submission that got a log index but no proof stays `pending` until GET on the entry returns
one. An unreachable log is reported as such; nothing is invented.
"""
from __future__ import annotations
import base64
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import flags, keys

LOG_URL = "https://rekor.sigstore.dev"
SEARCH_URL = "https://search.sigstore.dev"
TIMEOUT_SECONDS = 6.0
KEY_LABEL = "anchoring/rekor/p256/v1"


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


def signing_key():
    """The P-256 key that signs each root before it is logged. Derived from the committee secret,
    so its public key -- and therefore every past entry -- stays checkable after a restart."""
    from cryptography.hazmat.primitives.asymmetric import ec

    order = int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)
    scalar = int.from_bytes(keys.seed(KEY_LABEL, 48), "big") % (order - 1) + 1
    return ec.derive_private_key(scalar, ec.SECP256R1())


def public_key_pem() -> bytes:
    from cryptography.hazmat.primitives import serialization

    return signing_key().public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


def hashedrekord(root_hex: str) -> dict:
    """A Rekor `hashedrekord` entry for the root. The logged artifact is the 32 raw root bytes; its
    SHA-256 is what Rekor records, and the ECDSA signature over it is what Rekor checks."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec

    artifact = bytes.fromhex(root_hex)
    signature = signing_key().sign(artifact, ec.ECDSA(hashes.SHA256()))
    return {
        "apiVersion": "0.0.1",
        "kind": "hashedrekord",
        "spec": {
            "data": {"hash": {"algorithm": "sha256",
                              "value": hashlib.sha256(artifact).hexdigest()}},
            "signature": {
                "content": base64.b64encode(signature).decode(),
                "publicKey": {"content": base64.b64encode(public_key_pem()).decode()},
            },
        },
    }


class RekorLog:
    """Sigstore Rekor over httpx. Swapped for a fake in the tests.

    Both calls return (uuid, entry) or None. `entry` is Rekor's own JSON for the log entry:
    logIndex, integratedTime, logID, body and verification (signedEntryTimestamp, inclusionProof).
    """

    def submit(self, root_hex: str) -> tuple[str, dict] | None:
        import httpx

        try:
            response = httpx.post(f"{LOG_URL}/api/v1/log/entries", json=hashedrekord(root_hex),
                                  timeout=TIMEOUT_SECONDS)
        except Exception:
            return None
        if response.status_code == 201:
            return _first(response.json())
        if response.status_code == 409:
            # Already logged: Rekor points at the existing entry, which is the one we want.
            location = response.headers.get("location", "")
            uuid = location.rstrip("/").rsplit("/", 1)[-1]
            return self.fetch(uuid) if uuid else None
        return None

    def fetch(self, uuid: str) -> tuple[str, dict] | None:
        import httpx

        try:
            response = httpx.get(f"{LOG_URL}/api/v1/log/entries/{uuid}", timeout=TIMEOUT_SECONDS)
        except Exception:
            return None
        return _first(response.json()) if response.status_code == 200 else None


def _first(payload: dict) -> tuple[str, dict] | None:
    if not isinstance(payload, dict) or not payload:
        return None
    uuid, entry = next(iter(payload.items()))
    return uuid, entry


@dataclass
class Root:
    day: str
    merkle_root: str
    n_commitments: int
    submitted_at: str | None = None
    status: str = "pending"
    receipt: str | None = None
    log: str | None = None
    entry_uuid: str | None = None
    log_index: int | None = None
    integrated_at: str | None = None
    anchored_at: str | None = None
    note: str = ""
    leaves: frozenset[str] = frozenset()

    def as_dict(self) -> dict:
        mechanism = flags.mechanism("anchoring") or {}
        return {
            "day": self.day, "merkle_root": self.merkle_root,
            "n_commitments": self.n_commitments, "submitted_at": self.submitted_at,
            "status": self.status, "receipt": self.receipt, "log": self.log,
            "entry_uuid": self.entry_uuid, "log_index": self.log_index,
            "integrated_at": self.integrated_at, "anchored_at": self.anchored_at,
            "verify_url": self.verify_url(),
            "note": self.note,
            "means": (
                "An entry in Sigstore's public transparency log: anyone can check that this root "
                "existed by the time Rekor integrated it."
                if self.status == "anchored"
                else "Sent to the public log, no inclusion proof yet. A pending root proves "
                     "nothing on its own."
                if self.submitted_at
                else "Computed from this day's commitments and not submitted yet, so it proves "
                     "nothing outside this service."
            ),
            "guarantees": mechanism.get("guarantees"),
            "does_not": mechanism.get("does_not"),
        }

    def verify_url(self) -> str | None:
        """Only once anchored: a link beside a pending root would claim what it has not earned."""
        if self.status != "anchored" or self.log_index is None:
            return None
        return f"{SEARCH_URL}/?logIndex={self.log_index}"

    def take(self, uuid: str, entry: dict) -> None:
        """Copy what Rekor returned onto the root, and decide the status from it alone."""
        self.log = LOG_URL
        self.entry_uuid = uuid
        self.log_index = entry.get("logIndex")
        when = entry.get("integratedTime")
        if isinstance(when, int):
            self.integrated_at = datetime.fromtimestamp(when, timezone.utc).isoformat(
                timespec="seconds")
        verification = entry.get("verification") or {}
        self.receipt = base64.b64encode(
            json.dumps(verification, sort_keys=True).encode()).decode() if verification else None
        if verification.get("inclusionProof"):
            self.status = "anchored"
            self.anchored_at = self.anchored_at or _now()
            self.note = (f"In the public log at index {self.log_index}, with an inclusion proof "
                         "and a signed entry timestamp.")
        else:
            self.status = "pending"
            self.note = ("The log accepted the entry but returned no inclusion proof yet; it "
                         "becomes anchored when one is returned.")


@dataclass
class Anchors:
    roots: dict[str, Root] = field(default_factory=dict)
    log: RekorLog = field(default_factory=RekorLog)

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
        result = self.log.submit(root.merkle_root)
        root.submitted_at = _now()
        if result is None:
            root.status = "pending"
            root.note = ("The public log was not reachable from this host. The root stands; the "
                         "public timestamp does not exist yet.")
            return root
        root.take(*result)
        return root

    def upgrade(self, day: str) -> Root:
        root = self.roots.get(day)
        if root is None:
            raise KeyError(day)
        if root.status == "anchored" or not root.merkle_root:
            return root
        if not flags.enabled("FF_ANCHOR"):
            return root
        if not root.entry_uuid:
            return self.submit(day)
        result = self.log.fetch(root.entry_uuid)
        if result is None:
            root.note = "The public log did not return the entry this time; try again shortly."
            return root
        root.take(*result)
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
        self.log = RekorLog()
