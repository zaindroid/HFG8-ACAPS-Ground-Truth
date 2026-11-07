"""The message bodies. Short, personal, and safe on a lock screen.

Guarantees, each enforced by a function in here rather than by care:

* `assert_lock_screen_safe` refuses a body that carries the ACAPS rating, a severity number or a
  place name finer than the crisis title. A notification preview is read by whoever is holding the
  phone, which in this panel's case may be at a checkpoint.
* `reminder` is built from a template with no count in it. "Most of the panel has answered" is the
  strongest thing a reminder may say; a count in a panel of eight tells the reader how to be the
  fifth, and that is herding by arithmetic.
* The first contact carries the charter and the one-word opt-out in the same message as the
  question, because asking first and explaining later is how consent becomes a formality.

Does not: translate. English and French strings live here; anything else is a pilot task, and the
payload says which language it used rather than implying a choice was made.
"""
from __future__ import annotations
import re

FEEDBACK_SUBJECT = "How the panel saw it"
STOP_LINE_EN = "Reply STOP at any time and we stop. Reply PAUSE for a month."
STOP_LINE_FR = "Repondez STOP a tout moment et nous arretons. Repondez PAUSE pour un mois."
# The strongest thing a reminder may say about the others. No number, ever.
REMINDER_LINE_EN = "Most of the panel has answered."
REMINDER_LINE_FR = "La plupart du panel a repondu."


class Unsafe(ValueError):
    """A body that would be unsafe on a lock screen. Raised, not logged and sent anyway."""


def language_of(contact) -> str:
    return "fr" if "fr" in (contact.languages or []) and "en" not in (contact.languages or []) \
        else "en"


def _link(token: str, word: str | None = None) -> str:
    base = f"https://sealed-signals.zaindroid.me/e/{token}"
    return f"{base}?word={word}" if word else base


def crisis_line(risk: dict) -> str:
    """The risk at the level of its crisis title and nothing finer (section 6e).

    The ACAPS title names provinces; those are exactly what must not sit on a lock screen, so
    this reduces to the country and the subject. The full question is behind the link."""
    country = (risk.get("country") or "").strip()
    subject = "the situation you follow"
    title = (risk.get("title") or "").lower()
    for word, phrase in (("displacement", "displacement"), ("insecurity", "cross-border security"),
                         ("flood", "flooding"), ("food", "food security"),
                         ("cholera", "a disease outbreak"), ("access", "humanitarian access")):
        if word in title:
            subject = phrase
            break
    return f"{subject} in {country}" if country else subject


def assert_lock_screen_safe(body: str, risk: dict, question: str | None = None) -> None:
    """Refuse a body that leaks the anchor or the place.

    The rating is withheld because the card withholds it; a notification that says "ACAPS rates
    this High" has anchored the answer before the expert opened anything.

    `question` is the frozen question text, which is exempt and checked separately. There is a
    real tension in section 6e here: it asks for the question in the message and for no place
    name finer than the crisis title. The frozen question names provinces, because ACAPS's own
    published risk does. The reading taken here is that the rule is about the *preview*: every
    body starts with the crisis-level line, so the two lines a lock screen shows name a country
    and a subject, and the question follows below. Everything this module composes around the
    question is still held to the rule, which is why the exemption is one named argument and not
    a switch that turns the check off."""
    if question:
        body = body.replace(question, " ")
    lowered = body.lower()
    for band in ("very low", "very high", "high", "medium", "low"):
        if re.search(rf"\b{band}\b", lowered):
            raise Unsafe(f"this body names the band '{band}'; the rating is not shown before "
                         "submission, including in a notification")
    if re.search(r"\b\d\.\d\b", body):
        raise Unsafe("this body carries a severity number; detail goes behind the link")
    for area in (risk.get("adm1_name") or []):
        if area and area.lower() in lowered:
            raise Unsafe(f"this body names {area}; a lock screen shows the first two lines to "
                         "whoever is holding the phone")


def first_contact(contact, pulse: dict, risk: dict, token: str, channel: str):
    """Consent-first: who is asking, why this expert, the charter, the opt-out, then the question.

    All four before the question, in one message, because a second message asking for consent
    after the first has already asked for work is a formality rather than a choice."""
    from . import contacts as contacts_mod

    french = language_of(contact) == "fr"
    asked_by = pulse.get("asked_by") or "the ACAPS Risk Radar team"
    why = (f"You have worked on {contact.coverage_area}." if contact.coverage_area
           else "You follow this crisis closely.")
    question = (pulse.get("question") or {}).get("text") or "One question about a risk rating."
    if french:
        body = "\n\n".join([
            f"Bonjour, je suis {asked_by}.",
            f"{why} Nous constituons un petit panel pour verifier une evaluation de risque sur "
            f"{crisis_line(risk)}.",
            contacts_mod.CHARTER,
            f"La question : {question}",
            f"Votre lien personnel : {_link(token)}",
            STOP_LINE_FR,
        ])
    else:
        body = "\n\n".join([
            f"Hello, I am {asked_by}.",
            f"{why} We are putting together a small panel to check one risk assessment on "
            f"{crisis_line(risk)}.",
            contacts_mod.CHARTER,
            f"The question: {question}",
            f"Your own link: {_link(token)}",
            STOP_LINE_EN,
        ])
    subject = ("Une question sur un risque" if french else "One question about a risk") \
        if channel == "email" else None
    return subject, body


def pulse_message(contact, pulse: dict, risk: dict, token: str, channel: str):
    """The ordinary ask, for a contact who has already consented."""
    french = language_of(contact) == "fr"
    question = (pulse.get("question") or {}).get("text") or "One question about a risk rating."
    deadline = (pulse.get("question") or {}).get("deadline") or ""
    link = _link(token)
    if channel == "sms":
        # One SMS, crisis line first. The numeric reply form is in it because a link is not
        # always openable, and an SMS preview is the whole message.
        head = (f"A propos de {crisis_line(risk)}." if french
                else f"About {crisis_line(risk)}.")
        body = (f"{head} {question} Reply 1-5 (1 very unlikely, 5 very likely) or open {link}. "
                f"{STOP_LINE_FR if french else STOP_LINE_EN}")
        return None, body
    # The crisis-level line first, so a notification preview names a country and a subject and
    # not a province. The question follows it.
    lines = [f"About {crisis_line(risk)}." if not french else f"A propos de {crisis_line(risk)}.",
             question]
    if channel == "email":
        # One link per word, each opening the confirmation screen. A link click never commits
        # (see api.answer): a mail scanner following every link in a message would otherwise
        # answer on the expert's behalf, five different ways.
        words = [("very unlikely", "very_unlikely"), ("unlikely", "unlikely"), ("even", "even"),
                 ("likely", "likely"), ("very likely", "very_likely")]
        lines.append("\n".join(f"{label}: {_link(token, key)}" for label, key in words))
        lines.append("Tapping a word opens a screen that shows your answer and asks you to "
                     "confirm. Nothing is recorded until you do.")
    else:
        lines.append(f"Your own link: {link}")
        if channel in ("whatsapp", "signal"):
            lines.append("You can also reply in words, or send a voice note.")
    if deadline:
        lines.append(f"The panel's answers open together after the deadline on the screen.")
    lines.append(STOP_LINE_FR if french else STOP_LINE_EN)
    subject = ("Une question" if french else "One question") if channel == "email" else None
    return subject, "\n\n".join(lines)


def reminder(contact, pulse: dict, risk: dict, token: str, channel: str):
    """One reminder, after 24 hours, with no count in it. Sent at most once, ever, per pulse."""
    french = language_of(contact) == "fr"
    question = (pulse.get("question") or {}).get("text") or "the question we sent"
    line = REMINDER_LINE_FR if french else REMINDER_LINE_EN
    if french:
        body = (f"{line} Si vous avez un avis sur : {question}\n\n{_link(token)}\n\n"
                f"{STOP_LINE_FR}")
    else:
        body = (f"{line} If you have a view on: {question}\n\n{_link(token)}\n\n{STOP_LINE_EN}")
    subject = ("Rappel" if french else "A reminder") if channel == "email" else None
    return subject, body


def how_many_answered(language: str, share: float | None) -> str:
    """Qualitative, and phrased in the reader's own language.

    It takes a share rather than a finished sentence: the API's English `_n_text` used to be
    passed straight in, which put an English first line on top of a French message."""
    if share is None:
        return "Le panel a repondu" if language == "fr" else "The panel answered"
    if language == "fr":
        if share >= 0.9:
            return "Tout le panel a repondu"
        if share >= 0.6:
            return "La plupart du panel a repondu"
        if share >= 0.4:
            return "Environ la moitie du panel a repondu"
        return "Une minorite du panel a repondu"
    if share >= 0.9:
        return "Everyone on the panel answered"
    if share >= 0.6:
        return "Most of the panel answered"
    if share >= 0.4:
        return "About half the panel answered"
    return "A minority of the panel answered"


def closing_the_loop(contact, feedback: dict) -> str:
    """Within 24 hours of the reveal: the group view, their own answer, the band, the decision.

    This is the first and only place an expert sees ACAPS's band, which is why the card can
    promise it is hidden (section 6a)."""
    language = language_of(contact)
    french = language == "fr"
    mean = feedback.get("group_mean")
    yours = (feedback.get("your_answer") or {}).get("probability")
    band = feedback.get("acaps_band") or "not published"
    decision = feedback.get("analyst_decision") or "not decided yet"
    n_text = how_many_answered(language, feedback.get("answered_share"))
    parts = []
    if french:
        parts.append(f"{n_text}.")
        if mean is not None:
            parts.append(f"L'avis du groupe est autour de {mean:.2f}.")
        if yours is not None:
            parts.append(f"Vous avez dit {yours:.2f}.")
        parts.append(f"ACAPS evalue ce risque : {band}.")
        parts.append(f"Decision de l'analyste : {decision}.")
    else:
        parts.append(f"{n_text}.")
        if mean is not None:
            parts.append(f"The group view is around {mean:.2f}.")
        if yours is not None:
            parts.append(f"You said {yours:.2f}.")
        parts.append(f"ACAPS rates this {band}.")
        parts.append(f"The analyst {decision}.")
    attribution = feedback.get("attribution_note")
    if attribution:
        parts.append(attribution)
    return " ".join(parts)


def voice_confirmation(parsed: dict) -> str:
    """Read back what we heard, in one line, with how to correct it.

    A transcription is a guess. Committing one without showing the expert what we heard would put
    a number on the record that they never said."""
    bits = []
    if parsed.get("probability") is not None:
        bits.append(f"{round(parsed['probability'] * 100)} %")
    elif parsed.get("likelihood_word"):
        bits.append(parsed["likelihood_word"].replace("_", " "))
    if parsed.get("stance") and parsed["stance"] != "estimate":
        bits.append(parsed["stance"].replace("_", " "))
    if parsed.get("confidence_word"):
        bits.append(parsed["confidence_word"])
    heard = ", ".join(bits) or "nothing we could read"
    return f"Got it: {heard}. Reply 'no' to correct it before the deadline."
