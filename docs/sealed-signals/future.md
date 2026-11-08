# After the hackathon: ranked features

Lane C. Revised for master prompt v3.4 (8 Nov). Ranked by value to ACAPS and risk of failure, highest first. Each item names the stakeholder it serves and what would have to be true. Order may change after the December pilot.

| Rank | Feature | Stakeholder served | Why this rank | What must be true |
|---|---|---|---|---|
| 1 | Supervised pilot with real experts: consent text, the analyst's own contacts, a committee that vets them | Committee, experts | Everything else depends on real experts joining and staying | ACAPS names the analyst and the committee; consent text reviewed by ACAPS; data terms agreed |
| 2 | Question drafting assistant: proposes the frozen question contract (event, place, threshold, deadline, adjudication rule) from the risk record, for the analyst to approve | Analysts, readers | The contract exists; drafting a good one (informative threshold, a published resolution source) is the workload | ACAPS agrees who adjudicates "materialised" and on what evidence |
| 3 | French card and consent text (replies are already parsed in French); Arabic after | Experts | The brief names French as a working language | Native-speaker review of every string |
| 4 | Retention without metrics: lapsed-expert re-invite by the analyst, cadence rules, thank-you wording tested with experts | Experts, committee | Expert pools lose people after launch [brief] | Week-8 participation measured in the pilot |
| 5 | External-feed alerts (ACLED, UNHCR, GDELT) beside the ACAPS monthly engine, as a per-risk menu the analyst chooses | Analysts | The monthly engine is blind between editions | False alarms stay low in the pilot; no timing claim versus ACAPS ratings |
| 6 | Production-grade security: audited post-quantum libraries instead of reference ones, committee keys in a hardware key store held by ACAPS, an independent review, a stable credential issuer key across restarts | Experts in sensitive contexts, committee | The build uses reference libraries, demo keys and a per-process credential issuer | ACAPS names a key holder; budget for a review |
| 7 | Voice-first answer on the device (speech to text on the phone; only text leaves) | Experts in the field | A spoken minute is easier than typing on a weak connection | On-device speech works offline in French and English; no audio is sent |
| 8 | Anticipatory-trigger export: a machine-readable "panel probability crossed X" signal for donors and agencies | Readers (UN agencies, INGOs, donors such as ECHO, FCDO, CERF, insurers) | Closes the impact chain. Trigger frameworks exist mostly for weather hazards, so start with a conflict-related partner who wants one. | A funder treats it as one input; legal review; the product still never acts alone |
| 9 | The zero-knowledge membership verifier (Groth16 check in the browser and on the server) and `FF_ZK` on | Experts in sensitive contexts | The tree and the nullifier are built; the proof check is not (`privacy-engineering.md` section 5) | Browser proof time under a few seconds on the lowest-end target phone |
| 10 | A public verification page anyone can run: recompute the round's commitment root, check the attestation and the anchor receipt | Readers, committee | Moves trust from our server to a check outsiders can repeat | Anchors confirm (hours); public key published and pinned |
| 11 | Machine panel member: a model forecaster, labelled as a model, scored like everyone else | Analysts | A baseline and a filler for thin contexts | It earns a track record before it gets weight; never mixed in silently; never expert-facing |
| 12 | Per-country panel dashboard for the analyst: panel health and coverage gaps over time | Analysts, committee | Keeps panels balanced as they grow | Enough pulses to show a trend |

Not planned: engagement scores, streaks, public leaderboards of named people, an expert-facing chatbot, scores that decide who is approved or removed.
