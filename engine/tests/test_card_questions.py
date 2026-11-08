"""The expert card's follow-up questions: reachability, debiasing and blindness."""
from __future__ import annotations

import json

from engine import data, probes, question_gen

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


# --- what the model is told, and what a question is allowed to say -------------------------

def test_the_prompt_carries_no_internal_data():
    """The context handed to the model is the published record and the expert's profile.

    Everything the expert answers blind to used to be in it: the band's resolution history, the
    expected exposure figure, and the monthly index values the pulse fired on, rows and all. A
    model given those writes questions about them, and a question is read by the person we are
    keeping them from. The expert's own calibration was in there too, which is theirs.
    """
    risk = dict(_risk())
    risk["probability_acaps"] = "High"
    risk["level"] = "High"
    risk["exposure"] = ">500,000"
    evidence = [{"metric": "index", "dataset": "inform-severity-index", "before": 6.1,
                 "after": 6.9, "delta": 0.8, "rank_this_month": 1, "n_crises_this_month": 123,
                 "url": "https://api.acaps.org/api/v1/inform-severity-index/"}]
    expert = {**_expert(), "track_record": {"brier": 0.11, "n_resolved": 23},
              "years_experience": 14}
    prompt = question_gen._context(risk, expert, evidence)
    for leaked in ("500,000", "6.1", "6.9", "0.8", "brier", "track_record", "years_experience",
                   "band_history", "share_materialised", "rank_this_month", "probability_acaps",
                   "expected_exposure"):
        assert leaked not in prompt, f"the prompt leaks {leaked}"
    # What did survive is what a question needs: the subject, the horizon, and who is answering.
    assert "Chad" in prompt and "index rose" in prompt
    assert "conflict" in prompt and "Ouaddai" in prompt


def test_no_question_announces_what_it_is_measuring():
    """A question that says it is checking an anchor gets a managed answer.

    The techniques are the method, not the subject. Nothing on a card may name one or tell the
    expert what the analyst will do with the answer.
    """
    tells = ("bias", "anchor", "debias", "devil's advocac", "pre-mortem", "premortem",
             "base rate", "base-rate", "calibrat", "overconfiden", "minority view",
             "why this is asked", "this question is asked", "we are testing", "to test whether")
    for expert_id in ("X-syn-01", "X-syn-03", "X-syn-06", "X-syn-07", "X-unknown-04"):
        flow = probes.card_flow(_risk(), _expert(expert_id))
        for probe in flow["bank"].values():
            text = " ".join(
                [probe["question"], probe.get("help", "")]
                + [o.get("label", "") for o in probe.get("options") or []]
            ).lower()
            for tell in tells:
                assert tell not in text, f"{probe['id']} explains itself: {tell}"


def test_the_prompt_forbids_invented_magnitudes_and_self_explanation():
    """The instruction is only half of it -- see the validator test below -- but it has to be
    in there, because a model that is not told will reach for a number."""
    system = question_gen.SYSTEM.lower()
    assert "50,000" in system and "direction" in system
    assert "never be told that a question is" in system
    assert "exactly two questions" in system


def test_a_generated_question_with_an_invented_number_is_dropped():
    """Defence in depth: the prompt says not to, and the cleaner enforces it. A year is not an
    invented number -- the deadline is a date from the record and a question has to name it."""
    kept = question_gen._clean({"questions": [
        {"id": "a", "kind": "choice", "role": "decomposition",
         "question": "Will arrivals in Ouaddai rise, hold or fall by 7 May 2027?",
         "options": [{"label": "Rise"}, {"label": "Hold"}, {"label": "Fall"}]},
        {"id": "b", "kind": "text", "role": "premortem",
         "question": "Will more than 50,000 people cross by then?"},
        {"id": "c", "kind": "text", "role": "premortem",
         "question": "Will prices rise by more than 25% in Abeche market?"},
        {"id": "d", "kind": "text", "role": "premortem",
         "question": "It is the deadline and this did not happen. What stopped it?"},
    ]})
    ids = [q["id"] for q in kept]
    assert "b" not in ids and "c" not in ids, "an invented magnitude survived"
    assert ids == ["a", "d"], f"expected the two clean questions, got {ids}"
    assert all(q["role"] for q in kept), "a role must survive, or no rule can route to it"


def test_a_card_never_asks_more_than_two_written_questions():
    """The core plus two. The pool may be larger; the walk is not."""
    flow = probes.card_flow(_risk(), _expert())
    assert flow["max_steps"] == 1 + probes.PROBE_SLOTS == 3
    assert question_gen.MAX_QUESTIONS == probes.PROBE_SLOTS == 2


def test_followups_route_generates_for_a_seat_with_no_expert_behind_it(empty):
    """A seat on the live panel has no expert until somebody scans its code, so its two
    questions are asked for when the seats go up rather than when the pulse is created."""
    api_client = empty
    if True:
        response = api_client.post("/api/questions/followups", json={
            "risk_id": RISK_ID,
            "expert": {"id": "demo-live-seat-1", "theme_tags": ["protection", "displacement"],
                       "geo_tags": ["TCD"], "region": "The Hague, Netherlands",
                       "affiliation_tag": "ngo"},
        })
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["source"] in ("model", "reviewed", "bank")
        assert body["max_asked"] == probes.PROBE_SLOTS
        assert 1 <= len(body["questions"]) <= probes.PROBE_SLOTS
        for probe in body["questions"]:
            assert probe["question"] and probe["kind"] in ("choice", "text", "rank")
        assert api_client.post("/api/questions/followups",
                               json={"risk_id": "R-nope"}).status_code == 404


def test_a_refusal_an_expert_reads_is_not_the_engine_talking_to_itself(seeded):
    """What the card showed on a second submit was "This action conflicts with the current
    round. Refresh before trying again." It is the engine's vocabulary, refreshing fixes
    nothing, and it buries the fact that matters: the answer is in and can still be changed.
    """
    api_client, pulse_id = seeded
    links = api_client.get("/api/demo/links").json()["links"]
    used = next(row for row in links if row["answered"])
    detail = api_client.post(
        f"/api/e/{used['token']}/answer",
        json={"round": 1, "stance": "estimate", "likelihood_word": "likely", "mask": "anonymous"},
    )
    assert detail.status_code == 409
    body = detail.json()["detail"]
    assert body["reason"] == "already_answered"
    line = body["line"]
    # Written for the person holding the link: what is true, and what they can do about it.
    assert "already in" in line and "change it" in line
    for internal in ("pulse", "round", "conflict", "PUT", "/api/", "token", "refresh"):
        assert internal.lower() not in line.lower(), f"the expert is shown {internal!r}"
    # The engine's own account of it is still there, for whoever is reading a log.
    assert "PUT /api/e/{token}/answer" in body["message"]
