"""Country scan: "What are the three biggest risks in Chad that might worsen humanitarian outcomes
in the next six months?" -- the brief's own example question, answered with the same guarantees as
a risk pulse."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def _past(minutes: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat(timespec="seconds")


def _future(hours: int = 2) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(timespec="seconds")


@pytest.fixture()
def scan_client(seeded):
    client, _ = seeded
    from engine.api import ALERTS, SCANS, SETTINGS, STORE
    from engine import scan as scan_lib
    scan_id = scan_lib.seed_demo(SCANS, STORE, SETTINGS, ALERTS)
    return client, scan_id, SCANS


def _open_link(scans, scan_id):
    return next(t for t, (s, _) in scans.tokens.items() if s == scan_id and t not in scans.used)


def _answer(client, token, **body):
    drafted = client.post(f"/api/s/{token}/answer", json={"mask": "pseudonym", **body})
    assert drafted.status_code == 200, drafted.text
    return client.post(f"/api/s/{token}/confirm", json={"confirm_token": drafted.json()["confirm_token"]})


def test_chad_scan_asks_the_briefs_question_with_acaps_candidates(scan_client):
    client, scan_id, _ = scan_client
    scan = client.get(f"/api/scans/{scan_id}").json()
    assert scan["question"] == ("What are the three biggest risks in Chad that might worsen "
                                "humanitarian outcomes in the next six months?")
    ids = [c["id"] for c in scan["candidates"]]
    assert "R1043" in ids and "R1066" in ids
    assert any(c["kind"] == "acaps_crisis" for c in scan["candidates"])
    # The crisis R1043 already covers is not offered twice.
    assert "TCD005" not in ids
    assert 3 <= len(ids) <= 8


def test_card_hides_acaps_view_and_shows_titles_only(scan_client):
    client, scan_id, scans = scan_client
    card = client.get(f"/api/s/{_open_link(scans, scan_id)}").json()
    assert card["acaps_view_shown"] is False
    assert all(set(c) == {"id", "title"} for c in card["candidates"])
    assert card["mask_default"] is None


def test_candidate_order_is_shuffled_per_link_and_stable_on_reload(scan_client):
    client, scan_id, scans = scan_client
    links = [t for t, (s, _) in scans.tokens.items() if s == scan_id]
    orders = {tuple(c["id"] for c in client.get(f"/api/s/{t}").json()["candidates"]) for t in links}
    assert len(orders) > 1, "everyone saw the same order; list position would anchor them all"
    first = client.get(f"/api/s/{links[0]}").json()["candidates"]
    again = client.get(f"/api/s/{links[0]}").json()["candidates"]
    assert first == again


def test_link_click_never_commits_a_scan_answer(scan_client):
    client, scan_id, scans = scan_client
    token = _open_link(scans, scan_id)
    before = len(scans.answers.get(scan_id, []))
    drafted = client.post(f"/api/s/{token}/answer", json={"mask": "pseudonym", "picks": ["R1043"]})
    assert drafted.json()["committed"] is False
    assert len(scans.answers.get(scan_id, [])) == before


def test_more_than_three_picks_or_no_mask_is_refused(scan_client):
    client, scan_id, scans = scan_client
    token = _open_link(scans, scan_id)
    ids = [c["id"] for c in client.get(f"/api/s/{token}").json()["candidates"]]
    assert client.post(f"/api/s/{token}/answer", json={"mask": "pseudonym", "picks": ids[:4]}).status_code == 422
    assert client.post(f"/api/s/{token}/answer", json={"picks": ids[:1]}).status_code == 422


def test_added_risk_needs_a_source_tag(scan_client):
    client, scan_id, scans = scan_client
    token = _open_link(scans, scan_id)
    refused = client.post(f"/api/s/{token}/answer",
                          json={"mask": "anonymous", "added": "Locust swarms in Batha"})
    assert refused.status_code == 422


def test_scan_reveal_refused_before_deadline(scan_client):
    client, scan_id, _ = scan_client
    assert client.post(f"/api/scans/{scan_id}/reveal", json={}).status_code == 409
    assert client.get(f"/api/scans/{scan_id}/result").status_code == 409


def test_scan_under_k_min_at_deadline_reveals_nothing(seeded):
    client, _ = seeded
    from engine.api import ALERTS, SCANS, STORE
    from engine import scan as scan_lib
    SCANS.reset()
    scan = scan_lib.create(SCANS, STORE, "TCD", _future(), ALERTS)
    for _ in range(3):
        _answer(client, _open_link(SCANS, scan["id"]), picks=["R1043"])
    scan["expires_at"] = _past()
    result = client.post(f"/api/scans/{scan['id']}/reveal", json={}).json()
    assert result["reveal_status"] == "insufficient_panel"
    assert "ranking" not in result


def test_scan_ranking_scores_three_two_one_and_sits_beside_acaps(scan_client):
    client, scan_id, scans = scan_client
    scans.scans[scan_id]["expires_at"] = _past()
    result = client.post(f"/api/scans/{scan_id}/reveal", json={}).json()
    assert result["reveal_status"] == "revealed"
    top = result["ranking"][0]
    assert top["id"] == "R1043"
    # Four first places and two second places among the six who ranked: 4*3 + 2*2.
    assert top["points"] == 16 and top["in_top3"] == 6 and result["n_ranking"] == 6
    assert result["abstentions"] == {"outside_my_expertise": 1, "not_enough_evidence": 1}
    assert all("acaps_view" in row and "acaps_rank" in row for row in result["ranking"])
    assert result["acaps_top3"][0] in {"R1043", "R1066"}


def test_crisis_without_risk_entry_in_panel_top3_is_flagged_for_the_analyst(scan_client):
    client, scan_id, scans = scan_client
    scans.scans[scan_id]["expires_at"] = _past()
    result = client.post(f"/api/scans/{scan_id}/reveal", json={}).json()
    flagged = [n for n in result["notes"] if n["kind"] == "no_risk_entry"]
    assert [n["id"] for n in flagged] == ["TCD007"]
    assert all("not a finding" in n["text"] for n in flagged)
    below = [n["id"] for n in result["notes"] if n["kind"] == "panel_below_acaps"]
    assert below == ["TCD001"]
    assert result["panel_top3"] == ["R1043", "TCD007", "R1066"]


def test_public_scan_result_never_returns_an_individual(scan_client):
    client, scan_id, scans = scan_client
    scans.scans[scan_id]["expires_at"] = _past()
    client.post(f"/api/scans/{scan_id}/reveal", json={})
    public = client.get(f"/api/scans/{scan_id}/result", params={"audience": "public"}).json()
    text = repr(public)
    assert "pseudonym" not in text and "expert_id" not in text and "Cholera" not in text
    assert public["n"] >= 5


def test_added_risk_goes_to_access_logged_queue_not_the_result(scan_client):
    client, scan_id, scans = scan_client
    scans.scans[scan_id]["expires_at"] = _past()
    result = client.post(f"/api/scans/{scan_id}/reveal", json={}).json()
    assert result["added_risks"]["count"] == 1
    assert "Cholera" not in repr(result)
    assert client.get(f"/api/scans/{scan_id}/verification-queue").status_code == 403
    entries = client.get(f"/api/scans/{scan_id}/verification-queue",
                         params={"who": "analyst", "why": "corroborate"}).json()["entries"]
    assert entries[0]["text"].startswith("Cholera") and entries[0]["source_tag"] == "read"


def test_region_lines_describe_three_or_more_voices(scan_client):
    client, scan_id, scans = scan_client
    scans.scans[scan_id]["expires_at"] = _past()
    result = client.post(f"/api/scans/{scan_id}/reveal", json={}).json()
    assert all(row["n"] >= 3 for row in result["by_region"])


def test_scan_correction_before_deadline_keeps_the_earlier_commitment(scan_client):
    client, scan_id, scans = scan_client
    token = _open_link(scans, scan_id)
    first = _answer(client, token, picks=["R1066"]).json()
    second = _answer(client, token, picks=["R1043", "R1066"]).json()
    assert second["version"] == 2 and second["commitment"] != first["commitment"]
    mine = [a for a in scans.answers[scan_id] if a.commitment == second["commitment"]][0]
    assert mine.versions[0]["commitment"] == first["commitment"]


def test_scan_verify_recomputes_the_round_root(scan_client):
    client, scan_id, scans = scan_client
    scans.scans[scan_id]["expires_at"] = _past()
    client.post(f"/api/scans/{scan_id}/reveal", json={})
    assert client.post(f"/api/scans/{scan_id}/verify", json={}).json()["valid"] is True
    assert client.post(f"/api/scans/{scan_id}/verify", json={"verify_hash": "0" * 64}).json()["valid"] is False


def test_anonymous_scan_answer_stores_no_expert_id(scan_client):
    client, scan_id, scans = scan_client
    token = _open_link(scans, scan_id)
    sealed = _answer(client, token, mask="anonymous", picks=["R1043"]).json()
    mine = [a for a in scans.answers[scan_id] if a.commitment == sealed["commitment"]][0]
    assert mine.expert_id is None and mine.pseudonym is None
