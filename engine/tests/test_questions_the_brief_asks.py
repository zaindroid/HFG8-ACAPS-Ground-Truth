"""The questions this solution is supposed to answer, one test each.

The challenge brief sets one worked question -- "What are the three biggest risks in Chad
that might worsen humanitarian outcomes in the next six months?" -- and the master prompt
sets the rest through the loop it describes. Each test below is named for the question it
proves the product can answer, and fails if a route stops answering it.

These are acceptance tests over the API, not unit tests of a module: they say what a user
can get out, not how it is computed.
"""
from __future__ import annotations

SIX_MONTH_BANDS = ("Very Low", "Low", "Medium", "High", "Very High")


def test_what_are_the_three_biggest_risks_in_chad_in_the_next_six_months(seeded):
    """The brief's own worked question, answered from the Risk List the engine serves."""
    client, _ = seeded
    risks = client.get("/api/risks").json()["risks"]
    chad = [r for r in risks if "Chad" in r["country"]]
    assert chad, "no active Chad risk to rank"

    order = {band: index for index, band in enumerate(SIX_MONTH_BANDS)}
    ranked = sorted(chad, key=lambda r: -order.get(r.get("probability_acaps") or "", -1))[:3]
    assert all(r["horizon_months"] == 6 for r in ranked), "the horizon is not six months"
    for risk in ranked:
        assert risk["title"] and risk["risk_id"]
        # A ranking nobody can interrogate is not an answer to this question.
        assert risk.get("triggers") is not None


def test_do_the_experts_agree_with_the_acaps_rating(seeded):
    """Ground truthing: the panel's view set beside ACAPS's own, after the reveal."""
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    assert 0.0 <= result["mean"] <= 1.0
    assert result["n"] >= 5, "a group view below five is never published"
    risk = client.get("/api/risks/R1043").json()
    assert risk["probability_acaps"] in SIX_MONTH_BANDS
    # Both numbers exist on the same scale, which is what makes agreement readable.
    assert risk["probability_assumed_number"] is not None


def test_how_likely_is_this_within_six_months_and_how_spread_is_the_panel(seeded):
    """Forecasting: a number, and the disagreement around it, never the number alone."""
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    spread = result["spread"]
    assert spread["min"] <= result["mean"] <= spread["max"]
    assert result["distribution"], "no distribution to show the spread"
    # "Outside my area" and "not enough evidence" are answers, not estimates, so they
    # count in n and stay out of the distribution.
    abstained = sum(a["count"] for a in result["abstentions"])
    assert sum(b["count"] for b in result["distribution"]) == result["n"] - abstained


def test_what_is_acaps_missing_on_this_risk(seeded):
    """The question the brief says experts are uniquely able to answer."""
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    themes = result["missing_themes"]
    assert themes, "no themes came out of the free text"
    for theme in themes:
        assert theme["theme"] and theme["count"] >= 1
        # Corroboration is a status, so an unchecked claim is visibly unchecked.
        assert theme["corroboration"] in ("corroborated", "single-source", "not checked")


def test_which_trigger_would_move_an_experts_view_most(seeded):
    """ACAPS's key-assumption check, asked on the card and answerable from the record."""
    client, _ = seeded
    risk = client.get("/api/risks/R1043").json()
    assert len(risk["triggers"]) >= 2, "a trigger question needs alternatives"
    assert all(t.get("title") for t in risk["triggers"])


def test_how_well_has_acaps_own_rating_performed(seeded):
    """The baseline any expert view has to beat, computed from resolved risks."""
    client, _ = seeded
    insights = client.get("/api/insights").json()
    assert insights["totals"]["resolved"] > 0
    bands = {b["label"]: b for b in insights["calibration"]}
    assert bands, "no calibration to report"
    for band in bands.values():
        assert 0.0 <= band["rate"] <= 1.0
        assert band["n"] >= 1
    if "High" in bands and "Medium" in bands:
        # The product's whole premise: the top band already discriminates, the middle does
        # not. If that stops being true the pitch has to change with it.
        assert bands["High"]["rate"] > bands["Medium"]["rate"]


def test_what_did_the_analyst_do_with_the_panels_view(seeded):
    """Nothing publishes itself, so the record has to show a person deciding."""
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    draft = client.post(f"/api/pulses/{pulse_id}/draft").json()
    assert draft["status"] == "draft", "a draft must not arrive already accepted"
    decided = client.post(f"/api/drafts/{draft['id']}/decision", json={
        "action": "accept", "note": "Panel evidence supports the rating.",
        "what_decision": "Pre-position shelter", "for_whom": "NGO preparedness lead",
        "by_when": "2026-11-20",
    }).json()
    assert decided["status"] in ("accepted", "edited")
    assert decided.get("note")


def test_a_reader_can_check_the_record_without_seeing_a_person(seeded):
    """The public answer: what the panel said, what happened, and no individual anywhere."""
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    draft = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{draft['id']}/decision", json={
        "action": "accept", "note": "Recorded.", "what_decision": "Pre-position shelter",
        "for_whom": "NGO preparedness lead", "by_when": "2026-11-20",
    })
    ledger = client.get("/api/ledger").json()
    assert ledger["entries"], "an accepted draft left no public record"
    body = str(ledger)
    for leak in ("pseudonym", "expert_id", "X-syn-"):
        assert leak not in body, f"the public ledger exposes {leak}"
    entry = ledger["entries"][0]
    assert client.post("/api/ledger/verify",
                       json={"verify_hash": entry["verify_hash"]}).json()["valid"]


def test_what_changed_this_month_to_justify_asking(seeded):
    """The alert is arithmetic on ACAPS's own editions, and says which rule fired."""
    client, _ = seeded
    run = client.post("/api/alerts/replay",
                      json={"month_from": "Mar2026", "month_to": "Apr2026"}).json()
    assert run["events"], "the replay produced no shift"
    top = run["events"][0]
    assert top["rule_hit"], "an alert that cannot say why it fired is not evidence"
    assert top["before"] is not None and top["after"] is not None
    assert top["rank_this_month"] >= 1


def test_which_expertise_is_this_panel_missing(seeded):
    """Who to ask next: the composition check has to be able to fail."""
    client, _ = seeded
    match = client.get("/api/panels/match?risk_id=R1043").json()
    composition = match["composition"]
    assert "gaps" in composition and "ok" in composition
    assert composition["max_per_affiliation"] == 3
    assert match["experts"], "no panel was matched"
    assert all(e["affiliation_tag"] != "guest" for e in match["experts"]), (
        "an open demo link is not vetted expertise and must not fill a panel seat"
    )


def test_did_it_happen_and_was_the_panel_right(seeded):
    """The question that closes the loop and makes any of the scoring meaningful."""
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    draft = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{draft['id']}/decision", json={
        "action": "accept", "note": "Recorded.", "what_decision": "Pre-position shelter",
        "for_whom": "NGO preparedness lead", "by_when": "2026-11-20",
    })
    # Scoring is refused until the question is frozen, so a forecast is never settled
    # against a question nobody agreed to.
    premature = client.post("/api/risks/R1043/resolve", json={
        "outcome": "materialised", "resolved_at": "2027-05-07T00:00:00+00:00"})
    assert premature.status_code == 409, "resolved without a frozen question contract"

    frozen = client.post("/api/risks/R1043/contract", json={
        "event": "Cross-border incursions cause a significant deterioration in eastern Chad",
        "location": "Ouaddai, Wadi Fira, Sila, Ennedi Est",
        "horizon_deadline": "2027-05-07",
        "resolution_source": "ACAPS Risk Radar status for R1043",
        "adjudication_rule": "The Risk Radar manager sets the status; partial "
                             "materialisation is a note, not a score.",
    })
    assert frozen.status_code == 201, frozen.json()
    resolved = client.post("/api/risks/R1043/resolve", json={
        "outcome": "materialised", "resolved_at": "2027-05-07T00:00:00+00:00",
    }).json()
    assert resolved["scores_written"] >= 1, "resolution scored nothing"
    entry = next(e for e in client.get("/api/ledger").json()["entries"]
                 if e["risk_id"] == "R1043")
    assert entry["outcome"] == "materialised"
    assert entry["honesty"]["misses"] in (0, 1), "the record must show hits and misses alike"
