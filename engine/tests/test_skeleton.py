"""Smoke test: the loop runs end to end against the seeded synthetic panel."""
from __future__ import annotations

from helpers import reveal_now


def test_health_and_risk_routes(seeded):
    client, _ = seeded
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/risks/R1043").json()["risk_id"] == "R1043"
    assert client.get("/api/radar/status").json()["source"] == "csv"


def test_full_loop(seeded):
    client, pulse_id = seeded

    # The seeded round's deadline is 24 hours out, so this is the recorded analyst override and
    # the result says so (helpers.reveal_now).
    revealed = reveal_now(client, pulse_id).json()
    assert revealed["n"] >= 5
    assert revealed["revealed_reason"] == "analyst_before_deadline"

    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    assert drafted["status"] == "draft"

    client.post("/api/risks/R1043/contract", json={
        "event": "Sustained cross-border attacks on eastern Chad border localities",
        "location": "Ouaddai, Chad",
        "horizon_deadline": "2027-05-07",
        "resolution_source": "ACAPS Risk Radar status field",
        "adjudication_rule": "Materialised if ACAPS marks it so by the deadline.",
    })
    decided = client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept",
        "what_decision": "Pre-position shelter and cash in Ouaddai",
        "for_whom": "NGO preparedness lead, eastern Chad",
        "by_when": "2026-11-20",
    }).json()
    assert decided["status"] == "accepted"

    resolved = client.post("/api/risks/R1043/resolve", json={"outcome": "materialised"}).json()
    assert resolved["scores_written"] > 0


def test_every_response_carries_provenance(seeded):
    client, pulse_id = seeded
    for path in ("/api/risks", "/api/risks/R1043", "/api/radar/status",
                 f"/api/pulses/{pulse_id}", "/api/ledger"):
        body = client.get(path).json()
        assert body["served_from"] == "live", path
        assert body["generated_at"], path
