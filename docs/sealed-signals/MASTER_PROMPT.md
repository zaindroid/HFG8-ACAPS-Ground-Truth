# Sealed Signals — master prompt v3.4 (team of 3)

> **v3.4, Sat 7 Nov evening — after three more independent reviews of the Reach and elicitation design, and ACAPS's
> own workflow poster and cognitive-biases brief.** The loop stands. What changes: (1) **No hidden measurement.** The
> seed questions, knowledge-gap measure, response-time and edit-count measures and the overclaiming foil are gone from
> the pulse. Calibration is a separate, consent-gated programme (`FF_CALIBRATION`, off): the expert is told exactly what
> is measured, opts in by one reply, and sees their own report before anyone else. The committee sees panel-level and
> affiliation-level sentences only (n ≥ 3), never a person. (2) **Consent-first first contact**: personal note from the
> analyst, "why you", one-line charter, STOP by one word. (3) **The card**: event, place, threshold and deadline first;
> no severity line before submission; one required input (likelihood, with the percentage range printed under each
> word); everything else optional; per-answer mask with no default; explicit submit with a confirmation screen (no
> commit on link click); correction allowed until the deadline; no ACAPS rating shown after submit (it appears in the
> group feedback only). (4) **Reveal at the deadline**, never "when five are in"; under five: insufficient panel, nothing
> revealed; reminder wording neutral. (5) **Relayed answers** (call, paper, liaison, partner API) are labelled, carry
> consent and provenance, and are confirmed by the expert through their own link. (6) **Wording**: "pseudonymised", never
> "anonymous"; "ML-KEM-768 for key establishment, AES-256-GCM at rest"; the gap we fill is "ad-hoc checks between
> scheduled reviews are not structured, time-stamped or auditable", not "no record". (7) **Reveal view** has four
> columns: agreement · disagreement (unattributed) · missing evidence · analyst rationale; distinctive free text goes to
> the access-logged verification queue. (8) **ACAPS's own vocabulary**: section 0b maps every module to ACAPS's analysis
> workflow and names biases as ACAPS's 2016 brief names them. (9) **Pitch**: crypto is out of the three minutes except
> the Verify click; spine line "easier to contribute to, easier to scrutinise, easier to trace"; personas are design
> hypotheses, not evidence. Routes changed: `/analyst/board` → `/committee/scoring` (panel-level); `/committee/patterns/
> {pseudonym}` → `/committee/patterns/{panel_id}`; new `/e/{token}/confirm`, `PUT /e/{token}/answer`,
> `/me/{token}/calibration/opt-in`. If your agent is on v3.3: re-read sections 0, 0b, 1a, 4, 5, 6d, 6e, 6a, 8 and 10.

> **v3.3, Sat 7 Nov afternoon — Reach: experts never sign up; one screen; elicitation designed to measure bias and the
> knowledge gap without confronting anyone.** New section 6e (Reach module in the analyst portal: contacts, channels,
> magic links everywhere, inbound parsing, call scheduling, learned preferences), rewritten section 8 item 1 (the expert
> screen: one screen, four items, no scrolling), and section 6d extended with seed questions, meta-knowledge, test-retest
> and response-time measures. Routes under /reach/* and /inbound/*. Everything flows into the same Answer record, with the
> same masks, commitments and credentials, whatever the channel.

> **v3.2, Sat 7 Nov afternoon — build the full hardening stack, each piece with its exact guarantee.** Team capacity is
> not the constraint; precision of claims is. Everything below is built, visible in the product, flagged on by default
> where it cannot break the demo, and described everywhere with its "guarantees / does not" sentence from
> docs/sealed-signals/trust-design.md. New in v3.2: section 6c (post-quantum registry and attestations, blind-signed
> credentials, zero-knowledge membership, timestamp anchoring) and section 6d (per-expert response-pattern reports).
> The core loop and the alert engine still come first in build order; hardening is built in parallel by extra agents.

> **v3.1, Sat 7 Nov midday — the Risk Alert Engine runs on ACAPS's own monthly data.** We verified the ACAPS API with a
> registered token (data/acaps-api/README.md). `risk-list/` is published history (stale, no R1043); `crises/`,
> `countries/`, and the **monthly `inform-severity-index/<MonYYYY>/` and `humanitarian-access/<MonYYYY>/` editions are
> current (Nov 2026)**. Crisis TCD005 "Displacement from Sudan to Chad" (Ennedi Est, Wadi Fira, Ouaddaï, Sila; connected
> to SDN001) jumped 6.1 → 6.9 in April 2026, the largest move of 123 crises that month: R1043's own story, in ACAPS's own
> numbers. Changes: (1) the alert engine (section 6b) is primary, deterministic, built on these editions; external feeds
> (ACLED, UNHCR, GDELT) are a later note. (2) The Radar shows the live editions with source badges. (3) The demo opens
> with the engine diffing the current month live. (4) The agent loop stays behind `FF_AGENTS`; alerts never use a model.
> Cached editions are in `data/acaps-api/` so everything runs offline; a token (`ACAPS_API_TOKEN`) makes it live.

> **v3, Fri 6 Nov night — after two independent technical reviews.** The loop stands; the claims around it were
> over-stated. If your agent is on v2: re-read sections 0, 4, 5, 6, 6a, 7, 8 and 10. Summary of changes:
> 1. "Sealed" means: commitments prove timing and consistency and block *peer* anchoring. They do not hide answers from
>    the server. Section 1a is the who-can-learn-what table; it replaces every "nothing leaves the device" sentence.
> 2. Aggregation: **equal-weight mean is primary**; spread and minority rationales shown; surprisingly-popular is a
>    labelled experiment with a defined elicitation; no fixed extremizing; weights start equal, shrink to a prior, capped.
> 3. Score against the export's **Probability** field (five bands), never Risk Level; the number mapping is an assumption.
> 4. Synthetic results are a **sensitivity test**, not proof. No "earlier than ACAPS" claim: the export has no structured
>    rating history (verified), so the timing chart is dropped.
> 5. A frozen **question contract** per risk before any scoring (docs/sealed-signals/question-contract.md).
> 6. Anonymity for the pilot, stated honestly: restricted registry, stable internal ids, pseudonyms to peers, aggregates
>    to the public. Blind-signed credentials = phase 2; Semaphore = one slide. No "claim later" for anonymous answers.
> 7. Integrity detectors are **descriptions, not diagnoses**: no auto-penalties, no auto-fallback, analyst reads them.
>    Priority: coverage gap and single-origin claims. "n ≥ 5" is a disclosure rule, not an anonymity guarantee.
> 8. Skeptic tightened (exact provenance; judgement / observation / inference separated; uncorroborated ≠ false).
> 9. Deterministic draft template is the default; the agent loop stays behind `FF_AGENTS=false`.
> 10. Ledger gains "what decision, for whom, by when" and "panel view rejected: analyst rationale".
> 11. Score forecasts, not people: committee-side only; group outcome report to all who answered; private calibration
>     opt-in after 5 resolutions; never score free text; scores never gate approval.
> 12. Card: no countdown in the product (jury exercise only); "outside my expertise" and "not enough evidence" options;
>     round 2 optional and asynchronous; wording "rating hidden until after submission".
> 13. Doorbell: analyst-triggered is primary; automated indicator mapping is phase 2 as a per-risk menu.
> 14. Pitch: OpenTimestamps, ML-KEM/ML-DSA and the hardware notary are out of the 3 minutes; one privacy-engineering
>     page in the repo. "Ready for a supervised pilot of this workflow", not "pilot-ready Monday".
> Innovation framing: "distinctive for this challenge": a one-minute masked expert loop that publishes its own
> limitations and misses, with hidden-rating first rounds, descriptive integrity notes and a decision-oriented ledger.

> **v2, Fri 6 Nov evening — what changed after the ACAPS mentor interview.** If your agent already started on v1, read
> section 0a first, then re-read sections 4, 5 and 6: contracts and routes gained fields and endpoints; nothing was removed.
> 1. We build **the Risk Radar platform ACAPS does not have**, on their live API (CSV fallback), and put the expert loop on top.
> 2. Experts are vetted professionals (analysts, journalists, researchers) with **geographic + thematic tags**; pulses route
>    to the best-matched 8, not a fixed country list. Sign-up → ACAPS committee approval → credential.
> 3. New **integrity layer** (section 6a, superseded by v3 wording): hidden-rating first round, accuracy prompt, descriptive
>    integrity notes, shared-origin and corroboration checks on free text. Notes are moderator-only.
> 4. New **public honesty box** on every ledger entry: what fed into this, confidence, gaps, hit rate, misses included.
> 5. The app is **one validation layer among others**: nothing changes an ACAPS product automatically (unchanged, now explicit).
> 6. Email magic link is the primary channel; WhatsApp second.

Hackathon for Good #8 · ACAPS "Ground Truth" challenge · The Hague, 6–8 Nov 2026
**Submission: Sunday 8 Nov, 12:00 CET.** Track pitches 13:00, final 15:10.

Paste this file as the first message to your coding agent (Claude Code / Cursor) inside this repo, followed by one line:
`I am on Lane A` (backend), `Lane B` (frontend) or `Lane C` (research & pitch). Everything the agent needs is here.
These branches hold only our scaffold plus the ACAPS data; the organisers' original files live on `main` of this fork.

---

## 0. The idea in one paragraph (keep this text identical in README, slides and UI)

Sealed Signals is the Risk Radar platform ACAPS does not have: the live Risk List from the ACAPS API, with an expert loop,
descriptive integrity notes and a public audit trail on top. An ACAPS analyst (or, in phase 2, an indicator doorbell)
sends a one-minute question to the eight best-matched vetted experts. Experts answer on their phone behind a mask they
choose, with ACAPS's rating hidden until after submission. Answers are committed with a timestamp, opened together,
summarised as an equal-weight mean with spread and minority reasons, annotated with integrity notes the analyst reads,
turned into a cited draft the analyst accepts, edits or rejects, and published as a group view on a ledger with an honesty
box that states what fed into it, its limits and its misses. When the risk resolves, forecasts are scored committee-side
and every panel member gets the group outcome report. Nothing publishes itself.

The gap, stated exactly: ACAPS has a documented methodology and peer review for its scheduled products. The ad-hoc expert
checks between scheduled reviews, by email and conversation, are not structured, time-stamped or auditable. Sealed
Signals adds a reviewable trail to those checks. It does not replace ACAPS's method; it sits inside it (section 0b).
Pitch spine: **easier to contribute to, easier to scrutinise, easier to trace.**

Tagline: **The machine rings the doorbell, the panel answers, the analyst decides, the ledger remembers.**
Demo risk: **R1043**, escalating cross-border insecurity in eastern Chad (Sudan war). Numbers from the data: 139 risks,
57 countries, 104 resolved; High risks materialised 84 %, Medium only 47 %.

## 0a. What the ACAPS mentor told us (Fri 6 Nov) — design facts, quote them in the pitch

- Experts are **not sources on the ground**; they are well-informed professionals who already track crises: think-tank
  analysts, journalists, researchers, early-warning practitioners. Expertise is geographic **and thematic** (an earthquake
  expert outside Venezuela is still the right person for a Venezuela quake). Experts tag themselves at sign-up.
- **Gateway**: experts apply, ACAPS approves on credentials and track of work; "a trust system that builds over time";
  a committee of several ACAPS admins (global team; the Risk Radar manager sits in France).
- **His open question, which we answer**: a panel could lean one way or be packed to steer funding. The app must be one
  validation layer among others; products never change automatically; ACAPS must minimise bias and state limitations and
  what fed into each product. "We will get things wrong, like a prediction market; the point is honesty about it."
- **No platform exists**: the old app died with the US funding cuts; Risk Radar is a dataset on the website plus an API that
  most heavy users pull into their own systems. He said the Risk Radar "should have a platform" and that we may build one
  on the API to showcase the loop. API docs are in the shared pack (token auth, free account).
- **Today's process**: 32 analysts track their countries' parameters daily, score risks manually with simple thresholds,
  update weekly. "Not very automated, lots of space to improve."

## 0b. Where we sit in ACAPS's own method, in ACAPS's own words (quote these, Lane C)

ACAPS's analysis workflow poster (v2.0, acaps.org/en/methodology) has four phases, Design → Acquire → Analyse →
Communicate, and transversal activities: keep an audit trail, evaluate and validate evidence, hypotheses and assumptions,
communicate uncertainty, peer review. Our modules map onto it; the UI says so in one quiet line per screen:

| ACAPS phase / step | Sealed Signals module |
| --- | --- |
| 3.1 Explore: "spot early signals" | Risk Alert Engine (6b): month-over-month diff of ACAPS's own editions |
| 3.4 Interpret: "evaluate evidence and plausibility" | The pulse and the reveal view (agreement · disagreement · missing evidence) |
| 3.5 Anticipate: "identify triggers and indicators to monitor" | Trigger pick on the card; missing-evidence column; verification queue |
| 4 Communicate: "communicate uncertainty", "peer review" | Cited draft, analyst accept / edit / reject, honesty box |
| Throughout: "keep an audit trail" | Ledger, commitments, decision log |

ACAPS's technical brief on cognitive biases (March 2016) names 38 biases and recommends structured analytic techniques
(alternative hypotheses, devil's advocacy, key-assumption check, what-if analysis). We use ACAPS's names everywhere:

| ACAPS bias (their definition) | What we do |
| --- | --- |
| Anchoring effect ("focus on one piece of information") | ACAPS's rating and the severity-change line are not shown before submission |
| Groupthink, false consensus | Commit-and-reveal; round 2 shows an anonymised spread only; reminder never states counts |
| Availability cascade, recency, salience | Saw / read / heard tag; "news-driven" note on the desk; alert engine uses indices, not headlines |
| Absence of evidence ("failure to consider completeness") | "Not enough evidence" is a real answer; missing-evidence column; coverage-gap note |
| Confirmation bias → their mitigation "devil's advocacy" | Optional line "strongest reason this would NOT happen" |
| Institutional bias | Affiliation cap (≤ 3 of 8 from one type); affiliation-level sentences to the committee (n ≥ 3) |
| Overconfidence | Outcome scoring of forecasts; group outcome report; consent-gated calibration programme |
| Key-assumption check | Trigger pick: "which trigger would move your view most?" feeds the analyst's trigger list |

Two more sentences from the poster, to quote verbatim: at the end of Communicate the outputs are "tailored, relevant and
readable analysis outputs, providing solid reasoning and **reviewed by subject experts**" with a "**clearly and explicitly
communicated limit of knowledge and how it impacts confidence in the results**". The first is the expert loop; the second
is the honesty box. Step numbers for slides: 3.1 Explore item 15 "notice possible signals or stories in your data"; 3.4
Interpret item 27 "evaluate evidence and assess plausibility"; 3.5 Anticipate item 32 "identify triggers and track new
developments"; 4 Communicate items 38 "communicate uncertainty and document data and methods" and 39 "(self) edit and
peer review"; 5 Throughout "organise and document your work: provide an audit trail".

**Personas** (ACAPS's own, from 30 interviews with readers; two axes, global/field × information users/producers; the
organisers say they are also the kind of experts ACAPS engages). Full mapping in `docs/sealed-signals/personas.md`.
Design hypotheses, not evidence; every channel below is marked "assumed, to verify in the pilot".

| Persona | Who | What they said that we answer | Role in Sealed Signals | Contact type, assumed channel |
| --- | --- | --- | --- | --- |
| Emily | Head of methodology, donor emergency team, HQ, global | "With ACAPS I know what you don't know and what is assumed"; "understanding which sources are more reliable is tricky"; wants "online access to all resources used to build an analysis, even those with different perspectives" | Reader of the ledger and honesty box; panel member on health and nutrition themes; a reviewer who will check the Verify click | HQ methodologist; email, Teams |
| Jose | Emergency specialist, UN regional office in Jordan, covers Sudan among six countries | Wants "an easy way for field-users to provide quality feedback to HQ level to get a more accurate picture"; "discrepancies between information shared and the real situation"; wants updates "only for the countries I cover" | The expert the pulse is built for: covers Sudan, so the R1043 demo panel; also receives alerts filtered to his countries | Regional desk expert; email with one-click links, Teams; app alert |
| Pierre | MEAL officer, IFRC, field, deployed for months, now food crisis in Nairobi | Wants reliable sources fast on a new mission, in-depth context, scenario skills; limited resources and time | Field expert on food and displacement; the "outside my area" and voice-note paths exist for him; reader of trigger lists | Field practitioner; WhatsApp, voice note, scheduled call |
| Aisha | INGO country director, Madagascar, one country, 150 staff | Financial visibility "rarely beyond 6–10 months"; wants "information on political projections" to decide between an emergency and a development team | Reader of the ledger's "what decision, for whom, by when" line (her horizon matches the six-month question); one-country expert, rarely available | Country lead; email weekly, scheduled call; low cadence |

Three design consequences, all already in v3.4: the question horizon is six months because that is the readers' planning
horizon (Aisha, Pierre); alerts and pulses are filtered by the countries a person covers (Jose); every ledger entry
lists what fed into it and what is not known (Emily).

## 0c. The jury sheet (handed out Saturday evening; every lane reads this)

Scores 1 to 10 per criterion; total = A Concept ×4 (40 %) + B Prototype ×2 (20 %) + C Technology feasibility ×1.5
(future-proof, ethics, security, legal side of AI) + D Product potential ×1.5 + E Business feasibility ×0.5 + F Wow
×0.5. The sheet's own challenge check: "the brief's must-haves are easy to use, expert-controlled anonymity and public
anonymity; weigh them under A and B." Consequences: the live demo is inside the three minutes (B is 20 % and asks "does
it work"); the three must-haves are named in the jury's words on slide 2 and shown working in the demo (card, mask
picker, ledger); ethics, security and legal are labelled on slide 3; slide 6 carries one sentence of business model.
Full mapping and the Q&A answers: docs/sealed-signals/judging-checklist.md. Lane B: the mask picker and the ledger's
"never an individual" line must be visible without explanation. Lane A: `make demo` runs the full loop in under
75 seconds.

## 0d. Repository standard (enforced at every merge)

1. Root files: `CLAUDE.md` (project context), `README.md` (problem, five-step solution, the must-haves by the
   organisers' name with code paths, architecture, technology table, run, evidence, real vs synthetic, what we do not
   claim, pilot), `AGENTS.md` (file map and the test or command behind each claim), `SUBMISSION.md`, `CHANGELOG.md`.
   Every code path in them stays true; if a module moves, update the table in the same commit.
2. Evidence: `scripts/capture_evidence.sh` writes `docs/evidence/make-check.txt`, `make-demo.txt`, `tree.txt`; Lane B
   adds `docs/evidence/screens/` (three screens at 375 px and 1920 px) and `phones.md` (measured time and taps);
   Lane A adds `sensitivity.png`. Regenerated from a clean clone at the Sunday freeze.
3. Tests are named by the behaviour they prove (`test_link_click_never_commits`, `test_reveal_refused_before_deadline`,
   `test_public_ledger_never_returns_individual`, `test_replay_apr2026_tcd005_rank1`, `test_blind_token_reuse_rejected`,
   `test_pattern_sentence_never_names_pseudonym`).
4. Every module has a top docstring saying what it does, what it guarantees and what it does not, in the trust-design
   wording. Every feature flag is documented in `engine/engine/hardening/flags.py` with its fallback.
5. No dead code, no TODO, no placeholder text on the submitted branch. Unfinished work is deleted or moved behind a
   flag that is documented as off.
6. The organisers' files stay unchanged (`docs/challenge/`, `data/`, `references/`, `notebooks/`); ours sit beside them.
7. Submission: `demo` contains `main`'s history. Sunday 10:30 freeze: all lanes merged into `demo`, `make check` green,
   evidence captured, README tables true, tag `v1.0`. One pull request `demo` → `main` with `SUBMISSION.md` as the
   description, merged before 11:30; the submission form links to `main`.

## 1a. Who can learn what (replaces every "sealed" or "nothing leaves the device" claim)

| Party | Before reveal | After reveal | Ever |
|---|---|---|---|
| The expert | their own answer | their answer + group view | their own private calibration (opt-in) |
| Peers on the panel | nothing | anonymised distribution, pseudonymous rationales if the author chose `pseudonym` | never a name, never a `known`/`anonymous` author |
| ACAPS admins / analyst | that an answer exists (count) | answers with the mask the expert chose; `anonymous` answers carry no identity link and get no personalised feedback or calibration | the identity registry (restricted, logged access) |
| The public | nothing | aggregates with n ≥ 5, honesty box, outcomes | never an individual answer or rationale |
| The server | the committed value is stored encrypted at rest; application access controls, not cryptography, keep staff from reading it early | everything the admins see | the registry, under access logging |

Commit-and-reveal guarantees: an answer cannot be changed after submission, the timestamp is verifiable, and peers cannot
see each other before the round closes. It does not guarantee confidentiality from the operator. Small panels with
distinctive rationales can re-identify a dissenter to peers; the card warns about this next to the mask picker, and the
honesty box carries the same line. Public wording is always "pseudonymised", never "anonymous": pseudonymisation is not
anonymisation, and deleting the registry does not anonymise linked answers or prose.

## 1. Hard rules (from the ACAPS brief; a jury will check)

1. **No real expert data.** Synthetic experts and answers only (`data/synthetic/`).
2. **Expert-controlled confidentiality** per answer: `known` (to ACAPS) · `pseudonym` (to peers) · `anonymous` (no
   identity stored with the answer). Public output is aggregate only; never return an aggregate with fewer than **5**
   contributions (a disclosure rule, not an anonymity guarantee).
3. **One minute, one card, no login** (magic link). Minutes, not sessions.
4. **No chatbot feel, no engagement metrics.** AI is analyst-side only. We show calibration and outcomes, never time-in-app.
5. **Nothing publishes itself.** Rating updates reach the ledger only through the analyst's accept / edit / reject.
6. **Use the Risk Radar data** (`data/risk-radar-export.csv`) for scoring, the proof simulation and the demo.
7. Deliverables: working prototype, 3-minute pitch, repo link + short description (README).
8. **One validation layer among others.** The platform proposes; an ACAPS analyst decides; the committee administers.
   Bias flags are moderator-only. Public pages show aggregates, caveats and track record, never flags about a person.

## 2. Branches and merging

- `main` = always runnable. Nobody commits to `main` directly.
- Lanes: `lane/backend`, `lane/frontend`, `lane/research`. Rebase on `main` before every push.
- **Merge checkpoints** (whoever is free merges, the others review in 5 minutes): Sat 13:00 · Sat 20:00 · Sun 10:30 (freeze).
- A merge must keep `make check` green (section 9). Unfinished work stays behind a flag or a stub, never breaks `main`.
- Contracts (section 4) and routes (section 5) change only by announcing in the team chat and editing this file in the same commit.
- Commits: plain messages, the human's own git identity, no AI co-author lines.

## 3. Repository layout

```
README.md                         what we built, how it works, why (Lane C writes narrative, Lane A the run instructions)
docs/sealed-signals/
  MASTER_PROMPT.md                this file
  contracts.md                    section 4 + 5 in detail, kept in sync
  demo-script.md                  3-minute script (Lane C)
  impact.md                       stakeholders, before/after, impact chain (Lane C)
  judging-checklist.md            every jury dimension → where we show it (Lane C)
fixtures/                         JSON examples of every API response — Lane B builds against these first
engine/                           Python 3.12 · FastAPI · SQLite (Lane A)
  engine/{settings,models,db,anonymity,seal,aggregate,scoring,analyst,api}.py
  engine/agents/{investigator,skeptic,judge,loop}.py   analyst-side verification loop (section 6), model-optional
  engine/doorbell/{connectors.py,trigger_map.py,detect.py,run_daily.py}
  engine/radar.py                 ACAPS API client: risk-list, crises, countries, inform-severity-index/<Mon>, humanitarian-access/<Mon>;
                                  token from env, 1 req/s, pages via `next`; reads data/acaps-api/*.json when no token (same models)
  engine/alerts/{link,diff,rules,run}.py   Risk Alert Engine (section 6b): deterministic month-over-month diffs, no model
  engine/experts.py               sign-up, tags, committee approval, credential issue, panel matching by tags
  engine/integrity/{anchoring,calibration,herding,collusion,recency,coverage,rumour}.py   section 6a, moderator-only
  engine/sim/simulate_panels.py   backtest on the 104 resolved risks → reports/proof.json + proof.png
  tests/                          pytest, offline, < 5 s
ui/                               Lane B: Vite + React (or Lovable export committed here); .env: VITE_API_URL=http://127.0.0.1:18000
scripts/seed.py                   synthetic experts/panels/answers into the DB
scripts/demo_replay.py            replays stored indicator history for eastern Chad, fires the R1043 pulse
data/synthetic/                   experts.json, panels.json, answers.json, indicators_chad.csv (aggregated counts only)
reports/                          proof.png, proof.json
Makefile                          make dev / make check / make seed / make demo
```

## 4. Contracts (engine/models.py — everyone codes against these)

```
Mask = "known" | "pseudonym" | "anonymous"

Expert        id, pseudonym, geo_tags[] (ISO codes), theme_tags[] (conflict|displacement|flood|earthquake|epidemic|food|
              access|political|economic), affiliation_tag (org type, used only for composition caps), languages[],
              channel ("email"|"whatsapp"|"sms"), status ("applied"|"approved"|"paused"), approved_by[], synthetic=true
Panel         id, risk_id, expert_ids[] (best 8 by tag match), k_min=5, composition{max_per_affiliation:3, geo_spread, theme_cover}
Risk          risk_id, title, country_iso, country, probability_acaps (text: Very Low..Very High), impact_acaps (1-5),
              level ("Low"|"Medium"|"High"), status, triggers[{id,title,description}], horizon_months=6, sources[]
Pulse         id, risk_id, panel_id, fired_at, reason ("doorbell"|"analyst"|"experts"|"heartbeat"), round (1|2),
              evidence[{source, indicator, value, baseline, z, url}] (shown after submission, never before),
              question {event, location, threshold, deadline} (from the QuestionContract; shown first on the card),
              expires_at (the reveal time; fixed at send), n_answers, reveal_status ("open"|"revealed"|"insufficient_panel")
Answer        id, pulse_id, mask (chosen per answer, no default), pseudonym|null, likelihood_word ("very_unlikely"|"unlikely"|
              "even"|"likely"|"very_likely")|null, probability (0..1)|null (optional exact number; a word is never silently
              turned into a point: the aggregate uses the band midpoint and says so), confidence (1..5)|null (optional),
              stance ("estimate"|"outside_my_expertise"|"not_enough_evidence"), panel_share_yes (0..1)|null (optional,
              off the main card; elicitation fixed: "what share of this panel will say likely or very likely?"),
              missing (≤240 chars)|null, against (≤240 chars)|null ("strongest reason this would NOT happen"),
              trigger_pick (trigger id)|null, source_tag ("saw"|"read"|"heard"|null), round (1|2),
              changed_mind (bool, round 2 only), relayed (bool), relayed_by ("analyst"|"liaison"|"partner"|null),
              confirmed_by_expert_at|null (required for relayed answers before they count),
              submitted_at, corrected_at|null (allowed until pulse.expires_at; every version kept), committed_at, revealed_at|null
Commitment    answer_id, commitment (sha256 of canonical json + salt), committed_at   # timing + consistency proof only
RoundResult   pulse_id, n, mean (equal weight, PRIMARY), spread {min, max, iqr},
              disagreement[{position ("lower"|"higher"), n, summary (unattributed, one line, written from themes, never verbatim)}],
              missing_evidence[{theme, n}], verification_queue_count (distinctive free text lives in the access-logged queue, not here),
              weighted_mean (shrunk, capped; secondary), sp_experiment {answer ("yes"|"no"), method:"Prelec 2017 / Palley & Soll peer-prediction weighting", label:"experimental"},
              distribution[{bucket, count}], agreement_by_region[{region, n, mean}], missing_themes[{theme, count, origin ("many"|"single"),
              corroboration ("corroborated"|"single-source"|"uncorroborated"|"not checked")}], revealed_at,
              integrity_notes[{kind ("convergence"|"co_movement"|"shared_origin"|"coverage_gap"|"news_driven"),
              text (descriptive, never a verdict), evidence}]           # moderator-only; stripped from public responses
DraftUpdate   id, risk_id, pulse_id, proposed_probability (text scale), proposed_level, rationale_md,
              claims[{claim_id, text, evidence_kind ("panel"|"indicator"|"source"), evidence_ref, numbers[]}],
              skeptic[{claim_id, verdict ("supported"|"not_supported"), checks[]}], missing_checks[{theme, status}],
              judge{coverage, numbers_match, overall, flagged_claim_ids[]}, repair_rounds,
              status ("draft"|"accepted"|"edited"|"rejected"), decided_by, decided_at, note
LedgerEntry   risk_id, pulse_id, sealed_at, group_probability, acaps_probability, acaps_level,
              outcome (null|"materialised"|"not_materialised"), resolved_at|null, verify_hash,
              honesty{n, agreement (0..1), spread [min, max], coverage_gaps[], claims_corroborated (int),
              claims_total (int), claims_in_verification_queue (int), panel_hit_rate (0..1|null), misses (int), caveat (str),
              decision_use {what_decision, for_whom, by_when}, panel_view_rejected (bool), analyst_rationale (str|null)}   # public
Crisis        crisis_id, crisis_name, iso3[], drivers[], adm1_name[], connected_crises[], active        (from crises/)
Edition       dataset ("inform-severity-index"|"humanitarian-access"), month ("Nov2026"), fetched_at, source ("api"|"cache")
SeverityPoint crisis_id, month, index, category, human_impact, conditions, people_in_need, reliability, last_updated
RiskCrisisLink risk_id, crisis_id, how ("iso3+driver"|"analyst"), confirmed_by, confirmed_at
ShiftEvent    id, crisis_id, risk_id|null, month_from, month_to, metric ("index"|"human_impact"|"people_in_need"|"access"|"category"),
              before, after, delta, rank_this_month (1 = largest move), n_crises_this_month, rule_hit (str), pulse_id|null, status ("proposed"|"pulsed"|"dismissed")
QuestionContract  risk_id, event (one sentence), location, horizon_deadline (date), resolution_source, adjudication_rule,
              frozen_at   # must exist before a pulse can be scored
Credential    token_id (nullifier), issued_for_panel, spent_on_pulse|null, scheme ("rsa-blind-rfc9474"|"semaphore"|"hmac")
Attestation   risk_id, outcome, resolved_at, commitment_root, signature (ML-DSA-65), key_id, anchor_receipt|null
AnchorRoot    day, merkle_root, submitted_at, status ("pending"|"anchored"), receipt|null
PanelPattern  panel_id, n_pulses, n_experts, sentences[] (panel-level only: convergence after reveal, spread over time,
              abstention share, source mix, coverage gaps), by_affiliation[{affiliation_tag, n (≥ 3 or merged), sentence}]
              # committee-side; never per person; descriptive, never causal
CalibrationItem  id, risk_id, question, options[], known_answer, source_record, confidence_prompt ("how sure are you this is
              right, 50–100 %")   # only inside the consent-gated programme (FF_CALIBRATION), never on a pulse card
CalibrationEnrolment  expert_internal_id, consented_at, disclosure_version, items_answered, report_available (bool, ≥ 20 items),
              report_off (bool, expert can switch off any time)
Contact       expert_id, display_name (registry only), org_type, coverage_area (broad professional coverage, never current
              physical location), theme_tags[], languages[], channel_pref, hour_pref, tz, consent {charter_version, consented_at,
              stopped_at|null}, preferences_set_by ("expert"|"suggested_by_analyst"), status ("invited"|"answered_once"|"active"|"paused"|"stopped"),
              paused_until|null
Delivery      pulse_id, channel, sent_at, delivered_at|null, answered_at|null, relayed (bool)
Charter       version, text (what we ask, how often, what we store, who sees what, how to stop), sent_with_first_contact (bool)
Score         expert_internal_id, risk_id, brier, resolved_at, weight_after        # committee-side only
OutcomeReport pulse_id, group_mean, outcome, analyst_decision_summary              # sent to everyone who answered
Calibration   expert_internal_id, n_resolved, mean_brier, interval_coverage|null, note   # private, opt-in, after 5 resolutions; expert can turn off
```

Every response carries `served_from: "live"` and `generated_at`. Every aggregate carries `n`; `n < 5` is never returned.

## 5. API (port 18000; CORS for http://localhost:5173)

```
GET  /health
GET  /radar/status                {risk_list: {source, fetched_at, n}, editions: [{dataset, month, source, fetched_at}], token_present}
GET  /crises · GET /crises/{id}   crisis + linked risks + monthly series (SeverityPoint[] + access)
GET  /radar/editions              months available per dataset
POST /alerts/run                  {month_to?} → diff latest two editions for every crisis → ShiftEvent[] ranked; links to active risks
GET  /alerts                      ShiftEvent[] with status; GET /alerts/{id}
POST /alerts/{id}/pulse           analyst approves → creates the Pulse with the event's numbers as evidence
POST /alerts/{id}/dismiss         {note}
POST /risks/{risk_id}/link        {crisis_id} analyst confirms the risk ↔ crisis link
POST /alerts/replay               {month_from:"Mar2026", month_to:"Apr2026"} → the April 2026 TCD005 event, for the demo
GET  /risks                       active risks (live ACAPS API, CSV fallback) · GET /risks/{risk_id}
POST /experts/apply               {geo_tags, theme_tags, affiliation_tag, languages, channel} → {expert_id, status:"applied"}
POST /experts/{id}/approve        committee approval (needs 2 admins) → status approved, credential issued
GET  /panels/match?risk_id=       the 8 best-matched approved experts + composition check
GET  /integrity/{pulse_id}        moderator-only: integrity notes (descriptive) + evidence
GET  /committee/patterns/{panel_id}   section 6d panel-level sentences (never per person)
POST /me/{token}/calibration/opt-in   {consent: true, disclosure_version} → CalibrationEnrolment   (FF_CALIBRATION)
GET  /me/{token}/calibration/items    next CalibrationItem for an enrolled expert (404 unless enrolled)
POST /me/{token}/calibration/off      switch the report off
GET  /registry/status             {encryption: "ML-KEM-768 hybrid"|"off", key_holder, access_log_count}
GET  /committee/access-log        registry reads (who, when, why)
POST /credentials/issue           committee: blind-sign a batch of tokens for an approved expert (FF_BLIND)
POST /e/{token}/answer            accepts `credential` (blind-signed token) or `zk_proof` with the Answer; rejects reuse
GET  /ledger/{risk_id}/attestation  ML-DSA-65 signature, public key id, anchor receipt
GET  /anchors                     daily roots with status anchored / pending and receipts
POST /risks/{risk_id}/contract    freeze the QuestionContract (required before resolve)
GET  /pulses/{id}/outcome-report  the group outcome report sent to all who answered
POST /pulses                      {risk_id, reason:"analyst", question?} → Pulse
POST /pulses/doorbell/run         run the detector once → {shifts[], pulses_fired[]}
GET  /pulses/{id}                 Pulse
GET  /e/{token}                   expert card payload: {question, round, group_view_if_round2}; never evidence or the ACAPS band before submission
POST /e/{token}/answer            draft Answer → {confirm_token, summary}   # nothing committed yet; link clicks never commit
POST /e/{token}/confirm           {confirm_token} → {committed_at, commitment}; first valid confirmation per expert per pulse counts
PUT  /e/{token}/answer            correction until pulse.expires_at → new commitment; previous versions kept and shown to the committee
POST /e/{token}/relayed-confirm   expert confirms an answer entered on their behalf (relayed answers count only after this)
GET  /e/{token}/feedback          after the reveal: group view, ACAPS band, analyst decision (this is where the band first appears)
POST /pulses/{id}/reveal          at expires_at (scheduler) or by the analyst after expires_at; n < 5 → reveal_status "insufficient_panel", answers kept, nothing revealed
GET  /pulses/{id}/result          RoundResult
POST /pulses/{id}/draft           → DraftUpdate
POST /drafts/{id}/decision        {action: accept|edit|reject, edited_probability?, note} → DraftUpdate (+ LedgerEntry on accept/edit)
GET  /ledger · GET /ledger/{risk_id} · POST /ledger/verify {verify_hash} → {valid, sealed_at, anchor}
POST /risks/{risk_id}/resolve     {outcome, resolved_at} → {scores_written, weights_updated}
GET  /me/{token}/calibration      Calibration (private, opt-in, 404 until 5 resolutions)
GET  /committee/scoring           {panels[{risk_id, n, panel_brier, acaps_band_brier}], divergence[{risk_id, panel, acaps}]}   # panel-level only
GET  /sim/proof                   contents of reports/proof.json
GET  /events                      SSE: pulse_fired · answer_sealed · round_revealed · draft_decided · risk_resolved
```

Example payloads for every route are in `fixtures/` (Lane B starts from these; Lane A keeps them true).

## 6. Algorithms (Lane A)

- **Commitment**: `commitment = sha256(canonical_json(answer) + salt)`, stored with `committed_at` before anything else;
  plaintext encrypted at rest; values appear only in aggregates after the round closes. Guarantee: timing and
  consistency, resistance to peer anchoring. Not confidentiality from the operator (section 1a). `verify_hash` of a
  ledger entry = sha256 of the round's sorted commitments; the public Verify button checks exactly that and says so.
- **Masks (pilot design)**: restricted identity registry with stable internal expert ids and logged access; pseudonym
  to peers = HMAC(server_key, expert_id); `anonymous` answers are stored without any identity link, cannot be claimed
  later, and receive no personalised feedback or calibration (the card says so when that mask is chosen). Blind-signed single-use credentials are the phase-2 path if anonymity from ACAPS itself is required (threat
  model: issuance timing, network metadata, revocation, scoring). Zero-knowledge group membership (Semaphore) is one slide
  in docs/sealed-signals/privacy-engineering.md, not a build.
- **Aggregate (primary)**: equal-weight arithmetic mean of probabilities, with spread (min, max, IQR) and the minority
  rationales shown next to it. **Experiment (labelled)**: surprisingly-popular on the binary question, elicitation fixed
  as "what share of this panel will put the probability above 0.5?" (Prelec, Seung & McCoy 2017; peer-prediction
  weighting per Palley & Soll; Lane C verifies the exact citations before any slide).
- **Weighted mean (secondary)**: weights start equal; after resolutions, performance estimates shrink toward the prior
  (n_resolved / (n_resolved + 5)); any single weight capped at 2× the median. No extremizing. Map to ACAPS's Probability
  bands with an explicit, documented assumption (Very Low .1 · Low .3 · Medium .5 · High .7 · Very High .9); the export
  publishes no numeric bands (verified).
- **Scoring**: only after a frozen QuestionContract. Brier = (p − outcome)² per forecast, committee-side. Stances
  `outside_my_expertise` and `not_enough_evidence` are never scored. Free text is never scored. Scores never gate approval
  or removal in the pilot.
- **k-anonymity**: any aggregate needs n ≥ 5; regional breakdowns need n ≥ 3 per region or are merged.
- **Pulse triggers**: (1) the Risk Alert Engine (section 6b) proposes; the analyst approves; (2) the analyst asks the
  panel directly; (3) two experts tap "something is changing". One pulse per expert per 7 days across all panels
  (priority rule: the alert with the highest rank this month wins; the others wait). External feeds (ACLED,
  UNHCR, GDELT) are a later note, not in the build.
- **Draft update**: the default path is a deterministic template with traceable fields (every sentence names its
  aggregate, indicator record or source). The agent loop below is behind `FF_AGENTS=false` and is used only if it is
  stable by Saturday 20:00.
- **Analyst-side verification loop** (`engine/agents/`, flag `FF_AGENTS`, default off). Same pattern as our FloodSense engine, model-optional, never expert-facing:
  1. **Investigator** drafts the rating update as claims. Each claim cites one of three evidence kinds: a panel aggregate
     (`n`, weighted probability, SP answer, a missing-theme count), a doorbell indicator (source, value, baseline, URL), or
     a source already in the risk's `Source` / `Rationale` fields. No other knowledge is allowed in a claim.
  2. **Skeptic** checks each claim: the number is exactly the value in a versioned aggregate or indicator record (no
     tolerance); a factual claim carries a supporting passage, publication date and geography; the claim is labelled as
     panel judgement, observed indicator or analyst inference; the event definition, horizon and probability scale match
     the question contract; no wording stronger than the evidence. For each `missing` theme the panel raised, the Skeptic looks for corroboration in the ACAPS API /
     ReliefWeb (cached fixtures offline) and labels it `corroborated` / `uncorroborated` / `not checked`. Claims that fail are
     marked, never deleted.
  3. **Judge** scores the draft: citation coverage, numbers match, grounding (supported / partial / unsupported per claim),
     and an overall score; the draft carries the scores and the flagged claim ids.
  4. **Analyst (HITL)** sees the draft with its verdicts and decides accept / edit / reject. One repair round if the Judge
     flags a claim: the Investigator rewrites only the flagged claims to what their evidence shows.
  The expert never sees any of this; the ledger stores the Judge scores next to the decision so the audit trail is complete.
  Deterministic fallback when no model is configured: the Investigator composes claims from templates over the aggregates
  and evidence, the Skeptic and Judge run their checks exactly as above.

## 6b. Risk Alert Engine (Lane A builds first; the moat; no model anywhere in it)

Data: ACAPS monthly editions `inform-severity-index/<MonYYYY>/` (index 0–10, category, Human Impact, Conditions of affected
people, People in need, Reliability, Last updated) and `humanitarian-access/<MonYYYY>/` (ACCESS 0–5 and sub-indicators),
per crisis; `crises/` for names, drivers, admin-1 areas, connected crises. Cached in `data/acaps-api/`; live with a token.

1. **Link** each active risk (CSV, e.g. R1043) to a crisis: same iso3 and a driver keyword match (displacement / conflict /
   flood / drought) against `crises[].drivers`; the analyst confirms once (`POST /risks/{id}/link`). R1043 ↔ TCD005.
2. **Diff** the latest two editions for every crisis: delta of index, Human Impact, People in need, access, and category
   change. Rank by |delta| across all crises that month; record `rank_this_month` and `n_crises_this_month`.
3. **Rules** (visible and editable on the desk, per risk): index Δ ≥ 0.5, or a component Δ ≥ 1.0, or a category change, or
   access Δ ≥ 1. A hit produces a ShiftEvent with the numbers, the crisis, the linked risk and the rule that fired.
4. **Propose, never fire**: events appear on the desk's Alerts page; the analyst approves (creates the pulse with the
   event as evidence), or dismisses with a note. Reliability of the edition is shown next to the event.
5. **Replay**: `POST /alerts/replay {Mar2026, Apr2026}` reproduces the real April event: TCD005 6.1 → 6.9 (+0.8, rank 1 of
   123; Human Impact 6.0 → 7.6), linked to R1043. This is the demo's opening fact.

Tests: the Mar→Apr 2026 cached editions must yield TCD005 as rank 1 with delta 0.8; a month with no moves yields no
events; a dismissed event never pulses; the same edition diffed twice yields no duplicate events.

## 6c. Hardening stack (Lane A or a parallel agent; every item built, flagged, and visible)

| # | Mechanism | Build | Where it shows | Guarantee we state | Does not |
| --- | --- | --- | --- | --- | --- |
| 1 | **Post-quantum registry encryption** (`FF_PQ`, default on) | ML-KEM-768 (hybrid with X25519) for key establishment; AES-256-GCM encrypts the expert-id ↔ identity map at rest; key held by the committee service. Say exactly that; never "ML-KEM encrypts the registry" | Registry page: lock line "identity map: ML-KEM-768 hybrid key establishment, AES-256-GCM at rest, key held by the committee" | Long-horizon confidentiality of the identity map against harvest-now-decrypt-later | Confidentiality from an administrator with the key; anything about answers |
| 2 | **Post-quantum outcome attestations** (`FF_PQ`) | ML-DSA-65 (`dilithium-py`) signs each resolved ledger entry (risk_id, outcome, resolved_at, round commitment root); public key published on the ledger; `verify` checks hash and signature | Ledger row: "attested, ML-DSA-65, verify" | The outcome record was issued by ACAPS's committee key and not altered since | Truth of the outcome; anything about who answered |
| 3 | **Blind-signed single-use credentials** (`FF_BLIND`, default on) | RSA blind signatures (RFC 9474, `cryptography`): on approval the committee signs a blinded token per pulse allowance; the expert unblinds client-side and spends one token per answer; server verifies signature and rejects reuse (nullifier) | Expert card for the `anonymous` mask: "answered with a one-time vetted credential"; committee view: tokens issued / spent, never linked | A vetted panel member answered, unlinkable to the approval by ACAPS | Protection against timing or network-metadata correlation; re-identification by distinctive wording |
| 4 | **Zero-knowledge group membership** (`FF_ZK`, default off until stable) | Semaphore v4 group per panel; the card generates a proof in the browser ("member of panel P answered pulse Q", nullifier per pulse); server verifies | Round view: "proof verified" per answer | Membership without identity, double-answer prevention | Reputation portability; not required for the pilot design |
| 5 | **Timestamp anchoring** (`FF_ANCHOR`, default on, degrades to "pending") | Daily Merkle root of all commitments submitted to OpenTimestamps (Bitcoin calendar servers); receipt stored; ledger shows "anchored / pending" | Ledger: anchor status per day; Verify shows the root and receipt | Independent proof the commitments existed by that time | Anything else; no tokens, no chain logic, no cost |
| 6 | **Registry access log** | Every read of the identity map is logged (who, when, why) and shown to the committee | Committee view: access log | ACAPS access is defined and visible | Prevention of access by an authorised admin |

Rules for all six: deterministic fallbacks so the demo never blocks (pending anchor, software signer, HMAC credential when
a flag is off); the README and the UI state which path ran; every sentence about them on stage uses the "guarantee / does
not" wording. Tests: encrypt/decrypt round trip; attestation verify passes and fails on a flipped byte; blind token
verifies, reuse rejected, unlinkable (server cannot match token to approval); ZK proof verifies, nullifier rejects a second
answer; anchor pending → anchored transition; a registry read appears in the log.

## 6e. Reach: experts never sign up (analyst portal module; Lane A builds, Lane B shows)

The analyst's address book is the registry. The expert's first contact is a question. The channel adapts to the expert.

- **First contact is consent-first.** The first message is a personal note from the analyst by name: why this expert
  ("you worked on the Chad–Sudan border"), the one-line charter (what we ask, how often, what we store, who sees what,
  how to stop), and the opt-out in one word ("reply STOP at any time"). The question follows in the same message. No
  reply means no second question that week; a STOP is honoured within the hour and logged.
- **Contacts**: name, organisation type (affiliation tag), coverage area (broad professional coverage, never current
  physical location) and theme tags, languages, preferred channel and hour (learned from the first reply, editable by
  the expert by reply or link; the analyst can suggest, never override), consent record, status (invited → answered once
  → active → paused → stopped). Added by the analyst from existing contacts or imported from a CSV. No account, no
  password, no portal for the expert, ever. Credentials, masks and keys are created at committee approval, server-side.
- **Lock-screen safety**: message bodies carry no sensitive place names, no identifiable notes and no ACAPS rating; the
  risk is named at the level of the crisis title only; detail is behind the link.
- **Channels** (all built, all carrying the same magic link; channel preference is a hypothesis until the recruited
  panel confirms it): email first (plain text, < 2 KB, personal sender name, one link per likelihood word that opens a
  confirmation screen, never a commit on click; plain reply in the analyst's own thread also parsed), WhatsApp and
  Signal (message with the link and the reply template; voice notes accepted), SMS (numeric reply "4 likely", or the
  link), Teams direct message as an adaptive card (`FF_TEAMS`, only where the agency permits the integration), scheduled
  call (ICS invite to the expert and the analyst), phone call with keypad answers and missed-call trigger (`FF_IVR`,
  pilot path, fixture telephony in the demo; tariffs verified with a local partner before any "free" claim), USSD
  deferred. Send time = 08:00 in the expert's time zone; Friday afternoon avoided unless the alert is escalating.
- **Relayed answers** (call, paper and photo, field liaison, partner API): labelled `relayed`, with who relayed, the
  expert's consent and provenance recorded, counted only after the expert confirms through their own link or by reply.
  Relayed answers are shown as "extended panel" in the honesty box. An organisation posting answers for its experts is
  not the panel; without the expert's own confirmation the answer never enters an aggregate.
- **Magic link**: one token per expert per pulse, in every message. Opens the one-screen card (section 8). Answers from
  any channel resolve to the same token, so the record is identical whether they typed in the card, replied by email,
  sent a voice note or spoke to the analyst.
- **Inbound parsing** (`POST /inbound/email`, `/inbound/whatsapp`, `/inbound/sms`, `/inbound/voice`): tolerant parser for
  a probability (0–100, "70 %", "seventy", "soixante-dix", five-word scale), confidence (1–5 or "sure / not sure"),
  the panel question, the free line, abstention phrases ("outside my area", "pas mon domaine"), mask words
  ("anonymous", "nickname", "fine to name me"), "pause" words. Voice notes are transcribed and confirmed back in one line
  ("Got it: 70 %, confidence 4. Reply 'no' to correct."). Unparseable replies go to the analyst, never dropped.
- **Cadence and respect**: hard cap one pulse per expert per 7 days across all panels; "pause" for 30 days by one word;
  STOP forever by one word; reminders at most once, after 24 h, neutral wording ("most of the panel has answered"; never
  a count in a panel of eight); the window is fixed at send (48 h default) and the reveal happens at that deadline, not
  when five answers are in, so fast responders are not privileged; late responders stay blind until they submit; under
  five at the deadline: "insufficient panel", the analyst is told, answers are kept for the record and nothing is
  revealed. The analyst sees who has not answered and may write a personal message; the system never sends a third.
- **Closing the loop** (automatic, in the expert's language and channel): within 24 h of the reveal, "Most of the panel
  answered; the group view is around 0.7; you said 0.8; ACAPS rates this High; the analyst kept High." Attribution ("your
  note on Adré was added to the triggers") only when the analyst explicitly recorded it. On resolution, the outcome
  report. Yearly, a private thank-you with early access to the global risk analysis. No ranking anywhere. This feedback
  message is where the expert first sees ACAPS's band; the card never shows it.
- **Honesty box** records the channel mix and the share of relayed answers.
- **Language**: English and French parsed in the MVP; numbers are language-agnostic; free text is kept in the original
  and translated for the analyst with the original attached.

Routes: `GET/POST /reach/contacts`, `POST /reach/contacts/import`, `POST /reach/pulses/{id}/send {channel_override?}`,
`GET /reach/pulses/{id}/delivery` (sent / delivered / answered per channel, counts only), `POST /reach/calls/schedule`,
`POST /inbound/{channel}`, `POST /reach/preferences/{expert_id}` (expert-editable by reply or link; the analyst can only
suggest, and a suggestion is marked until the expert confirms), `POST /reach/contacts/{id}/stop` (one-word opt-out).

## 6d. Pattern reports (panel-level) and the consent-gated calibration programme

**No measurement is hidden in a pulse.** The pulse card asks the question and nothing else. Nothing on it is a test, and
nothing about a person is computed from it except what the person was told: their answer is stored, committed and scored
against the outcome once the question resolves.

**Panel-level pattern reports** (`GET /committee/patterns/{panel_id}`, committee-side): after at least 3 pulses, sentences
about the panel, never a person: "answers became more similar after the reveal on 2 of 4 pulses"; "the spread narrowed
over the last three pulses"; "one in four answers was an abstention"; "most free text was tagged heard"; "this panel has
no access expert". Affiliation-level sentences only where the affiliation has n ≥ 3 on the panel, otherwise merged;
descriptive, never causal ("UN-affiliated answers sat above the mean on 3 of 4 pulses" is allowed; "UN experts are
optimistic" is not). Tests: seeded convergent and divergent synthetic panels produce the expected sentences; no sentence
ever contains a pseudonym.

**Calibration programme** (`FF_CALIBRATION`, default off; Lane A3 builds it; the demo shows it as a flagged feature on the
committee view and nowhere on the pulse card):
- Enrolment is separate from the panel: the expert receives a one-paragraph disclosure (what is asked, how often, what
  is computed, who sees it, that they see it first, that they can switch it off) and consents by one reply. Consent is
  versioned.
- Items are short factual questions whose answer ACAPS already holds, with a numeric confidence prompt ("how sure are
  you this is right, 50–100 %"), sent on their own at most twice a month, never inside a pulse. Numeric confidence on
  comparable items is what makes a calibration curve meaningful; three confidence words against right/wrong items do not.
- A report exists only after 20 items, goes to the expert first and alone through their link, and is one paragraph in
  plain words ("when you said 90 % you were right about 7 times in 10"). The committee sees it only if the expert opts
  in a second time, and never as a weight. Forecast calibration (Brier over resolved pulses, after 5 resolutions) is the
  same: expert first, opt-in, off at any time.
- Not built, and recommended against: fictitious references (overclaiming foils), response-time and edit-count measures,
  test–retest traps. Nothing that a participant would recognise as deception.

Reporting lines for the pitch and the README: "calibration is measured only with consent, and the expert sees it before
we do"; "the committee reads about panels, not people".

## 6a. Integrity layer (Lane A builds, Lane B shows on the desk only, Lane C explains)

Expert-facing, the only two changes to the card:
- **Rating and evidence hidden until after submission.** Round 1 does not display ACAPS's rating nor the severity-change
  line; the expert submits their own answer first (we avoid displaying the anchor; we cannot guarantee cognitively
  independent judgement; ACAPS's brief calls this the anchoring effect). The optional round 2 shows the anonymised
  group only; ACAPS's band appears in the feedback message after the reveal (Tversky & Kahneman on anchoring; Delphi
  practice of independent first rounds).
- **Accuracy prompt + source tag.** Above the "what are we missing" line: "Is this something you saw, read, or heard?"
  with a three-way tag (Pennycook & Rand: a single accuracy nudge measurably reduces the spread of false claims).

Moderator-facing notes (desk only; never public, never shown to experts; descriptions in ACAPS's bias vocabulary, never
verdicts; nothing changes automatically, the analyst reads and decides which round to use and records why):
- **Convergence after reveal** (ACAPS: groupthink): "round-2 answers moved toward the mean on n of m; k gave a new reason".
- **Co-movement** (ACAPS: false consensus): "these pseudonyms moved together on m of p pulses"; shown only at m ≥ 3 of
  p ≥ 4, with the reminder that shared expertise and shared sources look the same; benign test cases included.
- **News-driven** (ACAPS: availability cascade, recency): "the panel's view moved while ACAPS's indices were flat";
  descriptive; we cannot infer headline versus field evidence from timing and the note says so.
- **Coverage gap** (ACAPS: absence of evidence): panel tags vs the risk's triggers → `coverage_gaps[]`; also public in
  the honesty box. Priority signal, deterministic, with single-origin claims.

**Reveal view (desk)**: four columns, agreement · disagreement · missing evidence · analyst rationale. Disagreement is
unattributed in a panel of eight: a one-line summary written from themes ("two experts expect displacement rather than
attacks"), never verbatim text; the distinctive free text lives in the access-logged verification queue with the
source tag. The honesty box carries one standing line: "in a panel of eight, a distinctive reason may identify its
author to colleagues; experts were told this before answering".

Rumour pipeline for the free-text claims:
- **Shared origin** (priority, deterministic): near-identical wording across experts or rounds counts once and is noted
  as "these claims may share an origin".
- **Corroboration** (the Skeptic, section 6): each claim checked against the ACAPS API, ReliefWeb and ACLED (cached fixtures
  offline) → `corroborated / single-source / uncorroborated`. Uncorroborated claims never enter the draft; they sit in a
  verification queue for the analyst with the source tag. Absence from the selected databases is not evidence of falsity.

Public honesty box on every ledger entry: n, agreement, spread, coverage gaps, claims corroborated / total / in
verification queue, the panel's hit rate and number of misses, a one-line caveat, "what decision this could inform, for
whom, by when", and when the analyst rejected the panel view, that fact and the analyst's rationale. This is the mentor's
"state what fed into this".

Deterministic, all of it. Seeded tests show the code produces the intended note; they are not a sensitivity or
specificity claim, and the README says so.

## 7. Sensitivity test on the resolved risks (Lane A builds, Lane C presents it as what it is)

On the 104 resolved risks, simulate panels of eight under several scenarios: mixed accuracy; shared bias (all experts
pulled the same way); correlated errors (shared sources); no expert advantage (pure noise). Report Brier of the equal-weight
mean, the shrunk weighted mean and the ACAPS Probability band mapped to a number (stated assumption), with bootstrap
intervals labelled "resampling spread, not statistical confidence". Output `reports/sensitivity.json` and one chart. It is a
software and sensitivity test of the pipeline; it says nothing about real experts and makes no timing claim. Off the
3-minute headline; on the repo page and in Q&A.

## 8. UI (Lane B) — three screens

1. **Expert screen** `/e/:token` — one screen on a 375-px phone, no header chrome; targets (measured on two real phones
   before Saturday 18:00, written in the README as measured, not claimed): under 60 seconds, three taps for the common
   path, under 50 KB, usable on 2G. Zoom, translation and accessibility are never sacrificed to avoid a scroll. Looks
   like a note from a colleague, not a survey.
   - Line 1, the question, exactly as frozen in the question contract: event, place, threshold, deadline. ("Will more
     than 50,000 new arrivals from Sudan be registered in Ouaddaï and Wadi Fira by 31 March 2027?") Who is asking, by
     name, in small type. No severity line, no ACAPS band, no evidence before submission.
   - The one required input: five words as large tap targets, each with its percentage range printed under it
     (very unlikely < 10 % · unlikely 10–35 % · even 35–65 % · likely 65–90 % · very likely > 90 %), and a small
     "exact number" field for people who think in percentages. A word is never silently treated as a point.
   - Always visible, small, never scored: "Outside my area" and "Not enough evidence".
   - Optional, collapsed under "add a note": how sure (not sure · fairly sure · sure); one line "what are we missing?"
     or, alternating, "strongest reason this would NOT happen", with the saw / read / heard tag; "which trigger would
     move your view most?" (the risk's triggers as three chips).
   - Mask: chosen per answer, no default, three plain words (named to ACAPS · nickname to peers · no identity kept),
     with the one-line limit ("in a panel of eight a distinctive reason may identify you to colleagues") and, for "no
     identity kept", "you will not receive personal feedback on this answer". Changeable by reply.
   - Submit opens a confirmation screen that repeats the answer in one line; "Confirm" commits. A link click or a
     mail scanner can never commit. "Change my answer" works until the deadline shown on the screen; every version is
     kept.
   - After confirming, one line: "Thanks. You'll hear how the panel saw it after the deadline." Nothing else; no
     dashboard, no history page, no rating.
   - No timer in the product (the jury exercise adds one). No progress bar. No emoji. Large type, high contrast.
   - Round 2, when the analyst opens it: the same screen with the anonymised spread as five bars and the unattributed
     disagreement summary, one question "Still your answer?" (keep · revise) and an optional line "what changed your
     mind?". ACAPS's band is still not shown.
   - The feedback message after the reveal (section 6e) is where the expert first sees ACAPS's band and the analyst's
     decision.
   Primary channel: email with one link per word opening the confirmation screen; identical content by WhatsApp, Signal,
   SMS, Teams or a call (section 6e). The calibration programme (6d) has its own screen under `/c/:token`, never mixed
   with a pulse.
2. **Analyst desk** `/desk` — projector-friendly: live envelope tray (SSE, counts only), reveal at the deadline (the
   button says "Reveal (deadline passed)" or "Opens at 09:00 Monday"), the four-column reveal view (agreement ·
   disagreement, unattributed · missing evidence · analyst rationale), distribution chart (ACAPS line, panel dots, SP
   experiment labelled), Chad map with agreement by region, verification queue (access-logged), draft card with
   Accept / Edit / Reject (with the "what decision, for whom, by when" fields and a rationale box), committee-only
   scoring view, an **Alerts** page (the engine's ranked ShiftEvents for the current month with "Run engine", "Replay April
   2026", Approve pulse / Dismiss, the rule that fired, the edition's reliability), an "Ask the panel" button per risk,
   and an **integrity notes** panel per round: descriptive sentences with evidence (section 6a), no verdict colours.
   Crisis pages show the monthly severity series as a small line chart with the shift marked. **Committee view**:
   applications, approvals (two admins), credential batches issued / spent (counts only), registry status with the
   encryption line, access log, panel-level pattern reports as sentences, calibration programme enrolments (counts,
   flagged `FF_CALIBRATION`), panel-level scoring. **Ledger**: attestation line and anchor status per
   entry; Verify shows hash match, signature check and anchor receipt, each with its one-line meaning. Plus a
   **Radar** view: the live Risk List from the ACAPS API as a table and map with a "source: ACAPS API / CSV" badge, and a
   committee view for expert applications (approve needs two admins).
3. **Public ledger** `/ledger` — per risk: sealed-at, group probability, ACAPS rating, outcome, **Verify** (turns green),
   and the **honesty box** (n, agreement, spread, coverage gaps, corroborated / queued claims, hit rate and misses, caveat,
   decision use, relayed share, the standing re-identification line, and "panel view rejected" with the analyst's
   rationale when that happened). No names anywhere, no notes about anyone.

White background, one accent colour, big type. Build against `fixtures/` first (a `VITE_MOCK=1` mode serving the fixtures),
switch to the live API at the Saturday 20:00 merge.

## 8a. UI / UX standard (Lane B, enforced at every merge)

Professional, minimal, modern. The jury should think "this already exists in production", not "a hackathon demo".

- **Palette**: white background, near-black text, one muted accent (deep teal or slate blue), one semantic colour each for
  good / warning / critical. No neon, no gradients as decoration, no glow, no blinking or pulsing elements, no animated
  backgrounds. Motion only to explain state (an envelope locking, a chart revealing), 150–250 ms, and off under
  `prefers-reduced-motion`.
- **No emoji anywhere**: not in UI, README, slides, commit messages or the demo. Icons are a single consistent line-icon
  set (Lucide), 1.5 px stroke, used sparingly.
- **Type**: one body face (Inter or IBM Plex Sans), one weight for headings; a fixed type scale; tabular numbers for
  probabilities and scores; running text ≤ 65 characters wide. No all-caps shouting, no decorative fonts.
- **Layout**: 8-px spacing grid, consistent card edges and padding, generous whitespace, left-aligned text; phone-first for
  the expert card (375 px), projector-first for the analyst desk (1920 px, 16:9), both without horizontal scroll.
- **Components**: shadcn/ui or plain Radix primitives; every interactive element looks interactive; visible focus states;
  real empty, loading and error states (never a blank screen); a Copy button where an export would be.
- **Content**: real risk titles, real numbers from the data, synthetic experts labelled as synthetic in a footer line. Short,
  plain labels; no marketing language inside the product.
- **Charts**: one scale, labelled axes, the ACAPS rating as a reference line, the panel as points, confidence shown as
  whiskers; chart text in the page's own type and colours.
- **Adaptable**: theme tokens in one file; the same components serve expert card, desk and ledger; works on phone, laptop
  and projector; French strings isolated in a locale file even if only English ships.
- Before each merge: screenshot the three screens at phone and desktop width and attach them to the PR.

## 8b. Integration standard (Lanes A and B, enforced at every merge)

- Every feature in section 0 is wired end to end and clickable in the demo: doorbell → pulse → card → seal → reveal →
  aggregate → draft → decision → ledger → resolve → calibration. Nothing is "shown in a slide but not in the product".
- No mocked data in the final build: `VITE_MOCK` is off from the Saturday 20:00 merge; fixtures remain only for tests.
- Each technology appears exactly where it does work, and the UI says so in one quiet line where relevant:
  sealing (commitment hash + time on the ledger), masks (the chosen mask echoed on the card), equal-weight mean with the
  SP experiment labelled on the distribution chart, panel-level scoring (committee view), the alert engine (evidence line
  on the pulse, shown after submission), verification loop (Skeptic verdicts and Judge scores on the draft card, flagged
  claims marked), HITL (the decision log on the draft), the group outcome report and the opt-in calibration report. If a
  technology has no visible effect, it is cut, not described.
- Feature flags (`FF_PQ`, `FF_BLIND`, `FF_ZK`, `FF_ANCHOR`, `FF_AGENTS`, `FF_CALIBRATION`, `FF_IVR`, `FF_TEAMS`,
  `LLM_BASE_URL`) default to the path that works offline; the README states which path the demo ran with. Never claim on
  stage a path that is off.
- `make demo` runs the complete loop on R1043 with the synthetic panel in under 60 seconds, from a clean clone, with no
  network. That is the smoke test before every rehearsal.

## 9. Definition of done (freeze Sunday 10:30)

- `make check` green: pytest offline, UI builds, fixtures validate against the models.
- `make seed && make dev` → full loop on R1043 with synthetic experts: doorbell → pulse → 8 sealed answers → reveal →
  draft → accept → ledger → resolve → scores → calibration.
- `reports/proof.png` on the slide with assumptions.
- README: paragraph from section 0, architecture diagram, run instructions, what is synthetic vs live, limits, team.
- Pitch rehearsed twice with the QR step (jury becomes the panel); fallback `make demo` pre-loads 8 synthetic answers.

## 9a. The three minutes (Lane C owns demo-script.md; deck in pitch/sealed-signals-slides.html; six slides, fixed)

0:00 slide 1, the problem (20 s) · 0:20 slide 2, the solution and the three must-haves in the jury's words (25 s) ·
0:45 live demo from the product (75 s): approve the April alert, send the pulse, the jury scans and answers on the card,
reveal, draft with Skeptic marks, accept with "what decision, for whom, by when", ledger, one click on Verify · 2:00
slide 3, how it is built, ethics, security and legal badges (20 s) · 2:20 slide 4, the card against six biases and the
agent loop (20 s) · 2:40 slide 5, why people can trust it (10 s) · 2:50 slide 6, it runs, it is different, opportunity
and model (10 s) · close on the spine line. Fallback slides B if the demo fails. Q&A answers in judging-checklist.md.
Nothing is said on stage about a path that is off.

## 10. Lanes

### Lane A — Backend (engine, data, proof)
Build sections 4–7 in `engine/`, `scripts/seed.py`, SSE. Order: models + db + seed → radar client over data/acaps-api
(risk-list, crises, countries, editions; live with token) → **Risk Alert Engine (6b) with the April 2026 replay test** →
experts + tags + committee approval + panel matching → pulses from approved alerts and from the analyst; answer/commit
(rating hidden, stances, source tag) → reveal + equal-weight aggregate with spread and minority rationales → integrity
notes (6a) → deterministic draft template citing the INFORM record + tightened Skeptic checks → decision + ledger with
honesty box → question contract + resolve + committee-side scoring + outcome report → sensitivity test + chart → agent
loop behind its flag only if stable. Keep `fixtures/` true to real responses (regenerate them from the running API).
Milestones: API with seeded data Sat 10:00 · full loop Sat 18:00 · proof.png Sat 20:00 · polish Sun.

### Lane A2 — Hardening agent (runs in parallel with Lane A; same branch, folders engine/hardening/ and engine/tests/hardening/)
Build section 6c items 1, 2, 3, 5, 6 first, then 4; then section 6d. Keep every fallback working with the flag off.
Deliver `docs/sealed-signals/privacy-engineering.md` updated with what is now built and the test evidence.

### Lane A3 — Reach agent (parallel; folders engine/reach/, engine/inbound/, engine/tests/reach/)
Build section 6e: consent-first first contact with the charter and STOP, contacts, channels with the magic link in every
message (email one-link-per-word with confirmation screen first), inbound parsers (email, WhatsApp, SMS, voice with
confirmation), Teams and IVR behind their flags with fixture transports, call scheduling, relayed answers with expert
confirmation, expert-editable preferences, cross-panel cadence cap, deadline reveal with the insufficient-panel path,
neutral reminder, loop-closing messages, delivery counts. Then section 6d: panel-level pattern reports and the
calibration programme behind `FF_CALIBRATION`. Tests: every parser phrase in English and French; STOP honoured and
logged; the cross-panel weekly cap; a paused or stopped expert never receives; a relayed answer never counts before the
expert confirms; a link click never commits; a correction before the deadline replaces the commitment and keeps the old
one; reveal before the deadline is refused; n < 5 at the deadline yields insufficient_panel and no reveal; a voice note
round-trips to a confirmed number; no pattern sentence ever contains a pseudonym; no calibration item ever appears on a
pulse card.

### Lane B — Frontend (three screens + demo stage)
Build section 8 in `ui/` against `fixtures/` from the first hour (`VITE_MOCK=1`), then the live API. The expert screen is
the hero (question first, one required input with ranges, stances, optional note, per-answer mask, confirmation screen,
correction until the deadline, no rating anywhere): measure it on two real phones over the venue Wi-Fi by Saturday
18:00 and write the numbers in the README; QR flow for the jury. Analyst desk with the Reach module (contacts with
consent status, first-contact preview with the charter, send pulse per channel, delivery counts, call scheduling,
"pulse as it will look" per channel), the four-column reveal view, the verification queue, the Alerts page, the Radar
and crisis pages, the committee view (panel-level only); public ledger with the honesty box.
Milestones: expert card mock Sat 12:00 · desk + ledger mock Sat 16:00 · live API Sat 20:00 · stage polish Sun.

### Lane C — Research, impact, pitch (no code; docs + slides)
1. **Stakeholders** (`docs/sealed-signals/impact.md`): ACAPS analysts, field experts (local NGO staff, researchers,
   anticipatory-action practitioners), ACAPS readers (UN agencies, INGOs, donors such as ECHO/FCDO/CERF, insurers), affected
   populations. For each: how the world works today → what changes with Sealed Signals → what they get out of it → how they
   want to give their view (channel, language, time) → what would make them stop. Use the four personas from the
   organisers' pack (Emily, Jose, Pierre, Aisha) as design hypotheses: map each to a contact type and a default channel
   marked "assumed, to verify in the pilot"; never present a persona as evidence of channel preference or willingness to
   be calibrated. Section 0b and docs/sealed-signals/personas.md hold the mapping; the persona slide follows the spine
   line and shows Jose answering the Chad pulse, Emily reading the honesty box, Aisha reading the decision line.
2. **Before / after**: ACAPS's own workflow poster (Design → Acquire → Analyse → Communicate) with our modules placed on
   it (section 0b table); the gap stated exactly as in section 0 (ad-hoc checks between scheduled reviews are not
   structured, time-stamped or auditable). One diagram. Never "today there is no record".
3. **Impact chain**: better probability → earlier decision → anticipatory funds released (IFRC/WFP/CERF frameworks) → aid
   pre-positioned → lower cost and mortality. Cite FAO/WFP anticipatory-action evaluations; mark every number as cited or
   illustrative. Worked example on R1043 (over a million Sudanese refugees in eastern Chad since 2023).
4. **Interview Alex (ACAPS) today**: the question list in `docs/sealed-signals/questions-for-acaps.md`; write his answers
   verbatim into impact.md and quote him in the pitch.
5. **Judging checklist** (`judging-checklist.md`): each dimension (problem understanding, expert experience, anonymity &
   trust, feasibility, data use, innovation, presentation) and the MoSCoW rows → the exact screen, number or sentence
   where we show it. Anything uncovered becomes a task for Lane A/B.
6. **Deck + demo script** (`demo-script.md`): the beats of section 9a; slides: the gap (47 %), where we sit in ACAPS's
   workflow, the loop, the demo, spine line, personas, sensitivity chart (repo and Q&A), pilot plan for December, team.
   Pitch practice Saturday 16:00.
7. **README narrative** (section 0 + why + limits), and the one-paragraph submission description.
8. **More features**: a ranked list of what to add after the hackathon (voice-first on device, machine panel member,
   hardware notary, anticipatory triggers, French/Arabic), each with the stakeholder it serves.
8a. **Hardening narrative** (repo page and Q&A, not the three minutes): the six mechanisms of section 6c, each with its
   guarantee and its limit, in the trust-design wording; "what we did not do and why" (no public scores, no hidden
   measurement, no auto-decisions, no blockchain logic).
9. **Honesty and limits narrative**: one slide on hidden-rating first rounds, descriptive integrity notes, the honesty box
   and the group outcome report, with sources (Tversky & Kahneman on anchoring; Tetlock / Good Judgment Project on
   calibration; Prelec, Seung & McCoy 2017 and Palley & Soll on peer-prediction methods, experiment only; Pennycook &
   Rand on accuracy prompts; Lord, Lepper & Preston 1984 on "consider the opposite"; the Delphi method; ACAPS's own
   cognitive-biases brief of March 2016 and its analysis workflow poster, quoted by name). Verify every citation,
   including any PMC reference, before a slide.
10a. **Privacy-engineering page** (docs/sealed-signals/privacy-engineering.md): the who-can-learn-what table, the pilot
   anonymity design, the phase-2 blind-signature path with its threat model, and one paragraph each on ZK membership,
   timestamp anchoring and post-quantum protection of the registry as research directions. None of it in the 3 minutes.
10b. **Question contract template** (docs/sealed-signals/question-contract.md) with R1043 filled in: event, location,
   deadline, resolution source, adjudication rule.
10. **Platform framing**: "the Risk Radar platform ACAPS does not have" — one before/after slide: website + API today,
    platform + loop + audit trail tomorrow; what the 32 analysts gain per week.

## 11. If you get stuck
Ask in the team chat with: what you tried, the error, what you need from the other lane. Never silently change a contract.
If a lane is blocked for more than 45 minutes, swap tasks at the next checkpoint.
