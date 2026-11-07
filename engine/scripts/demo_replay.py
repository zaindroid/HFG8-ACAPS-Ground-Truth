"""`make demo` -- the whole loop on R1043 with the synthetic panel, offline, in well under 60 seconds.

doorbell -> pulse -> 8 sealed answers -> reveal -> aggregate -> draft -> decision -> ledger -> resolve
-> scores -> calibration. No network: the risk comes from the export, the answers from engine/seeding.py.
This is the smoke test to run before every rehearsal, and the fallback if a live demo goes wrong on stage.

It writes reports/proof.json, which GET /sim/proof serves.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


def step(number: int, label: str) -> None:
    print(f"  {number}. {label}")


def main() -> int:
    started = time.monotonic()
    from engine.api import STORE, SETTINGS, app
    from engine.seeding import seed_demo

    print("Sealed Signals -- full loop on R1043, offline, synthetic panel")
    client = TestClient(app)
    with client:
        pulse_id = seed_demo(STORE, SETTINGS)

        step(1, "risk alert engine: replay Mar2026 -> Apr2026 on ACAPS's own editions")
        from engine.api import ALERTS
        from engine.seeding import seed_alerts

        replay = seed_alerts(ALERTS)
        top = replay["events"][0]
        print(f"       {replay['n_crises']} crises diffed, {len(replay['events'])} events")
        print(f"       rank 1: {top['crisis_id']} {top['crisis_name']} "
              f"{top['metric']} {top['before']} -> {top['after']} ({top['delta']:+.2f}), "
              f"rule: {top['rule_hit']}")
        print(f"       linked risk {top['risk_id']}, reliability {top['reliability']}, "
              f"status {top['status']} -- proposed, not fired")
        if not (top["crisis_id"] == "TCD005" and top["rank_this_month"] == 1
                and abs(top["delta"] - 0.8) < 1e-9):
            return _fail("the April 2026 replay no longer reproduces the TCD005 event")

        step(2, "doorbell (the risk's own ACAPS triggers)")
        doorbell = client.post("/api/pulses/doorbell/run?threshold=40").json()
        print(f"       {doorbell['n_shifts']} triggers at or above 40% completion across active risks")

        step(3, f"pulse {pulse_id}")
        pulse = client.get(f"/api/pulses/{pulse_id}").json()
        question = pulse["question"]
        print(f"       {len(pulse['evidence'])} evidence lines, deadline {question['deadline']}, "
              f"from the {question['source'].replace('_', ' ')}")
        print(f"       question: {question['text'][:70]}...")

        step(4, "reach: the question goes to the channel each expert already uses")
        sent = client.post(f"/api/reach/pulses/{pulse_id}/send", json={}).json()
        channels = sorted({row["channel"] for row in sent["sent"]})
        print(f"       {sent['n_sent']} messages composed on {', '.join(channels)}")
        for refused in sent["refused"][:2]:
            print(f"       refused: {refused['why'][:76]}")
        print(f"       {sent['transport_note'][:96]}")

        step(5, "a reply by SMS, parsed into the same Answer record")
        reply_pulse = client.post("/api/pulses", json={"risk_id": "R1043",
                                                       "reason": "analyst"}).json()
        from engine.api import STORE as _STORE

        reply_token = _STORE.issue_token(reply_pulse["id"], "X-syn-01")
        reply = client.post("/api/inbound/sms", json={
            "token": reply_token, "text": "soixante-dix pour cent, assez sur"}).json()
        print(f"       read {', '.join(reply['parsed']['read'])} -> "
              f"{reply['act']}, commitment {reply['commitment'][:16]}...")

        step(6, "sealed answers")
        tray = client.get(f"/api/pulses/{pulse_id}/tray").json()
        print(f"       {tray['n_answers']} envelopes, revealable={tray['revealable']} (k_min={tray['k_min']})")
        print(f"       first commitment {tray['envelopes'][0]['commitment'][:24]}...")

        step(7, "reveal at the deadline (forced here, and the result says so)")
        result = client.post(f"/api/pulses/{pulse_id}/reveal", json={"force": True}).json()
        print(f"       n={result['n']} mean={result['mean']} spread="
              f"{result['spread']['min']}-{result['spread']['max']} iqr={result['spread']['iqr']}")
        print(f"       weighted (secondary)={result['weighted_mean']}  "
              f"sp(experimental)={result['sp_experiment']['answer']}")
        print(f"       revealed_reason={result['revealed_reason']}  "
              f"{result['number_note'][:72]}")
        for item in result["disagreement"]:
            print(f"       disagreement ({item['n']} {item['position']}): {item['summary'][:70]}")
        print(f"       {result['verification_queue_count']} lines held for verification")
        if "integrity_notes" in result:
            return _fail("integrity notes leaked into the public reveal response")
        if "probe_summary" in result:
            return _fail("the closed follow-up counts leaked into the public reveal response")

        step(8, "integrity notes (moderator only)")
        notes = client.get(f"/api/integrity/{pulse_id}").json()["integrity_notes"]
        for note in notes:
            print(f"       [{note['kind']}] {note['text'][:72]}")
        if not notes:
            print("       none on this round")

        step(9, "draft")
        drafted = client.post(f"/api/pulses/{pulse_id}/draft").json()
        print(f"       {drafted['id']} proposes {drafted['proposed_probability']} "
              f"(ACAPS: {drafted['acaps_probability']}), {len(drafted['claims'])} claims")
        print(f"       judge coverage={drafted['judge']['coverage']} "
              f"numbers_match={drafted['judge']['numbers_match']} "
              f"flagged={drafted['judge']['flagged_claim_ids'] or 'none'}")

        step(10, "question contract")
        client.post(f"/api/risks/R1043/contract", json={
            "event": "Sustained cross-border attacks on eastern Chad border localities",
            "location": "Ouaddai, Wadi Fira and Sila, Chad",
            "horizon_deadline": "2027-05-07",
            "resolution_source": "ACAPS Risk Radar status field",
            "adjudication_rule": "Materialised if ACAPS marks the risk materialised by the deadline.",
        })

        step(11, "analyst decision")
        decided = client.post(f"/api/drafts/{drafted['id']}/decision", json={
            "action": "accept", "decided_by": "analyst-demo",
            "what_decision": "Pre-position shelter and cash in Ouaddai",
            "for_whom": "NGO preparedness lead, eastern Chad",
            "by_when": "2026-11-20",
        }).json()
        print(f"       {decided['status']} by {decided['decided_by']}")

        step(12, "ledger")
        entry = client.get("/api/ledger").json()["entries"][0]
        print(f"       group={entry['group_probability']} acaps={entry['acaps_probability']} "
              f"verify_hash={entry['verify_hash'][:24]}...")
        verified = client.post("/api/ledger/verify", json={"verify_hash": entry["verify_hash"]}).json()
        print(f"       verify: valid={verified['valid']} over {verified['n_commitments']} commitments")
        if not verified["valid"]:
            return _fail("the ledger entry did not verify against its own commitments")

        step(13, "resolve and score")
        resolved = client.post("/api/risks/R1043/resolve", json={"outcome": "materialised"}).json()
        print(f"       {resolved['scores_written']} scores written, weights updated")

        step(14, "outcome report")
        report = client.get(f"/api/pulses/{pulse_id}/outcome-report").json()
        print(f"       outcome={report['outcome']} decision={report['analyst_decision_summary'][:48]}")

        step(15, "closing the loop: what each expert who answered is told")
        closed = client.post(f"/api/reach/pulses/{pulse_id}/close-the-loop").json()
        print(f"       {closed['n_sent']} messages, in the language each contact reads")
        if closed["sent"]:
            print(f"       “{closed['sent'][0]['body'][:150]}”")

        elapsed = time.monotonic() - started
        proof = {
            "risk_id": "R1043",
            "pulse_id": pulse_id,
            "n": result["n"],
            "panel_mean": result["mean"],
            "acaps_probability": entry["acaps_probability"],
            "acaps_assumed_number": entry["honesty"].get("agreement") and None,
            "proposed": drafted["proposed_probability"],
            "decision": decided["status"],
            "verify_hash": entry["verify_hash"],
            "verify_valid": verified["valid"],
            "integrity_notes": len(notes),
            "alert_replay": {
                "months": [replay["month_from"], replay["month_to"]],
                "n_crises": replay["n_crises"],
                "rank_1": top["crisis_id"],
                "delta": top["delta"],
            },
            "scores_written": resolved["scores_written"],
            "reach": {
                "messages_composed": sent["n_sent"],
                "channels": channels,
                "refused_by_a_cadence_or_consent_rule": sent["n_refused"],
                "loop_closed_to": closed["n_sent"],
                "transport": "recorded -- no provider is configured in this build",
            },
            "seconds": round(elapsed, 2),
            "offline": True,
            "synthetic_panel": True,
            "assumptions": [
                "Probability band to number is this build's assumption, not an ACAPS mapping.",
                "Experts are synthetic; their answers are not evidence about Chad.",
                "Sealing proves timing and consistency, not confidentiality from the operator.",
                "A single round is a sensitivity test, not proof that the method works.",
            ],
        }
        out = ROOT / "reports"
        out.mkdir(exist_ok=True)
        (out / "proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")

    print(f"\nloop complete in {elapsed:.2f}s -- reports/proof.json written")
    if elapsed > 60:
        return _fail(f"the loop took {elapsed:.1f}s; the stage budget is 60s")
    return 0


def _fail(message: str) -> int:
    print(f"\nFAILED: {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
