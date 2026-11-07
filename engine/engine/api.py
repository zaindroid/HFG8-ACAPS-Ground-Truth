"""Sealed Signals API.

Routes follow MASTER_PROMPT section 5. The three platform routes /health, /ready and /version come from the
deployment contract: /health must not touch any dependency, because a slow check there marks every app on the
node unhealthy at once.

The built UI, when present, is served under /app -- the API keeps the root namespace, because /ledger and
/e/{token} are API routes in section 5 and cannot also be HTML pages.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import acaps, alerts as alert_engine, data, draft as draft_builder, logging_conf, settings as settings_mod
from . import probes
from .store import Expert, Store, TooFew, now, pseudonym_for, round_verify_hash

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures"
UI_DIST = ROOT / "ui" / "dist"

log = logging.getLogger("sealed_signals")
SETTINGS = settings_mod.load()
STORE = Store(k_min=SETTINGS.k_min)
ALERTS = alert_engine.new_store()
_subscribers: set[asyncio.Queue] = set()


def envelope(payload: dict) -> dict:
    """Every response carries served_from and generated_at (section 4)."""
    return {**payload, "served_from": "live", "generated_at": now()}


async def publish(event: str, payload: dict) -> None:
    for queue in list(_subscribers):
        try:
            queue.put_nowait((event, payload))
        except asyncio.QueueFull:
            _subscribers.discard(queue)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_conf.configure(SETTINGS.log_level)
    logging_conf.log(log, "info", "starting", app_env=SETTINGS.app_env, sha=SETTINGS.git_sha,
                     k_min=SETTINGS.k_min, ui_built=UI_DIST.exists())
    if os.environ.get("SEED_ON_START", "true").lower() == "true":
        from .seeding import seed_alerts, seed_demo
        pulse_id = seed_demo(STORE, SETTINGS)
        replay = seed_alerts(ALERTS)
        logging_conf.log(log, "info", "seeded synthetic panel", pulse_id=pulse_id,
                         n_experts=len(STORE.experts), n_answers=STORE.n_answers(pulse_id),
                         n_alerts=len(replay["events"]), replay=f"{replay['month_from']}->{replay['month_to']}")
    yield
    logging_conf.log(log, "info", "shutting down")


app = FastAPI(
    title="Sealed Signals",
    version="0.2.0",
    description="A small trusted panel challenges and forecasts ACAPS risk analyses in one minute, "
                "behind a mask each expert chooses.",
    lifespan=lifespan,
)
# Business routes live on this router and are served under /api. The UI owns the root namespace:
# /desk, /ledger and /e/{token} are its pages, so they cannot also be API paths.
api = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https://.*\.zaindroid\.me",
    allow_methods=["*"],
    allow_headers=["*"],
)


def fixture(name: str) -> dict:
    path = FIX / name
    if not path.exists():
        raise HTTPException(501, f"not implemented yet; fixture {name} missing")
    return envelope(json.loads(path.read_text(encoding="utf-8")))


# -- platform contract ---------------------------------------------------------
@app.get("/health", tags=["platform"])
def health():
    """Deliberately dependency-free: no CSV read, no store walk."""
    return {"status": "ok", "service": "sealed-signals"}


@app.get("/ready", tags=["platform"])
def ready():
    try:
        n_risks = len(data.all_risks())
    except Exception as exc:  # noqa: BLE001 -- readiness reports, it does not raise
        logging_conf.log(log, "error", "readiness failed", error=type(exc).__name__)
        return JSONResponse({"status": "not_ready", "reason": "risk export unreadable"}, status_code=503)
    if not n_risks:
        return JSONResponse({"status": "not_ready", "reason": "risk export empty"}, status_code=503)
    return {"status": "ready", "n_risks": n_risks, "ui_built": UI_DIST.exists()}


@app.get("/version", tags=["platform"])
def version():
    return {"sha": SETTINGS.git_sha, "built": SETTINGS.built_at, "app": "sealed-signals",
            "api": app.version, "env": SETTINGS.app_env}


# -- radar and risks -----------------------------------------------------------
@api.get("/radar/status", tags=["risks"])
def radar_status():
    """Where every number on screen came from. The badges on the desk read straight off this."""
    csv_status = data.radar_status()
    api_status = acaps.status()
    return envelope({
        "risk_list": {
            "source": csv_status["source"],
            "fetched_at": csv_status["fetched_at"],
            "n": csv_status["n_risks"],
            "n_active": csv_status["n_active"],
            "api_n": api_status["api_risk_list"]["n"],
            "api_last_update": api_status["api_risk_list"]["last_update"],
            "note": api_status["api_risk_list"]["note"],
        },
        "editions": api_status["editions"],
        "token_present": api_status["token_present"],
        "probability_assumption": csv_status["probability_assumption"],
        # Kept so nothing that reads the flat shape breaks; the nested fields above are the contract.
        "source": csv_status["source"],
        "n_risks": csv_status["n_risks"],
        "n_active": csv_status["n_active"],
        "live_available": api_status["token_present"],
    })


@api.get("/radar/editions", tags=["radar"])
def radar_editions():
    months = acaps.available()
    return envelope({
        "datasets": [
            {
                "dataset": dataset,
                "months": month_list,
                "latest": month_list[-1] if month_list else None,
                "source": "api" if acaps.token_present() else "cache",
            }
            for dataset, month_list in months.items()
        ],
        "token_present": acaps.token_present(),
        "note": "Cached editions ship in data/acaps-api/ so this runs with no network. "
                "Set ACAPS_API_TOKEN to fetch live.",
    })


# -- crises --------------------------------------------------------------------
@api.get("/crises", tags=["radar"])
def crises(iso3: str | None = None, limit: int = 400):
    rows = list(acaps.crises().values())
    if iso3:
        wanted = iso3.strip().upper()
        rows = [c for c in rows if wanted in {code.upper() for code in c["iso3"]}]
    return envelope({"crises": rows[:limit], "n": len(rows)})


@api.get("/crises/{crisis_id}", tags=["radar"])
def crisis(crisis_id: str):
    found = acaps.crisis(crisis_id)
    if not found:
        raise HTTPException(404, f"no crisis {crisis_id} in the ACAPS registry")
    linked = [risk_id for risk_id, link in ALERTS.links.items() if link["crisis_id"] == crisis_id]
    suggested = [s["risk_id"] for s in alert_engine.suggest_links() if s["crisis_id"] == crisis_id]
    return envelope({
        **found,
        "linked_risks": linked,
        "suggested_risks": [r for r in suggested if r not in linked],
        "series": acaps.series(crisis_id),
        "access": acaps.access_by_month(crisis_id),
        "latest": acaps.severity_point(crisis_id, acaps.latest_month() or ""),
    })


# -- the risk alert engine -----------------------------------------------------
@api.post("/alerts/run", tags=["alerts"])
def alerts_run(body: dict = Body(default_factory=dict)):
    """Diff the two most recent cached editions (or those ending at month_to) for every crisis."""
    month_from, month_to = alert_engine.latest_pair(month_to=body.get("month_to"))
    if not month_from or not month_to:
        raise HTTPException(409, "at least two cached editions are needed before anything can be diffed")
    result = alert_engine.run(ALERTS, month_from, month_to)
    logging_conf.log(log, "info", "alert run", month_from=month_from, month_to=month_to,
                     n_events=len(result["events"]))
    return envelope(result)


@api.post("/alerts/replay", tags=["alerts"])
def alerts_replay(body: dict = Body(default_factory=dict)):
    """Reproduce a past month from the cached editions. The demo opens on Mar2026 -> Apr2026."""
    month_from = body.get("month_from") or "Mar2026"
    month_to = body.get("month_to") or "Apr2026"
    available = acaps.available().get(acaps.INFORM, [])
    missing = [m for m in (month_from, month_to) if m not in available]
    if missing:
        raise HTTPException(404, f"no cached edition for {', '.join(missing)}; have {available}")
    return envelope(alert_engine.run(ALERTS, month_from, month_to))


@api.get("/alerts", tags=["alerts"])
def list_alerts(status: str | None = None):
    rows = list(ALERTS.events.values())
    if status:
        rows = [e for e in rows if e["status"] == status]
    rows.sort(key=lambda e: (e["metric"] != "index", e["direction"] != "deterioration",
                             e["rank_this_month"]))
    return envelope({"events": rows, "n": len(rows), "rules": alert_engine.RULES})


@api.get("/alerts/{alert_id}", tags=["alerts"])
def get_alert(alert_id: str):
    found = ALERTS.events.get(alert_id)
    if not found:
        raise HTTPException(404, f"no alert {alert_id}")
    return envelope(found)


@api.post("/alerts/{alert_id}/pulse", status_code=201, tags=["alerts"])
async def alert_to_pulse(alert_id: str, body: dict = Body(default_factory=dict)):
    """The analyst approves an event. Only here does an alert become a question for the panel."""
    event = ALERTS.events.get(alert_id)
    if not event:
        raise HTTPException(404, f"no alert {alert_id}")
    if event["status"] == "dismissed":
        raise HTTPException(409, "this event was dismissed; a dismissed event never pulses")
    if event["status"] == "pulsed":
        raise HTTPException(409, f"already pulsed as {event['pulse_id']}")

    risk_id = body.get("risk_id") or event.get("risk_id")
    if not risk_id:
        raise HTTPException(422, "this event has no linked risk; confirm one with POST /risks/{id}/link")
    risk = data.get_risk(risk_id)
    if not risk:
        raise HTTPException(404, f"no risk {risk_id} in the export")

    pulse = _build_pulse(risk, "doorbell", body.get("question"), _alert_evidence(event))
    pulse["alert_id"] = alert_id
    event["status"] = "pulsed"
    event["pulse_id"] = pulse["id"]
    await publish("pulse_fired", {"pulse_id": pulse["id"], "risk_id": risk_id, "alert_id": alert_id})
    logging_conf.log(log, "info", "alert approved into a pulse", alert_id=alert_id,
                     pulse_id=pulse["id"], risk_id=risk_id)
    # Returned as the event itself: the UI reads status and pulse_id off the top level, and the
    # created pulse rides along under "pulse" for callers that want it.
    return envelope({**event, "pulse": pulse})


@api.post("/alerts/{alert_id}/dismiss", tags=["alerts"])
def dismiss_alert(alert_id: str, body: dict = Body(default_factory=dict)):
    event = ALERTS.events.get(alert_id)
    if not event:
        raise HTTPException(404, f"no alert {alert_id}")
    if event["status"] == "pulsed":
        raise HTTPException(409, "this event already became a pulse and cannot be dismissed")
    note = (body.get("note") or "").strip()
    if not note:
        raise HTTPException(422, "dismissing an event requires a note saying why")
    event["status"] = "dismissed"
    event["note"] = note
    event["dismissed_by"] = body.get("dismissed_by") or "analyst"
    event["dismissed_at"] = now()
    return envelope(event)


def _alert_evidence(event: dict) -> list[dict]:
    """The event's own numbers become the pulse's evidence line, so the expert sees what moved."""
    evidence = [{
        "source": "ACAPS INFORM Severity",
        # The edition fields the UI renders on an evidence line: which dataset, which crisis, which
        # two months, and where the move ranked. Without these it falls back to a bare value pair.
        "dataset": "inform-severity-index",
        "crisis_id": event["crisis_id"],
        "metric": event["metric"],
        "month_from": event["month_from"],
        "month_to": event["month_to"],
        "before": event["before"],
        "after": event["after"],
        "delta": event["delta"],
        "rank_this_month": event["rank_this_month"],
        "n_crises_this_month": event["n_crises_this_month"],
        "indicator": f"{event['metric']}:{event['crisis_id']}",
        "value": event["after"],
        "baseline": event["before"],
        "z": None,
        "url": "https://api.acaps.org/api/v1/inform-severity-index/",
        "note": (
            f"{event['crisis_name']}: {event['metric'].replace('_', ' ')} "
            f"{event['before']} to {event['after']} between {event['month_from']} and "
            f"{event['month_to']} ({event['rule_hit']}; rank {event['rank_this_month']} of "
            f"{event['n_crises_this_month']} crises this month; reliability {event['reliability']})"
        ),
    }]
    for name, pair in (event.get("components") or {}).items():
        if pair[0] is None or pair[1] is None or abs(pair[1] - pair[0]) < 0.3:
            continue
        evidence.append({
            "source": f"ACAPS {name.replace('_', ' ')}",
            "dataset": "inform-severity-index",
            "crisis_id": event["crisis_id"],
            "metric": name,
            "month_from": event["month_from"],
            "month_to": event["month_to"],
            "before": pair[0],
            "after": pair[1],
            "delta": round(pair[1] - pair[0], 2),
            "indicator": f"{name}:{event['crisis_id']}",
            "value": pair[1],
            "baseline": pair[0],
            "z": None,
            "url": "https://api.acaps.org/api/v1/inform-severity-index/",
            "note": f"{name.replace('_', ' ')} {pair[0]} to {pair[1]}",
        })
    return evidence


@api.post("/risks/{risk_id}/link", status_code=201, tags=["alerts"])
def link_risk(risk_id: str, body: dict = Body(default_factory=dict)):
    """The analyst confirms the risk-to-crisis link once. Suggestions are iso3 plus a driver keyword;
    a wrong link would put real ACAPS numbers behind the wrong question."""
    risk = data.get_risk(risk_id)
    if not risk:
        raise HTTPException(404, f"no risk {risk_id} in the export")
    crisis_id = body.get("crisis_id")
    if not crisis_id:
        raise HTTPException(422, "crisis_id is required")
    if not acaps.crisis(crisis_id):
        raise HTTPException(404, f"no crisis {crisis_id} in the ACAPS registry")
    link = alert_engine.confirm_link(ALERTS, risk_id, crisis_id, body.get("confirmed_by") or "analyst")
    return envelope(link)


@api.get("/risks/{risk_id}/link", tags=["alerts"])
def get_link(risk_id: str):
    confirmed = ALERTS.links.get(risk_id)
    suggestions = [s for s in alert_engine.suggest_links() if s["risk_id"] == risk_id]
    return envelope({"risk_id": risk_id, "confirmed": confirmed, "suggested": suggestions})


@api.get("/risks", tags=["risks"])
def risks(status: str = "Active", limit: int = 200):
    rows = data.active_risks() if status.lower() == "active" else data.all_risks()
    return envelope({"risks": rows[:limit], "n": len(rows), "filter": status})


@api.get("/risks/{risk_id}", tags=["risks"])
def risk(risk_id: str):
    found = data.get_risk(risk_id)
    if not found:
        raise HTTPException(404, f"no risk {risk_id} in the export")
    return envelope(found)


@api.post("/risks/{risk_id}/contract", status_code=201, tags=["risks"])
def freeze_contract(risk_id: str, body: dict = Body(default_factory=dict)):
    """A frozen question contract is required before any scoring (section 5)."""
    found = data.get_risk(risk_id)
    if not found:
        raise HTTPException(404, f"no risk {risk_id} in the export")
    required = ("event", "location", "horizon_deadline", "resolution_source", "adjudication_rule")
    missing = [field for field in required if not body.get(field)]
    if missing:
        raise HTTPException(422, f"a question contract needs: {', '.join(missing)}")
    contract = {**{field: body[field] for field in required}, "risk_id": risk_id, "frozen_at": now()}
    STORE.contracts[risk_id] = contract
    return envelope(contract)


# -- experts and panels --------------------------------------------------------
@api.post("/experts/apply", status_code=201, tags=["panel"])
def experts_apply(body: dict = Body(default_factory=dict)):
    expert = STORE.add_expert(Expert(
        id=f"X-{uuid.uuid4().hex[:8]}",
        geo_tags=body.get("geo_tags") or [],
        theme_tags=body.get("theme_tags") or [],
        affiliation_tag=body.get("affiliation_tag") or "ngo",
        languages=body.get("languages") or ["en"],
        channel=body.get("channel") or "email",
        status="applied",
        region=body.get("region") or "",
        synthetic=bool(body.get("synthetic", True)),
    ))
    return envelope({"expert_id": expert.id, "status": expert.status,
                     "approvals_required": 2,
                     "note": "Approval needs two admins before this expert can be matched to a panel."})


@api.post("/experts/{expert_id}/approve", status_code=201, tags=["panel"])
def approve_expert(expert_id: str, body: dict = Body(default_factory=dict)):
    """Committee approval. Two distinct admins are required, so one admin approving twice does not
    make a panel member -- the second call from the same admin is refused rather than counted."""
    expert = STORE.experts.get(expert_id)
    if not expert:
        raise HTTPException(404, f"no expert {expert_id}")
    admin = (body.get("admin") or "").strip()
    if not admin:
        raise HTTPException(422, "admin is required: an approval has to be attributable to someone")

    approvals = STORE.approvals.setdefault(expert_id, [])
    if admin in approvals:
        raise HTTPException(409, f"{admin} has already approved this expert; a second admin is needed")
    approvals.append(admin)

    if len(approvals) >= 2 and expert.status != "approved":
        expert.status = "approved"
    return envelope({
        "expert_id": expert_id,
        "status": expert.status,
        "approvals": approvals,
        "approvals_required": 2,
        "credential_issued": expert.status == "approved",
        "note": "Approved experts can be matched to a panel."
        if expert.status == "approved"
        else f"{2 - len(approvals)} more approval(s) needed, from a different admin.",
    })



def _track_record(expert_id: str) -> dict:
    """An expert's record on risks the Risk List has already resolved.

    Reported only above five resolved forecasts, the same floor the board and the private
    calibration report use: fewer than that is noise wearing a number. `moved_before_acaps`
    counts the times the expert was on the correct side of 0.5 while the ACAPS band for that
    risk was not -- the cases where asking would have changed the picture.
    """
    mine = [s for s in STORE.scores if s["expert_internal_id"] == expert_id]
    if len(mine) < 5:
        return {"n_resolved": len(mine), "reported": False,
                "note": "A track record opens after five resolved forecasts."}
    briers = [s["brier"] for s in mine]
    scored = [s for s in mine if s.get("probability") is not None and s.get("outcome")]
    right = sum(1 for s in scored
                if (s["probability"] >= 0.5) == (s["outcome"].lower() == "materialised"))
    earlier = 0
    for s in scored:
        band = data.band_to_number(s.get("acaps_band"))
        if band is None:
            continue
        truth = s["outcome"].lower() == "materialised"
        if ((s["probability"] >= 0.5) == truth) and ((band >= 0.5) != truth):
            earlier += 1
    expert = STORE.experts.get(expert_id)
    return {
        "reported": True,
        "n_resolved": len(mine),
        "mean_brier": round(sum(briers) / len(briers), 4),
        "hit_rate": round(right / len(scored), 4) if scored else None,
        "moved_before_acaps": earlier,
        "reliability_weight": round(expert.weight, 4) if expert else 1.0,
        "on_theme_share": round(
            sum(1 for s in mine if s.get("on_theme")) / len(mine), 4),
    }



@api.get("/insights", tags=["radar"])
def insights():
    """How the Risk List has actually performed, computed from the export the engine loaded.

    The UI shipped these as a build-time file; served here they follow whatever data the
    engine is reading, so the charts cannot quietly describe a different dataset from the
    one answering /risks. Resolved risks only: active ones have no outcome to count.
    """
    rows = data.all_risks()
    resolved = [r for r in rows if r["status"].lower() in ("materialised", "not materialised")]

    def tally(key: str, order: list[str]):
        out = []
        for value in order:
            group = [r for r in resolved if (r.get(key) or "") == value]
            if not group:
                continue
            hit = sum(1 for r in group if r["status"].lower() == "materialised")
            row = {"label": value, "n": len(group), "materialised": hit,
                   "rate": round(hit / len(group), 4)}
            if key == "probability_acaps":
                row["expected"] = data.band_to_number(value)
            out.append(row)
        return out

    bands = ["Very Low", "Low", "Medium", "High", "Very High"]
    matrix = []
    for band in bands:
        for impact in range(1, 6):
            cell = [r for r in resolved
                    if (r.get("probability_acaps") or "") == band and r.get("impact_acaps") == impact]
            hit = sum(1 for r in cell if r["status"].lower() == "materialised")
            matrix.append({"probability": band, "impact": impact, "n": len(cell),
                           "materialised": hit,
                           "rate": round(hit / len(cell), 4) if cell else None})
    return envelope({
        "source": "ACAPS Risk List as loaded by this engine",
        "totals": {
            "risks": len(rows),
            "resolved": len(resolved),
            "active": sum(1 for r in rows if r["status"].lower().startswith("active")),
            "materialised": sum(1 for r in resolved if r["status"].lower() == "materialised"),
            "countries": len({c.strip() for r in rows for c in r["country"].split(",") if c.strip()}),
        },
        "calibration": tally("probability_acaps", bands),
        "by_level": tally("level", ["Low", "Medium", "High"]),
        "matrix": matrix,
    })


@api.get("/panels/match", tags=["panel"])
def panels_match(risk_id: str = "R1043"):
    """The best-matched approved experts, plus the composition check. Caps matter more than scores:
    a panel of eight from one organisation is not a panel."""
    found = data.get_risk(risk_id)
    if not found:
        raise HTTPException(404, f"no risk {risk_id} in the export")
    risk_themes = {theme for trigger in found["triggers"]
                   for theme in [_theme(trigger)] if theme}
    iso = {code.strip() for code in found["country_iso"].split(",")}
    # Stage guests hold open links for the QR step; they are not vetted expertise and must
    # not be matched onto a panel ahead of someone who is.
    approved = [e for e in STORE.experts.values()
                if e.status == "approved" and e.affiliation_tag != "guest"]

    def score(expert: Expert) -> tuple[int, int]:
        return (len(set(expert.theme_tags) & risk_themes), len(set(expert.geo_tags) & iso))

    ranked = sorted(approved, key=lambda e: (-sum(score(e)), e.id))
    chosen: list[Expert] = []
    per_affiliation: dict[str, int] = {}
    for expert in ranked:
        if per_affiliation.get(expert.affiliation_tag, 0) >= 3:
            continue
        chosen.append(expert)
        per_affiliation[expert.affiliation_tag] = per_affiliation.get(expert.affiliation_tag, 0) + 1
        if len(chosen) == 8:
            break
    covered = {theme for expert in chosen for theme in expert.theme_tags}
    return envelope({
        "risk_id": risk_id,
        "panel_id": f"PAN-{found['country_iso'].split(',')[0].strip()}",
        "k_min": STORE.k_min,
        "experts": [{"expert_id": e.id, "pseudonym": pseudonym_for(e.id, SETTINGS.pseudonym_key),
                     "theme_tags": e.theme_tags, "geo_tags": e.geo_tags,
                     "affiliation_tag": e.affiliation_tag, "region": e.region,
                     # How well this expert fits: themes matched plus country matched, over what
                     # the risk asks for. Shown so a panel can be argued with, not just accepted.
                     "match": round(sum(score(e)) / max(1, len(risk_themes) + 1), 4),
                     "languages": e.languages,
                     "years_experience": e.years_experience,
                     "track_record": _track_record(e.id),
                     "synthetic": e.synthetic} for e in chosen],
        "composition": {
            "max_per_affiliation": 3,
            "per_affiliation": per_affiliation,
            "theme_cover": sorted(covered & risk_themes),
            "themes_wanted": sorted(risk_themes),
            "themes_uncovered": sorted(risk_themes - covered),
            "gaps": sorted(risk_themes - covered),
            "geo_spread": sorted({e.region for e in chosen if e.region}),
            # The panel is only "ok" when it clears k_min, covers every theme the risk names, and
            # no single organisation holds more than three seats.
            "ok": (
                len(chosen) >= STORE.k_min
                and not (risk_themes - covered)
                and all(count <= 3 for count in per_affiliation.values())
            ),
        },
        "n_approved_available": len(approved),
    })


def _theme(trigger: dict) -> str | None:
    from .store import _theme_of_trigger
    return _theme_of_trigger(trigger)


# -- pulses --------------------------------------------------------------------
def _build_pulse(risk: dict, reason: str, question: str | None, evidence: list[dict]) -> dict:
    pulse_id = f"P-{len(STORE.pulses) + 1:04d}"
    # The default question must not name the ACAPS band. The card claims the rating is hidden until
    # submission, and a question that quotes it would anchor the answer it is trying to collect --
    # which is exactly what the blind round exists to prevent.
    blind_question = (
        "Is the level of concern on this risk still right, and what are we missing? "
        "You will see the current ACAPS rating as soon as you submit."
    )
    pulse = {
        "id": pulse_id,
        "risk_id": risk["risk_id"],
        "panel_id": f"PAN-{risk['country_iso'].split(',')[0].strip()}",
        "fired_at": now(),
        "reason": reason,
        "round": 1,
        "evidence": evidence,
        "question": question or blind_question,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(timespec="seconds"),
        "n_answers": 0,
    }
    STORE.pulses[pulse_id] = pulse
    return pulse


@api.post("/pulses", status_code=201, tags=["pulse"])
async def create_pulse(body: dict = Body(default_factory=dict)):
    risk_id = body.get("risk_id") or "R1043"
    found = data.get_risk(risk_id)
    if not found:
        raise HTTPException(404, f"no risk {risk_id} in the export")
    pulse = _build_pulse(found, body.get("reason") or "analyst", body.get("question"),
                         body.get("evidence") or _trigger_evidence(found))
    await publish("pulse_fired", {"pulse_id": pulse["id"], "risk_id": risk_id})
    logging_conf.log(log, "info", "pulse fired", pulse_id=pulse["id"], risk_id=risk_id,
                     reason=pulse["reason"])
    return envelope(pulse)


def _trigger_evidence(risk: dict) -> list[dict]:
    """ACAPS's own trigger completion rate is the honest default signal: a published judgement,
    not a number we invented. z is reported as null because a single reading has no baseline."""
    evidence = []
    for trigger in risk["triggers"]:
        if trigger.get("completion_rate") is None:
            continue
        evidence.append({
            # A completion rate is a single published percentage: it has no baseline and no z-score.
            # Sending baseline 0 made every renderer print "40 versus 0 baseline", which reads as a
            # comparison that was never made. The statement goes in the label instead.
            "source": f"{trigger['title']} - {trigger['completion_rate']}% complete",
            "indicator": f"trigger_completion:{trigger['id']}",
            "value": trigger["completion_rate"],
            "baseline": None,
            "z": None,
            "url": (trigger.get("sources") or [{}])[0].get("url", "https://www.acaps.org/en/countries"),
            "note": trigger["title"],
        })
    return evidence


@api.get("/pulses/{pulse_id}", tags=["pulse"])
def get_pulse(pulse_id: str):
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    return envelope({**pulse, "n_answers": STORE.n_answers(pulse_id)})


@api.post("/pulses/doorbell/run", tags=["pulse"])
async def doorbell_run(threshold: int = 40, fire: bool = False):
    """One pass of the detector over the open triggers of active risks. It watches the risk's own
    triggers, not a generic news feed, which is the whole point of the doorbell."""
    shifts, fired = [], []
    for risk in data.active_risks():
        for trigger in risk["triggers"]:
            rate = trigger.get("completion_rate")
            if rate is None or rate < threshold:
                continue
            shifts.append({
                "risk_id": risk["risk_id"], "country": risk["country"],
                "trigger_id": trigger["id"], "acaps_trigger_id": trigger.get("acaps_trigger_id"),
                "title": trigger["title"], "completion_rate": rate,
                "acaps_probability": risk.get("probability_acaps"),
            })
    shifts.sort(key=lambda s: s["completion_rate"], reverse=True)
    if fire:
        for shift in shifts[:3]:
            risk = data.get_risk(shift["risk_id"])
            pulse = _build_pulse(risk, "doorbell", None, _trigger_evidence(risk))
            fired.append({"pulse_id": pulse["id"], "risk_id": risk["risk_id"]})
            await publish("pulse_fired", {"pulse_id": pulse["id"], "risk_id": risk["risk_id"]})
    return envelope({"threshold": threshold, "shifts": shifts, "pulses_fired": fired,
                     "n_shifts": len(shifts),
                     "note": "Signal is the ACAPS trigger completion rate. Pass fire=true to open pulses."})


@api.get("/pulses/{pulse_id}/tray", tags=["pulse"])
def tray(pulse_id: str):
    """Sealed envelopes: commitment and time, never a value. This is what the desk may show
    before the reveal."""
    if pulse_id not in STORE.pulses:
        raise HTTPException(404, f"no pulse {pulse_id}")
    envelopes = STORE.tray(pulse_id)
    return envelope({"pulse_id": pulse_id, "n_answers": len(envelopes), "k_min": STORE.k_min,
                     "revealable": len(envelopes) >= STORE.k_min, "envelopes": envelopes})


# -- the expert card -----------------------------------------------------------

def _expert_profile(expert_id: str) -> dict:
    expert = STORE.experts.get(expert_id)
    if not expert:
        return {"id": expert_id, "theme_tags": [], "geo_tags": [], "region": ""}
    return {"id": expert.id, "theme_tags": expert.theme_tags,
            "geo_tags": expert.geo_tags, "region": expert.region}


@api.get("/e/{token}", tags=["expert"])
def card(token: str):
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid; ask the analyst for a new one")
    pulse_id, expert_id = resolved
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    risk = data.get_risk(pulse["risk_id"]) or {}
    rnd = 2 if pulse_id in STORE.results else 1
    group_view = None
    if rnd == 2:
        result = STORE.results[pulse_id]
        group_view = {"mean": result["mean"], "distribution": result["distribution"],
                      "spread": result["spread"], "n": result["n"]}
    # The rating is withheld in round 1 so it cannot anchor a first, independent answer. Round 2 is
    # the opposite by design (section 8): it is the informed round, and it shows ACAPS's rating and
    # the group alongside it. Hiding it there would withhold the very evidence round 2 exists to add.
    answered = STORE.answered(pulse_id, expert_id)
    blind = rnd == 1 and not answered
    public_risk = {key: value for key, value in risk.items()
                   if key not in ("probability_acaps", "level", "probability_assumed_number")}
    return envelope({
        "pulse": {**pulse, "n_answers": STORE.n_answers(pulse_id)},
        "risk": public_risk if blind else risk,
        "round": rnd,
        "group_view_if_round2": group_view,
        "already_answered": answered,
        "mask_options": list(("known", "pseudonym", "anonymous")),
        "mask_note": "Distinctive wording can be recognised by peers even under a pseudonym.",
        "stances": ["estimate", "outside_my_expertise", "not_enough_evidence"],
        "source_tags": ["saw", "read", "heard"],
        "accuracy_prompt": "Is this something you saw, read, or heard?",
        "elicitation": "What share of this panel will put the probability above 0.5?",
        "rating_hidden_until_submission": blind,
        "blind": blind,
        # Chosen from the risk record and this expert's own tags, nothing else. The card is
        # therefore fixed when the link is issued and cannot reflect another expert's answer.
        "probe_flow": probes.card_flow(
            risk, _expert_profile(expert_id), pulse.get("evidence")),
        "probe_note": "These follow the scored question and are never aggregated into it.",
    })


@api.post("/e/{token}/answer", status_code=201, tags=["expert"])
async def answer(token: str, body: dict = Body(default_factory=dict)):
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid; ask the analyst for a new one")
    pulse_id, expert_id = resolved
    if pulse_id in STORE.results and int(body.get("round", 1)) == 1:
        raise HTTPException(409, "round 1 is closed on this pulse; this link now opens round 2")
    risk_for_probes = data.get_risk(STORE.pulses[pulse_id]["risk_id"]) or {}
    allowed = probes.accepted_ids(risk_for_probes, _expert_profile(expert_id))
    submitted = body.get("probe_answers") or {}
    if not isinstance(submitted, dict):
        raise HTTPException(422, "probe_answers must be an object keyed by probe id")
    # Only answers to probes this card actually asked are kept, so a crafted request cannot
    # inject a theme the expert was never shown.
    body = {**body, "probe_answers": {k: v for k, v in submitted.items() if k in allowed}}
    try:
        sealed = STORE.seal(pulse_id, expert_id, body, SETTINGS.commitment_salt, SETTINGS.pseudonym_key)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    STORE.mark_used(token)
    await publish("answer_sealed", {"pulse_id": pulse_id, "n_answers": STORE.n_answers(pulse_id)})
    logging_conf.log(log, "info", "answer sealed", pulse_id=pulse_id, mask=sealed.mask,
                     n_answers=STORE.n_answers(pulse_id))
    risk = data.get_risk(STORE.pulses[pulse_id]["risk_id"]) or {}
    return envelope({
        "committed_at": sealed.committed_at,
        "commitment": sealed.commitment,
        "mask": sealed.mask,
        "pseudonym": sealed.pseudonym,
        "message": "Submitted. You will get the group outcome when this resolves.",
        "sealing_note": "The commitment proves when you answered and that you have not changed it. "
                        "It does not hide your answer from the operator of this service.",
        "acaps_rating_now_visible": {"probability_acaps": risk.get("probability_acaps"),
                                     "level": risk.get("level")},
    })


# -- reveal and aggregate ------------------------------------------------------
@api.post("/pulses/{pulse_id}/reveal", tags=["round"])
async def reveal(pulse_id: str):
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    risk = data.get_risk(pulse["risk_id"]) or {}
    try:
        result = STORE.reveal(pulse_id, risk)
    except TooFew as exc:
        raise HTTPException(409, str(exc)) from exc
    await publish("round_revealed", {"pulse_id": pulse_id})
    logging_conf.log(log, "info", "round revealed", pulse_id=pulse_id, n=result["n"])
    return envelope(_public_result(result))


@api.get("/pulses/{pulse_id}/result", tags=["round"])
def result(pulse_id: str):
    found = STORE.results.get(pulse_id)
    if not found:
        raise HTTPException(404, f"pulse {pulse_id} has not been revealed")
    return envelope(_public_result(found))


def _public_result(result: dict) -> dict:
    """Integrity notes are moderator-only and are stripped here (section 4)."""
    return {key: value for key, value in result.items() if key != "integrity_notes"}


@api.get("/integrity/{pulse_id}", tags=["round"])
def integrity(pulse_id: str):
    found = STORE.results.get(pulse_id)
    if not found:
        raise HTTPException(404, f"pulse {pulse_id} has not been revealed")
    return envelope({
        "pulse_id": pulse_id,
        "integrity_notes": found.get("integrity_notes", []),
        "moderator_only": True,
        "note": "Descriptions, not diagnoses. Nothing here penalises an expert automatically.",
    })


# -- draft and decision --------------------------------------------------------
@api.post("/pulses/{pulse_id}/draft", tags=["draft"])
def make_draft(pulse_id: str):
    pulse = STORE.pulses.get(pulse_id)
    found = STORE.results.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    if not found:
        raise HTTPException(409, "reveal the round before drafting from it")
    risk = data.get_risk(pulse["risk_id"]) or {}
    built = draft_builder.build(risk, pulse, found)
    STORE.drafts[built["id"]] = built
    return envelope(built)


@api.post("/drafts/{draft_id}/decision", tags=["draft"])
async def decide(draft_id: str, body: dict = Body(default_factory=dict)):
    found = STORE.drafts.get(draft_id)
    if not found:
        raise HTTPException(404, f"no draft {draft_id}")
    action = body.get("action")
    if action not in ("accept", "edit", "reject"):
        raise HTTPException(422, "action must be accept, edit or reject")
    if action == "reject" and not body.get("note"):
        raise HTTPException(422, "rejecting the panel's view requires a rationale; it goes on the public ledger")

    # The UI sends these nested under decision_use; earlier callers send them flat. Accept both.
    use = {**(body.get("decision_use") or {})}
    for field in ("what_decision", "for_whom", "by_when"):
        use.setdefault(field, body.get(field))
    for field in ("what_decision", "for_whom", "by_when"):
        if action in ("accept", "edit") and not use.get(field):
            raise HTTPException(422, f"an accepted update needs {field}: what decision, for whom, by when")
    body = {**body, **use}

    found["status"] = {"accept": "accepted", "edit": "edited", "reject": "rejected"}[action]
    found["decided_by"] = body.get("decided_by") or "analyst"
    found["decided_at"] = now()
    found["note"] = body.get("note")
    if action == "edit" and body.get("edited_probability"):
        found["proposed_probability"] = body["edited_probability"]

    result = STORE.results[found["pulse_id"]]
    answers = STORE.answers.get(found["pulse_id"], [])
    entry = {
        "risk_id": found["risk_id"],
        "pulse_id": found["pulse_id"],
        "sealed_at": min((a.committed_at for a in answers), default=now()),
        "group_probability": result["mean"],
        "acaps_probability": found.get("acaps_probability"),
        "acaps_level": found.get("acaps_level"),
        "proposed_probability": found["proposed_probability"],
        "decision": found["status"],
        "outcome": None,
        "resolved_at": None,
        "verify_hash": round_verify_hash([a.commitment for a in answers]),
        "honesty": draft_builder.honesty_box(result, found, {**body, "action": action}),
    }
    STORE.ledger = [e for e in STORE.ledger if e["pulse_id"] != entry["pulse_id"]] + [entry]
    await publish("draft_decided", {"draft_id": draft_id, "action": action})
    logging_conf.log(log, "info", "draft decided", draft_id=draft_id, action=action)
    return envelope({**found, "ledger_entry": entry})


# -- ledger --------------------------------------------------------------------
@api.get("/ledger", tags=["ledger"])
def ledger():
    return envelope({"entries": list(reversed(STORE.ledger)), "k_min": STORE.k_min,
                     "note": "Group views only. No names, and nothing about any individual."})


@api.get("/ledger/{risk_id}", tags=["ledger"])
def ledger_for(risk_id: str):
    entries = [e for e in STORE.ledger if e["risk_id"].lower() == risk_id.lower()]
    if not entries:
        raise HTTPException(404, f"nothing sealed for {risk_id} yet")
    return envelope({"entries": entries, "k_min": STORE.k_min})


@api.post("/ledger/verify", tags=["ledger"])
def verify(body: dict = Body(default_factory=dict)):
    wanted = (body.get("verify_hash") or "").strip().lower()
    for entry in STORE.ledger:
        if entry["verify_hash"].lower() == wanted:
            answers = STORE.answers.get(entry["pulse_id"], [])
            recomputed = round_verify_hash([a.commitment for a in answers])
            return envelope({
                "valid": recomputed == entry["verify_hash"],
                "sealed_at": entry["sealed_at"],
                "anchor": None,
                "checked": "sha256 of this round's sorted answer commitments, recomputed now",
                "n_commitments": len(answers),
                "note": "This proves the sealed set has not changed since it was published. "
                        "It is not an external timestamp: no public chain is anchored in this build.",
            })
    raise HTTPException(404, "no ledger entry carries that hash")


# -- outcome, scoring, calibration ---------------------------------------------
@api.post("/risks/{risk_id}/resolve", tags=["outcome"])
async def resolve(risk_id: str, body: dict = Body(default_factory=dict)):
    outcome = body.get("outcome")
    if outcome not in ("materialised", "not_materialised"):
        raise HTTPException(422, "outcome must be materialised or not_materialised")
    if risk_id not in STORE.contracts:
        raise HTTPException(409, "freeze the question contract before resolving; otherwise the score "
                                 "is settled against a question nobody agreed to")
    entries = [e for e in STORE.ledger if e["risk_id"].lower() == risk_id.lower()]
    if not entries:
        raise HTTPException(404, f"nothing sealed for {risk_id} yet")
    resolved_at = body.get("resolved_at") or now()
    truth = 1.0 if outcome == "materialised" else 0.0
    written = 0
    for entry in entries:
        entry["outcome"] = outcome
        entry["resolved_at"] = resolved_at
        group = entry.get("group_probability")
        if group is not None:
            entry["honesty"]["panel_hit_rate"] = 1.0 if round(group) == truth else 0.0
            entry["honesty"]["misses"] = 0 if round(group) == truth else 1
        for answer in STORE.answers.get(entry["pulse_id"], []):
            if answer.probability is None:
                continue
            brier = round((answer.probability - truth) ** 2, 4)
            STORE.scores.append({
                "expert_internal_id": answer.expert_id or "anonymous",
                "risk_id": risk_id, "brier": brier, "resolved_at": resolved_at,
            })
            expert = STORE.experts.get(answer.expert_id)
            if expert:
                # Weights move slowly and stay capped; one round never makes a super-estimator.
                expert.weight = max(0.5, min(2.0, expert.weight + (0.25 - brier)))
                written += 1
    await publish("risk_resolved", {"risk_id": risk_id, "outcome": outcome})
    return envelope({"scores_written": written, "weights_updated": written,
                     "outcome": outcome, "resolved_at": resolved_at,
                     "scored_against": "the export's Probability band, never Risk Level"})


@api.get("/pulses/{pulse_id}/outcome-report", tags=["outcome"])
def outcome_report(pulse_id: str):
    found = STORE.results.get(pulse_id)
    if not found:
        raise HTTPException(404, f"pulse {pulse_id} has not been revealed")
    entry = next((e for e in STORE.ledger if e["pulse_id"] == pulse_id), None)
    decided = next((d for d in STORE.drafts.values() if d["pulse_id"] == pulse_id), {})
    return envelope({
        "pulse_id": pulse_id,
        "group_mean": found["mean"],
        "outcome": (entry or {}).get("outcome"),
        "analyst_decision_summary": (
            f"{decided.get('status', 'no decision yet')}"
            + (f": {decided.get('note')}" if decided.get("note") else "")
        ),
        "note": "Sent to everyone who answered, whatever mask they chose.",
    })


@api.get("/me/{token}/calibration", tags=["outcome"])
def calibration(token: str):
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid")
    _, expert_id = resolved
    mine = [s for s in STORE.scores if s["expert_internal_id"] == expert_id]
    if len(mine) < 5:
        raise HTTPException(404, f"a calibration report opens after 5 resolved risks; you have {len(mine)}")
    briers = [s["brier"] for s in mine]
    expert = STORE.experts.get(expert_id)
    return envelope({
        "pseudonym": pseudonym_for(expert_id, SETTINGS.pseudonym_key),
        "n_resolved": len(mine),
        "mean_brier": round(sum(briers) / len(briers), 4),
        "reliability_weight": round(expert.weight, 4) if expert else 1.0,
        "note": "Private and opt-in. Nobody else sees this.",
    })


@api.get("/analyst/board", tags=["desk"])
def board():
    by_expert: dict[str, list[float]] = {}
    for score in STORE.scores:
        by_expert.setdefault(score["expert_internal_id"], []).append(score["brier"])
    supers = []
    for expert_id, briers in by_expert.items():
        if len(briers) < 5:
            continue   # no track record, no board entry
        expert = STORE.experts.get(expert_id)
        supers.append({
            "pseudonym": pseudonym_for(expert_id, SETTINGS.pseudonym_key),
            "n": len(briers),
            "mean_brier": round(sum(briers) / len(briers), 4),
            "weight": round(expert.weight, 4) if expert else 1.0,
        })
    supers.sort(key=lambda row: row["mean_brier"])
    divergence = []
    for entry in STORE.ledger:
        acaps = data.band_to_number(entry.get("acaps_probability"))
        if entry.get("group_probability") is not None and acaps is not None:
            divergence.append({"risk_id": entry["risk_id"], "panel": entry["group_probability"],
                               "acaps": acaps})
    return envelope({"super_estimators": supers, "divergence": divergence,
                     "note": "A board entry needs 5 resolved risks. Empty is the honest state early on."})


@api.get("/sim/proof", tags=["desk"])
def proof():
    path = ROOT / "reports" / "proof.json"
    if not path.exists():
        raise HTTPException(404, "run `make demo` to write reports/proof.json first")
    return envelope(json.loads(path.read_text(encoding="utf-8")))


# -- events --------------------------------------------------------------------
@api.get("/events", tags=["desk"])
async def events(request: Request):
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    _subscribers.add(queue)

    async def stream():
        try:
            yield "event: hello\ndata: {}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event, payload = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield f"event: {event}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
        finally:
            _subscribers.discard(queue)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# -- demo helpers --------------------------------------------------------------
@api.get("/demo/links", tags=["desk"])
def demo_links():
    """The magic links for the seeded synthetic panel, so the desk can open a card on stage."""
    rows = []
    for token, (pulse_id, expert_id) in STORE.tokens.items():
        expert = STORE.experts.get(expert_id)
        rows.append({"token": token, "pulse_id": pulse_id,
                     "pseudonym": pseudonym_for(expert_id, SETTINGS.pseudonym_key),
                     "region": expert.region if expert else "",
                     "answered": STORE.answered(pulse_id, expert_id),
                     "card_url": f"/e/{token}"})
    return envelope({"links": rows, "synthetic": True,
                     "note": "Synthetic experts. Real panels get these by email magic link."})


# -- the built UI --------------------------------------------------------------
app.include_router(api, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    if not UI_DIST.exists():
        return RedirectResponse("/docs")
    return FileResponse(UI_DIST / "index.html")


if UI_DIST.exists():
    class SinglePageApp(StaticFiles):
        """Serve index.html for any path the build has no file for, so /app/desk and /app/e/<token>
        survive a reload or a shared link. StaticFiles(html=True) alone does not do this: it falls
        back to 404.html, and serves index.html only for a directory path."""

        async def get_response(self, path: str, scope):  # type: ignore[override]
            try:
                return await super().get_response(path, scope)
            except StarletteHTTPException as exc:
                if exc.status_code == 404:
                    return await super().get_response("index.html", scope)
                raise

    app.mount("/", SinglePageApp(directory=str(UI_DIST), html=True), name="ui")
