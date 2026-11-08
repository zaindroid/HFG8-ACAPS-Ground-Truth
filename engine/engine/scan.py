"""Country scan: the second pulse kind, for the brief's own example question.

"What are the three biggest risks in Chad that might worsen humanitarian outcomes in the next six
months?" A risk pulse asks how likely one frozen event is. A country scan asks the panel to rank
what ACAPS should be watching in one country, and puts that ranking next to ACAPS's own view.

What the expert sees: the question, the country's candidates as large tap targets (ACAPS's active
Risk List entries for the country, plus the ACAPS-tracked crises in it that no active risk covers),
up to three taps in order of importance, an optional line for a risk that is not on the list with a
saw / read / heard tag, the two abstentions, and the mask. Nothing else.

What it guarantees, the same as a risk pulse:
- No anchor. ACAPS's level and severity for each candidate are hidden until the reveal, and the
  order of the candidates is shuffled per link (stable for that link), so the first item on the
  screen is not the same item for everyone -- list position is an anchor too.
- A click never commits. `POST /s/{token}/answer` drafts; `/confirm` commits a salted SHA-256 of the
  canonical answer with a timestamp. A correction before the deadline replaces the commitment and
  keeps the earlier one.
- Reveal at the deadline, never "when five are in". Fewer than k_min counted answers at the
  deadline: insufficient panel, nothing aggregated, nothing revealed.
- Public anonymity. The result carries counts per candidate and nothing per person. A risk only one
  expert added is the line most likely to identify them, so added risks go to the access-logged
  verification queue and the result carries their themes and count only.

What it does not guarantee: secrecy from the operator (this process holds the plaintext), or that a
ranking by eight people is the true ranking. It is a structured, time-stamped panel view the analyst
reads beside ACAPS's own -- one validation layer among others.
"""
from __future__ import annotations

import hashlib
import hmac
import random
import uuid
from dataclasses import dataclass, field

from . import acaps, alerts as alert_engine, data
from . import store as store_mod
from .store import MASKS, SOURCE_TAGS, STANCES, Store, TooEarly, commit, now, past, pseudonym_for

MAX_PICKS = 3
MAX_CANDIDATES = 8
ADDED_MAX_CHARS = 200
POINTS = (3, 2, 1)          # first, second, third pick
LEVEL_ORDER = {"very high": 5, "high": 4, "medium": 3, "low": 2, "very low": 1}
QUESTION = ("What are the three biggest risks in {country} that might worsen humanitarian "
            "outcomes in the next six months?")


@dataclass
class ScanAnswer:
    id: str
    scan_id: str
    expert_id: str | None          # None for "no identity kept"
    mask: str
    pseudonym: str | None
    stance: str
    picks: list[str]
    added: str | None
    source_tag: str | None
    region: str
    committed_at: str
    commitment: str
    versions: list[dict] = field(default_factory=list)


class ScanStore:
    """Scans, their links, drafts and sealed answers. Experts and the verification queue are the
    main store's, so a scan uses the same vetted panel and the same attributed queue reads."""

    def __init__(self) -> None:
        self.scans: dict[str, dict] = {}
        self.tokens: dict[str, tuple[str, str]] = {}
        self.used: set[str] = set()
        self.pending: dict[str, dict] = {}
        self.answers: dict[str, list[ScanAnswer]] = {}
        self.results: dict[str, dict] = {}

    def reset(self) -> None:
        for part in (self.scans, self.tokens, self.pending, self.answers, self.results):
            part.clear()
        self.used.clear()


# -- candidates ---------------------------------------------------------------

def _words(text: str) -> set[str]:
    return {w.strip(",.()").lower() for w in text.split() if len(w.strip(",.()")) > 3}


def candidates(iso3: str, alert_store=None) -> tuple[str, list[dict]]:
    """The country's active ACAPS risks, then the ACAPS crises in it that no active risk covers.

    A crisis counts as covered when an analyst confirmed its link to one of the risks, or when the
    crisis name shares a place word with a risk title ("Displacement from Sudan to Chad" and a
    risk about the Sudan conflict). The country's own name never counts as a shared word."""
    iso3 = iso3.upper()
    risks = [r for r in data.active_risks()
             if iso3 in {c.strip().upper() for c in (r.get("country_iso") or "").split(",")}]
    country = next((r["country"].split(",")[0].strip() for r in risks
                    if "," not in (r.get("country_iso") or "")), None)
    registry = {cid: c for cid, c in acaps.crises().items()
                if iso3 in {i.upper() for i in c["iso3"]}}
    if not country:
        country = next((c["crisis_name"].rsplit(" in ", 1)[-1] for c in registry.values()
                        if " in " in c["crisis_name"]), iso3)
    country_word = country.lower()

    confirmed = set()
    if alert_store is not None:
        confirmed = {link["crisis_id"] for link in alert_store.links.values()}
    risk_words = set().union(*[_words(r["title"]) for r in risks]) - {country_word} if risks else set()

    out: list[dict] = []
    for risk in risks:
        out.append({
            "id": risk["risk_id"], "kind": "acaps_risk", "title": risk["title"],
            "acaps_view": {"level": risk.get("level"), "probability": risk.get("probability_acaps"),
                           "impact": risk.get("impact_acaps")},
            "acaps_rank_key": LEVEL_ORDER.get((risk.get("level") or "").lower(), 0) * 10
                              + (risk.get("impact_acaps") or 0),
        })
    month = acaps.latest_month()
    seen_names: set[str] = set()
    for crisis_id, crisis in sorted(registry.items()):
        name = crisis["crisis_name"]
        if crisis_id in confirmed or name in seen_names:
            continue
        if (_words(name) - {country_word, "crisis", "conflict", "displacement", "floods",
                            "drought", "complex", "province", "regional"}) & risk_words:
            continue
        seen_names.add(name)
        point = acaps.severity_point(crisis_id, month) if month else None
        index = point.get("index") if point else None
        out.append({
            "id": crisis_id, "kind": "acaps_crisis", "title": name,
            "acaps_view": {"inform_severity": index,
                           "category": point.get("category") if point else None,
                           "month": month if point else None,
                           "note": None if point else "not in the current INFORM edition",
                           "active_risk_entry": False},
            "acaps_rank_key": round((index or 0) * 4, 2),
        })
    return country, out[:MAX_CANDIDATES]


def _order_for(token: str, ids: list[str], key: str) -> list[str]:
    """Shuffle per link, stable for that link: the same expert sees the same order on reload, and
    no single candidate sits first for everybody."""
    seed = int(hmac.new(key.encode(), token.encode(), hashlib.sha256).hexdigest()[:12], 16)
    order = list(ids)
    random.Random(seed).shuffle(order)
    return order


# -- create, card, draft, confirm ---------------------------------------------

def create(scans: ScanStore, main: Store, iso3: str, expires_at: str, alert_store=None,
           panel_size: int = 8) -> dict:
    country, cands = candidates(iso3, alert_store)
    if len(cands) < MAX_PICKS:
        raise ValueError(f"{iso3} has {len(cands)} candidates; a top-three question needs at least three")
    scan_id = f"S-{iso3.upper()}-{uuid.uuid4().hex[:6]}"
    # Guests (the room on stage) get links separately; they are never part of the vetted panel.
    approved = [e for e in main.experts.values()
                if e.status == "approved" and e.affiliation_tag != "guest"
                and iso3.upper() in [g.upper() for g in e.geo_tags]]
    chosen, per_aff = [], {}
    for expert in sorted(approved, key=lambda e: e.id):
        if per_aff.get(expert.affiliation_tag, 0) >= 3:
            continue
        chosen.append(expert)
        per_aff[expert.affiliation_tag] = per_aff.get(expert.affiliation_tag, 0) + 1
        if len(chosen) == panel_size:
            break
    scan = {
        "id": scan_id, "kind": "country_scan", "iso3": iso3.upper(), "country": country,
        "question": QUESTION.format(country=country), "max_picks": MAX_PICKS,
        "candidates": cands, "created_at": now(), "expires_at": expires_at,
        "reveal_status": "open", "panel": [e.id for e in chosen],
    }
    scans.scans[scan_id] = scan
    for expert in chosen:
        issue_token(scans, scan_id, expert.id)
    return scan


def issue_token(scans: ScanStore, scan_id: str, expert_id: str) -> str:
    token = uuid.uuid4().hex[:16]
    scans.tokens[token] = (scan_id, expert_id)
    return token


def card(scans: ScanStore, token: str, key: str) -> dict:
    scan_id, _ = _resolve(scans, token)
    scan = scans.scans[scan_id]
    by_id = {c["id"]: c for c in scan["candidates"]}
    order = _order_for(token, list(by_id), key)
    return {
        "scan_id": scan_id, "kind": "country_scan", "question": scan["question"],
        "max_picks": MAX_PICKS, "pick_note": "Tap up to three, most important first.",
        # Title only: no level, no severity, no kind. The ACAPS view appears after the reveal.
        "candidates": [{"id": cid, "title": by_id[cid]["title"]} for cid in order],
        "added_prompt": "A risk that is not on this list (optional)",
        "source_tags": list(SOURCE_TAGS), "stances": list(STANCES),
        "mask_options": [{"id": "known", "label": "named to ACAPS"},
                         {"id": "pseudonym", "label": "nickname to peers"},
                         {"id": "anonymous", "label": "no identity kept",
                          "note": "you will not receive personal feedback on this answer"}],
        "mask_default": None,
        "mask_note": store_mod.REIDENTIFICATION_NOTE.replace("its author", "you").replace(
            "; experts were told this before answering", ""),
        "expires_at": scan["expires_at"], "correction_allowed_until": scan["expires_at"],
        "acaps_view_shown": False, "order": "shuffled for this link",
        "already_answered": token in scans.used,
    }


def _resolve(scans: ScanStore, token: str) -> tuple[str, str]:
    found = scans.tokens.get(token)
    if not found:
        raise KeyError("unknown link")
    return found


def normalise(scan: dict, body: dict) -> dict:
    mask = body.get("mask")
    if mask not in MASKS:
        raise ValueError("choose how you appear: known, pseudonym or anonymous (there is no default)")
    stance = body.get("stance") or "estimate"
    if stance not in STANCES:
        raise ValueError(f"stance must be one of {', '.join(STANCES)}")
    valid = {c["id"] for c in scan["candidates"]}
    picks = [p for p in (body.get("picks") or []) if p]
    if stance == "estimate":
        if not picks and not (body.get("added") or "").strip():
            raise ValueError("pick at least one risk, add one, or choose an abstention")
        if len(picks) > MAX_PICKS:
            raise ValueError(f"at most {MAX_PICKS} picks")
        if len(set(picks)) != len(picks):
            raise ValueError("each risk can be picked once")
        unknown = [p for p in picks if p not in valid]
        if unknown:
            raise ValueError(f"not a candidate for this scan: {', '.join(unknown)}")
    else:
        picks = []
    added = (body.get("added") or "").strip()[:ADDED_MAX_CHARS] or None
    source_tag = body.get("source_tag") if added else None
    if added and source_tag not in SOURCE_TAGS:
        raise ValueError("tag the added risk: saw, read or heard")
    return {"mask": mask, "stance": stance, "picks": picks, "added": added, "source_tag": source_tag}


def draft(scans: ScanStore, token: str, body: dict) -> dict:
    scan_id, expert_id = _resolve(scans, token)
    scan = scans.scans[scan_id]
    if scan["reveal_status"] != "open" or past(scan["expires_at"]):
        raise PermissionError("this scan is closed")
    clean = normalise(scan, body)
    confirm_token = uuid.uuid4().hex[:12]
    scans.pending[confirm_token] = {"token": token, "clean": clean, "at": now()}
    titles = {c["id"]: c["title"] for c in scan["candidates"]}
    summary = ("; ".join(f"{i + 1}. {titles[p][:60]}" for i, p in enumerate(clean["picks"]))
               or clean["stance"].replace("_", " "))
    return {"confirm_token": confirm_token, "summary": summary, "committed": False,
            "message": "Nothing is recorded until you confirm."}


def confirm(scans: ScanStore, main: Store, token: str, confirm_token: str, salt: str,
            key: str) -> dict:
    held = scans.pending.pop(confirm_token, None)
    if not held or held["token"] != token:
        raise KeyError("confirmation not found for this link")
    scan_id, expert_id = _resolve(scans, token)
    scan = scans.scans[scan_id]
    if scan["reveal_status"] != "open" or past(scan["expires_at"]):
        raise PermissionError("this scan is closed")
    clean = held["clean"]
    committed_at = now()
    commitment = commit({**clean, "scan_id": scan_id, "committed_at": committed_at}, salt)
    expert = main.experts.get(expert_id)
    existing = next((a for a in scans.answers.get(scan_id, [])
                     if a.id == _answer_id(token, key)), None)
    if existing:
        # A correction before the deadline: the new commitment replaces the old, which is kept.
        existing.versions.append({"commitment": existing.commitment,
                                  "committed_at": existing.committed_at})
        for name, value in clean.items():
            setattr(existing, name, value)
        existing.committed_at, existing.commitment = committed_at, commitment
        if clean["mask"] == "anonymous":
            existing.expert_id, existing.pseudonym = None, None
        answer = existing
    else:
        answer = ScanAnswer(
            id=_answer_id(token, key), scan_id=scan_id,
            expert_id=None if clean["mask"] == "anonymous" else expert_id,
            mask=clean["mask"],
            pseudonym=pseudonym_for(expert_id, key) if clean["mask"] == "pseudonym" else None,
            stance=clean["stance"], picks=clean["picks"], added=clean["added"],
            source_tag=clean["source_tag"], region=(expert.region if expert else "") or "",
            committed_at=committed_at, commitment=commitment)
        scans.answers.setdefault(scan_id, []).append(answer)
    scans.used.add(token)
    return {"committed_at": committed_at, "commitment": commitment,
            "version": len(answer.versions) + 1,
            "correction_allowed_until": scan["expires_at"],
            "message": "Thanks. You'll hear how the panel saw it after the deadline."}


def _answer_id(token: str, key: str) -> str:
    # Derived from the link, not stored against it: an anonymous answer can be corrected from its
    # own link without the answer carrying the expert's id.
    return "SA-" + hmac.new(key.encode(), ("scan:" + token).encode(), hashlib.sha256).hexdigest()[:10]


# -- reveal and result ---------------------------------------------------------

def reveal(scans: ScanStore, main: Store, scan_id: str, reason: str = "deadline") -> dict:
    scan = scans.scans[scan_id]
    if reason != "analyst_before_deadline" and not past(scan["expires_at"]):
        raise TooEarly(scan["expires_at"])
    answers = scans.answers.get(scan_id, [])
    if len(answers) < main.k_min:
        scan["reveal_status"] = "insufficient_panel"
        return {"scan_id": scan_id, "reveal_status": "insufficient_panel", "n": len(answers),
                "k_min": main.k_min, "revealed_reason": reason,
                "message": (f"{len(answers)} answers counted; this scan needs {main.k_min}. "
                            "The answers are kept and nothing is revealed, to anyone.")}
    result = _aggregate(scan, answers)
    result.update({"reveal_status": "revealed", "revealed_reason": reason, "revealed_at": now(),
                   "verify_hash": store_mod.round_verify_hash([a.commitment for a in answers]),
                   "reidentification_note": store_mod.REIDENTIFICATION_NOTE})
    _queue_added(main, scan_id, answers)
    result["verification_queue_count"] = len(main.verification_queue.get(scan_id, []))
    scans.results[scan_id] = result
    scan["reveal_status"] = "revealed"
    return result


def _aggregate(scan: dict, answers: list[ScanAnswer]) -> dict:
    ranking_answers = [a for a in answers if a.stance == "estimate" and a.picks]
    n_rankers = len(ranking_answers)
    tally = {c["id"]: {"points": 0, "in_top3": 0, "first": 0} for c in scan["candidates"]}
    for answer in ranking_answers:
        for position, pick in enumerate(answer.picks):
            tally[pick]["points"] += POINTS[position]
            tally[pick]["in_top3"] += 1
            if position == 0:
                tally[pick]["first"] += 1
    acaps_order = [c["id"] for c in sorted(scan["candidates"], key=lambda c: -c["acaps_rank_key"])]
    panel_order = sorted(tally, key=lambda cid: (-tally[cid]["points"], -tally[cid]["in_top3"],
                                                 acaps_order.index(cid)))
    by_id = {c["id"]: c for c in scan["candidates"]}
    ranking = []
    for rank, cid in enumerate(panel_order, start=1):
        cand = by_id[cid]
        ranking.append({
            "rank": rank, "id": cid, "title": cand["title"], "kind": cand["kind"],
            "points": tally[cid]["points"], "in_top3": tally[cid]["in_top3"],
            "first_choice": tally[cid]["first"],
            "share_in_top3": round(tally[cid]["in_top3"] / n_rankers, 4) if n_rankers else None,
            "acaps_view": cand["acaps_view"], "acaps_rank": acaps_order.index(cid) + 1,
        })
    top3 = [r["id"] for r in ranking[:MAX_PICKS]]
    acaps_top3 = acaps_order[:MAX_PICKS]
    notes = []
    for row in ranking[:MAX_PICKS]:
        if row["kind"] == "acaps_crisis" and row["in_top3"]:
            notes.append({"kind": "no_risk_entry", "id": row["id"],
                          "text": (f"{_cap(store_mod._count_word(row['in_top3']))} of {n_rankers} put "
                                   f"\"{row['title']}\" in their top three; ACAPS tracks it as a crisis "
                                   "but has no active Risk List entry for it. A candidate for the analyst "
                                   "to consider, not a finding.")})
    for cid in acaps_top3:
        if cid not in top3:
            row = next(r for r in ranking if r["id"] == cid)
            notes.append({"kind": "panel_below_acaps", "id": cid,
                          "text": (f"ACAPS ranks \"{row['title']}\" in its top three; "
                                   f"{store_mod._count_word(row['in_top3'])} of {n_rankers} experts did.")})
    leader = ranking[0] if ranking else None
    agreement = round(leader["first_choice"] / n_rankers, 4) if leader and n_rankers else None
    added = [a for a in answers if a.added]
    themes: dict[str, int] = {}
    for a in added:
        for theme in store_mod._themes_in(a.added) or ["other"]:
            themes[theme] = themes.get(theme, 0) + 1
    return {
        "scan_id": scan["id"], "kind": "country_scan", "iso3": scan["iso3"],
        "country": scan["country"], "question": scan["question"],
        "n": len(answers), "n_ranking": n_rankers,
        "abstentions": {s: sum(1 for a in answers if a.stance == s) for s in STANCES[1:]},
        "ranking": ranking,
        "panel_top3": top3, "acaps_top3": acaps_top3,
        "overlap_with_acaps_top3": len(set(top3) & set(acaps_top3)),
        "first_choice_agreement": agreement,
        "notes": notes,
        "added_risks": {"count": len(added),
                        "themes": [{"theme": t, "count": c} for t, c in sorted(themes.items())],
                        "where": "verification queue, access-logged"},
        "by_region": _by_region(ranking_answers),
        "method": ("Points 3, 2 and 1 for first, second and third pick; ties broken by how many "
                   "experts picked it, then by ACAPS's own order. ACAPS's order: Risk List entries "
                   "by level and impact, then crises by current INFORM severity."),
    }


def _by_region(answers: list[ScanAnswer]) -> list[dict]:
    """First choices by region, only where a region has three or more voices; smaller groups are
    merged so no region line describes one or two people."""
    groups: dict[str, list[ScanAnswer]] = {}
    for a in answers:
        groups.setdefault(a.region or "unattributed", []).append(a)
    merged: dict[str, list[ScanAnswer]] = {}
    for region, members in groups.items():
        merged.setdefault(region if len(members) >= 3 else "other regions", []).extend(members)
    out = []
    for region, members in sorted(merged.items()):
        if len(members) < 3:
            continue
        firsts: dict[str, int] = {}
        for a in members:
            firsts[a.picks[0]] = firsts.get(a.picks[0], 0) + 1
        top = max(firsts.items(), key=lambda kv: kv[1])
        out.append({"region": region, "n": len(members), "top_first_choice": top[0],
                    "count": top[1]})
    return out


def _queue_added(main: Store, scan_id: str, answers: list[ScanAnswer]) -> None:
    queue = [{"id": f"VQ-{i + 1:03d}", "pulse_id": scan_id, "kind": "added_risk", "text": a.added,
              "source_tag": a.source_tag, "corroboration": "not checked",
              "author": {"mask": a.mask, "pseudonym": a.pseudonym if a.mask == "pseudonym" else None},
              "status": "to_verify"}
             for i, a in enumerate(x for x in answers if x.added)]
    main.verification_queue[scan_id] = queue


def public(result: dict) -> dict:
    """What the public may see: the aggregate, never an individual. Already true of the result, so
    this only drops the analyst-facing notes about missing Risk List entries."""
    return {k: v for k, v in result.items() if k not in ("notes",)}


def _cap(word: str) -> str:
    return word[:1].upper() + word[1:]


# -- the demo scan ----------------------------------------------------------------

DEMO_ANSWERS = [
    # Synthetic. The panel agrees with ACAPS on the Sudan border, and five of the six who rank put
    # the flood season in their top three -- a crisis ACAPS tracks, absent from the current INFORM
    # edition and with no active Risk List entry. ACAPS's third, the complex crisis, makes only two
    # top threes. Two abstain; one adds a risk that goes to the verification queue.
    {"mask": "pseudonym", "picks": ["R1043", "TCD007", "R1066"]},
    {"mask": "pseudonym", "picks": ["R1043", "R1066", "TCD007"]},
    {"mask": "known", "picks": ["R1043", "TCD007", "TCD001"],
     "added": "Cholera after the rains in the Ouaddai camps", "source_tag": "read"},
    {"mask": "anonymous", "picks": ["TCD007", "R1043", "R1066"]},
    {"mask": "pseudonym", "picks": ["R1043", "TCD004", "TCD007"]},
    {"mask": "known", "picks": ["R1066", "R1043", "TCD001"]},
    {"mask": "pseudonym", "stance": "outside_my_expertise"},
    {"mask": "anonymous", "stance": "not_enough_evidence"},
]


def seed_demo(scans: ScanStore, main: Store, settings, alert_store=None, iso3: str = "TCD",
              hours: int = 48, guests: int = 4) -> str:
    """One country scan for Chad with the synthetic panel's answers sealed, plus open links for the
    room. Leaves the scan open: it reveals at its deadline like any other."""
    from datetime import datetime, timedelta, timezone
    scans.reset()
    expires = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(timespec="seconds")
    scan = create(scans, main, iso3, expires, alert_store)
    valid = {c["id"] for c in scan["candidates"]}
    tokens = [t for t, (sid, _) in scans.tokens.items() if sid == scan["id"]]
    for token, row in zip(tokens, DEMO_ANSWERS):
        body = {"stance": row.get("stance", "estimate"), "mask": row["mask"],
                "picks": [p for p in row.get("picks", []) if p in valid],
                "added": row.get("added"), "source_tag": row.get("source_tag")}
        drafted = draft(scans, token, body)
        confirm(scans, main, token, drafted["confirm_token"], settings.commitment_salt,
                settings.pseudonym_key)
    for index in range(1, guests + 1):
        guest_id = f"X-guest-{index:02d}"
        if guest_id in main.experts:
            issue_token(scans, scan["id"], guest_id)
    return scan["id"]
