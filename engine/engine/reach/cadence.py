"""Cadence: the rules that make being on this panel bearable.

Guarantees, all enforced here and not left to the sender's judgement:

* one pulse per expert per seven days, across every panel. A second one is refused with the date
  they become eligible again, so the analyst can see the rule rather than wonder why.
* a stopped contact is never sent anything. A paused one is never sent anything until the pause
  ends.
* at most one reminder per pulse, and only after 24 hours. There is never a third message.
* send at the expert's own hour in their own time zone, and not Friday afternoon unless the alert
  is escalating -- a question that lands at 16:40 on a Friday is a question answered on Monday or
  not at all.

Does not: decide whether a question is worth asking. That is the analyst's call, and these rules
only ever say "not yet" or "not this way".
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

PULSE_EVERY_DAYS = 7
REMINDER_AFTER_HOURS = 24
MAX_REMINDERS = 1
FRIDAY = 4
FRIDAY_CUTOFF_HOUR = 12


class Refused(ValueError):
    """A cadence rule said no. The message is addressed to the analyst reading it."""


def _parse(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def check(contact, history: list, kind: str = "pulse") -> None:
    """Raise `Refused` unless this message may go out now."""
    if contact.status == "stopped":
        return _refuse(f"{contact.expert_id} replied STOP on "
                       f"{(contact.stopped_at or 'an earlier date')[:10]}. Nothing is sent to a "
                       "stopped contact, including a reminder.")
    if contact.is_paused():
        return _refuse(f"{contact.expert_id} is paused until {contact.paused_until[:10]}.")

    if kind == "reminder":
        pulses = [d for d in history if d.kind in ("pulse", "first_contact")]
        if not pulses:
            return _refuse("there is nothing to remind this contact about on this pulse")
        latest = max((_parse(d.sent_at) for d in pulses if d.sent_at), default=None)
        if latest and datetime.now(timezone.utc) - latest < timedelta(hours=REMINDER_AFTER_HOURS):
            due = (latest + timedelta(hours=REMINDER_AFTER_HOURS)).isoformat(timespec="seconds")
            return _refuse(f"the reminder for this pulse is due at {due}, "
                           f"{REMINDER_AFTER_HOURS} hours after the question went out")
        reminders = [d for d in history if d.kind == "reminder"]
        if len(reminders) >= MAX_REMINDERS:
            return _refuse("this contact has already had the one reminder. The analyst may write "
                           "personally; the system never sends a third message.")
        return None

    if kind in ("pulse", "first_contact"):
        sent = [_parse(d.sent_at) for d in history if d.kind in ("pulse", "first_contact")]
        latest = max((s for s in sent if s), default=None)
        if latest:
            eligible = latest + timedelta(days=PULSE_EVERY_DAYS)
            if datetime.now(timezone.utc) < eligible:
                return _refuse(
                    f"{contact.expert_id} had a question on {latest.date().isoformat()}. The cap "
                    f"is one pulse per expert per {PULSE_EVERY_DAYS} days across every panel; "
                    f"they are eligible again on {eligible.date().isoformat()}.")
    return None


def _refuse(message: str):
    raise Refused(message)


def next_send_time(contact, escalating: bool = False) -> str:
    """The expert's own hour in their own time zone, Friday afternoon avoided.

    `escalating` is the one override, and it belongs to the alert rather than to the sender: a
    deteriorating crisis is the case where a Friday evening question is the right thing to do."""
    offset = timedelta(hours=float(getattr(contact, "utc_offset_hours", 0.0) or 0.0))
    local = datetime.now(timezone.utc) + offset
    hour = int(getattr(contact, "hour_pref", 8) or 8)
    target = local.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= local:
        target = target + timedelta(days=1)
    if not escalating:
        while target.weekday() == FRIDAY and target.hour >= FRIDAY_CUTOFF_HOUR:
            target = (target + timedelta(days=1)).replace(hour=hour)
        if target.weekday() in (5, 6):
            # A weekend send becomes Monday. Nobody on a vetted professional panel owes us a
            # Saturday, and a question sent then is answered late or resented.
            target = target + timedelta(days=(7 - target.weekday()))
            target = target.replace(hour=hour)
    return (target - offset).isoformat(timespec="seconds")


def status() -> dict:
    return {
        "one_pulse_every_days": PULSE_EVERY_DAYS,
        "reminder_after_hours": REMINDER_AFTER_HOURS,
        "max_reminders_per_pulse": MAX_REMINDERS,
        "pause_by_one_word_days": 30,
        "stop": "immediate and logged",
        "send_hour": "the expert's own preferred hour in their own time zone",
        "friday_afternoon": "avoided unless the alert is escalating",
        "reminder_wording": "never carries a count of who has answered",
    }
