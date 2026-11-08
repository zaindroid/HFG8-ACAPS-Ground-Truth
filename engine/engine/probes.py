"""The probe flow the expert card walks after the scored question (Lane B's three-step card).

What this is. Step 1 of the card is frozen and identical for everyone: stance, likelihood, panel
share, confidence. It is the only thing the group view aggregates and the only thing an outcome
scores. Steps 2 and 3 are chosen from what this expert has already said on this card, and they
collect prose: themes, coverage, what they would watch. Probe answers never touch the probability.

Why the rules travel with the card instead of the server deciding each step. A round trip per
step would send partial answers before the commitment, which is what committing exists to
prevent, and would put venue wifi between a question and its answer. Nothing a peer could set is
readable in the flow, so the card cannot herd even by accident: every condition reads the
expert's own four numbers.

Why this is not hidden measurement (section 6d, v3.4). Every probe is a question the expert reads
and answers knowingly; nothing is timed, nothing counts edits, and no fictitious reference is
planted. The branching changes which question is asked, not what is computed about the person --
and what is computed about a person is nothing, outside the consent-gated calibration programme.

The content is ACAPS's own. The help lines quote the export's Rationale, Current vulnerability
and Expected exposure columns for this risk, because a question like "is this still true where
you work?" has to quote something ACAPS actually wrote; asking about our own paraphrase would
collect an opinion about our summary.
"""
from __future__ import annotations
import hashlib

MAX_STEPS = 3
TEXT_LIMIT = 240
RECALL_WINDOW_DAYS = 30
NOTE = ("Steps 2 and 3 are chosen on your device from your own answers. Nothing is sent until "
        "you confirm.")
AGGREGATION_NOTE = "These follow the scored question and are never aggregated into it."
# Where each probe's answer goes once it is in. Returned with the flow so the card can say it and
# the desk can show it: a question whose destination is unstated is a question with a hidden use.
DESTINATION = {
    "trigger_hinge": "the analyst's trigger list",
    "trigger_hinge_other": "the analyst's trigger list",
    "trigger_rank": "the analyst's trigger list",
    "minority_why": "the verification queue",
    "what_would_move": "the missing-evidence column",
    "evidence_seen": "the verification queue",
    "holding_back": "the verification queue",
    "watch_indicator": "the analyst's indicator watchlist",
    "counterfactual": "the missing-evidence column",
    "alternative_driver": "the coverage note",
    "rationale_rebuttal": "the coverage note",
    "rationale_rebuttal_why": "the verification queue",
    "vulnerability_check": "the coverage note",
    "exposure_sanity": "the coverage note",
}
SECTORS = ("Food security", "Health", "WASH", "Shelter", "Displacement", "Nutrition",
           "Protection", "Livelihoods")


def _first_sentence(text: str | None, limit: int = 220) -> str | None:
    if not text:
        return None
    cleaned = " ".join(str(text).split())
    cut = cleaned.find(". ")
    sentence = cleaned[:cut + 1] if cut != -1 else cleaned
    return sentence if len(sentence) <= limit else sentence[:limit].rstrip() + "..."


def _rotate(options: list[dict], seed: str) -> list[dict]:
    """Rotate the option order per expert, against primacy.

    Deterministic from the expert id, so the same person sees the same order on a reload -- an
    order that reshuffles mid-answer is a different question each time it is read. Any option
    marked `dk` is pinned last whatever the rotation does: 'cannot say' belongs at the end, set
    apart, so it is not picked by position."""
    plain = [o for o in options if not o.get("dk")]
    unsure = [o for o in options if o.get("dk")]
    if plain:
        offset = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(plain)
        plain = plain[offset:] + plain[:offset]
    return plain + unsure


def _trigger_options(risk: dict) -> list[dict]:
    return [{"value": trigger["id"], "label": trigger["title"]}
            for trigger in (risk.get("triggers") or [])[:4]]


def build(risk: dict, seed: str = "") -> dict | None:
    """The ProbeFlow for one risk and one expert. None when the risk has nothing to probe with."""
    triggers = _trigger_options(risk)
    rationale = _first_sentence(risk.get("rationale"))
    vulnerability = _first_sentence(risk.get("vulnerability"))
    exposure = (risk.get("expected_exposure") or "").strip()
    needs = [need for need in (risk.get("priority_needs") or []) if need]
    sectors = needs + [s for s in SECTORS if s not in needs]

    bank: dict[str, dict] = {
        "minority_why": {
            "id": "minority_why", "kind": "text", "limit": TEXT_LIMIT,
            "question": ("You expect to land apart from this panel. What do you know that they "
                         "may not?"),
            "help": ("The gap between your own estimate and your guess at theirs is the reason "
                     "this is being asked."),
        },
        "what_would_move": {
            "id": "what_would_move", "kind": "text", "limit": TEXT_LIMIT,
            "question": "What would move you, either way?",
            "help": "One thing you would need to see.",
        },
        "evidence_seen": {
            "id": "evidence_seen", "kind": "text", "limit": TEXT_LIMIT,
            "question": "What are you seeing that supports that?",
            "help": (f"In the last {RECALL_WINDOW_DAYS} days, and only what you would stand "
                     "behind."),
        },
        "holding_back": {
            "id": "holding_back", "kind": "text", "limit": TEXT_LIMIT,
            "question": "What is holding this back?",
            "help": "The reason it has not happened already.",
        },
        "watch_indicator": {
            "id": "watch_indicator", "kind": "text", "limit": TEXT_LIMIT,
            "question": "What would you watch to know it had started?",
            "help": "One observable thing, as early as you can make it.",
        },
        "counterfactual": {
            "id": "counterfactual", "kind": "text", "limit": TEXT_LIMIT,
            "question": "What would have to be true for this not to happen?",
            "help": "The strongest reason it does not, in one line.",
        },
    }

    if triggers:
        # A forced choice between named triggers, not "is T1 the hinge? yes/no": a yes/no
        # question collects agreement from everyone who is unsure, which is the acquiescence
        # effect and not a finding about triggers.
        bank["trigger_hinge"] = {
            "id": "trigger_hinge", "kind": "choice",
            "question": "Which of these matters most for what happens next?",
            "options": _rotate(triggers + [{"value": "something_else",
                                            "label": "Something not listed", "dk": True}], seed),
            "follow_up": {"when": "something_else", "id": "trigger_hinge_other", "kind": "text",
                          "question": "What is it?", "limit": TEXT_LIMIT},
        }
        bank["trigger_rank"] = {
            "id": "trigger_rank", "kind": "rank",
            "question": "Which of these would move the situation most?",
            "help": "Order them. The one you put first is the one you would watch.",
            "options": _rotate(triggers, seed),
        }

    bank["alternative_driver"] = {
        "id": "alternative_driver", "kind": "choice",
        "question": "What is driving this most, as you see it?",
        "help": (f"ACAPS frames it as: {_first_sentence(risk.get('title'), 130)}"
                 if risk.get("title") else None),
        "options": _rotate([{"value": sector, "label": sector} for sector in sectors[:6]]
                           + [{"value": "as_titled", "label": "As framed above"},
                              {"value": "cannot_say", "label": "Cannot say", "dk": True}], seed),
    }

    if rationale:
        bank["rationale_rebuttal"] = {
            "id": "rationale_rebuttal", "kind": "choice",
            "question": "ACAPS writes this. Does it match what you see?",
            "help": rationale,
            # No neutral middle and no agree-first order: "matches / partly / does not match" with
            # agreement at the top is a question that rewards the quickest tap.
            "options": _rotate([{"value": "agree", "label": "Matches"},
                                {"value": "partly", "label": "Partly"},
                                {"value": "disagree", "label": "Does not match"}], seed),
            "follow_up": {"when": ["partly", "disagree"], "id": "rationale_rebuttal_why",
                          "kind": "text", "question": "What is wrong or missing in it?",
                          "limit": TEXT_LIMIT},
        }

    if vulnerability:
        bank["vulnerability_check"] = {
            "id": "vulnerability_check", "kind": "choice",
            "question": (f"Is this still true where you work, over the last "
                         f"{RECALL_WINDOW_DAYS} days?"),
            "help": vulnerability,
            "options": _rotate([{"value": "still_true", "label": "Still true"},
                                {"value": "worse", "label": "Worse than that now"},
                                {"value": "improved", "label": "Better than that now"},
                                {"value": "cannot_say", "label": "Cannot say", "dk": True}], seed),
        }

    if exposure:
        bank["exposure_sanity"] = {
            "id": "exposure_sanity", "kind": "choice",
            "question": "How many people would you expect this to reach?",
            # ACAPS's own figure comes after the answer, never before it. Showing it first turns
            # the question into a test of whether they will agree with us.
            "help": "Answer before ACAPS's own figure is shown.",
            "reveal_after": f"ACAPS expects {exposure}.",
            "options": [{"value": "<20,000", "label": "<20,000"},
                        {"value": "20,000-100,000", "label": "20,000-100,000"},
                        {"value": "100,000-250,000", "label": "100,000-250,000"},
                        {"value": "250,000-500,000", "label": "250,000-500,000"},
                        {"value": ">500,000", "label": ">500,000"},
                        {"value": "cannot_say", "label": "Cannot say", "dk": True}],
        }

    rules = [
        {"step": 2, "when": {"gap_at_least": 0.25}, "probe": "minority_why",
         "why": "They expect to sit apart from the panel, which is the view worth hearing."},
        {"step": 2, "when": {"confidence_at_most": 2}, "probe": "what_would_move",
         "why": "Low confidence: what would change it is more useful than what it is."},
        {"step": 2, "when": {"probability_at_least": 0.75}, "probe": "evidence_seen",
         "why": "High conviction: ask what they are seeing that supports it."},
        {"step": 2, "when": {"probability_at_most": 0.25}, "probe": "holding_back",
         "why": "Low estimate with conviction: ask what is holding it back."},
        {"step": 2, "otherwise": True,
         "probe": "trigger_hinge" if triggers else "counterfactual"},
        {"step": 3, "after": "trigger_hinge", "when": {"answered": True},
         "probe": "watch_indicator",
         "why": "They named the hinge; ask what would show it starting."},
        {"step": 3, "after": "minority_why", "probe": "alternative_driver"},
        {"step": 3, "after": "what_would_move",
         "probe": "vulnerability_check" if vulnerability else "counterfactual"},
        {"step": 3, "after": "evidence_seen",
         "probe": "exposure_sanity" if exposure else "counterfactual"},
        {"step": 3, "after": "holding_back", "probe": "alternative_driver"},
        {"step": 3, "otherwise": True, "probe": "counterfactual"},
    ]
    # An open question before the closed ones that follow it, so their option lists cannot frame
    # the open answer; and never a rule pointing at a probe this risk did not produce.
    rules = [rule for rule in rules if rule["probe"] in bank]
    if not rules:
        return None
    return {
        "max_steps": MAX_STEPS,
        "bank": {key: {k: v for k, v in probe.items() if v is not None}
                 for key, probe in bank.items()},
        "rules": rules,
        "note": NOTE,
        "destinations": {key: DESTINATION[key] for key in DESTINATION if key in bank
                         or key.endswith("_other") or key.endswith("_why")},
    }


def themes_from(probe_answers: dict | None) -> list[str]:
    """The free-text probe answers, as lines for the missing-evidence and verification columns.

    Choice answers are not in here: 'still_true' is a datum about coverage, not a sentence
    somebody wrote, and running it through the text clustering would invent a theme out of a
    radio button."""
    if not probe_answers:
        return []
    out = []
    for key, value in probe_answers.items():
        if not isinstance(value, str):
            continue
        text = value.strip()
        if text and key in DESTINATION and DESTINATION[key] in (
                "the verification queue", "the missing-evidence column"):
            out.append(text[:TEXT_LIMIT])
    return out
