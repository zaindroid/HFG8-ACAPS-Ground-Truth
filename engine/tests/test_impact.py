"""The thank-you message: what an expert's minute changed, from the record only, never a verdict."""
from __future__ import annotations

import re

from helpers import commit_answer, open_token, reveal_now


def _decided(client, pulse_id):
    reveal_now(client, pulse_id)
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "what_decision": "preparedness planning for Ouaddai and Wadi Fira",
        "for_whom": "UNHCR Chad", "by_when": "15 December", "note": "kept High; Adre added to triggers"})


def _answered_link(client, pulse_id):
    from engine.api import STORE
    token = open_token(STORE, pulse_id)
    assert commit_answer(client, token).status_code == 201
    return token


def test_feedback_does_not_show_the_experts_own_answer_by_default(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    feedback = client.get(f"/api/e/{token}/feedback").json()
    assert feedback["your_answer"] is None
    assert client.get(f"/api/e/{token}/feedback", params={"show_mine": True}).json()["your_answer"]


def test_thank_you_says_what_changed_and_for_whom(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    text = client.get(f"/api/e/{token}/feedback").json()["impact"]["text"]
    assert text.startswith("Thank you.")
    assert "UNHCR Chad" in text and "15 December" in text
    assert "Adre added to triggers" in text


def test_scale_uses_acaps_exposure_figure_never_a_score_as_headcount(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    impact = client.get(f"/api/e/{token}/feedback").json()["impact"]
    assert "more than 500,000 people to be exposed" in impact["text"]
    assert impact["facts"]["scale"]["exposure"]["source"] == "ACAPS Risk List, expected exposure"
    assert "people in need" not in impact["text"]


def test_thank_you_never_claims_lives_saved_or_scores_a_person(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    text = client.get(f"/api/e/{token}/feedback").json()["impact"]["text"].lower()
    for word in ("saved", "lives", "you were right", "you were wrong", "your score", "you said", "rank"):
        assert word not in text
    assert not re.search(r"brier", text)


def test_analyst_note_must_be_written_and_is_quoted(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    assert client.post(f"/api/pulses/{pulse_id}/thanks", json={"text": " "}).status_code == 422
    client.post(f"/api/pulses/{pulse_id}/thanks",
                json={"text": "Your note on the Adre crossings reached us before any report did.", "by": "Alex, ACAPS"})
    text = client.get(f"/api/e/{token}/feedback").json()["impact"]["text"]
    assert "Adre crossings" in text and "Alex, ACAPS" in text


def test_reach_appears_only_when_acaps_supplies_it(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    assert "read by" not in client.get(f"/api/e/{token}/feedback").json()["impact"]["text"]
    client.post(f"/api/pulses/{pulse_id}/reach", json={"organisations": 340})
    assert "340 organisations" in client.get(f"/api/e/{token}/feedback").json()["impact"]["text"]


def test_outcome_reports_can_be_switched_off_by_the_expert(seeded):
    client, pulse_id = seeded
    token = _answered_link(client, pulse_id)
    _decided(client, pulse_id)
    before = client.get(f"/api/pulses/{pulse_id}/outcome-report").json()["recipients"]
    assert client.post(f"/api/e/{token}/reports-off").json()["reports_on"] is False
    after = client.get(f"/api/pulses/{pulse_id}/outcome-report").json()["recipients"]
    assert after == before - 1
