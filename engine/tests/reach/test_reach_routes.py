"""The Reach routes an analyst drives, and the one claim the whole module rests on.

That claim is that nothing was sent. A delivery view showing eight green ticks for messages that
never left the machine would be the most useful-looking lie in the product, so the transport is
asserted here, on the route, and not only in the module that composes the body.
"""
from __future__ import annotations

from engine.reach import contacts as contact_lib
from helpers import reveal_now


def test_the_status_route_says_what_is_built_and_what_is_merely_recorded(seeded):
    client, _ = seeded
    body = client.get("/api/reach/status").json()
    channels = {row["channel"]: row for row in body["channels"]}
    assert set(channels) == {"email", "whatsapp", "signal", "sms", "teams", "call", "ivr"}
    assert channels["email"]["enabled"] is True
    assert channels["teams"]["enabled"] is False and channels["teams"]["flag"] == "FF_TEAMS"
    assert channels["ivr"]["enabled"] is False and channels["ivr"]["falls_back_to"] == "sms"
    assert all(row["transport"] == "recorded" for row in body["channels"])
    assert "Send anything" in body["does_not"]
    assert body["cadence"]["one_pulse_every_days"] == 7


def test_sending_records_a_message_per_contact_and_names_the_rule_that_refused_the_rest(seeded):
    client, pulse_id = seeded
    body = client.post(f"/api/reach/pulses/{pulse_id}/send", json={}).json()
    assert body["n_sent"] >= 5, "the consented, unpaused contacts are asked"
    assert body["n_refused"] >= 1, "the seeded panel has a stopped and a paused contact"
    reasons = " ".join(row["why"] for row in body["refused"])
    assert "STOP" in reasons or "paused" in reasons
    assert "address book" in reasons, "the stage guests are deliberately outside Reach"
    for row in body["sent"]:
        assert row["transport"] == "recorded"
        assert row["body"] and "/e/" in row["body"]
    assert "No message left this machine" in body["transport_note"]


def test_a_stopped_contact_is_refused_by_name_and_never_sent_to(seeded):
    client, pulse_id = seeded
    body = client.post(f"/api/reach/pulses/{pulse_id}/send", json={}).json()
    stopped = next(row for row in body["refused"] if row["expert_id"] == "X-syn-08")
    assert "replied STOP" in stopped["why"]
    outbox = client.get("/api/reach/outbox", params={"pulse_id": pulse_id}).json()
    assert all(message["expert_id"] != "X-syn-08" for message in outbox["messages"])


def test_a_flagged_off_channel_is_delivered_over_its_fallback_and_the_record_says_so(seeded):
    client, pulse_id = seeded
    client.post(f"/api/reach/pulses/{pulse_id}/send", json={})
    outbox = client.get("/api/reach/outbox", params={"pulse_id": pulse_id, "limit": 100}).json()
    # X-syn-05 prefers Teams, which is flagged off; the message goes by email and says email.
    teams_contact = [m for m in outbox["messages"] if m["expert_id"] == "X-syn-05"]
    assert teams_contact and teams_contact[0]["channel"] == "email"


def test_the_delivery_view_reports_counts_per_channel_and_no_names(seeded):
    client, pulse_id = seeded
    client.post(f"/api/reach/pulses/{pulse_id}/send", json={})
    report = client.get(f"/api/reach/pulses/{pulse_id}/delivery").json()
    assert report["sent"] >= 5
    assert report["channels"] and all("channel" in row for row in report["channels"])
    flat = str(report)
    for name in ("Contact 01", "Contact 02", "example.invalid"):
        assert name not in flat
    assert all(row["transport"] == "recorded" for row in report["channels"])


def test_the_contacts_list_carries_no_name_and_no_address(seeded):
    client, _ = seeded
    body = client.get("/api/reach/contacts").json()
    assert body["n_contacts"] == 8
    flat = str(body)
    assert "Contact 01 (synthetic)" not in flat
    assert "example.invalid" not in flat
    assert all(row["has_address_on_file"] for row in body["contacts"])
    assert body["reachable"] == 6, "one stopped and one paused"


def test_importing_a_csv_adds_contacts_as_invited_and_unconsented(seeded):
    client, _ = seeded
    body = client.post("/api/reach/contacts/import", json={
        "csv": "expert_id,org_type,channel_pref,languages\n"
               "X-new-01,ngo,whatsapp,en;fr\n"}).json()
    assert body["added"] == ["X-new-01"]
    added = next(row for row in client.get("/api/reach/contacts").json()["contacts"]
                 if row["expert_id"] == "X-new-01")
    assert added["status"] == "invited"
    assert added["consent"]["consented_at"] is None
    assert "consent-first" in body["note"]


def test_stop_through_the_route_is_immediate_and_in_the_consent_log(seeded):
    client, _ = seeded
    assert client.post("/api/reach/contacts/X-syn-01/stop", json={}).status_code == 200
    contact = next(row for row in client.get("/api/reach/contacts").json()["contacts"]
                   if row["expert_id"] == "X-syn-01")
    assert contact["status"] == "stopped" and contact["consent"]["stopped_at"]
    log = client.get("/api/reach/consent-log").json()
    assert log["entries"][0]["act"] == "stopped"
    assert log["entries"][0]["expert_id"] == "X-syn-01"


def test_an_analyst_suggestion_cannot_overwrite_an_expert_set_preference(seeded):
    client, _ = seeded
    # X-syn-01 set their own channel in the seed.
    refused = client.post("/api/reach/preferences/X-syn-01",
                          json={"channel_pref": "sms", "by": "suggested_by_analyst"})
    assert refused.status_code == 422
    assert "cannot overwrite" in refused.json()["detail"]
    # X-syn-04's current value is a suggestion, so another suggestion is allowed and stays marked.
    body = client.post("/api/reach/preferences/X-syn-04",
                       json={"channel_pref": "sms", "by": "suggested_by_analyst"}).json()
    assert body["channel_pref"] == "sms"
    assert body["channel_pref_set_by"] == "suggested_by_analyst"
    assert "marked as one" in body["message"]


def test_an_expert_may_set_their_own_preference_through_their_link(seeded):
    client, _ = seeded
    body = client.post("/api/reach/preferences/X-syn-04",
                       json={"channel_pref": "signal", "by": "expert"}).json()
    assert body["channel_pref_set_by"] == "expert"
    assert "own choice" in body["message"]


def test_consent_is_refused_against_an_old_charter(seeded):
    client, _ = seeded
    refused = client.post("/api/reach/contacts/X-syn-01/consent",
                          json={"charter_version": "2020-01-01.1"})
    assert refused.status_code == 422
    assert "does not carry across" in refused.json()["detail"]
    fresh = client.post("/api/reach/contacts/X-syn-01/consent",
                        json={"charter_version": contact_lib.CHARTER_VERSION})
    assert fresh.status_code == 201
    assert "How to stop" in fresh.json()["charter"]


def test_a_scheduled_call_produces_an_invite_and_says_the_answer_must_be_confirmed(seeded):
    client, pulse_id = seeded
    body = client.post("/api/reach/calls/schedule",
                       json={"pulse_id": pulse_id, "expert_id": "X-syn-06"}).json()
    assert "BEGIN:VCALENDAR" in body["ics"] and "DURATION:PT10M" in body["ics"]
    assert body["transport"] == "recorded"
    assert "relayed-confirm" in body["note"]


def test_a_reminder_is_refused_until_the_question_has_had_a_day(seeded):
    client, pulse_id = seeded
    client.post(f"/api/reach/pulses/{pulse_id}/send", json={})
    body = client.post(f"/api/reach/pulses/{pulse_id}/send", json={"kind": "reminder"}).json()
    assert body["n_sent"] == 0
    assert all("due at" in row["why"] or "STOP" in row["why"] or "paused" in row["why"]
               or "address book" in row["why"] for row in body["refused"])


def test_closing_the_loop_goes_only_to_the_experts_who_answered(seeded):
    client, pulse_id = seeded
    reveal_now(client, pulse_id)
    body = client.post(f"/api/reach/pulses/{pulse_id}/close-the-loop").json()
    assert body["n_sent"] >= 1
    channels = set()
    for message in body["sent"]:
        channels.add(message["channel"])
        if message["channel"] == "email":
            # The band appears here and nowhere earlier, which is what lets the card promise it
            # is hidden until after submission. In the reader's own language, including the
            # first line: a French message with an English opening sentence is how a template
            # leaks.
            french = "L'avis du groupe" in message["body"]
            if french:
                assert "ACAPS evalue ce risque : High" in message["body"]
                assert "a repondu" in message["body"]
                assert "Most of the panel" not in message["body"]
            else:
                assert "ACAPS rates this High" in message["body"]
                # The thank-you from engine.impact, not a personal comparison.
                assert message["body"].startswith("Thank you.")
                assert "your answer was part of it" in message["body"]
        else:
            # Chat and SMS: the crisis-level line and the link, nothing a preview could leak.
            assert "/feedback" in message["body"]
            assert "High" not in message["body"]
            assert "group view" not in message["body"].lower()
        # Never the expert's own answer, on any channel.
        assert "You said" not in message["body"]
        assert "Vous avez dit" not in message["body"]
    assert "only the experts who answered" in body["note"].lower()


def test_closing_the_loop_before_a_reveal_is_refused(seeded):
    client, pulse_id = seeded
    refused = client.post(f"/api/reach/pulses/{pulse_id}/close-the-loop")
    assert refused.status_code == 409
    assert "reveal the round" in refused.json()["detail"]
