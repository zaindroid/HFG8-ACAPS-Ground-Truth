"""The adaptive half of the expert card.

Two rules hold the whole design together.

**The scored question never varies.** Probability, panel share, confidence and stance are the
frozen core: identical wording, identical order, asked of everyone. They are what the group
view aggregates and what Brier scores, so question-contract.md stays satisfied and the mean
stays a mean of one quantity. Probes sit after the core and feed themes, coverage and
minority reasons only. Nothing here touches a number that is published or scored.

**A card reads nothing about other experts.** Every choice below comes from the risk record
and from the expert's own profile, so the card is fully determined once the link is issued,
before anyone has answered. That is not a policy against herding, it is the absence of a
channel for it: there is no value a peer could set that would change what this card asks.

Probes are selected from a fixed bank, generated from fields the export already carries. The
selection is a hash of the expert and risk ids, so it is reproducible, loggable and even
across a panel without anyone coordinating it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROBE_SLOTS = 2        # the minute allows the core plus two, no more
TEXT_LIMIT = 240

# The humanitarian sectors the export itself uses, so "something other than conflict" is
# offered as a real option rather than left for the expert to volunteer against the framing.
PRIORITY_NEEDS = [
    "Protection", "Food security", "Health", "WASH", "Shelter",
    "Displacement", "Nutrition", "Livelihoods", "Humanitarian access", "Education",
]
EXPOSURE_BANDS = ["<20,000", "20,000-100,000", "100,000-250,000", "250,000-500,000", ">500,000"]


def _digest(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:8], 16)


# Round 1 hides the ACAPS rating so it cannot anchor a first answer. An excerpt lifted from
# the rationale must not reintroduce it by quoting the band in prose.
BAND_WORDS = ("very low", "very high", "low probability", "high probability",
              "medium probability", "rated high", "rated medium", "rated low")


def _scrub_rating(text: str) -> str:
    out = text
    for word in BAND_WORDS:
        for variant in (word, word.capitalize(), word.title()):
            out = out.replace(variant, "[rating withheld]")
    return out


def _first_sentence(text: str, limit: int = 220) -> str:
    cleaned = " ".join(_scrub_rating(text or "").split())
    if not cleaned:
        return ""
    for stop in (". ", "; "):
        if stop in cleaned[:limit]:
            return cleaned[: cleaned.index(stop, 0, limit) + 1].strip()
    return (cleaned[:limit] + "…") if len(cleaned) > limit else cleaned


def trigger_order(risk: dict, expert_id: str) -> list[dict]:
    """The risk's triggers, rotated per expert.

    If every card lists the same trigger first, the whole panel anchors on it and the group
    view records that ordering as if it were a finding. Rotating by expert id spreads the
    first-position effect instead of concentrating it, and the rotation is reproducible.
    """
    triggers = [t for t in (risk.get("triggers") or []) if t.get("title")]
    if len(triggers) < 2:
        return triggers
    offset = _digest(expert_id, risk.get("risk_id", "")) % len(triggers)
    return triggers[offset:] + triggers[:offset]


def _off_theme_need(risk: dict, expert_themes: list[str]) -> list[str]:
    """Sector options that do not restate the expert's own speciality.

    A conflict analyst asked to choose among conflict framings will choose one. The point of
    this probe is to make room for the answer their expertise does not predict.
    """
    own = {t.lower() for t in expert_themes}
    alias = {"conflict": "Protection", "displacement": "Displacement", "food": "Food security",
             "access": "Humanitarian access", "political": "Protection", "economic": "Livelihoods"}
    mine = {alias.get(t, "") for t in own}
    return [need for need in PRIORITY_NEEDS if need not in mine][:6]


def deadline_text(risk: dict) -> str:
    """The horizon as a date. "Within six months" is not something anyone forecasts against."""
    from datetime import date, timedelta

    months = int(risk.get("horizon_months") or 6)
    return (date.today() + timedelta(days=round(months * 30.44))).strftime("%d %B %Y")


def band_base_rate(risk: dict) -> tuple[int, float] | None:
    """How often this probability band has actually resolved yes, from the export itself.

    Used to confront an estimate with the record, never to correct it: an expert sitting
    well off the base rate may be the one seeing what the base rate cannot.
    """
    from . import data

    band = (risk.get("probability_acaps") or "").strip()
    if not band:
        return None
    resolved = [r for r in data.resolved_risks()
                if (r.get("probability_acaps") or "").strip() == band]
    if len(resolved) < 10:
        return None
    hit = sum(1 for r in resolved if r["status"].lower() == "materialised")
    return len(resolved), hit / len(resolved)


# One question per expertise, naming the thing that expertise actually decides.
SECTOR_QUESTIONS = {
    "displacement": ("Which area runs out of absorption capacity first?",
                     "Sites, registration and services, not arrival numbers."),
    "conflict": ("Whose next move decides this?",
                 "The actor the others react to."),
    "food": ("If the border closes for a month, which market fails first?",
             "Where supply has no second route."),
    "access": ("Which route closes first if this escalates?",
               "The one whose loss cuts off the most people."),
    "political": ("Which decision in the capital would change this most?",
                  "One that could plausibly be taken this quarter."),
    "economic": ("What price moves first, and by how much?",
                 "The one that moves before the headline indicators do."),
}


def build_bank(risk: dict, expert: dict) -> list[dict]:
    """Questions built from this record: its own triggers, horizon, wording and history.

    A prompt that would read identically for any risk is not worth an expert's minute, so
    nothing here is generic: the triggers are named, the deadline is a date, the base rate
    is this band's own, and the sector question is the one this expert can answer.
    """
    themes = expert.get("theme_tags") or []
    triggers = trigger_order(risk, expert.get("id", ""))
    regions = [r for r in (risk.get("regions") or []) if r]
    by = deadline_text(risk)
    base = band_base_rate(risk)
    bank: list[dict] = []

    if len(triggers) >= 2:
        # Decomposition. One probability hides which link the expert doubts, and the
        # weakest link is the part an analyst can go and check.
        bank.append({
            "id": "weakest_link",
            "kind": "choice",
            "question": f"Several things must line up for this by {by}. Which is least likely?",
            "help": "The one you would bet against.",
            "options": [{"value": t.get("id") or t["title"], "label": t["title"]}
                        for t in triggers[:4]]
            + [{"value": "all_plausible", "label": "All are plausible", "dk": True}],
        })
        # Conditional. Two experts can agree on a number and disagree completely about
        # what drives it; this is where that shows.
        bank.append({
            "id": "conditional",
            "kind": "choice",
            "question": f'If "{triggers[0]["title"]}" happens, where does your estimate go?',
            "help": "Assume it happens within two months.",
            "options": [{"value": "much_higher", "label": "Much higher"},
                        {"value": "higher", "label": "Higher"},
                        {"value": "unchanged", "label": "Unchanged, already priced in"},
                        {"value": "lower", "label": "Lower"}],
        })

    if base:
        count, rate = base
        bank.append({
            "id": "base_rate_challenge",
            "kind": "text",
            "question": (f"Of {count} resolved risks ACAPS rated "
                         f"{risk.get('probability_acaps')}, {round(rate * 100)}% happened. "
                         "What makes this one different?"),
            "help": "If nothing does, say so. That is an answer.",
            "limit": TEXT_LIMIT,
        })

    # Pre-mortem: standing in a future where it already failed surfaces reasons that
    # "what could go wrong" does not.
    bank.append({
        "id": "premortem",
        "kind": "text",
        "question": f"It is {by} and this did not happen. What stopped it?",
        "help": "One line, written as though you already knew.",
        "limit": TEXT_LIMIT,
    })
    bank.append({
        "id": "surprise",
        "kind": "text",
        "question": f"What would genuinely surprise you by {by}?",
        "help": "Not the worst case. The thing you would not have predicted.",
        "limit": TEXT_LIMIT,
    })
    # An observable with a deadline can be checked; an opinion cannot.
    bank.append({
        "id": "observable_7d",
        "kind": "text",
        "question": "Name one thing checkable within seven days that would move your estimate.",
        "help": "Something an analyst could go and look at.",
        "limit": TEXT_LIMIT,
    })
    # A rise in recorded incidents is ambiguous between escalation and coverage, and
    # people on the ground are the only ones who can separate the two.
    bank.append({
        "id": "reporting_or_real",
        "kind": "choice",
        "question": "Recorded incidents here have risen. Escalation, or better reporting?",
        "options": [{"value": "escalation", "label": "Real escalation"},
                    {"value": "reporting", "label": "Mostly better reporting"},
                    {"value": "both", "label": "Both, about equally"},
                    {"value": "cannot_say", "label": "Cannot say", "dk": True}],
    })

    sector = next((SECTOR_QUESTIONS[t] for t in themes if t in SECTOR_QUESTIONS), None)
    if sector:
        question, help_text = sector
        bank.append({
            "id": "sector_specific",
            "kind": "choice" if regions else "text",
            "question": question,
            "help": help_text,
            **({"options": [{"value": r, "label": r} for r in regions[:4]]
                + [{"value": "cannot_say", "label": "Cannot say", "dk": True}]}
               if regions else {"limit": TEXT_LIMIT}),
        })

    rationale = _first_sentence(risk.get("rationale", ""))
    if rationale:
        bank.append({
            "id": "rationale_rebuttal",
            "kind": "choice",
            "question": "ACAPS writes this. Does it match what you see?",
            "help": rationale,
            "options": [{"value": "agree", "label": "Matches"},
                        {"value": "partly", "label": "Partly"},
                        {"value": "disagree", "label": "Does not match"}],
            "follow_up": {
                "when": ["partly", "disagree"],
                "id": "rationale_rebuttal_why",
                "kind": "text",
                "question": "What is wrong or missing in it?",
                "limit": TEXT_LIMIT,
            },
        })

    vulnerability = _first_sentence(risk.get("vulnerability", ""))
    if vulnerability:
        bank.append({
            "id": "vulnerability_check",
            "kind": "choice",
            "question": "Is this still true where you work, over the last 30 days?",
            "help": vulnerability,
            "options": [{"value": "still_true", "label": "Still true"},
                        {"value": "improved", "label": "Better than that now"},
                        {"value": "worse", "label": "Worse than that now"},
                        {"value": "cannot_say", "label": "Cannot say", "dk": True}],
        })

    bank.append({
        "id": "minority_why",
        "kind": "text",
        "question": "You expect to land apart from this panel. What do they not know?",
        "help": "The gap between your estimate and your guess at theirs is why this is asked.",
        "limit": TEXT_LIMIT,
    })
    return bank


# --- where a card's questions come from -----------------------------------------------
# Three sources, in order. A reviewed set wins because a person has read it. A live model
# call comes next, and only when LLM_BASE_URL is set. The deterministic bank is last and
# always available, so the card never depends on a network the venue may not have.

REVIEWED = Path(__file__).resolve().parents[2] / "data" / "generated-questions.json"


def _reviewed_for(risk_id: str, expert_id: str) -> list[dict]:
    """Questions written by a model and checked by a person, committed to the repo.

    Keyed by risk and expert, falling back to a set written for the expert's expertise so
    a new panel member is not dropped back to the generic bank.
    """
    try:
        store = json.loads(REVIEWED.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    sets = store.get("sets", {})
    return sets.get(f"{risk_id}:{expert_id}") or []


def bank_for(risk: dict, expert: dict, evidence: list[dict] | None = None) -> list[dict]:
    reviewed = _reviewed_for(risk.get("risk_id", ""), expert.get("id", ""))
    if reviewed:
        return reviewed
    try:
        from . import question_gen
        written = question_gen.generate(risk, expert, evidence)
        if written:
            return written
    except Exception:
        # A generator failure must never cost the expert their card.
        pass
    return build_bank(risk, expert)


def _rotate_options(probe: dict, seed: int) -> dict:
    """Rotate the substantive options and pin "cannot say" last.

    In a self-administered list the first option is picked more often than the others for no
    reason connected to its content. Rotating per expert turns that into noise spread across
    the panel rather than a bias pushing every card the same way. Don't-know stays at the
    bottom: it is a legitimate answer, not a first resort for anyone in a hurry.
    """
    options = probe.get("options") or []
    if len(options) < 3:
        return probe
    substantive = [o for o in options if not o.get("dk")]
    dk = [o for o in options if o.get("dk")]
    offset = seed % len(substantive)
    probe = {**probe, "options": substantive[offset:] + substantive[:offset] + dk}
    if probe.get("follow_up"):
        probe["follow_up"] = _rotate_options(probe["follow_up"], seed + 1)
    return probe


# --- the stepped flow ---------------------------------------------------------------
# Step 1 is the frozen core and is not described here. Steps 2 and 3 are chosen by rules
# over what this expert has already said on this card -- their own numbers and their own
# previous choice, never a peer's.
#
# The rules ship with the card and are evaluated on the device. A server round trip per
# step would mean partial answers leaving the phone before the Seal, which is exactly what
# sealing exists to prevent; it would also put venue wifi between a question and its answer.
# Declarative rules keep the branching auditable: the card can be replayed from the logged
# rule set and the expert's own inputs.

def flow_rules() -> list[dict]:
    """Ordered. First match wins; `otherwise` closes each step."""
    return [
        # Step 2 -- read from the core the expert has just given.
        {"step": 2, "when": {"gap_at_least": 0.25}, "probe": "minority_why",
         "why": "They expect to sit apart from the panel, which is the view worth hearing."},
        {"step": 2, "when": {"confidence_at_most": 2}, "probe": "what_would_move",
         "why": "Low confidence: what would change it is more useful than what it is."},
        {"step": 2, "when": {"probability_at_least": 0.75}, "probe": "evidence_seen",
         "why": "High conviction: ask what they are seeing that supports it."},
        {"step": 2, "when": {"probability_at_most": 0.25}, "probe": "holding_back",
         "why": "Low estimate with conviction: ask what is holding it back."},
        {"step": 2, "otherwise": True, "probe": "trigger_hinge"},

        # Step 3 -- read from the answer to step 2.
        {"step": 3, "after": "trigger_hinge", "when": {"answered": True},
         "probe": "watch_indicator",
         "why": "They named the hinge; ask what would show it starting."},
        {"step": 3, "after": "minority_why", "probe": "alternative_driver"},
        {"step": 3, "after": "what_would_move", "probe": "vulnerability_check"},
        {"step": 3, "after": "evidence_seen", "probe": "exposure_sanity"},
        {"step": 3, "after": "holding_back", "probe": "alternative_driver"},
        {"step": 3, "otherwise": True, "probe": "counterfactual"},
    ]


def select(risk: dict, expert: dict, slots: int = PROBE_SLOTS) -> list[dict]:
    """Pick this expert's probes.

    Spread by hash rather than by what the panel has already covered: reading the round would
    make one expert's card depend on another's answer, which is the channel sealing exists to
    remove. Across a panel the hash still spreads the bank; it just does so without anyone
    talking to anyone.
    """
    bank = bank_for(risk, expert)
    if not bank:
        return []
    seed = _digest(expert.get("id", ""), risk.get("risk_id", ""))
    chosen: list[dict] = []
    index = seed % len(bank)
    stride = 1 + (seed % (len(bank) - 1 or 1))
    guard = 0
    while len(chosen) < min(slots, len(bank)) and guard < len(bank) * 4:
        probe = bank[index % len(bank)]
        if probe["id"] not in {c["id"] for c in chosen}:
            chosen.append(probe)
        index += stride
        guard += 1
    # An open question answered after two closed ones inherits their options as a frame, so
    # it goes first when it is drawn at all.
    chosen.sort(key=lambda probe: 0 if probe["kind"] == "text" else 1)
    return [_rotate_options(probe, seed) for probe in chosen]


def card_flow(risk: dict, expert: dict, evidence: list[dict] | None = None) -> dict:
    """Everything the card needs to walk three steps without calling home.

    The bank is rotated per expert for option order; the rules decide which probe each step
    lands on, from this expert's own answers. Shipping both means the device can branch
    without sending a partial answer anywhere.
    """
    seed = _digest(expert.get("id", ""), risk.get("risk_id", ""))
    bank = [_rotate_options(probe, seed)
            for probe in bank_for(risk, expert, evidence)]
    return {
        "max_steps": 3,
        "bank": {probe["id"]: probe for probe in bank},
        "rules": flow_rules(),
        "note": "Steps 2 and 3 are chosen on your device from your own answers. "
                "Nothing is sent until you seal.",
    }


def accepted_ids(risk: dict, expert: dict) -> set[str]:
    """Every probe id this card could legitimately reach, follow-ups included."""
    ids: set[str] = set()
    for probe in bank_for(risk, expert):
        ids.add(probe["id"])
        if probe.get("follow_up"):
            ids.add(probe["follow_up"]["id"])
    return ids
