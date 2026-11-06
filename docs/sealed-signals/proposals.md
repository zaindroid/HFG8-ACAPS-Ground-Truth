# Proposals and open decisions (Lane C to the team)

Lane C does not edit `engine/`, `ui/` or `fixtures/`. Anything research suggests the product should change is here. Revised for master prompt v3; items v3 already fixed are listed at the bottom.

Priority: **M** = before the Sat 20:00 merge, **S** = before the Sun 10:30 freeze, **L** = after.

## Decisions for the humans

- **D1. Scoreboard.** The brief's Could row asks to "recognise consistently accurate experts". v3 says score forecasts, not people; committee-side only; never gate approval; calibration private and opt-in after 5 resolutions. Choose: (a) committee-only pseudonymous view, and say in Q&A that recognition is a pilot decision; (b) a pseudonymous panel-visible board after 5 resolutions. We recommend (a) for December.
- **D2. Proof slide.** v3 takes the synthetic results off the 3-minute headline (a sensitivity test, repo page and Q&A). Slide 5 in the deck is now a backup slide. The demo script spends that time on the ledger instead.
- **D3. Live minute in the pitch.** The jury exercise adds a countdown; the product has none. Decide whether the live step runs 60 seconds or is cut when 5 answers arrive.

## Proposals

### P1. Retention path (S) - Lane A + B
- Gap: "come back" and "sustained engagement". v3 added the outcome report. Still missing: a "lapsed" status on the committee view for an approved expert with no answer in 28 days, with a one-click re-invite. No streaks, no counts.

### P2. Question contract for R1043 (M) - the analyst, Lane A
- See "Lane C review" in `question-contract.md`. Four points: the event must say "new" incidents after the pulse date (the risk text says attacks already happened in 2026, so the question could resolve trivially); "significant deterioration" needs the export's own wording; resolution source is ACAPS itself (circular, disclose); partial materialisation rule.

### P3. Low-bandwidth budget and SMS stub (S) - Lane B, Lane A
- Page budget for the card (suggest under 100 kB, measured in `make check`). The `sms` channel has no route; flag it as a stub.

### P4. French card strings (S) - Lane B
- About 15 strings for the card and magic-link email. Arabic stays on the future list.

### P5. Merged regions note (S) - Lane B
- "Regions with fewer than 3 answers are combined."

### P6. Flags footer (M) - Lane A + B
- Footer on `/desk` and `/ledger`: "Draft: template. Agents: off. Anchor: off. Doorbell: phase 2 (replay)." We never claim a path that is off.

### P7. Demo panel must reach n of 5 or more (M) - Lane A
- If fewer than 5 jury answers are committed, the aggregate rule hides the result. Demo mode tops up with labelled synthetic answers. The desk shows live and synthetic answers apart.

### P8. Sensitivity test wording (M) - Lane A
- Label the output `sensitivity`, not `proof` (v3 section 7 already says so; the existing route is `/sim/proof` and the file `reports/proof.png`, which still say proof). Rename or caption it. Report the bootstrap as "resampling spread, not statistical confidence".

### P9. Hit rate for a new panel (S) - Lane A
- `panel_hit_rate` null shows "no resolved questions yet", not 0.

### P10. One "what fed into this" sentence (S) - Lane A + B
- Generated at the top of the honesty box from existing fields: "Based on 7 committed answers from a panel of 8, 2 of 3 claims corroborated, 1 in the verification queue."

### P11. Refugee figure (M) - team
- The master prompt (Lane C item 3) says "over a million Sudanese refugees in eastern Chad since 2023". UNHCR figures found were about 800,000 to 870,000 registered by mid-2025. Source a current figure or change the sentence. We use the verifiable wording.

### P12. Six-step method (L) - team
- No numbered ACAPS list found. Ask Alex for the official steps. impact.md labels its six-step grouping as ours.

### P13. Contradictions inside master prompt v3 (M) - whoever owns the file
1. Section 6a still says suspected herding means "the aggregate then uses round 1 (`used_round`)". The v3 changelog says no automatic fallback. Which holds?
2. Section 4 says "Palley & Soll" for peer-prediction weighting. The records show Palley and Soll 2019 is "pivoting"; peer-prediction weighting is Palley and Satopaa 2023. See `bias-and-honesty.md` 3.5.
3. Section 8b still lists "sealing", "reliability weights (super-estimator board)", "surprisingly-popular highlighted" and a "calibration report" as wired features. Under v3 the weights are secondary, SP is a labelled experiment, and calibration is opt-in after 5 resolutions.
4. Lane C item 6 lists "the proof chart" among slides; section 7 says the test is off the headline.
5. Section 8b still names the flags `FF_ZK` and `FF_ANCHOR`. The privacy page treats zero-knowledge membership and timestamp anchoring as research directions that are not in the build. Remove them from 8b or mark them off.

### P14. Demo trigger (M) - Lane B
- The analyst sends the pulse from a button on `/desk` (v3). The demo script uses it. The phone then receives the magic link. Confirm the button works end to end and that the email link opens the card on the phone.

## Done by v3 (kept for the record)

Question contract (now exists); group outcome report route; no extremizing; stance options on the card; no countdown in the product; scoring committee-side; honesty box fields for decision use and rejected panel view; privacy-engineering page created.
