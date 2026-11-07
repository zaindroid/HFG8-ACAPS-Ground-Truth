"""Fetch the live ACAPS Risk List into a CSV, and derive the aggregates the UI charts read.

The API returns more than the hackathon CSV export: date_entered, last_risk_update, crisis_id
and geographic_level, plus 199 resolved outcomes instead of 104. Both outputs are written from
one fetch so the chart numbers and the CSV can never disagree.

Usage:
    ACAPS_TOKEN=<token> python scripts/fetch_acaps_risk_list.py

Outputs:
    data/acaps-risk-list.csv        one row per risk, lists flattened to "a; b"
    ui/src/data/risk-insights.json  aggregates for the Risk Radar charts
"""

from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.acaps.org/api/v1/risk-list/"
ROOT = Path(__file__).resolve().parents[1]
CSV_OUT = ROOT / "data" / "acaps-risk-list.csv"
JSON_OUT = ROOT / "ui" / "src" / "data" / "risk-insights.json"

FIELDS = [
    "risk_id", "risk_title", "country", "iso3", "crisis_id", "geographic_level",
    "risk_type", "date_entered", "last_risk_update", "published", "publication_link",
    "probability", "impact", "intensity", "risk_level", "status", "exposure",
    "trigger", "vulnerability", "rationale",
]
PROBABILITIES = ["Very Low", "Low", "Medium", "High", "Very High"]
LEVELS = ["Low", "Medium", "High"]
# The band midpoints ACAPS's five-point scale implies, used as the calibration reference.
BAND_MIDPOINT = {"Very Low": 0.1, "Low": 0.3, "Medium": 0.5, "High": 0.7, "Very High": 0.9}
RESOLVED = ("Materialised", "Not materialised")


def fetch(token: str) -> list[dict]:
    rows: list[dict] = []
    url: str | None = API
    while url:
        request = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            sys.exit(f"ACAPS API returned {error.code} for {url}. Check ACAPS_TOKEN.")
        except urllib.error.URLError as error:
            sys.exit(f"Cannot reach the ACAPS API: {error.reason}")
        rows += payload.get("results", [])
        url = payload.get("next")
        print(f"  fetched {len(rows)} of {payload.get('count', '?')}")
    return rows


def flatten(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value).replace("\r\n", "\n")


def write_csv(rows: list[dict]) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: flatten(row.get(field)) for field in FIELDS})
    print(f"  wrote {CSV_OUT.relative_to(ROOT)} ({len(rows)} rows)")


def read_csv() -> list[dict]:
    with CSV_OUT.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def outcomes(rows: list[dict], field: str, order: list[str]):
    """Count resolved risks and materialisations per value of `field`, in `order`."""
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        key = (row.get(field) or "").strip()
        if key and row.get("status") in RESOLVED:
            tally[key][0] += 1
            tally[key][1] += row["status"] == "Materialised"
    return [
        {"label": key, "n": tally[key][0], "materialised": tally[key][1],
         "rate": round(tally[key][1] / tally[key][0], 4)}
        for key in order if tally[key][0]
    ]


def build_insights(rows: list[dict]) -> dict:
    resolved = [r for r in rows if r.get("status") in RESOLVED]
    calibration = outcomes(rows, "probability", PROBABILITIES)
    for band in calibration:
        band["expected"] = BAND_MIDPOINT[band["label"]]

    matrix = []
    for probability in PROBABILITIES:
        for impact in "12345":
            cell = [r for r in resolved
                    if (r.get("probability") or "").strip() == probability
                    and (r.get("impact") or "").strip() == impact]
            materialised = sum(1 for r in cell if r["status"] == "Materialised")
            matrix.append({
                "probability": probability,
                "impact": int(impact),
                "n": len(cell),
                "materialised": materialised,
                "rate": round(materialised / len(cell), 4) if cell else None,
            })

    cohorts = []
    years: Counter = Counter(r["date_entered"][:4] for r in rows if r.get("date_entered"))
    for year in sorted(years):
        cohort = [r for r in rows if (r.get("date_entered") or "").startswith(year)]
        done = [r for r in cohort if r.get("status") in RESOLVED]
        cohorts.append({
            "year": year,
            "entered": len(cohort),
            "materialised": sum(1 for r in done if r["status"] == "Materialised"),
            "not_materialised": sum(1 for r in done if r["status"] == "Not materialised"),
            "active": sum(1 for r in cohort if r.get("status") == "Active"),
        })

    crises: Counter = Counter()
    for row in rows:
        for crisis in filter(None, (row.get("crisis_id") or "").split("; ")):
            crises[crisis] += 1

    # Per-crisis history, so an alert on a crisis can show what the Risk List has
    # already recorded against it. Keyed by crisis_id, which the alert feed carries.
    by_crisis = {}
    for crisis in crises:
        linked = [r for r in rows
                  if crisis in (r.get("crisis_id") or "").split("; ")]
        done = [r for r in linked if r.get("status") in RESOLVED]
        by_crisis[crisis] = {
            "risks": len(linked),
            "resolved": len(done),
            "materialised": sum(1 for r in done if r["status"] == "Materialised"),
            "active": sum(1 for r in linked if r.get("status") == "Active"),
            "examples": [
                {"risk_id": r["risk_id"], "title": r["risk_title"],
                 "level": r.get("risk_level", ""), "status": r["status"],
                 "entered": r.get("date_entered", "")[:10]}
                for r in sorted(done, key=lambda r: r.get("date_entered", ""), reverse=True)[:3]
            ],
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "ACAPS API v1 risk-list",
        "totals": {
            "risks": len(rows),
            "resolved": len(resolved),
            "active": sum(1 for r in rows if r.get("status") == "Active"),
            "materialised": sum(1 for r in resolved if r["status"] == "Materialised"),
            "countries": len({c for r in rows
                              for c in filter(None, (r.get("country") or "").split("; "))}),
            "crises": len(crises),
        },
        "calibration": calibration,
        "by_level": outcomes(rows, "risk_level", LEVELS),
        "matrix": matrix,
        "cohorts": cohorts,
        "by_crisis": by_crisis,
    }


def main() -> None:
    token = os.environ.get("ACAPS_TOKEN", "").strip()
    if not token:
        sys.exit("Set ACAPS_TOKEN to your ACAPS API token (api.acaps.org, free account).")
    print("Fetching the ACAPS Risk List...")
    write_csv(fetch(token))
    # Derive the chart aggregates from the CSV that was just written, not from the API
    # response, so the charts always describe exactly what the committed CSV contains.
    insights = build_insights(read_csv())
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(insights, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {JSON_OUT.relative_to(ROOT)}")
    totals = insights["totals"]
    print(f"  {totals['risks']} risks · {totals['resolved']} resolved · "
          f"{totals['countries']} countries · {totals['crises']} crises")


if __name__ == "__main__":
    main()
