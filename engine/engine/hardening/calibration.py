"""Section 6d: the consent-gated calibration programme. `FF_CALIBRATION`, default off.

This is the only place in the build where anything is measured about an individual, and it is
built so that nobody can be measured without having read what is measured and said yes:

* enrolment is separate from any panel. The expert receives one paragraph -- what is asked, how
  often, what is computed, who sees it, that they see it first, that they can switch it off -- and
  consents by one reply. The consent is versioned, and a disclosure change needs a fresh consent.
* items are short factual questions whose answer ACAPS already holds, taken from the resolved
  risks in the export, each carrying the record it is adjudicated against. They are sent on their
  own, never inside a pulse card.
* a numeric confidence prompt, 50 to 100 %, comes with each item. That is what makes a calibration
  curve mean anything; three confidence words against right/wrong items do not.
* a report exists only after 20 items, goes to the expert first and alone, and is one paragraph
  in plain words. The committee sees it only after a second, separate opt-in, and never as a
  weight on anything.
* `off` at any time, and off means the report stops being produced, not hidden.

Deliberately not built, and recommended against in the design doc: fictitious references
(overclaiming foils), response-time and edit-count measures, test-retest traps. Nothing a
participant would recognise as deception if it were explained to them afterwards.
"""
from __future__ import annotations
import statistics
from dataclasses import dataclass, field

DISCLOSURE_VERSION = "2026-11-07.1"
DISCLOSURE = (
    "We would like to check how well your confidence matches your accuracy. If you join, we will "
    "send you at most two short questions a month, on their own and never inside a panel "
    "question. Each is about something ACAPS already has a record of, and we ask how sure you are "
    "on a scale from 50 to 100 %. After 20 questions we write you one paragraph in plain words -- "
    "for example, 'when you said 90 % you were right about 7 times in 10'. You see it before "
    "anyone at ACAPS does, and the committee sees it only if you then say yes a second time. It "
    "is never used as a weight on your answers, never shown to other experts, and never a reason "
    "to approve or remove anyone. Reply STOP to this message at any time and we stop computing it."
)
MIN_ITEMS = 20
CONFIDENCE_PROMPT = "How sure are you that this is right, 50 to 100 %?"
NEVER = ("Never without consent. Never a weight. Never to the committee before the expert. Never "
         "a reason to approve or remove anyone.")


@dataclass
class Enrolment:
    expert_internal_id: str
    consented_at: str
    disclosure_version: str
    answers: list[dict] = field(default_factory=list)
    report_off: bool = False
    shared_with_committee: bool = False

    @property
    def items_answered(self) -> int:
        return len(self.answers)

    @property
    def report_available(self) -> bool:
        return self.items_answered >= MIN_ITEMS and not self.report_off

    def as_dict(self) -> dict:
        return {
            "expert_internal_id": self.expert_internal_id,
            "consented_at": self.consented_at,
            "disclosure_version": self.disclosure_version,
            "items_answered": self.items_answered,
            "report_available": self.report_available,
            "report_off": self.report_off,
            "shared_with_committee": self.shared_with_committee,
            "items_still_needed": max(0, MIN_ITEMS - self.items_answered),
        }


class Programme:
    """Enrolments and answered items. Keyed by internal expert id and never by pseudonym: a
    pseudonym is what peers see, and this is not peer-facing at all."""

    def __init__(self) -> None:
        self.enrolments: dict[str, Enrolment] = {}

    def enrol(self, expert_internal_id: str, consent: bool, disclosure_version: str,
              at: str) -> Enrolment:
        if not consent:
            raise ValueError("enrolment needs an explicit yes; silence is not consent")
        if disclosure_version != DISCLOSURE_VERSION:
            raise ValueError(
                f"this consent is against disclosure {disclosure_version}; the current one is "
                f"{DISCLOSURE_VERSION}. Consent does not carry across a change to what we measure.")
        existing = self.enrolments.get(expert_internal_id)
        if existing and existing.disclosure_version == disclosure_version:
            existing.report_off = False
            return existing
        enrolment = Enrolment(expert_internal_id, at, disclosure_version)
        self.enrolments[expert_internal_id] = enrolment
        return enrolment

    def get(self, expert_internal_id: str) -> Enrolment | None:
        return self.enrolments.get(expert_internal_id)

    def switch_off(self, expert_internal_id: str) -> Enrolment:
        enrolment = self.enrolments.get(expert_internal_id)
        if not enrolment:
            raise ValueError("there is nothing to switch off; this expert is not enrolled")
        enrolment.report_off = True
        enrolment.shared_with_committee = False
        return enrolment

    def record(self, expert_internal_id: str, item: dict, answer: str,
               confidence: int, at: str) -> Enrolment:
        enrolment = self.enrolments.get(expert_internal_id)
        if not enrolment:
            raise ValueError("this expert is not enrolled in the calibration programme")
        if not 50 <= int(confidence) <= 100:
            raise ValueError("confidence is a percentage from 50 to 100")
        enrolment.answers.append({
            "item_id": item["id"],
            "risk_id": item["risk_id"],
            "answer": answer,
            "correct": answer == item["known_answer"],
            "confidence": int(confidence),
            "answered_at": at,
            "source_record": item["source_record"],
        })
        return enrolment

    def counts(self) -> dict:
        """What the committee view may see: counts, no names, no reports."""
        enrolled = list(self.enrolments.values())
        return {
            "enrolled": len(enrolled),
            "reports_available": sum(1 for e in enrolled if e.report_available),
            "switched_off": sum(1 for e in enrolled if e.report_off),
            "shared_with_committee": sum(1 for e in enrolled if e.shared_with_committee),
            "disclosure_version": DISCLOSURE_VERSION,
            "min_items": MIN_ITEMS,
            "means": ("Counts only. A report belongs to the expert, and reaches the committee only "
                      "if that expert says yes a second time."),
        }


def items_from_resolved(risks: list[dict], limit: int = 40) -> list[dict]:
    """Items whose answer ACAPS already holds: did this resolved risk materialise?

    They come from the export's own resolved rows, so every item carries the record it is scored
    against and nothing is invented. A question we made up would be a question with no adjudicator.
    """
    items = []
    for risk in risks:
        # ACAPS's own Status column, which is the field the Risk List resolves a risk with. The
        # "What materialised?" column is a description of what happened, not a verdict, so it is
        # not what an item is adjudicated against.
        status = (risk.get("status") or "").strip().lower()
        if status not in ("materialised", "not materialised"):
            continue
        materialised = "yes" if status == "materialised" else "no"
        items.append({
            "id": f"CI-{risk['risk_id']}",
            "risk_id": risk["risk_id"],
            "question": (f"Did this risk materialise within its horizon? ‘{risk['title']}’ "
                         f"({risk.get('country') or risk.get('country_iso')})"),
            "options": ["yes", "no"],
            "known_answer": materialised,
            "source_record": f"ACAPS Risk List export, {risk['risk_id']}, Status column",
            "confidence_prompt": CONFIDENCE_PROMPT,
        })
        if len(items) >= limit:
            break
    return items


def report(enrolment: Enrolment) -> dict:
    """One paragraph in plain words, for the expert. No score, no league table, no weight.

    The sentence form is the one from the design: "when you said 90 % you were right about 7 times
    in 10". Buckets with fewer than three answers are not reported -- one answer at 70 % is not a
    hit rate."""
    if enrolment.report_off:
        raise ValueError("this expert switched the report off")
    if enrolment.items_answered < MIN_ITEMS:
        raise ValueError(f"a report opens after {MIN_ITEMS} items; this one has "
                         f"{enrolment.items_answered}")
    buckets: dict[int, list[dict]] = {}
    for answer in enrolment.answers:
        buckets.setdefault(min(int(answer["confidence"]) // 10 * 10, 90), []).append(answer)
    lines, rows = [], []
    for floor in sorted(buckets):
        group = buckets[floor]
        hit = sum(1 for a in group if a["correct"]) / len(group)
        rows.append({"confidence_band": f"{floor}-{floor + 9} %", "n": len(group),
                     "share_correct": round(hit, 4)})
        if len(group) >= 3:
            lines.append(f"when you said about {floor} % you were right about "
                         f"{round(hit * 10)} times in 10")
    overall = statistics.fmean(
        [(a["confidence"] / 100 - (1.0 if a["correct"] else 0.0)) ** 2
         for a in enrolment.answers])
    return {
        "items_answered": enrolment.items_answered,
        "paragraph": ("Over your " + str(enrolment.items_answered) + " answers, "
                      + ("; ".join(lines) if lines else
                         "no confidence band has three answers yet, so there is nothing to say "
                         "about any of them")
                      + "."),
        "by_confidence": rows,
        "brier": round(overall, 4),
        "brier_note": ("A Brier score over factual items, not over forecasts. Lower is better and "
                       "0.25 is what answering every item at 50 % would give you."),
        "who_sees_this": ("You, first and alone. The committee sees it only if you say yes a "
                          "second time, and never as a weight."),
        "never": NEVER,
    }
