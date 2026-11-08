"""The thank-you message experts receive: what their minute changed, from the record only.

Built from facts the system holds, never from estimates:
- that the panel's input counted (how many answered, in words);
- what the analyst decided and what changed in the analysis (the decision log);
- who the update informed and by when (the "what decision, for whom, by when" field);
- the scale of what it concerns (the Risk List's own exposure figure, and the crisis's INFORM severity);
- reach, only when ACAPS supplies it (readers or organisations);
- a personal line, only when an analyst wrote one;
- on resolution, what happened and what the system learned.

What it never contains: a personal score, the expert's own answer beside the result, a ranking, or a
number about lives saved. A forecast cannot be shown to have saved anyone, and an expert would know
that; "ACAPS expects more than 500,000 people to be exposed" is ACAPS's own published figure,
"saved" would not be.
"""
from __future__ import annotations

import re

from . import acaps, alerts as alert_engine


def scale(risk: dict, alert_store) -> dict | None:
    """The scale of what the risk concerns, in ACAPS's own published words and numbers.

    Exposure is the Risk List's own "expected exposure" figure for this risk (for R1043, ">500,000").
    Severity is the linked crisis's INFORM rating and category for the latest cached month. ACAPS
    publishes "people in need" in INFORM as a 0-10 sub-score, not a headcount, so it is never
    printed as a number of people."""
    exposure = (risk.get("expected_exposure") or "").strip()
    exposure_count = None
    match = re.search(r"([<>~]?)\s*([\d.,]+)\s*(million|m\b|k\b)?", exposure, re.I)
    if match:
        number = float(match.group(2).replace(",", ""))
        unit = (match.group(3) or "").lower()
        number *= 1_000_000 if unit in ("million", "m") else 1_000 if unit == "k" else 1
        exposure_count = {"value": int(number), "qualifier": {">": "more than", "<": "fewer than",
                                                              "~": "about"}.get(match.group(1), ""),
                          "source": "ACAPS Risk List, expected exposure"}
    link = alert_store.links.get(risk.get("risk_id") or "") if alert_store is not None else None
    crisis_id = link["crisis_id"] if link else next(
        (x["crisis_id"] for x in alert_engine.suggest_links() if x["risk_id"] == risk.get("risk_id")), None)
    month = acaps.latest_month()
    severity = None
    if crisis_id and month:
        point = acaps.severity_point(crisis_id, month) or {}
        if point.get("index") is not None:
            severity = {"index": point.get("index"), "category": point.get("category"),
                        "crisis_name": (acaps.crisis(crisis_id) or {}).get("crisis_name"),
                        "month": month, "source": "ACAPS INFORM Severity Index"}
    if not exposure_count and not severity:
        return None
    return {"exposure": exposure_count, "severity": severity}


def _people(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + " million"
    return f"{n:,}"


def _decision_line(decision: str | None, rationale: str | None) -> str | None:
    if decision in ("accepted", "edited"):
        return ("ACAPS used the panel's input in its update"
                + (f": {rationale.rstrip('.')}." if rationale else "."))
    if decision == "rejected":
        return ("ACAPS weighed the panel's view and kept its own rating"
                + (f"; the reason is on the public record: {rationale}" if rationale else
                   "; the reason is on the public record."))
    return None


def message(*, n: int, n_text: str, risk: dict, entry: dict | None, size: dict | None,
            analyst_note: dict | None, reach: dict | None, decision_note: str | None = None) -> dict:
    honesty = (entry or {}).get("honesty") or {}
    use = honesty.get("decision_use") or {}
    decision = (entry or {}).get("decision")
    outcome = (entry or {}).get("outcome")
    lines: list[str] = []
    lines.append(f"Thank you. {n_text[:1].upper() + n_text[1:]}, and your answer was part of it.")
    changed = _decision_line(decision, honesty.get("analyst_rationale") or decision_note)
    if changed:
        lines.append(changed)
    if use.get("what_decision") and use.get("for_whom"):
        lines.append(f"The update informed {use['what_decision']} for {use['for_whom']}"
                     + (f", due {use['by_when']}." if use.get("by_when") else "."))
    exposure = (size or {}).get("exposure")
    severity = (size or {}).get("severity")
    if exposure:
        lines.append(f"ACAPS expects {exposure['qualifier'] + ' ' if exposure['qualifier'] else ''}"
                     f"{_people(exposure['value'])} people to be exposed to this risk (Risk List).")
    if severity:
        lines.append(f"It sits within {severity['crisis_name']}, which ACAPS rates "
                     f"{severity['category']} severity, {severity['index']} out of 10 "
                     f"(INFORM, {severity['month'][:3]} {severity['month'][3:]}).")
    if reach and reach.get("text"):
        lines.append(reach["text"])
    if outcome:
        lines.append("The risk materialised." if outcome == "materialised" else
                     "The risk did not materialise in the six months.")
        if honesty.get("misses"):
            lines.append("The panel and ACAPS both learned from this one: what was missed is now "
                         "part of what ACAPS monitors for this crisis.")
    if analyst_note and analyst_note.get("text"):
        lines.append(f"“{analyst_note['text']}” {analyst_note.get('by') or 'ACAPS'}")
    return {
        "headline": "What your minute changed",
        "lines": lines,
        "text": " ".join(lines),
        "facts": {
            "n": n,
            "decision": decision,
            "decision_use": use or None,
            "scale": size,
            "reach": reach,
            "outcome": outcome,
            "analyst_note": analyst_note,
            "update_link": next((s.get("url") for s in risk.get("sources") or [] if s.get("url")), None),
        },
        "never_contains": "a personal score, your answer beside the result, a ranking, or lives saved",
        "personal_view": ("Your own answer is not in this message. You can see it from your link "
                          "if you ask for it, and private calibration is available if you opt in."),
    }
