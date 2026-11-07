"""In-memory store for the pilot loop: experts, sealed answers, revealed round results.

What "sealed" means here (MASTER_PROMPT section 1a): the commitment proves *timing and consistency* and blocks peer
anchoring, because no answer value is readable through the API until the round is revealed. It is NOT confidentiality
from the operator -- this process holds the plaintext in memory. Do not describe it as more than that.

Aggregation (section 6): equal-weight mean is PRIMARY. Reliability weights start equal, shrink to a prior of 1.0 and
are capped, so weighted_mean is a secondary number. Surprisingly-popular is a labelled experiment, never the headline.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher

MASKS = ("known", "pseudonym", "anonymous")
STANCES = ("estimate", "outside_my_expertise", "not_enough_evidence")
SOURCE_TAGS = ("saw", "read", "heard")
BUCKETS = ("0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0")
SP_METHOD = "Prelec 2017 / Palley & Soll peer-prediction weighting"
WEIGHT_FLOOR, WEIGHT_CEIL = 0.5, 2.0

TRIGGER_THEMES = {
    "displacement": ("refugee", "displace", "arrival", "influx", "idp"),
    "conflict": ("raid", "militia", "armed", "fighting", "escalation", "attack", "insecurity"),
    "flood": ("flood", "rain", "inundat"),
    "food": ("food", "harvest", "hunger", "famine"),
    "epidemic": ("cholera", "measles", "outbreak", "epidemic"),
    "access": ("access", "road", "blockade", "convoy"),
    "political": ("election", "government", "coup", "political"),
    "economic": ("price", "inflation", "currency", "economic"),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def commit(payload: dict, salt: str) -> str:
    return hashlib.sha256((canonical_json(payload) + salt).encode("utf-8")).hexdigest()


def round_verify_hash(commitments: list[str]) -> str:
    """verify_hash of a ledger entry = sha256 of the round's sorted commitments. The public Verify
    button checks exactly that, and the UI says exactly that -- nothing about an external anchor."""
    return hashlib.sha256("".join(sorted(commitments)).encode("utf-8")).hexdigest()


def pseudonym_for(expert_id: str, key: str) -> str:
    """Stable pseudonym to peers = HMAC(server_key, expert_id). Readable, and not reversible by peers."""
    digest = hmac.new(key.encode("utf-8"), expert_id.encode("utf-8"), hashlib.sha256).hexdigest()
    adjectives = ("quiet", "tall", "dry", "long", "early", "far", "low", "open", "still", "wide")
    nouns = ("heron", "acacia", "wadi", "dune", "kite", "baobab", "oryx", "harmattan", "reed", "ibis")
    first = adjectives[int(digest[:4], 16) % len(adjectives)]
    second = nouns[int(digest[4:8], 16) % len(nouns)]
    # Two words give 100 names, and a roster in the dozens collides long before that --
    # two experts reading as one person on the board. The suffix widens it to 25,600
    # while staying pronounceable, deterministic and no more reversible than before.
    return f"{first}-{second}-{digest[8:10]}"


def bucket_of(probability: float) -> str:
    return BUCKETS[min(int(probability * 5), 4)]


@dataclass
class Expert:
    id: str
    geo_tags: list[str] = field(default_factory=list)
    theme_tags: list[str] = field(default_factory=list)
    affiliation_tag: str = "ngo"
    languages: list[str] = field(default_factory=lambda: ["en"])
    channel: str = "email"
    status: str = "applied"
    region: str = ""
    weight: float = 1.0
    years_experience: int = 0
    synthetic: bool = True


@dataclass
class Answer:
    id: str
    pulse_id: str
    expert_id: str
    mask: str
    pseudonym: str | None
    probability: float | None
    confidence: int | None
    stance: str
    panel_share_yes: float | None
    missing: str
    source_tag: str | None
    round: int
    changed_mind: bool
    committed_at: str
    commitment: str
    revealed_at: str | None = None
    # Answers to the probes this card asked. They feed themes and coverage; they are never
    # aggregated into the published probability, which stays the frozen core alone.
    probe_answers: dict = field(default_factory=dict)

    def public_view(self) -> dict:
        """What may leave the server before a reveal: the proof of timing, never the value."""
        return {
            "id": self.id,
            "committed_at": self.committed_at,
            "commitment": self.commitment,
            "mask": self.mask,
            "pseudonym": self.pseudonym if self.mask == "pseudonym" else None,
        }


class TooFew(Exception):
    """A round with fewer than k_min answers is never aggregated or returned."""

    def __init__(self, n: int, k_min: int) -> None:
        self.n, self.k_min = n, k_min
        super().__init__(f"{n} answers sealed; this round needs {k_min} before anything can be revealed")


class Store:
    """Single-process store. Rebuildable with `make seed`; nothing here is a system of record."""

    def __init__(self, k_min: int = 5) -> None:
        self.k_min = k_min
        self.experts: dict[str, Expert] = {}
        self.answers: dict[str, list[Answer]] = {}
        self.results: dict[str, dict] = {}
        self.tokens: dict[str, tuple[str, str]] = {}
        # Which links have been used. Deliberately separate from the answers: this records *that*
        # someone answered, which is needed to stop a double submission, and never which answer was
        # theirs. For an anonymous answer that is the only trace, and it stops at the fact.
        self.used_tokens: set[str] = set()
        self.contracts: dict[str, dict] = {}
        self._token_of: dict[str, str] = {}
        self.ledger: list[dict] = []
        self.pulses: dict[str, dict] = {}
        self.drafts: dict[str, dict] = {}
        self.scores: list[dict] = []
        self.approvals: dict[str, list[str]] = {}

    def reset(self) -> None:
        self.experts.clear()
        self.answers.clear()
        self.results.clear()
        self.tokens.clear()
        self.used_tokens.clear()
        self._token_of.clear()
        self.contracts.clear()
        self.ledger.clear()
        self.pulses.clear()
        self.drafts.clear()
        self.scores.clear()
        self.approvals.clear()

    # -- experts and tokens -----------------------------------------------------
    def add_expert(self, expert: Expert) -> Expert:
        self.experts[expert.id] = expert
        return expert

    def issue_token(self, pulse_id: str, expert_id: str) -> str:
        token = uuid.uuid4().hex[:16]
        self.tokens[token] = (pulse_id, expert_id)
        self._token_of[f"{pulse_id}:{expert_id}"] = token
        return token

    def resolve_token(self, token: str) -> tuple[str, str] | None:
        return self.tokens.get(token)

    def mark_used(self, token: str) -> None:
        self.used_tokens.add(token)

    def answered(self, pulse_id: str, expert_id: str) -> bool:
        """True once this link has been used. Asking the answers instead would miss every anonymous
        one, because those carry no expert id -- which is the point of them."""
        token = self._token_of.get(f"{pulse_id}:{expert_id}")
        return bool(token) and token in self.used_tokens

    # -- sealing ----------------------------------------------------------------
    def seal(self, pulse_id: str, expert_id: str, body: dict, salt: str, key: str) -> Answer:
        mask = body.get("mask", "pseudonym")
        if mask not in MASKS:
            raise ValueError(f"mask must be one of {MASKS}")
        stance = body.get("stance", "estimate")
        if stance not in STANCES:
            raise ValueError(f"stance must be one of {STANCES}")

        probability = body.get("probability")
        if stance == "estimate":
            if probability is None:
                raise ValueError("probability is required when stance is 'estimate'")
            probability = float(probability)
            if not 0.0 <= probability <= 1.0:
                raise ValueError("probability must be between 0 and 1")
        else:
            probability = None

        source_tag = body.get("source_tag")
        if source_tag is not None and source_tag not in SOURCE_TAGS:
            raise ValueError(f"source_tag must be one of {SOURCE_TAGS}")

        confidence = body.get("confidence")
        if confidence is not None:
            confidence = int(confidence)
            if not 1 <= confidence <= 5:
                raise ValueError("confidence must be between 1 and 5")

        share = body.get("panel_share_yes")
        if share is not None:
            share = float(share)
            if not 0.0 <= share <= 1.0:
                raise ValueError("panel_share_yes must be between 0 and 1")

        # An 'anonymous' answer is stored with no identity link, and so cannot be claimed later.
        stored_expert = "" if mask == "anonymous" else expert_id
        pseudonym = pseudonym_for(expert_id, key) if mask == "pseudonym" else None
        missing = (body.get("missing") or "")[:240]
        probe_answers = {
            str(k): (v[:240] if isinstance(v, str) else v)
            for k, v in (body.get("probe_answers") or {}).items()
        }
        rnd = int(body.get("round", 1))
        committed_at = now()

        payload = {
            "pulse_id": pulse_id, "mask": mask, "probability": probability, "confidence": confidence,
            "stance": stance, "panel_share_yes": share, "missing": missing, "source_tag": source_tag,
            "round": rnd, "committed_at": committed_at,
            # Sealed with the rest: a probe answer cannot be edited after the fact either.
            "probe_answers": probe_answers,
        }
        answer = Answer(
            id=f"A-{uuid.uuid4().hex[:8]}", pulse_id=pulse_id, expert_id=stored_expert, mask=mask,
            pseudonym=pseudonym, probability=probability, confidence=confidence, stance=stance,
            panel_share_yes=share, missing=missing, source_tag=source_tag, round=rnd,
            changed_mind=bool(body.get("changed_mind", False)), committed_at=committed_at,
            commitment=commit(payload, salt), probe_answers=probe_answers,
        )
        self.answers.setdefault(pulse_id, []).append(answer)
        return answer

    def n_answers(self, pulse_id: str) -> int:
        return len(self.answers.get(pulse_id, []))

    def tray(self, pulse_id: str) -> list[dict]:
        """The analyst's envelope tray before a reveal: sealed envelopes, no values."""
        return [a.public_view() for a in self.answers.get(pulse_id, [])]

    # -- reveal -----------------------------------------------------------------
    def reveal(self, pulse_id: str, risk: dict | None = None) -> dict:
        answers = self.answers.get(pulse_id, [])
        if len(answers) < self.k_min:
            raise TooFew(len(answers), self.k_min)
        revealed_at = now()
        for answer in answers:
            answer.revealed_at = revealed_at
        result = self._aggregate(pulse_id, answers, revealed_at, risk or {})
        self.results[pulse_id] = result
        return result

    def _aggregate(self, pulse_id: str, answers: list[Answer], revealed_at: str, risk: dict) -> dict:
        estimates = [a for a in answers if a.stance == "estimate" and a.probability is not None]
        probabilities = [a.probability for a in estimates]
        mean = round(statistics.fmean(probabilities), 4) if probabilities else None

        spread = None
        if probabilities:
            spread = {
                "min": round(min(probabilities), 4),
                "max": round(max(probabilities), 4),
                "iqr": round(_iqr(probabilities), 4),
            }

        weighted_mean = None
        if estimates:
            weights = [_capped_weight(self.experts.get(a.expert_id)) for a in estimates]
            weighted_mean = round(
                sum(p * w for p, w in zip(probabilities, weights)) / sum(weights), 4
            )

        distribution = [{"bucket": b, "count": 0} for b in BUCKETS]
        position = {b: i for i, b in enumerate(BUCKETS)}
        for probability in probabilities:
            distribution[position[bucket_of(probability)]]["count"] += 1

        return {
            "pulse_id": pulse_id,
            "n": len(answers),
            "n_estimates": len(estimates),
            "mean": mean,
            "spread": spread,
            "minority_rationales": _minority_rationales(estimates, mean),
            "weighted_mean": weighted_mean,
            "sp_experiment": _sp_experiment(estimates),
            "dissent_index": round(_iqr(probabilities), 4) if probabilities else None,
            "distribution": distribution,
            "agreement_by_region": self._agreement_by_region(estimates),
            "missing_themes": _missing_themes(answers, risk),
            "unmatched_notes": _unmatched_notes(answers, risk),
            "abstentions": [
                {"stance": stance, "count": sum(1 for a in answers if a.stance == stance)}
                for stance in ("outside_my_expertise", "not_enough_evidence")
            ],
            "revealed_at": revealed_at,
            "integrity_notes": self._integrity_notes(answers, risk),
            "verify_hash": round_verify_hash([a.commitment for a in answers]),
        }

    def _agreement_by_region(self, estimates: list[Answer]) -> list[dict]:
        groups: dict[str, list[float]] = {}
        for answer in estimates:
            expert = self.experts.get(answer.expert_id)
            region = (expert.region if expert else "") or "unattributed"
            groups.setdefault(region, []).append(answer.probability)
        out = []
        for region, values in sorted(groups.items()):
            # One voice is not a regional view: report the count, withhold the mean.
            out.append({
                "region": region,
                "n": len(values),
                "mean": round(statistics.fmean(values), 4) if len(values) >= 2 else None,
            })
        return out

    def _integrity_notes(self, answers: list[Answer], risk: dict) -> list[dict]:
        """Descriptions, never diagnoses (section 6a). No verdicts, no auto-penalties, no colours.
        Priority order: coverage gaps first, then single-origin claims."""
        notes: list[dict] = []
        panel_themes: list[str] = []
        for answer in answers:
            expert = self.experts.get(answer.expert_id)
            if expert:
                panel_themes.extend(expert.theme_tags)
        tally = {theme: panel_themes.count(theme) for theme in sorted(set(panel_themes))}
        tag_line = ", ".join(f"{k} x{v}" for k, v in tally.items()) or "no tags on record"

        for trigger in risk.get("triggers") or []:
            theme = _theme_of_trigger(trigger)
            if theme and tally.get(theme, 0) == 0:
                notes.append({
                    "kind": "coverage_gap",
                    "text": f"Trigger {trigger.get('id')} ({trigger.get('title')}) has no panel member tagged {theme}.",
                    "evidence": f"panel tags: {tag_line}",
                })

        texts = [(a.id, a.missing.strip()) for a in answers if a.missing.strip()]
        for i in range(len(texts)):
            matched = False
            for j in range(i + 1, len(texts)):
                ratio = SequenceMatcher(None, texts[i][1].lower(), texts[j][1].lower()).ratio()
                if ratio >= 0.85:
                    notes.append({
                        "kind": "shared_origin",
                        "text": "Two 'what are we missing' entries may share an origin (near-identical wording).",
                        "evidence": f"similarity {ratio:.2f}",
                    })
                    matched = True
                    break
            if matched:
                break

        heard = sum(1 for a in answers if a.source_tag == "heard")
        if heard >= max(2, len(answers) // 2):
            notes.append({
                "kind": "shared_origin",
                "text": f"{heard} of {len(answers)} entries are tagged 'heard' rather than seen or read.",
                "evidence": "source_tag distribution on this round",
            })
        return notes


def _theme_of_trigger(trigger: dict) -> str | None:
    text = f"{trigger.get('title', '')} {trigger.get('description', '')}".lower()
    for theme, words in TRIGGER_THEMES.items():
        if any(word in text for word in words):
            return theme
    return None


def _capped_weight(expert: Expert | None) -> float:
    """Weights start equal, shrink toward a prior of 1.0, and are capped (section 6)."""
    raw = expert.weight if expert else 1.0
    shrunk = 1.0 + 0.5 * (raw - 1.0)
    return max(WEIGHT_FLOOR, min(WEIGHT_CEIL, shrunk))


def _iqr(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    lower = ordered[:middle]
    upper = ordered[middle + 1:] if len(ordered) % 2 else ordered[middle:]
    if not lower or not upper:
        return round(max(ordered) - min(ordered), 4)
    return statistics.median(upper) - statistics.median(lower)


def _minority_rationales(estimates: list[Answer], mean: float | None) -> list[str]:
    """The reasons behind the answers furthest from the group, so the spread keeps its argument."""
    if mean is None:
        return []
    far = [a for a in estimates if a.missing.strip() and abs(a.probability - mean) >= 0.2]
    far.sort(key=lambda a: abs(a.probability - mean), reverse=True)
    return [a.missing.strip() for a in far[:3]]


def _sp_experiment(estimates: list[Answer]) -> dict:
    """Surprisingly-popular, labelled experimental. The elicitation is fixed: the share of this panel
    that will put the probability above 0.5. 'yes' means the panel's own answer beat its prediction
    of itself. This is never the headline number."""
    predictions = [a.panel_share_yes for a in estimates if a.panel_share_yes is not None]
    if not predictions or not estimates:
        return {
            "answer": None, "method": SP_METHOD, "label": "experimental",
            "note": "no peer predictions supplied on this round",
        }
    actual = sum(1 for a in estimates if a.probability > 0.5) / len(estimates)
    predicted = statistics.fmean(predictions)
    return {
        "answer": "yes" if actual > predicted else "no",
        "method": SP_METHOD,
        "label": "experimental",
        "actual_share_above_0_5": round(actual, 4),
        "predicted_share": round(predicted, 4),
    }


# Words that make a line about this risk rather than about anything at all. Built from the
# risk's own record -- its title, its triggers, its country and regions -- plus the standing
# humanitarian vocabulary, so the test is "does this bear on the risk in front of you".
STANDING_VOCABULARY = {
    "conflict", "armed", "attack", "raid", "militia", "shelling", "drone", "incursion",
    "clash", "violence", "insecurity", "fighting", "displace", "displacement", "refugee",
    "returnee", "influx", "camp", "idp", "shelter", "food", "hunger", "famine", "harvest",
    "nutrition", "market", "price", "water", "sanitation", "cholera", "health", "clinic",
    "disease", "outbreak", "access", "road", "convoy", "crossing", "border", "blockade",
    "supply", "fuel", "protection", "abuse", "trafficking", "detention", "flood", "drought",
    "rains", "season", "seasonal", "funding", "donor", "evacuation", "curfew", "checkpoint",
}
MIN_RELEVANT_WORDS = 4


def risk_vocabulary(risk: dict | None) -> set[str]:
    if not risk:
        return set(STANDING_VOCABULARY)
    text = " ".join([
        risk.get("title", ""), risk.get("country", ""), risk.get("risk_type", "") or "",
        " ".join(t.get("title", "") + " " + t.get("description", "") for t in risk.get("triggers", [])),
    ]).lower()
    words = {w.strip(".,;:()[]\"'") for w in text.split() if len(w) > 4}
    return STANDING_VOCABULARY | words


def line_is_relevant(text: str, vocabulary: set[str]) -> bool:
    """Does this line bear on the risk at hand?

    A guest at a demo can write anything, and a panel view that absorbs anything is not a
    panel view. This asks only whether the words overlap the risk's own vocabulary -- it is
    not a judgement of whether the contributor is right, and unmatched lines are kept and
    shown to the analyst separately rather than thrown away.
    """
    if len(text.split()) < MIN_RELEVANT_WORDS:
        return False
    words = {w.strip(".,;:()[]\"'").lower() for w in text.split()}
    return bool(words & vocabulary)


def _unmatched_notes(answers: list[Answer], risk: dict | None = None) -> list[dict]:
    """Lines that did not match the risk's vocabulary. Held, not deleted: the analyst sees
    them, they simply do not enter the group view or the draft."""
    vocabulary = risk_vocabulary(risk)
    return [
        {"text": a.missing.strip(), "reason": "no overlap with this risk's vocabulary"}
        for a in answers
        if a.missing.strip() and not line_is_relevant(a.missing.strip(), vocabulary)
    ]


def _missing_themes(answers: list[Answer], risk: dict | None = None) -> list[dict]:
    """Cluster the free-text 'what are we missing' lines. Corroboration stays 'not checked' until
    something actually checks it -- the word is a status, not a compliment."""
    vocabulary = risk_vocabulary(risk)
    clusters: list[dict] = []
    for answer in answers:
        text = answer.missing.strip()
        if not text or not line_is_relevant(text, vocabulary):
            continue
        for cluster in clusters:
            if SequenceMatcher(None, cluster["theme"].lower(), text.lower()).ratio() >= 0.6:
                cluster["count"] += 1
                cluster["tags"].append(answer.source_tag)
                break
        else:
            clusters.append({"theme": text, "count": 1, "tags": [answer.source_tag]})

    out = []
    for cluster in sorted(clusters, key=lambda c: c["count"], reverse=True):
        tags = [tag for tag in cluster.pop("tags") if tag]
        corroboration = "not checked"
        if cluster["count"] >= 2 and any(tag == "saw" for tag in tags):
            corroboration = "corroborated"
        elif cluster["count"] >= 2:
            corroboration = "single-source"
        out.append({
            **cluster,
            "origin": "many" if cluster["count"] > 1 else "single",
            "corroboration": corroboration,
        })
    return out
