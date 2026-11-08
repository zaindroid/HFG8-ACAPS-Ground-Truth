"""An answer that arrives as a reply, through the routes it actually arrives through.

The parser is asked the things people really send: a keypad digit, a percentage, a spelled-out
number in French, an abstention with a stray figure in the same sentence, and a STOP buried in a
polite refusal. Then the route is asked whether a reply commits, whether a second reply corrects,
and whether a reply nobody can read is dropped.
"""
from __future__ import annotations

import pytest

from engine.inbound import parse
from helpers import open_token, reveal_now


# -- the parser ----------------------------------------------------------------
@pytest.mark.parametrize("text, word", [
    ("4 likely", "likely"),
    ("press 2", "unlikely"),
    ("even, nothing moved this week", "even"),
    ("tres probable", "very_likely"),
    ("very unlikely I'm afraid", "very_unlikely"),
])
def test_a_keypad_or_a_word_reads_as_a_likelihood(text, word):
    assert parse(text, "sms").likelihood_word == word


@pytest.mark.parametrize("text, probability", [
    ("70 %", 0.7),
    ("0.35", 0.35),
    ("seventy percent", 0.7),
    ("soixante-dix pour cent", 0.7),
    ("30", 0.3),
])
def test_a_number_reads_as_a_probability_in_the_forms_people_send(text, probability):
    assert parse(text, "whatsapp").probability == pytest.approx(probability)


def test_a_spelled_number_is_not_read_as_the_shorter_one_inside_it():
    """soixante-dix is seventy, not ten. The hyphen is a word boundary, so the short match fires
    too unless the long one is tried first."""
    assert parse("soixante-dix", "sms").probability == pytest.approx(0.7)


def test_seventy_is_not_read_as_a_fifty_fifty_answer():
    """'seventy' contains 'even'. A substring match read a 70 % answer as the word 'even'."""
    parsed = parse("seventy percent", "email")
    assert parsed.probability == pytest.approx(0.7)
    assert parsed.likelihood_word is None


def test_an_abstention_is_not_overruled_by_a_number_in_the_same_sentence():
    parsed = parse("Outside my area, but I hear 80% from colleagues", "email")
    assert parsed.stance == "outside_my_expertise"
    assert parsed.probability is None, "an abstention is a complete answer, not a prelude to one"


@pytest.mark.parametrize("text", ["pas mon domaine", "not my field", "wrong person"])
def test_an_abstention_is_read_in_either_language(text):
    assert parse(text, "sms").stance == "outside_my_expertise"


def test_a_stop_word_is_read_before_anything_else_in_the_reply():
    parsed = parse("stop, wrong person, maybe 80%", "sms")
    assert parsed.act == "stop"
    assert parsed.probability is None, "somebody opting out has not given an answer"


def test_a_pause_word_pauses_rather_than_stopping():
    assert parse("pause please, travelling", "whatsapp").act == "pause"


def test_a_number_and_a_word_that_disagree_keep_the_number_and_say_so():
    parsed = parse("unlikely 90%", "email")
    assert parsed.probability == pytest.approx(0.9)
    assert parsed.likelihood_word is None
    assert any("did not match" in note for note in parsed.not_read)


def test_a_mask_word_and_a_free_line_survive_the_number():
    parsed = parse("0.35 and keep me anonymous, camps are past capacity", "whatsapp")
    assert parsed.mask == "anonymous"
    assert parsed.missing == "camps are past capacity"


def test_a_reply_nobody_can_read_keeps_the_original_and_asks_for_the_analyst():
    parsed = parse("Thanks, I'll look into it and come back to you", "email")
    assert parsed.needs_analyst is True
    assert parsed.original.startswith("Thanks, I'll look")
    assert parsed.not_read


def test_an_empty_reply_is_unreadable_rather_than_an_answer():
    assert parse("", "sms").needs_analyst is True


# -- the route -----------------------------------------------------------------
def _as_contact(client, store, pulse_id: str) -> tuple[str, str]:
    """An open link whose expert is in the address book.

    The seeded panel has all eight answers in, so the open links belong to the stage guests --
    walk-ups with no consent and deliberately outside Reach. Adding one through the route is what
    an analyst actually does, and it exercises the path: add, consent, then reply."""
    from engine.reach import contacts as contact_lib

    token = open_token(store, pulse_id)
    _, expert_id = store.tokens[token]
    client.post("/api/reach/contacts", json={
        "expert_id": expert_id, "display_name": "Added by the analyst (synthetic)",
        "org_type": "ngo", "coverage_area": "eastern Chad", "channel_pref": "sms",
        "charter_version": contact_lib.CHARTER_VERSION,
    })
    return token, expert_id



def test_a_typed_reply_commits_where_a_link_click_does_not(seeded):
    """A link click reaches a draft; a reply is a deliberate act and commits. The difference is
    the whole reason POST /answer was split in two."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    before = STORE.n_answers(pulse_id)
    response = client.post("/api/inbound/sms", json={"token": token, "text": "4 likely"})
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True and body["act"] == "committed"
    assert body["commitment"] and body["version"] == 1
    assert STORE.n_answers(pulse_id) == before + 1


def test_a_second_reply_before_the_deadline_corrects_rather_than_being_refused(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    client.post("/api/inbound/sms", json={"token": token, "text": "4 likely"})
    second = client.post("/api/inbound/sms", json={"token": token, "text": "actually 40%"})
    assert second.status_code == 200
    body = second.json()
    assert body["act"] == "corrected" and body["version"] == 2
    _, expert_id = STORE.tokens[token]
    answer = STORE.find_answer(pulse_id, expert_id, None)
    assert answer.probability == pytest.approx(0.4)
    assert answer.previous_versions, "the first reply is kept"


def test_a_stop_in_a_reply_stops_the_contact_and_records_no_answer(seeded):
    client, pulse_id = seeded
    from engine.api import REACH, STORE

    token, expert_id = _as_contact(client, STORE, pulse_id)
    before = STORE.n_answers(pulse_id)
    response = client.post("/api/inbound/whatsapp",
                           json={"token": token, "text": "stop, not the right person"})
    assert response.json()["act"] == "stop"
    assert REACH.book.require(expert_id).status == "stopped"
    assert STORE.n_answers(pulse_id) == before
    assert REACH.book.consent_log[-1]["act"] == "stopped"


def test_an_unreadable_reply_goes_to_the_analyst_with_its_original_text(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    before = STORE.n_answers(pulse_id)
    body = client.post("/api/inbound/email",
                       json={"token": token, "text": "Happy to help, call me"}).json()
    assert body["accepted"] is False and body["needs_analyst"] is True
    assert body["parsed"]["original"] == "Happy to help, call me"
    assert STORE.n_answers(pulse_id) == before, "nothing is guessed at"


def test_a_reply_on_an_unresolvable_link_is_held_rather_than_dropped(seeded):
    client, _ = seeded
    body = client.post("/api/inbound/email",
                       json={"token": "not-a-token", "text": "70%"}).json()
    assert body["accepted"] is False and body["needs_analyst"] is True
    assert body["parsed"]["probability"] == pytest.approx(0.7), "we still read what they sent"


def test_a_voice_note_is_read_back_before_it_can_stand(seeded):
    """A transcription is a guess. Committing one silently puts a number on the record that the
    expert never said, so the response carries the line they have to be shown."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    body = client.post("/api/inbound/voice",
                       json={"token": token,
                             "transcript": "I'd say about seventy percent, fairly sure"}).json()
    assert body["act"] == "committed"
    assert "Got it: 70 %" in body["read_back"]
    assert "Reply 'no' to correct" in body["read_back"]
    assert body["transcript_source"] == "the request", "this build has no speech model"


def test_a_reply_after_the_deadline_is_refused(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    STORE.pulses[pulse_id]["expires_at"] = "2020-01-01T00:00:00+00:00"
    response = client.post("/api/inbound/sms", json={"token": token, "text": "4 likely"})
    assert response.status_code == 409
    assert "closed at" in response.json()["detail"]


def test_an_answer_that_arrived_by_reply_is_in_the_channel_mix_on_the_ledger(seeded):
    client, pulse_id = seeded
    from engine.api import REACH, STORE

    token, _ = _as_contact(client, STORE, pulse_id)
    client.post(f"/api/reach/pulses/{pulse_id}/send", json={})
    client.post("/api/inbound/sms", json={"token": token, "text": "4 likely"})
    reveal_now(client, pulse_id)
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "decision_use": {"what_decision": "d", "for_whom": "w",
                                             "by_when": "2026-12-01"}})
    honesty = client.get("/api/ledger").json()["entries"][0]["honesty"]
    assert honesty["channel_mix"], "the public record says how the answers arrived"
    assert sum(honesty["channel_mix"].values()) >= 1
    assert REACH.delivery_report(pulse_id)["answered"] >= 1
