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
RELAY_CHANNELS = ("analyst", "liaison", "partner")

# The one required input on the card (section 8). The printed range is part of the question, not
# decoration: a word is never silently turned into a point, so when an expert gives only a word the
# aggregate uses the band midpoint and every payload that carries the number says which it used.
# The midpoints are the band centres rounded to two places, the same figures the card prints.
LIKELIHOOD_WORDS = (
    {"id": "very_unlikely", "label": "very unlikely", "range": "under 10 %",
     "midpoint": 0.05, "lo": 0.0, "hi": 0.10},
    {"id": "unlikely", "label": "unlikely", "range": "10 to 35 %",
     "midpoint": 0.22, "lo": 0.10, "hi": 0.35},
    {"id": "even", "label": "even", "range": "35 to 65 %",
     "midpoint": 0.5, "lo": 0.35, "hi": 0.65},
    {"id": "likely", "label": "likely", "range": "65 to 90 %",
     "midpoint": 0.78, "lo": 0.65, "hi": 0.90},
    {"id": "very_likely", "label": "very likely", "range": "over 90 %",
     "midpoint": 0.95, "lo": 0.90, "hi": 1.0},
)
WORD_BY_ID = {word["id"]: word for word in LIKELIHOOD_WORDS}
# The card offers three words (section 8); the contract scale is 1 to 5. These are its ends and its
# middle, and the payload says that is what happened rather than implying five steps were offered.
CONFIDENCE_WORDS = {"not sure": 1, "fairly sure": 3, "sure": 5}
CONFIDENCE_SCALE_NOTE = ("The card offers three words. They are stored as 1, 3 and 5 of the "
                         "1-to-5 contract scale; no finer reading was collected.")
REIDENTIFICATION_NOTE = ("In a panel of eight a distinctive reason may identify its author to "
                         "colleagues; experts were told this before answering.")
# How far from the panel mean an answer has to sit before it counts as disagreement rather than
# ordinary spread.
DISAGREEMENT_MARGIN = 0.15
# Above this similarity two "what are we missing" entries are treated as one origin, not two
# sources. Both the integrity notes and the corroboration status read it, so they cannot disagree.
SHARED_ORIGIN_RATIO = 0.85
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


def past(timestamp: str) -> bool:
    """Has this ISO timestamp passed? Parsed, not compared as text: the card writes deadlines with
    a Z and this process writes them with +00:00, and those two sort in the wrong order."""
    try:
        when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return True   # an unreadable deadline must not block a reveal for ever
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= when


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
    return f"{first}-{second}"


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
    likelihood_word: str | None = None
    probability_source: str | None = None     # "exact" | "band_midpoint" | None
    confidence_word: str | None = None
    against: str = ""
    trigger_pick: str | None = None
    relayed: bool = False
    relayed_by: str | None = None
    confirmed_by_expert_at: str | None = None
    submitted_at: str | None = None
    corrected_at: str | None = None
    version: int = 1
    previous_versions: list[dict] = field(default_factory=list)
    probe_answers: dict = field(default_factory=dict)
    edit_key_hash: str = ""
    edit_key_once: str | None = None    # cleared by take_edit_key after the one response that gets it
    revealed_at: str | None = None

    def written_lines(self) -> list[tuple[str, str]]:
        """Every line this expert actually wrote, with where it came from. The card's two fixed
        prompts and whatever free-text probes their path through steps 2 and 3 landed on."""
        lines = [("missing", (self.missing or "").strip()),
                 ("against", (self.against or "").strip())]
        for key, value in (self.probe_answers or {}).items():
            # A chosen option is one token with no spaces ("250,000-500,000", "still_true"). It is
            # a datum, not a sentence, and clustering it as free text invents a theme out of a
            # radio button. Those are counted in `probe_summary` instead.
            if isinstance(value, str) and value.strip() and " " in value.strip():
                lines.append((f"probe:{key}", value.strip()))
        return [(kind, text) for kind, text in lines if text]

    def counts(self) -> bool:
        """A relayed answer counts only once the expert has confirmed it through their own link
        (section 4). Until then it is held, visible to the analyst as held, and never aggregated."""
        return (not self.relayed) or bool(self.confirmed_by_expert_at)

    def public_view(self) -> dict:
        """What may leave the server before a reveal: the proof of timing, never the value."""
        return {
            "id": self.id,
            "committed_at": self.committed_at,
            "commitment": self.commitment,
            "mask": self.mask,
            "pseudonym": self.pseudonym if self.mask == "pseudonym" else None,
            "version": self.version,
            "corrected_at": self.corrected_at,
            "relayed": self.relayed,
            "relayed_by": self.relayed_by,
            "counts": self.counts(),
        }

    def snapshot(self) -> dict:
        """A kept version. Every correction keeps the one it replaced, commitment included, so the
        committee can see that a view changed and when, not only the answer that survived."""
        return {
            "version": self.version,
            "likelihood_word": self.likelihood_word,
            "probability": self.probability,
            "probability_source": self.probability_source,
            "confidence": self.confidence,
            "stance": self.stance,
            "missing": self.missing,
            "against": self.against,
            "trigger_pick": self.trigger_pick,
            "source_tag": self.source_tag,
            "probe_answers": dict(self.probe_answers),
            "mask": self.mask,
            "committed_at": self.committed_at,
            "commitment": self.commitment,
        }


class TooFew(Exception):
    """A round with fewer than k_min answers is never aggregated or returned."""

    def __init__(self, n: int, k_min: int) -> None:
        self.n, self.k_min = n, k_min
        super().__init__(f"{n} answers sealed; this round needs {k_min} before anything can be revealed")


class TooEarly(Exception):
    """A reveal before the deadline printed on the card. v3.4 fixes the reveal at `expires_at`:
    "when five are in" would let the panel size decide the moment, which is exactly the signal a
    reminder is not allowed to carry."""

    def __init__(self, expires_at: str) -> None:
        self.expires_at = expires_at
        super().__init__(f"this round opens at {expires_at}; it cannot be revealed before then")


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
        # Drafts live here until a confirmation commits them. A link click, a mail scanner or a
        # link preview fetch can reach POST /answer; none of them can reach a commitment.
        self.pending: dict[str, dict] = {}
        # A reveal that found fewer than k_min answers. Kept apart from `results` on purpose:
        # nothing was aggregated, so there is no result, and round 2 must not open off the back
        # of it either.
        self.reveal_attempts: dict[str, dict] = {}
        # Distinctive free text, held for the analyst with its source tag, read only through an
        # attributed request (who and why), each read appended to the log beside it.
        self.verification_queue: dict[str, list[dict]] = {}
        self.queue_access_log: list[dict] = []
        # edit-key hash -> answer id. The only handle on an anonymous answer: the key lives in the
        # expert's own confirmation message, so holding this map does not tell the server whose
        # answer it is. See `correct`.
        self._answer_by_edit_key: dict[str, str] = {}

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
        self.pending.clear()
        self.reveal_attempts.clear()
        self.verification_queue.clear()
        self.queue_access_log.clear()
        self._answer_by_edit_key.clear()

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

    # -- the card: draft, confirm, correct --------------------------------------
    def normalise(self, body: dict) -> dict:
        """One validator for every way an answer arrives -- the card, a correction, a relayed
        entry, the seed. Raises ValueError with the sentence the expert should read.

        The mask has no default (section 8). A default mask is a decision about someone's
        confidentiality taken by whoever wrote the code, so this refuses instead of guessing."""
        mask = body.get("mask")
        if mask is None or mask == "":
            raise ValueError("choose how your answer is attributed; there is no default mask")
        if mask not in MASKS:
            raise ValueError(f"mask must be one of {MASKS}")

        stance = body.get("stance", "estimate")
        if stance not in STANCES:
            raise ValueError(f"stance must be one of {STANCES}")

        word = body.get("likelihood_word")
        if word is not None and word not in WORD_BY_ID:
            raise ValueError(f"likelihood_word must be one of {tuple(WORD_BY_ID)}")

        probability = body.get("probability")
        if probability is not None:
            probability = float(probability)
            if not 0.0 <= probability <= 1.0:
                raise ValueError("probability must be between 0 and 1")

        source = None
        if stance == "estimate":
            if word is None and probability is None:
                raise ValueError("an estimate needs one of the five words, or an exact percentage")
            if probability is not None:
                source = "exact"
                if word is not None and not (WORD_BY_ID[word]["lo"] <= probability
                                             <= WORD_BY_ID[word]["hi"]):
                    raise ValueError(
                        f"{probability:.2f} is outside '{WORD_BY_ID[word]['label']}' "
                        f"({WORD_BY_ID[word]['range']}); pick the word that matches your number")
            else:
                probability = WORD_BY_ID[word]["midpoint"]
                source = "band_midpoint"
        else:
            # "Outside my area" and "not enough evidence" are real answers and are never scored.
            probability, word, source = None, None, None

        source_tag = body.get("source_tag")
        if source_tag is not None and source_tag not in SOURCE_TAGS:
            raise ValueError(f"source_tag must be one of {SOURCE_TAGS}")

        raw_confidence = body.get("confidence")
        confidence, confidence_word = None, None
        if isinstance(raw_confidence, str) and raw_confidence.strip():
            confidence_word = raw_confidence.strip().lower()
            if confidence_word not in CONFIDENCE_WORDS:
                raise ValueError(f"confidence must be one of {tuple(CONFIDENCE_WORDS)}")
            confidence = CONFIDENCE_WORDS[confidence_word]
        elif raw_confidence is not None:
            confidence = int(raw_confidence)
            if not 1 <= confidence <= 5:
                raise ValueError("confidence must be between 1 and 5")

        share = body.get("panel_share_yes")
        if share is not None:
            share = float(share)
            if not 0.0 <= share <= 1.0:
                raise ValueError("panel_share_yes must be between 0 and 1")

        relayed = bool(body.get("relayed", False))
        relayed_by = body.get("relayed_by")
        if relayed and relayed_by not in RELAY_CHANNELS:
            raise ValueError(f"a relayed answer needs relayed_by in {RELAY_CHANNELS}")
        if not relayed:
            relayed_by = None

        # The probe answers from steps 2 and 3 of the card. Kept as written, counted and
        # clustered like the other free text, and never read into the probability: the number the
        # panel mean uses is the one the expert gave in step 1 and nothing else.
        probes: dict = {}
        for key, value in (body.get("probe_answers") or {}).items():
            key = str(key)[:64]
            if isinstance(value, str):
                probes[key] = value.strip()[:240]
            elif isinstance(value, (list, tuple)):
                probes[key] = [str(item)[:64] for item in value][:8]
            elif value is not None:
                probes[key] = str(value)[:64]
        probes = {key: value for key, value in probes.items() if value}

        return {
            "mask": mask,
            "stance": stance,
            "probe_answers": probes,
            "likelihood_word": word,
            "probability": probability,
            "probability_source": source,
            "confidence": confidence,
            "confidence_word": confidence_word,
            "panel_share_yes": share,
            "missing": (body.get("missing") or "")[:240],
            "against": (body.get("against") or "")[:240],
            "trigger_pick": body.get("trigger_pick") or None,
            "source_tag": source_tag,
            "round": int(body.get("round", 1)),
            "changed_mind": bool(body.get("changed_mind", False)),
            "relayed": relayed,
            "relayed_by": relayed_by,
        }

    def summarise(self, clean: dict) -> str:
        """The one line the confirmation screen repeats back. Written from the normalised answer,
        not from the request, so what is confirmed is what will be committed."""
        if clean["stance"] != "estimate":
            head = {"outside_my_expertise": "outside my area",
                    "not_enough_evidence": "not enough evidence"}[clean["stance"]]
        elif clean["probability_source"] == "exact":
            head = f"{clean['probability'] * 100:.0f} %"
            if clean["likelihood_word"]:
                head += f" ({WORD_BY_ID[clean['likelihood_word']]['label']})"
        else:
            word = WORD_BY_ID[clean["likelihood_word"]]
            head = f"{word['label']} ({word['range']})"
        parts = [head, {"known": "named to ACAPS", "pseudonym": "nickname to peers",
                        "anonymous": "no identity kept"}[clean["mask"]]]
        if clean["confidence_word"]:
            parts.append(clean["confidence_word"])
        if clean["missing"]:
            parts.append(f"note: {clean['missing'][:60]}")
        if clean["against"]:
            parts.append(f"against: {clean['against'][:60]}")
        if clean["trigger_pick"]:
            parts.append(f"trigger: {clean['trigger_pick']}")
        if clean["probe_answers"]:
            parts.append(f"{len(clean['probe_answers'])} follow-up answers")
        return " · ".join(parts)

    def draft(self, pulse_id: str, expert_id: str, body: dict) -> dict:
        """POST /e/{token}/answer. Validates, prices the word into a number, and hands back a
        confirmation token. Nothing is in `answers` yet and no commitment exists."""
        clean = self.normalise(body)
        token = f"cf-{uuid.uuid4().hex[:6]}"
        self.pending[token] = {"pulse_id": pulse_id, "expert_id": expert_id, "answer": clean,
                               "drafted_at": now()}
        return {"confirm_token": token, "summary": self.summarise(clean), "committed": False,
                "message": "Nothing is recorded until you confirm.",
                "answer": clean}

    def confirm(self, confirm_token: str, pulse_id: str, expert_id: str,
                salt: str, key: str) -> Answer:
        """POST /e/{token}/confirm. The first valid confirmation per expert per pulse counts."""
        pending = self.pending.get(confirm_token)
        if not pending:
            raise ValueError("this confirmation has expired or was already used; "
                             "open your link again to answer")
        if pending["pulse_id"] != pulse_id or pending["expert_id"] != expert_id:
            raise ValueError("this confirmation belongs to a different link")
        if self.answered(pulse_id, expert_id):
            raise ValueError("an answer from this link is already committed; "
                             "use 'change my answer' to correct it before the deadline")
        del self.pending[confirm_token]
        return self._commit(pulse_id, expert_id, pending["answer"], salt, key)

    def seal(self, pulse_id: str, expert_id: str, body: dict, salt: str, key: str) -> Answer:
        """Draft and confirm in one step. Not reachable from the card -- the card always goes
        through the confirmation screen -- and used by the seed, the relayed path and the tests."""
        return self._commit(pulse_id, expert_id, self.normalise(body), salt, key)

    def _commit(self, pulse_id: str, expert_id: str, clean: dict, salt: str, key: str) -> Answer:
        # An 'anonymous' answer is stored with no identity link, and so cannot be claimed later.
        stored_expert = "" if clean["mask"] == "anonymous" else expert_id
        pseudonym = pseudonym_for(expert_id, key) if clean["mask"] == "pseudonym" else None
        committed_at = now()
        edit_key = uuid.uuid4().hex[:12]
        answer = Answer(
            id=f"A-{uuid.uuid4().hex[:8]}", pulse_id=pulse_id, expert_id=stored_expert,
            pseudonym=pseudonym, committed_at=committed_at, submitted_at=committed_at,
            commitment=self._commitment(pulse_id, clean, committed_at, 1, salt),
            edit_key_hash=hashlib.sha256(edit_key.encode("utf-8")).hexdigest(),
            mask=clean["mask"], stance=clean["stance"], likelihood_word=clean["likelihood_word"],
            probability=clean["probability"], probability_source=clean["probability_source"],
            confidence=clean["confidence"], confidence_word=clean["confidence_word"],
            panel_share_yes=clean["panel_share_yes"], missing=clean["missing"],
            against=clean["against"], trigger_pick=clean["trigger_pick"],
            source_tag=clean["source_tag"], round=clean["round"],
            changed_mind=clean["changed_mind"], relayed=clean["relayed"],
            relayed_by=clean["relayed_by"], probe_answers=clean["probe_answers"],
        )
        answer.edit_key_once = edit_key
        self.answers.setdefault(pulse_id, []).append(answer)
        self._answer_by_edit_key[answer.edit_key_hash] = answer.id
        return answer

    def take_edit_key(self, answer: Answer) -> str | None:
        """The key minted with the answer, handed out once: to the response that committed it.
        Reading it clears it, so nothing in the store holds the key afterwards -- only its hash,
        which cannot be turned back into the handle."""
        key = answer.edit_key_once
        answer.edit_key_once = None
        return key

    def _commitment(self, pulse_id: str, clean: dict, committed_at: str, version: int,
                    salt: str) -> str:
        payload = {
            "pulse_id": pulse_id, "version": version, "committed_at": committed_at,
            "mask": clean["mask"], "stance": clean["stance"],
            "likelihood_word": clean["likelihood_word"], "probability": clean["probability"],
            "confidence": clean["confidence"], "panel_share_yes": clean["panel_share_yes"],
            "missing": clean["missing"], "against": clean["against"],
            "trigger_pick": clean["trigger_pick"], "source_tag": clean["source_tag"],
            "round": clean["round"],
            # In the commitment too. An answer whose follow-ups could be edited after the fact
            # while the hash still matched would make the commitment prove less than it says.
            "probe_answers": clean["probe_answers"],
        }
        return commit(payload, salt)

    def find_answer(self, pulse_id: str, expert_id: str, edit_key: str | None) -> "Answer | None":
        """How a correction finds the answer it replaces.

        With an edit key, by the key: that is the only route to an answer under the 'no identity
        kept' mask, because such an answer stores no expert id and the server must not keep a
        token-to-answer map that would reconstruct one. The key is minted once and returned in the
        confirmation; only its hash is stored here.

        Without a key, by expert id, which exists for the other two masks."""
        if edit_key:
            answer_id = self._answer_by_edit_key.get(
                hashlib.sha256(edit_key.encode("utf-8")).hexdigest())
            for answer in self.answers.get(pulse_id, []):
                if answer.id == answer_id:
                    return answer
            return None
        if not expert_id:
            return None
        for answer in self.answers.get(pulse_id, []):
            if answer.expert_id == expert_id:
                return answer
        return None

    def correct(self, answer: Answer, body: dict, salt: str) -> Answer:
        """PUT /e/{token}/answer, allowed until pulse.expires_at. Every version is kept."""
        clean = self.normalise(body)
        if clean["mask"] != answer.mask:
            # Changing the mask on a committed answer would rewrite who could already have seen
            # what. The card says the mask is changeable by reply, which is a conversation with
            # the analyst, not a silent overwrite here.
            raise ValueError("the mask cannot be changed by a correction; reply to the analyst "
                             "and the answer will be withdrawn and re-taken")
        answer.previous_versions.append(answer.snapshot())
        corrected_at = now()
        answer.version += 1
        answer.corrected_at = corrected_at
        answer.committed_at = corrected_at
        answer.commitment = self._commitment(answer.pulse_id, clean, corrected_at,
                                             answer.version, salt)
        for name in ("stance", "likelihood_word", "probability", "probability_source",
                     "confidence", "confidence_word", "panel_share_yes", "missing",
                     "against", "trigger_pick", "source_tag", "changed_mind",
                     "probe_answers"):
            setattr(answer, name, clean[name])
        return answer

    def confirm_relayed(self, answer: Answer) -> Answer:
        """POST /e/{token}/relayed-confirm. A relayed answer counts only after this."""
        if not answer.relayed:
            raise ValueError("this answer was not relayed; there is nothing to confirm")
        answer.confirmed_by_expert_at = now()
        return answer

    def n_answers(self, pulse_id: str) -> int:
        return len(self.answers.get(pulse_id, []))

    def tray(self, pulse_id: str) -> list[dict]:
        """The analyst's envelope tray before a reveal: sealed envelopes, no values."""
        return [a.public_view() for a in self.answers.get(pulse_id, [])]

    # -- reveal -----------------------------------------------------------------
    def reveal(self, pulse_id: str, risk: dict | None = None,
               reason: str = "deadline") -> dict:
        """Reveal at the deadline (section 6a as revised in v3.4).

        The moment is `pulse.expires_at`, fixed when the pulse was sent and printed on the card.
        It is never "when five are in": that would let the arrival of one more answer decide when
        the round closes, and a reminder is not allowed to carry that signal. An analyst can only
        reveal after the deadline, and a reveal before it -- which the demo uses -- is recorded as
        such in the result, so no screen can show a deadline reveal that was not one.

        Under k_min the round goes to `insufficient_panel`: the answers are kept, nothing is
        aggregated and nothing is revealed, not even to the analyst."""
        answers = self.answers.get(pulse_id, [])
        counting = [a for a in answers if a.counts()]
        pulse = self.pulses.get(pulse_id) or {}
        expires_at = pulse.get("expires_at")
        if expires_at and reason != "analyst_before_deadline" and not past(expires_at):
            raise TooEarly(expires_at)
        if len(counting) < self.k_min:
            held = len(answers) - len(counting)
            attempt = {
                "pulse_id": pulse_id,
                "reveal_status": "insufficient_panel",
                "n": len(counting),
                "k_min": self.k_min,
                "held_for_confirmation": held,
                "attempted_at": now(),
                "revealed_reason": reason,
                "message": (f"{len(counting)} answers counted; this round needs {self.k_min}. "
                            "The answers are kept and nothing is revealed, to anyone."),
                "means": ("An insufficient panel is a result about us, not about the risk: too few "
                          "of the eight answered to say anything about the question."),
            }
            if held:
                attempt["message"] += (f" {held} relayed answer(s) are held until the expert "
                                       "confirms through their own link.")
            self.reveal_attempts[pulse_id] = attempt
            if pulse:
                pulse["reveal_status"] = "insufficient_panel"
            return attempt
        revealed_at = now()
        for answer in counting:
            answer.revealed_at = revealed_at
        result = self._aggregate(pulse_id, counting, revealed_at, risk or {})
        result["reveal_status"] = "revealed"
        result["revealed_reason"] = reason
        result["reidentification_note"] = REIDENTIFICATION_NOTE
        self.results[pulse_id] = result
        self._fill_verification_queue(pulse_id, counting, result)
        result["verification_queue_count"] = len(self.verification_queue.get(pulse_id, []))
        self.reveal_attempts.pop(pulse_id, None)
        if pulse:
            pulse["reveal_status"] = "revealed"
        return result

    # -- the verification queue -------------------------------------------------
    def _fill_verification_queue(self, pulse_id: str, answers: list[Answer],
                                 result: dict) -> None:
        """Distinctive free text does not go in the round result (section 6a as revised).

        A line only one person wrote is the line most likely to identify its author in a panel of
        eight, and it is also the line most worth checking. So it goes here, behind an attributed
        read, with its source tag and its corroboration status -- and the public result carries
        only the count."""
        shared = {theme["theme"] for theme in result.get("missing_themes", [])
                  if theme.get("count", 0) > 1}
        status_of = {theme["theme"]: theme.get("corroboration", "not checked")
                     for theme in result.get("missing_themes", [])}
        queue: list[dict] = []
        for answer in answers:
            for kind, text in answer.written_lines():
                if kind == "missing" and any(
                        SequenceMatcher(None, text.lower(), theme.lower()).ratio() >= 0.6
                        for theme in shared):
                    continue   # a theme several people raised; it is in missing_themes already
                queue.append({
                    "id": f"VQ-{len(queue) + 1:03d}",
                    "pulse_id": pulse_id,
                    "kind": kind,
                    "text": text,
                    "source_tag": answer.source_tag,
                    "corroboration": status_of.get(text, "not checked"),
                    "author": {"mask": answer.mask,
                               "pseudonym": answer.pseudonym if answer.mask == "pseudonym" else None},
                    "status": "to_verify",
                })
        self.verification_queue[pulse_id] = queue

    def read_verification_queue(self, pulse_id: str, who: str, why: str) -> list[dict]:
        """Every read is attributed and logged, like a registry read. An unattributed read is
        refused rather than logged as unknown: 'who read this' with no answer is not a log."""
        who, why = (who or "").strip(), (why or "").strip()
        if not who or not why:
            raise ValueError("a verification-queue read needs who and why; "
                             "an unattributed read is refused")
        self.queue_access_log.append({"pulse_id": pulse_id, "who": who, "why": why,
                                      "at": now(),
                                      "n_entries": len(self.verification_queue.get(pulse_id, []))})
        return self.verification_queue.get(pulse_id, [])

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
            "weighted_mean": weighted_mean,
            "sp_experiment": _sp_experiment(estimates),
            "dissent_index": round(_iqr(probabilities), 4) if probabilities else None,
            "distribution": distribution,
            "agreement_by_region": self._agreement_by_region(estimates),
            "missing_themes": _missing_themes(answers),
            "abstentions": [
                {"stance": stance, "count": sum(1 for a in answers if a.stance == stance)}
                for stance in ("outside_my_expertise", "not_enough_evidence")
            ],
            "disagreement": _disagreement(estimates, mean),
            "probe_summary": _probe_summary(answers),
            "missing_evidence": _missing_evidence(answers),
            "number_note": _number_note(estimates),
            "relayed_share": round(sum(1 for a in answers if a.relayed) / len(answers), 4),
            "corrections": sum(1 for a in answers if a.version > 1),
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
                if ratio >= SHARED_ORIGIN_RATIO:
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


def _probe_summary(answers: list[Answer]) -> list[dict]:
    """What the card's closed follow-ups came back as, per question.

    Counts of chosen options, which is a coverage signal for the analyst: whether the panel reads
    ACAPS's own rationale as still true, which sector they think is driving it, how large they
    expected the exposure to be. Moderator-only, like the integrity notes -- these are small
    counts on a panel of eight, and a one-of-eight option count published beside a distinctive
    free-text line is the pair that identifies somebody."""
    tally: dict[str, dict[str, int]] = {}
    for answer in answers:
        for key, value in (answer.probe_answers or {}).items():
            if isinstance(value, list):
                chosen = [str(item) for item in value][:1]   # a ranking: only the top choice
            elif isinstance(value, str) and " " not in value.strip():
                chosen = [value.strip()]                     # a chosen option, not a sentence
            else:
                continue
            for option in chosen:
                tally.setdefault(key, {})[option] = tally.setdefault(key, {}).get(option, 0) + 1
    out = []
    for probe, counts in sorted(tally.items()):
        out.append({
            "probe": probe,
            "n": sum(counts.values()),
            "options": [{"option": option, "count": count}
                        for option, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))],
        })
    return out


def _number_note(estimates: list[Answer]) -> str:
    """Says which numbers the mean was made of. A word is never silently turned into a point
    (section 4), so if any of these answers was a word, the payload that carries the mean says so
    and how many."""
    words = sum(1 for a in estimates if a.probability_source == "band_midpoint")
    exact = sum(1 for a in estimates if a.probability_source == "exact")
    if not estimates:
        return "No estimates on this round; there is no mean."
    if not words:
        return f"All {exact} estimates were given as exact percentages."
    if not exact:
        return (f"All {words} estimates were given as one of the five words; the mean uses each "
                "band's midpoint, which is an assumption about what the word meant.")
    return (f"{exact} estimates were exact percentages and {words} were one of the five words; "
            "for those the mean uses the band midpoint, which is an assumption.")


def _themes_in(text: str) -> list[str]:
    lowered = text.lower()
    return [theme for theme, words in TRIGGER_THEMES.items()
            if any(word in lowered for word in words)]


def _count_word(n: int) -> str:
    return ("no", "one", "two", "three", "four", "five", "six", "seven", "eight")[n] if n <= 8 else str(n)


def _disagreement(estimates: list[Answer], mean: float | None) -> list[dict]:
    """The disagreement column of the reveal view (section 6a as revised in v3.4).

    Unattributed, and written from themes rather than from anyone's sentence: in a panel of eight
    a quoted line identifies its author to colleagues, which is exactly the harm the mask was
    chosen to avoid. So the summary names the direction, the count and the subject the notes were
    about, and the sentences themselves go to the verification queue."""
    if mean is None or not estimates:
        return []
    out = []
    for position, group in (
        ("lower", [a for a in estimates if mean - a.probability >= DISAGREEMENT_MARGIN]),
        ("higher", [a for a in estimates if a.probability - mean >= DISAGREEMENT_MARGIN]),
    ):
        if not group:
            continue
        themes: dict[str, int] = {}
        for answer in group:
            for theme in _themes_in(f"{answer.missing} {answer.against}"):
                themes[theme] = themes.get(theme, 0) + 1
        ranked = sorted(themes, key=lambda t: (-themes[t], t))[:2]
        noun = "expert" if len(group) == 1 else "experts"
        verb = "puts" if len(group) == 1 else "put"
        line = (f"{_count_word(len(group)).capitalize()} {noun} {verb} the chance "
                f"{'below' if position == 'lower' else 'above'} the panel mean")
        # A lone dissenter gets the direction and nothing else. "One expert, and their note was
        # about displacement" is the sentence our own re-identification warning is about: in a
        # panel of eight the subject narrows it to a person. Two or more is a position; one is a
        # colleague, and the theme stays in the access-logged queue with the text.
        if ranked and len(group) > 1:
            line += f"; their notes are about {' and '.join(ranked)}."
        elif len(group) == 1:
            line += "; the subject of their note is not summarised here, because in a panel of "
            line += "eight it would name them."
        else:
            line += " and gave no written reason."
        out.append({
            "position": position,
            "n": len(group),
            "summary": line,
            "written_from": "themes",
            "distance_from_mean": round(
                max(abs(a.probability - mean) for a in group), 4),
        })
    return out


def _missing_evidence(answers: list[Answer]) -> list[dict]:
    """The missing-evidence column: what the panel said it could not see, as themes with counts.
    ACAPS's own brief calls the opposite failure 'absence of evidence'; this is the column that
    keeps it on the screen instead of in a footnote.

    Only themes two or more people raised. A line one person wrote is the line that identifies
    its author in a panel of eight, so it goes to the access-logged verification queue and this
    column carries the count of those instead of their text."""
    clusters = _missing_themes(answers)
    out = [{"theme": cluster["theme"], "n": cluster["count"]}
           for cluster in clusters if cluster["count"] > 1]
    singles = sum(1 for cluster in clusters if cluster["count"] == 1)
    if singles:
        out.append({"theme": f"{singles} raised by one expert each, held for verification",
                    "n": singles, "in_queue": True})
    return out


def _missing_themes(answers: list[Answer]) -> list[dict]:
    """Cluster the free-text 'what are we missing' lines. Corroboration stays 'not checked' until
    something actually checks it -- the word is a status, not a compliment."""
    clusters: list[dict] = []
    written = [(answer, text) for answer in answers
               for kind, text in answer.written_lines() if kind != "against"]
    for answer, text in written:
        for cluster in clusters:
            if SequenceMatcher(None, cluster["theme"].lower(), text.lower()).ratio() >= 0.6:
                cluster["count"] += 1
                cluster["tags"].append(answer.source_tag)
                cluster["texts"].append(text)
                break
        else:
            clusters.append({"theme": text, "count": 1, "tags": [answer.source_tag],
                             "texts": [text]})

    out = []
    for cluster in sorted(clusters, key=lambda c: c["count"], reverse=True):
        tags = [tag for tag in cluster.pop("tags") if tag]
        texts = cluster.pop("texts")
        # Two people repeating the same sentence are one origin. Calling that corroborated while
        # the integrity notes call it a shared origin would be the system contradicting itself in
        # two panels of the same screen, so the stricter reading wins.
        repeated = any(
            SequenceMatcher(None, a.lower(), b.lower()).ratio() >= SHARED_ORIGIN_RATIO
            for index, a in enumerate(texts) for b in texts[index + 1:]
        )
        corroboration = "not checked"
        if repeated:
            corroboration = "single-source"
        elif cluster["count"] >= 2 and any(tag == "saw" for tag in tags):
            corroboration = "corroborated"
        elif cluster["count"] >= 2:
            corroboration = "single-source"
        single = cluster["count"] == 1
        out.append({
            **cluster,
            # A theme only one person raised keeps its count and its status and loses its words.
            # The sentence is in the verification queue, behind an attributed read, because in a
            # panel of eight it names the person who wrote it.
            "theme": ("held in the verification queue (one expert)" if single
                      else cluster["theme"]),
            "text_withheld": single,
            "in_queue": single,
            "origin": "many" if cluster["count"] > 1 else "single",
            "corroboration": corroboration,
        })
    return out
