# Sealed Signals — master prompt v3.3 (team of 3)

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

## 1a. Who can learn what (replaces every "sealed" or "nothing leaves the device" claim)

| Party | Before reveal | After reveal | Ever |
|---|---|---|---|
| The expert | their own answer | their answer + group view | their own private calibration (opt-in) |
| Peers on the panel | nothing | anonymised distribution, pseudonymous rationales if the author chose `pseudonym` | never a name, never a `known`/`anonymous` author |
| ACAPS admins / analyst | that an answer exists (count) | answers with the mask the expert chose; `anonymous` answers without identity | the identity registry (restricted, logged access) |
| The public | nothing | aggregates with n ≥ 5, honesty box, outcomes | never an individual answer or rationale |
| The server | the committed value is stored encrypted at rest; application access controls, not cryptography, keep staff from reading it early | everything the admins see | the registry, under access logging |

Commit-and-reveal guarantees: an answer cannot be changed after submission, the timestamp is verifiable, and peers cannot
see each other before the round closes. It does not guarantee confidentiality from the operator. Small panels with
distinctive rationales can re-identify a dissenter to peers; the card warns about this next to the mask picker.

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
              evidence[{source, indicator, value, baseline, z, url}], question, expires_at, n_answers
Answer        id, pulse_id, mask, pseudonym|null, probability (0..1)|null, confidence (1..5)|null,
              stance ("estimate"|"outside_my_expertise"|"not_enough_evidence"), panel_share_yes (0..1)|null
              (elicitation, fixed: "what share of this panel will put the probability above 0.5?"),
              missing (≤240 chars), source_tag ("saw"|"read"|"heard"|null), round (1|2), changed_mind (bool, round 2 only),
              committed_at, revealed_at|null
Commitment    answer_id, commitment (sha256 of canonical json + salt), committed_at   # timing + consistency proof only
RoundResult   pulse_id, n, mean (equal weight, PRIMARY), spread {min, max, iqr}, minority_rationales[],
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
PatternReport pseudonym, n_pulses, calibration, overconfidence, extremity, agreement_with_acaps, round2_shift, source_mix{},
              abstention_rate, seed_accuracy, perceived_vs_actual_gap, meta_accuracy, test_retest_delta, median_latency_s, sentences[]
Contact       expert_id, display_name (registry only), org_type, geo_tags[], theme_tags[], languages[], channel_pref, hour_pref, tz,
              consent_note, status ("invited"|"answered_once"|"active"|"paused"), paused_until|null
Delivery      pulse_id, channel, sent_at, delivered_at|null, answered_at|null, entered_on_behalf (bool)
SeedItem      id, risk_id, question, options[], known_answer, source_record
Score         expert_internal_id, risk_id, brier, resolved_at, weight_after        # committee-side only
OutcomeReport pulse_id, group_mean, outcome, analyst_decision_summary              # sent to everyone who answered
Calibration   expert_internal_id, n_resolved, mean_brier, overconfidence (−1..1), note   # private, opt-in, after 5 resolutions
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
GET  /committee/patterns/{pseudonym} · GET /me/{token}/patterns    section 6d reports
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
GET  /e/{token}                   expert card payload: {pulse, risk, round, group_view_if_round2}
POST /e/{token}/answer            Answer → {committed_at, commitment}
POST /pulses/{id}/reveal          → RoundResult (opens round 1, starts round 2)
GET  /pulses/{id}/result          RoundResult
POST /pulses/{id}/draft           → DraftUpdate
POST /drafts/{id}/decision        {action: accept|edit|reject, edited_probability?, note} → DraftUpdate (+ LedgerEntry on accept/edit)
GET  /ledger · GET /ledger/{risk_id} · POST /ledger/verify {verify_hash} → {valid, sealed_at, anchor}
POST /risks/{risk_id}/resolve     {outcome, resolved_at} → {scores_written, weights_updated}
GET  /me/{token}/calibration      Calibration (private, opt-in, 404 until 5 resolutions)
GET  /analyst/board               {super_estimators[{pseudonym, n, mean_brier, weight}], divergence[{risk_id, panel, acaps}]}
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
  to peers = HMAC(server_key, expert_id); `anonymous` answers are stored without any identity link and cannot be claimed
  later. Blind-signed single-use credentials are the phase-2 path if anonymity from ACAPS itself is required (threat
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
  panel directly; (3) two experts tap "something is changing". One pulse per expert per 7 days. External feeds (ACLED,
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
| 1 | **Post-quantum registry encryption** (`FF_PQ`, default on) | ML-KEM-768 hybrid (`kyber-py` or `liboqs-python`) wraps the AES-256-GCM key that encrypts the expert-id ↔ identity map at rest; key held by the committee service | Registry page: lock line "identity map encrypted with ML-KEM-768 hybrid, key held by the committee" | Long-horizon confidentiality of the identity map against harvest-now-decrypt-later | Confidentiality from an administrator with the key; anything about answers |
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

- **Contacts**: name, organisation type (affiliation tag), geo and theme tags, languages, preferred channel and hour
  (learned from the first reply, editable by the analyst), consent note, status (invited → answered once → active →
  paused). Added by the analyst from existing contacts or imported from a CSV. No account, no password, no portal for the
  expert, ever. Credentials, masks and keys are created at committee approval, server-side.
- **Channels** (all built, all carrying the same magic link): email (plain text, < 2 KB, personal sender name, reply
  template at the bottom), WhatsApp and Signal (message with the link and the reply template; voice notes accepted),
  SMS (numeric reply "70 4"), scheduled call (ICS invite to the expert and the analyst; answer entered by the analyst as
  "entered on behalf of, with consent"), partner API (org credential posts answers for its own experts). Send time =
  08:00 in the expert's time zone; never Friday afternoon locally.
- **Magic link**: one token per expert per pulse, in every message. Opens the one-screen card (section 8). Answers from
  any channel resolve to the same token, so the record is identical whether they typed in the card, replied by email,
  sent a voice note or spoke to the analyst.
- **Inbound parsing** (`POST /inbound/email`, `/inbound/whatsapp`, `/inbound/sms`, `/inbound/voice`): tolerant parser for
  a probability (0–100, "70 %", "seventy", "soixante-dix", five-word scale), confidence (1–5 or "sure / not sure"),
  the panel question, the free line, abstention phrases ("outside my area", "pas mon domaine"), mask words
  ("anonymous", "nickname", "fine to name me"), "pause" words. Voice notes are transcribed and confirmed back in one line
  ("Got it: 70 %, confidence 4. Reply 'no' to correct."). Unparseable replies go to the analyst, never dropped.
- **Cadence and respect**: hard cap one pulse per expert per 7 days; "pause me" for 30 days by one word; reminders at most
  once, after 24 h, with social proof ("6 of 8 have answered"); 48-hour window; reveal happens at k ≥ 5 regardless.
- **Closing the loop** (automatic, in the expert's language and channel): within 24 h of the reveal, "7 of 8 answered;
  group 0.69; you said 0.80; the analyst kept High and added your note on Adré to the triggers"; on resolution, the
  outcome report; yearly, a private thank-you with early access to the global risk analysis. No ranking anywhere.
- **Honesty box** records the channel mix and the share of answers entered on behalf of experts.

Routes: `GET/POST /reach/contacts`, `POST /reach/contacts/import`, `POST /reach/pulses/{id}/send {channel_override?}`,
`GET /reach/pulses/{id}/delivery` (sent / delivered / answered per channel, counts only), `POST /reach/calls/schedule`,
`POST /inbound/{channel}`, `POST /reach/preferences/{expert_id}` (analyst-editable learned preferences).

## 6d. Per-expert response-pattern reports (descriptive, private, committee-side)

From data already stored, per pseudonym, after at least 3 pulses: calibration and overconfidence (Brier vs stated
confidence), extremity (share of answers at ≤ 0.1 or ≥ 0.9), agreement-with-ACAPS after reveal, round-2 shift size
(anchoring susceptibility), source-tag mix (saw / read / heard), abstention rate, answer latency, co-movement partners.

Measures that come from the card itself, invisibly (section 8, item 1): all computed server-side, never shown as a
judgement to the expert, and disclosed in the one-paragraph terms the analyst sends with the first contact ("some items
help us calibrate").
- **Seed questions** (Cooke's classical model): about one pulse in three carries one short factual item whose answer ACAPS
  already knows from its data ("roughly how many Sudanese arrivals per day did ACAPS record in late September: under 100,
  100–300, over 300?"). Performance on seed items = *actual* knowledge of the context; stated confidence = *perceived*.
  The gap between the two is the knowledge-gap measure, per pseudonym, as a sentence.
- **Meta-knowledge item** ("what share of the panel will say likely?"): peer-prediction accuracy identifies experts without
  a track record (Prelec; Martinie, Wilkening & Howe 2020) and feeds the surprisingly-popular experiment.
- **Test–retest**: occasionally the same judgement is asked in a different form two pulses apart (five words vs a number);
  the difference is a reliability measure.
- **Response time and edit count** on the card: very fast extreme answers and heavy slider editing are noted, not judged.
- **Overclaiming foil** (`FF_FOIL`, off by default; requires ACAPS's explicit consent and disclosure): one in ten seed
  items refers to a plausible but non-existent report; "yes, I saw it" measures overclaiming (Paulhus). We ship it
  behind a flag and recommend ACAPS decide; it is never on in the demo.
All of it produces sentences for the committee and, opt-in, for the expert as feedback; never a score, never public,
never a gate.
Output: sentences with the numbers ("moves toward ACAPS's band in round 2 on 4 of 5 pulses"), shown to the committee and,
opt-in, to the expert as feedback. Never a score, never public, never used to approve or remove in the pilot, never on free
text. Route `GET /committee/patterns/{pseudonym}` and `GET /me/{token}/patterns`. Tests: seeded anchoring-prone,
extreme, and well-calibrated synthetic experts produce the expected sentences; a benign expert produces none.

## 6a. Integrity layer (Lane A builds, Lane B shows on the desk only, Lane C explains)

Expert-facing, the only two changes to the card:
- **Rating hidden until after submission.** Round 1 does not display ACAPS's rating; the expert submits their own number
  first (we avoid displaying the anchor; we cannot guarantee cognitively independent judgement). The optional round 2
  shows ACAPS and the anonymised group; the shift is logged as an integrity note (Tversky & Kahneman on anchoring; Delphi
  practice of independent first rounds).
- **Accuracy prompt + source tag.** Above the "what are we missing" line: "Is this something you saw, read, or heard?"
  with a three-way tag (Pennycook & Rand: a single accuracy nudge measurably reduces the spread of false claims).

Moderator-facing detectors (desk only; never public, never shown to experts):
- **Herding**: round-2 answers converge toward the mean with no new reasons → `herding: suspected`; the aggregate then uses
  round 1 (`used_round`).
- **Collusion / independence**: pairwise agreement across pulses beyond what shared evidence explains → `collusion_pairs`;
  composition caps at panel build time (≤ 3 of 8 from one affiliation tag; geographic spread; theme cover).
- **Recency / availability**: panel probability moves with news volume (GDELT) while hard indicators (ACLED, UNHCR) are
  flat → `recency: suspected`.
- **Coverage gap**: panel tags vs the risk's triggers (a conflict risk with no conflict expert) → `coverage_gaps[]`; also
  goes public as a caveat in the honesty box.

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

1. **Expert screen** `/e/:token` — one screen, no scrolling, no header chrome, phone first; it must complete in under
   60 seconds with at most five taps. Looks like a note from a colleague, not a survey.
   - Line 1 (two sentences): who is asking and why now, in plain words, with the alert evidence ("ACAPS's severity for
     Displacement from Sudan to Chad rose 6.1 → 6.9 in April, the largest move of 123 crises.").
   - Item A, likelihood: five words (very unlikely · unlikely · even · likely · very likely) as large tap targets, with
     an optional number field for those who think in percentages. ACAPS's band is not shown.
   - Item B, confidence: three words (not sure · fairly sure · sure).
   - Item C, panel: "Most of the panel will say…" three options (unlikely · even · likely).
   - Item D, one line: "What are we missing?" with the saw / read / heard tag; optional.
   - Occasionally, in place of D or added below it, one seed item or one trigger pick (section 6d), always one tap.
   - Always visible, small: "Outside my area" and "Not enough evidence".
   - Mask: shown once on the first answer (badge · nickname · ghost, with the one-line limit), then remembered; one small
     link "change how you appear".
   - Submit → one line: "Thanks. ACAPS currently rates this High. You'll hear how the group saw it within a day." Then
     nothing else; no dashboard, no history page for the expert.
   - No timer in the product (the jury exercise adds one). No progress bar. No emoji. Large type, high contrast, works on
     a 2G connection (text only, < 50 KB).
   - Round 2, when opened: the same screen with the anonymised spread drawn as five bars and one question: "Still your
     answer?" (keep · revise), plus one optional line.
   Primary channel: email magic link; identical content by WhatsApp, Signal, SMS or a call (section 6e).
2. **Analyst desk** `/desk` — projector-friendly: live envelope tray (SSE), Reveal button, distribution chart (ACAPS line,
   panel dots, SP highlight), Chad map with agreement by region, digest with cited reasons, draft card with
   Accept / Edit / Reject (with the "what decision, for whom, by when" fields and a rationale box), committee-only
   scoring view, an **Alerts** page (the engine's ranked ShiftEvents for the current month with "Run engine", "Replay April
   2026", Approve pulse / Dismiss, the rule that fired, the edition's reliability), an "Ask the panel" button per risk,
   and an **integrity notes** panel per round: descriptive sentences with evidence (section 6a), no verdict colours.
   Crisis pages show the monthly severity series as a small line chart with the shift marked. **Committee view**:
   applications, approvals (two admins), credential batches issued / spent (counts only), registry status with the
   encryption line, access log, per-expert pattern reports as sentences. **Ledger**: attestation line and anchor status per
   entry; Verify shows hash match, signature check and anchor receipt, each with its one-line meaning. Plus a
   **Radar** view: the live Risk List from the ACAPS API as a table and map with a "source: ACAPS API / CSV" badge, and a
   committee view for expert applications (approve needs two admins).
3. **Public ledger** `/ledger` — per risk: sealed-at, group probability, ACAPS rating, outcome, **Verify** (turns green),
   and the **honesty box** (n, agreement, spread, coverage gaps, corroborated / queued claims, hit rate and misses, caveat,
   decision use, and "panel view rejected" with the analyst's rationale when that happened). No names anywhere, no notes
   about anyone.

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
  sealing (commitment hash + time on the ledger), masks (the chosen mask echoed on the card), surprisingly-popular
  (highlighted on the distribution chart), reliability weights (super-estimator board), doorbell (evidence line on the
  pulse), verification loop (Skeptic verdicts and Judge scores shown on the draft card, flagged claims marked), HITL (the
  decision log on the draft), scoring (the calibration report). If a technology has no visible effect,
  it is cut, not described.
- Feature flags (`FF_ZK`, `FF_ANCHOR`, `LLM_BASE_URL`) default to the path that works offline; the README states which
  path the demo ran with. Never claim on stage a path that is off.
- `make demo` runs the complete loop on R1043 with the synthetic panel in under 60 seconds, from a clean clone, with no
  network. That is the smoke test before every rehearsal.

## 9. Definition of done (freeze Sunday 10:30)

- `make check` green: pytest offline, UI builds, fixtures validate against the models.
- `make seed && make dev` → full loop on R1043 with synthetic experts: doorbell → pulse → 8 sealed answers → reveal →
  draft → accept → ledger → resolve → scores → calibration.
- `reports/proof.png` on the slide with assumptions.
- README: paragraph from section 0, architecture diagram, run instructions, what is synthetic vs live, limits, team.
- Pitch rehearsed twice with the QR step (jury becomes the panel); fallback `make demo` pre-loads 8 synthetic answers.

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
Build section 6e: contacts, channels with the magic link in every message, inbound parsers (email, WhatsApp, SMS, voice
with confirmation), call scheduling, learned preferences, cadence caps, loop-closing messages, delivery counts. Then the
seed items and the measures of section 6d that come from the card. Tests: every parser phrase in English and French; the
weekly cap; a paused expert never receives; an on-behalf answer is marked; a voice note round-trips to a confirmed number.

### Lane B — Frontend (three screens + demo stage)
Build section 8 in `ui/` against `fixtures/` from the first hour (`VITE_MOCK=1`), then the live API. The expert screen is
the hero (one screen, five taps, rating hidden, stances, saw/read/heard): test it on two real phones over the venue Wi-Fi
by Saturday 18:00; QR flow for the jury. Analyst desk with the Reach module (contacts, send pulse per channel, delivery
counts, call scheduling, "pulse as it will look" preview per channel), the Alerts page, the Radar and crisis pages, the
committee view; public ledger with the honesty box.
Milestones: expert card mock Sat 12:00 · desk + ledger mock Sat 16:00 · live API Sat 20:00 · stage polish Sun.

### Lane C — Research, impact, pitch (no code; docs + slides)
1. **Stakeholders** (`docs/sealed-signals/impact.md`): ACAPS analysts, field experts (local NGO staff, researchers,
   anticipatory-action practitioners), ACAPS readers (UN agencies, INGOs, donors such as ECHO/FCDO/CERF, insurers), affected
   populations. For each: how the world works today → what changes with Sealed Signals → what they get out of it → how they
   want to give their view (channel, language, time) → what would make them stop. Use the four personas in the brief
   (Jose, Emily, Pierre, Aisha).
2. **Before / after**: how ACAPS produces and updates a risk today (six-step method, analyst judgement, informal expert calls);
   after: doorbell → panel → cited draft → analyst decision → ledger → score. One diagram.
3. **Impact chain**: better probability → earlier decision → anticipatory funds released (IFRC/WFP/CERF frameworks) → aid
   pre-positioned → lower cost and mortality. Cite FAO/WFP anticipatory-action evaluations; mark every number as cited or
   illustrative. Worked example on R1043 (over a million Sudanese refugees in eastern Chad since 2023).
4. **Interview Alex (ACAPS) today**: the question list in `docs/sealed-signals/questions-for-acaps.md`; write his answers
   verbatim into impact.md and quote him in the pitch.
5. **Judging checklist** (`judging-checklist.md`): each dimension (problem understanding, expert experience, anonymity &
   trust, feasibility, data use, innovation, presentation) and the MoSCoW rows → the exact screen, number or sentence
   where we show it. Anything uncovered becomes a task for Lane A/B.
6. **Deck + demo script** (`demo-script.md`): 3 minutes, QR step, fallback; slides: problem (47 %), the loop, the demo,
   the proof chart, impact chain, pilot plan for December, team. Pitch practice Saturday 16:00.
7. **README narrative** (section 0 + why + limits), and the one-paragraph submission description.
8. **More features**: a ranked list of what to add after the hackathon (voice-first on device, machine panel member,
   hardware notary, anticipatory triggers, French/Arabic), each with the stakeholder it serves.
8a. **Hardening narrative**: one slide listing the six mechanisms of section 6c and the pattern reports of 6d, each with
   its guarantee and its limit, in the trust-design wording; a second slide "what we did not do and why" (no public
   scores, no auto-decisions, no blockchain logic).
9. **Honesty and limits narrative**: one slide on hidden-rating first rounds, descriptive integrity notes, the honesty box
   and the group outcome report, with sources (Tversky & Kahneman on anchoring; Tetlock / Good Judgment Project on
   calibration; Prelec, Seung & McCoy 2017 and Palley & Soll on peer-prediction methods, experiment only; Pennycook &
   Rand on accuracy prompts; the Delphi method). Verify every citation, including any PMC reference, before a slide.
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
