"""The section 5 routes added in v3.2, on the product surface.

/credentials, /registry, /committee, /ledger/{id}/attestation, /anchors, /committee/patterns --
plus the two changes to existing routes: an answer may carry a credential or a proof, and a resolve
signs an outcome attestation.
"""
from __future__ import annotations
import base64

from engine.hardening import credentials as credentials_mod


def test_trust_status_carries_all_six_mechanisms_with_their_wording(seeded):
    client, _ = seeded
    body = client.get("/api/trust/status").json()
    assert len(body["mechanisms"]) == 7
    for mechanism in body["mechanisms"]:
        assert mechanism["guarantees"] and mechanism["does_not"]
    assert body["flags"]["FF_ZK"] is False
    assert body["zk"]["proof_verifier"] == "not implemented in this build"


def test_registry_status_shows_the_lock_line(seeded):
    client, _ = seeded
    body = client.get("/api/registry/status").json()
    assert body["encryption"].startswith("ML-KEM-768")
    assert body["key_id"]
    assert "key held by the committee" in body["lock_line"]
    assert body["does_not"]


def test_an_identity_goes_in_encrypted_and_only_comes_out_through_the_log(seeded):
    client, _ = seeded
    applied = client.post("/api/experts/apply", json={
        "geo_tags": ["TCD"], "theme_tags": ["access"],
        "identity": {"name": "Applicant (synthetic)", "email": "a@example.invalid"},
    }).json()
    expert_id = applied["expert_id"]
    assert applied["identity_stored"] is True
    # The application response must not echo the identity back.
    assert "a@example.invalid" not in client.get("/api/panels/match").text

    before = client.get("/api/committee/access-log").json()["n_reads"]
    refused = client.post("/api/committee/registry/read", json={"expert_id": expert_id})
    assert refused.status_code == 422
    assert client.get("/api/committee/access-log").json()["n_reads"] == before

    opened = client.post("/api/committee/registry/read", json={
        "expert_id": expert_id, "who": "committee-admin", "why": "duplicate application check",
    })
    assert opened.status_code == 200
    assert opened.json()["identity"]["email"] == "a@example.invalid"
    log = client.get("/api/committee/access-log").json()
    assert log["n_reads"] == before + 1
    assert log["entries"][0]["who"] == "committee-admin"


def test_approval_issues_a_credential_batch(seeded):
    client, _ = seeded
    expert_id = client.post("/api/experts/apply", json={"geo_tags": ["TCD"]}).json()["expert_id"]
    client.post(f"/api/experts/{expert_id}/approve", json={"admin": "admin-a"})
    approved = client.post(f"/api/experts/{expert_id}/approve", json={"admin": "admin-b"}).json()
    assert approved["status"] == "approved"
    assert approved["credential_batch"]["n_issued"] == 3
    assert approved["credential_batch"]["scheme"] == "rsa-blind-rfc9474"

    summary = client.get("/api/credentials/status").json()
    assert summary["n_issued"] >= 3
    assert summary["linked"] is False


def test_credentials_issue_signs_blinded_values_and_never_sees_the_token(seeded):
    client, _ = seeded
    expert_id = client.post("/api/experts/apply", json={"geo_tags": ["TCD"]}).json()["expert_id"]
    for admin in ("admin-a", "admin-b"):
        client.post(f"/api/experts/{expert_id}/approve", json={"admin": admin})

    issuer = client.get("/api/credentials/issuer").json()
    modulus, exponent = int(issuer["n"], 16), issuer["e"]
    token_id = "a1" * 16
    blinded, inverse = credentials_mod.blind(
        credentials_mod.message_for(token_id), modulus, exponent
    )
    issued = client.post("/api/credentials/issue", json={
        "expert_id": expert_id, "panel_id": "PAN-TCD", "blinded": [hex(blinded)],
    })
    assert issued.status_code == 201
    body = issued.json()
    assert body["unlinkable"] is True
    assert token_id not in issued.text

    signature = base64.b64encode(
        credentials_mod.unblind(int(body["blind_signatures"][0], 16), inverse, modulus)
    ).decode()

    # Spend it on a real answer, then try to spend it again.
    link = next(row for row in client.get("/api/demo/links").json()["links"]
                if not row["answered"])
    # The credential is spent by the confirmation, never by the draft: a token burned on an
    # answer nobody confirmed would be this expert's one chance at the pulse, spent by a link
    # preview.
    drafted = client.post(f"/api/e/{link['token']}/answer", json={
        "mask": "anonymous", "stance": "estimate", "likelihood_word": "even",
        "probability": 0.6, "confidence": "fairly sure", "source_tag": "read",
        "missing": "Spent a blind credential.", "round": 1,
    })
    assert drafted.status_code == 200
    answered = client.post(f"/api/e/{link['token']}/confirm", json={
        "confirm_token": drafted.json()["confirm_token"],
        "credential": {"token_id": token_id, "signature": signature},
    })
    assert answered.status_code == 201
    assert answered.json()["credential"] == {
        "spent": True, "unlinkable": True, "scheme": "rsa-blind-rfc9474",
        "line": answered.json()["credential"]["line"],
    }

    other = next(row for row in client.get("/api/demo/links").json()["links"]
                 if not row["answered"] and row["token"] != link["token"])
    again = client.post(f"/api/e/{other['token']}/answer", json={
        "mask": "anonymous", "stance": "estimate", "likelihood_word": "likely", "round": 1,
    })
    second = client.post(f"/api/e/{other['token']}/confirm", json={
        "confirm_token": again.json()["confirm_token"],
        "credential": {"token_id": token_id, "signature": signature},
    })
    assert second.status_code == 409
    assert "already spent" in second.json()["detail"]


def test_credentials_are_refused_before_approval(seeded):
    client, _ = seeded
    expert_id = client.post("/api/experts/apply", json={"geo_tags": ["TCD"]}).json()["expert_id"]
    refused = client.post("/api/credentials/issue", json={"expert_id": expert_id, "count": 2})
    assert refused.status_code == 409
    assert "approval" in refused.json()["detail"]


def test_an_anonymous_answer_without_a_credential_says_which_path_ran(seeded):
    client, _ = seeded
    link = next(row for row in client.get("/api/demo/links").json()["links"]
                if not row["answered"])
    drafted = client.post(f"/api/e/{link['token']}/answer", json={
        "mask": "anonymous", "stance": "estimate", "likelihood_word": "even",
        "confidence": "not sure", "round": 1, "missing": "No credential presented.",
    }).json()
    body = client.post(f"/api/e/{link['token']}/confirm",
                       json={"confirm_token": drafted["confirm_token"]}).json()
    assert body["credential"]["spent"] is True
    assert body["credential"]["unlinkable"] is False
    assert "did not bring its own" in body["credential"]["line"]


def test_a_membership_proof_is_refused_while_the_flag_is_off(seeded):
    client, _ = seeded
    link = next(row for row in client.get("/api/demo/links").json()["links"]
                if not row["answered"])
    drafted = client.post(f"/api/e/{link['token']}/answer", json={
        "mask": "pseudonym", "stance": "estimate", "likelihood_word": "even", "round": 1,
    })
    refused = client.post(f"/api/e/{link['token']}/confirm", json={
        "confirm_token": drafted.json()["confirm_token"],
        "zk_proof": {"panel_id": "PAN-TCD", "group_root": "00" * 32,
                     "nullifier": "11" * 32, "points": list(range(8))},
    })
    assert refused.status_code == 409
    assert "FF_ZK is off" in refused.json()["detail"]


def test_anchors_lists_a_root_for_the_sealed_day(seeded):
    client, _ = seeded
    body = client.get("/api/anchors").json()
    assert body["roots"], "the seeded round sealed commitments, so a root exists"
    root = body["roots"][0]
    assert len(root["merkle_root"]) == 64
    assert root["status"] in ("pending", "anchored")
    assert root["does_not"]
    assert client.post("/api/anchors/2026-01-01/submit").status_code == 404


def test_resolving_signs_an_outcome_attestation(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal", json={"force": True})
    draft = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{draft['id']}/decision", json={
        "action": "accept", "note": "Accepted for the attestation test.",
        "decision_use": {"what_decision": "brief the team", "for_whom": "field office",
                         "by_when": "2026-12-01"},
    })
    client.post("/api/risks/R1043/contract", json={
        "event": "Arrivals exceed the planned site capacity in Ouaddai.",
        "location": "Ouaddai, Chad", "horizon_deadline": "2026-12-31",
        "resolution_source": "ACAPS Risk Radar", "adjudication_rule": "ACAPS published status",
    })
    resolved = client.post("/api/risks/R1043/resolve", json={"outcome": "materialised"}).json()
    assert resolved["attestation"]["scheme"] == "ML-DSA-65"

    attestation = client.get("/api/ledger/R1043/attestation").json()
    assert attestation["verification"]["valid"] is True
    assert attestation["public_key"]["public_key"], "the verification key must be published"
    assert "Truth of the outcome" in attestation["attestation"]["does_not"]


def test_an_unresolved_risk_has_no_attestation(seeded):
    client, _ = seeded
    missing = client.get("/api/ledger/R1043/attestation")
    assert missing.status_code == 404
    assert "not resolved" in missing.json()["detail"]


def test_ledger_verify_reports_three_separate_checks(seeded):
    client, pulse_id = seeded
    client.post(f"/api/pulses/{pulse_id}/reveal", json={"force": True})
    draft = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{draft['id']}/decision", json={
        "action": "accept", "note": "Accepted so the ledger has an entry.",
        "decision_use": {"what_decision": "brief the team", "for_whom": "field office",
                         "by_when": "2026-12-01"},
    })
    entry = client.get("/api/ledger").json()["entries"][0]
    body = client.post("/api/ledger/verify", json={"verify_hash": entry["verify_hash"]}).json()
    assert body["valid"] is True
    assert body["checked_means"]
    assert body["attestation"] is None
    assert "not resolved" in body["attestation_means"]
    assert body["anchor"] is None, "a pending root offers no link"
    assert body["anchor_root"]["merkle_root"]
    assert "proves nothing" in body["anchor_means"]


def test_committee_patterns_are_panel_level_and_name_nobody(seeded):
    """v3.4: the committee reads about panels, not people. The per-pseudonym report that used to
    live at this path is gone, and nothing replaced it on the committee side."""
    client, _ = seeded
    from engine.api import HARD, SETTINGS, STORE
    from engine.seeding_hardening import seed_all

    seed_all(HARD, STORE, SETTINGS)
    listed = client.get("/api/committee/patterns").json()
    assert listed["min_pulses"] == 3 and listed["min_per_affiliation"] == 3
    assert "reports" not in listed, "the per-expert listing is gone"

    # The seeded history gives one panel three revealed rounds; the demo panel has one.
    with_sentences = {panel["panel_id"] for panel in listed["panels"]}
    assert with_sentences, "the seeded history should open at least one panel report"
    below = {panel["panel_id"] for panel in listed["not_yet"]}
    assert "PAN-TCD" in below, "one revealed round is below the floor"

    panel_id = sorted(with_sentences)[0]
    one = client.get(f"/api/committee/patterns/{panel_id}").json()
    assert one["never_per_person"] is True
    assert one["sentences"], "an open report says something"
    for group in one["by_affiliation"]:
        assert group["n"] >= 3 or group["affiliation_tag"] == "merged"

    # No internal id and no pseudonym anywhere in any of it.
    flat = client.get("/api/committee/patterns").text + client.get(
        f"/api/committee/patterns/{panel_id}").text
    assert "X-syn-" not in flat
    for adjective in ("quiet-", "tall-", "dry-", "long-", "early-"):
        assert adjective not in flat
    assert client.get("/api/committee/patterns/PAN-NOWHERE").status_code == 404


def test_the_calibration_programme_is_off_and_says_what_it_would_measure(seeded):
    """Section 6d: the only mechanism here that measures a person ships off, and the disclosure
    is readable anyway -- what we would measure is not a secret, it is what consent is given
    against."""
    client, pulse_id = seeded
    from engine.api import STORE

    token = next(t for t, (p, _) in STORE.tokens.items() if p == pulse_id)
    disclosure = client.get("/api/calibration/disclosure").json()
    assert disclosure["enabled"] is False
    assert disclosure["min_items"] == 20
    assert "50 to 100" in disclosure["confidence_prompt"]
    assert "STOP" in disclosure["disclosure"]
    assert "deception" in disclosure["not_built"]

    refused = client.post(f"/api/me/{token}/calibration/opt-in",
                          json={"consent": True, "disclosure_version": disclosure[
                              "disclosure_version"]})
    assert refused.status_code == 409
    assert "nothing about any individual" in refused.json()["detail"]["message"]
    assert client.get("/api/committee/calibration").json()["enrolled"] == 0


def test_the_calibration_programme_needs_consent_against_the_current_disclosure(seeded):
    client, pulse_id = seeded
    import os

    from engine.api import HARD, STORE
    from engine.hardening import calibration as calibration_lib

    token = next(t for t, (p, _) in STORE.tokens.items() if p == pulse_id)
    os.environ["FF_CALIBRATION"] = "true"
    try:
        silent = client.post(f"/api/me/{token}/calibration/opt-in", json={"consent": False})
        assert silent.status_code == 422 and "explicit yes" in silent.json()["detail"]

        stale = client.post(f"/api/me/{token}/calibration/opt-in",
                            json={"consent": True, "disclosure_version": "2020-01-01.1"})
        assert stale.status_code == 422
        assert "does not carry across" in stale.json()["detail"]

        joined = client.post(f"/api/me/{token}/calibration/opt-in", json={
            "consent": True, "disclosure_version": calibration_lib.DISCLOSURE_VERSION})
        assert joined.status_code == 201
        assert joined.json()["items_still_needed"] == 20

        items = client.get(f"/api/me/{token}/calibration/items").json()
        assert len(items["items"]) <= 2
        assert items["items"][0]["source_record"].startswith("ACAPS Risk List export")
        assert items["items"][0]["source_record"].endswith("Status column")
        assert items["items"][0]["known_answer"] in ("yes", "no")

        # No report before the floor, and the committee sees a count and nothing else.
        assert client.get(f"/api/me/{token}/calibration/report").status_code == 404
        counts = client.get("/api/committee/calibration").json()
        assert counts["enrolled"] == 1 and counts["reports_available"] == 0
        assert "belongs to the expert" in counts["means"]

        off = client.post(f"/api/me/{token}/calibration/off").json()
        assert off["report_off"] is True
    finally:
        os.environ.pop("FF_CALIBRATION", None)
        HARD.calibration.enrolments.clear()


