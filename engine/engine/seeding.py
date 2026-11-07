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
# skill: how much of theoutcome the expert sees on risks inside their themes (0-1).
# years: declared field experience. Both are synthetic, and both are stated as such in the API.
PANEL = [
    {"id": "X-syn-01", "region": "Ouaddai", "themes": ["conflict", "access"], "affiliation": "ngo",
     "skill": 0.52, "years": 11, "langs": ["fr", "ar", "en"]},
    {"id": "X-syn-02", "region": "Ouaddai", "themes": ["conflict", "political"], "affiliation": "un",
     "skill": 0.34, "years": 7, "langs": ["fr", "en"]},
    {"id": "X-syn-03", "region": "Wadi Fira", "themes": ["displacement", "food"], "affiliation": "ngo",
     "skill": 0.44, "years": 9, "langs": ["fr", "ar"]},
    {"id": "X-syn-04", "region": "Wadi Fira", "themes": ["conflict"], "affiliation": "research",
     "skill": 0.26, "years": 4, "langs": ["en"]},
    {"id": "X-syn-05", "region": "Sila", "themes": ["access", "food"], "affiliation": "ngo",
     "skill": 0.38, "years": 13, "langs": ["fr", "ar", "en"]},
    {"id": "X-syn-06", "region": "Sila", "themes": ["conflict", "displacement"], "affiliation": "un",
     "skill": 0.58, "years": 15, "langs": ["fr", "en"]},
    {"id": "X-syn-07", "region": "N'Djamena", "themes": ["political", "economic"], "affiliation": "government",
     "skill": 0.18, "years": 6, "langs": ["fr"]},
    {"id": "X-syn-08", "region": "Ennedi-Est", "themes": ["conflict", "access"], "affiliation": "research",
     "skill": 0.47, "years": 8, "langs": ["fr", "en"]},
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
            languages=row.get("langs", ["fr", "en"]),
            channel="email",
            status="approved",
            region=row["region"],
            years_experience=row.get("years", 0),
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
    seed_roster(store)
    # Past forecasts first: the board, the weights and the calibration reports all read
    # from this, and a weight earned on history should be in place before this round.
    seed_history(store, settings.pseudonym_key)
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

    # Open links with nothing sealed behind them, for the QR step where the jury becomes the
    # panel. They are tagged for where they actually are -- The Hague, general expertise --
    # rather than borrowed Chad credentials, because the demo should not claim that a jury
    # member in a conference hall has field knowledge of Ouaddai. They are excluded from
    # panel matching for the same reason; what they write is still read.
    for index in range(1, 9):
        guest = store.add_expert(Expert(
            id=f"X-guest-{index:02d}", geo_tags=["NLD"], theme_tags=["general"],
            affiliation_tag="guest", languages=["en", "nl"], channel="email",
            status="approved", region="The Hague", years_experience=0, synthetic=True,
        ))
        store.issue_token(pulse_id, guest.id)
    return pulse_id


# --- Track records -------------------------------------------------------------------
# A super-estimator board with no history is an empty board, and a calibration report
# with nothing in it teaches an expert nothing. So each synthetic expert carries a past:
# forecasts on risks the Risk List has already resolved, scored against those real
# outcomes. The forecasts are generated, the outcomes are not, which is why a good
# expert here scores well rather than being declared good.

HISTORY_SEED = 20261107          # fixed, so every clone shows the same board
HISTORY_PER_EXPERT = (9, 16)     # how many past risks each expert has answered

# Which Risk List themes a trigger or title belongs to, for deciding whether a past risk
# sat inside an expert's declared expertise.
THEME_WORDS = {
    "conflict": ("conflict", "armed", "attack", "clash", "militia", "insecurity", "violence", "offensive"),
    "displacement": ("displace", "refugee", "returnee", "influx", "camp", "idp"),
    "food": ("food", "hunger", "famine", "harvest", "nutrition", "market", "price"),
    "access": ("access", "road", "blockade", "siege", "constraint", "supply"),
    "political": ("political", "election", "government", "coup", "protest", "sanction"),
    "economic": ("economic", "currency", "inflation", "fuel", "economy"),
}


def _themes_of(risk: dict) -> set[str]:
    text = f"{risk.get('title', '')} {risk.get('risk_type', '')}".lower()
    return {theme for theme, words in THEME_WORDS.items() if any(w in text for w in words)}


def seed_history(store: Store, pseudonym_key: str) -> int:
    """Give every seeded expert a real track record on already-resolved risks.

    An expert sees the outcome more clearly on risks inside their own themes, and barely
    at all outside them: skill is applied on-theme and halved off-theme. Brier is then the
    ordinary (p - outcome)^2 against what actually happened, and the reliability weight is
    moved by the same rule the live resolve path uses, so nothing here is special-cased.
    """
    import random

    from . import data

    resolved = [r for r in data.resolved_risks() if r.get("probability_acaps")]
    if not resolved:
        return 0
    profiles = [(row["id"], row["skill"], set(row["themes"])) for row in PANEL]
    profiles += [
        (expert_id, skill, set(store.experts[expert_id].theme_tags))
        for expert_id, skill in ROSTER_SKILL.items()
        if expert_id in store.experts
    ]
    written = 0
    for expert_id, expert_skill, expert_themes in profiles:
        expert = store.experts.get(expert_id)
        if not expert:
            continue
        rng = random.Random(f"{HISTORY_SEED}-{expert_id}")
        pool = rng.sample(resolved, min(len(resolved), rng.randint(*HISTORY_PER_EXPERT)))
        for risk in pool:
            truth = 1.0 if risk["status"].lower() == "materialised" else 0.0
            on_theme = bool(_themes_of(risk) & expert_themes)
            skill = expert_skill if on_theme else expert_skill * 0.5
            # Start at the base rate, move toward the truth by skill, then add honest noise.
            estimate = 0.5 + (truth - 0.5) * skill + rng.gauss(0, 0.20)
            estimate = round(min(0.97, max(0.03, estimate)), 2)
            brier = round((estimate - truth) ** 2, 4)
            store.scores.append({
                "expert_internal_id": expert.id,
                "risk_id": risk["risk_id"],
                "brier": brier,
                "resolved_at": risk.get("resolved_at") or "2026-01-01T00:00:00+00:00",
                "probability": estimate,
                "outcome": risk["status"],
                "acaps_band": risk.get("probability_acaps"),
                "on_theme": on_theme,
            })
            written += 1
        expert.weight = weight_from_brier(
            [s["brier"] for s in store.scores if s["expert_internal_id"] == expert.id])
    return written


def weight_from_brier(briers: list[float]) -> float:
    """w = 1 / (0.1 + mean Brier), the master prompt's rule, scaled so that chance-level
    accuracy (0.25) lands on 1.0 and clamped to the range the live path also respects."""
    if not briers:
        return 1.0
    mean = sum(briers) / len(briers)
    at_chance = 1 / (0.1 + 0.25)
    return round(max(0.5, min(2.0, (1 / (0.1 + mean)) / at_chance)), 4)


# --- The wider roster ----------------------------------------------------------------
# A panel of eight is the brief's panel size, not the size of the network. With only the
# Chad eight on file, /panels/match had nothing to choose from: every risk returned the
# same people and the composition check could never fail. This builds approved experts
# across the countries that actually carry active risks, so selection is a real step.

LANGUAGES_BY_ISO = {
    "SDN": ["ar", "en"], "SSD": ["en", "ar"], "TCD": ["fr", "ar"], "NER": ["fr"],
    "NGA": ["en"], "CMR": ["fr", "en"], "MLI": ["fr"], "ETH": ["am", "en"],
    "KEN": ["en", "sw"], "SOM": ["so", "en"], "MOZ": ["pt"], "MDG": ["fr", "mg"],
    "AFG": ["ps", "fa"], "SYR": ["ar"], "YEM": ["ar"], "PSE": ["ar"],
    "MMR": ["my", "en"], "PHL": ["en", "tl"], "IDN": ["id"], "COL": ["es"],
}
AFFILIATIONS = ["ngo", "un", "research", "government", "local-ngo", "donor"]
THEME_CYCLE = ["conflict", "displacement", "food", "access", "political", "economic"]


def seed_roster(store: Store, per_country: int = 4) -> int:
    """Approved experts across every country with an active risk.

    Themes are dealt from a fixed cycle rather than fitted to each country's risks, so some
    panels come out short of a theme the risk actually names. That gap is the point: the
    coverage check should be able to fail, or it is not a check.
    """
    import random

    from . import data

    seen: dict[str, str] = {}
    for risk in data.active_risks():
        for iso, name in zip(risk["country_iso"].split(","), risk["country"].split(",")):
            iso, name = iso.strip(), name.strip()
            if iso and iso != "TCD":        # the Chad panel is hand-written above
                seen.setdefault(iso, name)

    added = 0
    for index, (iso, name) in enumerate(sorted(seen.items())):
        rng = random.Random(f"{HISTORY_SEED}-roster-{iso}")
        for seat in range(per_country):
            themes = [THEME_CYCLE[(index + seat) % len(THEME_CYCLE)]]
            if seat % 2 == 0:
                themes.append(THEME_CYCLE[(index + seat + 2) % len(THEME_CYCLE)])
            expert = Expert(
                id=f"X-{iso.lower()}-{seat + 1:02d}",
                geo_tags=[iso],
                theme_tags=themes,
                affiliation_tag=AFFILIATIONS[(index + seat) % len(AFFILIATIONS)],
                languages=LANGUAGES_BY_ISO.get(iso, ["en"]),
                channel=["email", "whatsapp", "sms"][seat % 3],
                status="approved",
                region=name,
                years_experience=rng.randint(3, 18),
                synthetic=True,
            )
            store.add_expert(expert)
            ROSTER_SKILL[expert.id] = round(rng.uniform(0.15, 0.55), 3)
            added += 1
    return added


ROSTER_SKILL: dict[str, float] = {}
