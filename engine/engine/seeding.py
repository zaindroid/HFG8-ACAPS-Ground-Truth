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
            languages=["fr", "en"],
            channel="email",
            status="approved",
            region=row["region"],
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
    from .api import _build_pulse, _trigger_evidence   # imported here to avoid a circular import

    store.reset()
    seed_experts(store)
    risk = data.get_risk(risk_id)
    if not risk:
        raise RuntimeError(f"{risk_id} is not in the export; cannot seed the demo")

    store.contracts[risk_id] = {**QUESTION_CONTRACT, "risk_id": risk_id, "frozen_at": now()}
    pulse = _build_pulse(risk, "doorbell", None, _trigger_evidence(risk))
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

    # Four open links with nothing sealed behind them, for the QR step where the jury becomes the panel.
    for index in range(1, 5):
        guest = store.add_expert(Expert(
            id=f"X-guest-{index:02d}", geo_tags=["TCD"], theme_tags=["conflict"],
            affiliation_tag="guest", status="approved", region="stage", synthetic=True,
        ))
        store.issue_token(pulse_id, guest.id)
    return pulse_id
