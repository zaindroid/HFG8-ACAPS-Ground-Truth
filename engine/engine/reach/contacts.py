"""The analyst's address book, which is the registry (section 6e).

Guarantees. A contact has no account, no password and no portal: everything an expert can change,
they change by replying or through their link. A preference the analyst suggested is marked as
suggested until the expert confirms it, and sending uses the expert's own value whenever one
exists. STOP is immediate and logged. Pause is 30 days by one word.

Does not. Hold a current physical location -- `coverage_area` is the broad professional patch an
expert works on, because a field worker's whereabouts is the one piece of information in here
that could put somebody in danger, and it is not needed to route a question.
"""
from __future__ import annotations
import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

CHANNEL_PREFS = ("email", "whatsapp", "signal", "sms", "teams", "call")
STATUSES = ("invited", "answered_once", "active", "paused", "stopped")
SET_BY = ("expert", "suggested_by_analyst")
PAUSE_DAYS = 30
CHARTER_VERSION = "2026-11-07.1"
CHARTER = (
    "What we ask: one question about a risk you already follow, at most once a week. "
    "How long: under a minute. "
    "What we store: your answer, the time you sent it, and the name and organisation you gave us. "
    "Who sees what: you choose per answer whether ACAPS sees your name, your peers see a "
    "nickname, or no identity is kept at all. Public pages only ever show group figures. "
    "How to stop: reply STOP and we stop, or PAUSE for a month."
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass
class Contact:
    expert_id: str
    display_name: str = ""              # registry only, never in a public payload
    org_type: str = "ngo"
    coverage_area: str = ""
    theme_tags: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=lambda: ["en"])
    channel_pref: str = "email"
    hour_pref: int = 8
    tz: str = "UTC"
    utc_offset_hours: float = 0.0
    preferences_set_by: str = "suggested_by_analyst"
    status: str = "invited"
    paused_until: str | None = None
    charter_version: str | None = None
    consented_at: str | None = None
    stopped_at: str | None = None
    address: str = ""                   # registry only: the mailbox or number the analyst holds

    def effective_channel(self) -> str:
        return self.channel_pref if self.channel_pref in CHANNEL_PREFS else "email"

    def is_paused(self) -> bool:
        until = _parse(self.paused_until)
        return bool(until and datetime.now(timezone.utc) < until)

    def public_view(self) -> dict:
        """What the desk may read. No name, no mailbox, no number: the analyst sees those in the
        registry behind an attributed read, not in a list that a screenshot could carry."""
        return {
            "expert_id": self.expert_id,
            "org_type": self.org_type,
            "coverage_area": self.coverage_area,
            "theme_tags": list(self.theme_tags),
            "languages": list(self.languages),
            "channel_pref": self.channel_pref,
            "channel_pref_set_by": self.preferences_set_by,
            "hour_pref": self.hour_pref,
            "tz": self.tz,
            "status": self.status,
            "paused_until": self.paused_until,
            "consent": {
                "charter_version": self.charter_version,
                "consented_at": self.consented_at,
                "stopped_at": self.stopped_at,
            },
            "has_address_on_file": bool(self.address),
        }


class Refused(ValueError):
    """A contact rule said no. The message is written to be read by the analyst."""


class Book:
    def __init__(self) -> None:
        self.contacts: dict[str, Contact] = {}
        # Every stop, pause and consent, with its timestamp. An opt-out that is honoured but not
        # recorded cannot be shown to have been honoured.
        self.consent_log: list[dict] = []

    def reset(self) -> None:
        self.contacts.clear()
        self.consent_log.clear()

    def add(self, contact: Contact) -> Contact:
        self.contacts[contact.expert_id] = contact
        return contact

    def get(self, expert_id: str) -> Contact | None:
        return self.contacts.get(expert_id)

    def require(self, expert_id: str) -> Contact:
        contact = self.contacts.get(expert_id)
        if not contact:
            raise Refused(f"{expert_id} is not in the address book; add the contact first")
        return contact

    def upsert(self, body: dict) -> Contact:
        expert_id = (body.get("expert_id") or "").strip()
        if not expert_id:
            raise Refused("a contact needs an expert_id")
        existing = self.contacts.get(expert_id)
        contact = existing or Contact(expert_id=expert_id)
        for name in ("display_name", "org_type", "coverage_area", "channel_pref", "tz",
                     "address"):
            if body.get(name) is not None:
                setattr(contact, name, str(body[name]).strip())
        for name in ("theme_tags", "languages"):
            if body.get(name) is not None:
                setattr(contact, name, [str(v).strip() for v in body[name] if str(v).strip()])
        if body.get("hour_pref") is not None:
            contact.hour_pref = max(0, min(23, int(body["hour_pref"])))
        if body.get("utc_offset_hours") is not None:
            contact.utc_offset_hours = float(body["utc_offset_hours"])
        if contact.channel_pref not in CHANNEL_PREFS:
            raise Refused(f"channel_pref must be one of {CHANNEL_PREFS}")
        return self.add(contact)

    # -- consent ---------------------------------------------------------------
    def record_consent(self, expert_id: str, charter_version: str) -> Contact:
        contact = self.require(expert_id)
        if charter_version != CHARTER_VERSION:
            raise Refused(
                f"this consent is against charter {charter_version}; the current one is "
                f"{CHARTER_VERSION}. Consent does not carry across a change to what we ask.")
        contact.charter_version = charter_version
        contact.consented_at = now()
        contact.stopped_at = None
        contact.status = "active" if contact.status == "answered_once" else contact.status
        self.consent_log.append({"expert_id": expert_id, "act": "consented",
                                 "charter_version": charter_version, "at": contact.consented_at})
        return contact

    def stop(self, expert_id: str, said: str = "STOP") -> Contact:
        """One word, honoured now, logged. Not a flag to review later."""
        contact = self.require(expert_id)
        contact.status = "stopped"
        contact.stopped_at = now()
        contact.paused_until = None
        self.consent_log.append({"expert_id": expert_id, "act": "stopped", "said": said,
                                 "at": contact.stopped_at})
        return contact

    def pause(self, expert_id: str, days: int = PAUSE_DAYS, said: str = "PAUSE") -> Contact:
        contact = self.require(expert_id)
        contact.status = "paused"
        until = datetime.now(timezone.utc) + timedelta(days=max(1, int(days)))
        contact.paused_until = until.isoformat(timespec="seconds")
        self.consent_log.append({"expert_id": expert_id, "act": "paused", "said": said,
                                 "until": contact.paused_until, "at": now()})
        return contact

    def mark_answered(self, expert_id: str) -> Contact | None:
        contact = self.contacts.get(expert_id)
        if not contact:
            return None
        contact.status = "active" if contact.status == "answered_once" else "answered_once"
        return contact

    # -- preferences -----------------------------------------------------------
    def set_preferences(self, expert_id: str, body: dict, by: str) -> Contact:
        """The expert can set their own. The analyst can only suggest.

        A suggestion is applied so the next message goes somewhere plausible, and it stays marked
        as a suggestion so nobody can later claim the expert chose it. Once the expert confirms,
        their value is theirs and an analyst suggestion no longer overwrites it."""
        if by not in SET_BY:
            raise Refused(f"preferences are set by one of {SET_BY}")
        contact = self.require(expert_id)
        if by == "suggested_by_analyst" and contact.preferences_set_by == "expert":
            raise Refused(
                f"{expert_id} set their own channel and hour; an analyst may suggest a change in "
                "a message but cannot overwrite it here")
        for name in ("channel_pref", "tz"):
            if body.get(name) is not None:
                setattr(contact, name, str(body[name]).strip())
        if body.get("hour_pref") is not None:
            contact.hour_pref = max(0, min(23, int(body["hour_pref"])))
        if body.get("utc_offset_hours") is not None:
            contact.utc_offset_hours = float(body["utc_offset_hours"])
        if contact.channel_pref not in CHANNEL_PREFS:
            raise Refused(f"channel_pref must be one of {CHANNEL_PREFS}")
        contact.preferences_set_by = by
        self.consent_log.append({"expert_id": expert_id, "act": "preferences",
                                 "set_by": by, "channel": contact.channel_pref, "at": now()})
        return contact

    # -- import ----------------------------------------------------------------
    def import_csv(self, text: str) -> dict:
        """From the analyst's own contacts. Rows missing an id are reported, never guessed at."""
        reader = csv.DictReader(io.StringIO(text))
        added, skipped = [], []
        for index, row in enumerate(reader, start=2):
            body = {key: value for key, value in row.items() if key and value not in (None, "")}
            tags = body.pop("theme_tags", "")
            languages = body.pop("languages", "")
            body["theme_tags"] = [t.strip() for t in str(tags).split(";") if t.strip()]
            body["languages"] = [l.strip() for l in str(languages).split(";") if l.strip()] or ["en"]
            try:
                contact = self.upsert(body)
            except (Refused, ValueError) as error:
                skipped.append({"line": index, "why": str(error)})
                continue
            added.append(contact.expert_id)
        return {
            "added": added, "skipped": skipped, "n_added": len(added),
            "note": ("Imported contacts start as invited and unconsented. The first message is "
                     "the consent-first note; nothing else is sent until they reply."),
        }

    def summary(self) -> dict:
        by_status: dict[str, int] = {}
        for contact in self.contacts.values():
            by_status[contact.status] = by_status.get(contact.status, 0) + 1
        return {
            "n_contacts": len(self.contacts),
            "by_status": dict(sorted(by_status.items())),
            "consented": sum(1 for c in self.contacts.values() if c.consented_at),
            "charter_version": CHARTER_VERSION,
            "reachable": sum(1 for c in self.contacts.values()
                             if c.status != "stopped" and not c.is_paused()),
        }
