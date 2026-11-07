"""Sealed Signals API skeleton. Serves /health and, until Lane A replaces them, every fixture from ../fixtures so Lane B
can build against real-shaped responses from minute one. Replace routes one by one; keep the fixtures true."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

FIX = Path(__file__).resolve().parents[2] / "fixtures"
app = FastAPI(title="Sealed Signals", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


def fixture(name: str) -> dict:
    p = FIX / name
    if not p.exists():
        raise HTTPException(501, f"not implemented yet; fixture {name} missing")
    body = json.loads(p.read_text(encoding="utf-8"))
    body["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return body


@app.get("/health")
def health():
    return fixture("GET_health.json")

@app.get("/risks")
def risks():
    return fixture("GET_risks.json")

@app.get("/risks/{risk_id}")
def risk(risk_id: str):
    return fixture(f"GET_risks_{risk_id}.json")

@app.post("/pulses", status_code=201)
def create_pulse(body: dict):
    return fixture("POST_pulses_response.json")

@app.post("/pulses/doorbell/run")
def doorbell():
    return fixture("POST_pulses_doorbell_run_response.json")

@app.get("/e/{token}")
def card(token: str):
    return fixture("GET_e_token.json")

@app.post("/e/{token}/answer", status_code=201)
def answer(token: str, body: dict):
    return fixture("POST_e_token_answer_response.json")

@app.post("/pulses/{pulse_id}/reveal")
def reveal(pulse_id: str):
    return fixture("POST_pulses_reveal_response.json")

@app.get("/pulses/{pulse_id}/result")
def result(pulse_id: str):
    return fixture("GET_pulses_result.json")

@app.post("/pulses/{pulse_id}/draft")
def draft(pulse_id: str):
    return fixture("POST_pulses_draft_response.json")

@app.post("/drafts/{draft_id}/decision")
def decision(draft_id: str, body: dict):
    return fixture("POST_drafts_decision_response.json")

@app.get("/ledger")
def ledger():
    return fixture("GET_ledger.json")

@app.post("/ledger/verify")
def verify(body: dict):
    return fixture("POST_ledger_verify_response.json")

@app.get("/me/{token}/calibration")
def calibration(token: str):
    return fixture("GET_me_calibration.json")

@app.get("/analyst/board")
def board():
    return fixture("GET_analyst_board.json")

@app.get("/sim/proof")
def proof():
    return fixture("GET_sim_proof.json")


@app.get("/radar/status")
def radar_status():
    return fixture("GET_radar_status.json")

@app.post("/experts/apply", status_code=201)
def experts_apply(body: dict):
    return fixture("POST_experts_apply_response.json")

@app.get("/panels/match")
def panels_match(risk_id: str = "R1043"):
    return fixture("GET_panels_match.json")

@app.get("/integrity/{pulse_id}")
def integrity(pulse_id: str):
    return fixture("GET_integrity_pulse.json")


@app.post("/risks/{risk_id}/contract", status_code=201)
def freeze_contract(risk_id: str, body: dict):
    return fixture("GET_risks_R1043.json")

@app.get("/pulses/{pulse_id}/outcome-report")
def outcome_report(pulse_id: str):
    return fixture("GET_pulses_outcome_report.json")


@app.post("/alerts/run")
def alerts_run(body: dict | None = None):
    return fixture("POST_alerts_run_response.json")

@app.post("/alerts/replay")
def alerts_replay(body: dict | None = None):
    return fixture("POST_alerts_replay_response.json")

@app.get("/alerts")
def alerts():
    return fixture("GET_alerts.json")

@app.post("/alerts/{alert_id}/pulse", status_code=201)
def alerts_pulse(alert_id: str):
    return fixture("POST_alerts_pulse_response.json")

@app.get("/crises/{crisis_id}")
def crisis(crisis_id: str):
    return fixture("GET_crises_TCD005.json")
