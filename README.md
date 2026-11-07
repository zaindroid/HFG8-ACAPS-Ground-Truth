# Sealed Signals

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

> **One correction to that paragraph, and we would rather say it here than be caught on it.** "Nothing identifying ever
> leaves the expert's device" is not what this build does. Sealing proves *timing and consistency* and blocks *peer*
> anchoring; the server holds the plaintext. See [Who can learn what](#who-can-learn-what).

## Run

```bash
pip install -r engine/requirements.txt
make install                 # python deps and UI deps, from a clean clone
make demo                    # the whole loop on R1043, offline, in about 1.5 s
make dev                     # API on :18000, and the built UI at /app
make check                   # pytest, UI build, fixture validation
```

`make dev` then serves:

| Path | What it is |
|------|------------|
| `/` | public entry; Login opens the workspace |
| `/alerts` | the Risk Alert Engine: ranked shift events, approve or dismiss, crisis history |
| `/desk` | analyst desk: envelope tray, reveal, distribution, draft, integrity notes |
| `/ledger` | public ledger with the honesty box and verification trail |
| `/radar` | the risk list with map, filters and source provenance |
| `/e/<token>` | the expert card; `/api/demo/links` lists the seeded links |
| `/api/*` | the engine. `/docs` is the generated API reference |

**The UI owns the root namespace and the engine answers under `/api`.** This is Lane B's layout
(`ui/src/service.ts` defaults `VITE_API_URL` to `/api`), and it is the only arrangement that works:
`/ledger` and `/e/{token}` are UI pages in section 8 and API routes in section 5, so they cannot both
live at the root. Section 5's paths are unchanged, they are just reached under the prefix. The Vite dev
proxy forwards `/api` without stripping it, so development and production address the engine identically.

The engine refuses to start without `COMMITMENT_SALT` and `PSEUDONYM_KEY`. That is deliberate: a sealing salt that
silently defaults is worse than one that is missing. `make dev` loads `engine/.env.example` for you; in production the
platform generates both and sets them before the first start.

## Architecture

```
ACAPS monthly editions (data/acaps-api/)        ACAPS Risk Radar export (data/, 139 risks)
  inform-severity-index/<MonYYYY>                        |
  humanitarian-access/<MonYYYY>                          |
        |                                                |
        v                                                |
  RISK ALERT ENGINE (6b)  -- diff two editions, fixed numeric rules, rank per
  metric and per direction. Proposes; never fires.       |
        |                                                |
        |  analyst approves on /app/alerts               v
        +--------------------------> pulse <----- doorbell (the risk's own triggers)
                           |
                           v
                    expert card  /app/e/<token>      blind: no ACAPS band shown
                           |
                      seal: sha256(canonical_json(answer) + salt)
                           |
                     [ k_min = 5 ]  nothing is aggregated below five answers
                           v
                   reveal -> RoundResult     equal-weight mean is PRIMARY
                           |                 weighted mean is secondary, capped
                           |                 surprisingly-popular is labelled experimental
                           v
              deterministic draft + Skeptic + Judge     every claim cites its evidence
                           |
                    analyst decides  (accept / edit / reject, with a rationale)
                           v
                  public ledger + honesty box + verify_hash
                           |
                     resolve -> Brier scores -> weights -> private calibration
```

One FastAPI process serves the API at the root and the built single-page UI under `/app`. The API keeps the root
namespace because `/ledger` and `/e/{token}` are API routes in the contract, so they cannot also be HTML pages.

## The Risk Alert Engine

`POST /alerts/replay {"month_from":"Mar2026","month_to":"Apr2026"}` reproduces the real move the demo opens on:

```
TCD005  Displacement from Sudan to Chad   index 6.1 -> 6.9  (+0.80)
        rank 1 of 123 crises diffed       rule: index delta >= 0.5
        Human impact 6.04 -> 7.57         reliability: Very High
        linked risk R1043                 status: proposed
```

No model is involved anywhere in it. It diffs two cached ACAPS editions, applies the thresholds in
`alerts.RULES` (index 0.5, components 1.0, access 1.0, or any category change), and ranks the hits. Then it
stops: an analyst approves an event into a pulse, or dismisses it with a note that is required, not optional.

**Ranking is per metric and per direction, and this is a deliberate departure from one line of the spec.**
Section 6b says "rank by |delta|". Ranked that way, April 2026's largest move is PAK007 at −0.90, an
*improvement*, and TCD005's +0.80 comes second — so an early-warning queue would open with good news, and
the pitch line "the largest move of 123 crises that month" would be false. Ranking within each metric and
each direction puts TCD005 at rank 1 of the index deteriorations (matching `fixtures/GET_alerts.json` and
`POST_alerts_replay_response.json`, which already encode this), and PAK007 at rank 1 of the improvements.
Every event also carries `rank_by_abs_delta`, so the other ordering is recorded rather than hidden. The
defensible sentence on stage is **"the largest deterioration of 123 crises that month"**.

Comparing deltas across different metrics is also avoided: a 1.75 move in a sub-component is not "bigger"
than a 0.80 move in the headline index.

## Who can learn what

This replaces every "nothing leaves the device" claim.

| | Sees the answer before the reveal | Sees who wrote it |
|---|---|---|
| Other panel members | no | pseudonym only, and distinctive wording is still recognisable |
| The analyst | no | aggregates only, never an individual answer |
| Whoever operates this server | **yes** | yes, except for `anonymous` answers |
| The public ledger | aggregate only, and only at n ≥ 5 | never |

The commitment is `sha256(canonical_json(answer) + salt)` stored with `committed_at`. It proves when an answer was given
and that it has not changed since. It is not confidentiality from the operator. `anonymous` answers are stored with no
identity link at all, so they cannot be claimed or scored later — and the link's "used" flag records only *that* someone
answered, never which answer was theirs. Blind-signed credentials are the phase-2 path if anonymity from ACAPS itself is
required.

`n ≥ 5` is a disclosure rule, not an anonymity guarantee.

## What is real and what is not

**Real.** The 139 risks, their titles, probabilities, impacts, statuses and triggers all come from the committed ACAPS
Risk Radar export. So do the trigger completion rates the doorbell fires on — those are ACAPS's own published judgement,
not a signal we invented. The commitments, the aggregation, the Skeptic checks, the Judge scores, the verify hash and the
Brier scoring are all computed, not staged.

**Synthetic.** The eight experts and their answers come from `engine/seeding.py`. They are labelled synthetic in the API,
on every screen footer and in the ledger's own caveat. Their answers are not evidence about Chad or anywhere else.

**Assumed.** Probability is a five-band text field in the export. Scoring needs a number, so `data.PROBABILITY_BANDS`
maps each band to its midpoint. ACAPS publishes the bands, not these midpoints, and the mapping appears in the rationale
of every draft so nobody can mistake it for an ACAPS figure. Scoring is against Probability, never Risk Level — Risk
Level is derived from Probability × Impact, so scoring it would score our own arithmetic.

**Not built.** The live ACAPS API is wired but runs from the cache: `ACAPS_API_TOKEN` is unset, so
`/radar/status` reports `token_present: false` and every edition is badged `cache` on screen. The published
`risk-list/` endpoint is history (214 rows, last updated Jul 2025, no R1000+ ids), which is why the active
risk list comes from the CSV export instead.
No external timestamp anchor — Verify recomputes the hash from the round's commitments and says exactly that. The agent
loop behind `FF_AGENTS` is not wired: the draft generator is the deterministic template, which is the default the spec
asks for. The store is in process and rebuilt on restart; it is not a system of record.

## Limits worth saying out loud

- One round with a synthetic panel is a **sensitivity test, not proof** that the method works.
- There is no structured rating history in the export, so no "we moved earlier than ACAPS" claim is possible, and none
  is made.
- Integrity notes are **descriptions, not diagnoses**. Nothing in them penalises an expert or changes a weight; the
  analyst reads them and decides.
- Reliability weights start equal, shrink toward a prior and are capped. One round never makes a super-estimator, and
  the board stays empty until an expert has five resolved risks.
- A question contract must be frozen before a risk can be resolved, otherwise the score settles a question nobody agreed
  to. `/risks/{id}/resolve` returns 409 until it exists.

## Repository

```
engine/        FastAPI app, store, aggregation, deterministic draft, scripts, tests
  engine/      api.py  store.py  draft.py  data.py  acaps.py  alerts.py  seeding.py  settings.py
  scripts/     seed.py  demo_replay.py
  tests/       53 tests: disclosure floor, blinding, integrity, ledger, scoring, alert engine
ui/            Lane B's frontend (React 19 + Vite): entry, workspace, radar, alerts,
               expert card, analyst desk, public ledger, committee gateway, stage
data/          ACAPS Risk Radar export, its data dictionary, and cached monthly API editions
fixtures/      example payloads for every route, validated by make check
docs/          master prompt, contracts, question contract, privacy engineering
app.yaml       deployment contract
Dockerfile     node build of the UI, then one python process serving both on 8080
```

## Team

Zain Ul Haq (backend) · *name* (frontend) · *name* (research and pitch).
Challenge: ACAPS Ground Truth, Hackathon for Good #8.
Synthetic experts only. ACAPS Risk Radar data under ACAPS terms of use.
