"""Section 6e: what Reach promises an expert, and what it refuses to pretend.

These tests exist because the promises are the product. "One question a week" is only true if
something refuses the second one; "STOP within the hour" is only true if the stop is immediate
and recorded; and "nothing on a lock screen" is only true if a body carrying the band is refused
rather than sent.
"""
from __future__ import annotations

import pytest

from engine.reach import cadence, channels, contacts, messages

RISK = {
    "risk_id": "R1043", "country": "Chad",
    "title": "Escalating cross-border insecurity increases protection risks in eastern Chad",
    "probability_acaps": "High", "level": "High",
    "adm1_name": ["Ouaddai", "Wadi Fira", "Sila"],
}
PULSE = {
    "id": "P-0001", "risk_id": "R1043", "asked_by": "Alex, ACAPS Risk Radar",
    # The real frozen question for the demo risk, provinces included. An earlier version of this
    # fixture left them out, so the preview test below passed without ever exercising the case
    # it exists for.
    "question": {"text": "Will more than 50,000 new arrivals from Sudan be registered in "
                         "Ouaddai and Wadi Fira by 31 March 2027?",
                 "deadline": "2027-03-31"},
}


def _contact(**overrides) -> contacts.Contact:
    base = {"expert_id": "X-01", "display_name": "Contact (synthetic)",
            "coverage_area": "the Chad-Sudan border", "channel_pref": "email"}
    return contacts.Contact(**{**base, **overrides})


# -- the body on a lock screen -------------------------------------------------
def test_a_message_naming_the_acaps_band_is_refused():
    with pytest.raises(messages.Unsafe, match="names the band"):
        messages.assert_lock_screen_safe("ACAPS rates this High. Do you agree?", RISK)


def test_a_message_naming_a_province_is_refused():
    with pytest.raises(messages.Unsafe, match="Ouaddai"):
        messages.assert_lock_screen_safe("Arrivals in Ouaddai have doubled.", RISK)


def test_a_message_carrying_a_severity_number_is_refused():
    with pytest.raises(messages.Unsafe, match="severity number"):
        messages.assert_lock_screen_safe("The index moved from 6.1 to 6.9.", RISK)


def test_the_composed_pulse_message_passes_the_lock_screen_check():
    for channel in ("email", "whatsapp", "sms", "signal"):
        _, body = messages.pulse_message(_contact(channel_pref=channel), PULSE, RISK, "tok",
                                         channel)
        messages.assert_lock_screen_safe(body, RISK, PULSE["question"]["text"])
        assert "tok" in body


def test_the_subject_and_the_opening_line_name_a_country_and_not_a_province():
    """What is actually guaranteed, stated exactly.

    The subject is held to the rule with no exemption: it carries no province, no rating and no
    severity number. The body opens with the crisis-level line, so the first thing read is a
    country and a subject. The frozen question follows, and it does name provinces, because
    ACAPS's own published risk does and the expert has to see the question they are answering. So
    a long preview on a large screen can show them -- and an SMS is one line, so its whole
    message is the preview. That is the limit of this guarantee, and saying it holds for every
    channel and every preview length would be a claim the code does not make good on."""
    for channel in ("email", "whatsapp", "sms", "signal"):
        subject, body = messages.pulse_message(_contact(channel_pref=channel), PULSE, RISK,
                                               "tok", channel)
        if subject:
            messages.assert_lock_screen_safe(subject, RISK)
            for area in RISK["adm1_name"]:
                assert area not in subject, f"{channel}: the subject showed {area}"
        # The first sentence, not the first line: an SMS is one line, so its whole message is
        # the preview. What holds on every channel is that the message *begins* at crisis level.
        opening = body.split(".")[0]
        assert "Chad" in opening, f"{channel}: the body does not open at crisis level"
        for area in RISK["adm1_name"]:
            assert area not in opening, f"{channel}: the opening sentence showed {area}"
        # And a province appears nowhere except inside the frozen question itself.
        without_question = body.replace(PULSE["question"]["text"], " ")
        for area in RISK["adm1_name"]:
            assert area not in without_question, \
                f"{channel}: {area} appears outside the frozen question"
        assert "High" not in body and "6.1" not in body


def test_the_frozen_question_is_exempt_but_nothing_around_it_is():
    question = PULSE["question"]["text"]
    messages.assert_lock_screen_safe(f"About the situation. {question}", RISK, question)
    with pytest.raises(messages.Unsafe):
        messages.assert_lock_screen_safe(f"Ouaddai again. {question}", RISK, question)


def test_the_crisis_line_names_the_country_and_no_province():
    line = messages.crisis_line(RISK)
    assert "Chad" in line
    for area in RISK["adm1_name"]:
        assert area not in line


# -- the first contact ---------------------------------------------------------
# -- closing the loop: the thank-you, never the expert's own answer --------------
FEEDBACK = {
    "group_mean": 0.62, "answered_share": 0.75, "acaps_band": "High",
    "analyst_decision": "accepted",
    # A caller that still passes the expert's own answer must not get it printed.
    "your_answer": {"probability": 0.81},
    "impact": {"text": "Thank you. Most of the panel answered, and your answer was part of it. "
                       "ACAPS used the panel's input in its update."},
}


def test_closing_the_loop_never_shows_the_experts_own_answer():
    for channel in ("email", "whatsapp", "signal", "sms", "teams", "call"):
        for languages in (["en"], ["fr"]):
            body = messages.closing_the_loop(_contact(channel_pref=channel, languages=languages),
                                             FEEDBACK, channel=channel, risk=RISK, token="tok")
            assert "0.81" not in body
            assert "You said" not in body and "Vous avez dit" not in body


def test_closing_the_loop_by_email_carries_the_impact_message_and_the_band():
    body = messages.closing_the_loop(_contact(), FEEDBACK, channel="email", risk=RISK,
                                     token="tok")
    assert body.startswith(FEEDBACK["impact"]["text"])
    assert "ACAPS rates this High." in body
    assert "/e/tok/feedback" in body


def test_closing_the_loop_without_an_impact_message_is_group_only():
    feedback = {k: v for k, v in FEEDBACK.items() if k != "impact"}
    body = messages.closing_the_loop(_contact(), feedback, channel="email", risk=RISK,
                                     token="tok")
    assert body.startswith("Most of the panel answered.")
    assert "The group view is around 0.62." in body
    assert "0.81" not in body


def test_closing_the_loop_on_chat_and_sms_is_only_the_crisis_line_and_the_link():
    for channel in ("whatsapp", "signal", "sms", "teams"):
        body = messages.closing_the_loop(_contact(channel_pref=channel), FEEDBACK,
                                         channel=channel, risk=RISK, token="tok")
        messages.assert_lock_screen_safe(body, RISK)
        assert messages.crisis_line(RISK) in body
        assert body.endswith("/e/tok/feedback")
        assert "Thank you" not in body and "0.62" not in body


def test_first_contact_carries_the_charter_the_reason_and_the_opt_out():
    _, body = messages.first_contact(_contact(), PULSE, RISK, "tok", "email")
    assert "Alex, ACAPS Risk Radar" in body
    assert "the Chad-Sudan border" in body, "why this expert, in their own terms"
    assert "What we ask" in body and "How to stop" in body, "the charter, in the same message"
    assert "STOP" in body
    assert PULSE["question"]["text"] in body, "the question is in the first message, not a later one"


def test_first_contact_is_in_french_for_a_french_only_contact():
    _, body = messages.first_contact(_contact(languages=["fr"]), PULSE, RISK, "tok", "email")
    assert "Bonjour" in body and "Repondez STOP" in body


# -- the reminder --------------------------------------------------------------
def test_the_reminder_never_carries_a_count():
    _, body = messages.reminder(_contact(), PULSE, RISK, "tok", "email")
    assert messages.REMINDER_LINE_EN in body
    for count in ("1 of", "2 of", "3 of", "4 of", "5 of", "6 of", "7 of", "8 of",
                  "four", "five", "six", "seven"):
        assert count not in body.lower(), f"a reminder saying '{count}' tells the reader how to " \
                                          "be the fifth"


def test_the_email_pulse_gives_one_link_per_word_and_says_a_tap_commits_nothing():
    _, body = messages.pulse_message(_contact(), PULSE, RISK, "tok", "email")
    for word in ("very_unlikely", "unlikely", "even", "likely", "very_likely"):
        assert f"word={word}" in body
    assert "Nothing is recorded until you do" in body


def test_the_sms_pulse_fits_one_message_and_offers_a_numeric_reply():
    _, body = messages.pulse_message(_contact(channel_pref="sms"), PULSE, RISK, "tok", "sms")
    assert "Reply 1-5" in body
    assert len(body) < 480, "an SMS that spills into four parts is not an SMS"


# -- cadence -------------------------------------------------------------------
def test_a_second_pulse_inside_seven_days_is_refused_with_the_eligible_date():
    from engine.reach import Delivery

    history = [Delivery(pulse_id="P-0001", expert_id="X-01", channel="email", kind="pulse",
                        scheduled_for="now", sent_at=contacts.now())]
    with pytest.raises(cadence.Refused, match="eligible again"):
        cadence.check(_contact(), history, "pulse")


def test_a_stopped_contact_is_sent_nothing_including_a_reminder():
    contact = _contact(status="stopped", stopped_at=contacts.now())
    for kind in ("pulse", "first_contact", "reminder"):
        with pytest.raises(cadence.Refused, match="replied STOP"):
            cadence.check(contact, [], kind)


def test_a_paused_contact_is_sent_nothing_until_the_pause_ends():
    book = contacts.Book()
    book.add(_contact())
    book.pause("X-01")
    with pytest.raises(cadence.Refused, match="paused until"):
        cadence.check(book.require("X-01"), [], "pulse")


def test_a_reminder_before_twenty_four_hours_is_refused():
    from engine.reach import Delivery

    history = [Delivery(pulse_id="P-0001", expert_id="X-01", channel="email", kind="pulse",
                        scheduled_for="now", sent_at=contacts.now())]
    with pytest.raises(cadence.Refused, match="due at"):
        cadence.check(_contact(), history, "reminder")


def test_there_is_never_a_third_message():
    from datetime import datetime, timedelta, timezone

    from engine.reach import Delivery

    old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(timespec="seconds")
    history = [
        Delivery(pulse_id="P-0001", expert_id="X-01", channel="email", kind="pulse",
                 scheduled_for=old, sent_at=old),
        Delivery(pulse_id="P-0001", expert_id="X-01", channel="email", kind="reminder",
                 scheduled_for=old, sent_at=old),
    ]
    with pytest.raises(cadence.Refused, match="never sends a third"):
        cadence.check(_contact(), history, "reminder")


def test_the_send_time_is_the_experts_own_hour_and_not_friday_afternoon():
    from datetime import datetime

    when = datetime.fromisoformat(cadence.next_send_time(
        _contact(hour_pref=7, utc_offset_hours=1)))
    local = when.hour + 1
    assert local % 24 == 7
    assert when.weekday() not in (5, 6), "nobody on this panel owes us a Saturday"
    assert not (when.weekday() == cadence.FRIDAY and local >= cadence.FRIDAY_CUTOFF_HOUR)


def test_an_escalating_alert_may_send_on_a_friday_afternoon():
    """The one override, and it belongs to the alert rather than to whoever is sending."""
    from datetime import datetime

    escalating = datetime.fromisoformat(cadence.next_send_time(
        _contact(hour_pref=16, utc_offset_hours=0), escalating=True))
    assert escalating.weekday() in range(7)


# -- the address book ----------------------------------------------------------
def test_stop_is_immediate_and_recorded():
    book = contacts.Book()
    book.add(_contact())
    contact = book.stop("X-01", "stop, wrong person")
    assert contact.status == "stopped" and contact.stopped_at
    entry = book.consent_log[-1]
    assert entry == {"expert_id": "X-01", "act": "stopped", "said": "stop, wrong person",
                     "at": contact.stopped_at}


def test_an_analyst_cannot_overwrite_a_preference_the_expert_set():
    book = contacts.Book()
    book.add(_contact())
    book.set_preferences("X-01", {"channel_pref": "whatsapp"}, "expert")
    with pytest.raises(contacts.Refused, match="cannot overwrite"):
        book.set_preferences("X-01", {"channel_pref": "sms"}, "suggested_by_analyst")
    assert book.require("X-01").channel_pref == "whatsapp"


def test_an_analyst_suggestion_is_marked_as_a_suggestion():
    book = contacts.Book()
    book.add(_contact(preferences_set_by="suggested_by_analyst"))
    contact = book.set_preferences("X-01", {"channel_pref": "sms"}, "suggested_by_analyst")
    assert contact.channel_pref == "sms"
    assert contact.public_view()["channel_pref_set_by"] == "suggested_by_analyst"


def test_consent_does_not_carry_across_a_charter_change():
    book = contacts.Book()
    book.add(_contact())
    with pytest.raises(contacts.Refused, match="does not carry across"):
        book.record_consent("X-01", "2020-01-01.1")
    assert book.require("X-01").consented_at is None


def test_a_contact_never_carries_a_physical_location_or_a_name_to_the_desk():
    book = contacts.Book()
    book.add(_contact(display_name="A Real Name", address="someone@example.invalid"))
    view = book.require("X-01").public_view()
    assert "A Real Name" not in str(view)
    assert "someone@example.invalid" not in str(view)
    assert view["has_address_on_file"] is True
    assert "coverage_area" in view and "location" not in view


def test_importing_contacts_reports_the_rows_it_could_not_read():
    book = contacts.Book()
    report = book.import_csv(
        "expert_id,org_type,channel_pref,theme_tags\n"
        "X-99,ngo,email,conflict;access\n"
        ",ngo,email,conflict\n"
        "X-98,ngo,carrier-pigeon,conflict\n")
    assert report["added"] == ["X-99"]
    assert len(report["skipped"]) == 2
    assert any("expert_id" in row["why"] for row in report["skipped"])
    assert any("channel_pref" in row["why"] for row in report["skipped"])
    assert book.require("X-99").theme_tags == ["conflict", "access"]


# -- channels ------------------------------------------------------------------
def test_a_flagged_off_channel_falls_back_and_says_which():
    assert channels.enabled("teams") is False
    assert channels.resolve("teams") == "email"
    assert channels.resolve("ivr") == "sms"
    teams = next(row for row in channels.status() if row["channel"] == "teams")
    assert teams["falls_back_to"] == "email"
    assert "app registration" in teams["off_note"]


def test_every_channel_reports_that_nothing_was_sent():
    for row in channels.status():
        assert row["transport"] == "recorded"
    assert "No message left this machine" in channels.TRANSPORT_NOTE
