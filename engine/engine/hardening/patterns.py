"""Section 6d: pattern reports about panels, never about people.

v3.4 removed per-expert reports from the committee view. The reason is in the section itself: no
measurement of a person may be hidden inside a pulse, and a sentence about one expert, written
from answers they gave to a question that never said it was measuring them, is exactly that. So
this module reads a panel's rounds and says things about the panel.

The rules, once:

* every sentence is about the panel or about an affiliation group with at least three members on
  it, never about an individual, and never contains a pseudonym;
* descriptive, never causal -- "UN-affiliated answers sat above the mean on 3 of 4 pulses" is
  allowed, "UN experts are optimistic" is not;
* nothing at all until the panel has three revealed rounds;
* free text is counted (its source tag, whether a reason was given) and never quoted or scored.

Individual calibration exists only inside the consent-gated programme: the expert is told what is
measured, opts in, and sees their own report before anyone else. That lives in `calibration.py`.
"""
from __future__ import annotations
import statistics

MIN_PULSES = 3
# An affiliation group smaller than this is merged: three is the smallest group where a sentence
# is about a group rather than about the one or two people in it.
MIN_PER_AFFILIATION = 3
# A source tag or a direction has to hold this share of the answers before it is worth a sentence.
DOMINANT_SHARE = 0.5
# Below this the spread "did not change much": two rounds of eight answers move by small amounts
# for no reason worth reporting.
SPREAD_MOVE = 0.05

NEVER = ("Never about a person. Never a score. Never public. Never a reason to approve or remove "
         "anyone in the pilot. Free text is counted, never quoted.")

THEME_LABELS = {
    "displacement": "displacement", "conflict": "conflict", "flood": "flood",
    "food": "food security", "epidemic": "epidemic", "access": "humanitarian-access",
    "political": "political", "economic": "economic",
}


def _spread_of(result: dict) -> float | None:
    spread = result.get("spread") or {}
    if spread.get("max") is None or spread.get("min") is None:
        return None
    return round(spread["max"] - spread["min"], 4)


def _plural(n: int, singular: str, plural: str | None = None) -> str:
    return singular if n == 1 else (plural or f"{singular}s")


def report(store, panel_id: str) -> dict:
    """One PanelPattern. `store` is the live Store; nothing is read from outside it."""
    pulses = [p for p in store.pulses.values() if p.get("panel_id") == panel_id]
    pulses.sort(key=lambda p: p.get("fired_at") or "")
    pulse_ids = [p["id"] for p in pulses]
    revealed = [pid for pid in pulse_ids if pid in store.results]
    answers = [a for pid in pulse_ids for a in store.answers.get(pid, [])]
    # Who sat on this panel: everyone issued a link for one of its rounds, plus anyone whose
    # answer carries an id. The second half matters because a round can be seeded or relayed
    # without a link, and a panel of eight that reports "0 experts" is a bug the reader cannot
    # see past. An answer under the 'no identity kept' mask adds nobody, which is the point of it.
    expert_ids = {expert for pid, expert in store.tokens.values() if pid in pulse_ids}
    expert_ids |= {a.expert_id for a in answers if a.expert_id}

    base = {
        "panel_id": panel_id,
        "n_pulses": len(pulse_ids),
        "n_pulses_revealed": len(revealed),
        "n_experts": len(expert_ids),
        "never_per_person": True,
        "never": NEVER,
    }
    if len(revealed) < MIN_PULSES:
        return {
            **base,
            "sentences": [],
            "by_affiliation": [],
            "note": (f"A panel report opens after {MIN_PULSES} revealed rounds; this panel has "
                     f"{len(revealed)}. Nothing is computed before then, because two rounds of "
                     "eight answers will show a pattern whether or not one is there."),
        }

    sentences: list[str] = []
    for builder in (_convergence, _spread_over_time, _abstentions, _source_mix, _coverage):
        line = builder(store, revealed, answers, pulses, expert_ids)
        if line:
            sentences.append(line)

    return {
        **base,
        "sentences": sentences,
        "by_affiliation": _by_affiliation(store, revealed, expert_ids),
        "note": ("Descriptive sentences about this panel. An empty list is the honest output when "
                 "nothing stands out."),
    }


def _convergence(store, revealed, answers, pulses, expert_ids) -> str | None:
    """ACAPS's brief calls it groupthink: did the second round move toward the first round's mean?
    Counted, with how many of those moves came with a written reason -- a revision with a reason
    is a different event from a revision without one, and the sentence does not decide which."""
    moved, with_reason, considered = 0, 0, 0
    for pulse_id in revealed:
        result = store.results[pulse_id]
        mean = result.get("mean")
        if mean is None:
            continue
        rounds = {1: [], 2: []}
        for answer in store.answers.get(pulse_id, []):
            if answer.probability is not None and answer.round in rounds:
                rounds[answer.round].append(answer)
        if not rounds[2]:
            continue
        considered += 1
        before = statistics.fmean([abs(a.probability - mean) for a in rounds[1]]) if rounds[1] else None
        after = statistics.fmean([abs(a.probability - mean) for a in rounds[2]])
        if before is not None and after < before:
            moved += 1
            with_reason += sum(1 for a in rounds[2] if a.changed_mind and a.missing.strip())
    if not considered:
        return None
    if not moved:
        return (f"Round-2 answers did not move toward the mean on any of {considered} "
                f"{_plural(considered, 'pulse')} with a second round.")
    line = (f"Round-2 answers moved toward the mean on {moved} of {considered} "
            f"{_plural(considered, 'pulse')}")
    if with_reason:
        line += (f"; {with_reason} of those revisions came with a new written reason.")
    else:
        line += "; none of those revisions came with a written reason."
    return line


def _spread_over_time(store, revealed, answers, pulses, expert_ids) -> str | None:
    recent = [s for s in (_spread_of(store.results[pid]) for pid in revealed[-3:])
              if s is not None]
    if len(recent) < 2:
        return None
    first, last = recent[0], recent[-1]
    span = f"over the last {len(recent)} revealed {_plural(len(recent), 'round')}"
    if abs(last - first) < SPREAD_MOVE:
        return f"The spread stayed close to {last:.2f} {span}."
    direction = "narrowed" if last < first else "widened"
    return f"The spread {direction} from {first:.2f} to {last:.2f} {span}."


def _abstentions(store, revealed, answers, pulses, expert_ids) -> str | None:
    counted = [a for a in answers if a.pulse_id in revealed]
    if not counted:
        return None
    abstained = sum(1 for a in counted if a.stance != "estimate")
    if not abstained:
        return f"Every one of the {len(counted)} answers carried an estimate; none abstained."
    return (f"{abstained} of {len(counted)} answers were abstentions "
            f"(‘outside my area’ or ‘not enough evidence’), which are real "
            "answers here and are never scored.")


def _source_mix(store, revealed, answers, pulses, expert_ids) -> str | None:
    tagged = [a.source_tag for a in answers
              if a.pulse_id in revealed and a.missing.strip() and a.source_tag]
    if not tagged:
        return None
    counts = {tag: tagged.count(tag) for tag in set(tagged)}
    top = max(counts, key=lambda tag: (counts[tag], tag))
    if counts[top] / len(tagged) < DOMINANT_SHARE:
        return (f"The free text was tagged across all three sources: "
                + ", ".join(f"{counts[tag]} {tag}" for tag in sorted(counts)) + ".")
    return (f"{counts[top]} of {len(tagged)} free-text lines were tagged ‘{top}’.")


def _coverage(store, revealed, answers, pulses, expert_ids) -> str | None:
    """Which expertise this panel does not have, across the risks it was actually asked about.
    The same signal as the per-round coverage note, read over the panel's whole history."""
    from .. import data
    from ..store import _theme_of_trigger
    needed: set[str] = set()
    for pulse in pulses:
        if pulse["id"] not in revealed:
            continue
        risk = data.get_risk(pulse["risk_id"]) or {}
        for trigger in risk.get("triggers") or []:
            theme = _theme_of_trigger(trigger)
            if theme:
                needed.add(theme)
    held: set[str] = set()
    for expert_id in expert_ids:
        expert = store.experts.get(expert_id)
        if expert:
            held.update(expert.theme_tags)
    gaps = sorted(needed - held)
    if not gaps:
        return None
    labels = [THEME_LABELS.get(theme, theme) for theme in gaps]
    return (f"This panel has no {labels[0]} expert." if len(labels) == 1 else
            f"This panel has no expert tagged {', '.join(labels[:-1])} or {labels[-1]}.")


def _by_affiliation(store, revealed, expert_ids) -> list[dict]:
    """Affiliation-level sentences, and only where the affiliation has three members on the panel.
    Everything smaller is merged and says so: a sentence about the two people from one
    organisation is a sentence about those two people."""
    groups: dict[str, list[str]] = {}
    for expert_id in expert_ids:
        expert = store.experts.get(expert_id)
        tag = (expert.affiliation_tag if expert else "") or "unrecorded"
        groups.setdefault(tag, []).append(expert_id)

    out, merged = [], []
    for tag, members in sorted(groups.items()):
        if len(members) < MIN_PER_AFFILIATION:
            merged.extend(members)
            continue
        above, considered = 0, 0
        for pulse_id in revealed:
            result = store.results[pulse_id]
            mean = result.get("mean")
            if mean is None:
                continue
            theirs = [a.probability for a in store.answers.get(pulse_id, [])
                      if a.expert_id in members and a.probability is not None]
            if not theirs:
                continue
            considered += 1
            if statistics.fmean(theirs) > mean:
                above += 1
        if not considered:
            continue
        if above == 0:
            sentence = (f"{tag}-affiliated answers sat at or below the panel mean on all "
                        f"{considered} {_plural(considered, 'pulse')}.")
        elif above == considered:
            sentence = (f"{tag}-affiliated answers sat above the panel mean on all "
                        f"{considered} {_plural(considered, 'pulse')}.")
        else:
            sentence = (f"{tag}-affiliated answers sat above the panel mean on {above} of "
                        f"{considered} {_plural(considered, 'pulse')}.")
        out.append({"affiliation_tag": tag, "n": len(members), "sentence": sentence})
    if merged:
        out.append({"affiliation_tag": "merged", "n": len(merged),
                    "sentence": (f"{len(merged)} panel members are in affiliation groups below "
                                 f"n = {MIN_PER_AFFILIATION} and are merged; no sentence is "
                                 "written about them.")})
    return out
