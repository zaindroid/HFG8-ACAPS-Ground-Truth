# AGENTS.md — repository map and how to verify each claim

Start with `README.md`. This file says where each part lives and which test or command checks it.

## Layout

| Path | What it is |
| --- | --- |
| `engine/` | FastAPI backend: ACAPS API client with cache, Risk Alert Engine, expert loop (pulses, commitments, reveal, aggregation), draft verification loop, ledger, scoring, Reach (channels, inbound parsing), hardening (registry encryption, attestations, blind credentials, anchoring, access log). Tests in `engine/tests/`. |
| `ui/` | React + Vite frontend: expert screen `/e/:token`, analyst desk (`/alerts`, `/desk`, Reach, committee), public ledger `/ledger`, Risk Radar `/radar`. Playwright tests. |
| `fixtures/` | Example payloads for every API route, regenerated from the running API; validated by `scripts/validate_fixtures.py`. |
| `data/acaps-api/` | Cached ACAPS API editions (risk list, crises, countries, monthly INFORM severity and humanitarian access) so the demo runs offline. `data/acaps-api/README.md` documents the endpoints as verified. |
| `data/risk-radar-export.csv` | The organisers' Risk Radar export, 139 risks, 104 resolved. Unchanged. |
| `docs/sealed-signals/` | Specification and design: `MASTER_PROMPT.md` (the spec every lane built against, with its changelog), `contracts.md`, `trust-design.md`, `privacy-engineering.md`, `reach-design.md`, `question-contract.md`, `personas.md`, `judging-checklist.md`, and the research and pitch notes: `impact.md` (stakeholders, ACAPS's method, impact chain), `bias-and-honesty.md` (the sources behind each bias design), `judging-moscow-map.md`, `demo-script.md`, `pitch.md`, `future.md`, `proposals.md` (open items found by research). |
| `docs/evidence/` | Committed outputs: `make-check.txt` (tests, UI build, fixture validation), `make-demo.txt` (the offline loop transcript), screenshots of the three screens at phone and desktop width, `sensitivity.png`. |
| `docs/challenge/` | The organisers' original README and CLAUDE.md, unchanged, for reference. |
| `pitch/` | The six-slide deck (`sealed-signals-slides.html`, open in a browser) and its contact sheet. |
| `slides/` | Presentation variants: `make-animated/` (the Figma Make animated deck as a Vite project) and `motion-v2/` (an animated HTML deck and a demo walkthrough video). The pitch itself uses `pitch/`; these have not been checked against the figures in `proposals.md`. |
| `reports/` | Generated outputs of the sensitivity test. |
| `Makefile` | `make install`, `make check`, `make demo`, `make dev`, `make ui`. |

## How to verify each claim

| Claim | Command or file |
| --- | --- |
| The test suite passes | `make check`; committed output in `docs/evidence/make-check.txt` |
| The full loop runs offline from a clean clone in under 60 s | `make demo`; transcript in `docs/evidence/make-demo.txt` |
| The alert engine reproduces the April 2026 Chad move (TCD005, 6.1 → 6.9, the largest deterioration of 123) | `engine/tests/test_alerts.py`; `POST /api/alerts/replay` with `{"month_from":"Mar2026","month_to":"Apr2026"}`; fixture `fixtures/POST_alerts_replay_response.json` |
| Answers are committed before reveal and a link click never commits | `engine/tests/test_loop.py` (confirm step, correction before deadline, reveal refused before the deadline, n < 5 never revealed) |
| Masks are chosen per answer; the public ledger never returns an individual | `engine/tests/test_loop.py`; `scripts/validate_fixtures.py` fails on any aggregate with n < 5 |
| The draft checker rejects a number not in a record and holds unsourced claims | `engine/engine/draft.py`; `engine/tests/test_loop.py` |
| Hardening: encrypt/decrypt round trip, attestation fails on a flipped byte, blind token reuse rejected, anchor pending → anchored, registry reads logged | `engine/tests/hardening/` |
| Pattern reports never name a person; calibration items never appear on a pulse card | `engine/tests/hardening/test_patterns.py` |
| The country scan answers the brief's example question, hides ACAPS's view, shuffles per link, reveals at the deadline, keeps added risks out of the result | `engine/tests/test_scan.py` |
| Every API route has a true example payload | `fixtures/` and `scripts/validate_fixtures.py` |
| The UI builds and the three screens render | `make check`; `docs/evidence/screens/` |
| What is live and what is cached | `GET /api/radar/status` reports source and fetched_at per dataset; `data/acaps-api/README.md` |

## Feature flags

`FF_PQ`, `FF_BLIND`, `FF_ZK` (off), `FF_ANCHOR`, `FF_AGENTS` (off, model-optional), `FF_CALIBRATION` (off,
consent-gated), `FF_IVR`, `FF_TEAMS`, `LLM_BASE_URL`. Every flag has a deterministic fallback so the demo never blocks;
the README and the UI state which path ran. Nothing in the pitch depends on a flag that is off.

## What is synthetic

Experts, their answers and the panel are synthetic and labelled as such in the UI and in `data/synthetic/`. ACAPS data
(export and API editions) is real and used under ACAPS's terms. The sensitivity test on the 104 resolved risks is a
software and sensitivity test of the pipeline; it says nothing about real experts and makes no timing claim.
