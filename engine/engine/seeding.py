"""The synthetic panel and a sealed round, so a clean clone has something to show.

Everything here is SYNTHETIC and labelled as such in the API and in the UI footer. These are not real
humanitarian experts and their answers are not evidence about Chad -- they exist so the loop can be
demonstrated offline, with no network and no real person's judgement standing in for a made-up one.
"""
from __future__ import annotations

from . import data
from .store import Expert, Store

# Eight synthetic experts. Regions are real eastern-Chad admin names so the map has somewhere to put them;
# the affiliation caps are exercised on purpose (three NGO entries maximum per panel).
PANEL = [
    {"id": "X-syn-01", "region": "Ouaddai", "themes": ["conflict", "access"], "affiliation": "ngo"},
    {"id": "X-syn-02", "region": "Ouaddai", "themes": ["conflict", "political"], "affiliation": "un"},
    {"id": "X-syn-03", "region": "Wadi Fira", "themes": ["displacement", "food"], "affiliation": "ngo"},
    {"id": "X-syn-04", "region": "Wadi Fira", "themes": ["conflict"], "affiliation": "research"},
    {"id": "X-syn-05", "region": "Sila", "themes": ["access", "food"], "affiliation": "ngo"},
    {"id": "X-syn-06", "region": "Sila", "themes": ["conflict", "displacement"], "affiliation": "un"},
    {"id": "X-syn-07", "region": "N'Djamena", "themes": ["political", "economic"], "affiliation": "government"},
    {"id": "X-syn-08", "region": "Ennedi-Est", "themes": ["conflict", "access"], "affiliation": "research"},
]

# One round of answers: a real spread with a reasoned minority, two abstentions, and two entries whose
# wording is close enough that the integrity layer should say so out loud.
ANSWERS = [
    {"mask": "pseudonym", "probability": 0.85, "confidence": 4, "panel_share_yes": 0.7, "source_tag": "saw",
     "missing": "Night-time militia movement near Adre is not in any public reporting yet."},
    {"mask": "pseudonym", "probability": 0.80, "confidence": 4, "panel_share_yes": 0.75, "source_tag": "heard",
     "missing": "Night-time militia movement near Adre is not in public reporting yet."},
    {"mask": "known", "probability": 0.75, "confidence": 3, "panel_share_yes": 0.6, "source_tag": "read",
     "missing": "Camp capacity in Ouaddai is already past what the sites were planned for."},
    {"mask": "anonymous", "probability": 0.70, "confidence": 3, "panel_share_yes": 0.65, "source_tag": "saw",
     "missing": "Camp capacity in Ouaddai is beyond the planned site figures."},
    {"mask": "pseudonym", "probability": 0.55, "confidence": 2, "panel_share_yes": 0.55, "source_tag": "read",
     "missing": "Seasonal access after the rains will decide whether any of this can be reached."},
    {"mask": "pseudonym", "probability": 0.30, "confidence": 4, "panel_share_yes": 0.6, "source_tag": "saw",
     "missing": "Border raids have slowed since mid-September; the pressure is displacement, not attacks."},
    {"mask": "known", "stance": "outside_my_expertise", "panel_share_yes": 0.7,
     "missing": "I work on prices, not protection. Ask me about the market in Abeche."},
    {"mask": "pseudonym", "stance": "not_enough_evidence", "panel_share_yes": 0.65, "source_tag": "heard",
     "missing": "Nothing I have seen this week would move me either way."},
]

DEMO_RISK = "R1043"


def seed_experts(store: Store) -> list[Expert]:
    experts = []
    for row in PANEL:
        experts.append(store.add_expert(Expert(
            id=row["id"],
            geo_tags=["TCD"],
            theme_tags=row["themes"],
            affiliation_tag=row["affiliation"],
            languages=["fr", "en"],
            channel="email",
            status="approved",
            region=row["region"],
            synthetic=True,
        )))
    return experts


DEMO_CRISIS = "TCD005"
DEMO_REPLAY = ("Mar2026", "Apr2026")


def seed_alerts(alert_store, risk_id: str = DEMO_RISK, crisis_id: str = DEMO_CRISIS) -> dict:
    """Confirm the R1043 - TCD005 link and replay the real April 2026 move, so the desk opens on the
    fact the demo opens on: ACAPS's own numbers, diffed by our own rules."""
    from . import alerts as alert_engine

    alert_store.reset()
    alert_engine.confirm_link(alert_store, risk_id, crisis_id, "seed")
    return alert_engine.run(alert_store, *DEMO_REPLAY)


def seed_demo(store: Store, settings, risk_id: str = DEMO_RISK, seal: bool = True) -> str:
    """Build the panel, open a pulse on the demo risk, and seal one round of answers.

    Returns the pulse id. Idempotent enough for a restart: a second call rebuilds from empty.
    """
    from .api import _build_pulse, _trigger_evidence   # imported here to avoid a circular import

    store.reset()
    seed_experts(store)
    risk = data.get_risk(risk_id)
    if not risk:
        raise RuntimeError(f"{risk_id} is not in the export; cannot seed the demo")

    pulse = _build_pulse(risk, "doorbell", None, _trigger_evidence(risk))
    pulse_id = pulse["id"]

    for row, expert in zip(ANSWERS, PANEL):
        # Each panel member gets a magic link; /demo/links lists them for the desk.
        token = store.issue_token(pulse_id, expert["id"])
        if seal:
            body = {"stance": row.get("stance", "estimate"), "round": 1, **row}
            store.seal(pulse_id, expert["id"], body, settings.commitment_salt, settings.pseudonym_key)
            store.mark_used(token)

    # Four open links with nothing sealed behind them, for the QR step where the jury becomes the panel.
    for index in range(1, 5):
        guest = store.add_expert(Expert(
            id=f"X-guest-{index:02d}", geo_tags=["TCD"], theme_tags=["conflict"],
            affiliation_tag="guest", status="approved", region="stage", synthetic=True,
        ))
        store.issue_token(pulse_id, guest.id)
    return pulse_id
