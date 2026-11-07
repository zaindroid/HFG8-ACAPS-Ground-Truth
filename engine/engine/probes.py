"""The follow-up questions that come after the card's scored core.

Guarantees. The scored core never varies, so the group view aggregates one quantity and
the question contract stays frozen; probe answers reach themes and coverage and never the
published probability. A card is decided by the risk record and this expert's own answers,
so it is fixed when the link is issued and holds no channel through which a peer's view
could reach it. Every card carries at least one of the mitigations ACAPS names in its 2016
bias brief, whatever the expert answered.

Does not guarantee. That an expert reads the question as written, that routing by keyword
is the routing a person would choose, or that a generated question is a good one; a model
writes them analyst-side and a person can overrule the routing. Rotating option order
spreads primacy across a panel rather than removing it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROBE_SLOTS = 2        # the core plus two; the minute allows no more
TEXT_LIMIT = 240



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




# What a question is for, rather than which question it is. Rules target these, so a
# reviewed set written by a model routes exactly like the built-in bank.
DECOMPOSITION = "decomposition"
CONDITIONAL = "conditional"
PREMORTEM = "premortem"
BASE_RATE = "base_rate"
MINORITY = "minority"
OBSERVABLE = "observable"
PROVENANCE = "provenance"
CONTEXT = "context"

# The mitigations ACAPS's own bias brief names: devil's advocacy, an anchor to the record,
# and room for the informed minority. One of these is on every card.
DEBIASING = (PREMORTEM, BASE_RATE, MINORITY)


def role_of(probe: dict) -> str:
    return probe.get("role") or CONTEXT


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
            "role": DECOMPOSITION,
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
            "role": CONDITIONAL,
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
            "role": BASE_RATE,
            "kind": "text",
            # Deliberately does not name the band: round one hides ACAPS's rating, and a
            # question that quotes it hands back the anchor.
            "question": (f"Of {count} resolved risks in this probability band, "
                         f"{round(rate * 100)}% happened. What makes this one different?"),
            "help": "If nothing does, say so. That is an answer.",
            "limit": TEXT_LIMIT,
        })

    # Pre-mortem: standing in a future where it already failed surfaces reasons that
    # "what could go wrong" does not.
    bank.append({
        "id": "premortem",
            "role": PREMORTEM,
        "kind": "text",
        "question": f"It is {by} and this did not happen. What stopped it?",
        "help": "One line, written as though you already knew.",
        "limit": TEXT_LIMIT,
    })
    bank.append({
        "id": "surprise",
            "role": PREMORTEM,
        "kind": "text",
        "question": f"What would genuinely surprise you by {by}?",
        "help": "Not the worst case. The thing you would not have predicted.",
        "limit": TEXT_LIMIT,
    })
    # An observable with a deadline can be checked; an opinion cannot.
    bank.append({
        "id": "observable_7d",
            "role": OBSERVABLE,
        "kind": "text",
        "question": "Name one thing checkable within seven days that would move your estimate.",
        "help": "Something an analyst could go and look at.",
        "limit": TEXT_LIMIT,
    })
    # A rise in recorded incidents is ambiguous between escalation and coverage, and
    # people on the ground are the only ones who can separate the two.
    bank.append({
        "id": "reporting_or_real",
            "role": PROVENANCE,
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
            "role": CONTEXT,
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
            "role": CONTEXT,
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
            "role": CONTEXT,
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
            "role": MINORITY,
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
    """Ordered; the first match wins. Rules name a role, never a question.

    Routing on a literal id meant a reviewed set, whose ids are its own, matched nothing
    and the card silently skipped to submit. Roles are the contract between a rule and
    whatever bank is in play.

    Step 2 reads the core the expert has just given. Step 3 is always a debiasing role
    they have not already seen, so the mitigations ACAPS names do not depend on where the
    sliders happened to sit: at the defaults nobody would otherwise meet one.
    """
    return [
        {"step": 2, "when": {"gap_at_least": 0.25}, "role": MINORITY,
         "why": "They expect to sit apart from the panel, which is the view worth hearing."},
        {"step": 2, "when": {"confidence_at_most": 2}, "role": CONDITIONAL,
         "why": "Low confidence: what would change it is worth more than what it is."},
        {"step": 2, "when": {"probability_at_least": 0.75}, "role": DECOMPOSITION,
         "why": "High conviction: ask which link of their own chain is weakest."},
        {"step": 2, "when": {"probability_at_most": 0.25}, "role": DECOMPOSITION,
         "why": "Low estimate held firmly: the same question, from the other side."},
        {"step": 2, "otherwise": True, "role": DECOMPOSITION},
        {"step": 3, "roles": list(DEBIASING), "otherwise": True,
         "why": "Devil's advocacy, the record, or the minority view: every card gets one."},
    ]


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
        "debiasing_roles": list(DEBIASING),
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
