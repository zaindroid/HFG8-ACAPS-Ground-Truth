"""Synthetic material for the hardening stack and the pattern reports (MASTER_PROMPT 6c, 6d).

Everything here is SYNTHETIC: invented names against invented experts, and a history of invented
answers to real past risks. It exists so the committee view, the registry lock line, the access log
and the pattern reports have real rounds behind them on stage rather than an empty page, and so the
6d thresholds are exercised by something other than a unit test.

The profiles are deliberate. One expert anchors on the ACAPS band in round 2, one answers at the
extremes, one is well calibrated, one states more confidence than the answers earn, one abstains
often, one keeps tagging answers "heard" -- and one is ordinary and gets no sentences at all, which
is the output the report should produce most of the time.
"""
from __future__ import annotations

from . import data, draft as draft_builder
from .store import Store

IDENTITIES = {
    "X-syn-01": {"name": "Amina Dago (synthetic)", "email": "amina.dago@example.invalid",
                 "organisation": "Eastern Chad protection NGO (synthetic)", "country": "TCD"},
    "X-syn-02": {"name": "Joseph Mbaye (synthetic)", "email": "j.mbaye@example.invalid",
                 "organisation": "UN agency, Ouaddai (synthetic)", "country": "TCD"},
    "X-syn-03": {"name": "Fatime Oumar (synthetic)", "email": "f.oumar@example.invalid",
                 "organisation": "Displacement response NGO (synthetic)", "country": "TCD"},
    "X-syn-04": {"name": "Paul Ndjekouneyom (synthetic)", "email": "paul.n@example.invalid",
                 "organisation": "Sahel research institute (synthetic)", "country": "TCD"},
    "X-syn-05": {"name": "Halime Brahim (synthetic)", "email": "h.brahim@example.invalid",
                 "organisation": "Access and logistics NGO (synthetic)", "country": "TCD"},
    "X-syn-06": {"name": "Daniel Koumakoye (synthetic)", "email": "d.koumakoye@example.invalid",
                 "organisation": "UN agency, Sila (synthetic)", "country": "TCD"},
    "X-syn-07": {"name": "Mariam Saleh (synthetic)", "email": "m.saleh@example.invalid",
                 "organisation": "Ministry liaison (synthetic)", "country": "TCD"},
    "X-syn-08": {"name": "Issa Tidjani (synthetic)", "email": "i.tidjani@example.invalid",
                 "organisation": "Conflict monitoring institute (synthetic)", "country": "TCD"},
}

# Five risks ACAPS has already resolved, in the region this panel is tagged for. The outcomes are
# ACAPS's own published status, not ours -- only the answers against them are invented. The truth
# value is 1.0 for Materialised and 0.0 for Not materialised; `seed_pattern_history` reads it from
# the export rather than trusting the number here, and skips a risk whose status has changed.
HISTORY = (
    ("R0033", 1.0),   # MLI, inter-communal violence in central Mali: Materialised
    ("R0089", 0.0),   # MLI, deterioration of the humanitarian situation: Not materialised
    ("R0301", 1.0),   # MLI, sanctions and lost livelihoods: Materialised
    ("R0094", 0.0),   # CMR, attacks on civilians and IDP camps: Not materialised
    ("R0978", 1.0),   # NGA/NER, Lakurawa resurgence: Materialised
)
OUTCOME_TRUTH = {"materialised": 1.0, "not materialised": 0.0}

# profile -> how this expert answers. `first` is round 1; `second`, when set, is round 2.
PROFILES = {
    "X-syn-01": "anchors",
    "X-syn-02": "extreme",
    "X-syn-03": "calibrated",
    "X-syn-04": "ordinary",
    "X-syn-05": "overconfident",
    "X-syn-06": "abstains",
    "X-syn-07": "hearsay",
    "X-syn-08": "extreme",
}


def _answer_for(profile: str, index: int, truth: float, published: float | None) -> dict | None:
    """One round-1 answer. Returns None when this profile sits the pulse out entirely."""
    band = published if published is not None else 0.5
    if profile == "anchors":
        # Starts a long way from the published band, every time.
        far = 0.25 if band > 0.5 else 0.75
        return {"probability": far, "confidence": 3, "source_tag": "read",
                "missing": "I want to see the band before I commit."}
    if profile == "extreme":
        # Extremity is overprecision, not accuracy: near-certain answers, wrong on two of five.
        certain = 0.95 if truth > 0.5 else 0.05
        if index in (1, 3):
            certain = 1.0 - certain
        return {"probability": certain, "confidence": 4, "source_tag": "saw",
                "missing": "This one is not close."}
    if profile == "calibrated":
        close = 0.8 if truth > 0.5 else 0.2
        return {"probability": close, "confidence": 5, "source_tag": "read",
                "missing": "Consistent with what the sites reported last month."}
    if profile == "ordinary":
        return {"probability": 0.6 if truth > 0.5 else 0.4, "confidence": 3,
                "source_tag": ("saw", "read", "heard")[index % 3],
                "missing": "Nothing unusual to flag here."}
    if profile == "overconfident":
        wrong = 0.85 if truth < 0.5 else 0.15
        return {"probability": wrong, "confidence": 5, "source_tag": "read",
                "missing": "I am confident about this."}
    if profile == "abstains":
        if index % 3 == 0:
            return {"probability": 0.5, "confidence": 2, "source_tag": "read",
                    "missing": "Only on the ones I know."}
        return {"stance": "outside_my_expertise", "source_tag": None,
                "missing": "Outside what I work on."}
    if profile == "hearsay":
        return {"probability": 0.65 if truth > 0.5 else 0.35, "confidence": 3,
                "source_tag": "heard",
                "missing": "Second-hand from colleagues in the field."}
    return None


def _second_round(profile: str, published: float | None) -> dict | None:
    if profile != "anchors" or published is None:
        return None
    return {"probability": round(published, 2), "confidence": 4, "source_tag": "read",
            "changed_mind": True, "missing": "Changed my mind after seeing the band."}


def seed_identities(hardening, store: Store) -> int:
    """Put the synthetic identities into the encrypted registry, then read one back -- a genuine
    read, which is why it genuinely appears in the access log."""
    written = 0
    for expert_id, identity in IDENTITIES.items():
        if expert_id in store.experts:
            hardening.registry.put(expert_id, identity)
            written += 1
    if written:
        hardening.registry.read(
            next(iter(IDENTITIES)), who="seed", why="confirm the registry decrypts after seeding"
        )
    return written


def seed_groups(hardening, store: Store) -> dict:
    """One membership group per panel, from identity commitments. The group and its root are real;
    the proof verifier is not (see hardening/zk.py)."""
    from .hardening import zk

    commitments = [zk.identity_commitment(expert_id) for expert_id in store.experts]
    group = hardening.membership.add_group("PAN-TCD", commitments)
    return group.as_dict()


def seed_pattern_history(store: Store, settings, hardening=None) -> dict:
    """Five resolved pulses of synthetic history, so the 6d reports have something to describe."""
    from .api import _build_pulse, _trigger_evidence

    pulses, scored = [], 0
    for index, (risk_id, _documented_truth) in enumerate(HISTORY):
        risk = data.get_risk(risk_id)
        if not risk:
            continue
        # The outcome comes from the export. If ACAPS has since changed it, the export wins and the
        # constant above is ignored; if it is no longer resolved at all, the risk is skipped.
        truth = OUTCOME_TRUTH.get((risk.get("status") or "").strip().lower())
        if truth is None:
            continue
        published = risk.get("probability_assumed_number")
        pulse = _build_pulse(risk, "history", None, _trigger_evidence(risk))
        pulse["history"] = True
        pulse["resolved_outcome"] = "materialised" if truth > 0.5 else "not_materialised"
        pulses.append(pulse["id"])

        for expert_id, profile in PROFILES.items():
            if expert_id not in store.experts:
                continue
            first = _answer_for(profile, index, truth, published)
            if first is None:
                continue
            body = {"mask": "pseudonym", "round": 1, "stance": first.get("stance", "estimate"),
                    **first}
            store.seal(pulse["id"], expert_id, body, settings.commitment_salt,
                       settings.pseudonym_key)
            second = _second_round(profile, published)
            if second:
                store.seal(pulse["id"], expert_id,
                           {"mask": "pseudonym", "round": 2, "stance": "estimate", **second},
                           settings.commitment_salt, settings.pseudonym_key)
            probability = (second or first).get("probability")
            if probability is None:
                continue
            store.scores.append({
                "expert_internal_id": expert_id, "risk_id": risk_id,
                "brier": round((probability - truth) ** 2, 4),
                "resolved_at": pulse["fired_at"],
            })
            scored += 1

        # Close the round the way a real one closes: reveal it, draft from it, record the
        # analyst's decision and the outcome on the ledger. Without this the history is a pile of
        # sealed answers with no result, so the panel reports have nothing to describe and
        # /committee/scoring has no resolved round to score a panel against. The reveal is
        # recorded as a before-deadline analyst reveal, because that is what it is.
        try:
            result = store.reveal(pulse["id"], risk, "analyst_before_deadline")
        except Exception:                                              # noqa: BLE001
            continue
        if result.get("reveal_status") != "revealed":
            continue
        built = draft_builder.build(risk, pulse, result)
        store.drafts[built["id"]] = built
        # Two of the five were rejected by the analyst, and one of those later materialised. A
        # history in which the analyst agreed every time would make the ledger's own "panel view
        # rejected" column look like a field nobody uses.
        rejected = index in (1, 3)
        decision = {
            "action": "reject" if rejected else "accept",
            "what_decision": "Weekly risk review for the country team",
            "for_whom": f"ACAPS analyst, {risk.get('country')}",
            "by_when": pulse["fired_at"][:10],
            "note": ("Indicators were flat that month and the panel sat above them; recorded "
                     "here so the miss is the analyst's, not the panel's." if rejected else None),
        }
        built["status"] = "rejected" if rejected else "accepted"
        built["decided_by"] = "analyst"
        built["decided_at"] = pulse["fired_at"]
        built["note"] = decision["note"]
        answers = store.answers.get(pulse["id"], [])
        store.ledger.append({
            "risk_id": risk_id,
            "pulse_id": pulse["id"],
            "sealed_at": min((a.committed_at for a in answers), default=pulse["fired_at"]),
            "group_probability": result["mean"],
            "acaps_probability": risk.get("probability_acaps"),
            "acaps_level": risk.get("level"),
            "proposed_probability": built["proposed_probability"],
            "decision": built["status"],
            "outcome": pulse["resolved_outcome"],
            "resolved_at": pulse["fired_at"],
            "verify_hash": result["verify_hash"],
            "honesty": draft_builder.honesty_box(result, built, decision),
            "synthetic": True,
        })

    if hardening is not None:
        days: dict[str, list[str]] = {}
        for answers in store.answers.values():
            for answer in answers:
                days.setdefault(answer.committed_at[:10], []).append(answer.commitment)
        for day, commitments in days.items():
            hardening.anchors.record(day, commitments)

    return {"pulses": pulses, "scores_written": scored, "synthetic": True}


def seed_credentials(hardening, store: Store, allowance: int = 2) -> dict:
    """A credential batch per approved synthetic expert, and one token spent for the anonymous
    answer in the seeded round -- which is a real spend against a real answer, not a number typed
    into a dashboard. The batches use the demo path, so they are marked linkable, as they are."""
    issued = spent = 0
    for expert_id, expert in store.experts.items():
        if expert.status != "approved" or not expert_id.startswith("X-syn-"):
            continue
        batch = hardening.credentials.issue(expert_id, "PAN-TCD", None, allowance)
        issued += batch["n_issued"]
        anonymous = [a for answers in store.answers.values() for a in answers
                     if a.mask == "anonymous"]
        if anonymous and spent < len(anonymous):
            token = batch["credentials"][0]
            hardening.credentials.spend(token["token_id"], token["signature"],
                                        anonymous[spent].pulse_id)
            spent += 1
    return {"credentials_issued": issued, "credentials_spent": spent}


def seed_all(hardening, store: Store, settings) -> dict:
    """Everything 6c and 6d need, in one call. Safe to skip: the loop works without it."""
    identities = seed_identities(hardening, store)
    group = seed_groups(hardening, store)
    credentials = seed_credentials(hardening, store)
    history = seed_pattern_history(store, settings, hardening)
    return {"identities": identities, "group": group, **credentials, **history}
