"""The cited draft update, built deterministically.

The deterministic template is the DEFAULT (section 9 of the master prompt). The agent loop stays behind
FF_AGENTS=false, so the demo never depends on a model being reachable. Every claim carries its evidence
reference; the Skeptic checks each claim's numbers against the aggregate it came from, and the Judge reports
coverage and number agreement. A claim whose numbers do not match the data it cites is flagged, not quietly fixed.
"""
from __future__ import annotations
import uuid

from . import data, store
from .store import now

# Which band to propose, given the panel's equal-weight mean. Boundaries are the midpoints between
# the band numbers in data.PROBABILITY_BANDS -- the same stated assumption, used in one direction only.
_BAND_EDGES = [(0.15, "Very Low"), (0.375, "Low"), (0.625, "Medium"), (0.85, "High")]


def band_for(probability: float) -> str:
    for edge, name in _BAND_EDGES:
        if probability < edge:
            return name
    return "Very High"


def level_for(band: str, impact: int | None) -> str:
    """ACAPS derives Risk Level from Probability x Impact. We mirror that rather than invent a level."""
    impact = impact or 3
    score = {"Very Low": 1, "Low": 2, "Medium": 3, "High": 4, "Very High": 5}[band] * impact
    if score >= 16:
        return "High"
    if score >= 8:
        return "Medium"
    return "Low"


def _number_in(value: float, haystack: list[float], tolerance: float = 0.011) -> bool:
    return any(abs(value - candidate) <= tolerance for candidate in haystack)


def build(risk: dict, pulse: dict, result: dict) -> dict:
    """Assemble claims from the aggregate and the pulse evidence, then check them."""
    mean = result.get("mean")
    n = result.get("n")
    proposed = band_for(mean) if mean is not None else (risk.get("probability_acaps") or "Medium")
    spread = result.get("spread") or {}
    claims: list[dict] = []

    if mean is not None:
        claims.append({
            "claim_id": "C1",
            "text": (f"The panel's equal-weight mean probability is {mean:.2f} (n={n}), "
                     f"against the current ACAPS rating of {risk.get('probability_acaps') or 'unrated'}."),
            "evidence_kind": "panel",
            "evidence_ref": f"{pulse['id']}:mean",
            "numbers": [mean, float(n)],
        })
        claims.append({
            "claim_id": "C2",
            "text": (f"Panel answers run from {spread.get('min', 0):.2f} to {spread.get('max', 0):.2f} "
                     f"(IQR {spread.get('iqr', 0):.2f}), so the group is "
                     f"{'tightly grouped' if (spread.get('iqr') or 0) <= 0.15 else 'genuinely split'}."),
            "evidence_kind": "panel",
            "evidence_ref": f"{pulse['id']}:spread",
            "numbers": [spread.get("min"), spread.get("max"), spread.get("iqr")],
        })

    for index, theme in enumerate(result.get("missing_themes") or [], start=1):
        if theme["count"] < 2:
            continue
        claims.append({
            "claim_id": f"M{index}",
            "text": f"{theme['count']} experts raise: {theme['theme']}",
            "evidence_kind": "panel",
            "evidence_ref": f"{pulse['id']}:missing_themes[{index - 1}]",
            "numbers": [float(theme["count"])],
        })

    for index, item in enumerate(pulse.get("evidence") or [], start=1):
        claims.append({
            "claim_id": f"E{index}",
            "text": _indicator_sentence(item),
            "evidence_kind": "indicator",
            "evidence_ref": item["indicator"],
            # A completion rate has no baseline, so only the numbers actually present are cited.
            "numbers": [float(x) for x in (item["value"], item.get("baseline")) if x is not None],
        })

    skeptic = _skeptic(claims, result, pulse)
    flagged = [s["claim_id"] for s in skeptic if s["verdict"] != "supported"]
    checked = [s for s in skeptic if s["checks"]]
    judge = {
        "coverage": round(len(checked) / len(claims), 4) if claims else 0.0,
        "numbers_match": round(1 - len(flagged) / len(claims), 4) if claims else 0.0,
        "overall": round((1 - len(flagged) / len(claims)) * 0.96, 4) if claims else 0.0,
        "flagged_claim_ids": flagged,
    }

    rationale = _rationale(risk, pulse, result, proposed, mean)
    return {
        "id": f"D-{uuid.uuid4().hex[:8]}",
        "risk_id": risk["risk_id"],
        "pulse_id": pulse["id"],
        "proposed_probability": proposed,
        "proposed_level": level_for(proposed, risk.get("impact_acaps")),
        "acaps_probability": risk.get("probability_acaps"),
        "acaps_level": risk.get("level"),
        "rationale_md": rationale,
        "claims": claims,
        "skeptic": skeptic,
        "missing_checks": [
            {"theme": theme["theme"], "status": theme["corroboration"]}
            for theme in (result.get("missing_themes") or [])
        ],
        "judge": judge,
        "repair_rounds": 0,
        "citations": _citations(risk, pulse),
        "status": "draft",
        "decided_by": None,
        "decided_at": None,
        "note": None,
        "generator": "deterministic-template",
        "generated_at": now(),
        "served_from": "live",
    }


def _indicator_sentence(item: dict) -> str:
    """Read an indicator back in words. A completion rate has no baseline and no z-score, so the
    sentence does not invent one -- writing "baseline of 0 (z=None)" would be noise dressed as rigour."""
    label = item.get("note") or item["indicator"]
    if str(item["indicator"]).startswith("trigger_completion"):
        return f"{item['source']} puts the trigger '{label}' at {item['value']}% complete."
    sentence = f"{item['source']} reports {label} at {item['value']}"
    if item.get("baseline") is not None and item.get("baseline") != 0:
        sentence += f" against a baseline of {item['baseline']}"
    if item.get("z") is not None:
        sentence += f" (z={item['z']})"
    return sentence + "."


def _skeptic(claims: list[dict], result: dict, pulse: dict) -> list[dict]:
    """Exact provenance. Judgement, observation and inference are kept apart, and an uncorroborated
    claim is marked uncorroborated -- which is not the same as false."""
    aggregate_numbers = [
        value for value in [
            result.get("mean"), result.get("weighted_mean"),
            float(result.get("n") or 0),
            (result.get("spread") or {}).get("min"),
            (result.get("spread") or {}).get("max"),
            (result.get("spread") or {}).get("iqr"),
        ] if value is not None
    ]
    aggregate_numbers += [float(t["count"]) for t in (result.get("missing_themes") or [])]
    indicator_numbers: list[float] = []
    for item in pulse.get("evidence") or []:
        indicator_numbers += [
            float(x) for x in (item.get("value"), item.get("baseline")) if x is not None
        ]

    out = []
    for claim in claims:
        checks: list[str] = []
        verdict = "supported"
        haystack = aggregate_numbers if claim["evidence_kind"] == "panel" else indicator_numbers

        if claim["evidence_kind"] == "panel":
            if (result.get("n") or 0) >= 5:
                checks.append("aggregate exists, n>=5")
            else:
                verdict = "not_supported"
                checks.append("aggregate below the disclosure floor of 5")

        numbers = [float(x) for x in claim["numbers"] if x is not None]
        if numbers and all(_number_in(x, haystack) for x in numbers):
            checks.append("numbers match cited value")
        elif numbers:
            verdict = "not_supported"
            checks.append("a cited number is absent from the evidence it points at")

        if claim["evidence_kind"] == "indicator":
            if any(item["indicator"] == claim["evidence_ref"] for item in pulse.get("evidence") or []):
                checks.append("evidence present on pulse")
            else:
                verdict = "not_supported"
                checks.append("no indicator on this pulse carries that reference")

        out.append({"claim_id": claim["claim_id"], "verdict": verdict, "checks": checks})
    return out


def _rationale(risk: dict, pulse: dict, result: dict, proposed: str, mean: float | None) -> str:
    acaps = risk.get("probability_acaps") or "unrated"
    lines = []
    if mean is not None:
        verb = "supports" if proposed == acaps else "argues against"
        lines.append(
            f"The panel's equal-weight mean is {mean:.2f} (n={result['n']}), which {verb} the current "
            f"{acaps} rating. Proposed: {proposed}."
        )
        spread = result.get("spread") or {}
        sentence = (
            f"Answers range {spread.get('min', 0):.2f}-{spread.get('max', 0):.2f} "
            f"(IQR {spread.get('iqr', 0):.2f})."
        )
        if result.get("weighted_mean") is not None:
            sentence += (
                f" The weighted mean is {result['weighted_mean']:.2f}, shown as a secondary number only."
            )
        lines.append(sentence)
    # The minority is kept in the draft as a direction and a subject, never as its own sentence:
    # the draft is published, and a quoted line from a panel of eight names its author to the
    # colleagues who sat on it. The sentences themselves stay in the verification queue.
    for item in (result.get("disagreement") or [])[:2]:
        lines.append(f"Disagreement, kept in: {item['summary']}")
    for theme in (result.get("missing_themes") or [])[:3]:
        lines.append(
            f"Raised by {theme['count']}: {theme['theme']} ({theme['corroboration']})."
        )
    for item in pulse.get("evidence") or []:
        lines.append(f"{_indicator_sentence(item)} ({item['url']})")
    for note in (result.get("integrity_notes") or [])[:2]:
        lines.append(f"Integrity note ({note['kind']}): {note['text']}")
    if (result.get("sp_experiment") or {}).get("answer"):
        sp = result["sp_experiment"]
        lines.append(
            f"Surprisingly-popular (experimental): {sp['answer']}. Actual share above 0.5 "
            f"{sp.get('actual_share_above_0_5')} against a predicted {sp.get('predicted_share')}."
        )
    lines.append(
        f"Probability band to number is an assumption of this build, not an ACAPS mapping: "
        f"{data.PROBABILITY_BANDS}."
    )
    return "\n\n".join(lines)


def _citations(risk: dict, pulse: dict) -> list[dict]:
    citations = [{"text": item["source"], "url": item["url"]} for item in pulse.get("evidence") or []]
    citations += (risk.get("sources") or [])[:4]
    seen, out = set(), []
    for citation in citations:
        if citation["url"] in seen:
            continue
        seen.add(citation["url"])
        out.append(citation)
    return out


def honesty_box(result: dict, draft: dict, decision: dict) -> dict:
    """The public honesty box. It must be able to say an uncomfortable thing: that the analyst rejected
    the panel, and why. Hit rate stays null until a resolved outcome exists -- never a flattering zero."""
    spread = result.get("spread") or {}
    claims_total = len(draft.get("claims") or [])
    supported = sum(1 for s in draft.get("skeptic") or [] if s["verdict"] == "supported")
    # The real queue length when the round produced one, and the draft's own count of unchecked
    # themes otherwise. Reporting the second when the first exists would understate it.
    queued = result.get("verification_queue_count")
    if queued is None:
        queued = sum(
            1 for theme in draft.get("missing_checks") or []
            if theme["status"] in ("not checked", "single-source", "uncorroborated")
        )
    gaps = [note["text"] for note in result.get("integrity_notes") or [] if note["kind"] == "coverage_gap"]
    rejected = decision.get("action") == "reject"
    return {
        "n": result.get("n"),
        "agreement": result.get("mean"),
        "spread": [spread.get("min"), spread.get("max")],
        "coverage_gaps": gaps,
        "claims_corroborated": supported,
        "claims_total": claims_total,
        "claims_in_verification_queue": queued,
        "panel_hit_rate": None,
        "misses": 0,
        "caveat": (
            "First round for this panel, so there is no track record to weigh it against. "
            "Experts are synthetic in this build. The band-to-number mapping is an assumption."
        ),
        "decision_use": {
            "what_decision": decision.get("what_decision"),
            "for_whom": decision.get("for_whom"),
            "by_when": decision.get("by_when"),
        },
        "panel_view_rejected": rejected,
        "analyst_rationale": decision.get("note") if rejected else None,
        # Share of this round's answers that someone else entered on the expert's behalf and the
        # expert then confirmed. A panel partly filled in by phone is a different thing from one
        # that answered on its own, and the public record says which it was.
        "relayed_share": result.get("relayed_share", 0.0),
        "corrections": result.get("corrections", 0),
        # The standing line, on every entry. It is the limit of what the mask protects, and it
        # belongs beside the group view rather than in a footnote nobody opens.
        "reidentification_note": store.REIDENTIFICATION_NOTE,
    }
