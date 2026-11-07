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
import urllib.error
import urllib.request

from . import probes

TIMEOUT_SECONDS = 25
MAX_QUESTIONS = 6

SYSTEM = """You write the follow-up questions an ACAPS analyst puts to one humanitarian \
expert about one risk.

You are writing for someone who has worked in this context for years. Generic elicitation \
wastes their time: no "what are we missing", no "how confident are you", nothing that would \
read the same for a different risk in a different country. Every question must be answerable \
only by someone who knows this place, and must name something real from the record -- an \
actor, a town, a route, a date, a number.

Use the techniques that actually move a forecast:
- decomposition: which link in the chain is weakest
- conditionals: if X happens, where does the estimate go
- pre-mortem: it is the deadline and this did not happen; what stopped it
- discrimination: what would tell two competing explanations apart
- observables: one thing checkable within a week
- base-rate confrontation, where the record gives you one

Hard constraints:
- Never state or imply ACAPS's own probability band or risk level. The expert answers blind.
- No yes/no questions about a proposition: people agree when unsure, and the agreement rate \
then looks like a finding. Use forced choice between named alternatives.
- No double-barrelled questions, no negations in the stem, no leading wording.
- Every choice question offers a don't-know option, marked "dk": true.
- A free-text answer must fit in 240 characters, so ask for one line, not an essay.
- Ask about what the expert can observe, not about what they feel.

Return raw JSON and nothing else. No prose before or after, no code fences.
Shape: {"questions": [...]}, each question being
{"id": "snake_case", "kind": "choice"|"text", "question": "...", "help": "...",
 "options": [{"value": "...", "label": "...", "dk": true|false}]}
"choice" needs options; "text" needs no options and takes "limit": 240.
Return between 3 and 6 questions, ordered most to least informative."""


def enabled() -> bool:
    return bool(os.environ.get("LLM_BASE_URL", "").strip())


def _context(risk: dict, expert: dict, evidence: list[dict] | None) -> str:
    base = probes.band_base_rate(risk)
    record = {
        "risk": {
            "title": risk.get("title"),
            "country": risk.get("country"),
            "risk_type": risk.get("risk_type"),
            "deadline": probes.deadline_text(risk),
            "expected_exposure": risk.get("exposure"),
            "rationale": (risk.get("rationale") or "")[:1800],
            "vulnerability": (risk.get("vulnerability") or "")[:900],
            "triggers": [
                {"id": t.get("id"), "title": t.get("title"),
                 "description": (t.get("description") or "")[:300]}
                for t in (risk.get("triggers") or [])
            ],
        },
        # The record's own history, so the model can confront an estimate with it rather
        # than inventing a benchmark.
        "band_history": (
            {"n_resolved": base[0], "share_materialised": round(base[1], 3)} if base else None
        ),
        # What moved, in ACAPS's own monthly indices, which is what fired this pulse.
        "what_changed": (evidence or [])[:4],
        "expert": {
            "works_in": expert.get("region") or ", ".join(expert.get("geo_tags") or []),
            "expertise": expert.get("theme_tags"),
            "organisation_type": expert.get("affiliation_tag"),
            "years_experience": expert.get("years_experience"),
            "track_record": expert.get("track_record"),
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


def _clean(raw: dict) -> list[dict]:
    """Keep only well-formed questions, and strip anything that would leak the rating.

    A model that returns something unusable should cost the expert nothing: whatever fails
    validation is dropped, and if everything fails the caller falls back to the bank.
    """
    out: list[dict] = []
    for item in (raw or {}).get("questions", [])[:MAX_QUESTIONS]:
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
        out.append(probe)
    return out


def generate(risk: dict, expert: dict, evidence: list[dict] | None = None) -> list[dict]:
    """Questions for this expert on this risk, or an empty list to use the bank instead."""
    if not enabled():
        return []
    raw = _call(_context(risk, expert, evidence))
    return _clean(raw) if raw else []
