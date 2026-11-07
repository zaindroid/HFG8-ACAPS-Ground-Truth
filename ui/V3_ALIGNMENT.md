# Lane B alignment with master prompt v3

Reviewed 7 November 2026 against the changelog, sections 1a, 4, 5, 6a, 8 and 10, question-contract.md and privacy-engineering.md. Upstream: `origin/demo` at `e73033f`. Implementation changes are confined to `ui/`.

## Where we had diverged and what changed

| Requirement | Frontend correction |
| --- | --- |
| Commitment proves timing/consistency, not confidentiality from the operator | Card explains operator access, restricted-registry design, peer/public visibility, distinctive-reason re-identification, and the disclosure threshold's limits. Fixture receipts remain explicitly synthetic. |
| Hidden rating, stances, no countdown | Round-one rating remains hidden. Product countdown removed. Estimate / outside my expertise / not enough evidence submit `stance`; abstentions send null probability, confidence and panel share. |
| Fixed peer elicitation | `panel_share_yes` asks what share will put probability above 0.5. Removed the old `agree` / `panel_guess` request fields. Receipt reads `committed_at`. |
| Mean is primary | Desk and round two show equal-weight mean. Shared desk chart shows min/max spread, IQR, minority reasons, secondary weighted mean and explicitly experimental SP. Probability-band mapping is labelled an assumption. |
| Descriptive integrity only | Moderator notes show text and evidence with neutral presentation. No suspected-herding/collusion verdict cards or automatic aggregation changes. Forecast scoring moved to the committee view. |
| Analyst-triggered first; automation phase 2 | Ask panel is primary. Doorbell action/replay log requires `VITE_FF_DOORBELL=1`; off by default. Indicator evidence remains labelled as replay context. No earlier-than-ACAPS claim. |
| Exact provenance, uncorroborated is not false | Legacy weighted-probability draft references and mismatched mean claims are withheld from the grounded narrative and block API approval. Uncorroborated themes remain a verification queue, with an explicit limits statement. Mock approval is a labelled replay only. |
| Decision-oriented ledger | Decision forms capture what decision, for whom and by when. Ledger honesty boxes show those fields, queued claims, misses, rejection of the panel view and analyst rationale. No individual rationale is public. |
| Frozen question contract before scoring | Desk edits the provided example and calls the new contract endpoint. Scoring remains disabled unless the response echoes the contract and supplies a valid `frozen_at`. A risk object or a successful HTTP status alone is insufficient. |
| Outcome report / opt-in calibration | Separate group outcome report checks matching pulse/result and at least five estimates. Private calibration does not fetch until opt-in, withholds scores below five resolutions, excludes timing claims and avoids showing a personal leaderboard on the desk. Anonymous responses offer no later-claim link. |

## Deliberate demo scope requested by the user

- `/` is a small ACAPS-connected entry page with selected official research links, not a full mirror of ACAPS.
- **Login** is a button that opens the demo workspace directly. There is no credential form or real authentication. A session marker only controls presentation; it does not secure HTTP endpoints or grant committee roles. Logout returns to the public page.
- Team tools, including the ledger view, sit behind that entry button for the presentation. This changes how the jury navigates, not the ledger's aggregate-only disclosure rules.
- `/e/:token` remains a no-login expert invitation as required by v3. Private calibration remains invitation-based and optional. These are the explicit exceptions to the team entry flow.
- The optional impact/contribution story remains removed. Country/publication discovery has been removed from the workspace; selected official links remain only on the public landing page. The hero remains the expert card, analyst desk and ledger.

## Backend/fixture dependencies still open

1. The v3 result fixture has mean 0.69, but the draft still cites `weighted_probability=0.78`, and the R1043 ledger retains 0.78. Do not silently relabel the old numbers as a new mean. API approval is blocked on the stale claim; mock ledger labels the discrepancy. Lane A must regenerate a consistent round, draft and ledger.
2. Calibration fixture still contains `moved_before_acaps` and a timing claim. The UI deliberately excludes both, and no longer treats weight as a personal achievement metric. A v3 backend should enforce opt-in and five-resolution eligibility.
3. The contract scaffold returns a Risk object, not a frozen QuestionContract. The UI rejects this confirmation, so actual scoring remains disabled until Lane A returns the promised version and timestamp. Binding contract versions to forecasts and preventing retrospective edits are server responsibilities.
4. Draft provenance does not yet carry all the source passages, publication dates and geography required by the tightened Skeptic. Frontend checks cannot establish that a factual claim is true. Deterministic draft generation, complete provenance and agent flags belong to Lane A.
5. The scaffold is fixture-backed. No real credential issuance, operator access controls, committee authorization, cryptographic sealing, outcome delivery or live scoring is established by frontend tests. Login is intentionally a demo button, not an access-control system.
6. Integrity and matching fixtures still disagree on displacement coverage. Both are presented as supplied evidence, not silently reconciled.
7. The master itself contains legacy wording in sections 6a/8b/9 (automatic fallback, proof chart, fixed earlier technology descriptions) that conflicts with its v3 changelog and updated contracts. This implementation follows the v3 changelog: descriptive notes, primary mean, sensitivity test, no timing proof, automation phase 2.

## Remaining rehearsal checks

The contract editor is available before a pulse; the group outcome report is independent of draft approval. API scoring is available after a recorded analyst decision, including rejection, and still requires a confirmed frozen contract. The mock editor is explicitly local and performs no scoring.

The ledger now includes a five-stage provenance visual with selectable details. It presents counts, the stored seal time, recorded decisions and the backend's verification verdict without inventing reveal/decision/verification timestamps. External anchors are shown as supplied proofs only after a valid receipt and matching timestamp. Demo matches, failed checks, absent anchors and unsafe proof URLs remain visibly distinct. A failed outcome refresh removes the previously displayed report.

Frontend verification covers public entry and logout, no-login invitations, nullable abstention payloads, equal-weight mean vs secondary weighting, opt-in/five-resolution calibration, invalid frozen-contract responses, mismatched outcome reports, proof-link safety, receipt timestamp mismatch, accessible ledger regions and responsive screenshots. The separate real-scaffold suite uses the fetched v3 API through the frontend proxy. This verifies presentation and contract handling, not cryptographic or production security claims.

Connect Lane A's completed implementation, run the full offline team demo and team checks, test two real phones on venue Wi-Fi, and verify the projector/QR scan distance. Browser simulations do not substitute for those checks. Lane C owns root README/pitch wording; its old claims should be audited against v3 as well.
# V3.1 update — 7 November 2026

Synced `origin/demo` through `b2bc37c`, including the v3.1 master prompt and `trust-design.md`. The earlier v3 assessment is historical; the v3.1 changelog supersedes its phase-2 automation guidance.

Implemented compatibility: the expert card and both desks render edition evidence (`before`, `after`, `delta`, months and change rank). Radar reads nested `risk_list` status and shows separate API/cache edition sources. Severity remains distinct from forecast probability. Existing legacy evidence remains readable.

Three-minute presentation update:

- Primary navigation is Alerts, Expert card, Analyst desk and Ledger; supporting tools are under More. The overview presents the same four-step Chad journey.
- Alerts supports current edition runs, April replay, compact selectable shifts, a marked severity trend, rule/rank/reliability, panel requests and note-required dismissal. API failures preserve the proposed alert; unsupported backend actions never appear successful. The local scaffold still needs the dismissal endpoint.
- Both desks show the ACAPS band beside the sealed/revealed equal-weight panel mean and spread. The expert card remains blind in round one. Ledger records remain compact and expandable with their existing verification trail.
- The local sample draft now cites the ACAPS edition change. Shared backend draft provenance remains Lane A's responsibility.
- Radar has expandable edition history, loaded from `/radar/editions` in API mode. The local view lists only the four retained INFORM editions and one access edition, not every month in the crisis-only trend.
- Alerts has expandable risk-link review: same-country active risks, crisis drivers and risk triggers, explicit analyst confirmation, and `POST /risks/{id}/link`. API confirmation requires reading the link back from `/crises/{id}`; panel routing refreshes from `/alerts` rather than inventing a new mapping locally.

Remaining frontend work beyond this presentation pass:

1. Add dedicated crisis browsing and component time-series (the Alerts detail currently shows severity history and component changes).
2. Confirm final edition-history response shape with Lane A. The UI currently accepts a dataset-to-months map or dataset rows with `months` in `editions`/`datasets`.
3. Rehearse against Lane A's implemented routes. At this sync the scaffold still lacks dismissal, link confirmation and edition history; their API-mode controls show the service error without a mock fallback.
4. The shared draft still cites older ACLED/UNHCR evidence and weighted probability. Preserve API approval guards until its provenance is consistent.
5. Audit copy against trust-design: no blockchain claims, no promise of anonymity from the operator, no public individual responses or moderator-only rationale. Commitments establish timing/consistency, not factual truth. External indicators remain later enrichment.

Validation: TypeScript, API-mode and mock production builds passed. All 54 frontend browser checks and 33 API-contract checks passed across phone, desktop and projector widths. The final chart-sizing change was checked again with the six Alerts journey cases. Alerts and Radar include accessibility checks. API-contract checks intercept HTTP responses; they do not establish backend security or missing scaffold capabilities.

Edition/link follow-up validation: mock production build and 18 targeted browser checks passed (12 local UI/journey checks and six API-contract checks). This includes unsupported endpoints, retry, same-country selection, explicit confirmation, read-after-write verification, unchanged routing after a failed confirmation, accessibility and responsive overflow checks.

