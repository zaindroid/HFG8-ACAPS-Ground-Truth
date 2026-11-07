"""The channels, and exactly what each one is in this build.

Every channel carries the same magic link and resolves to the same Answer record, so the record
is identical whether the expert tapped a word in an email, replied to an SMS with "4 likely", sent
a voice note or spoke to the analyst (section 6e).

**Nothing here sends a message.** There is no SMTP server, no WhatsApp Business account, no SMS
gateway and no Teams app registration in this repository, so `transport_for` returns `recorded`
for every channel and the composed message goes to an outbox. The reason this is written out
rather than hidden behind a provider interface with a note-to-self in it: a product that shows "sent" for
a message that never left the machine is lying to the analyst about whether an expert was asked,
which is the one thing the delivery view exists to answer.

What a pilot replaces: `Reach.deliver`. A provider must (1) return its own transport name, (2) set
`delivered_at` only from the provider's receipt and never from the fact that the call returned,
and (3) leave `answered_at` alone -- an answer is an answer arriving, not a message being read.
"""
from __future__ import annotations

from ..hardening import flags as ff

# channel -> (what it is, the flag that gates it, the reply shape an expert can use)
CHANNELS: dict[str, dict] = {
    "email": {
        "name": "Email",
        "flag": None,
        "built": "Plain text under 2 KB, personal sender name, one link per likelihood word; a "
                 "plain reply in the analyst's own thread is parsed instead",
        "reply": "tap a word, or reply in plain words",
        "first_choice": True,
    },
    "whatsapp": {
        "name": "WhatsApp",
        "flag": None,
        "built": "Message with the link and a reply template; voice notes accepted and "
                 "transcribed, then confirmed back in one line",
        "reply": "tap the link, reply, or send a voice note",
    },
    "signal": {
        "name": "Signal",
        "flag": None,
        "built": "Same message as WhatsApp; chosen by experts who prefer it",
        "reply": "tap the link, reply, or send a voice note",
    },
    "sms": {
        "name": "SMS",
        "flag": None,
        "built": "One message with the link and the numeric reply form",
        "reply": 'reply "4 likely", or tap the link',
    },
    "teams": {
        "name": "Microsoft Teams",
        "flag": "FF_TEAMS",
        "built": "Direct message as an adaptive card; only where the agency permits the "
                 "integration, which is an agreement and not a code change",
        "reply": "answer in the card",
        "off_note": "FF_TEAMS is off: Teams needs an app registration inside the agency's own "
                    "tenant, which no hackathon build can have. Falls back to email.",
    },
    "call": {
        "name": "Scheduled call",
        "flag": None,
        "built": "An ICS invite to the expert and the analyst; the analyst takes the answer and "
                 "enters it as relayed, and it counts only once the expert confirms it",
        "reply": "speak to the analyst, then confirm by link or reply",
    },
    "ivr": {
        "name": "Phone keypad (IVR)",
        "flag": "FF_IVR",
        "built": "Keypad answers and a missed-call trigger",
        "reply": "press 1 to 5",
        "off_note": "FF_IVR is off: it needs a telephony account, and the tariffs have to be "
                    "verified with a local partner before anyone says the word free. Falls back "
                    "to SMS.",
    },
}
FALLBACK = {"teams": "email", "ivr": "sms"}
TRANSPORT_NOTE = (
    "No message left this machine. Every channel composes the real body and records it in the "
    "outbox; `transport: recorded` says so on each one. Replace Reach.deliver with a provider to "
    "send for real."
)


def enabled(channel: str) -> bool:
    spec = CHANNELS.get(channel)
    if not spec:
        return False
    flag = spec.get("flag")
    return True if flag is None else ff.enabled(flag)


def resolve(channel: str) -> str:
    """The channel actually used. A flagged-off channel falls back rather than failing: the point
    is that the expert is asked, and the delivery record says which channel carried it."""
    channel = (channel or "email").strip().lower()
    if channel not in CHANNELS:
        return "email"
    if enabled(channel):
        return channel
    return FALLBACK.get(channel, "email")


def transport_for(_channel: str) -> str:
    """`recorded`, for every channel, until a provider exists. One function to change."""
    return "recorded"


def status() -> list[dict]:
    """What the committee view and the README both read, so they cannot disagree."""
    rows = []
    for key, spec in CHANNELS.items():
        rows.append({
            "channel": key,
            "name": spec["name"],
            "flag": spec.get("flag"),
            "enabled": enabled(key),
            "built": spec["built"],
            "reply": spec["reply"],
            "falls_back_to": FALLBACK.get(key) if not enabled(key) else None,
            "off_note": spec.get("off_note") if not enabled(key) else None,
            "transport": transport_for(key),
        })
    return rows
