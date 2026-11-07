# Judging checklist

Lane C. Revised for master prompt v3.2 (7 Nov). Every jury dimension and every MoSCoW row from the organisers' `evaluation-criteria.md` (on `main`), mapped to the exact place we show it. "Where" names a screen from master prompt section 8, a file, or a sentence for the pitch. Status: **covered**, **partial** (works, gap named), **gap** (task in `proposals.md`).

Checked against the design in master prompt v3 and the fixtures in the repo. Lane A and B are still building, so "where" describes the design. Re-run this check at the Sat 20:00 merge.

Claims we do not make (v3 and v3.2): "anonymous from everyone"; "quantum-proof"; "anchored" while the receipt is pending; "signed by ACAPS" while the key is a demo key; "nothing identifying leaves the device"; answers "sealed" from everyone; a fixed 60-second countdown in the product; reliability-weighted headline number; extremizing; "proof"; "earlier than ACAPS"; diagnoses of experts.

## 1. Jury dimensions

| Dimension | What the jury looks for | Where we show it | Status |
|---|---|---|---|
| Problem understanding | Does the team grasp ACAPS's challenge? | Slide 1: "Medium-rated risks materialised 47 % of the time [data: 27 of 58 resolved]." The mentor's facts: no platform, 32 analysts update weekly by hand, "we will get things wrong ... the point is honesty about it." | covered |
| Expert experience | Would a busy expert use it? | `/e/:token`: one card, about a minute, no login, mask picker with a recognition warning, "outside my expertise" and "not enough evidence" options, rating hidden until submission. After resolution: the group outcome report (`GET /pulses/{id}/outcome-report`). | covered; retention beyond the outcome report is thin (P1) |
| Anonymity and trust | Is the model thoughtful and robust? | Who-can-learn-what table (master prompt 1a, `privacy-engineering.md`). Mask per answer echoed on the card. Restricted identity registry, logged access. `anonymous` answers stored without identity. Verify checks timing and consistency only, and says so. Public output is aggregate only; n of 5 or more is a disclosure rule, not an anonymity guarantee. Committee gateway, two-admin approval. Hardening stack, each item shown with its "guarantees / does not" line and only when its flag is on: ML-KEM-768 registry encryption line, registry access log, ML-DSA attestation line and anchor status on each ledger entry, one-time credential line on the `anonymous` card, ZK proof line only if `FF_ZK` is on (`privacy-engineering.md`, `trust-design.md`). | covered; the honesty of the limits is the strength. Do not say "cannot be read", "anonymous from everyone", "quantum-proof" or "anchored" (when pending) on stage. Open question Q-A1: anonymity from ACAPS only holds if the answer is submitted apart from the personal magic link (P21). |
| Feasibility | Could it be piloted with real experts? | Email magic link. ACAPS API with CSV fallback. The Risk Alert Engine runs on ACAPS's own monthly editions, cached for offline use, live with a token. Analyst approves every pulse. Frozen question contract per risk. `make demo` offline. Slide 8: supervised pilot of this workflow, with measures (impact.md 3.6). | partial: contract wording for R1043 needs analyst sign-off (P2) |
| Data use | Does it use the Risk Radar data? | The 84 % / 47 % rates [data]. Brier of the ACAPS Probability band on 99 resolved risks: 0.213 [data; band-to-number mapping is an assumption]. Sensitivity test on the 104 resolved risks (Lane A, repo page and Q&A). R1043 throughout. Alerts page: ACAPS monthly severity and access editions, TCD005 rise 6.1 to 6.9 (largest rise of 123 crises, April 2026) linked to R1043 [data, verified]. Radar view with source badges (API or cache). | covered once Lane A's test lands |
| Innovation | Something new in consultation or forecasting? | The framing in v3: "distinctive for this challenge": a one-minute masked expert loop that publishes its own limitations and misses, with hidden-rating first rounds, descriptive integrity notes and a decision-oriented ledger. We do not say "first". | covered |
| Presentation | Is the 3-minute pitch clear? | `demo-script.md` (timed), `pitch.md`, `slides/` (8 slides). Rehearsal Sat 16:00. | covered once rehearsed |

## 2. MoSCoW rows

### Must have

| Row | Where we show it | Status |
|---|---|---|
| Easy to use; a community experts want to come back to | `/e/:token` card, phone first. Return reasons: group outcome report, a heard view, opt-in calibration after 5 resolutions. | partial: "community" is thin (P1) |
| Expert-controlled anonymity | Mask picker: badge (known), nickname (pseudonym), ghost (anonymous). The chosen mask is echoed back after submitting. Contract: `Answer.mask`. The one-line recognition warning sits next to the picker. | covered |
| Public anonymity | `/ledger` shows group probability and honesty box only. No names, no notes about anyone. `n < 5` is never returned. | covered |

### Should have

| Row | Where we show it | Status |
|---|---|---|
| Sustained engagement while respecting time | One pulse per expert per 7 days at most; round 2 optional and asynchronous; outcome report on resolution. Pilot measure: share of approved experts still answering in week 8. | partial: no re-engagement path for a lapsed expert (P1) |
| Short, focused contributions | Single card, one text line of 240 characters, about a minute. | covered |
| Small trusted groups (5 to 10) | Panel of the best 8 matched by tags, minimum 5, caps of 3 per affiliation type, committee approval. | covered |

### Should not

| Row | Where we show it | Status |
|---|---|---|
| Engagement metrics as the goal | We store and show none: no time-in-app, no streaks, no visit counts. Pitch sentence: "We show outcomes and honest limits, never time in the app." | covered |
| AI chatbot feel | No chat. AI is analyst-side only and off by default (`FF_AGENTS=false`); the draft is a fixed template. | covered |

### Could have

| Row | Where we show it | Status |
|---|---|---|
| Super estimator scoreboard | v3 scores forecasts, not people: a committee-only scoring view on `/desk`, pseudonyms only, never gating approval. | partial: tension with the brief's "recognise consistently accurate experts". **Needs a team decision (D1 in proposals.md).** |
| Agreement and disagreement, including by geography | `/desk` distribution chart with ACAPS line and panel dots; spread and minority reasons; Chad map with agreement by region (regions under 3 answers merged). | covered; show the merge note (P5) |
| Mobile and low-bandwidth | Card is phone first, magic link email. | partial: no payload budget; SMS channel in the contract has no route (P3) |
| Multilingual (French and others) | French strings isolated in a locale file; English ships. | gap: French card text not built (P4) |

### Can have

| Row | Where we show it | Status |
|---|---|---|
| AI behind the scenes | Default: deterministic draft template with traceable sentences. Agent loop (investigator, skeptic, judge) behind `FF_AGENTS`, only if stable by Sat 20:00. Say which one ran. | covered |

## 3. Brief checks outside MoSCoW

| Item | Where | Status |
|---|---|---|
| No real expert data | Footer on every screen: "Synthetic experts." README table of synthetic vs live. | covered |
| Loop with outcomes shared publicly | `/ledger`: outcome, Verify, honesty box; outcome report to the panel | covered |
| Turn risks into resolvable questions | Frozen `QuestionContract` per risk (`question-contract.md`, `POST /risks/{id}/contract`) | partial: R1043 wording needs fixes (P2) |
| Show where experts agree and disagree | spread, minority reasons, distribution chart | covered |
| Pilot readiness | Slide 8. Phrase: "ready for a supervised pilot of this workflow", not "pilot-ready Monday". | covered |
| Four personas | impact.md part 1; Slide 7 | covered |
| SDGs 1, 2, 3, 10, 16, 17 | README, one line | partial: not yet written |

## 4. Sentences to say on stage

1. Problem: "Medium-rated ACAPS risks happened 47 % of the time. A donor cannot act on a coin flip."
2. Expert: "A minute, a phone, no login, and you choose how much ACAPS knows about you."
3. Trust: "Answers are committed with a timestamp and opened together. Anyone can check the round was not changed. We do not claim the operator cannot read them. The table is in the repo."
4. Feasibility: "The analyst sends the question. It runs on the ACAPS API today."
5. Data: "We tested the pipeline on all 104 resolved risks, with synthetic panels. That tests the software, not real experts."
6. Innovation: "A one-minute expert loop that publishes its own limits and misses."
7. Honesty: "Every ledger entry says what fed into it, what decision it could inform, and when the analyst overruled the panel."
