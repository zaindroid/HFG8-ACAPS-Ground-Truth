# Sealed Signals

Sealed Signals is the Risk Radar platform ACAPS does not have: the live Risk List from the ACAPS API, with an expert loop,
descriptive integrity notes and a public audit trail on top. An ACAPS analyst (or, in phase 2, an indicator doorbell)
sends a one-minute question to the eight best-matched vetted experts. Experts answer on their phone behind a mask they
choose, with ACAPS's rating hidden until after submission. Answers are committed with a timestamp, opened together,
summarised as an equal-weight mean with spread and minority reasons, annotated with integrity notes the analyst reads,
turned into a cited draft the analyst accepts, edits or rejects, and published as a group view on a ledger with an honesty
box that states what fed into it, its limits and its misses. When the risk resolves, forecasts are scored committee-side
and every panel member gets the group outcome report. Nothing publishes itself.

*The machine rings the doorbell, the panel answers, the analyst decides, the ledger remembers.*

Challenge: ACAPS "Ground Truth", Hackathon for Good #8, The Hague, 6-8 Nov 2026. Demo risk: R1043, escalating cross-border insecurity in eastern Chad.

## Why

ACAPS rates risks on probability and impact. Among the 104 resolved risks in the Risk Radar export, 32 of 38 High-rated risks materialised (84 %), but only 27 of 58 Medium-rated risks did (47 %). A Medium rating is close to a coin flip, and a reader cannot tell how it was reached or how often the ratings are right.

What we learned from ACAPS on 6 Nov:
- Experts are informed professionals who already track crises, not sources on the ground. They are matched on geography and theme, and a committee approves them.
- 32 analysts track their countries daily, score risks by hand and update weekly.
- There is no platform. Risk Radar is a dataset and an API.
- A panel could lean one way. The tool must be one validation layer among others, products never change automatically, and ACAPS must say what fed into each product. In the mentor's words: "We will get things wrong, like a prediction market; the point is honesty about it."

Sealed Signals is our answer: a loop that asks the right people at the right moment, keeps a verifiable record of what they said and when, leaves the decision to the analyst, and publishes its own limits and misses.

More: [impact](docs/sealed-signals/impact.md) | [integrity and honesty](docs/sealed-signals/bias-and-honesty.md) | [privacy engineering](docs/sealed-signals/privacy-engineering.md) | [question contract](docs/sealed-signals/question-contract.md) | [judging checklist](docs/sealed-signals/judging-checklist.md) | [demo script](docs/sealed-signals/demo-script.md) | [future work](docs/sealed-signals/future.md)

## How it works

```mermaid
flowchart LR
  A[Analyst trigger] --> B[Matched panel]
  B --> C[Committed answers]
  C --> D[Integrity notes]
  D --> E[Cited draft]
  E --> F[Analyst decision]
  F --> G[Ledger with honesty box]
  G --> H[Scoring and outcome report]
  H -.-> B
```

1. **Trigger.** The analyst sends a one-minute question for a risk. Phase 2: an indicator doorbell, using indicators the analyst picks from a menu for that risk, suggests a pulse.
2. **Matched panel.** Up to 8 approved experts, picked by geographic and thematic tags, with no more than 3 from one affiliation type.
3. **Committed answers.** One card, about a minute, magic link, no login. ACAPS's rating is hidden until after submission. The expert picks a mask: known, pseudonym or anonymous. Each answer is committed with a timestamp.
4. **Integrity notes.** For the analyst only. Descriptions such as "round 2 answers moved toward the mean without new reasons" or "no displacement expert on this panel". They do not judge anyone and change nothing automatically.
5. **Cited draft.** By default a fixed template: every sentence names its aggregate, indicator or source. Claims that cannot be checked go to a verification queue; absence from the databases we search is not evidence they are false.
6. **Analyst decision.** Accept, edit or reject. Only this step changes a rating.
7. **Ledger.** Group view next to the ACAPS rating, a Verify button, and an honesty box: contributors, agreement, spread, gaps, claims corroborated and queued, hit rate and misses, a caveat, the decision it could inform, and the analyst's reason when the panel view was rejected.
8. **Scoring.** After a frozen question contract, forecasts are scored (Brier), committee-side. Everyone who answered receives the group outcome report. Calibration is private and opt-in after 5 resolutions.

Who can learn what: master prompt section 1a, reproduced in [privacy engineering](docs/sealed-signals/privacy-engineering.md). Commitments prove timing and consistency and stop peers anchoring on each other. They do not hide answers from the operator.

## Run

```
pip install -r engine/requirements.txt
make seed && make dev        # API on :18000
make ui                      # frontend on :5173
make demo                    # full loop on R1043, offline
make check                   # tests, UI build, fixture validation
```

Lane A and Lane B own this section and the architecture detail.

## Synthetic and live

| Part | Status |
|---|---|
| ACAPS Risk Radar export (139 risks, 57 countries, 104 resolved) | Real ACAPS data, used under ACAPS terms |
| Live Risk List through the ACAPS API | Live when a token is set; otherwise the CSV export is used. The badge on the Radar view says which. |
| Experts, panels, answers | **Synthetic.** No real expert data is used, as the challenge requires. Labelled "synthetic" in the product. |
| Indicator history for the Chad replay | Stored aggregated counts (`data/synthetic/indicators_chad.csv`), used only to show phase 2. Lane A to state whether the counts are real or generated. |
| Sensitivity test on the 104 resolved risks | Real outcomes, synthetic panels, several scenarios (mixed accuracy, shared bias, correlated errors, pure noise). Tests the software and says nothing about real experts or timing. |
| Draft update | Deterministic template by default. The agent loop (`FF_AGENTS`) is off unless stable. The demo states which ran. |
| Other flags | Default to the offline path. We never claim a path that is off. |

## Limits

- Everything about expert behaviour is untested with real experts. The pilot is the first real test.
- The sensitivity test checks the pipeline under assumptions. It does not show that real experts are accurate and makes no claim that the panel moves earlier than ACAPS. The export has no structured rating history.
- Commitments give timing and consistency, not secrecy from the operator. ACAPS admins can see answers with the mask the expert chose. The identity registry is restricted and logged. `anonymous` answers are stored without identity and cannot be claimed later. Anonymity from ACAPS itself would need blind-signed credentials (phase 2).
- An aggregate of 5 or more contributions is a disclosure rule, not an anonymity guarantee. On a small panel a distinctive reason can be recognised by peers; the card says so.
- A small panel can lean one way. We cap composition, show coverage gaps in public and rely on a committee gateway. We cannot prove independence.
- Integrity notes describe the data. Seeded tests show the code produces the intended note. They are not a claim about sensitivity or specificity.
- The ACAPS risk status that resolves a question is set by ACAPS, which is also the rating under test. We disclose this.
- Older imported ACAPS risks resolve over much longer periods than six months, so the 84 % and 47 % rates mix time frames.
- Impact: anticipatory-action evidence on cost and speed comes mostly from floods, droughts and harsh winters. We do not claim the same for conflict risks. See the impact note.

## Team

Zain Ul Haq (backend) | (frontend: name to add) | (research and pitch: name to add)

## ACAPS data terms

The Risk Radar export is shared by ACAPS for this challenge and is used under ACAPS's terms of use. Do not redistribute it outside this repository. No personal data of real experts is used.
