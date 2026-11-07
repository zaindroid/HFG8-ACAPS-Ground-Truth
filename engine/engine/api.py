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

from . import (acaps, alerts as alert_engine, data, draft as draft_builder, logging_conf,
               probes as probe_lib, settings as settings_mod)
from . import inbound as inbound_lib
from . import reach as reach_mod
from .reach import cadence as cadence_lib, channels as channel_lib, \
    contacts as contact_lib, messages as message_lib
from . import hardening as hardening_mod
from .hardening import (anchors as anchor_lib, calibration as calibration_lib,
                        flags as ff, patterns as pattern_lib)
from . import store
from .store import Expert, Store, TooFew, now, pseudonym_for, round_verify_hash

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures"
UI_DIST = ROOT / "ui" / "dist"

log = logging.getLogger("sealed_signals")
SETTINGS = settings_mod.load()
STORE = Store(k_min=SETTINGS.k_min)
ALERTS = alert_engine.new_store()
HARD = hardening_mod.new()
# Section 6e. The analyst's address book, the outbox and the cadence rules. Separate from STORE
# because a contact outlives any one pulse, and separate from HARD because reaching somebody is
# not a cryptographic guarantee -- it is a promise about how often we will bother them.
REACH = reach_mod.new()
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


async def deadline_watch(tick: float = 15.0) -> None:
    """The scheduler that makes "reveal at the deadline" a mechanism rather than a button label.

    Every tick, any open round whose `expires_at` has passed is revealed, exactly as if the
    analyst had pressed the button at that moment -- including the insufficient-panel path, which
    is what happens to a round the deadline closed with four answers in it. Nothing here can
    reveal a round early: it calls the same `Store.reveal`, which refuses."""
    while True:
        try:
            await asyncio.sleep(tick)
            for pulse in list(STORE.pulses.values()):
                if pulse.get("reveal_status") not in (None, "open"):
                    continue
                if not store.past(pulse.get("expires_at") or ""):
                    continue
                risk = data.get_risk(pulse["risk_id"]) or {}
                try:
                    result = STORE.reveal(pulse["id"], risk, "deadline")
                except store.TooEarly:
                    continue
                if result.get("reveal_status") == "insufficient_panel":
                    await publish("round_insufficient",
                                  {"pulse_id": pulse["id"], "n": result["n"]})
                    logging_conf.log(log, "info", "deadline closed an insufficient round",
                                     pulse_id=pulse["id"], n=result["n"])
                else:
                    await publish("round_revealed", {"pulse_id": pulse["id"]})
                    logging_conf.log(log, "info", "deadline revealed a round",
                                     pulse_id=pulse["id"], n=result["n"])
        except asyncio.CancelledError:
            raise
        except Exception as exc:                                  # noqa: BLE001
            # A scheduler that dies on one bad pulse stops revealing every other round, which is
            # a worse failure than the one it just hit.
            logging_conf.log(log, "error", "deadline watch error", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging_conf.configure(SETTINGS.log_level)
    logging_conf.log(log, "info", "starting", app_env=SETTINGS.app_env, sha=SETTINGS.git_sha,
                     k_min=SETTINGS.k_min, ui_built=UI_DIST.exists())
    if os.environ.get("SEED_ON_START", "true").lower() == "true":
        from .seeding import seed_alerts, seed_contacts, seed_demo
        pulse_id = seed_demo(STORE, SETTINGS)
        book = seed_contacts(REACH, STORE)
        replay = seed_alerts(ALERTS)
        logging_conf.log(log, "info", "seeded synthetic panel", pulse_id=pulse_id,
                         n_experts=len(STORE.experts), n_answers=STORE.n_answers(pulse_id),
                         n_alerts=len(replay["events"]), contacts=book["n_contacts"],
                         reachable=book["reachable"],
                         replay=f"{replay['month_from']}->{replay['month_to']}")
        # Sections 6c and 6d: identities in the encrypted registry, one membership group, and five
        # resolved pulses of history so the pattern reports describe something real. Deliberately
        # separate from seed_demo, so the core loop and its tests never depend on it.
        if os.environ.get("SEED_HARDENING", "true").lower() == "true":
            from .seeding_hardening import seed_all
            hardening_seed = seed_all(HARD, STORE, SETTINGS)
            logging_conf.log(log, "info", "seeded hardening stack",
                             identities=hardening_seed["identities"],
                             history_pulses=len(hardening_seed["pulses"]),
                             scores=hardening_seed["scores_written"],
                             group_root=hardening_seed["group"]["root"][:12],
                             flags=ff.flags())
    watcher = None
    if os.environ.get("DEADLINE_WATCH", "true").lower() == "true":
        watcher = asyncio.create_task(deadline_watch())
    yield
    if watcher:
        watcher.cancel()
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
    return {"sha": SETTINGS.git_sha, "branch": SETTINGS.branch, "built": SETTINGS.built_at,
            "started_at": SETTINGS.started_at, "app": "sealed-signals",
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
            f"{event['month_to']} ({event['rule_hit']}; rank {event['rank_this_month']} by "
            f"{event['direction']} among {event['n_crises_this_month']} crises compared this "
            f"month; reliability {event['reliability']})"
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
    # Optional, and both only ever copied, never composed from the risk: the threshold is the line
    # the adjudication rule will be read against, and the text is the sentence the card prints.
    # If the analyst wrote them here they are frozen with the rest; if not, the card falls back to
    # a sentence built from the event, which is clumsier but cannot drift from the contract.
    for extra in ("threshold", "text"):
        if body.get(extra):
            contract[extra] = body[extra]
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
    # Identity details never sit in the expert record. They go into the encrypted registry, and
    # the only way back out is POST /committee/registry/read, which logs the read.
    identity = body.get("identity") or {}
    if identity:
        HARD.registry.put(expert.id, {
            key: str(value)[:200] for key, value in identity.items()
            if key in ("name", "email", "phone", "organisation", "country")
        })
    return envelope({"expert_id": expert.id, "status": expert.status,
                     "approvals_required": 2,
                     "identity_stored": bool(identity),
                     "identity_note": HARD.registry.status()["lock_line"] if identity else
                     "No identity details were sent, so none are held.",
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

    credential_batch = None
    if len(approvals) >= 2 and expert.status != "approved":
        expert.status = "approved"
        # Section 6c item 3: the credential batch is minted on approval, not on answering, so the
        # committee never sees issuance and spending in the same moment.
        batch = HARD.credentials.issue(expert_id, body.get("panel_id") or "", None,
                                       int(body.get("allowance") or 3))
        credential_batch = {key: batch[key] for key in
                            ("batch_id", "n_issued", "scheme", "unlinkable", "note")}
    return envelope({
        "expert_id": expert_id,
        "status": expert.status,
        "approvals": approvals,
        "approvals_required": 2,
        "credential_issued": expert.status == "approved",
        "credential_batch": credential_batch,
        "note": "Approved experts can be matched to a panel."
        if expert.status == "approved"
        else f"{2 - len(approvals)} more approval(s) needed, from a different admin.",
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
    approved = [e for e in STORE.experts.values() if e.status == "approved"]

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
def _human_date(iso: str | None) -> str:
    if not iso:
        return "the end of the horizon"
    try:
        return datetime.fromisoformat(str(iso)[:10]).strftime("%-d %B %Y")
    except ValueError:
        try:
            parsed = datetime.fromisoformat(str(iso)[:10])
        except ValueError:
            return str(iso)
        return f"{parsed.day} {parsed.strftime('%B %Y')}"


def _question_object(risk: dict, override: str | dict | None) -> dict:
    """The question{} object the card shows first (section 4, v3.4).

    It comes from the frozen QuestionContract when one exists, because that is the text the answer
    will be adjudicated against; a card that asks something looser than the contract collects
    answers to a question nobody scored. With no contract the pulse falls back to an open question
    and says so, and the deadline is the risk's own horizon.

    The fallback never names the ACAPS band: the card promises the rating is hidden until after
    submission, and a question that quotes it would anchor the answer it exists to collect."""
    if isinstance(override, dict):
        return {**override, "source": override.get("source", "analyst")}
    contract = STORE.contracts.get(risk["risk_id"])
    if contract:
        deadline = str(contract["horizon_deadline"])[:10]
        text = contract.get("text") or (
            f"Will {contract['event'][0].lower()}{contract['event'][1:]} "
            f"by {_human_date(deadline)}?")
        return {
            "event": contract["event"],
            "location": contract["location"],
            "threshold": contract.get("threshold") or contract["adjudication_rule"],
            "deadline": deadline,
            "text": text,
            "source": "question_contract",
            "frozen_at": contract["frozen_at"],
            "resolution_source": contract["resolution_source"],
        }
    deadline = (datetime.now(timezone.utc)
                + timedelta(days=30 * int(risk.get("horizon_months") or 6))).date().isoformat()
    event = override or "the level of concern on this risk changes"
    return {
        "event": event,
        "location": risk.get("country") or risk.get("country_iso") or "",
        "threshold": None,
        "deadline": deadline,
        "text": (f"Is the level of concern on this risk still right by {_human_date(deadline)}, "
                 "and what are we missing?"),
        "source": "open_question",
        "note": ("No question contract is frozen for this risk, so this round cannot be scored "
                 "against an outcome. Freeze one with POST /api/risks/{risk_id}/contract."),
    }


def _build_pulse(risk: dict, reason: str, question: str | dict | None, evidence: list[dict],
                 expires_at: str | None = None, asked_by: str | None = None) -> dict:
    pulse_id = f"P-{len(STORE.pulses) + 1:04d}"
    pulse = {
        "id": pulse_id,
        "risk_id": risk["risk_id"],
        "panel_id": f"PAN-{risk['country_iso'].split(',')[0].strip()}",
        "fired_at": now(),
        "reason": reason,
        "round": 1,
        "evidence": evidence,
        "question": _question_object(risk, question),
        "asked_by": asked_by or SETTINGS.asked_by,
        # Fixed at send, printed on the card, and the only thing that decides when the round
        # opens (section 6a as revised in v3.4).
        "expires_at": expires_at or (datetime.now(timezone.utc)
                                     + timedelta(hours=24)).isoformat(timespec="seconds"),
        "reveal_status": "open",
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
    expires_at = body.get("expires_at")
    if not expires_at and body.get("expires_in_minutes") is not None:
        expires_at = (datetime.now(timezone.utc)
                      + timedelta(minutes=int(body["expires_in_minutes"]))).isoformat(
                          timespec="seconds")
    pulse = _build_pulse(found, body.get("reason") or "analyst", body.get("question"),
                         body.get("evidence") or _trigger_evidence(found),
                         expires_at, body.get("asked_by"))
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
def _panel_size(pulse_id: str) -> int:
    return sum(1 for pid, _ in STORE.tokens.values() if pid == pulse_id)


def _expert_profile(expert_id: str) -> dict:
    """What the probe bank is allowed to read about an expert: their tags and their region, and
    nothing another expert set. The card is fully determined once the link is issued."""
    expert = STORE.experts.get(expert_id)
    if not expert:
        return {"id": expert_id, "theme_tags": [], "geo_tags": [], "region": ""}
    return {"id": expert.id, "theme_tags": expert.theme_tags,
            "geo_tags": expert.geo_tags, "region": expert.region}


def _mask_options() -> list[dict]:
    return [
        {"id": "known", "label": "named to ACAPS"},
        {"id": "pseudonym", "label": "nickname to peers"},
        {"id": "anonymous", "label": "no identity kept",
         "note": "you will not receive personal feedback on this answer"},
    ]


def _group_view(pulse_id: str) -> dict | None:
    """What round 2 shows: the anonymised spread and the unattributed disagreement summary.
    ACAPS's band is not here. The expert sees the band for the first time in the feedback message
    after the reveal (section 8, v3.4) -- showing it in round 2 would anchor the revision the
    round exists to collect."""
    result = STORE.results.get(pulse_id)
    if not result:
        return None
    return {
        "n": result["n"],
        "mean": result["mean"],
        "spread": result["spread"],
        "distribution": result["distribution"],
        "disagreement": result.get("disagreement") or [],
        "acaps_band_shown": False,
    }


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
    answered = STORE.answered(pulse_id, expert_id)
    # Nothing on this card carries ACAPS's rating, in either round. The severity-change line and
    # the alert evidence are withheld until the expert has submitted, for the same reason: ACAPS's
    # own brief calls it the anchoring effect, and the blind round exists to avoid displaying the
    # anchor. The band appears once, in the feedback message after the reveal.
    show_evidence = answered or rnd == 2
    public_risk = {key: value for key, value in risk.items()
                   if key not in ("probability_acaps", "level", "probability_assumed_number")}
    public_pulse = {key: value for key, value in pulse.items() if key != "evidence"}
    if show_evidence:
        public_pulse["evidence"] = pulse.get("evidence") or []
    triggers = [{"id": t["id"], "title": t["title"]} for t in (risk.get("triggers") or [])[:3]]
    return envelope({
        "pulse": {**public_pulse, "n_answers": STORE.n_answers(pulse_id)},
        "risk": public_risk,
        # The first line of the card, exactly as frozen in the question contract.
        "question": pulse["question"],
        "asked_by": pulse.get("asked_by"),
        "round": rnd,
        "group_view_if_round2": _group_view(pulse_id) if rnd == 2 else None,
        "already_answered": answered,
        "likelihood_words": [dict(word) for word in store.LIKELIHOOD_WORDS],
        "stances": list(store.STANCES),
        "mask_options": _mask_options(),
        "mask_default": None,
        "mask_note": store.REIDENTIFICATION_NOTE,
        "optional": {
            "confidence": list(store.CONFIDENCE_WORDS),
            "confidence_note": store.CONFIDENCE_SCALE_NOTE,
            "note_prompt": "What are we missing?",
            "note_prompt_alternate": "What is the strongest reason this would NOT happen?",
            "accuracy_prompt": "Is this something you saw, read, or heard?",
            "source_tags": list(store.SOURCE_TAGS),
            "trigger_pick_prompt": "Which trigger would move your view most?",
            "triggers": triggers,
            "panel_share_prompt": ("What share of this panel will say likely or very likely?"),
        },
        "expires_at": pulse.get("expires_at"),
        "correction_allowed_until": pulse.get("expires_at"),
        # The three-step card's follow-up questions, chosen on the device from the expert's own
        # step-1 answers. They travel with the card so no partial answer leaves the phone before
        # the confirmation, and the conditions only ever read the four numbers this expert just
        # entered -- nothing a peer set is readable here, so the card cannot herd.
        "probe_flow": probe_lib.card_flow(risk, _expert_profile(expert_id)),
        "probe_note": "These follow the scored question and are never aggregated into it.",
        "evidence_shown": show_evidence,
        "acaps_band_shown": False,
        "commit_note": ("Submitting opens a confirmation screen. Nothing is recorded until you "
                        "confirm, so a link click or a mail scanner cannot answer for you."),
        "after_confirm_line": ("Thanks. You'll hear how the panel saw it after the deadline."),
    })


def _spend_credential(body: dict, pulse_id: str, expert_id: str, mask: str) -> dict:
    """Section 6c item 3 on the answering side, at the moment of confirmation.

    The credential is spent by the confirmation, never by the draft: a token burned on an answer
    nobody confirmed would be a vetted member's one chance at this pulse, spent by a link preview.

    A card that presents a credential spends it, and a second spend of the same token is refused.
    A card that presents none still answers -- the magic link already gates this round -- and when
    the mask is 'no identity kept' the server mints and spends one itself so the flow is complete
    on stage. That fallback is linkable by construction, and the response says so rather than
    borrowing the unlinkability claim it has not earned."""
    presented = body.get("credential") or {}
    if not ff.enabled("FF_BLIND"):
        return {"spent": False, "scheme": "hmac",
                "line": "FF_BLIND is off: no credential was involved in this answer."}
    if presented:
        try:
            record = HARD.credentials.spend(presented.get("token_id") or "",
                                            presented.get("signature") or "", pulse_id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"spent": True, "unlinkable": True, "scheme": record["scheme"],
                "line": "Answered with a one-time vetted credential. The committee can check it "
                        "was issued to an approved expert and cannot tell which one."}
    if mask != "anonymous":
        return {"spent": False,
                "line": "No credential on this answer: the magic link identified the round, and "
                        "this mask does not ask for unlinkability."}
    batch = HARD.credentials.issue(expert_id, "", None, 1)
    token = batch["credentials"][0]
    HARD.credentials.spend(token["token_id"], token["signature"], pulse_id)
    return {"spent": True, "unlinkable": False, "scheme": batch["scheme"],
            "line": "Answered with a one-time vetted credential, minted here because the card did "
                    "not bring its own. Single-use holds; unlinkability does not on this path."}


def _check_zk(body: dict, pulse_id: str) -> dict | None:
    """Section 6c item 4. Off by default, and when it is on the verdict says what went unchecked."""
    proof = body.get("zk_proof")
    if not proof:
        return None
    if not ff.enabled("FF_ZK"):
        raise HTTPException(409, "FF_ZK is off on this build, so no membership proof is accepted. "
                                 "The reason is in GET /api/zk/status: the Groth16 verifier is not "
                                 "implemented here.")
    verdict = HARD.membership.verify(proof, pulse_id)
    if not verdict["accepted"]:
        raise HTTPException(409, {"message": "this membership proof was not accepted", **verdict})
    return verdict


def _open_round(token: str, round_wanted: int = 1) -> tuple[str, str, dict]:
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid; ask the analyst for a new one")
    pulse_id, expert_id = resolved
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    if pulse_id in STORE.results and round_wanted == 1:
        raise HTTPException(409, "round 1 is closed on this pulse; this link now opens round 2")
    return pulse_id, expert_id, pulse


@api.post("/e/{token}/answer", status_code=200, tags=["expert"])
def answer(token: str, body: dict = Body(default_factory=dict)):
    """A draft, and only a draft (section 5, v3.4).

    This is the route a link click, a mail scanner or a link preview can reach, so it commits
    nothing: it validates the answer, prices a word into the band midpoint, and returns the one
    line the confirmation screen repeats back with a token to confirm it."""
    pulse_id, expert_id, pulse = _open_round(token, int(body.get("round", 1)))
    risk = data.get_risk(pulse["risk_id"]) or {}
    if STORE.answered(pulse_id, expert_id):
        raise HTTPException(409, "an answer from this link is already committed; use "
                                 "PUT /api/e/{token}/answer to change it before the deadline")
    if store.past(pulse.get("expires_at") or ""):
        raise HTTPException(409, f"this round closed at {pulse.get('expires_at')}")
    submitted = body.get("probe_answers") or {}
    if not isinstance(submitted, dict):
        raise HTTPException(422, "probe_answers must be an object keyed by probe id")
    if submitted:
        # Only answers to probes this card actually asked are kept, so a crafted request cannot
        # write arbitrary keys into an Answer and out through the themes.
        allowed = probe_lib.accepted_ids(risk, _expert_profile(expert_id))
        body = {**body, "probe_answers": {key: value for key, value in submitted.items()
                                          if key in allowed}}
    try:
        drafted = STORE.draft(pulse_id, expert_id, body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    answer_view = drafted.pop("answer")
    return envelope({
        **drafted,
        "probability_used": answer_view["probability"],
        "probability_source": answer_view["probability_source"],
        "number_note": ("You chose a word. If you confirm, the panel mean will use that band's "
                        "midpoint; add an exact percentage if that is not what you meant."
                        if answer_view["probability_source"] == "band_midpoint" else
                        "Your exact percentage is what the panel mean will use."
                        if answer_view["probability_source"] == "exact" else
                        "This answer carries no number and is never scored."),
        "confirm_at": f"/api/e/{token}/confirm",
        "expires_at": pulse.get("expires_at"),
    })


@api.post("/e/{token}/confirm", status_code=201, tags=["expert"])
async def confirm(token: str, body: dict = Body(default_factory=dict)):
    """The commit. The first valid confirmation per expert per pulse counts."""
    pulse_id, expert_id, pulse = _open_round(token)
    confirm_token = (body.get("confirm_token") or "").strip()
    pending = STORE.pending.get(confirm_token)
    if not pending:
        raise HTTPException(409, "this confirmation has expired or was already used; open your "
                                 "link again to answer")
    if STORE.answered(pulse_id, expert_id):
        raise HTTPException(409, "an answer from this link is already committed; use "
                                 "PUT /api/e/{token}/answer to change it before the deadline")
    mask = pending["answer"]["mask"]
    credential_result = _spend_credential(body, pulse_id, expert_id, mask)
    zk_result = _check_zk(body, pulse_id)
    try:
        sealed = STORE.confirm(confirm_token, pulse_id, expert_id,
                               SETTINGS.commitment_salt, SETTINGS.pseudonym_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    STORE.mark_used(token)
    _record_day_roots()
    await publish("answer_sealed", {"pulse_id": pulse_id, "n_answers": STORE.n_answers(pulse_id)})
    logging_conf.log(log, "info", "answer committed", pulse_id=pulse_id, mask=sealed.mask,
                     n_answers=STORE.n_answers(pulse_id))
    return envelope({
        "committed_at": sealed.committed_at,
        "commitment": sealed.commitment,
        "version": sealed.version,
        "mask": sealed.mask,
        "pseudonym": sealed.pseudonym,
        "correction_allowed_until": pulse.get("expires_at"),
        # Handed out exactly once, here. It is how an answer under the 'no identity kept' mask can
        # still be corrected: that answer stores no expert id, so without this key the only way to
        # find it again would be a token-to-answer map, which would undo the mask.
        "edit_key": STORE.take_edit_key(sealed),
        "edit_key_note": ("Keep this with your link if you may want to change your answer. It is "
                          "the only handle on an answer with no identity kept, and we store only "
                          "its hash."),
        "message": "Thanks. You'll hear how the panel saw it after the deadline.",
        "sealing_note": "The commitment proves when you answered and that you have not changed it. "
                        "It does not hide your answer from the operator of this service.",
        "acaps_band_shown": False,
        "band_note": "ACAPS's own rating is in the message you get after the deadline, not here.",
        "credential": credential_result,
        "zk": zk_result,
        "anchor": HARD.anchors.for_day(sealed.committed_at[:10]),
    })


@api.put("/e/{token}/answer", tags=["expert"])
def correct_answer(token: str, body: dict = Body(default_factory=dict)):
    """A correction, allowed until the deadline printed on the card. Every version is kept and
    the committee sees them, so a changed view is visible as a change rather than as the only
    answer that ever existed."""
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid; ask the analyst for a new one")
    pulse_id, expert_id = resolved
    pulse = STORE.pulses.get(pulse_id) or {}
    if store.past(pulse.get("expires_at") or ""):
        raise HTTPException(409, f"the deadline passed at {pulse.get('expires_at')}; this answer "
                                 "can no longer be changed")
    found = STORE.find_answer(pulse_id, expert_id, body.get("edit_key"))
    if not found:
        raise HTTPException(404, "no committed answer found for this link. An answer with no "
                                 "identity kept can only be corrected with the edit key from its "
                                 "confirmation.")
    try:
        updated = STORE.correct(found, body, SETTINGS.commitment_salt)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    _record_day_roots()
    logging_conf.log(log, "info", "answer corrected", pulse_id=pulse_id, version=updated.version)
    return envelope({
        "committed_at": updated.committed_at,
        "commitment": updated.commitment,
        "version": updated.version,
        "previous_versions_kept": len(updated.previous_versions),
        "correction_allowed_until": pulse.get("expires_at"),
        "message": "Changed. Your earlier answer is kept with its own timestamp.",
    })


@api.post("/e/{token}/relayed-confirm", tags=["expert"])
def relayed_confirm(token: str, body: dict = Body(default_factory=dict)):
    """An answer taken by phone, on paper or through a liaison is entered by the analyst and
    labelled relayed. It does not count until the expert confirms it here, through their own
    link: otherwise the panel could be filled in by the people who convene it."""
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid; ask the analyst for a new one")
    pulse_id, expert_id = resolved
    found = STORE.find_answer(pulse_id, expert_id, body.get("edit_key"))
    if not found:
        raise HTTPException(404, "no answer found for this link")
    try:
        STORE.confirm_relayed(found)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    logging_conf.log(log, "info", "relayed answer confirmed", pulse_id=pulse_id)
    return envelope({
        "confirmed_by_expert_at": found.confirmed_by_expert_at,
        "relayed_by": found.relayed_by,
        "counts": found.counts(),
        "message": "Confirmed. Your answer now counts in this round.",
    })


def _n_text(n: int, panel: int) -> str:
    """Qualitative on purpose. Before the deadline no message to an expert may carry a count --
    a count is the one piece of information that turns a reminder into a nudge toward the group.
    After the reveal the exact n is public on the ledger; this line is simply how a note to a
    colleague reads."""
    if not panel:
        return f"{n} answers came in"
    share = n / panel
    if share >= 0.9:
        return "everyone on the panel answered"
    if share >= 0.6:
        return "most of the panel answered"
    if share >= 0.4:
        return "about half the panel answered"
    return "a minority of the panel answered"


@api.get("/e/{token}/feedback", tags=["expert"])
def feedback(token: str):
    """The message after the reveal, and the only place an expert sees ACAPS's band (section 8)."""
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid; ask the analyst for a new one")
    pulse_id, expert_id = resolved
    pulse = STORE.pulses.get(pulse_id) or {}
    result = STORE.results.get(pulse_id)
    if not result:
        attempt = STORE.reveal_attempts.get(pulse_id)
        if attempt:
            return envelope({
                "pulse_id": pulse_id,
                "reveal_status": "insufficient_panel",
                "message": ("Too few of the panel answered, so nothing was opened -- not even to "
                            "the analyst. Your answer is kept and was not shown to anyone."),
                "acaps_band_shown": False,
            })
        raise HTTPException(404, f"this round has not opened yet; it opens at "
                                 f"{pulse.get('expires_at')}")
    risk = data.get_risk(pulse.get("risk_id") or "") or {}
    mine = STORE.find_answer(pulse_id, expert_id, None)
    entry = next((e for e in STORE.ledger if e["pulse_id"] == pulse_id), None)
    your_answer = None
    if mine:
        your_answer = {"likelihood_word": mine.likelihood_word, "probability": mine.probability,
                       "probability_source": mine.probability_source, "stance": mine.stance,
                       "version": mine.version}
    return envelope({
        "pulse_id": pulse_id,
        "reveal_status": "revealed",
        "revealed_at": result["revealed_at"],
        "n_text": _n_text(result["n"], _panel_size(pulse_id)),
        "n": result["n"],
        "group_mean": result["mean"],
        "spread": result["spread"],
        "disagreement": result.get("disagreement") or [],
        "number_note": result.get("number_note"),
        "your_answer": your_answer,
        "your_answer_note": (None if your_answer else
                             "You answered with no identity kept, so this service cannot tell "
                             "which answer was yours and shows you the group view only."),
        "acaps_band": risk.get("probability_acaps"),
        "acaps_level": risk.get("level"),
        "acaps_band_shown": True,
        "analyst_decision": (entry or {}).get("decision") or "not decided yet",
        "analyst_rationale": ((entry or {}).get("honesty") or {}).get("analyst_rationale"),
        "attribution": (mine.pseudonym if mine and mine.mask == "pseudonym" else
                        "named to ACAPS" if mine and mine.mask == "known" else None),
        "outcome_report_pending": (entry or {}).get("outcome") is None,
        "reidentification_note": store.REIDENTIFICATION_NOTE,
    })


# -- reveal and aggregate ------------------------------------------------------
@api.post("/pulses/{pulse_id}/reveal", tags=["round"])
async def reveal(pulse_id: str, body: dict = Body(default_factory=dict)):
    """Reveal at the deadline. Before it, only with `force`, and then the result says so."""
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    risk = data.get_risk(pulse["risk_id"]) or {}
    reason = "analyst_before_deadline" if body.get("force") else "deadline"
    try:
        result = STORE.reveal(pulse_id, risk, reason)
    except store.TooEarly as exc:
        raise HTTPException(409, {
            "message": str(exc),
            "expires_at": exc.expires_at,
            "why": "The reveal time is fixed when the pulse is sent, so no one can open a round "
                   "early because they like the answers that arrived first.",
        }) from exc
    if result.get("reveal_status") == "insufficient_panel":
        await publish("round_insufficient", {"pulse_id": pulse_id, "n": result["n"]})
        logging_conf.log(log, "info", "insufficient panel", pulse_id=pulse_id, n=result["n"])
        return envelope(result)
    await publish("round_revealed", {"pulse_id": pulse_id})
    logging_conf.log(log, "info", "round revealed", pulse_id=pulse_id, n=result["n"],
                     reason=reason)
    return envelope(_public_result(result))


@api.get("/pulses/{pulse_id}/result", tags=["round"])
def result(pulse_id: str):
    found = STORE.results.get(pulse_id)
    if found:
        return envelope(_public_result(found))
    attempt = STORE.reveal_attempts.get(pulse_id)
    if attempt:
        return envelope(attempt)
    raise HTTPException(404, f"pulse {pulse_id} has not been revealed")


MODERATOR_ONLY = ("integrity_notes", "probe_summary")


def _public_result(result: dict) -> dict:
    """Moderator-only keys are stripped here (section 4): the integrity notes, and the counts of
    the card's closed follow-ups, which are small enough on a panel of eight to point at a
    person when read beside the rest of the page."""
    return {key: value for key, value in result.items() if key not in MODERATOR_ONLY}


# -- the verification queue ----------------------------------------------------
@api.get("/verification-queue/{pulse_id}", tags=["round"])
def verification_queue(pulse_id: str, who: str = "", why: str = ""):
    """The distinctive free text, which is deliberately not in the round result. Reading it is an
    attributed act: who and why, logged beside the entries."""
    if pulse_id not in STORE.verification_queue:
        raise HTTPException(404, f"no verification queue for {pulse_id}; reveal the round first")
    try:
        entries = STORE.read_verification_queue(pulse_id, who, why)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return envelope({
        "pulse_id": pulse_id,
        "entries": entries,
        "n_entries": len(entries),
        "read_by": who,
        "why": why,
        "means": ("These lines were written by one person each. They are the most worth checking "
                  "and the most likely to identify their author in a panel of eight, which is why "
                  "they are here and not in the published result."),
        "corroboration_note": ("Absence from the checked databases is not evidence of falsity."),
    })


@api.get("/committee/verification-log", tags=["committee"])
def verification_log():
    log_entries = STORE.queue_access_log
    return envelope({
        "reads": list(reversed(log_entries)),
        "n_reads": len(log_entries),
        "means": "Every read of a verification queue, with who asked and why.",
    })


@api.get("/integrity/{pulse_id}", tags=["round"])
def integrity(pulse_id: str):
    found = STORE.results.get(pulse_id)
    if not found:
        raise HTTPException(404, f"pulse {pulse_id} has not been revealed")
    return envelope({
        "pulse_id": pulse_id,
        "integrity_notes": found.get("integrity_notes", []),
        # Counts of the card's closed follow-ups. Moderator-only for the same reason as the
        # notes: a one-of-eight option count read beside a distinctive line names a person.
        "probe_summary": found.get("probe_summary", []),
        "missing_themes": found.get("missing_themes", []),
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
        "honesty": {
            **draft_builder.honesty_box(result, found, {**body, "action": action}),
            # Section 6e: the honesty box records the channel mix. A panel answered entirely by
            # phone through one analyst is a different object from one that answered on its own,
            # and the public record says which it was.
            "channel_mix": REACH.channel_mix(found["pulse_id"]),
        },
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
            _record_day_roots()
            attestation = HARD.attestations.latest(entry["risk_id"])
            day = answers[0].committed_at[:10] if answers else None
            anchor = HARD.anchors.for_day(day) if day else None
            return envelope({
                "valid": recomputed == entry["verify_hash"],
                "sealed_at": entry["sealed_at"],
                "checked": "sha256 of this round's sorted answer commitments, recomputed now",
                "checked_means": "The sealed set has not changed since it was published.",
                "n_commitments": len(answers),
                "attestation": attestation,
                "attestation_verification": (
                    HARD.attestations.verify(attestation) if attestation else None
                ),
                "attestation_means": (
                    "The outcome record was issued by the committee key and has not been altered."
                    if attestation else
                    "No attestation yet: this risk is not resolved, so there is no outcome to sign."
                ),
                # `anchor` stays what the UI contract says it is: a link to a supplied proof, or
                # null. It is null until a root is genuinely anchored, which is the honest state
                # for every round in this build. The root itself goes under its own key.
                "anchor": _anchor_url(anchor),
                "anchor_root": anchor,
                "anchor_means": (
                    (anchor or {}).get("means")
                    if anchor else "No daily root recorded for this round."
                ),
                "note": "Three separate checks, three separate meanings. The hash proves the set "
                        "is unchanged. The signature proves who issued the outcome record. The "
                        "anchor proves timing, and only once its status reads anchored.",
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
    # Section 6c item 2: sign the record, not the truth. The commitment root ties the signature to
    # the exact set of sealed answers this outcome settles.
    commitment_root = anchor_lib.merkle_root(
        [a.commitment for entry in entries for a in STORE.answers.get(entry["pulse_id"], [])]
    )
    attestation = HARD.attestations.attest(risk_id.upper(), outcome, resolved_at, commitment_root)
    for entry in entries:
        entry["attestation"] = {key: attestation[key] for key in
                                ("scheme", "key_id", "signature", "commitment_root")}
    await publish("risk_resolved", {"risk_id": risk_id, "outcome": outcome})
    return envelope({"scores_written": written, "weights_updated": written,
                     "outcome": outcome, "resolved_at": resolved_at,
                     "attestation": attestation,
                     "attestation_public_key": HARD.attestations.public_key(),
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


@api.get("/committee/scoring", tags=["committee"])
def committee_scoring():
    """Panel-level scoring, replacing the per-expert board of v3.3 and earlier (section 5, v3.4).

    The old board ranked pseudonyms by Brier score. Even without names and even committee-side,
    that is a leaderboard of people built from answers to questions that never said they were
    being scored against each other. What the committee gets now is how each *panel* did against
    the ACAPS band it was asked about, which is what tells them whether the loop is worth
    running. Per-expert numbers exist only inside the consent-gated calibration programme."""
    panels: dict[str, dict] = {}
    for pulse in STORE.pulses.values():
        panel_id = pulse.get("panel_id")
        if not panel_id:
            continue
        row = panels.setdefault(panel_id, {
            "panel_id": panel_id, "risk_ids": [], "n_pulses": 0, "n_answers": 0,
            "n_resolved": 0, "panel_brier": None, "acaps_band_brier": None, "status": "open",
        })
        row["n_pulses"] += 1
        row["n_answers"] += STORE.n_answers(pulse["id"])
        if pulse["risk_id"] not in row["risk_ids"]:
            row["risk_ids"].append(pulse["risk_id"])

    # Brier of the panel's own mean against the outcome, and of the ACAPS band mapped to a number
    # against the same outcome. The mapping is an assumption of this build and the payload says so.
    for entry in STORE.ledger:
        if entry.get("outcome") is None:
            continue
        pulse = STORE.pulses.get(entry["pulse_id"]) or {}
        row = panels.get(pulse.get("panel_id"))
        if not row:
            continue
        truth = 1.0 if entry["outcome"] == "materialised" else 0.0
        group = entry.get("group_probability")
        acaps = data.band_to_number(entry.get("acaps_probability"))
        row.setdefault("_panel", []).append((group - truth) ** 2 if group is not None else None)
        row.setdefault("_acaps", []).append((acaps - truth) ** 2 if acaps is not None else None)
        row["n_resolved"] += 1
        row["status"] = "resolved"

    rows = []
    for row in panels.values():
        for key, out in (("_panel", "panel_brier"), ("_acaps", "acaps_band_brier")):
            scores = [s for s in row.pop(key, []) if s is not None]
            row[out] = round(sum(scores) / len(scores), 4) if scores else None
        rows.append(row)
    rows.sort(key=lambda r: r["panel_id"])

    divergence = []
    for entry in STORE.ledger:
        acaps = data.band_to_number(entry.get("acaps_probability"))
        if entry.get("group_probability") is not None and acaps is not None:
            divergence.append({"risk_id": entry["risk_id"], "panel": entry["group_probability"],
                               "acaps": acaps})
    return envelope({
        "panels": rows,
        "divergence": divergence,
        "note": ("Panel-level only. No per-expert scores exist outside the consent-gated "
                 "calibration programme, and none of these numbers weights anybody's answer."),
        "band_assumption": (f"The ACAPS band is mapped to a number by this build, not by ACAPS: "
                            f"{data.PROBABILITY_BANDS}."),
        "empty_note": "A panel with no resolved risk has no Brier score. Empty is the honest "
                      "state early on.",
    })


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


# -- hardening stack: sections 6c and 6d ---------------------------------------
def _commitments_by_day() -> dict[str, list[str]]:
    days: dict[str, list[str]] = {}
    for answers in STORE.answers.values():
        for answer in answers:
            days.setdefault(answer.committed_at[:10], []).append(answer.commitment)
    return days


def _record_day_roots() -> None:
    """Keep the daily Merkle roots in step with the sealed commitments. Cheap, and it means the
    ledger can always show a root for the day a round was sealed, submitted or not."""
    for day, commitments in _commitments_by_day().items():
        HARD.anchors.record(day, commitments)


def _anchor_url(root: dict | None) -> str | None:
    """The link the ledger offers as a supplied proof. Only once the root is actually anchored:
    a pending submission has a receipt but nothing to show anyone, and a link beside the words
    "external anchor supplied" would be a claim the root has not earned."""
    if not root or root.get("status") != "anchored" or not root.get("calendar"):
        return None
    return f"{root['calendar']}/timestamp/{root['merkle_root']}"


def _expert_by_pseudonym(pseudonym: str) -> str | None:
    wanted = (pseudonym or "").strip().lower()
    for expert_id in STORE.experts:
        if pseudonym_for(expert_id, SETTINGS.pseudonym_key).lower() == wanted:
            return expert_id
    return None


def _acaps_probability(risk_id: str) -> float | None:
    risk = data.get_risk(risk_id) or {}
    return risk.get("probability_assumed_number")


@api.get("/trust/status", tags=["trust"])
def trust_status():
    """Everything the product needs to describe the hardening stack, including the exact
    guarantee / does-not wording. One source, so the UI and the slides cannot drift."""
    return envelope(HARD.status())


@api.get("/registry/status", tags=["trust"])
def registry_status():
    return envelope(HARD.registry.status())


@api.get("/committee/access-log", tags=["trust"])
def committee_access_log():
    """Mechanism 6. Reading an identity is allowed and logged; the log is the control."""
    return envelope({
        "entries": list(reversed(HARD.registry.log())),
        # Not `n`: that name means "answers in this round" everywhere else here, and the fixture
        # validator rightly refuses any fixture carrying n < 5.
        "n_reads": len(HARD.registry.access_log),
        "guarantees": (ff.mechanism("access_log") or {}).get("guarantees"),
        "does_not": (ff.mechanism("access_log") or {}).get("does_not"),
    })


@api.post("/committee/registry/read", tags=["trust"])
def committee_registry_read(body: dict = Body(default_factory=dict)):
    """The only way to open an identity. Refuses an unattributed read, and logs every one."""
    expert_id = (body.get("expert_id") or "").strip()
    if expert_id not in STORE.experts:
        raise HTTPException(404, f"no expert {expert_id}")
    try:
        identity = HARD.registry.read(expert_id, body.get("who") or "", body.get("why") or "")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if identity is None:
        raise HTTPException(404, f"no identity on file for {expert_id}")
    return envelope({"expert_id": expert_id, "identity": identity,
                     "logged": HARD.registry.log()[-1],
                     "note": "This read is now in the committee access log, permanently."})


@api.get("/credentials/issuer", tags=["trust"])
def credential_issuer():
    """The issuer public key, so a client can blind its own tokens and keep them unlinkable."""
    return envelope({
        **HARD.credentials.public_key(),
        "how": "Encode the message 'sealed-signals/credential/v1:<token_id>' with EMSA-PSS "
               "(SHA-384, zero salt), blind it with r^e mod n, send the hex to "
               "POST /api/credentials/issue as `blinded`, then unblind with r^-1.",
    })


@api.post("/credentials/issue", status_code=201, tags=["trust"])
def credentials_issue(body: dict = Body(default_factory=dict)):
    """Mechanism 3. Committee-side blind signing of a batch for an approved expert."""
    expert_id = (body.get("expert_id") or "").strip()
    expert = STORE.experts.get(expert_id)
    if not expert:
        raise HTTPException(404, f"no expert {expert_id}")
    if expert.status != "approved":
        raise HTTPException(409, "credentials are issued on approval; this expert is "
                                 f"{expert.status}")
    blinded = body.get("blinded") or None
    count = int(body.get("count") or 0)
    if not blinded and count <= 0:
        raise HTTPException(422, "send `blinded` (preferred: you keep the unlinkability) or "
                                 "`count` for the demo path")
    if count > 32:
        raise HTTPException(422, "32 tokens is the ceiling on one batch")
    issued = HARD.credentials.issue(expert_id, body.get("panel_id") or "", blinded, count)
    logging_conf.log(log, "info", "credentials issued", expert_id=expert_id,
                     n=issued["n_issued"], unlinkable=issued["unlinkable"])
    return envelope({**issued,
                     "guarantees": (ff.mechanism("blind_credentials") or {}).get("guarantees"),
                     "does_not": (ff.mechanism("blind_credentials") or {}).get("does_not")})


@api.get("/credentials/status", tags=["trust"])
def credentials_status():
    """Counts only: issued, spent, and the fact that nothing joins the two."""
    return envelope(HARD.credentials.summary())


@api.get("/ledger/{risk_id}/attestation", tags=["trust"])
def ledger_attestation(risk_id: str):
    """Mechanism 2. The signature over the resolved outcome record, and its verification."""
    record = HARD.attestations.latest(risk_id)
    if not record:
        raise HTTPException(404, f"{risk_id.upper()} has no attestation: it is not resolved yet")
    anchor = HARD.anchors.receipt_for_commitment(record.get("commitment_root") or "")
    return envelope({
        "attestation": record,
        "verification": HARD.attestations.verify(record),
        "public_key": HARD.attestations.public_key(),
        "anchor": _anchor_url(anchor),
        "anchor_root": anchor,
        "history": HARD.attestations.for_risk(risk_id),
    })


@api.get("/anchors", tags=["trust"])
def anchors_list():
    """Mechanism 5. Daily commitment roots, with status anchored or pending, and the receipt."""
    _record_day_roots()
    return envelope({
        "roots": HARD.anchors.all(),
        "calendars": list(anchor_lib.CALENDARS),
        "enabled": ff.enabled("FF_ANCHOR"),
        "guarantees": (ff.mechanism("anchoring") or {}).get("guarantees"),
        "does_not": (ff.mechanism("anchoring") or {}).get("does_not"),
    })


@api.post("/anchors/{day}/submit", tags=["trust"])
def anchor_submit(day: str):
    _record_day_roots()
    try:
        root = HARD.anchors.submit(day)
    except KeyError as exc:
        raise HTTPException(404, f"no commitments recorded on {day}") from exc
    logging_conf.log(log, "info", "anchor submitted", day=day, status=root.status)
    return envelope(root.as_dict())


@api.post("/anchors/{day}/upgrade", tags=["trust"])
def anchor_upgrade(day: str):
    """Ask the calendar whether the root has made it into a block yet. Usually: not yet."""
    try:
        root = HARD.anchors.upgrade(day)
    except KeyError as exc:
        raise HTTPException(404, f"no root recorded on {day}") from exc
    return envelope(root.as_dict())


@api.get("/zk/status", tags=["trust"])
def zk_status():
    """Mechanism 4, including the part this build does not do. Read `proof_verifier`."""
    return envelope(HARD.membership.status())


@api.get("/committee/patterns/{panel_id}", tags=["committee"])
def committee_patterns(panel_id: str):
    """Section 6d, committee side, panel-level only.

    v3.4 removed the per-expert report that used to live at this path under a pseudonym. The
    reason is in the section: nothing about a person is computed from a pulse, because the pulse
    never told them it was measuring them. What the committee reads is about the panel."""
    known = {pulse.get("panel_id") for pulse in STORE.pulses.values()}
    if panel_id not in known:
        raise HTTPException(404, f"no panel {panel_id} has been pulsed on this instance")
    return envelope(pattern_lib.report(STORE, panel_id))


@api.get("/committee/patterns", tags=["committee"])
def committee_patterns_all():
    """Every panel, with the ones below the floor shown as below the floor rather than omitted:
    the committee should see the floor working, not an empty page."""
    panels = sorted({pulse.get("panel_id") for pulse in STORE.pulses.values() if pulse.get("panel_id")})
    reports = [pattern_lib.report(STORE, panel_id) for panel_id in panels]
    return envelope({
        "panels": [r for r in reports if r["sentences"]],
        "not_yet": [{"panel_id": r["panel_id"], "n_pulses_revealed": r["n_pulses_revealed"]}
                    for r in reports if not r["sentences"]],
        "min_pulses": pattern_lib.MIN_PULSES,
        "min_per_affiliation": pattern_lib.MIN_PER_AFFILIATION,
        "never": pattern_lib.NEVER,
    })


# -- the consent-gated calibration programme (section 6d, FF_CALIBRATION) ------
def _calibration_guard() -> None:
    if not ff.enabled("FF_CALIBRATION"):
        raise HTTPException(409, {
            "message": "FF_CALIBRATION is off on this build, so nothing about any individual is "
                       "being measured.",
            "what_it_would_be": calibration_lib.DISCLOSURE,
            "why_off": "It is the only mechanism here that measures a person. It ships off so "
                       "that the default state of the system is one where nobody is measured.",
        })


def _enrolled_expert(token: str) -> str:
    resolved = STORE.resolve_token(token)
    if not resolved:
        raise HTTPException(404, "this link is not valid")
    return resolved[1]


@api.get("/calibration/disclosure", tags=["calibration"])
def calibration_disclosure():
    """The paragraph an expert reads before consenting. Readable with the flag off on purpose:
    what we would measure is not a secret, it is the thing consent is given against."""
    return envelope({
        "enabled": ff.enabled("FF_CALIBRATION"),
        "disclosure": calibration_lib.DISCLOSURE,
        "disclosure_version": calibration_lib.DISCLOSURE_VERSION,
        "min_items": calibration_lib.MIN_ITEMS,
        "confidence_prompt": calibration_lib.CONFIDENCE_PROMPT,
        "never": calibration_lib.NEVER,
        "not_built": ("Fictitious references, response-time and edit-count measures and "
                      "test-retest traps are deliberately not built: a participant would "
                      "recognise any of them as deception if we explained it afterwards."),
    })


@api.post("/me/{token}/calibration/opt-in", status_code=201, tags=["calibration"])
def calibration_opt_in(token: str, body: dict = Body(default_factory=dict)):
    _calibration_guard()
    expert_id = _enrolled_expert(token)
    try:
        enrolment = HARD.calibration.enrol(
            expert_id, bool(body.get("consent")),
            body.get("disclosure_version") or "", now())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return envelope({**enrolment.as_dict(),
                     "disclosure": calibration_lib.DISCLOSURE,
                     "message": "You are in. You will see your own report first, and you can "
                                "switch it off at any time."})


@api.get("/me/{token}/calibration/items", tags=["calibration"])
def calibration_items(token: str, limit: int = 2):
    """The next items, and never more than the programme says it sends: at most two a month, on
    their own, never inside a pulse card."""
    _calibration_guard()
    expert_id = _enrolled_expert(token)
    enrolment = HARD.calibration.get(expert_id)
    if not enrolment:
        raise HTTPException(404, "this link is not enrolled in the calibration programme")
    answered = {answer["item_id"] for answer in enrolment.answers}
    pool = calibration_lib.items_from_resolved(data.resolved_risks())
    remaining = [item for item in pool if item["id"] not in answered]
    return envelope({
        "items": remaining[:max(1, min(int(limit), 2))],
        "items_answered": enrolment.items_answered,
        "items_still_needed": enrolment.as_dict()["items_still_needed"],
        "confidence_prompt": calibration_lib.CONFIDENCE_PROMPT,
        "note": "Each item is something ACAPS already has a record of; the record is named on it.",
    })


@api.post("/me/{token}/calibration/items", status_code=201, tags=["calibration"])
def calibration_answer(token: str, body: dict = Body(default_factory=dict)):
    _calibration_guard()
    expert_id = _enrolled_expert(token)
    wanted = (body.get("item_id") or "").strip()
    item = next((i for i in calibration_lib.items_from_resolved(data.resolved_risks())
                 if i["id"] == wanted), None)
    if not item:
        raise HTTPException(404, f"no calibration item {wanted}")
    try:
        enrolment = HARD.calibration.record(expert_id, item, (body.get("answer") or "").strip(),
                                            int(body.get("confidence") or 0), now())
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    # Whether this one was right is not returned. Item-by-item feedback would turn the programme
    # into a quiz with a score, and the report is the only output it has.
    return envelope({**enrolment.as_dict(),
                     "message": ("Recorded. Nothing comes back item by item; the report comes "
                                 f"after {calibration_lib.MIN_ITEMS} of them.")})


@api.get("/me/{token}/calibration/report", tags=["calibration"])
def calibration_report(token: str):
    """The expert's own report, and the first place it exists at all."""
    _calibration_guard()
    expert_id = _enrolled_expert(token)
    enrolment = HARD.calibration.get(expert_id)
    if not enrolment:
        raise HTTPException(404, "this link is not enrolled in the calibration programme")
    try:
        return envelope({**calibration_lib.report(enrolment), "private": True,
                         "note_to_you": "Yours alone unless you say otherwise."})
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@api.post("/me/{token}/calibration/share", tags=["calibration"])
def calibration_share(token: str, body: dict = Body(default_factory=dict)):
    """The second, separate opt-in: the committee sees the report only after this."""
    _calibration_guard()
    expert_id = _enrolled_expert(token)
    enrolment = HARD.calibration.get(expert_id)
    if not enrolment:
        raise HTTPException(404, "this link is not enrolled in the calibration programme")
    if not enrolment.report_available:
        raise HTTPException(409, "there is no report to share yet")
    enrolment.shared_with_committee = bool(body.get("share"))
    return envelope({**enrolment.as_dict(),
                     "message": ("Shared with the committee as a paragraph, never as a weight."
                                 if enrolment.shared_with_committee else
                                 "Not shared. The committee sees only that an enrolment exists.")})


@api.post("/me/{token}/calibration/off", tags=["calibration"])
def calibration_off(token: str):
    _calibration_guard()
    expert_id = _enrolled_expert(token)
    try:
        enrolment = HARD.calibration.switch_off(expert_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return envelope({**enrolment.as_dict(),
                     "message": "Off. The report is no longer computed, and the committee no "
                                "longer sees that it exists."})


@api.get("/committee/calibration", tags=["committee"])
def committee_calibration():
    """Counts, flagged. No names, no reports, unless an expert shared one."""
    return envelope({"enabled": ff.enabled("FF_CALIBRATION"), **HARD.calibration.counts()})


# -- reach: the channels, the address book and the inbound replies -------------
def _contact_or_404(expert_id: str):
    contact = REACH.book.get(expert_id)
    if not contact:
        raise HTTPException(404, f"{expert_id} is not in the address book")
    return contact


@api.get("/reach/status", tags=["reach"])
def reach_status():
    """What is built, what is flagged off, and the sentence that keeps the delivery view honest."""
    return envelope({
        "channels": channel_lib.status(),
        "cadence": cadence_lib.status(),
        "contacts": REACH.book.summary(),
        "charter": contact_lib.CHARTER,
        "charter_version": contact_lib.CHARTER_VERSION,
        "transport_note": channel_lib.TRANSPORT_NOTE,
        "guarantees": ("One pulse per expert per seven days across every panel. STOP honoured "
                       "immediately and logged. No message body carries the ACAPS rating, a "
                       "severity number or a place name finer than the crisis title. A reminder "
                       "never carries a count of who has answered."),
        "does_not": ("Send anything. No gateway or mailbox is configured in this build, so every "
                     "message is composed in full and recorded in the outbox."),
    })


@api.get("/reach/contacts", tags=["reach"])
def list_contacts():
    """No names and no addresses: the desk needs to route a question, not read a phone book."""
    return envelope({
        "contacts": [c.public_view() for c in sorted(REACH.book.contacts.values(),
                                                     key=lambda c: c.expert_id)],
        **REACH.book.summary(),
        "note": ("Display names and addresses stay in the restricted registry; this list carries "
                 "neither, so a screenshot of the desk cannot carry them either."),
    })


@api.post("/reach/contacts", status_code=201, tags=["reach"])
def add_contact(body: dict = Body(default_factory=dict)):
    try:
        contact = REACH.book.upsert(body)
    except (contact_lib.Refused, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    if body.get("charter_version"):
        try:
            REACH.book.record_consent(contact.expert_id, body["charter_version"])
        except contact_lib.Refused as exc:
            raise HTTPException(422, str(exc)) from exc
    return envelope({**contact.public_view(),
                     "note": ("Added as invited and unconsented. The first message is the "
                              "consent-first note, and nothing else is sent until they reply.")})


@api.post("/reach/contacts/import", status_code=201, tags=["reach"])
def import_contacts(body: dict = Body(default_factory=dict)):
    """From the analyst's own contacts, as a CSV they already have."""
    text = body.get("csv") or ""
    if not text.strip():
        raise HTTPException(422, "send the file contents as `csv`")
    report = REACH.book.import_csv(text)
    return envelope({**report, **REACH.book.summary()})


@api.post("/reach/contacts/{expert_id}/stop", tags=["reach"])
def stop_contact(expert_id: str, body: dict = Body(default_factory=dict)):
    """One word, honoured now. The route exists so the inbound parser and the analyst use the
    same path, and so the act lands in the consent log either way."""
    _contact_or_404(expert_id)
    contact = REACH.book.stop(expert_id, body.get("said") or "STOP")
    logging_conf.log(log, "info", "contact stopped", expert_id=expert_id)
    return envelope({**contact.public_view(),
                     "message": "Stopped. Nothing further is sent, including reminders."})


@api.post("/reach/contacts/{expert_id}/pause", tags=["reach"])
def pause_contact(expert_id: str, body: dict = Body(default_factory=dict)):
    _contact_or_404(expert_id)
    contact = REACH.book.pause(expert_id, int(body.get("days") or contact_lib.PAUSE_DAYS),
                               body.get("said") or "PAUSE")
    return envelope({**contact.public_view(), "message": "Paused."})


@api.post("/reach/contacts/{expert_id}/consent", status_code=201, tags=["reach"])
def consent_contact(expert_id: str, body: dict = Body(default_factory=dict)):
    _contact_or_404(expert_id)
    try:
        contact = REACH.book.record_consent(expert_id, body.get("charter_version") or "")
    except contact_lib.Refused as exc:
        raise HTTPException(422, str(exc)) from exc
    return envelope({**contact.public_view(), "charter": contact_lib.CHARTER})


@api.post("/reach/preferences/{expert_id}", tags=["reach"])
def set_preferences(expert_id: str, body: dict = Body(default_factory=dict)):
    """The expert sets theirs; the analyst can only suggest. `by` says which this is."""
    _contact_or_404(expert_id)
    try:
        contact = REACH.book.set_preferences(expert_id, body,
                                             body.get("by") or "suggested_by_analyst")
    except (contact_lib.Refused, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return envelope({
        **contact.public_view(),
        "message": ("Saved as the expert's own choice." if contact.preferences_set_by == "expert"
                    else "Saved as a suggestion, and marked as one until the expert confirms it."),
    })


@api.get("/reach/consent-log", tags=["reach"])
def consent_log():
    """Every consent, pause and stop, with its time. An opt-out that is honoured but not recorded
    cannot be shown to have been honoured."""
    entries = REACH.book.consent_log
    return envelope({"entries": list(reversed(entries)), "n_entries": len(entries)})


@api.post("/reach/pulses/{pulse_id}/send", tags=["reach"])
def reach_send(pulse_id: str, body: dict = Body(default_factory=dict)):
    """Compose and record the message for every panel member who may receive one.

    Refusals are returned per expert rather than failing the call: one stopped contact must not
    stop the other seven from being asked, and the analyst needs to see which rule applied."""
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    risk = data.get_risk(pulse["risk_id"]) or {}
    kind = body.get("kind") or "pulse"
    if kind not in ("pulse", "first_contact", "reminder"):
        raise HTTPException(422, "kind must be pulse, first_contact or reminder")
    sent, refused = [], []
    for token, (token_pulse, expert_id) in sorted(STORE.tokens.items(),
                                                  key=lambda item: item[1][1]):
        if token_pulse != pulse_id:
            continue
        if not REACH.book.get(expert_id):
            refused.append({"expert_id": expert_id,
                            "why": "not in the address book; add the contact first"})
            continue
        try:
            delivery = REACH.send_pulse(pulse, risk, expert_id, token,
                                        body.get("channel_override"), kind,
                                        bool(body.get("escalating")))
        except (cadence_lib.Refused, contact_lib.Refused, message_lib.Unsafe) as exc:
            refused.append({"expert_id": expert_id, "why": str(exc)})
            continue
        sent.append({"expert_id": expert_id, "channel": delivery.channel,
                     "scheduled_for": delivery.scheduled_for, "transport": delivery.transport,
                     "subject": delivery.subject, "body": delivery.body})
    logging_conf.log(log, "info", "reach send", pulse_id=pulse_id, kind=kind,
                     sent=len(sent), refused=len(refused))
    return envelope({
        "pulse_id": pulse_id, "kind": kind, "sent": sent, "refused": refused,
        "n_sent": len(sent), "n_refused": len(refused),
        "transport_note": channel_lib.TRANSPORT_NOTE,
    })


@api.get("/reach/pulses/{pulse_id}/delivery", tags=["reach"])
def reach_delivery(pulse_id: str):
    """Counts per channel. Who answered is the analyst's business in the registry, not a field
    on a route the desk leaves open on a projector."""
    if not STORE.pulses.get(pulse_id):
        raise HTTPException(404, f"no pulse {pulse_id}")
    return envelope(REACH.delivery_report(pulse_id))


@api.get("/reach/outbox", tags=["reach"])
def reach_outbox(pulse_id: str | None = None, limit: int = 20):
    """The composed messages themselves, because the honest claim is "recorded, not sent" and
    that claim is only checkable if the thing recorded can be read."""
    rows = REACH.for_pulse(pulse_id) if pulse_id else REACH.outbox
    return envelope({
        "messages": [d.as_dict() for d in rows[-max(1, min(int(limit), 100)):]],
        "n_messages": len(rows),
        "transport_note": channel_lib.TRANSPORT_NOTE,
    })


@api.post("/reach/calls/schedule", status_code=201, tags=["reach"])
def schedule_call(body: dict = Body(default_factory=dict)):
    """An ICS invite to the expert and the analyst. The answer taken on that call is entered as
    relayed and counts only after the expert confirms it through their own link."""
    pulse_id = (body.get("pulse_id") or "").strip()
    expert_id = (body.get("expert_id") or "").strip()
    pulse = STORE.pulses.get(pulse_id)
    if not pulse:
        raise HTTPException(404, f"no pulse {pulse_id}")
    contact = _contact_or_404(expert_id)
    when = body.get("starts_at") or cadence_lib.next_send_time(contact)
    token = STORE._token_of.get(f"{pulse_id}:{expert_id}")
    ics = "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sealed Signals//Reach//EN",
        "BEGIN:VEVENT", f"UID:{pulse_id}-{expert_id}@sealed-signals",
        f"DTSTART:{str(when)[:19].replace('-', '').replace(':', '')}Z",
        "DURATION:PT10M",
        "SUMMARY:One question about a risk you follow",
        f"DESCRIPTION:A ten-minute call with {pulse.get('asked_by')}. "
        "Your answer is entered for you and counts once you confirm it.",
        "END:VEVENT", "END:VCALENDAR",
    ])
    delivery = REACH.deliver(reach_mod.Delivery(
        pulse_id=pulse_id, expert_id=expert_id, channel="call", kind="call",
        scheduled_for=str(when), token=token, body=ics, subject="A ten-minute call"))
    return envelope({
        "pulse_id": pulse_id, "expert_id": expert_id, "starts_at": delivery.scheduled_for,
        "ics": ics, "transport": delivery.transport,
        "note": ("The answer from this call is entered as relayed and does not count until the "
                 "expert confirms it at POST /api/e/{token}/relayed-confirm."),
    })


@api.post("/inbound/{channel}", tags=["reach"])
async def inbound(channel: str, body: dict = Body(default_factory=dict)):
    """An answer that arrived as a reply rather than a tap.

    A typed reply commits, unlike a link click: writing "4 likely" and sending it is a deliberate
    act, where following a URL is something a mail scanner does. The reply is read back in the
    response and the answer stays correctable until the deadline, which is the same promise the
    confirmation screen makes.

    A voice note is the exception that proves the rule: the transcript is a guess, so the response
    carries the read-back line the expert has to be shown before the deadline."""
    if channel not in ("email", "whatsapp", "signal", "sms", "voice"):
        raise HTTPException(404, f"no inbound channel {channel}")
    token = (body.get("token") or "").strip()
    text = body.get("text") or body.get("transcript") or ""
    resolved = STORE.resolve_token(token)
    if not resolved:
        # An unresolvable reply is still a person who answered. It goes to the analyst with the
        # text, rather than being dropped because the token was mangled by a mail client.
        parsed = inbound_lib.parse(text, channel)
        return envelope({
            "accepted": False, "needs_analyst": True, "parsed": parsed.as_dict(),
            "why": "this link could not be resolved, so the reply is held for the analyst",
        })
    pulse_id, expert_id = resolved
    parsed = inbound_lib.parse(text, channel)

    if parsed.act == "stop":
        if REACH.book.get(expert_id):
            REACH.book.stop(expert_id, parsed.original[:60])
        return envelope({"accepted": True, "act": "stop", "parsed": parsed.as_dict(),
                         "message": "Stopped. Nothing further is sent."})
    if parsed.act == "pause":
        if REACH.book.get(expert_id):
            REACH.book.pause(expert_id, contact_lib.PAUSE_DAYS, parsed.original[:60])
        return envelope({"accepted": True, "act": "pause", "parsed": parsed.as_dict(),
                         "message": f"Paused for {contact_lib.PAUSE_DAYS} days."})
    if parsed.needs_analyst:
        return envelope({
            "accepted": False, "needs_analyst": True, "parsed": parsed.as_dict(),
            "why": ("nothing in this reply could be read as a likelihood, an abstention or an "
                    "opt-out, so it goes to the analyst with the original text"),
        })

    pulse = STORE.pulses.get(pulse_id) or {}
    if store.past(pulse.get("expires_at") or ""):
        raise HTTPException(409, f"this round closed at {pulse.get('expires_at')}")
    contact = REACH.book.get(expert_id)
    default_mask = "pseudonym"
    answer_body = parsed.answer_body(default_mask)
    answer_body["relayed"] = bool(body.get("relayed"))
    if answer_body["relayed"]:
        answer_body["relayed_by"] = body.get("relayed_by") or "analyst"

    existing = STORE.find_answer(pulse_id, expert_id, None)
    try:
        if existing:
            # A second reply before the deadline is a correction, not a refusal. Someone who
            # writes "actually, 40" should not be told their answer is already in.
            answer = STORE.correct(existing, answer_body, SETTINGS.commitment_salt)
            act = "corrected"
        else:
            answer = STORE.seal(pulse_id, expert_id, answer_body, SETTINGS.commitment_salt,
                                SETTINGS.pseudonym_key)
            STORE.take_edit_key(answer)
            STORE.mark_used(token)
            act = "committed"
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    _record_day_roots()
    REACH.mark_answered(pulse_id, expert_id, answer.relayed)
    if contact:
        REACH.book.mark_answered(expert_id)
    await publish("answer_sealed", {"pulse_id": pulse_id, "n_answers": STORE.n_answers(pulse_id)})
    logging_conf.log(log, "info", "inbound answer", pulse_id=pulse_id, channel=channel, act=act)
    return envelope({
        "accepted": True, "act": act, "parsed": parsed.as_dict(),
        "committed_at": answer.committed_at, "commitment": answer.commitment,
        "version": answer.version, "mask": answer.mask,
        "counts": answer.counts(),
        "correction_allowed_until": pulse.get("expires_at"),
        "read_back": message_lib.voice_confirmation(parsed.as_dict()) if channel == "voice"
        else None,
        "transcript_source": "the request" if channel == "voice" else None,
        "message": ("Thanks. You'll hear how the panel saw it after the deadline."
                    if act == "committed" else
                    "Changed. Your earlier answer is kept with its own timestamp."),
    })


@api.post("/reach/pulses/{pulse_id}/close-the-loop", tags=["reach"])
def close_the_loop(pulse_id: str):
    """The message every expert who answered gets within 24 hours of the reveal: the group view,
    their own answer, ACAPS's band and what the analyst did. This is where the band first
    appears, which is what lets the card promise it is hidden."""
    result = STORE.results.get(pulse_id)
    if not result:
        raise HTTPException(409, "reveal the round before closing the loop on it")
    pulse = STORE.pulses.get(pulse_id) or {}
    risk = data.get_risk(pulse.get("risk_id") or "") or {}
    entry = next((e for e in STORE.ledger if e["pulse_id"] == pulse_id), None)
    sent = []
    for token, (token_pulse, expert_id) in sorted(STORE.tokens.items(),
                                                  key=lambda item: item[1][1]):
        if token_pulse != pulse_id or not STORE.answered(pulse_id, expert_id):
            continue
        contact = REACH.book.get(expert_id)
        if not contact:
            continue
        mine = STORE.find_answer(pulse_id, expert_id, None)
        panel = _panel_size(pulse_id)
        text = message_lib.closing_the_loop(contact, {
            "group_mean": result["mean"],
            "answered_share": (result["n"] / panel) if panel else None,
            "your_answer": {"probability": mine.probability} if mine else None,
            "acaps_band": risk.get("probability_acaps"),
            "analyst_decision": (entry or {}).get("decision") or "has not decided yet",
        })
        delivery = REACH.send_feedback(pulse_id, expert_id, text)
        sent.append({"expert_id": expert_id, "channel": delivery.channel, "body": text})
    return envelope({
        "pulse_id": pulse_id, "sent": sent, "n_sent": len(sent),
        "transport_note": channel_lib.TRANSPORT_NOTE,
        "note": ("Only the experts who answered. An answer with no identity kept gets the group "
                 "view without their own figure in it, because the service cannot tell which "
                 "answer was theirs."),
    })


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

        @staticmethod
        def _cache(response):
            """index.html must not be cached; the hashed assets should be, for ever.

            Vite names every bundle after its own contents, so `index-BJAbMz0I.js` can never mean
            two different things and is safe to keep. index.html is the one file that changes name
            for nothing and points at those names, so a browser holding yesterday's copy asks for
            assets this build no longer contains -- a blank page, on somebody else's laptop, with
            nothing in our logs to show it. Starlette sets neither header, which is how a deploy
            can be live and invisible at the same time."""
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("text/html"):
                response.headers["cache-control"] = "no-cache, must-revalidate"
            else:
                response.headers.setdefault("cache-control",
                                            "public, max-age=31536000, immutable")
            return response

        async def get_response(self, path: str, scope):  # type: ignore[override]
            try:
                return self._cache(await super().get_response(path, scope))
            except StarletteHTTPException as exc:
                if exc.status_code != 404:
                    raise
                # An unknown /api path is a 404, not the app. Serving index.html there hands a
                # caller HTML with a 200 on it, and the error they see is "unexpected token <"
                # somewhere else entirely -- which is how a renamed route costs an afternoon.
                # StaticFiles normalises the path with the OS separator, so on Windows this
                # arrives as api\analyst\board and a check for "api/" silently never fires.
                wanted = path.replace("\\", "/")
                if wanted == "api" or wanted.startswith("api/"):
                    raise HTTPException(404, f"no API route /{wanted}") from exc
                return await super().get_response("index.html", scope)

    app.mount("/", SinglePageApp(directory=str(UI_DIST), html=True), name="ui")
