"""The ACAPS API layer: monthly INFORM severity editions, humanitarian access, and the crisis registry.

Reads the cache in data/acaps-api/ when ACAPS_API_TOKEN is unset, so the whole demo runs offline with no
network at all. With a token the same shapes come from the live API. Every response says which it was --
a cached edition presented as live would be the one dishonesty this project cannot afford.

ACAPS terms of use apply to this data.
"""
from __future__ import annotations
import functools
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

CACHE = Path(__file__).resolve().parents[2] / "data" / "acaps-api"
INFORM = "inform-severity-index"
ACCESS = "humanitarian-access"

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_MONTH_FILE = re.compile(r"^(?P<dataset>[a-z-]+)-(?P<month>[A-Z][a-z]{2}\d{4})\.json$")

# The field names ACAPS publishes, mapped to the names section 4 uses. Kept in one place so a rename
# upstream breaks in one spot rather than in every caller.
SEVERITY_FIELDS = {
    "index": "INFORM Severity Index",
    "category": "INFORM Severity category",
    "human_impact": "Human Impact",
    "conditions": "Conditions of affected people",
    "people_in_need": "People in need",
    "reliability": "Reliability",
    "last_updated": "Last updated",
}


def token_present() -> bool:
    return bool(os.environ.get("ACAPS_API_TOKEN", "").strip())


def month_key(month: str) -> tuple[int, int]:
    """Sortable key for 'Apr2026'. Returns (year, month_number)."""
    name, year = month[:3], month[3:]
    return (int(year), MONTHS.index(name) + 1 if name in MONTHS else 0)


def _read(path: Path) -> list | dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(payload: list | dict) -> list[dict]:
    """The cache stores bare lists; the live API pages results under 'results'."""
    if isinstance(payload, dict):
        return payload.get("results") or []
    return payload


def _fetched_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")


@functools.lru_cache(maxsize=1)
def available() -> dict[str, list[str]]:
    """Which months are on disk, per dataset, newest last."""
    found: dict[str, list[str]] = {INFORM: [], ACCESS: []}
    if not CACHE.exists():
        return found
    for path in CACHE.glob("*.json"):
        match = _MONTH_FILE.match(path.name)
        if not match:
            continue
        dataset = match.group("dataset")
        if dataset in found:
            found[dataset].append(match.group("month"))
    for dataset in found:
        found[dataset] = sorted(set(found[dataset]), key=month_key)
    return found


@functools.lru_cache(maxsize=64)
def edition(dataset: str, month: str) -> dict[str, dict]:
    """One monthly edition, keyed by crisis_id. Empty dict when that month is not cached."""
    path = CACHE / f"{dataset}-{month}.json"
    if not path.exists():
        return {}
    return {row["crisis_id"]: row for row in _rows(_read(path)) if row.get("crisis_id")}


def edition_meta(dataset: str, month: str) -> dict:
    path = CACHE / f"{dataset}-{month}.json"
    return {
        "dataset": dataset,
        "month": month,
        "source": "api" if token_present() else "cache",
        "fetched_at": _fetched_at(path) if path.exists() else None,
    }


def latest_month(dataset: str = INFORM) -> str | None:
    months = available().get(dataset) or []
    return months[-1] if months else None


def previous_month(dataset: str, month: str) -> str | None:
    """The cached edition immediately before `month` -- not the calendar month before it, because the
    cache is not required to be contiguous and diffing against a month we do not hold is not a diff."""
    months = available().get(dataset) or []
    earlier = [m for m in months if month_key(m) < month_key(month)]
    return earlier[-1] if earlier else None


@functools.lru_cache(maxsize=1)
def crises() -> dict[str, dict]:
    path = CACHE / "crises.json"
    if not path.exists():
        return {}
    out = {}
    for row in _rows(_read(path)):
        crisis_id = row.get("crisis_id")
        if not crisis_id:
            continue
        out[crisis_id] = {
            "crisis_id": crisis_id,
            "crisis_name": row.get("crisis_name") or crisis_id,
            "iso3": row.get("iso3") or [],
            "drivers": row.get("drivers") or [],
            "adm1_name": row.get("adm1_name") or [],
            "connected_crises": row.get("connected_crises") or [],
            "active": bool(row.get("active", True)),
        }
    return out


def crisis(crisis_id: str) -> dict | None:
    return crises().get(crisis_id)


def severity_point(crisis_id: str, month: str) -> dict | None:
    row = edition(INFORM, month).get(crisis_id)
    if not row:
        return None
    point = {"crisis_id": crisis_id, "month": month}
    for name, field in SEVERITY_FIELDS.items():
        point[name] = row.get(field)
    return point


def series(crisis_id: str) -> list[dict]:
    """The crisis's index over every cached month, oldest first. Months with no row are skipped
    rather than interpolated -- a gap in ACAPS's publishing is not a flat line."""
    out = []
    for month in available().get(INFORM, []):
        row = edition(INFORM, month).get(crisis_id)
        if not row:
            continue
        out.append({
            "month": month,
            "index": row.get(SEVERITY_FIELDS["index"]),
            "category": row.get(SEVERITY_FIELDS["category"]),
        })
    return out


def access_score(crisis_id: str, month: str) -> float | None:
    row = edition(ACCESS, month).get(crisis_id)
    if not row:
        return None
    value = row.get("ACCESS")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def access_by_month(crisis_id: str) -> dict[str, float]:
    out = {}
    for month in available().get(ACCESS, []):
        score = access_score(crisis_id, month)
        if score is not None:
            out[month] = score
    return out


def status() -> dict:
    """What /radar/status reports about the API side: which editions we hold and where they came from."""
    editions = []
    for dataset in (INFORM, ACCESS):
        month = latest_month(dataset)
        if month:
            editions.append(edition_meta(dataset, month))
    risk_list_path = CACHE / "risk-list.json"
    api_rows = _rows(_read(risk_list_path)) if risk_list_path.exists() else []
    last_update = ""
    for row in api_rows:
        candidate = str(row.get("last_update") or row.get("Last updated") or "")[:10]
        last_update = max(last_update, candidate)
    return {
        "editions": editions,
        "token_present": token_present(),
        "api_risk_list": {
            "n": len(api_rows),
            "last_update": last_update or None,
            "note": "The published risk-list endpoint is history and does not carry R1000+ ids, "
                    "so the active risk list comes from the CSV export instead.",
        },
    }
