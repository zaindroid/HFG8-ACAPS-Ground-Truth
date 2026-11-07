"""A tolerant parser for replies, English and French.

The order of reading matters and is deliberate:

1. STOP and PAUSE words first. Somebody who writes "stop, wrong person" has opted out, and
   reading a number out of the rest of that sentence would record an answer from a person who
   just asked not to be asked.
2. Abstention phrases next. "Outside my area" is a complete answer (section 8) and must not be
   turned into a probability by a parser that found a stray number in the same line.
3. Then the number: a percentage, a bare 0-100, a decimal, a keypad 1-5, a spelled-out number in
   either language, or one of the five words.
4. Then the extras: confidence, mask words, and the free line.

Anything it cannot read, it says so about. `Parsed.needs_analyst` is the flag the desk reads; the
original text always travels with it.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

PARSED_FIELDS = ("stance", "likelihood_word", "probability", "confidence", "mask", "missing")

STOP_WORDS = ("stop", "unsubscribe", "arretez", "arreter", "desabonner", "no more")
PAUSE_WORDS = ("pause", "later", "plus tard", "hold off", "not now")
# Abstentions are read before numbers, so a stray figure in the sentence cannot overrule them.
OUTSIDE_WORDS = ("outside my area", "outside my expertise", "not my area", "not my field",
                 "pas mon domaine", "hors de mon domaine", "wrong person", "cannot help")
NOT_ENOUGH_WORDS = ("not enough evidence", "no evidence", "cannot say", "can't say", "no idea",
                    "pas assez", "je ne sais pas", "too early to say", "dont know", "don't know")
WORDS = {
    "very unlikely": "very_unlikely", "tres improbable": "very_unlikely",
    "very likely": "very_likely", "tres probable": "very_likely",
    "unlikely": "unlikely", "improbable": "unlikely",
    "likely": "likely", "probable": "likely",
    "even": "even", "fifty fifty": "even", "50/50": "even", "egal": "even",
    "moitie": "even",
}
# Keypad and five-point replies: "4", "4 likely", "press 4".
KEYPAD = {1: "very_unlikely", 2: "unlikely", 3: "even", 4: "likely", 5: "very_likely"}
MIDPOINTS = {"very_unlikely": 0.05, "unlikely": 0.22, "even": 0.5, "likely": 0.78,
             "very_likely": 0.95}
SPELLED = {
    "zero": 0, "ten": 10, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "dix": 10, "vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60,
    "soixante-dix": 70, "quatre-vingts": 80, "quatre-vingt-dix": 90, "cent": 100,
}
CONFIDENCE_WORDS = {
    "not sure": "not sure", "unsure": "not sure", "pas sur": "not sure",
    "fairly sure": "fairly sure", "quite sure": "fairly sure", "assez sur": "fairly sure",
    "very sure": "sure", "sure": "sure", "certain": "sure", "confident": "sure",
}
MASK_WORDS = {
    "anonymous": "anonymous", "no identity": "anonymous", "anonyme": "anonymous",
    "nickname": "pseudonym", "pseudonym": "pseudonym", "pseudonyme": "pseudonym",
    "fine to name me": "known", "you can name me": "known", "name me": "known",
    "vous pouvez me nommer": "known",
}


@dataclass
class Parsed:
    channel: str
    original: str
    act: str = "answer"                 # "answer" | "stop" | "pause" | "unreadable"
    stance: str = "estimate"
    likelihood_word: str | None = None
    probability: float | None = None
    confidence: str | None = None
    mask: str | None = None
    missing: str = ""
    read: list[str] = field(default_factory=list)
    not_read: list[str] = field(default_factory=list)

    @property
    def needs_analyst(self) -> bool:
        return self.act == "unreadable"

    def answer_body(self, default_mask: str = "pseudonym") -> dict:
        """The Answer the engine commits. The mask falls back only when the reply did not say:
        a reply cannot be refused for not repeating a choice the expert already made."""
        return {
            "mask": self.mask or default_mask,
            "stance": self.stance,
            "likelihood_word": self.likelihood_word,
            "probability": self.probability,
            "confidence": self.confidence,
            "missing": self.missing,
            "round": 1,
        }

    def as_dict(self) -> dict:
        return {
            "channel": self.channel,
            "act": self.act,
            "stance": self.stance,
            "likelihood_word": self.likelihood_word,
            "probability": self.probability,
            "confidence_word": self.confidence,
            "mask": self.mask,
            "missing": self.missing,
            "read": self.read,
            "not_read": self.not_read,
            "needs_analyst": self.needs_analyst,
            # The original always travels with the reading of it. A parser's output without the
            # text it came from cannot be checked by the person who has to act on it.
            "original": self.original,
        }


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _fold(text: str) -> str:
    """Lower-case and strip the accents a phone keyboard may or may not have produced."""
    import unicodedata

    folded = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in folded if not unicodedata.combining(c))


def _number(text: str) -> float | None:
    """A probability out of a reply, by the forms people actually use."""
    percent = re.search(r"(\d{1,3})\s*%", text)
    if percent:
        value = int(percent.group(1))
        return value / 100 if 0 <= value <= 100 else None
    decimal = re.search(r"\b0?\.(\d{1,2})\b", text)
    if decimal:
        return float(f"0.{decimal.group(1)}")
    # A bare 1-5 is the keypad and the five-point scale, not a 1 % chance. Handled by the caller
    # as a word, so it is excluded here.
    bare = re.search(r"\b(\d{1,3})\b", text)
    if bare:
        value = int(bare.group(1))
        if 6 <= value <= 100:
            return value / 100
    # Longest first: "soixante-dix" has to win over the "dix" inside it, and a hyphen counts as
    # a word boundary, so the short one matches too.
    for spelled, value in sorted(SPELLED.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<![\w-]){re.escape(spelled)}(?![\w-])", text):
            return value / 100
    return None


def parse(text: str, channel: str = "email") -> Parsed:
    original = _clean(text)
    folded = _fold(original)
    parsed = Parsed(channel=channel, original=original)
    if not folded:
        parsed.act = "unreadable"
        parsed.not_read.append("the message was empty")
        return parsed

    # 1. Opting out comes before anything else in the message.
    for word in STOP_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", folded):
            parsed.act = "stop"
            parsed.read.append(f"a stop word ({word})")
            return parsed
    for word in PAUSE_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", folded):
            parsed.act = "pause"
            parsed.read.append(f"a pause word ({word})")
            return parsed

    # 2. An abstention is a complete answer and is read before any number.
    for phrase in OUTSIDE_WORDS:
        if phrase in folded:
            parsed.stance = "outside_my_expertise"
            parsed.read.append("an abstention: outside their area")
            break
    else:
        for phrase in NOT_ENOUGH_WORDS:
            if phrase in folded:
                parsed.stance = "not_enough_evidence"
                parsed.read.append("an abstention: not enough evidence")
                break

    # 3. The number, unless they abstained.
    if parsed.stance == "estimate":
        for phrase, word in sorted(WORDS.items(), key=lambda kv: -len(kv[0])):
            # On a word boundary: "seventy" contains "even", and a substring match read that as
            # a fifty-fifty answer from somebody who had just said 70 %.
            if re.search(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", folded):
                parsed.likelihood_word = word
                parsed.read.append(f"the word '{phrase}'")
                break
        keypad = re.match(r"^(?:press\s*)?([1-5])\b", folded)
        if keypad and not parsed.likelihood_word:
            parsed.likelihood_word = KEYPAD[int(keypad.group(1))]
            parsed.read.append(f"a keypad answer ({keypad.group(1)})")
        exact = _number(folded)
        if exact is not None:
            word = parsed.likelihood_word
            # A number and a word that disagree: keep the number, drop the word, and say so.
            # The number is the more specific statement, and refusing the whole reply over a
            # mismatch would throw away an answer somebody took the trouble to send.
            if word and not (MIDPOINTS[word] - 0.25 <= exact <= MIDPOINTS[word] + 0.25):
                parsed.not_read.append(
                    f"the word '{word.replace('_', ' ')}' did not match {round(exact * 100)} %, "
                    "so the number was used and the word dropped")
                parsed.likelihood_word = None
            parsed.probability = round(exact, 4)
            parsed.read.append(f"{round(exact * 100)} %")
        if parsed.likelihood_word is None and parsed.probability is None:
            parsed.act = "unreadable"
            parsed.not_read.append("no likelihood, abstention or opt-out could be read")

    # 4. The extras.
    for phrase, value in sorted(CONFIDENCE_WORDS.items(), key=lambda kv: -len(kv[0])):
        if phrase in folded:
            parsed.confidence = value
            parsed.read.append(f"confidence '{value}'")
            break
    for phrase, value in sorted(MASK_WORDS.items(), key=lambda kv: -len(kv[0])):
        if phrase in folded:
            parsed.mask = value
            parsed.read.append(f"a mask choice ({value})")
            break
    # Whatever is left, once the machine-readable parts are taken out, is the free line.
    remainder = original
    for pattern in (r"\d{1,3}\s*%", r"\b0?\.\d{1,2}\b", r"^(?:press\s*)?[1-5]\b",
                    r"\b(?:per\s*cent|percent|pour\s*cent)\b",
                    r"\b(?:and|et)\s+keep\s+me\b"):
        remainder = re.sub(pattern, " ", remainder, flags=re.IGNORECASE)
    for phrase in (sorted(SPELLED, key=len, reverse=True) + list(WORDS)
                   + list(CONFIDENCE_WORDS) + list(MASK_WORDS)):
        remainder = re.sub(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", " ", remainder,
                           flags=re.IGNORECASE)
    remainder = _clean(re.sub(r"[.,;:]+", " ", remainder))
    if len(remainder) > 3:
        parsed.missing = remainder[:240]
        parsed.read.append("a free-text line")
    return parsed
