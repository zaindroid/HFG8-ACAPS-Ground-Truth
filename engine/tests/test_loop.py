"""The rules that must not quietly break: the disclosure floor, what a sealed answer leaks before a
reveal, where integrity notes may appear, and that a rejected panel view reaches the public ledger."""
from __future__ import annotations

import pytest

from engine import data, draft as draft_builder
from engine.store import Store, TooFew, commit, round_verify_hash


# -- the disclosure floor ------------------------------------------------------
def test_reveal_refuses_below_k_min():
    store = Store(k_min=5)
    for index in range(4):
        store.answers.setdefault("P-0001", []).append(
            _answer(store, index, 0.5 + index / 100)
        )
    with pytest.raises(TooFew) as raised:
        store.reveal("P-0001")
    assert raised.value.n == 4 and raised.value.k_min == 5


def test_reveal_endpoint_returns_409_below_k_min(empty):
    from engine.api import SETTINGS, STORE
    from engine.seeding import seed_demo

    seed_demo(STORE, SETTINGS, seal=False)
    pulse_id = next(iter(STORE.pulses))
    token = next(t for t, (p, _) in STORE.tokens.items() if p == pulse_id)
    for _ in range(3):
        empty.post(f"/api/e/{token}/answer", json={"probability": 0.6, "mask": "anonymous"})
    response = empty.post(f"/api/pulses/{pulse_id}/reveal")
    assert response.status_code == 409
    assert "needs 5" in response.json()["detail"]


def test_no_aggregate_is_served_before_a_reveal(seeded):
    client, pulse_id = seeded
    assert client.get(f"/api/pulses/{pulse_id}/result").status_code == 404


# -- what a sealed answer leaks ------------------------------------------------
def test_tray_shows_commitments_never_values(seeded):
    client, pulse_id = seeded
    tray = client.get(f"/api/pulses/{pulse_id}/tray").json()
    assert tray["n_answers"] == 8 and tray["revealable"] is True
    flat = str(tray)
    assert "probability" not in flat
    for envelope in tray["envelopes"]:
        assert len(envelope["commitment"]) == 64
        assert set(envelope) == {"id", "committed_at", "commitment", "mask", "pseudonym"}


def test_commitment_is_reproducible_and_salted():
    payload = {"pulse_id": "P-0001", "probability": 0.7}
    assert commit(payload, "salt-a") == commit(payload, "salt-a")
    assert commit(payload, "salt-a") != commit(payload, "salt-b")
    assert commit(payload, "salt-a") != commit({**payload, "probability": 0.8}, "salt-a")


def test_anonymous_answers_carry_no_identity_link(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    anonymous = [a for a in STORE.answers[pulse_id] if a.mask == "anonymous"]
    assert anonymous, "the seeded round should contain an anonymous answer"
    for answer in anonymous:
        assert answer.expert_id == ""
        assert answer.pseudonym is None


def test_acaps_rating_is_hidden_until_submission(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = next(t for t, (p, e) in STORE.tokens.items()
                 if p == pulse_id and not STORE.answered(p, e))
    card = client.get(f"/api/e/{token}").json()
    assert card["rating_hidden_until_submission"] is True
    assert "probability_acaps" not in card["risk"]
    assert "level" not in card["risk"]

    submitted = client.post(f"/api/e/{token}/answer", json={
        "probability": 0.6, "mask": "pseudonym", "confidence": 3, "source_tag": "read",
        "missing": "test entry", "panel_share_yes": 0.5,
    })
    assert submitted.status_code == 201
    assert submitted.json()["acaps_rating_now_visible"]["probability_acaps"] == "High"


# -- aggregation ---------------------------------------------------------------
def test_equal_weight_mean_is_primary_and_weighted_is_secondary(seeded):
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    # Six of the eight seeded answers are estimates; two abstain and must not enter the mean.
    assert result["n"] == 8
    assert result["n_estimates"] == 6
    assert result["mean"] == pytest.approx((0.85 + 0.80 + 0.75 + 0.70 + 0.55 + 0.30) / 6, abs=1e-4)
    assert result["weighted_mean"] is not None
    assert {row["stance"]: row["count"] for row in result["abstentions"]} == {
        "outside_my_expertise": 1, "not_enough_evidence": 1,
    }


def test_region_with_one_voice_reports_count_but_no_mean(seeded):
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    singles = [row for row in result["agreement_by_region"] if row["n"] < 2]
    assert singles, "the seeded panel has at least one single-voice region"
    assert all(row["mean"] is None for row in singles)


def test_minority_rationale_survives_the_aggregate(seeded):
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    assert any("Border raids have slowed" in text for text in result["minority_rationales"])


def test_sp_experiment_is_labelled_experimental(seeded):
    client, pulse_id = seeded
    result = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    assert result["sp_experiment"]["label"] == "experimental"
    assert result["sp_experiment"]["answer"] in ("yes", "no")


# -- integrity notes are moderator-only ---------------------------------------
def test_integrity_notes_are_stripped_from_public_responses(seeded):
    client, pulse_id = seeded
    revealed = client.post(f"/api/pulses/{pulse_id}/reveal").json()
    assert "integrity_notes" not in revealed
    assert "integrity_notes" not in client.get(f"/api/pulses/{pulse_id}/result").json()

    moderator = client.get(f"/api/integrity/{pulse_id}").json()
    assert moderator["moderator_only"] is True
    assert any(note["kind"] == "shared_origin" for note in moderator["integrity_notes"])
    for note in moderator["integrity_notes"]:
        assert note["text"] and note["evidence"]


# -- draft, skeptic, judge -----------------------------------------------------
def test_draft_claims_are_checked_against_their_own_evidence(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    assert drafted["generator"] == "deterministic-template"
    assert drafted["claims"], "a draft with no claims is not a draft"
    assert len(drafted["skeptic"]) == len(drafted["claims"])
    assert drafted["judge"]["flagged_claim_ids"] == []
    assert drafted["judge"]["numbers_match"] == 1.0


def test_skeptic_flags_a_number_that_is_not_in_the_evidence():
    result = {"n": 8, "mean": 0.69, "weighted_mean": 0.69,
              "spread": {"min": 0.3, "max": 0.9, "iqr": 0.2}, "missing_themes": []}
    pulse = {"id": "P-0001", "evidence": []}
    claims = [{"claim_id": "C9", "text": "invented", "evidence_kind": "panel",
               "evidence_ref": "P-0001:mean", "numbers": [0.42]}]
    verdicts = draft_builder._skeptic(claims, result, pulse)
    assert verdicts[0]["verdict"] == "not_supported"
    assert any("absent from the evidence" in check for check in verdicts[0]["checks"])


def test_proposed_band_follows_the_panel_not_the_existing_rating():
    assert draft_builder.band_for(0.05) == "Very Low"
    assert draft_builder.band_for(0.30) == "Low"
    assert draft_builder.band_for(0.50) == "Medium"
    assert draft_builder.band_for(0.69) == "High"
    assert draft_builder.band_for(0.95) == "Very High"


# -- decision and ledger -------------------------------------------------------
def test_accepting_requires_what_decision_for_whom_by_when(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    thin = client.post(f"/api/drafts/{drafted['id']}/decision", json={"action": "accept"})
    assert thin.status_code == 422
    assert "what_decision" in thin.json()["detail"]


def test_rejecting_the_panel_requires_a_rationale_and_publishes_it(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()

    silent = client.post(f"/api/drafts/{drafted['id']}/decision", json={"action": "reject"})
    assert silent.status_code == 422

    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "reject", "note": "Indicators are flat; I am not moving the rating on this.",
    })
    honesty = client.get("/api/ledger").json()["entries"][0]["honesty"]
    assert honesty["panel_view_rejected"] is True
    assert "Indicators are flat" in honesty["analyst_rationale"]


def test_ledger_entry_verifies_against_its_own_commitments(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "what_decision": "d", "for_whom": "w", "by_when": "2026-12-01",
    })
    entry = client.get("/api/ledger").json()["entries"][0]
    verified = client.post("/api/ledger/verify", json={"verify_hash": entry["verify_hash"]}).json()
    assert verified["valid"] is True and verified["n_commitments"] == 8
    assert verified["anchor"] is None
    assert client.post("/api/ledger/verify", json={"verify_hash": "0" * 64}).status_code == 404


def test_verify_hash_is_order_independent():
    assert round_verify_hash(["b", "a", "c"]) == round_verify_hash(["a", "b", "c"])


def test_public_ledger_carries_no_names(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "what_decision": "d", "for_whom": "w", "by_when": "2026-12-01",
    })
    flat = str(client.get("/api/ledger").json())
    for expert_id in ("X-syn-01", "X-syn-02", "X-syn-03"):
        assert expert_id not in flat


# -- scoring -------------------------------------------------------------------
def test_resolving_without_a_frozen_question_contract_is_refused(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "what_decision": "d", "for_whom": "w", "by_when": "2026-12-01",
    })
    refused = client.post("/api/risks/R1043/resolve", json={"outcome": "materialised"})
    assert refused.status_code == 409
    assert "question contract" in refused.json()["detail"]


def test_board_is_empty_until_five_resolutions(seeded):
    client, pulse_id = seeded
    board = client.get("/api/analyst/board").json()
    assert board["super_estimators"] == []


# -- the risk export -----------------------------------------------------------
def test_export_loads_the_documented_number_of_risks():
    # The data dictionary states 139 risks, 28 active. If the export is swapped, this should shout.
    assert len(data.all_risks()) == 139
    assert len(data.active_risks()) == 28


def test_accented_place_names_survive_the_encoding():
    risk = data.get_risk("R1043")
    joined = " ".join(t["description"] for t in risk["triggers"])
    assert "�" not in joined, "the export was decoded with the wrong codec"
    assert "Adré" in joined


def test_triggers_carry_acaps_completion_rates():
    risk = data.get_risk("R1043")
    assert risk["triggers"], "R1043 should parse at least one trigger"
    assert all(t["completion_rate"] is not None for t in risk["triggers"])


def test_band_mapping_is_explicit_and_never_derived_from_risk_level():
    assert data.band_to_number("High") == 0.75
    assert data.band_to_number("nonsense") is None
    assert data.radar_status()["probability_assumption"]["Very High"] == 0.95


# -- platform contract ---------------------------------------------------------
def test_health_is_dependency_free(seeded):
    client, _ = seeded
    response = client.get("/health")
    assert response.status_code == 200 and response.json()["status"] == "ok"


def test_ready_and_version(seeded):
    client, _ = seeded
    assert client.get("/ready").json()["status"] == "ready"
    version = client.get("/version").json()
    assert set(version) >= {"sha", "built"}


def test_openapi_is_served(seeded):
    client, _ = seeded
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Sealed Signals"
    assert "/api/pulses/{pulse_id}/reveal" in spec["paths"]


def _answer(store: Store, index: int, probability: float):
    from engine.store import Answer

    return Answer(
        id=f"A-{index}", pulse_id="P-0001", expert_id=f"X-{index}", mask="pseudonym",
        pseudonym="x", probability=probability, confidence=3, stance="estimate",
        panel_share_yes=0.5, missing="", source_tag="read", round=1, changed_mind=False,
        committed_at="2026-11-07T09:00:00+00:00", commitment="0" * 64,
    )


# -- the single-page app -------------------------------------------------------
def test_spa_deep_links_serve_the_app_not_a_404(seeded):
    """A shared /app/e/<token> link, or a reload on /app/desk, must not land on a 404."""
    client, _ = seeded
    import engine.api as api

    if not api.UI_DIST.exists():
        import pytest as _pytest
        _pytest.skip("UI not built; run `make check` or `npm run build` in ui/ first")
    for path in ("/", "/desk", "/ledger", "/e/deadbeef", "/alerts", "/radar"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "<div id=\"root\">" in response.text, path


def test_a_used_link_is_known_without_linking_an_anonymous_answer(seeded):
    """The desk must see that a link was used, and still not know which answer it produced."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = next(t for t, (p, e) in STORE.tokens.items() if p == pulse_id and not STORE.answered(p, e))
    assert client.post(f"/api/e/{token}/answer",
                       json={"probability": 0.6, "mask": "anonymous"}).status_code == 201
    _, expert_id = STORE.tokens[token]
    assert STORE.answered(pulse_id, expert_id) is True
    assert all(a.expert_id != expert_id for a in STORE.answers[pulse_id] if a.mask == "anonymous")


def test_the_question_does_not_leak_the_acaps_band_before_submission(seeded):
    """The card promises the rating is hidden until submission. The question must honour that too."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = next(t for t, (p, e) in STORE.tokens.items() if p == pulse_id and not STORE.answered(p, e))
    card = client.get(f"/api/e/{token}").json()
    band = "High"   # R1043's actual ACAPS band
    assert band not in card["pulse"]["question"]
    assert band not in str(card["risk"])
    assert card["rating_hidden_until_submission"] is True


def test_indicator_claims_never_print_a_none_or_a_fake_baseline(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal")
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    flat = drafted["rationale_md"] + " ".join(c["text"] for c in drafted["claims"])
    assert "None" not in flat
    assert "baseline of 0" not in flat
    assert "% complete" in flat


def test_source_urls_survive_the_markdown_escaping_in_the_export():
    risk = data.get_risk("R1043")
    urls = [s["url"] for s in risk["sources"]]
    urls += [s["url"] for t in risk["triggers"] for s in t["sources"]]
    assert urls, "R1043 should carry at least one source URL"
    for url in urls:
        assert not url.endswith(("\\", ")", ",", ";")), url
        assert url.startswith("http")


def test_round_two_shows_the_rating_that_round_one_hides(seeded):
    """Round 1 is blind so the first answer is independent. Round 2 is the informed round: hiding
    ACAPS's rating there would withhold the evidence that round exists to add."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = next(t for t, (p, e) in STORE.tokens.items() if p == pulse_id and not STORE.answered(p, e))
    first = client.get(f"/api/e/{token}").json()
    assert first["round"] == 1 and first["blind"] is True
    assert "probability_acaps" not in first["risk"]

    client.post(f"/api/pulses/{pulse_id}/reveal")
    second = client.get(f"/api/e/{token}").json()
    assert second["round"] == 2
    assert second["blind"] is False
    assert second["risk"]["probability_acaps"] == "High"
    assert second["group_view_if_round2"]["n"] == 8
