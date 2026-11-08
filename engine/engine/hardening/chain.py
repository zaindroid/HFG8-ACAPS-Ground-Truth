"""Mechanism 8: a hash-chained record of every step of the risk process.

One append-only chain per risk. Each event names the step (`kind`), when it happened (`at`), a
small `data` dict, and the hash of the event before it. The event's own hash is SHA-256 over the
canonical JSON (sorted keys, no spaces) of every field except `hash`, so changing, inserting or
removing any past event changes every hash after it. The first event points at 64 zeros.

The head of each risk's chain for a day is also a leaf of that day's anchoring root (anchors.py),
so the daily public log entry covers the process as well as the answers.

What goes into `data` is restricted on purpose: counts, risk / pulse / edition / crisis ids, enum
values and SHA-256 fingerprints. Never a name, an address, a pseudonym, an expert id or free text.
A fingerprint lets anyone holding the original check it; it does not publish the original.
"""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

GENESIS = "0" * 64
KINDS = (
    "alert_raised", "question_approved", "panel_invited", "answers_sealed", "revealed",
    "draft_created", "decision_recorded", "published", "outcome_resolved",
)
# The only keys an event may carry in `data`, and what each value may look like. Anything else is
# refused at append time, so a careless caller cannot put a name or a sentence into the chain.
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,39}$")
FIELDS: dict[str, str] = {
    "risk_id": "id", "pulse_id": "id", "draft_id": "id", "alert_id": "id", "crisis_id": "id",
    "month_from": "id", "month_to": "id",
    "rule": "enum", "metric": "enum", "direction": "enum", "action": "enum", "outcome": "enum",
    "reason": "enum", "status": "enum", "decision": "enum",
    "old_value": "number", "new_value": "number",
    "n": "count", "n_invited": "count", "n_answers": "count",
    "edition_sha256": "hex", "question_sha256": "hex", "commitment_root": "hex",
    "draft_sha256": "hex", "rationale_sha256": "hex", "entry_sha256": "hex",
    "verify_hash": "hex",
}
ENUM = re.compile(r"^[a-z][a-z0-9_]{0,39}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(obj) -> str:
    """SHA-256 of a string's UTF-8 bytes, or of any other value's canonical JSON."""
    raw = obj.encode() if isinstance(obj, str) else canonical(obj)
    return hashlib.sha256(raw).hexdigest()


def event_hash(event: dict) -> str:
    return hashlib.sha256(canonical({k: v for k, v in event.items() if k != "hash"})).hexdigest()


def check_data(data: dict) -> None:
    """Raise ValueError unless every key is allowed and every value has the allowed shape."""
    for key, value in data.items():
        shape = FIELDS.get(key)
        if shape is None:
            raise ValueError(f"chain data may not carry {key!r}")
        if value is None:
            continue
        ok = {
            "id": lambda v: isinstance(v, str) and bool(ID.match(v)),
            "enum": lambda v: isinstance(v, str) and bool(ENUM.match(v)),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "count": lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0,
            "hex": lambda v: isinstance(v, str) and bool(HEX64.match(v)),
        }[shape](value)
        if not ok:
            raise ValueError(f"chain data {key!r} is not a valid {shape}")


@dataclass
class Chain:
    events: dict[str, list[dict]] = field(default_factory=dict)

    def append(self, risk_id: str, kind: str, data: dict | None = None,
               at: str | None = None) -> dict:
        if kind not in KINDS:
            raise ValueError(f"unknown chain event kind {kind!r}")
        data = dict(data or {})
        check_data(data)
        chain = self.events.setdefault(risk_id, [])
        event = {
            "seq": len(chain),
            "risk_id": risk_id,
            "kind": kind,
            "at": at or _now(),
            "data": data,
            "prev_hash": chain[-1]["hash"] if chain else GENESIS,
        }
        event["hash"] = event_hash(event)
        chain.append(event)
        return event

    def get(self, risk_id: str) -> list[dict]:
        return list(self.events.get(risk_id, []))

    def head(self, risk_id: str) -> str | None:
        chain = self.events.get(risk_id)
        return chain[-1]["hash"] if chain else None

    def verify(self, risk_id: str) -> dict:
        return verify_events(self.events.get(risk_id, []))

    def heads_for_day(self, day: str) -> dict[str, str]:
        """Per risk, the hash of its last event recorded on that UTC day. Because each hash covers
        everything before it, that one value stands for the whole chain up to the end of the day."""
        heads: dict[str, str] = {}
        for risk_id, chain in self.events.items():
            on_day = [e for e in chain if e["at"][:10] == day]
            if on_day:
                heads[risk_id] = on_day[-1]["hash"]
        return heads

    def days(self) -> set[str]:
        return {e["at"][:10] for chain in self.events.values() for e in chain}

    def drop(self, risk_id: str) -> None:
        self.events.pop(risk_id, None)

    def reset(self) -> None:
        self.events.clear()


def verify_events(events: list[dict]) -> dict:
    """Recompute every hash and link. `broken_at` is the first seq that does not check: its own
    hash is wrong, it points at the wrong predecessor, or its position is not its seq (an event
    was removed or inserted before it)."""
    prev = GENESIS
    for position, event in enumerate(events):
        if (event.get("seq") != position or event.get("prev_hash") != prev
                or event.get("hash") != event_hash(event)):
            return {"intact": False, "broken_at": position, "length": len(events)}
        prev = event["hash"]
    return {"intact": True, "broken_at": None, "length": len(events)}
