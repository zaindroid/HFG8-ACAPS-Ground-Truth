"""The Risk Alert Engine (section 6b).

The four tests the master prompt names, plus the boundary that matters most: the engine proposes, the
analyst decides. Nothing here may open a round by itself.
"""
from __future__ import annotations

import pytest

from engine import acaps, alerts as alert_engine


@pytest.fixture()
def engine():
    store = alert_engine.new_store()
    alert_engine.confirm_link(store, "R1043", "TCD005", "test")
    return store


# -- the four tests section 6b asks for ----------------------------------------
def test_march_to_april_yields_tcd005_as_rank_one_with_delta_point_eight(engine):
    result = alert_engine.run(engine, "Mar2026", "Apr2026")
    assert result["n_crises"] == 123
    event = next(e for e in result["events"] if e["crisis_id"] == "TCD005")
    assert event["metric"] == "index"
    assert event["before"] == 6.1 and event["after"] == 6.9
    assert event["delta"] == pytest.approx(0.8)
    assert event["rank_this_month"] == 1
    assert event["n_crises_this_month"] == 123
    assert event["risk_id"] == "R1043"
    assert event["rule_hit"] == "index delta >= 0.5"
    # The components the pitch quotes, from the same edition.
    assert event["components"]["human_impact"] == [6.04, 7.57]


def test_a_month_with_no_moves_yields_no_events():
    """Oct2026 -> Nov2026: ACAPS republished the same figures, so an honest engine says nothing."""
    result = alert_engine.run(alert_engine.new_store(), "Oct2026", "Nov2026")
    assert result["n_crises"] == 122
    assert result["events"] == []
    assert "No crisis moved enough" in result["note"]


def test_the_same_edition_diffed_twice_yields_no_duplicate_events(engine):
    first = alert_engine.run(engine, "Mar2026", "Apr2026")
    count_after_first = len(engine.events)
    second = alert_engine.run(engine, "Mar2026", "Apr2026")
    assert len(engine.events) == count_after_first
    assert {e["id"] for e in first["events"]} == {e["id"] for e in second["events"]}


def test_a_dismissed_event_never_pulses(seeded):
    client, _ = seeded
    replay = client.post("/api/alerts/replay", json={"month_from": "Mar2026", "month_to": "Apr2026"}).json()
    event = next(e for e in replay["events"] if e["crisis_id"] == "TCD005")

    bare = client.post(f"/api/alerts/{event['id']}/dismiss", json={})
    assert bare.status_code == 422, "dismissing without a reason should be refused"

    client.post(f"/api/alerts/{event['id']}/dismiss", json={"note": "Already covered by the open round."})
    refused = client.post(f"/api/alerts/{event['id']}/pulse")
    assert refused.status_code == 409
    assert "dismissed" in refused.json()["detail"]


# -- propose, never fire -------------------------------------------------------
def test_running_the_engine_creates_no_pulse(seeded):
    client, _ = seeded
    before = len(client.get("/api/alerts").json()["events"])
    result = client.post("/api/alerts/replay", json={"month_from": "Mar2026", "month_to": "Apr2026"}).json()
    assert result["events"], "the April replay should propose something"
    assert all(e["status"] == "proposed" for e in result["events"])
    assert all(e["pulse_id"] is None for e in result["events"])
    assert len(client.get("/api/alerts").json()["events"]) >= before


def test_an_approved_alert_becomes_a_pulse_carrying_its_own_numbers(seeded):
    client, _ = seeded
    replay = client.post("/api/alerts/replay", json={"month_from": "Mar2026", "month_to": "Apr2026"}).json()
    event = next(e for e in replay["events"] if e["crisis_id"] == "TCD005")

    approved = client.post(f"/api/alerts/{event['id']}/pulse")
    assert approved.status_code == 201
    body = approved.json()
    assert body["status"] == "pulsed"
    assert body["pulse_id"] == body["pulse"]["id"]

    evidence = body["pulse"]["evidence"]
    assert evidence, "the pulse must carry the event's numbers as its evidence"
    headline = evidence[0]
    assert headline["baseline"] == 6.1 and headline["value"] == 6.9
    assert "rank 1 of 123" in headline["note"]
    assert "Very High" in headline["note"], "the edition's reliability belongs next to the event"

    again = client.post(f"/api/alerts/{event['id']}/pulse")
    assert again.status_code == 409, "approving the same event twice should not open a second round"


def test_an_event_with_no_linked_risk_cannot_be_pulsed(seeded):
    client, _ = seeded
    replay = client.post("/api/alerts/replay", json={"month_from": "Mar2026", "month_to": "Apr2026"}).json()
    unlinked = next(e for e in replay["events"] if e["risk_id"] is None)
    refused = client.post(f"/api/alerts/{unlinked['id']}/pulse")
    assert refused.status_code == 422
    assert "link" in refused.json()["detail"]


# -- ranking is honest ---------------------------------------------------------
def test_an_improvement_is_ranked_as_an_improvement_not_as_the_top_alert(engine):
    """PAK007 fell 0.9, a bigger absolute move than TCD005's 0.8. It must not head the queue of a
    system whose job is to notice things getting worse -- and its own rank must say which it is."""
    result = alert_engine.run(engine, "Mar2026", "Apr2026")
    index_events = [e for e in result["events"] if e["metric"] == "index"]
    assert index_events[0]["crisis_id"] == "TCD005"

    pak = next(e for e in result["events"] if e["crisis_id"] == "PAK007")
    assert pak["direction"] == "improvement"
    assert pak["rank_this_month"] == 1
    assert "improvement" in pak["rule_hit"]
    # The absolute-delta ordering is recorded rather than hidden: PAK007 did move furthest.
    assert pak["rank_by_abs_delta"] == 1
    tcd = next(e for e in result["events"] if e["crisis_id"] == "TCD005")
    assert tcd["rank_by_abs_delta"] == 2


def test_ranks_are_never_compared_across_different_metrics(engine):
    """A 1.75 move in a sub-component is not 'bigger' than a 0.8 move in the headline index."""
    result = alert_engine.run(engine, "Mar2026", "Apr2026")
    for metric in {e["metric"] for e in result["events"]}:
        for direction in ("deterioration", "improvement"):
            group = [e for e in result["events"] if e["metric"] == metric and e["direction"] == direction]
            assert sorted(e["rank_this_month"] for e in group) == list(range(1, len(group) + 1))


# -- linking -------------------------------------------------------------------
def test_r1043_links_to_tcd005_on_iso3_plus_driver():
    suggestions = [s for s in alert_engine.suggest_links() if s["risk_id"] == "R1043"]
    assert any(s["crisis_id"] == "TCD005" for s in suggestions)
    tcd = next(s for s in suggestions if s["crisis_id"] == "TCD005")
    assert tcd["how"] == "iso3+driver"
    assert "displacement" in tcd["matched_on"]


def test_linking_requires_a_real_risk_and_a_real_crisis(seeded):
    client, _ = seeded
    assert client.post("/api/risks/R1043/link", json={"crisis_id": "NOPE999"}).status_code == 404
    assert client.post("/api/risks/NOPE/link", json={"crisis_id": "TCD005"}).status_code == 404
    assert client.post("/api/risks/R1043/link", json={}).status_code == 422
    ok = client.post("/api/risks/R1043/link", json={"crisis_id": "TCD005"})
    assert ok.status_code == 201 and ok.json()["how"] == "analyst"


# -- the data layer ------------------------------------------------------------
def test_editions_are_served_from_the_cache_and_say_so(seeded):
    client, _ = seeded
    status = client.get("/api/radar/status").json()
    assert status["token_present"] is False
    assert status["risk_list"]["source"] == "csv"
    assert status["risk_list"]["n"] == 139
    datasets = {e["dataset"]: e for e in status["editions"]}
    assert datasets["inform-severity-index"]["source"] == "cache"
    assert datasets["inform-severity-index"]["month"] == "Nov2026"


def test_crisis_series_skips_months_rather_than_inventing_them():
    series = acaps.series("TCD005")
    months = [p["month"] for p in series]
    assert months == ["Mar2026", "Apr2026", "Oct2026", "Nov2026"], (
        "only cached months should appear; a publishing gap is not a flat line"
    )
    values = {p["month"]: p["index"] for p in series}
    assert values["Mar2026"] == 6.1 and values["Apr2026"] == 6.9


def test_crisis_endpoint_carries_the_link_and_the_admin_areas(seeded):
    client, _ = seeded
    client.post("/api/risks/R1043/link", json={"crisis_id": "TCD005"})
    body = client.get("/api/crises/TCD005").json()
    assert body["crisis_name"] == "Displacement from Sudan to Chad"
    assert "R1043" in body["linked_risks"]
    assert "Ouaddaï" in body["adm1_name"]
    assert "SDN001" in body["connected_crises"]
    assert client.get("/api/crises/NOPE999").status_code == 404


def test_only_crises_present_in_both_editions_are_diffed():
    """Mar has 140 rows and Apr has 126; a crisis that appears or disappears is not a severity change."""
    march = acaps.edition(acaps.INFORM, "Mar2026")
    april = acaps.edition(acaps.INFORM, "Apr2026")
    assert len(march) == 140 and len(april) == 126
    rows = alert_engine.diff_months("Mar2026", "Apr2026")
    assert len(rows) == len(set(march) & set(april)) == 123
