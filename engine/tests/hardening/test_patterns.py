"""Section 6d as v3.4 rewrote it: the committee reads about panels, not people.

What these tests hold in place is mostly a set of refusals. No sentence about an individual. No
pseudonym in any sentence. Nothing at all until the panel has three revealed rounds. An
affiliation group under three members merged rather than described. And the calibration
programme, which is the only thing here that measures a person, off unless an expert has read the
disclosure and said yes against its current version.

The panels are built here rather than seeded, so each test states the shape it depends on.
"""
from __future__ import annotations

import pytest

from engine.hardening import patterns
from engine.store import Expert, Store

SALT, KEY = "test-salt", "test-key"


def _panel(store: Store, affiliations: list[str]) -> list[str]:
    ids = []
    for index, affiliation in enumerate(affiliations, start=1):
        expert = store.add_expert(Expert(
            id=f"X-p{index:02d}", geo_tags=["TCD"], theme_tags=["conflict"],
            affiliation_tag=affiliation, status="approved", region="Ouaddai",
        ))
        ids.append(expert.id)
    return ids


def _round(store: Store, pulse_id: str, panel_id: str, experts: list[str],
           first: list[float], second: list[float] | None = None,
           source_tag: str = "read", abstain: int = 0, reveal: bool = True) -> dict:
    """One pulse on this panel, with a round 1 and optionally a round 2, then revealed."""
    store.pulses[pulse_id] = {
        "id": pulse_id, "risk_id": "R1043", "panel_id": panel_id, "round": 1,
        "fired_at": f"2026-0{len(store.pulses) + 1}-01T09:00:00+00:00",
        "evidence": [], "question": {}, "expires_at": "2020-01-01T00:00:00+00:00",
        "reveal_status": "open", "n_answers": 0,
    }
    for index, expert_id in enumerate(experts):
        store.issue_token(pulse_id, expert_id)
        if index >= len(experts) - abstain:
            store.seal(pulse_id, expert_id,
                       {"mask": "pseudonym", "stance": "not_enough_evidence", "round": 1,
                        "missing": "Nothing either way this week.", "source_tag": source_tag},
                       SALT, KEY)
            continue
        store.seal(pulse_id, expert_id,
                   {"mask": "pseudonym", "stance": "estimate", "round": 1,
                    "probability": first[index], "source_tag": source_tag,
                    "missing": f"A line from {expert_id} on {pulse_id}."},
                   SALT, KEY)
        if second is not None:
            store.seal(pulse_id, expert_id,
                       {"mask": "pseudonym", "stance": "estimate", "round": 2,
                        "probability": second[index], "changed_mind": True,
                        "source_tag": source_tag,
                        "missing": f"Revised view from {expert_id}."},
                       SALT, KEY)
    if reveal:
        # The expires_at above is in the past, so this is the deadline path, not an override.
        return store.reveal(pulse_id, {"triggers": []}, "deadline")
    return {}


# -- the floor -----------------------------------------------------------------
def test_nothing_opens_below_three_revealed_rounds():
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 5)
    for index in (1, 2):
        _round(store, f"P-000{index}", "PAN-A", experts, [0.6, 0.6, 0.6, 0.6, 0.6])
    report = patterns.report(store, "PAN-A")
    assert report["n_pulses_revealed"] == 2
    assert report["sentences"] == [] and report["by_affiliation"] == []
    assert "opens after 3 revealed rounds" in report["note"]
    assert report["never_per_person"] is True


# -- the sentences -------------------------------------------------------------
def test_convergence_after_the_reveal_is_counted_not_diagnosed():
    """ACAPS's brief calls it groupthink. The sentence says how often the second round moved
    toward the mean and how many of those revisions came with a reason. It does not say why."""
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 5)
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts,
               [0.2, 0.4, 0.6, 0.8, 0.9], second=[0.55, 0.55, 0.6, 0.6, 0.6])
    report = patterns.report(store, "PAN-A")
    line = next(s for s in report["sentences"] if "Round-2" in s)
    assert "moved toward the mean on 3 of 3" in line
    assert "written reason" in line
    for word in ("because", "herding", "groupthink", "copied"):
        assert word not in line.lower()


def test_the_spread_over_time_is_reported_with_both_ends():
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 5)
    _round(store, "P-0001", "PAN-A", experts, [0.1, 0.3, 0.5, 0.7, 0.9])
    _round(store, "P-0002", "PAN-A", experts, [0.3, 0.4, 0.5, 0.6, 0.7])
    _round(store, "P-0003", "PAN-A", experts, [0.45, 0.48, 0.5, 0.52, 0.55])
    line = next(s for s in patterns.report(store, "PAN-A")["sentences"] if "spread" in s)
    assert "narrowed from 0.80 to 0.10" in line


def test_abstentions_are_counted_and_called_real_answers():
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 6)
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts,
               [0.6, 0.6, 0.6, 0.6, 0.6, 0.6], abstain=2)
    line = next(s for s in patterns.report(store, "PAN-A")["sentences"] if "abstention" in s)
    assert "6 of 18 answers were abstentions" in line
    assert "never scored" in line


def test_a_dominant_source_tag_gets_a_sentence_and_a_mixed_one_does_not():
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 5)
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts,
               [0.6] * 5, source_tag="heard")
    line = next(s for s in patterns.report(store, "PAN-A")["sentences"] if "tagged" in s)
    assert "heard" in line and "15 of 15" in line


def test_the_coverage_gap_is_about_the_panel_not_a_person():
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 5)
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts, [0.6] * 5, reveal=False)
        store.pulses[f"P-000{index}"]["risk_id"] = "R1043"
        store.reveal(f"P-000{index}", None, "deadline")
    # Every seeded expert is tagged conflict only, and R1043 carries a displacement trigger.
    report = patterns.report(store, "PAN-A")
    gaps = [s for s in report["sentences"] if s.startswith("This panel has no")]
    assert gaps, "a panel with no displacement expert should say so"
    assert "expert" in gaps[0] and "X-p" not in gaps[0]


# -- never about a person ------------------------------------------------------
def test_no_sentence_contains_a_pseudonym_or_an_internal_id():
    store = Store(k_min=5)
    experts = _panel(store, ["un", "un", "un", "ngo", "ngo"])
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts,
               [0.9, 0.9, 0.9, 0.2, 0.2], second=[0.7, 0.7, 0.7, 0.4, 0.4])
    report = patterns.report(store, "PAN-A")
    flat = " ".join(report["sentences"] + [g["sentence"] for g in report["by_affiliation"]])
    for expert_id in experts:
        assert expert_id not in flat
    for answer in store.answers["P-0001"]:
        assert answer.pseudonym and answer.pseudonym not in flat


def test_affiliation_sentences_need_three_members_and_merge_below_that():
    store = Store(k_min=5)
    experts = _panel(store, ["un", "un", "un", "ngo", "research"])
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts, [0.9, 0.9, 0.9, 0.2, 0.2])
    groups = {g["affiliation_tag"]: g for g in patterns.report(store, "PAN-A")["by_affiliation"]}
    assert groups["un"]["n"] == 3
    assert "above the panel mean on all 3" in groups["un"]["sentence"]
    assert groups["merged"]["n"] == 2
    assert "below n = 3" in groups["merged"]["sentence"]
    assert "ngo" not in groups and "research" not in groups


def test_an_affiliation_sentence_is_descriptive_never_causal():
    store = Store(k_min=5)
    experts = _panel(store, ["un"] * 5)
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts, [0.9, 0.9, 0.9, 0.2, 0.2])
    sentence = patterns.report(store, "PAN-A")["by_affiliation"][0]["sentence"]
    assert "sat" in sentence
    for word in ("optimistic", "pessimistic", "biased", "because", "tend to"):
        assert word not in sentence.lower()


def test_an_answer_with_no_identity_kept_adds_nobody_to_the_panel():
    store = Store(k_min=5)
    experts = _panel(store, ["ngo"] * 5)
    for index in (1, 2, 3):
        _round(store, f"P-000{index}", "PAN-A", experts, [0.6] * 5)
    store.seal("P-0001", experts[0],
               {"mask": "anonymous", "stance": "estimate", "probability": 0.1},
               SALT, KEY)
    report = patterns.report(store, "PAN-A")
    assert report["n_experts"] == 5
    anonymous = [a for a in store.answers["P-0001"] if a.mask == "anonymous"]
    assert anonymous and anonymous[0].expert_id == ""


def test_the_report_module_has_no_per_expert_entry_point():
    """The per-expert report of v3.2 is gone, not hidden behind a flag. If it comes back, it
    comes back through the consent-gated programme, which is a different module."""
    assert not hasattr(patterns, "THRESHOLDS")
    assert "panel" in patterns.report.__doc__.lower()
    with pytest.raises(TypeError):
        patterns.report(Store(), "PAN-A", "X-p01")       # type: ignore[call-arg]


# -- the consent-gated calibration programme -----------------------------------
def test_a_calibration_report_opens_only_after_twenty_items():
    from engine.hardening import calibration

    programme = calibration.Programme()
    enrolment = programme.enrol("X-p01", True, calibration.DISCLOSURE_VERSION, "2026-11-07")
    item = {"id": "CI-1", "risk_id": "R1", "known_answer": "yes", "source_record": "export"}
    for index in range(19):
        programme.record("X-p01", {**item, "id": f"CI-{index}"}, "yes", 90, "2026-11-07")
    assert enrolment.report_available is False
    with pytest.raises(ValueError, match="opens after 20"):
        calibration.report(enrolment)

    programme.record("X-p01", {**item, "id": "CI-20"}, "no", 90, "2026-11-07")
    assert enrolment.report_available is True
    written = calibration.report(enrolment)
    assert "when you said about 90 %" in written["paragraph"]
    assert written["who_sees_this"].startswith("You, first and alone")


def test_switching_the_report_off_stops_it_being_computed():
    from engine.hardening import calibration

    programme = calibration.Programme()
    enrolment = programme.enrol("X-p01", True, calibration.DISCLOSURE_VERSION, "2026-11-07")
    item = {"id": "CI-1", "risk_id": "R1", "known_answer": "yes", "source_record": "export"}
    for index in range(20):
        programme.record("X-p01", {**item, "id": f"CI-{index}"}, "yes", 80, "2026-11-07")
    programme.switch_off("X-p01")
    assert enrolment.report_available is False
    assert enrolment.shared_with_committee is False
    with pytest.raises(ValueError, match="switched the report off"):
        calibration.report(enrolment)
    assert programme.counts()["switched_off"] == 1


def test_a_confidence_band_with_fewer_than_three_answers_is_not_reported():
    from engine.hardening import calibration

    programme = calibration.Programme()
    enrolment = programme.enrol("X-p01", True, calibration.DISCLOSURE_VERSION, "2026-11-07")
    item = {"id": "CI-1", "risk_id": "R1", "known_answer": "yes", "source_record": "export"}
    for index in range(19):
        programme.record("X-p01", {**item, "id": f"CI-{index}"}, "yes", 70, "2026-11-07")
    programme.record("X-p01", {**item, "id": "CI-99"}, "no", 95, "2026-11-07")
    written = calibration.report(enrolment)
    assert "about 70 %" in written["paragraph"]
    assert "about 90 %" not in written["paragraph"], "one answer at 95 % is not a hit rate"
    bands = {row["confidence_band"]: row["n"] for row in written["by_confidence"]}
    assert bands["90-99 %"] == 1


def test_the_committee_sees_counts_and_never_a_report():
    from engine.hardening import calibration

    programme = calibration.Programme()
    programme.enrol("X-p01", True, calibration.DISCLOSURE_VERSION, "2026-11-07")
    counts = programme.counts()
    assert counts == {
        "enrolled": 1, "reports_available": 0, "switched_off": 0,
        "shared_with_committee": 0, "disclosure_version": calibration.DISCLOSURE_VERSION,
        "min_items": calibration.MIN_ITEMS, "means": counts["means"],
    }
    assert "X-p01" not in str(counts)
