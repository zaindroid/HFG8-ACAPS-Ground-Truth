"""Section 6e: Reach. Experts never sign up; the question comes to them where they already are.

What this module does. It holds the analyst's address book, composes the message for each channel
around one magic link, records what was sent, enforces the cadence rules that make the whole thing
bearable to be on the receiving end of, and parses answers that come back as plain replies instead
of taps (`..inbound`).

What it guarantees. A contact who replies STOP is stopped immediately and the act is logged. No
expert receives more than one pulse in seven days across every panel. A message body carries
nothing that would be unsafe on a lock screen: no ACAPS rating, no severity number, no place name
finer than the crisis title. A reminder never carries a count of who has answered. A preference
the analyst suggested is marked as suggested until the expert confirms it.

What it does not do, and this is the part to say out loud: **it does not send anything.** No SMS
gateway, no WhatsApp Business account and no SMTP credentials exist in this build, so every
channel writes a fully composed message to an outbox and reports `transport: "recorded"`. That is
not a stub standing in for a thing we ran out of time for -- it is the honest state of a
hackathon build, and the payloads, the UI and the README say so in those words rather than
letting a green tick imply a delivery. `Reach.deliver` is the one function a pilot would replace,
and `reach/channels.py` documents the provider contract it would have to satisfy.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from . import cadence as cadence_mod
from . import channels as channels_mod
from . import contacts as contacts_mod
from . import messages as messages_mod

__all__ = ["Reach", "new", "cadence_mod", "channels_mod", "contacts_mod", "messages_mod"]


@dataclass
class Delivery:
    """One attempt to reach one expert about one pulse, on one channel."""
    pulse_id: str
    expert_id: str
    channel: str
    kind: str                       # "first_contact" | "pulse" | "reminder" | "feedback" | "call"
    scheduled_for: str
    sent_at: str | None = None
    transport: str = "recorded"
    token: str | None = None
    body: str = ""
    subject: str | None = None
    delivered_at: str | None = None
    answered_at: str | None = None
    relayed: bool = False

    def as_dict(self) -> dict:
        return {
            "pulse_id": self.pulse_id,
            # The expert id is in the record because the analyst's own address book is the
            # registry (section 6e) and they need to see who has not answered. It never leaves
            # through a public route: /reach/pulses/{id}/delivery returns counts per channel.
            "expert_id": self.expert_id,
            "channel": self.channel,
            "kind": self.kind,
            "scheduled_for": self.scheduled_for,
            "sent_at": self.sent_at,
            "transport": self.transport,
            "subject": self.subject,
            "body": self.body,
            "delivered_at": self.delivered_at,
            "answered_at": self.answered_at,
            "relayed": self.relayed,
        }


@dataclass
class Reach:
    book: contacts_mod.Book = field(default_factory=contacts_mod.Book)
    outbox: list[Delivery] = field(default_factory=list)

    # -- sending ---------------------------------------------------------------
    def deliver(self, delivery: Delivery) -> Delivery:
        """The one seam a pilot replaces.

        Here it records the message and marks the transport as recorded, so nothing in the
        product can report a delivery that did not happen. A provider implementation would set
        `transport` to its own name and `delivered_at` from the provider's receipt -- never from
        the fact that we called it."""
        delivery.sent_at = contacts_mod.now()
        delivery.transport = channels_mod.transport_for(delivery.channel)
        self.outbox.append(delivery)
        return delivery

    def send_pulse(self, pulse: dict, risk: dict, expert_id: str, token: str,
                   channel: str | None = None, kind: str = "pulse",
                   escalating: bool = False) -> Delivery:
        """Compose and record one pulse message. Raises `cadence.Refused` when a rule says no."""
        contact = self.book.require(expert_id)
        chosen = channels_mod.resolve(channel or contact.effective_channel())
        cadence_mod.check(contact, self.history_for(expert_id), kind)
        if kind == "reminder":
            subject, body = messages_mod.reminder(contact, pulse, risk, token, chosen)
        elif kind == "first_contact":
            subject, body = messages_mod.first_contact(contact, pulse, risk, token, chosen)
        else:
            subject, body = messages_mod.pulse_message(contact, pulse, risk, token, chosen)
        question = (pulse.get("question") or {}).get("text")
        messages_mod.assert_lock_screen_safe(body, risk, question)
        if subject:
            # The subject is held to the rule with no exemption: it is the one line every
            # notification shows, whatever the body does.
            messages_mod.assert_lock_screen_safe(subject, risk)
        return self.deliver(Delivery(
            pulse_id=pulse["id"], expert_id=expert_id, channel=chosen, kind=kind,
            scheduled_for=cadence_mod.next_send_time(contact, escalating),
            token=token, body=body, subject=subject,
        ))

    def send_feedback(self, pulse_id: str, expert_id: str, text: str) -> Delivery:
        """The loop-closing message, after the reveal. Not a pulse, so the 7-day cap does not
        apply to it: it is the thing we promised in return for answering, and withholding it to
        respect a cadence rule would be the rule eating its own purpose."""
        contact = self.book.require(expert_id)
        return self.deliver(Delivery(
            pulse_id=pulse_id, expert_id=expert_id, channel=contact.effective_channel(),
            kind="feedback", scheduled_for=contacts_mod.now(), body=text,
            subject=messages_mod.FEEDBACK_SUBJECT,
        ))

    # -- reading ---------------------------------------------------------------
    def history_for(self, expert_id: str) -> list[Delivery]:
        return [d for d in self.outbox if d.expert_id == expert_id]

    def for_pulse(self, pulse_id: str) -> list[Delivery]:
        return [d for d in self.outbox if d.pulse_id == pulse_id]

    def mark_answered(self, pulse_id: str, expert_id: str, relayed: bool = False) -> None:
        for delivery in self.for_pulse(pulse_id):
            if delivery.expert_id == expert_id and delivery.answered_at is None:
                delivery.answered_at = contacts_mod.now()
                delivery.relayed = relayed

    def delivery_report(self, pulse_id: str) -> dict:
        """Counts per channel, which is all a desk needs and all a public view may ever have."""
        rows = self.for_pulse(pulse_id)
        per_channel: dict[str, dict] = {}
        for delivery in rows:
            bucket = per_channel.setdefault(delivery.channel, {
                "channel": delivery.channel, "sent": 0, "delivered": 0, "answered": 0,
                "transport": delivery.transport,
            })
            bucket["sent"] += 1 if delivery.sent_at else 0
            bucket["delivered"] += 1 if delivery.delivered_at else 0
            bucket["answered"] += 1 if delivery.answered_at else 0
        return {
            "pulse_id": pulse_id,
            "channels": sorted(per_channel.values(), key=lambda row: row["channel"]),
            "sent": sum(1 for d in rows if d.sent_at),
            "answered": sum(1 for d in rows if d.answered_at),
            "relayed": sum(1 for d in rows if d.relayed),
            "reminders": sum(1 for d in rows if d.kind == "reminder"),
            "transport_note": channels_mod.TRANSPORT_NOTE,
        }

    def channel_mix(self, pulse_id: str) -> dict[str, int]:
        """For the honesty box: which channels the answers actually came in on."""
        mix: dict[str, int] = {}
        for delivery in self.for_pulse(pulse_id):
            if delivery.answered_at:
                mix[delivery.channel] = mix.get(delivery.channel, 0) + 1
        return dict(sorted(mix.items()))

    def reset(self) -> None:
        self.book.reset()
        self.outbox.clear()


def new() -> Reach:
    return Reach()
