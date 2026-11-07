"""The Risk Alert Engine (MASTER_PROMPT section 6b). No model anywhere in it.

Diffs two monthly ACAPS editions, applies visible numeric rules, and *proposes* events. It never fires a
pulse: an analyst approves one, or dismisses it with a note. That boundary is the whole design -- an
engine that opened rounds by itself would be asking experts to answer a threshold, not a question.

Ranking is per direction. A month's biggest deterioration and its biggest improvement are both rank 1 of
their own kind, because an early-warning queue that ranked an improvement above a deterioration would put
the wrong row at the top. `rank_by_abs_delta` is also recorded, so the other ordering is never hidden.
"""
from __future__ import annotations
import functools
import uuid
from dataclasses import dataclass, field

from . import acaps, data
from .store import now

# The rules, in one table so the desk can show them and an analyst can argue with them.
RULES = {
    "index": 0.5,
    "human_impact": 1.0,
    "conditions": 1.0,
    "people_in_need": 1.0,
    "access": 1.0,
}

# Driver keywords -> the theme vocabulary the rest of the engine already speaks.
DRIVER_THEMES = {
    "displacement": ("displacement", "refugee", "returnee", "migration"),
    "conflict": ("conflict", "violence", "insecurity", "war"),
    "flood": ("flood", "cyclone", "storm", "rain"),
    "drought": ("drought", "food", "famine", "hunger"),
    "earthquake": ("earthquake", "seismic"),
    "epidemic": ("epidemic", "cholera", "disease", "outbreak"),
    "economic": ("economic", "inflation", "currency"),
}


@dataclass
class AlertStore:
    events: dict[str, dict] = field(default_factory=dict)
    links: dict[str, dict] = field(default_factory=dict)      # risk_id -> RiskCrisisLink
    seen: set[tuple] = field(default_factory=set)             # dedupe key per (crisis, months, metric)

    def reset(self) -> None:
        self.events.clear()
        self.links.clear()
        self.seen.clear()


def _themes_of(text: str) -> set[str]:
    lowered = text.lower()
    return {theme for theme, words in DRIVER_THEMES.items() if any(w in lowered for w in words)}


def _risk_themes(risk: dict) -> set[str]:
    blob = " ".join(
        [risk.get("title") or ""]
        + [f"{t.get('title', '')} {t.get('description', '')}" for t in risk.get("triggers") or []]
    )
    return _themes_of(blob)


@functools.lru_cache(maxsize=1)
def _default_suggestions() -> tuple:
    return tuple(_suggest(data.active_risks()))


def suggest_links(risks: list[dict] | None = None) -> list[dict]:
    """Cached for the default sweep over active risks, which runs once per alert event otherwise."""
    if risks is None:
        return [dict(s) for s in _default_suggestions()]
    return _suggest(risks)


def _suggest(risks: list[dict]) -> list[dict]:
    """Same iso3 plus a driver keyword match. A suggestion only: an analyst confirms it once, because
    linking the wrong crisis to a risk would put real numbers behind the wrong question."""
    registry = acaps.crises()
    out = []
    for risk in risks:
        iso = {code.strip().upper() for code in (risk.get("country_iso") or "").split(",") if code.strip()}
        wanted = _risk_themes(risk)
        for crisis in registry.values():
            if not iso & {c.upper() for c in crisis["iso3"]}:
                continue
            overlap = wanted & _themes_of(" ".join(crisis["drivers"]))
            if not overlap:
                continue
            out.append({
                "risk_id": risk["risk_id"],
                "crisis_id": crisis["crisis_id"],
                "crisis_name": crisis["crisis_name"],
                "how": "iso3+driver",
                "matched_on": sorted(overlap),
                "drivers": crisis["drivers"],
                "confirmed_by": None,
                "confirmed_at": None,
            })
    return out


def confirm_link(store: AlertStore, risk_id: str, crisis_id: str, who: str = "analyst") -> dict:
    link = {
        "risk_id": risk_id,
        "crisis_id": crisis_id,
        "how": "analyst",
        "confirmed_by": who,
        "confirmed_at": now(),
    }
    store.links[risk_id] = link
    return link


def risk_for_crisis(store: AlertStore, crisis_id: str) -> str | None:
    """A confirmed link wins; otherwise fall back to the suggestion, marked as unconfirmed by the caller."""
    for risk_id, link in store.links.items():
        if link["crisis_id"] == crisis_id:
            return risk_id
    for suggestion in suggest_links():
        if suggestion["crisis_id"] == crisis_id:
            return suggestion["risk_id"]
    return None


def _delta(before, after) -> float | None:
    try:
        return round(float(after) - float(before), 4)
    except (TypeError, ValueError):
        return None


def diff_months(month_from: str, month_to: str) -> list[dict]:
    """Every crisis present in BOTH editions, with the deltas that matter. A crisis that appears or
    disappears between editions is not a change in severity, so it is not diffed."""
    before = acaps.edition(acaps.INFORM, month_from)
    after = acaps.edition(acaps.INFORM, month_to)
    rows = []
    for crisis_id in sorted(set(before) & set(after)):
        old, new = before[crisis_id], after[crisis_id]
        entry = {"crisis_id": crisis_id, "month_from": month_from, "month_to": month_to}
        for name, api_field in acaps.SEVERITY_FIELDS.items():
            if name in ("category", "reliability", "last_updated"):
                entry[f"{name}_before"] = old.get(api_field)
                entry[f"{name}_after"] = new.get(api_field)
                continue
            entry[f"{name}_before"] = old.get(api_field)
            entry[f"{name}_after"] = new.get(api_field)
            entry[f"{name}_delta"] = _delta(old.get(api_field), new.get(api_field))
        access_before = acaps.access_score(crisis_id, month_from)
        access_after = acaps.access_score(crisis_id, month_to)
        entry["access_before"] = access_before
        entry["access_after"] = access_after
        entry["access_delta"] = _delta(access_before, access_after)
        rows.append(entry)
    return rows


def _rule_hit(row: dict) -> tuple[str, str, float] | None:
    """The first rule that fires, as (metric, sentence, delta). Index first: it is the headline number."""
    for metric in ("index", "human_impact", "conditions", "people_in_need", "access"):
        delta = row.get(f"{metric}_delta")
        if delta is None:
            continue
        threshold = RULES[metric]
        if abs(delta) >= threshold:
            direction = ">=" if delta > 0 else "<="
            sign = "" if delta > 0 else " (improvement)"
            return metric, f"{metric} delta {direction} {threshold if delta > 0 else -threshold}{sign}", delta
    if row.get("category_before") != row.get("category_after"):
        return (
            "category",
            f"category change {row.get('category_before')} -> {row.get('category_after')}",
            0.0,
        )
    return None


def run(store: AlertStore, month_from: str, month_to: str, record: bool = True) -> dict:
    """One pass of the engine. Idempotent: diffing the same two editions twice adds no duplicates."""
    rows = diff_months(month_from, month_to)
    hits = []
    for row in rows:
        hit = _rule_hit(row)
        if hit:
            metric, sentence, delta = hit
            hits.append((row, metric, sentence, delta))

    # Rank within direction, and record the absolute-delta rank alongside it so neither is hidden.
    # Rank within (metric, direction). Ranking across metrics would compare numbers that are not
    # comparable -- a 1.75 move in a sub-component is not "bigger" than a 0.8 move in the headline
    # index -- and an improvement ranked above a deterioration would put the wrong row at the top of
    # an early-warning queue.
    groups: dict[tuple[str, str], list] = {}
    for hit in hits:
        metric, delta = hit[1], hit[3]
        direction = "deterioration" if delta > 0 else "improvement" if delta < 0 else "category"
        groups.setdefault((metric, direction), []).append(hit)
    for key, group in groups.items():
        group.sort(key=lambda h: -abs(h[3]))

    # The absolute-delta rank within the same metric, so the other ordering is recorded, never hidden.
    abs_rank: dict[tuple[str, str], int] = {}
    by_metric: dict[str, list] = {}
    for hit in hits:
        by_metric.setdefault(hit[1], []).append(hit)
    for metric, group in by_metric.items():
        for position, hit in enumerate(sorted(group, key=lambda h: -abs(h[3])), start=1):
            abs_rank[(hit[0]["crisis_id"], metric)] = position

    events = []
    for key in sorted(groups, key=lambda k: (k[0] != "index", k[1] != "deterioration", k[0])):
        for position, (row, metric, sentence, delta) in enumerate(groups[key], start=1):
            crisis = acaps.crisis(row["crisis_id"]) or {}
            key = (row["crisis_id"], month_from, month_to, metric)
            if record and key in store.seen:
                existing = next(
                    (e for e in store.events.values()
                     if (e["crisis_id"], e["month_from"], e["month_to"], e["metric"]) == key),
                    None,
                )
                if existing:
                    events.append(existing)
                    continue
            risk_id = risk_for_crisis(store, row["crisis_id"])
            event = {
                "id": f"S-{len(store.events) + len(events) + 1:04d}",
                "crisis_id": row["crisis_id"],
                "crisis_name": crisis.get("crisis_name") or row["crisis_id"],
                "risk_id": risk_id,
                "risk_link_confirmed": bool(store.links.get(risk_id or "")),
                "month_from": month_from,
                "month_to": month_to,
                "metric": metric,
                "before": _round(row.get(f"{metric}_before")) if metric != "category"
                else row.get("category_before"),
                "after": _round(row.get(f"{metric}_after")) if metric != "category"
                else row.get("category_after"),
                "delta": round(delta, 2),
                "direction": "deterioration" if delta > 0 else "improvement" if delta < 0 else "category",
                "rank_this_month": position,
                "rank_by_abs_delta": abs_rank.get((row["crisis_id"], metric)),
                "n_crises_this_month": len(rows),
                "components": {
                    "human_impact": [_round(row.get("human_impact_before")), _round(row.get("human_impact_after"))],
                    "conditions": [_round(row.get("conditions_before")), _round(row.get("conditions_after"))],
                    "people_in_need": [_round(row.get("people_in_need_before")), _round(row.get("people_in_need_after"))],
                },
                "access": [row.get("access_before"), row.get("access_after")],
                "category": [row.get("category_before"), row.get("category_after")],
                "reliability": row.get("reliability_after"),
                "last_updated": row.get("last_updated_after"),
                "rule_hit": sentence,
                "adm1": crisis.get("adm1_name") or [],
                "connected_crises": crisis.get("connected_crises") or [],
                "pulse_id": None,
                "status": "proposed",
                "note": None,
                "detected_at": now(),
            }
            if record:
                store.events[event["id"]] = event
                store.seen.add(key)
            events.append(event)

    # The queue the analyst reads: headline index moves first, deteriorations before improvements.
    ranked = sorted(events, key=lambda e: (
        e["metric"] != "index",
        e["direction"] != "deterioration",
        e["rank_this_month"],
    ))
    return {
        "month_from": month_from,
        "month_to": month_to,
        "n_crises": len(rows),
        "events": ranked,
        "rules": RULES,
        "note": (
            "No crisis moved enough to trip a rule between these two editions."
            if not ranked else
            "Proposed only. An analyst approves an event before any pulse is created."
        ),
    }


def _round(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def latest_pair(dataset: str = acaps.INFORM, month_to: str | None = None) -> tuple[str | None, str | None]:
    month_to = month_to or acaps.latest_month(dataset)
    if not month_to:
        return None, None
    return acaps.previous_month(dataset, month_to), month_to


def new_store() -> AlertStore:
    return AlertStore()


def fresh_id() -> str:
    return f"S-{uuid.uuid4().hex[:6]}"
