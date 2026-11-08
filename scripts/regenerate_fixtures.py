"""Regenerate fixtures/ from the running API.

`fixtures/` is the contract Lane B builds against with VITE_MOCK=1, and the README says Lane A
regenerates it from the real API so it never drifts. This script is that regeneration: it drives
the whole loop in-process against a freshly seeded store and writes every response it gets.

Run it from the repo root:

    python scripts/regenerate_fixtures.py

Two deliberate choices:

* It walks the loop in order (alert -> pulse -> card -> answer -> reveal -> draft -> decision ->
  ledger -> resolve) rather than hitting routes in isolation, because several responses only exist
  after the step before them. A fixture captured out of order is a fixture of an error.
* Request fixtures are written from the bodies actually sent, so a request and its response always
  belong to each other.

It never invents a field. If a route refuses, the refusal is reported and the old fixture is left
alone rather than replaced with a 404 body.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"

os.environ.setdefault("COMMITMENT_SALT", "fixture-salt")
os.environ.setdefault("PSEUDONYM_KEY", "fixture-pseudonym-key")
os.environ.setdefault("COMMITTEE_KEY", "fixture-committee-key")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("LOG_LEVEL", "warning")
os.environ.setdefault("SEED_ON_START", "true")
sys.path.insert(0, str(ROOT / "engine"))

from fastapi.testclient import TestClient  # noqa: E402

written: list[str] = []
skipped: list[str] = []


def save(name: str, payload: dict | list) -> None:
    path = FIX / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append(name)


def sample(payload: dict, key: str, keep: int, *, first: list[str] | None = None,
           id_field: str = "risk_id") -> dict:
    """Keep a representative slice of a long list.

    A fixture is a shape contract and a demo dataset, not a database dump: the UI imports these
    files at build time, so shipping all 28 active risks or every event of a month would put
    120 KB of ACAPS data into the mock bundle for no gain. The entries kept are real, unedited
    responses; only the number of them is a choice, and `fixtures/README.md` says so.
    """
    rows = payload.get(key)
    if not isinstance(rows, list) or len(rows) <= keep:
        return payload
    wanted = [r for r in rows if r.get(id_field) in (first or [])]
    rest = [r for r in rows if r not in wanted]
    return {**payload, key: (wanted + rest)[:keep]}


def capture(name: str, response, *, expect: int = 200) -> dict:
    """Write the response if it is the one we expected, and never write an error body."""
    if response.status_code != expect:
        skipped.append(f"{name}: got {response.status_code}, expected {expect}")
        return {}
    body = response.json()
    save(name, body)
    return body


def settle_a_historical_round(client) -> str | None:
    """Take one of the seeded history pulses all the way to a resolved ledger entry."""
    from engine.api import STORE

    history = [pid for pid, pulse in STORE.pulses.items()
               if pulse.get("history") and STORE.n_answers(pid) >= STORE.k_min]
    if not history:
        skipped.append("resolved ledger entry: no seeded history pulse has enough answers")
        return None
    pulse_id = history[0]
    risk_id = STORE.pulses[pulse_id]["risk_id"]
    if client.post(f"/api/pulses/{pulse_id}/reveal",
                   json={"force": True}).status_code != 200:
        return None
    draft = client.post(f"/api/pulses/{pulse_id}/draft").json()
    client.post(f"/api/drafts/{draft['id']}/decision", json={
        "action": "reject",
        "note": "Rejected: the panel read the displacement figures as a trend, and the registration "
                "backlog at the time explains most of the jump. Published with the decision.",
        "decision_use": {"what_decision": "Flag the deterioration in the weekly note",
                         "for_whom": "Regional analysts", "by_when": "2026-10-15"},
    })
    client.post(f"/api/risks/{risk_id}/contract", json={
        "event": "The risk as published by ACAPS.",
        "location": "See the export row.",
        "horizon_deadline": "2026-10-31",
        "resolution_source": "ACAPS Risk Radar export, Status field",
        "adjudication_rule": "Materialised when ACAPS publishes the risk as Materialised.",
    })
    client.post(f"/api/risks/{risk_id}/resolve",
                json={"outcome": "materialised", "resolved_at": "2026-10-20T09:00:00+00:00"})
    return pulse_id


def main() -> int:
    from engine.api import HARD, SETTINGS, STORE, app
    from engine.hardening import credentials as credential_lib
    from engine.seeding import seed_alerts, seed_demo
    from engine.seeding_hardening import seed_all

    STORE.reset()
    HARD.reset()

    with TestClient(app) as client:
        # The lifespan seeds on start; re-seed explicitly so a rerun is reproducible.
        pulse_id = seed_demo(STORE, SETTINGS)
        from engine.api import ALERTS

        seed_alerts(ALERTS)
        seed_all(HARD, STORE, SETTINGS)

        # -- platform and reference data --------------------------------------
        health = client.get("/health").json()
        # /health is deliberately dependency-free and returns no envelope; the fixture carries one
        # so the validator can treat every file the same way.
        save("GET_health.json", {**health, "served_from": "live",
                                 "generated_at": client.get("/api/risks").json()["generated_at"]})
        capture("GET_radar_status.json", client.get("/api/radar/status"))
        save("GET_risks.json",
             sample(client.get("/api/risks").json(), "risks", 4, first=["R1043"]))
        capture("GET_risks_R1043.json", client.get("/api/risks/R1043"))
        capture("GET_crises_TCD005.json", client.get("/api/crises/TCD005"))
        capture("GET_radar_editions.json", client.get("/api/radar/editions"))

        # -- the alert engine --------------------------------------------------
        capture("POST_alerts_run_response.json", client.post("/api/alerts/run"))
        replay = capture("POST_alerts_replay_response.json", client.post(
            "/api/alerts/replay", json={"month_from": "Mar2026", "month_to": "Apr2026"}))
        listed_full = client.get("/api/alerts").json()
        save("GET_alerts.json", sample(listed_full, "events", 5, first=["R1043"]))
        listed = listed_full

        # -- the panel ---------------------------------------------------------
        apply_body = {
            "geo_tags": ["TCD"], "theme_tags": ["displacement", "access"],
            "affiliation_tag": "ngo", "languages": ["fr", "en"], "channel": "email",
            "region": "Ouaddai",
            "identity": {"name": "Applicant (synthetic)", "email": "applicant@example.invalid",
                         "organisation": "Eastern Chad protection NGO (synthetic)"},
        }
        save("POST_experts_apply_request.json", apply_body)
        applied = capture("POST_experts_apply_response.json",
                          client.post("/api/experts/apply", json=apply_body), expect=201)
        expert_id = applied.get("expert_id", "")
        if expert_id:
            client.post(f"/api/experts/{expert_id}/approve", json={"admin": "admin-a"})
            capture("POST_experts_approve_response.json",
                    client.post(f"/api/experts/{expert_id}/approve",
                                json={"admin": "admin-b", "allowance": 3}), expect=201)
        capture("GET_panels_match.json", client.get("/api/panels/match?risk_id=R1043"))

        # -- a pulse and the expert card ---------------------------------------
        capture("POST_pulses_response.json",
                client.post("/api/pulses", json={"risk_id": "R1043", "reason": "analyst"}),
                expect=201)
        capture("POST_pulses_doorbell_run_response.json", client.post("/api/pulses/doorbell/run"))
        # The demo round itself. The desk defaults to this one, so it needs its own fixture: the
        # POST above returns whichever pulse that call created, which is not the round on stage.
        capture("GET_pulses_demo.json", client.get(f"/api/pulses/{pulse_id}"))

        # One resolved round before the demo round, so GET_ledger.json carries both a current entry
        # and a settled one. The ledger is a history: a fixture with a single row cannot show the
        # resolved view the UI builds, and the old hand-made fixture had two for that reason.
        settle_a_historical_round(client)

        links = client.get("/api/demo/links").json()["links"]
        open_link = next(row for row in links if not row["answered"]
                         and row["pulse_id"] == pulse_id)
        capture("GET_e_token.json", client.get(f"/api/e/{open_link['token']}"))

        # The card spends a credential it blinded itself, which is the path that earns the
        # unlinkability sentence -- so the fixture shows that one, not the demo fallback.
        issuer = client.get("/api/credentials/issuer").json()
        save("GET_credentials_issuer.json", issuer)
        token_id = "9f" * 16
        blinded, inverse = credential_lib.blind(
            credential_lib.message_for(token_id), int(issuer["n"], 16), issuer["e"])
        issue_body = {"expert_id": expert_id, "panel_id": "PAN-TCD", "blinded": [hex(blinded)]}
        save("POST_credentials_issue_request.json", issue_body)
        issued = capture("POST_credentials_issue_response.json",
                         client.post("/api/credentials/issue", json=issue_body), expect=201)
        signature = ""
        if issued.get("blind_signatures"):
            import base64

            signature = base64.b64encode(credential_lib.unblind(
                int(issued["blind_signatures"][0], 16), inverse, int(issuer["n"], 16))).decode()

        # The answer goes to its OWN pulse, never the demo round. Adding a ninth answer there
        # would change n and the group mean, and the demo round's numbers (8 answers, mean 69%)
        # are quoted in the UI, in the tests and on stage.
        side_pulse = client.post("/api/pulses",
                                 json={"risk_id": "R1043", "reason": "analyst"}).json()
        side_token = STORE.issue_token(side_pulse["id"], "X-syn-01")

        # v3.4 split answering in two. Both halves get a fixture, because the whole point of the
        # split is that the first one commits nothing: `POST /answer` is the route a link click or
        # a mail scanner can reach, and it returns a confirmation token and a summary line.
        answer_body = {
            "mask": "anonymous", "stance": "estimate", "likelihood_word": "likely",
            "probability": 0.7, "confidence": "fairly sure",
            "panel_share_yes": 0.65, "source_tag": "saw", "round": 1, "trigger_pick": "T2",
            "missing": "Camp capacity in Ouaddai is already past what the sites were planned for.",
            "against": "Registration could stay flat if the border stays quiet.",
            "changed_mind": False,
            "probe_answers": {
                "evidence_seen": "Two sites reported new arrivals last Thursday.",
                "exposure_sanity": "250,000-500,000",
            },
        }
        save("POST_e_token_answer_request.json", answer_body)
        drafted = capture("POST_e_token_answer_response.json",
                          client.post(f"/api/e/{side_token}/answer", json=answer_body))
        confirm_body = {"confirm_token": drafted.get("confirm_token", "")}
        if signature:
            confirm_body["credential"] = {"token_id": token_id, "signature": signature}
        save("POST_e_token_confirm_request.json", confirm_body)
        confirmed = capture("POST_e_token_confirm_response.json",
                            client.post(f"/api/e/{side_token}/confirm", json=confirm_body),
                            expect=201)

        # A correction, which is allowed until the deadline and keeps the version it replaces.
        correction_body = {**{k: v for k, v in answer_body.items() if k != "credential"},
                           "likelihood_word": "even", "probability": 0.55,
                           "edit_key": confirmed.get("edit_key"),
                           "missing": "Camp capacity in Ouaddai is past the planned site figures, "
                                      "but the registration backlog explains part of the jump."}
        save("PUT_e_token_answer_request.json", correction_body)
        capture("PUT_e_token_answer_response.json",
                client.put(f"/api/e/{side_token}/answer", json=correction_body))

        # And a relayed answer: taken by phone, held until its author confirms it.
        relay_token = STORE.issue_token(side_pulse["id"], "X-syn-02")
        relay_body = {"mask": "known", "stance": "estimate", "likelihood_word": "likely",
                      "round": 1, "relayed": True, "relayed_by": "analyst", "source_tag": "heard",
                      "missing": "Taken by phone; the expert had no signal for the link."}
        relay_draft = client.post(f"/api/e/{relay_token}/answer", json=relay_body).json()
        client.post(f"/api/e/{relay_token}/confirm",
                    json={"confirm_token": relay_draft.get("confirm_token", "")})
        capture("POST_e_token_relayed_confirm_response.json",
                client.post(f"/api/e/{relay_token}/relayed-confirm", json={}))

        # The insufficient-panel path, on its own pulse with three answers on it. Lane B needs
        # the shape: it is a 200 with a reveal_status and no aggregate, not an error.
        thin_pulse = client.post("/api/pulses",
                                 json={"risk_id": "R1043", "reason": "analyst"}).json()
        for expert_id_thin in ("X-syn-03", "X-syn-04", "X-syn-05"):
            thin_token = STORE.issue_token(thin_pulse["id"], expert_id_thin)
            thin_draft = client.post(f"/api/e/{thin_token}/answer", json={
                "mask": "pseudonym", "stance": "estimate", "likelihood_word": "even",
                "round": 1}).json()
            client.post(f"/api/e/{thin_token}/confirm",
                        json={"confirm_token": thin_draft.get("confirm_token", "")})
        capture("POST_pulses_reveal_insufficient_response.json",
                client.post(f"/api/pulses/{thin_pulse['id']}/reveal", json={"force": True}))

        # -- reveal, draft, decision -------------------------------------------
        capture("POST_pulses_reveal_response.json",
                client.post(f"/api/pulses/{pulse_id}/reveal", json={"force": True}))
        capture("GET_pulses_result.json", client.get(f"/api/pulses/{pulse_id}/result"))
        capture("GET_integrity_pulse.json", client.get(f"/api/integrity/{pulse_id}"))
        # The verification queue, read the only way it can be read: with a who and a why, which
        # the response and the log both carry.
        capture("GET_verification_queue.json",
                client.get(f"/api/verification-queue/{pulse_id}",
                           params={"who": "alex@acaps.invalid",
                                   "why": "checking the Adre claim before the draft"}))
        capture("GET_committee_verification_log.json",
                client.get("/api/committee/verification-log"))
        # The feedback message, which is where an expert first sees ACAPS's band.
        answered_link = next((row for row in client.get("/api/demo/links").json()["links"]
                              if row["pulse_id"] == pulse_id and row["answered"]), None)
        if answered_link:
            capture("GET_e_token_feedback.json",
                    client.get(f"/api/e/{answered_link['token']}/feedback"))
        draft = capture("POST_pulses_draft_response.json",
                        client.post(f"/api/pulses/{pulse_id}/draft"))

        decision_body = {
            "action": "accept",
            "note": "Accepted. The panel and the export agree on direction; the spread is in the "
                    "ledger with the minority reasons.",
            "decision_use": {
                "what_decision": "Brief the Ouaddai field office before the weekly planning call",
                "for_whom": "ACAPS analysts and the Chad response team",
                "by_when": "2026-12-01",
            },
        }
        save("POST_drafts_decision_request.json", decision_body)
        if draft.get("id"):
            capture("POST_drafts_decision_response.json",
                    client.post(f"/api/drafts/{draft['id']}/decision", json=decision_body))

        # -- ledger and verification -------------------------------------------
        ledger = capture("GET_ledger.json", client.get("/api/ledger"))
        entries = ledger.get("entries") or []
        if entries:
            capture("POST_ledger_verify_response.json", client.post(
                "/api/ledger/verify", json={"verify_hash": entries[0]["verify_hash"]}))

        # -- contract, resolve, attestation ------------------------------------
        contract_body = {
            "event": "Arrivals from Sudan exceed the planned site capacity in Ouaddai.",
            "location": "Ouaddai, Chad",
            "horizon_deadline": "2026-12-31",
            "resolution_source": "ACAPS Risk Radar export, Status field",
            "adjudication_rule": "Materialised when ACAPS publishes the risk as Materialised.",
        }
        save("POST_risks_contract_request.json", contract_body)
        capture("POST_risks_contract_response.json",
                client.post("/api/risks/R1043/contract", json=contract_body), expect=201)
        capture("POST_risks_resolve_response.json", client.post(
            "/api/risks/R1043/resolve",
            json={"outcome": "materialised", "resolved_at": "2026-11-07T12:00:00+00:00"}))
        capture("GET_ledger_attestation.json", client.get("/api/ledger/R1043/attestation"))

        # -- outcome and calibration -------------------------------------------
        capture("GET_pulses_outcome_report.json",
                client.get(f"/api/pulses/{pulse_id}/outcome-report"))
        for row in links:
            response = client.get(f"/api/me/{row['token']}/calibration")
            if response.status_code == 200:
                capture("GET_me_calibration.json", response)
                break
        else:
            skipped.append("GET_me_calibration.json: no expert has five resolved risks yet")
        capture("GET_committee_scoring.json", client.get("/api/committee/scoring"))
        proof = client.get("/api/sim/proof")
        if proof.status_code == 200:
            capture("GET_sim_proof.json", proof)
        else:
            skipped.append("GET_sim_proof.json: run `make demo` first to write reports/proof.json")

        # -- the hardening stack (sections 6c and 6d) --------------------------
        capture("GET_trust_status.json", client.get("/api/trust/status"))
        capture("GET_registry_status.json", client.get("/api/registry/status"))
        read_body = {"expert_id": expert_id, "who": "committee-admin",
                     "why": "duplicate application check before approval"}
        save("POST_committee_registry_read_request.json", read_body)
        capture("POST_committee_registry_read_response.json",
                client.post("/api/committee/registry/read", json=read_body))
        capture("GET_committee_access_log.json", client.get("/api/committee/access-log"))
        capture("GET_credentials_status.json", client.get("/api/credentials/status"))
        anchors = capture("GET_anchors.json", client.get("/api/anchors"))
        if anchors.get("roots"):
            day = anchors["roots"][0]["day"]
            capture("POST_anchors_submit_response.json",
                    client.post(f"/api/anchors/{day}/submit"))
        capture("GET_zk_status.json", client.get("/api/zk/status"))
        patterns = capture("GET_committee_patterns.json", client.get("/api/committee/patterns"))
        panels = patterns.get("panels") or []
        if panels:
            capture("GET_committee_patterns_panel.json",
                    client.get(f"/api/committee/patterns/{panels[0]['panel_id']}"))
        else:
            skipped.append("GET_committee_patterns_panel.json: no panel has three revealed rounds")
        # The calibration programme, with the flag off, which is the state the demo ships in.
        capture("GET_calibration_disclosure.json", client.get("/api/calibration/disclosure"))
        capture("GET_committee_calibration.json", client.get("/api/committee/calibration"))

        # Last, and on a clean store: approving the April alert is the product's opening move, so
        # the pulse it creates has to be the first one -- the round everything else points at.
        # Done here rather than inline because every capture above needs the seeded round intact.
        STORE.reset()
        ALERTS.reset()
        seed_alerts(ALERTS)
        events = client.get("/api/alerts").json().get("events") or []
        headline = next((e for e in events
                         if e["crisis_id"] == "TCD005" and e["metric"] == "index"), None)
        if headline:
            capture("POST_alerts_pulse_response.json",
                    client.post(f"/api/alerts/{headline['id']}/pulse"), expect=201)
        else:
            skipped.append("POST_alerts_pulse_response.json: no TCD005 index event in the replay")

    print(f"{len(written)} fixtures written")
    for name in skipped:
        print(f"  skipped {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
