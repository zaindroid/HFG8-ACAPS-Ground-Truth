# Sealed Signals

**Expert checks on ACAPS risk ratings that are easier to contribute to, easier to scrutinise, easier to trace.**

Team submission to the ACAPS "Ground Truth" challenge, Hackathon for Good #8, The Hague, 6–8 November 2026.
Team: Zain Ul Haq (backend), Saleeta Qadir (frontend), Sho Izuno (research and pitch).

`AGENTS.md` maps the repository and says how to verify each claim. Test output, the demo transcript and screenshots
are under `docs/evidence/`.

## 1. The problem

ACAPS rates humanitarian risks (probability, impact, triggers) for more than a hundred crises. In the Risk Radar export
shared with the challenge, 27 of 58 resolved Medium-rated risks materialised (47 %, a coin flip) and 32 of 38 High-rated
risks did (84 %). ACAPS has a documented methodology and peer review for its scheduled products. The expert checks
between those reviews, by email and conversation, are not structured, not time-stamped and not auditable; experts will
not sign up to a portal to change that; and nobody can see the bias in a panel or the record of its misses.

## 2. The solution in five steps

| Step | What happens | Which problem it answers |
| --- | --- | --- |
| 1 Alert | A deterministic diff of ACAPS's monthly INFORM severity and humanitarian-access editions finds the moves and ranks them across all crises. No model. It proposes; the analyst approves or dismisses. | Ratings go stale between reviews |
| 2 Ask | The analyst freezes a question contract (event, place, threshold, deadline) and Reach composes the message for each of the eight best-matched vetted experts on the channel they already use -- email, WhatsApp, Signal, SMS, Teams or a scheduled call -- around one magic link. No sign-up. In this build the messages are composed and recorded, not sent: there is no gateway here, and the product says so rather than showing a tick. | Experts never sign up |
| 3 Answer | One screen, one required tap, mask chosen per answer. ACAPS's rating is hidden. The answer is committed with a salted SHA-256 hash and a timestamp on confirmation, and all answers are revealed together at the deadline. | Anchoring, herding, social pressure |
| 4 Check | Equal-weight mean, spread, unattributed disagreement, missing evidence, descriptive bias notes. An Investigator, Skeptic and Judge turn the panel view into a cited draft; a checker rejects any number not exactly in a versioned record. | Bias nobody could see |
| 5 Decide and record | The analyst accepts, edits or rejects, with "what decision, for whom, by when". The public ledger keeps the group view, an honesty box, a Verify action and the misses. Scored at panel level when the risk resolves; every expert receives the outcome report. | No trail, no feedback, no misses |

Nothing publishes itself. Sealed Signals is one validation layer among others inside ACAPS's own analysis workflow.

## 3. The must-haves of the brief, built

| Must-have (organisers' wording) | Where it is in the product | Where it is in the code |
| --- | --- | --- |
| Easy to use | One screen at `/e/:token`, one required tap, under a minute, no account, any channel the expert already uses; a plain reply or a voice note also counts | `ui/src/ExpertCard.tsx`, `engine/engine/api.py` (`/e/{token}`), `engine/engine/reach/` |
| Expert-controlled anonymity | The mask is chosen per answer, with no default: named to ACAPS, nickname to peers, no identity kept; the limit is stated on the screen | `Answer.mask` in `engine/engine/store.py`; pseudonym = HMAC of an internal id; restricted identity registry with logged access |
| Public anonymity | The public ledger and every public aggregate show n ≥ 5 and never an individual answer, name or pseudonym | `scripts/validate_fixtures.py` fails on any aggregate with n < 5; `GET /api/ledger` strips individuals |

Should-haves: sustained engagement without engagement metrics (outcome report to every expert, one pulse a week at most
and STOP by one word, both enforced in `engine/engine/reach/cadence.py` and tested in `engine/tests/reach/`); short contributions (one screen); small trusted groups (eight per panel, committee-vetted,
affiliation cap). Should-nots respected: no engagement metrics, no chatbot feel (the expert never talks to a model).
Could-haves: agreement and disagreement by region on the desk; mobile and 2G-friendly expert screen; English and French
parsing of replies. Can-have: AI behind the scenes only, model-optional, never expert-facing.

## 4. Architecture

```
ACAPS API (live, cached in data/acaps-api/)            Risk Radar export (data/, 139 risks, 104 resolved)
  inform-severity-index/<MonYYYY>, humanitarian-access/<MonYYYY>, crises/, risk-list/
        |
        v
  Risk Alert Engine (engine/engine/alerts.py)  diff, rank, link to the active risk, propose
        |  analyst approves (question contract frozen)
        v
  Reach (engine/engine/reach/)  email, WhatsApp, Signal, SMS, Teams, call; magic link; inbound parsers; consent and STOP
        |
        v
  Expert screen (ui/src/ExpertCard.tsx)  one tap, mask per answer, confirm -> salted SHA-256 commitment
        |  reveal at the deadline
        v
  Aggregate (equal-weight mean, spread, unattributed disagreement) + descriptive integrity notes
        |
        v
  Draft loop (engine/engine/draft.py)  Investigator -> Skeptic -> Judge, model-optional, every number checked
        |  analyst accepts / edits / rejects, on record
        v
  Public ledger (ui/src/LedgerRecord.tsx)  honesty box, Verify (recomputes the commitment root), outcomes, misses
        |
        v
  Resolve: panel-level Brier, outcome report to every expert, opt-in private calibration
```

Technology, and where each piece does its work:

| Piece | Where | What it does |
| --- | --- | --- |
| ACAPS API client with offline cache | `engine/engine/acaps.py`, `data/acaps-api/` | Live monthly editions with a token; cached editions without one; `GET /api/radar/status` says which |
| Risk Alert Engine | `engine/engine/alerts.py` | Month-over-month diff per crisis, thresholds (index Δ ≥ 0.5, component Δ ≥ 1.0, category change, access Δ ≥ 1), rank across crises, replay of March→April 2026 |
| Commit-and-reveal | `engine/engine/store.py` | `sha256(canonical_json(answer) + salt)` stored before anyone sees the answer; reveal at the deadline; Verify recomputes the round root |
| Masks and registry | `engine/engine/hardening/registry.py` | Per-answer mask; HMAC pseudonyms; identity map encrypted with ML-KEM-768 hybrid key establishment and AES-256-GCM at rest; every read logged |
| Blind-signed credentials | `engine/engine/hardening/credentials.py` | RSA blind signatures (RFC 9474); one-time token per answer; reuse rejected; unlinkable to the approval |
| Attestations and anchoring | `engine/engine/hardening/attest.py`, `anchors.py` | ML-DSA-65 signatures on resolved ledger entries; daily Merkle root submitted to OpenTimestamps, shown as pending until confirmed |
| Verification loop | `engine/engine/draft.py` | Deterministic template by default; Investigator, Skeptic, Judge behind `FF_AGENTS`; exact provenance, uncorroborated claims held in a queue |
| Reach | `engine/engine/reach/`, `engine/engine/inbound/` | Email, WhatsApp, Signal, SMS, Teams (`FF_TEAMS`, off), scheduled call, IVR (`FF_IVR`, off); one magic link in every channel; inbound parsers (percentages, spelled numbers, keypad digits, the five-word scale, abstentions, mask words, STOP and PAUSE, English and French), voice-note read-back, cadence caps. **Nothing is sent**: no gateway or mailbox is configured, so every message is composed in full and recorded in an outbox you can read at `GET /api/reach/outbox`, and every payload says `transport: recorded` |
| Scoring and calibration | `engine/engine/hardening/calibration.py` | Frozen question contract before scoring; Brier at panel level; consent-gated calibration programme (`FF_CALIBRATION`, off) |
| Frontend | `ui/` | React and Vite; expert screen, analyst desk, public ledger, Risk Radar; Playwright tests |

## 5. Run it

```
make install        # python and UI dependencies, from a clean clone
make demo           # the full loop on R1043 with the synthetic panel, offline, under 60 s
make dev            # API on :18000 and the built UI at /
make check          # pytest, UI build, fixture validation
```

Optional: an ACAPS API token in `engine/.env` (`ACAPS_API_TOKEN`) makes the Radar and the alert engine live; without
it the cached editions in `data/acaps-api/` are used and the UI says so. The engine refuses to start without
`COMMITMENT_SALT` and `PSEUDONYM_KEY`; `make dev` loads `engine/.env.example`.

## 6. Evidence

In the repository now: `docs/evidence/make-check.txt` (194 engine tests, the UI build, 77 fixtures validated),
`docs/evidence/make-demo.txt` (the full offline loop, fifteen steps, under three seconds) and
`docs/evidence/tree.txt` (every file we wrote). `scripts/capture_evidence.sh` regenerates all three from a clean
clone. Screenshots of the three screens at phone and desktop width, and the measured time and taps on two real
phones, are added by the frontend lane at the Sunday freeze.

## 7. What is real and what is synthetic

Real: the ACAPS Risk Radar export (139 risks, 104 resolved) and the ACAPS API editions (risk list, crises, countries,
monthly INFORM severity and humanitarian access, cached for the demo). The April 2026 move for crisis TCD005,
"Displacement from Sudan to Chad" (index 6.1 → 6.9, the largest of 123 crises that month), is real and drives the demo.
Synthetic: every expert, panel and answer, labelled as synthetic in the UI. No real expert data is used anywhere.

## 8. What we do not claim

Reach does not send messages, and its lock-screen rule has a stated limit: the subject carries no
province and every message opens with a crisis-level line, but the frozen question names the provinces ACAPS's own
published risk names, because an expert cannot answer a question they have not been shown -- and an SMS is one line,
so its whole message is the preview. No SMTP server, WhatsApp Business account, SMS gateway or Teams app
registration exists in this repository, so every channel composes the real message body and records it; the delivery
view reports `transport: recorded` on every row and the outbox is readable. One function, `Reach.deliver`, is what a
pilot replaces. Channel preference is a design hypothesis until a recruited panel says otherwise, and the personas are
hypotheses too, not evidence.

Commitments prove timing and consistency and block peer anchoring; they do not hide answers from the operator. Masks
give confidentiality from peers and the public with defined, logged ACAPS access; they are pseudonymisation, not
anonymity from ACAPS, and the product says so. Timestamp anchoring is a timestamp, not a blockchain product. The
backtest in `reports/proof.json` is a transcript of one offline run of the loop, not a statistical result: the
sensitivity test over the 104 resolved risks under mixed-accuracy, shared-bias and correlated-error scenarios is
specified in MASTER_PROMPT section 7 and is not built, so nothing here says anything about real experts and nothing
claims a timing advantage over ACAPS. Scores are
for forecasts, panel-level, never for people; nothing is measured about an expert without consent. Integrity notes
describe patterns; they never diagnose a person.

## 9. Pilot

Ready for a supervised pilot of this workflow: one crisis (eastern Chad), one panel of eight real experts with consent
from the analyst's own contacts, three months, ACAPS's Risk Radar manager as the analyst. Measured: experts still
answering in week 8, minutes per weekly update, panel mean against the rating on questions that resolve. Usability now;
forecast quality only when questions resolve.

## 10. Documents

`docs/sealed-signals/MASTER_PROMPT.md` (the specification, with changelog), `contracts.md`, `trust-design.md`,
`privacy-engineering.md`, `reach-design.md` (the design as reviewed, superseded notes included), `question-contract.md`,
`personas.md`, `judging-checklist.md`. The organisers' original files are unchanged under `docs/challenge/`, `data/`,
`references/` and `notebooks/`. The pitch deck is `pitch/sealed-signals-slides.html`.

ACAPS data is used under ACAPS's terms of use. Licence: see `LICENSE`.
