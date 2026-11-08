"""Mechanism 8: the hash-chained record of the risk process."""
from __future__ import annotations
import copy
import json
import re

import pytest

from engine.hardening import anchors as anchors_mod, chain as chain_mod
from helpers import reveal_now

RATIONALE = "Field reports from Ouaddai point the other way; holding the rating."


def _built() -> chain_mod.Chain:
    c = chain_mod.Chain()
    c.append("R1", "question_approved", {"pulse_id": "P-0001", "reason": "analyst",
                                         "question_sha256": "ab" * 32})
    c.append("R1", "panel_invited", {"pulse_id": "P-0001", "n_invited": 9})
    c.append("R1", "answers_sealed", {"pulse_id": "P-0001", "n_answers": 8,
                                      "commitment_root": "cd" * 32})
    c.append("R1", "revealed", {"pulse_id": "P-0001", "n_answers": 8, "status": "revealed"})
    return c


def test_the_chain_builds_in_order_from_genesis():
    c = _built()
    events = c.get("R1")
    assert [e["seq"] for e in events] == [0, 1, 2, 3]
    assert events[0]["prev_hash"] == chain_mod.GENESIS == "0" * 64
    for before, after in zip(events, events[1:]):
        assert after["prev_hash"] == before["hash"]
    for event in events:
        body = {k: v for k, v in event.items() if k != "hash"}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        import hashlib
        assert event["hash"] == hashlib.sha256(raw).hexdigest()
    assert c.head("R1") == events[-1]["hash"]
    assert c.verify("R1") == {"intact": True, "broken_at": None, "length": 4}


@pytest.mark.parametrize("seq", [0, 1, 2, 3])
@pytest.mark.parametrize("field,value", [
    ("data", {"pulse_id": "P-0001", "n_invited": 99}),
    ("at", "2020-01-01T00:00:00+00:00"),
    ("kind", "published"),
])
def test_altering_any_past_event_is_detected_at_its_seq(seq, field, value):
    c = _built()
    c.events["R1"][seq][field] = copy.deepcopy(value)
    assert c.verify("R1") == {"intact": False, "broken_at": seq, "length": 4}


def test_rehashing_an_altered_event_is_still_detected_at_the_next_one():
    c = _built()
    event = c.events["R1"][1]
    event["data"] = {"pulse_id": "P-0001", "n_invited": 99}
    event["hash"] = chain_mod.event_hash(event)
    assert c.verify("R1")["broken_at"] == 2


@pytest.mark.parametrize("seq", [0, 1, 2])
def test_deleting_an_event_is_detected(seq):
    c = _built()
    del c.events["R1"][seq]
    result = c.verify("R1")
    assert result["intact"] is False and result["broken_at"] == seq and result["length"] == 3


def test_deleting_the_last_event_changes_the_head_a_holder_has():
    c = _built()
    published = c.head("R1")
    c.events["R1"].pop()
    assert c.head("R1") != published


# -- privacy -------------------------------------------------------------------
@pytest.mark.parametrize("data", [
    {"name": "Amina"},
    {"email": "x@example.invalid"},
    {"pseudonym": "Kestrel-12"},
    {"expert_id": "X-syn-01"},
    {"note": "free text"},
    {"pulse_id": "has spaces in it"},
    {"rule": "index delta >= 0.5"},
    {"question_sha256": "not-a-hash"},
    {"n_answers": -1},
])
def test_the_chain_refuses_anything_but_ids_enums_counts_and_fingerprints(data):
    with pytest.raises(ValueError):
        chain_mod.Chain().append("R1", "revealed", data)


def _full_process(client, pulse_id):
    reveal_now(client, pulse_id)
    drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{drafted['id']}/decision", json={
        "action": "edit", "edited_probability": "Medium", "note": RATIONALE,
        "what_decision": "Pre-position stock in Abeche", "for_whom": "Cluster lead",
        "by_when": "2026-12-01",
    })
    client.post("/api/risks/R1043/resolve", json={"outcome": "materialised"})
    return client.get("/api/risks/R1043/chain").json()


def test_the_seeded_demo_risk_has_an_intact_chain(seeded):
    client, _ = seeded
    body = client.get("/api/risks/R1043/chain").json()
    kinds = [e["kind"] for e in body["events"]]
    assert kinds == ["alert_raised", "question_approved", "panel_invited", "answers_sealed"]
    assert body["verify"] == {"intact": True, "broken_at": None, "length": 4}
    alert = body["events"][0]["data"]
    assert alert["crisis_id"] == "TCD005" and alert["rule"] == "index_rule"
    assert alert["old_value"] < alert["new_value"]
    assert re.fullmatch(r"[0-9a-f]{64}", alert["edition_sha256"])
    assert body["head"] == body["events"][-1]["hash"]


def test_the_whole_process_is_chained_and_holds_no_personal_data(seeded):
    from engine.api import STORE, SETTINGS
    from engine.store import pseudonym_for

    client, pulse_id = seeded
    body = _full_process(client, pulse_id)
    kinds = [e["kind"] for e in body["events"]]
    assert kinds == ["alert_raised", "question_approved", "panel_invited", "answers_sealed",
                     "revealed", "draft_created", "decision_recorded", "published",
                     "outcome_resolved"]
    assert body["verify"]["intact"] is True and body["verify"]["length"] == 9
    decision = body["events"][6]["data"]
    assert decision["action"] == "edit"
    assert decision["rationale_sha256"] == chain_mod.fingerprint(RATIONALE)

    flat = json.dumps(body["events"])
    assert RATIONALE not in flat
    assert "@" not in flat
    for expert_id in STORE.experts:
        assert expert_id not in flat
        assert pseudonym_for(expert_id, SETTINGS.pseudonym_key) not in flat
    for answer in STORE.answers.get(pulse_id, []):
        for text in (answer.missing, answer.against):
            if text:
                assert text not in flat
    for event in body["events"]:
        chain_mod.check_data(event["data"])          # every value has an allowed shape


def test_a_chain_head_is_a_leaf_of_the_days_anchor_root(seeded):
    from engine.api import HARD

    client, pulse_id = seeded
    body = _full_process(client, pulse_id)
    day = body["events"][-1]["at"][:10]
    root = HARD.anchors.roots[day]
    assert body["head"] in root.leaves
    assert root.n_chain_heads >= 1
    commitments = sorted(root.leaves - {body["head"]})
    assert root.merkle_root == anchors_mod.merkle_root(commitments + [body["head"]])
    assert root.merkle_root != anchors_mod.merkle_root(commitments)
    listed = client.get("/api/anchors").json()["roots"]
    assert any(r["day"] == day and r["n_chain_heads"] >= 1 for r in listed)


def test_record_takes_chain_heads_as_extra_leaves():
    store = anchors_mod.Anchors()
    root = store.record("2026-11-07", ["aa" * 32], ["bb" * 32])
    assert root.leaves == {"aa" * 32, "bb" * 32}
    assert root.n_commitments == 1 and root.n_chain_heads == 1
    assert root.merkle_root == anchors_mod.merkle_root(["aa" * 32, "bb" * 32])


def test_the_chain_route_for_an_unknown_risk_is_404(seeded):
    client, _ = seeded
    assert client.get("/api/risks/R0000000/chain").status_code == 404


def test_flag_off_records_nothing(seeded, monkeypatch):
    from engine.api import HARD

    client, pulse_id = seeded
    monkeypatch.setenv("FF_CHAIN", "0")
    before = len(HARD.chain.get("R1043"))
    reveal_now(client, pulse_id)
    assert len(HARD.chain.get("R1043")) == before
