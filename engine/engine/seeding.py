"""The synthetic panel and a sealed round, so a clean clone has something to show.

Everything here is SYNTHETIC and labelled as such in the API and in the UI footer. These are not real
humanitarian experts and their answers are not evidence about Chad -- they exist so the loop can be
demonstrated offline, with no network and no real person's judgement standing in for a made-up one.
"""
from __future__ import annotations

from . import data
from .store import Expert, Store, now

# Eight synthetic experts. Regions are real eastern-Chad admin names so the map has somewhere to put them;
# the affiliation caps are exercised on purpose (three NGO entries maximum per panel).
# skill: how much of theoutcome the expert sees on risks inside their themes (0-1).
# years: declared field experience. Both are synthetic, and both are stated as such in the API.
PANEL = [
    {"id": "X-syn-01", "region": "Ouaddaï", "themes": ["conflict", "access"], "affiliation": "ngo",
     "skill": 0.52, "years": 11, "langs": ["fr", "ar", "en"]},
    {"id": "X-syn-02", "region": "Ouaddaï", "themes": ["conflict", "political"], "affiliation": "un",
     "skill": 0.34, "years": 7, "langs": ["fr", "en"]},
    {"id": "X-syn-03", "region": "Wadi Fira", "themes": ["displacement", "food"], "affiliation": "ngo",
     "skill": 0.44, "years": 9, "langs": ["fr", "ar"]},
    {"id": "X-syn-04", "region": "Wadi Fira", "themes": ["conflict"], "affiliation": "research",
     "skill": 0.26, "years": 4, "langs": ["en"]},
    {"id": "X-syn-05", "region": "Ouaddaï", "themes": ["access", "food"], "affiliation": "ngo",
     "skill": 0.38, "years": 13, "langs": ["fr", "ar", "en"]},
    {"id": "X-syn-06", "region": "Wadi Fira", "themes": ["conflict", "displacement"], "affiliation": "un",
     "skill": 0.58, "years": 15, "langs": ["fr", "en"]},
    {"id": "X-syn-07", "region": "N'Djamena", "themes": ["political", "economic"], "affiliation": "government",
     "skill": 0.18, "years": 6, "langs": ["fr"]},
    {"id": "X-syn-08", "region": "Ennedi-Est", "themes": ["conflict", "access"], "affiliation": "research",
     "skill": 0.47, "years": 8, "langs": ["fr", "en"]},
]

# The frozen question contract for the demo risk. The card shows this and nothing looser: an
# answer is adjudicated against these words, and a card that asked something vaguer would collect
# answers to a question nobody can score.
QUESTION_CONTRACT = {
    "event": ("More than 50,000 new arrivals from Sudan registered by UNHCR in Ouadda\u00ef and "
              "Wadi Fira"),
    "location": "Ouadda\u00ef and Wadi Fira, eastern Chad",
    "threshold": "> 50,000 newly registered arrivals (cumulative from 1 November 2026)",
    "horizon_deadline": "2027-03-31",
    "resolution_source": "UNHCR registration figures for eastern Chad, as reported to ACAPS",
    "adjudication_rule": ("Cumulative newly registered arrivals in the two provinces, read from "
                          "the UNHCR figure published nearest the deadline. A revision published "
                          "later does not reopen the question."),
    "text": ("Will more than 50,000 new arrivals from Sudan be registered in Ouadda\u00ef and "
             "Wadi Fira by 31 March 2027?"),
}

# One round of answers: a real spread with a reasoned minority, two abstentions, two entries whose
# wording is close enough that the integrity layer should say so out loud, one answer taken by
# phone and confirmed by its author, and one that was corrected before the deadline.
#
# Three of the six estimates are a word with no number behind it, which is the common case on a
# phone. The aggregate uses the band midpoint for those and says so in `number_note` -- a word is
# never silently turned into a point.
ANSWERS = [
    {"mask": "pseudonym", "likelihood_word": "likely", "probability": 0.85, "confidence": "sure",
     "panel_share_yes": 0.7, "source_tag": "saw", "trigger_pick": "T1",
     "missing": "Night-time militia movement near Adre is not in any public reporting yet."},
    {"mask": "pseudonym", "likelihood_word": "likely", "confidence": "fairly sure",
     "panel_share_yes": 0.75, "source_tag": "heard", "trigger_pick": "T1",
     "missing": "Night-time militia movement near Adre is not in public reporting yet."},
    {"mask": "known", "likelihood_word": "likely", "confidence": "fairly sure",
     "panel_share_yes": 0.6, "source_tag": "read", "trigger_pick": "T2",
     "missing": "Camp capacity in Ouaddai is already past what the sites were planned for."},
    {"mask": "anonymous", "likelihood_word": "likely", "probability": 0.70,
     "confidence": "fairly sure", "panel_share_yes": 0.65, "source_tag": "saw",
     "trigger_pick": "T2",
     "missing": "Camp capacity in Ouaddai is beyond the planned site figures."},
    {"mask": "pseudonym", "likelihood_word": "even", "confidence": "not sure",
     "panel_share_yes": 0.55, "source_tag": "read", "trigger_pick": "T3",
     "missing": "Seasonal access after the rains will decide whether any of this can be reached."},
    # The reasoned minority, and the one answer that was corrected: it went in as 'even' and was
    # revised down before the deadline. Both versions are kept.
    {"mask": "pseudonym", "likelihood_word": "even", "confidence": "fairly sure",
     "panel_share_yes": 0.6, "source_tag": "saw", "trigger_pick": "T1",
     "missing": "Border raids have slowed since mid-September.",
     "_correction": {"mask": "pseudonym", "likelihood_word": "unlikely", "probability": 0.30,
                     "confidence": "sure", "panel_share_yes": 0.6, "source_tag": "saw",
                     "trigger_pick": "T1",
                     "missing": "Border raids have slowed since mid-September.",
                     "against": ("The pressure is displacement, not attacks; registration could "
                                 "stay flat while the border stays quiet.")}},
    # Taken by phone by the analyst and confirmed by its author through their own link. Until that
    # confirmation it would not have counted in the round at all.
    {"mask": "known", "stance": "outside_my_expertise", "panel_share_yes": 0.7,
     "relayed": True, "relayed_by": "analyst", "_relayed_confirm": True,
     "missing": ("Market prices in Abeche would tell you about absorption capacity, "
                 "and nobody is tracking them.")},
    {"mask": "pseudonym", "stance": "not_enough_evidence", "panel_share_yes": 0.65,
     "source_tag": "heard",
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


# The address book behind the synthetic panel (section 6e). Channels, languages and hours vary
# because that is the point of the module: the question goes where the expert already is. Two
# contacts are deliberately unreachable -- one stopped, one paused -- so the cadence rules are
# visible in the demo rather than only in the tests.
CONTACTS = [
    {"expert_id": "X-syn-01", "display_name": "Contact 01 (synthetic)", "org_type": "ngo",
     "coverage_area": "the Chad-Sudan border", "channel_pref": "email", "languages": ["fr", "en"],
     "hour_pref": 8, "tz": "Africa/Ndjamena", "utc_offset_hours": 1, "consented": True,
     "set_by": "expert"},
    {"expert_id": "X-syn-02", "display_name": "Contact 02 (synthetic)", "org_type": "un",
     "coverage_area": "protection in eastern Chad", "channel_pref": "whatsapp",
     "languages": ["en"], "hour_pref": 9, "tz": "Africa/Ndjamena", "utc_offset_hours": 1,
     "consented": True, "set_by": "expert"},
    {"expert_id": "X-syn-03", "display_name": "Contact 03 (synthetic)", "org_type": "ngo",
     "coverage_area": "displacement across the Sahel", "channel_pref": "sms",
     "languages": ["fr"], "hour_pref": 7, "tz": "Africa/Ndjamena", "utc_offset_hours": 1,
     "consented": True, "set_by": "expert"},
    {"expert_id": "X-syn-04", "display_name": "Contact 04 (synthetic)", "org_type": "research",
     "coverage_area": "armed group activity in Darfur", "channel_pref": "signal",
     "languages": ["en"], "hour_pref": 10, "tz": "Europe/Paris", "utc_offset_hours": 1,
     "consented": True, "set_by": "suggested_by_analyst"},
    {"expert_id": "X-syn-05", "display_name": "Contact 05 (synthetic)", "org_type": "ngo",
     "coverage_area": "humanitarian access in the east", "channel_pref": "teams",
     "languages": ["en"], "hour_pref": 9, "tz": "Europe/Paris", "utc_offset_hours": 1,
     "consented": True, "set_by": "suggested_by_analyst"},
    {"expert_id": "X-syn-06", "display_name": "Contact 06 (synthetic)", "org_type": "un",
     "coverage_area": "camp coordination in Ouaddai", "channel_pref": "call",
     "languages": ["fr", "en"], "hour_pref": 11, "tz": "Africa/Ndjamena",
     "utc_offset_hours": 1, "consented": True, "set_by": "expert"},
    {"expert_id": "X-syn-07", "display_name": "Contact 07 (synthetic)", "org_type": "government",
     "coverage_area": "market prices in the Sahel", "channel_pref": "email",
     "languages": ["fr"], "hour_pref": 8, "tz": "Africa/Ndjamena", "utc_offset_hours": 1,
     "consented": True, "set_by": "expert", "paused": True},
    {"expert_id": "X-syn-08", "display_name": "Contact 08 (synthetic)", "org_type": "research",
     "coverage_area": "cross-border trade routes", "channel_pref": "email", "languages": ["en"],
     "hour_pref": 8, "tz": "Europe/Paris", "utc_offset_hours": 1, "consented": True,
     "set_by": "expert", "stopped": True},
]

DEMO_CRISIS = "TCD005"
DEMO_REPLAY = ("Mar2026", "Apr2026")


def seed_alerts(alert_store, risk_id: str = DEMO_RISK, crisis_id: str = DEMO_CRISIS) -> dict:
    """Confirm the R1043 - TCD005 link and replay the real April 2026 move, so the desk opens on the
    fact the demo opens on: ACAPS's own numbers, diffed by our own rules."""
    from . import alerts as alert_engine

    alert_store.reset()
    alert_engine.confirm_link(alert_store, risk_id, crisis_id, "seed")
    return alert_engine.run(alert_store, *DEMO_REPLAY)


def _demo_evidence(risk: dict) -> list[dict]:
    """What the demo round shows as the reason it was sent.

    The April 2026 TCD005 severity move first, because that is the answer to "why am I being
    asked this" -- ACAPS's own index went 6.1 to 6.9, the largest deterioration of 123 crises
    that month. Then the risk's own trigger completion rates, which are also ACAPS's published
    judgement. Both are real records; the desk renders the first as a severity visual and the
    second as lines.

    The seeded round used to carry the trigger rates alone, which left the desk with nothing to
    draw and the demo with no answer to that question."""
    from . import alerts as alert_engine
    from .api import _alert_evidence, _chain_alert, _trigger_evidence

    evidence: list[dict] = []
    try:
        store = alert_engine.AlertStore()
        alert_engine.confirm_link(store, risk["risk_id"], DEMO_CRISIS, "seed")
        replay = alert_engine.run(store, *DEMO_REPLAY)
        event = next((e for e in replay["events"]
                      if e["crisis_id"] == DEMO_CRISIS and e["metric"] == "index"), None)
        if event:
            evidence = _alert_evidence(event)
            # The first step of the demo risk's process chain (mechanism 8).
            _chain_alert(risk["risk_id"], event)
    except Exception:                                                     # noqa: BLE001
        # The cached editions are in the repository, so this does not normally fail. If it ever
        # does, the round still goes out with the risk's own triggers rather than no evidence.
        evidence = []
    return evidence + _trigger_evidence(risk)


def seed_contacts(reach, store: Store) -> dict:
    """The address book for the synthetic panel. Separate from seed_demo so the core loop and its
    tests never depend on Reach existing."""
    from .reach import contacts as contact_lib

    reach.reset()
    for row in CONTACTS:
        contact = reach.book.upsert({
            "expert_id": row["expert_id"], "display_name": row["display_name"],
            "org_type": row["org_type"], "coverage_area": row["coverage_area"],
            "theme_tags": (store.experts[row["expert_id"]].theme_tags
                           if row["expert_id"] in store.experts else []),
            "languages": row["languages"], "channel_pref": row["channel_pref"],
            "hour_pref": row["hour_pref"], "tz": row["tz"],
            "utc_offset_hours": row["utc_offset_hours"],
            "address": f"{row['expert_id'].lower()}@example.invalid",
        })
        if row.get("consented"):
            reach.book.record_consent(contact.expert_id, contact_lib.CHARTER_VERSION)
        contact.preferences_set_by = row["set_by"]
        contact.status = "active"
        if row.get("paused"):
            reach.book.pause(contact.expert_id)
        if row.get("stopped"):
            reach.book.stop(contact.expert_id)
    return {**reach.book.summary(), "synthetic": True}


def seed_demo(store: Store, settings, risk_id: str = DEMO_RISK, seal: bool = True) -> str:
    """Build the panel, open a pulse on the demo risk, and seal one round of answers.

    Returns the pulse id. Idempotent enough for a restart: a second call rebuilds from empty.
    """
    from .api import HARD, _build_pulse, _chain   # imported here to avoid a circular import
    from .hardening import anchors as anchor_lib

    store.reset()
    HARD.chain.drop(risk_id)
    seed_experts(store)
    seed_roster(store)
    # Past forecasts first: the board, the weights and the calibration reports all read
    # from this, and a weight earned on history should be in place before this round.
    seed_history(store, settings.pseudonym_key)
    risk = data.get_risk(risk_id)
    if not risk:
        raise RuntimeError(f"{risk_id} is not in the export; cannot seed the demo")

    store.contracts[risk_id] = {**QUESTION_CONTRACT, "risk_id": risk_id, "frozen_at": now()}
    pulse = _build_pulse(risk, "alert", None, _demo_evidence(risk))
    pulse_id = pulse["id"]

    for row, expert in zip(ANSWERS, PANEL):
        # Each panel member gets a magic link; /demo/links lists them for the desk.
        token = store.issue_token(pulse_id, expert["id"])
        if not seal:
            continue
        body = {"stance": row.get("stance", "estimate"), "round": 1,
                **{k: v for k, v in row.items() if not k.startswith("_")}}
        answer = store.seal(pulse_id, expert["id"], body, settings.commitment_salt,
                            settings.pseudonym_key)
        store.take_edit_key(answer)
        if row.get("_correction"):
            store.correct(answer, {"stance": "estimate", "round": 1, **row["_correction"]},
                          settings.commitment_salt)
        if row.get("_relayed_confirm"):
            store.confirm_relayed(answer)
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

    # Mechanism 8: the rest of the demo risk's process chain. Counts and the commitment root only.
    _chain(risk_id, "panel_invited", {
        "pulse_id": pulse_id,
        "n_invited": sum(1 for (pid, _) in store.tokens.values() if pid == pulse_id),
    })
    answers = store.answers.get(pulse_id, [])
    if answers:
        _chain(risk_id, "answers_sealed", {
            "pulse_id": pulse_id, "n_answers": len(answers),
            "commitment_root": anchor_lib.merkle_root([a.commitment for a in answers]),
        })
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
