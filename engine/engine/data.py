"""The risk list, read from the ACAPS Risk Radar export in data/.

Source of truth is the export, not a fixture: 139 real risks across 57 countries. The live ACAPS API is the
intended first source; until that credential exists this reports `source: "csv"` through /radar/status and says so
in the UI, rather than claiming a live feed it does not have.

Probability is a five-band text field (Very Low .. Very High). PROBABILITY_BANDS is the number we score against,
and the mapping is an ASSUMPTION we state out loud -- ACAPS publishes the bands, not these midpoints. Never score
against Risk Level (section 0 of the master prompt): it is derived from Probability x Impact, so scoring it would
score our own arithmetic.
"""
from __future__ import annotations
import functools
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"
CSV = DATA / "risk-radar-export.csv"

# Assumption, stated in the UI and the pitch. Midpoint of each published band.
PROBABILITY_BANDS: dict[str, float] = {
    "Very Low": 0.05,
    "Low": 0.25,
    "Medium": 0.50,
    "High": 0.75,
    "Very High": 0.95,
}

COLUMNS = {
    "Risk ID": "risk_id",
    "Risk Title": "title",
    "Risk Type": "risk_type",
    "ISO": "country_iso",
    "Country": "country",
    "Probability": "probability_acaps",
    "Impact": "impact_acaps",
    "Risk Level": "level",
    "Status": "status",
    "Risk trend": "trend",
    "Triggers": "triggers_text",
    "Source": "sources_text",
    "Rationale": "rationale",
    "What materialised?": "materialised",
}


def band_to_number(band: str | None) -> float | None:
    """The stated assumption, in one place so the pitch and the engine cannot drift apart."""
    if not band:
        return None
    return PROBABILITY_BANDS.get(str(band).strip())


def _clean(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _field(block: str, label: str) -> str:
    """Pull one labelled field out of a trigger block, stopping at the next label."""
    pattern = (
        rf"^{label}:\s*(.*?)(?=^(?:Trigger ID|Title|Description|Sources|Completion rate"
        rf"|Completion rate history|Quantitative objective to meet 100%|Trend|Trend history"
        rf"|Date entered|Last update):|\Z)"
    )
    match = re.search(pattern, block, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    # The export sometimes puts the body on the next line, prefixed with a stray colon.
    return re.sub(r"\s+", " ", match.group(1).replace("\n:", " ")).strip(" :")


def _split_triggers(text: str) -> list[dict]:
    """ACAPS keeps each trigger as a labelled block in one cell. The blocks carry the field we most
    want for the doorbell: ACAPS's own completion rate, which is a published judgement, not our guess."""
    text = _clean(text)
    if not text:
        return []
    blocks = [b for b in re.split(r"(?=Trigger ID:)", text) if "Trigger ID:" in b]
    triggers = []
    for block in blocks:
        title = _field(block, "Title")
        description = _field(block, "Description")
        if not title and not description:
            continue
        acaps_id = _field(block, "Trigger ID")
        completion = _field(block, "Completion rate")
        percent = re.search(r"(\d{1,3})\s*%", completion)
        triggers.append({
            "id": f"T{len(triggers) + 1}",
            "acaps_trigger_id": acaps_id or None,
            "title": title or (description[:88] + "..." if len(description) > 88 else description),
            "description": description or title,
            "completion_rate": int(percent.group(1)) if percent else None,
            "sources": _split_sources(_field(block, "Sources")),
        })
        if len(triggers) >= 8:
            break
    return triggers


def _split_sources(text: str) -> list[dict]:
    urls = re.findall(r"https?://\S+", _clean(text))
    seen, out = set(), []
    for url in urls:
        # The export writes sources as markdown links with escaped parens, so a raw match drags in
        # a trailing "\)" that breaks the link wherever it is rendered.
        url = url.rstrip("\\).,;")
        if url in seen:
            continue
        seen.add(url)
        out.append({"text": re.sub(r"^https?://(www\.)?", "", url).split("/")[0], "url": url})
    return out[:6]


def _row_to_risk(row: pd.Series) -> dict:
    probability = _clean(row.get("probability_acaps")) or None
    impact = _clean(row.get("impact_acaps"))
    return {
        "risk_id": _clean(row.get("risk_id")),
        "title": _clean(row.get("title")),
        "risk_type": _clean(row.get("risk_type")) or None,
        "country_iso": _clean(row.get("country_iso")),
        "country": _clean(row.get("country")),
        "probability_acaps": probability,
        "probability_assumed_number": band_to_number(probability),
        "impact_acaps": int(float(impact)) if impact else None,
        "level": _clean(row.get("level")) or None,
        "status": _clean(row.get("status")) or "Unknown",
        "trend": _clean(row.get("trend")) or None,
        "horizon_months": 6,
        "triggers": _split_triggers(row.get("triggers_text")),
        "sources": _split_sources(row.get("sources_text")) or [
            {"text": f"ACAPS Risk List, {_clean(row.get('country'))}", "url": "https://www.acaps.org/en/countries"}
        ],
        "materialised": _clean(row.get("materialised")) or None,
    }


@functools.lru_cache(maxsize=1)
def _load() -> tuple[list[dict], str]:
    if not CSV.exists():
        return [], "missing"
    # The export is not UTF-8. Reading it as such turns every accented place name into a replacement
    # character, which then shows up in the UI and on the ledger -- so try the real encodings in order.
    frame = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            frame = pd.read_csv(CSV, dtype=str, keep_default_na=False, na_values=[""], encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if frame is None:
        raise RuntimeError(f"{CSV.name} could not be decoded as utf-8, cp1252 or latin-1")
    frame = frame.rename(columns=COLUMNS)
    risks = [_row_to_risk(row) for _, row in frame.iterrows()]
    risks = [r for r in risks if r["risk_id"]]
    fetched_at = datetime.fromtimestamp(CSV.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    return risks, fetched_at


def all_risks() -> list[dict]:
    return list(_load()[0])


def active_risks() -> list[dict]:
    return [r for r in all_risks() if r["status"].lower().startswith("active")]


def resolved_risks() -> list[dict]:
    """Risks with a known outcome -- the only ones the sensitivity test may use."""
    return [r for r in all_risks() if r["status"].lower() in ("materialised", "not materialised")]


def get_risk(risk_id: str) -> dict | None:
    for risk in all_risks():
        if risk["risk_id"].lower() == risk_id.lower():
            return risk
    return None


def radar_status() -> dict:
    risks, fetched_at = _load()
    return {
        "source": "csv",
        "live_available": False,
        "fetched_at": fetched_at,
        "n_risks": len(risks),
        "n_active": len(active_risks()),
        "n_resolved": len(resolved_risks()),
        "note": "ACAPS Risk Radar export under ACAPS terms of use. The live API is the intended first source; "
                "this build has no API credential, so it reads the export and says so.",
        "probability_assumption": PROBABILITY_BANDS,
    }
