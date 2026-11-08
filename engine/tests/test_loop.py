"""The rules that must not quietly break: the disclosure floor, what a sealed answer leaks before a
reveal, where integrity notes may appear, and that a rejected panel view reaches the public ledger."""
from __future__ import annotations

import pytest

from engine import data, draft as draft_builder
from engine.store import Store, commit, round_verify_hash
from helpers import commit_answer, draft_answer, open_token, reveal_now


# -- the disclosure floor ------------------------------------------------------
def test_a_round_below_k_min_becomes_an_insufficient_panel():
    """v3.4: under five the round goes to `insufficient_panel`. The answers are kept and nothing
    is revealed, to anyone -- not an error, a result about the panel."""
    store = Store(k_min=5)
    for index in range(4):
        store.answers.setdefault("P-0001", []).append(
            _answer(store, index, 0.5 + index / 100)
        )
    outcome = store.reveal("P-0001")
    assert outcome["reveal_status"] == "insufficient_panel"
    assert outcome["n"] == 4 and outcome["k_min"] == 5
    assert "P-0001" not in store.results, "nothing may be aggregated below the floor"
    assert len(store.answers["P-0001"]) == 4, "the answers are kept"


def test_the_insufficient_panel_route_reveals_nothing(empty):
    from engine.api import SETTINGS, STORE
    from engine.seeding import seed_demo

    seed_demo(STORE, SETTINGS, seal=False)
    pulse_id = next(iter(STORE.pulses))
    tokens = [t for t, (p, _) in STORE.tokens.items() if p == pulse_id][:3]
    for token in tokens:
        assert commit_answer(empty, token, mask="anonymous").status_code == 201
    response = reveal_now(empty, pulse_id)
    assert response.status_code == 200
    body = response.json()
    assert body["reveal_status"] == "insufficient_panel"
    assert "mean" not in body and "distribution" not in body
    assert "needs 5" in body["message"]
    # And the result route says the same thing rather than 404-ing as if nothing happened.
    assert empty.get(f"/api/pulses/{pulse_id}/result").json()["reveal_status"] == \
        "insufficient_panel"


def test_a_reveal_before_the_deadline_is_refused(seeded):
    """The reveal time is fixed when the pulse is sent. Not "when five are in": that would let
    the arrival of one more answer decide when the round closes."""
    client, pulse_id = seeded
    refused = client.post(f"/api/pulses/{pulse_id}/reveal", json={})
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert detail["expires_at"] and "cannot be revealed before" in detail["message"]
    # Forced, and the result says it was forced, so no screen can show a deadline reveal that
    # was not one.
    assert reveal_now(client, pulse_id).json()["revealed_reason"] == "analyst_before_deadline"


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
        assert set(envelope) == {"id", "committed_at", "commitment", "mask", "pseudonym",
                                 "version", "corrected_at", "relayed", "relayed_by", "counts"}
        assert "likelihood_word" not in envelope


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


def test_the_band_appears_only_in_the_feedback_after_the_reveal(seeded):
    """v3.4 moved ACAPS's band out of the card entirely -- out of round 1, out of round 2 and out
    of the submission receipt. It appears once, in the message after the deadline."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    card = client.get(f"/api/e/{token}").json()
    assert card["acaps_band_shown"] is False
    assert "probability_acaps" not in card["risk"]
    assert "level" not in card["risk"]
    assert "High" not in str(card["risk"])

    committed = commit_answer(client, token, confidence="fairly sure", source_tag="read",
                              missing="test entry", panel_share_yes=0.5)
    assert committed.status_code == 201
    receipt = committed.json()
    assert receipt["acaps_band_shown"] is False
    assert "acaps_rating_now_visible" not in receipt
    assert "after the deadline" in receipt["band_note"]

    # Before the reveal there is no feedback to read at all.
    assert client.get(f"/api/e/{token}/feedback").status_code == 404
    reveal_now(client, pulse_id)
    feedback = client.get(f"/api/e/{token}/feedback").json()
    assert feedback["acaps_band"] == "High" and feedback["acaps_band_shown"] is True


def test_a_draft_commits_nothing_and_a_link_click_cannot_answer(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    before = STORE.n_answers(pulse_id)
    drafted = draft_answer(client, token, missing="a draft only")
    assert drafted.status_code == 200
    assert drafted.json()["committed"] is False
    assert STORE.n_answers(pulse_id) == before, "a draft must not reach the answers"
    assert "commitment" not in drafted.json()

    confirmed = client.post(f"/api/e/{token}/confirm",
                            json={"confirm_token": drafted.json()["confirm_token"]})
    assert confirmed.status_code == 201
    assert STORE.n_answers(pulse_id) == before + 1
    # One confirmation per expert per pulse. The second is refused and points at the correction.
    replay = client.post(f"/api/e/{token}/confirm",
                         json={"confirm_token": drafted.json()["confirm_token"]})
    assert replay.status_code == 409


def test_the_mask_has_no_default(seeded):
    """A default mask is a decision about somebody's confidentiality taken by whoever wrote the
    code. The card offers three words and no preselection, so the engine refuses to guess."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    refused = client.post(f"/api/e/{token}/answer",
                          json={"stance": "estimate", "likelihood_word": "likely"})
    assert refused.status_code == 422
    assert "no default mask" in refused.json()["detail"]
    assert client.get(f"/api/e/{token}").json()["mask_default"] is None


def test_a_word_is_never_silently_turned_into_a_point(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    drafted = draft_answer(client, token, likelihood_word="unlikely").json()
    assert drafted["probability_source"] == "band_midpoint"
    assert drafted["probability_used"] == 0.22
    assert "midpoint" in drafted["number_note"]

    # An exact number outside the word it was filed under is refused rather than quietly kept.
    clash = draft_answer(client, token, likelihood_word="unlikely", probability=0.9)
    assert clash.status_code == 422
    assert "outside" in clash.json()["detail"]


def test_a_correction_keeps_the_version_it_replaces(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    first = commit_answer(client, token, likelihood_word="likely").json()
    corrected = client.put(f"/api/e/{token}/answer",
                           json={"mask": "pseudonym", "stance": "estimate",
                                 "likelihood_word": "unlikely"})
    assert corrected.status_code == 200
    body = corrected.json()
    assert body["version"] == 2 and body["previous_versions_kept"] == 1
    assert body["commitment"] != first["commitment"]

    _, expert_id = STORE.tokens[token]
    answer = STORE.find_answer(pulse_id, expert_id, None)
    assert answer.previous_versions[0]["likelihood_word"] == "likely"
    assert answer.likelihood_word == "unlikely"
    # The mask is not something a correction may rewrite: it decides who could already have seen
    # what.
    assert client.put(f"/api/e/{token}/answer",
                      json={"mask": "known", "stance": "estimate",
                            "likelihood_word": "even"}).status_code == 422


def test_a_relayed_answer_does_not_count_until_its_author_confirms(seeded):
    """An answer taken by phone is entered by the analyst. Until the expert confirms it through
    their own link it is held: otherwise the panel could be filled in by the people who convene
    it."""
    client, pulse_id = seeded
    from engine.api import SETTINGS, STORE

    token = open_token(STORE, pulse_id)
    _, expert_id = STORE.tokens[token]
    answer = STORE.seal(pulse_id, expert_id,
                        {"mask": "known", "stance": "estimate", "likelihood_word": "likely",
                         "relayed": True, "relayed_by": "analyst"},
                        SETTINGS.commitment_salt, SETTINGS.pseudonym_key)
    assert answer.counts() is False
    held = reveal_now(client, pulse_id).json()
    assert held["n"] == 8, "the held answer is not in the round"

    confirmed = client.post(f"/api/e/{token}/relayed-confirm", json={})
    assert confirmed.status_code == 200 and confirmed.json()["counts"] is True


# -- aggregation ---------------------------------------------------------------
def test_equal_weight_mean_is_primary_and_weighted_is_secondary(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    result = reveal_now(client, pulse_id).json()
    # Six of the eight seeded answers are estimates; two abstain and must not enter the mean.
    assert result["n"] == 8
    assert result["n_estimates"] == 6
    # Read from the answers rather than retyped here: the last set of literals in this file said
    # 69 % long after the engine had stopped producing it.
    estimates = [a.probability for a in STORE.answers[pulse_id]
                 if a.stance == "estimate" and a.probability is not None]
    assert result["mean"] == pytest.approx(sum(estimates) / len(estimates), abs=1e-4)
    assert result["weighted_mean"] is not None
    assert {row["stance"]: row["count"] for row in result["abstentions"]} == {
        "outside_my_expertise": 1, "not_enough_evidence": 1,
    }
    # Half the seeded estimates are a word with no number behind them, and the payload that
    # carries the mean says so.
    assert "band midpoint" in result["number_note"]


def test_region_with_one_voice_reports_count_but_no_mean(seeded):
    client, pulse_id = seeded
    result = reveal_now(client, pulse_id).json()
    singles = [row for row in result["agreement_by_region"] if row["n"] < 2]
    assert singles, "the seeded panel has at least one single-voice region"
    assert all(row["mean"] is None for row in singles)


def test_disagreement_is_unattributed_and_never_verbatim(seeded):
    """v3.4 replaced the verbatim minority rationale with a summary written from themes. In a
    panel of eight a quoted line identifies its author to the colleagues who sat on it."""
    client, pulse_id = seeded
    result = reveal_now(client, pulse_id).json()
    assert "minority_rationales" not in result
    lower = next(d for d in result["disagreement"] if d["position"] == "lower")
    assert lower["n"] >= 1 and lower["written_from"] == "themes"
    flat = str(result["disagreement"])
    for sentence in ("Border raids have slowed", "Night-time militia movement",
                     "Camp capacity in Ouaddai"):
        assert sentence not in flat, "no written answer may be quoted here"
    # And a lone dissenter does not even get their subject named.
    solo = [d for d in result["disagreement"] if d["n"] == 1]
    for item in solo:
        assert "would name them" in item["summary"]


def test_distinctive_free_text_lives_in_the_access_logged_queue(seeded):
    client, pulse_id = seeded
    result = reveal_now(client, pulse_id).json()
    assert result["verification_queue_count"] >= 1
    # The published result carries the count, never the lines.
    assert "Border raids have slowed" not in str(result)

    refused = client.get(f"/api/verification-queue/{pulse_id}")
    assert refused.status_code == 422 and "who and why" in refused.json()["detail"]

    read = client.get(f"/api/verification-queue/{pulse_id}",
                      params={"who": "alex@acaps", "why": "checking the Adre claim"})
    assert read.status_code == 200
    entries = read.json()["entries"]
    assert any("Border raids have slowed" in entry["text"] for entry in entries)
    assert all("expert_id" not in entry for entry in entries)
    log = client.get("/api/committee/verification-log").json()
    assert log["n_reads"] == 1
    assert log["reads"][0]["who"] == "alex@acaps" and log["reads"][0]["why"]


def test_a_theme_only_one_expert_raised_keeps_its_count_and_loses_its_words(seeded):
    client, pulse_id = seeded
    result = reveal_now(client, pulse_id).json()
    singles = [t for t in result["missing_themes"] if t["count"] == 1]
    assert singles, "the seeded round has themes only one expert raised"
    for theme in singles:
        assert theme["text_withheld"] is True and theme["in_queue"] is True
        assert "verification queue" in theme["theme"]
    shared = [t for t in result["missing_evidence"] if not t.get("in_queue")]
    assert shared and all(t["n"] > 1 for t in shared)


def test_sp_experiment_is_labelled_experimental(seeded):
    client, pulse_id = seeded
    result = reveal_now(client, pulse_id).json()
    assert result["sp_experiment"]["label"] == "experimental"
    assert result["sp_experiment"]["answer"] in ("yes", "no")


# -- integrity notes are moderator-only ---------------------------------------
def test_integrity_notes_are_stripped_from_public_responses(seeded):
    client, pulse_id = seeded
    revealed = reveal_now(client, pulse_id).json()
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
    reveal_now(client, pulse_id)
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
    reveal_now(client, pulse_id)
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    thin = client.post(f"/api/drafts/{drafted['id']}/decision", json={"action": "accept"})
    assert thin.status_code == 422
    assert "what_decision" in thin.json()["detail"]


def test_rejecting_the_panel_requires_a_rationale_and_publishes_it(seeded):
    client, pulse_id = seeded
    reveal_now(client, pulse_id)
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
    reveal_now(client, pulse_id)
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "what_decision": "d", "for_whom": "w", "by_when": "2026-12-01",
    })
    entry = client.get("/api/ledger").json()["entries"][0]
    verified = client.post("/api/ledger/verify", json={"verify_hash": entry["verify_hash"]}).json()
    assert verified["valid"] is True and verified["n_commitments"] == 8
    # Since v3.2 Verify reports three checks, each with its own meaning. The hash check is the one
    # that is valid here; the attestation does not exist until the risk resolves, and the anchor is
    # pending, which the response has to say rather than imply the round is externally timestamped.
    assert verified["attestation"] is None and "not resolved" in verified["attestation_means"]
    # Lane B's receipt guard rejects anything but a URL string or null here, and a pending root
    # is not a proof anyone can follow, so the link stays null and the root rides beside it.
    assert verified["anchor"] is None
    assert verified["anchor_root"]["status"] == "pending"
    assert "proves nothing" in verified["anchor_means"]
    assert "not submitted yet" in verified["anchor_means"]
    assert client.post("/api/ledger/verify", json={"verify_hash": "0" * 64}).status_code == 404


def test_verify_hash_is_order_independent():
    assert round_verify_hash(["b", "a", "c"]) == round_verify_hash(["a", "b", "c"])


def test_public_ledger_carries_no_names(seeded):
    client, pulse_id = seeded
    reveal_now(client, pulse_id)
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
    from engine.api import STORE

    # The seed freezes one for the demo risk, so this takes it away to test the guard.
    STORE.contracts.clear()
    reveal_now(client, pulse_id)
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "accept", "what_decision": "d", "for_whom": "w", "by_when": "2026-12-01",
    })
    refused = client.post("/api/risks/R1043/resolve", json={"outcome": "materialised"})
    assert refused.status_code == 409
    assert "question contract" in refused.json()["detail"]


def test_committee_scoring_is_panel_level_and_names_nobody(seeded):
    """v3.4 replaced the per-expert board with panel-level scoring. A leaderboard of pseudonyms
    built from answers that never said they were being ranked is the thing that went."""
    client, pulse_id = seeded
    scoring = client.get("/api/committee/scoring").json()
    assert "super_estimators" not in scoring
    assert client.get("/api/analyst/board").status_code == 404
    panel = next(row for row in scoring["panels"] if row["panel_id"] == "PAN-TCD")
    assert panel["n_resolved"] == 0 and panel["panel_brier"] is None
    assert "consent-gated" in scoring["note"]
    for expert_id in ("X-syn-01", "X-syn-02", "quiet-", "tall-"):
        assert expert_id not in client.get("/api/committee/scoring").text


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
    assert set(version) >= {"sha", "branch", "built", "started_at"}
    # The platform's SOURCE_COMMIT wins over a hand-set GIT_SHA, because `redeploy` reuses the
    # env config and leaves GIT_SHA pointing at whichever commit `deploy` last saw.
    import os

    from engine import settings as settings_mod

    os.environ["SOURCE_COMMIT"] = "abcdef1234567890"
    os.environ["GIT_SHA"] = "staleaa"
    try:
        assert settings_mod.load().git_sha == "abcdef1"
        del os.environ["SOURCE_COMMIT"]
        assert settings_mod.load().git_sha == "staleaa"
    finally:
        os.environ.pop("SOURCE_COMMIT", None)
        os.environ.pop("GIT_SHA", None)


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

    token = open_token(STORE, pulse_id)
    assert commit_answer(client, token, mask="anonymous").status_code == 201
    _, expert_id = STORE.tokens[token]
    assert STORE.answered(pulse_id, expert_id) is True
    assert all(a.expert_id != expert_id for a in STORE.answers[pulse_id] if a.mask == "anonymous")


def test_the_question_comes_from_the_frozen_contract_and_leaks_no_band(seeded):
    """The card's first line is the question as frozen, so the answer is adjudicated against the
    words the expert read. And it names no band: a question that quoted the rating would anchor
    the answer it exists to collect."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    card = client.get(f"/api/e/{token}").json()
    question = card["question"]
    assert question["source"] == "question_contract" and question["frozen_at"]
    assert set(question) >= {"event", "location", "threshold", "deadline", "text"}
    assert question["deadline"] == STORE.contracts["R1043"]["horizon_deadline"]
    band = "High"   # R1043's actual ACAPS band
    assert band not in str(question)
    assert band not in str(card["risk"])
    assert card["acaps_band_shown"] is False


def test_a_pulse_without_a_contract_says_it_cannot_be_scored(seeded):
    client, _ = seeded
    from engine.api import STORE

    STORE.contracts.clear()
    pulse = client.post("/api/pulses", json={"risk_id": "R1043"}).json()
    assert pulse["question"]["source"] == "open_question"
    assert "cannot be scored" in pulse["question"]["note"]


def test_the_card_withholds_the_alert_evidence_until_the_answer_is_in(seeded):
    """Section 6a: the severity-change line and the alert evidence are hidden with the band, for
    the same reason."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    card = client.get(f"/api/e/{token}").json()
    assert card["evidence_shown"] is False
    assert "evidence" not in card["pulse"]

    commit_answer(client, token)
    after = client.get(f"/api/e/{token}").json()
    assert after["evidence_shown"] is True and after["pulse"]["evidence"]


def test_the_card_carries_the_probe_flow_and_takes_its_answers(seeded):
    """The three-step card's follow-up questions travel with the card and are evaluated on the
    device, so no partial answer leaves the phone before the confirmation."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    flow = client.get(f"/api/e/{token}")["probe_flow"] if False else \
        client.get(f"/api/e/{token}").json()["probe_flow"]
    assert flow["max_steps"] == 3 and flow["bank"]
    assert all(rule["probe"] in flow["bank"] for rule in flow["rules"])
    # Every condition reads only this expert's own four numbers.
    for rule in flow["rules"]:
        assert set(rule.get("when") or {}) <= {"gap_at_least", "confidence_at_most",
                                               "probability_at_least", "probability_at_most",
                                               "answered"}
    committed = commit_answer(client, token, probe_answers={
        "evidence_seen": "Two sites reported new arrivals last Thursday.",
        "exposure_sanity": "250,000-500,000",
    })
    assert committed.status_code == 201
    _, expert_id = STORE.tokens[token]
    answer = STORE.find_answer(pulse_id, expert_id, None)
    assert answer.probe_answers["exposure_sanity"] == "250,000-500,000"
    # The probe answers never move the number.
    assert answer.probability == 0.78

    result = reveal_now(client, pulse_id).json()
    assert "probe_summary" not in result, "option counts on a panel of eight stay moderator-only"
    moderator = client.get(f"/api/integrity/{pulse_id}").json()
    summary = next(row for row in moderator["probe_summary"] if row["probe"] == "exposure_sanity")
    assert summary["options"][0]["option"] == "250,000-500,000"


def test_indicator_claims_never_print_a_none_or_a_fake_baseline(seeded):
    client, pulse_id = seeded
    reveal_now(client, pulse_id)
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


def test_round_two_shows_the_group_and_still_not_the_band(seeded):
    """v3.4 reversed what round 2 shows. It opens with the anonymised spread and the unattributed
    disagreement summary; ACAPS's band stays out, because showing it there would anchor the
    revision the round exists to collect. The band is in the feedback message and nowhere else."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    first = client.get(f"/api/e/{token}").json()
    assert first["round"] == 1 and first["acaps_band_shown"] is False
    assert "probability_acaps" not in first["risk"]

    reveal_now(client, pulse_id)
    second = client.get(f"/api/e/{token}").json()
    assert second["round"] == 2
    assert second["acaps_band_shown"] is False
    assert "probability_acaps" not in second["risk"]
    group = second["group_view_if_round2"]
    assert group["n"] == 8 and group["acaps_band_shown"] is False
    assert group["distribution"] and "disagreement" in group


def test_a_repeated_sentence_is_not_corroboration(seeded):
    """The seeded round has two near-identical 'what are we missing' entries, one tagged saw and
    one heard. Counting that as corroborated while the integrity notes call it a shared origin
    would have the same screen contradict itself."""
    client, pulse_id = seeded
    result = reveal_now(client, pulse_id).json()
    militia = next(t for t in result["missing_themes"] if "militia" in t["theme"].lower())
    assert militia["count"] >= 2
    assert militia["corroboration"] == "single-source"

    notes = client.get(f"/api/integrity/{pulse_id}").json()["integrity_notes"]
    assert any(note["kind"] == "shared_origin" for note in notes)
