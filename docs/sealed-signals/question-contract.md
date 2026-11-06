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

## Lane C review of the R1043 draft (7 Nov)

For the analyst to settle before the contract is frozen. We have not changed the frozen text above.

1. **Make the event about new incidents.** The risk text says repeated drone strikes and incursions already caused casualties on Chadian territory in 2026, and the 30 Sep update mentions "the August strikes". If the event is not tied to the pulse date, it could resolve "yes" on events that predate the question. Suggested wording: "After the pulse date, cross-border armed incursions ... cause ...".
2. **Define "significant deterioration".** The risk record's own quantitative objective for its first trigger reads: completion if "cross-border attacks become sustained and recurrent, affecting multiple border localities in eastern Chad and causing significant civilian casualties, displacement, or humanitarian access disruptions." Using that wording ties the question to ACAPS's own definition.
3. **Name who rates what.** The resolution source is the ACAPS Risk Radar status, set by the ACAPS manager. That is ACAPS judging the rating under test. This is acceptable for a pilot but must be disclosed in the honesty box and in Q&A.
4. **Partial materialisation.** The draft records it as a note and does not score it. State what counts as "partial" in advance (for example, a single incident, or incidents in one locality only) so the adjudicator does not decide afterwards.
5. **One question for experts.** The card's probability is for the event as written here, over the same horizon. The text in the risk title (protection risks and humanitarian needs) is broader than the event line. Use the event line on the card.
6. **Export data caveats.** The record has no structured rating history, and "Date entered" and updates are in free text. Do not claim a timing comparison.
