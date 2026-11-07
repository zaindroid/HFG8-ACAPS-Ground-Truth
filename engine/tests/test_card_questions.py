"""The expert card's follow-up questions: reachability, debiasing and blindness."""
from __future__ import annotations

import json

from engine import data, probes

RISK_ID = "R1043"
CORE_DEFAULTS = {"probability": 0.5, "panel_share": 0.5, "confidence": 3}


def _risk():
    return data.get_risk(RISK_ID)


def _expert(expert_id="X-syn-01", themes=("conflict", "access"), region="Ouaddai"):
    return {"id": expert_id, "theme_tags": list(themes), "geo_tags": ["TCD"], "region": region}


def test_every_rule_resolves_against_the_bank_it_ships_with():
    """The bug this guards: rules named literal question ids, a reviewed set has its own,
    so no rule matched and the card jumped to submit with no follow-up at all."""
    for expert_id in ("X-syn-01", "X-syn-03", "X-syn-06", "X-unknown-01"):
        flow = probes.card_flow(_risk(), _expert(expert_id))
        roles_present = {probes.role_of(p) for p in flow["bank"].values()}
        for rule in flow["rules"]:
            assert rule.get("roles") or rule.get("role"), f"rule without a role: {rule}"
        # Rules are ordered with fallbacks, so the guarantee is that each step can be
        # served, not that every individual rule matches this bank.
        for step in (2, 3):
            wanted = set()
            for rule in flow["rules"]:
                if rule["step"] == step:
                    wanted |= set(rule.get("roles") or [rule.get("role")])
            assert roles_present & wanted, (
                f"{expert_id}: step {step} cannot be served; wants {sorted(wanted)}, "
                f"bank offers {sorted(roles_present)}"
            )


def test_a_reviewed_set_is_reachable_not_just_present():
    """A reviewed set that loads but never routes is worse than no reviewed set."""
    flow = probes.card_flow(_risk(), _expert("X-syn-01"))
    reviewed_ids = {q["id"] for q in json.loads(
        probes.REVIEWED.read_text(encoding="utf-8"))["sets"][f"{RISK_ID}:X-syn-01"]}
    assert reviewed_ids <= set(flow["bank"]), "reviewed questions missing from the bank"
    assert all(probes.role_of(flow["bank"][i]) for i in reviewed_ids), (
        "a reviewed question without a role can never be routed to"
    )


def test_every_card_offers_a_debiasing_question_at_default_answers():
    """At 50/50 and middling confidence no threshold fires, and before this the expert
    met none of the mitigations ACAPS's bias brief names."""
    for expert_id in ("X-syn-01", "X-syn-03", "X-syn-06", "X-syn-07", "X-unknown-02"):
        flow = probes.card_flow(_risk(), _expert(expert_id))
        step_three = [r for r in flow["rules"] if r["step"] == 3]
        assert step_three, f"{expert_id}: no step 3"
        assert all(set(r.get("roles") or []) <= set(probes.DEBIASING) for r in step_three)
        offered = {probes.role_of(p) for p in flow["bank"].values()}
        assert offered & set(probes.DEBIASING), (
            f"{expert_id}: bank carries no debiasing question, so the card cannot offer one"
        )


def test_questions_never_state_the_acaps_rating():
    """Round one hides the rating; a question quoting the rationale must not restore it."""
    for expert_id in ("X-syn-01", "X-syn-04", "X-unknown-03"):
        flow = probes.card_flow(_risk(), _expert(expert_id))
        for probe in flow["bank"].values():
            text = f"{probe['question']} {probe.get('help', '')}".lower()
            for band in ("very low", "very high", "rated high", "rated medium"):
                assert band not in text, f"{probe['id']} leaks the band: {text[:90]}"


def test_a_question_is_specific_to_this_risk():
    """A prompt that would read the same for any risk in any country is not worth an
    expert's minute, so at least one names something from this record."""
    flow = probes.card_flow(_risk(), _expert())
    corpus = " ".join(f"{p['question']} {p.get('help', '')}" for p in flow["bank"].values())
    assert any(name in corpus for name in ("Ouaddai", "Adre", "Chad", "Abeche", "Sudan")), (
        "no question names anything from the risk record"
    )


def test_the_same_expert_always_gets_the_same_card():
    """A card has to be replayable: an analyst asking why an expert saw a question needs
    an answer, and a rotation that moved between loads would have none."""
    first = probes.card_flow(_risk(), _expert())
    second = probes.card_flow(_risk(), _expert())
    assert json.dumps(first["bank"], sort_keys=True) == json.dumps(second["bank"], sort_keys=True)


def test_dont_know_is_offered_and_never_leads():
    """An expert in a hurry should not find the easy answer first, and should not be
    forced to guess because no easy answer exists."""
    flow = probes.card_flow(_risk(), _expert())
    for probe in flow["bank"].values():
        options = probe.get("options") or []
        if not options:
            continue
        assert any(o.get("dk") for o in options), f"{probe['id']} forces a guess"
        assert not options[0].get("dk"), f"{probe['id']} leads with don't-know"
