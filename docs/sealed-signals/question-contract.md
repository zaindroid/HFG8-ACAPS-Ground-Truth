# Question contract (frozen before any scoring)

One per risk. Nothing is scored without it. Changing it after the first pulse creates a new contract version; earlier
forecasts are scored against the version they answered.

| Field | R1043 (example, to be confirmed by the analyst) |
|---|---|
| Risk ID | R1043 |
| Event (one sentence) | Cross-border armed incursions from Sudan into eastern Chad cause a significant deterioration in protection and humanitarian needs in Ouaddaï, Wadi Fira, Sila or Ennedi Est. |
| Location | Eastern Chad: Ouaddaï, Wadi Fira, Sila, Ennedi Est |
| Horizon deadline | 6 months from the pulse date (e.g. pulse 7 Nov 2026 → 7 May 2027) |
| Resolution source | ACAPS Risk Radar status for R1043 (materialised / not materialised), with OCHA and UNHCR Chad situation reports as supporting evidence |
| Adjudication rule | The ACAPS Risk Radar manager sets the status; "materialised" requires the hazard and the humanitarian impact as described in the risk's "What materialised?" field; partial materialisation is recorded as a note, not a score |
| Frozen at | (timestamp when the analyst freezes it) |

## Lane C review of the R1043 contracts (8 Nov)

Two contracts exist for R1043. The table above is the template draft (cross-border armed incursions). The product's seeded contract (`QUESTION_CONTRACT` in `engine/engine/seeding.py`, shown on the card) asks: "Will more than 50,000 new arrivals from Sudan be registered in Ouaddai and Wadi Fira by 31 March 2027?", threshold more than 50,000 newly registered arrivals cumulative from 1 November 2026, resolved from UNHCR registration figures nearest the deadline. The card and the ledger use the seeded one. Points for the analyst, who freezes whichever is used:

1. **Which risk does it test?** R1043 is about cross-border insecurity. Registered arrivals measure the displacement driver (the crisis TCD005), not an attack. Arrivals can pass the threshold with no attack, and an attack can occur without 50,000 arrivals. The ledger should say the question is a proxy for the risk and name what it measures.
2. **Is the threshold informative?** The 30 September update records more than 400 arrivals a day, about 20 times the earlier rate [data: R1043 "Rationale update"]. From 1 November to 31 March is 151 days; 151 times 400 is 60,400. The 50,000 line sits below a straight-line extrapolation of that rate, so the question may resolve yes without any change in conditions. Either raise it, or state the extrapolation on the card as the base case so the panel is forecasting a change, not a continuation.
3. **Resolution source.** "UNHCR registration figures for eastern Chad, as reported to ACAPS" must exist at province level for Ouaddai and Wadi Fira. If only a national or four-province figure is published, the adjudication rule cannot be applied. Confirm the source publishes that breakdown before freezing.
4. **Who adjudicates.** The adjudication is by the committee (as the scoring slide states), not by the analyst who approved the pulse. For the template draft above, the ACAPS Risk Radar manager sets the status, so ACAPS judges its own rating. Disclose it in the honesty box.
5. **Partial resolution.** State in advance what counts: a revision published after the deadline does not reopen the question (the seeded rule says so). Keep that sentence.
6. **Dates.** The template draft says pulse on 7 Nov 2026 resolves 7 May 2027; the seeded contract resolves on 31 March 2027, which is under five months. The master prompt says six months. Say which on the card.
