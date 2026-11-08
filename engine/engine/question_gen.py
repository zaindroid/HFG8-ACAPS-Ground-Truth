"""LLM-written questions for the expert card.

Why this runs where it does. The master prompt's fourth hard rule is that AI is
analyst-side only, and the card has to open on a bad connection, so the model does not run
on the expert's phone. It runs when the pulse is created: the analyst's side, with the
analyst able to read what it produced before a link goes out. The card then serves what was
generated for that expert, which also means a card can be replayed exactly and a bad
question can be traced to the prompt that produced it.

What the model is given: the risk's own record, how its probability band has actually
resolved, the severity move that triggered the pulse, the crises it connects to, and the
expert's own region, expertise and track record. What it must return: questions in the same
schema the deterministic bank uses, so everything downstream is unchanged.

Without LLM_BASE_URL the generator is simply absent and the deterministic bank answers. The
flag defaults off; the README states which path a demo ran.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from . import probes

TIMEOUT_SECONDS = 25
# Two, because two is all the card asks. The core plus two follow-ups is probes.PROBE_SLOTS,
# and generating six so that four are thrown away buys nothing: it spends tokens, widens the
# surface a bad question can come through, and makes the pool large enough that the two the
# rules happen to pick are not the two a person reviewed.
MAX_QUESTIONS = probes.PROBE_SLOTS

SYSTEM = """You write the follow-up questions an ACAPS analyst puts to one humanitarian \
expert about one risk.

Two things make a question worth asking, and both are required of both questions.

It has to be about this risk. Name something real from the record you are given -- an actor, a \
town, a route, a crossing, a season, the deadline. A question that would read the same for a \
different risk in a different country tells the analyst nothing.

It has to be about this expert. You are told where they work and what they work on. Ask what \
that person can answer from what they see: a protection specialist in one province and a \
logistician on a supply corridor should not receive the same question about the same risk. No \
generic elicitation -- no "what are we missing", no "how confident are you".

Use the techniques that actually move a forecast:
- decomposition: which link in the chain is weakest
- conditionals: if X happens, where does the estimate go
- pre-mortem: it is the deadline and this did not happen; what stopped it
- discrimination: what would tell two competing explanations apart
- observables: one thing checkable within a week
- base-rate confrontation, phrased as how comparable situations have gone before

These are your method, not your subject. The expert must never be told that a question is \
there to test an anchor, to check an overconfident estimate, to surface a minority view or to \
counter a bias, and no question may name a technique or describe what the analyst will do with \
the answer. A question that announces what it is measuring gets an answer the expert has \
managed. Ask it plainly, as a colleague would, and let it do its work unannounced. "help" \
clarifies the question itself -- a timeframe, an assumption to hold -- and never explains why \
the question is being put.

Ask about direction and sequence, not magnitude. "Will arrivals increase, stay about the \
same, or fall" is a question someone can answer and you can score later. "Will 50,000 more \
people arrive" is not: the threshold is invented, nobody tracks that exact figure, and an \
expert who thinks the direction is clear still cannot say whether it clears an arbitrary \
line. So: no invented counts, percentages, thresholds or money amounts anywhere in a stem or \
an option. A date already in the record is fine; a number you made up is not.

Hard constraints:
- Never state or imply ACAPS's own probability band or risk level, and never imply how often
risks like this one have resolved. The expert answers blind, and a hint at either is an anchor.
- No yes/no questions about a proposition: people agree when unsure, and the agreement rate \
then looks like a finding. Use forced choice between named alternatives.
- No double-barrelled questions, no negations in the stem, no leading wording.
- Every choice question offers a don't-know option, marked "dk": true.
- A free-text answer must fit in 240 characters, so ask for one line, not an essay.
- Ask about what the expert can observe, not about what they feel.

Return raw JSON and nothing else. No prose before or after, no code fences.
Shape: {"questions": [...]}, each question being
{"id": "snake_case", "kind": "choice"|"text", "role": "...", "question": "...", "help": "...",
 "options": [{"value": "...", "label": "...", "dk": true|false}]}
"choice" needs options; "text" needs no options and takes "limit": 240.

Return exactly two questions, because the card asks exactly two. The first is "decomposition" \
or "conditional". The second is "premortem", "base_rate" or "minority", so the card carries one \
of the debiasing techniques whatever the expert answered. Put the role in "role"."""


def enabled() -> bool:
    return bool(os.environ.get("LLM_BASE_URL", "").strip())


def _moved(evidence: list[dict] | None) -> list[str]:
    """What moved, named and given a direction, with the values left out.

    The pulse fires on ACAPS's own monthly indices, and the model used to be handed those rows
    whole: before, after, delta, this month's deterioration rank, the source URL. Two things go
    wrong with that. The figures are internal -- the expert answers without seeing ACAPS's
    reading of the situation, and a question that quotes an index move hands it to them. And a
    model given numbers writes questions about numbers, which is where a threshold nobody
    tracks comes from. Which indicator moved, and which way, is all the model needs in order to
    write about the right thing.
    """
    out: list[str] = []
    for item in (evidence or [])[:4]:
        metric = str(item.get("metric") or item.get("dataset") or "").replace("_", " ").strip()
        if not metric:
            continue
        before, after = item.get("before"), item.get("after")
        way = ""
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            way = " rose" if after > before else " fell" if after < before else " held steady"
        out.append(f"{metric}{way}")
    return out


def _context(risk: dict, expert: dict, evidence: list[dict] | None) -> str:
    """What the model is allowed to see.

    Everything here is either in the published risk record or is the expert's own profile, and
    everything internal is left out: ACAPS's probability band and risk level, how often that
    band has resolved, the expected exposure figure, the index values that fired the pulse, and
    the expert's own calibration. None of it makes a question better, each of it ends up inside
    one sooner or later, and a question is read by the person we are keeping it from.
    """
    record = {
        "risk": {
            "title": probes._scrub_rating(risk.get("title") or ""),
            "country": risk.get("country"),
            "risk_type": risk.get("risk_type"),
            "deadline": probes.deadline_text(risk),
            # Scrubbed, because the rationale is prose written by an analyst who knew the band
            # and sometimes says so, and whatever is quoted into a question reaches the expert.
            "rationale": probes._scrub_rating(risk.get("rationale") or "")[:1800],
            "vulnerability": probes._scrub_rating(risk.get("vulnerability") or "")[:900],
            "triggers": [
                {"id": t.get("id"),
                 "title": probes._scrub_rating(t.get("title") or ""),
                 "description": probes._scrub_rating(t.get("description") or "")[:300]}
                for t in (risk.get("triggers") or [])
            ],
        },
        "what_changed": _moved(evidence),
        # Enough to pitch a question at the right person, and nothing about how they have
        # scored before. Calibration is private to the expert and is not an input to a question.
        "expert": {
            "works_in": expert.get("region") or ", ".join(expert.get("geo_tags") or []),
            "expertise": expert.get("theme_tags"),
            "organisation_type": expert.get("affiliation_tag"),
        },
    }
    return json.dumps(record, ensure_ascii=False, indent=1)


def _call(prompt: str) -> dict | None:
    base = os.environ.get("LLM_BASE_URL", "").strip().rstrip("/")
    key = os.environ.get("LLM_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free").strip()
    body = json.dumps({
        "model": model,
        "temperature": 0.4,
        "max_tokens": 1600,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    # OpenRouter asks callers to identify themselves; harmless on other providers.
    if "openrouter" in base:
        headers["HTTP-Referer"] = os.environ.get(
            "LLM_REFERER", "https://github.com/zaindroid/HFG8-ACAPS-Ground-Truth")
        headers["X-Title"] = "Sealed Signals"
    request = urllib.request.Request(f"{base}/chat/completions", data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
    if "```" in text:
        parts = text.split("```")
        text = max(parts, key=len).removeprefix("json").removeprefix("JSON")
    for opener, closer in (("{", "}"), ("[", "]")):
        if opener not in text:
            continue
        try:
            parsed = json.loads(text[text.index(opener):text.rindex(closer) + 1])
        except ValueError:
            continue
        return {"questions": parsed} if isinstance(parsed, list) else parsed
    return None


ROLES = (probes.DECOMPOSITION, probes.CONDITIONAL, probes.PREMORTEM, probes.BASE_RATE,
         probes.MINORITY, probes.OBSERVABLE, probes.PROVENANCE, probes.CONTEXT)
# A count, a percentage or a sum of money the model decided on by itself. The instruction says
# not to, and an instruction is not a guarantee, so a question carrying one is dropped. A year
# is allowed, because the deadline is a date from the record and the question has to name it.
_INVENTED_NUMBER = re.compile(
    r"(?<![\d.])(?:\d{1,3}(?:[ ,.]\d{3})+|\d{3,})(?![\d.])|\d+(?:\.\d+)?\s?%|[$€£]\s?\d")


def _invents_a_number(probe: dict) -> bool:
    text = " ".join(
        [probe.get("question", ""), probe.get("help", "")]
        + [option.get("label", "") for option in probe.get("options") or []]
    )
    return any(
        not (len(match.group(0)) == 4 and match.group(0).isdigit()
             and 1900 <= int(match.group(0)) <= 2100)
        for match in _INVENTED_NUMBER.finditer(text)
    )


def _clean(raw: dict) -> list[dict]:
    """Keep only well-formed questions, and strip anything that would leak the rating.

    A model that returns something unusable should cost the expert nothing: whatever fails
    validation is dropped, and if everything fails the caller falls back to the bank.
    """
    out: list[dict] = []
    for item in (raw or {}).get("questions", []):
        if len(out) >= MAX_QUESTIONS:
            break
        if not isinstance(item, dict):
            continue
        kind, question = item.get("kind"), item.get("question")
        if kind not in ("choice", "text") or not isinstance(question, str) or len(question) < 12:
            continue
        probe = {
            "id": str(item.get("id") or f"llm_{len(out) + 1}")[:48],
            "kind": kind,
            "question": probes._scrub_rating(question)[:240],
            "generated": True,
        }
        # Roles are what the card's rules route on. Without one every generated question reads
        # as "context", no rule matches it, and the card quietly asks the built-in bank instead.
        if item.get("role") in ROLES:
            probe["role"] = item["role"]
        if item.get("help"):
            probe["help"] = probes._scrub_rating(str(item["help"]))[:240]
        if kind == "text":
            probe["limit"] = probes.TEXT_LIMIT
        else:
            options = [
                {"value": str(o.get("value") or o.get("label"))[:64],
                 "label": str(o.get("label"))[:80],
                 **({"dk": True} if o.get("dk") else {})}
                for o in item.get("options") or []
                if isinstance(o, dict) and o.get("label")
            ]
            if len(options) < 2:
                continue
            # The instruction asks for one; add it rather than force a guess if it is missing.
            if not any(o.get("dk") for o in options):
                options.append({"value": "cannot_say", "label": "Cannot say", "dk": True})
            probe["options"] = options[:6]
        if _invents_a_number(probe):
            continue
        out.append(probe)
    return out


def generate(risk: dict, expert: dict, evidence: list[dict] | None = None) -> list[dict]:
    """Questions for this expert on this risk, or an empty list to use the bank instead."""
    if not enabled():
        return []
    raw = _call(_context(risk, expert, evidence))
    return _clean(raw) if raw else []
