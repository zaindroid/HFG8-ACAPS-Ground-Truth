# Lane B v2 implementation and handoff

Upstream: `0b30156`, `lane/frontend`, master prompt v2. The remote history was rewritten. The previous checkout and its uncommitted work remain intact; this fresh checkout imports only our UI work. Implementation changes are confined to `ui/`.

## Differences from v1

| Area        | Required v2 change                                                           | Frontend status                                                                                                                                                                                                      |
| ----------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Expert card | Blind round one, nullable agree, confidence, accuracy prompt, saw/read/heard | Implemented. Rating and rating-bearing question are hidden even if an older API includes them. Round two restores the rating.                                                                                        |
| Radar       | API/CSV provenance, searchable Risk List and country map                     | Implemented at `/`, also `/radar`; country geometry bundled locally, no map service required.                                                                                                                        |
| Gateway     | Geographic/thematic application, committee approval, panel matching          | Implemented at `/apply`, `/committee` and the desk matching panel. API mode trusts server approval state; mock mode requires two distinct synthetic admin choices.                                                   |
| Integrity   | Moderator-only checks and evidence, source origin/corroboration              | Implemented on desk only. Group content is withheld below five; regional statistics below three.                                                                                                                     |
| Drafts      | Claims, Skeptic verdicts, Judge scores; uncorroborated claims to verify      | Implemented. API approval is blocked if a referenced theme is not corroborated; request a refreshed draft or reject. Numeric support is distinguished from source corroboration.                                     |
| Ledger      | Public honesty box and resolved history                                      | Implemented. Contribution count comes from `honesty.n`. Coverage gaps, confidence band, corroborated/total claims, hit rate including misses, and caveat are visible. No pseudonyms or integrity flags are rendered. |
| Calibration | Private overconfidence alongside calibration                                 | Implemented when supplied; absent values remain unavailable. The fixtures have no overconfidence index or forecast-level calibration curve; none is fabricated.                                                      |
| Demo stage  | QR invitations, reachable LAN link, offline mock fallback                    | Implemented at `/stage`. Live links must come from backend-issued credentials.                                                                                                                                       |

## Backend integration gaps found in this checkout

The engine is a fixture-serving skeleton, not the completed backend. In particular, pulse lookup, SSE events, expert approval and risk resolution are not implemented. Application listing, credential evidence upload, admin authentication and credential/email delivery have no usable route in the current skeleton. The committee UI therefore accepts an application ID and sends the documented approval request; it does not invent an applications-list endpoint or administrative identity.

The ACAPS API token belongs in the backend environment, never in a VITE variable. The frontend obtains `/risks` and `/radar/status` from the engine. It reports CSV fallback honestly.

The v2 draft fixture includes C2 about night-time militia movement while the same theme is marked uncorroborated in `missing_checks` and single-source in the result. The UI retains this as a moderator review item and omits it from the grounded narrative. API mode blocks accepting or editing that draft until the backend removes or corroborates the claim. Mock accept/edit remains explicitly a presentation replay, not a live publication.

The integrity fixture says there is no displacement expert, while the matching fixture lists displacement experts and no composition gap. Both are displayed as independently supplied evidence; the frontend does not silently reconcile them. Lane A must regenerate consistent responses for the same pulse and panel.

## What verification proves

The private contribution story was dropped at the user's request. Its page, artwork, animation dependencies and links have been removed; private calibration remains. Jury access now identifies loopback addresses and warns when the displayed QR still uses a previous link. Desk responses are checked against the selected risk/pulse, and stale event results are ignored after switching context.

In addition to contract tests, `npm run test:scaffold` makes real HTTP requests through the Vite proxy to the existing local scaffold on port 18000. Nine browser checks exercise available paths and verify graceful failure of missing routes. No backend source was changed, and the API is still fixture-backed.

Mock browser tests exercise the offline UI. API-mode browser tests intercept network responses to test HTTP bodies, SSE handling, errors, masks, approval, public privacy thresholds, scoring requests and unavailable features. These are contract tests, not evidence of a working live scoring or cryptographic service. Fixture Verify is not a blockchain transaction. API Verify reports the backend's verdict and any supplied timestamp anchor.

## Before the merge and rehearsal

ACAPS reader workflows now live inside the existing visual system: country directory/context, searchable and filtered selected publications, topics/data services, and portal-wide search. Risk links use the existing `/risks` contract and take analysts to `/desk?risk_id=…`. Radar country names now open country context. No backend files or shared contracts changed. Official metadata is explicitly dated 6 November 2026; the curated catalogue includes seven profiles, four reports and seven resources. It is not a full or live mirror. Official downloads, subscriptions, complete archives and methodology remain on ACAPS. Browser checks cover discovery, empty filters, deep links, global search, accessibility and connected-service failure without fixture fallback.

The team scaffold and the organiser `main` currently have separate root histories. The preliminary frontend checkpoint preserves the team's existing `lane/frontend` history; a rebase onto `main` was attempted and aborted after root scaffold conflicts. No force push was used, no root conflicts were resolved by changing other lanes, and `main` was not changed. Future integration needs the team to reconcile that history deliberately.

- Connect to the completed engine and run the full R1043 flow, including two distinct authenticated committee admins.
- Test on two real phones over venue Wi-Fi. Use a LAN host or HTTPS invitation; loopback URLs do not work from another device.
- Check QR scan distance, source contrast and chart readability on the actual projector.
- Attach phone and desktop screenshots from `test-results/` and API screenshots from `test-results-live/` to the PR.
- Run the team's `make check` and offline `make demo` once Lane A completes them. Frontend build and browser checks cannot substitute for that integration test.
