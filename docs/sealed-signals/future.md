# After the hackathon: ranked features

Lane C. Revised for master prompt v3 (7 Nov). Ranked by value to ACAPS and risk of failure, highest first. Each item names the stakeholder it serves and what would have to be true. Order may change after the December pilot.

| Rank | Feature | Stakeholder served | Why this rank | What must be true |
|---|---|---|---|---|
| 1 | Supervised pilot with real experts and a live committee: approvals, tagging, composition rules on real people | Committee, experts | Everything else depends on real experts joining and staying | ACAPS approves 8 or more experts for one country; consent text and data terms agreed |
| 2 | Question drafting assistant: proposes the frozen question contract (event, location, deadline, adjudication rule) from the risk record, for the analyst to approve | Analysts, readers | Scoring is only fair if "materialised" is clear. The contract exists; drafting it is the workload. | ACAPS agrees who decides "materialised" and on what evidence (question 3) |
| 3 | French, then Arabic, for the card, email and consent text | Experts | The brief names French as a working language | Native-speaker review of every string |
| 4 | Retention: lapsed-expert re-invite, quiet cadence rules, round 2 only when it adds something | Experts, committee | Expert pools lose people after launch [brief] | Pilot data on week-8 participation; no engagement metrics added |
| 5 | Phase-2 indicator doorbell: the analyst picks indicators per risk from a menu (ACLED, UNHCR, GDELT); the system suggests a pulse | Analysts | Saves the analyst watching; the analyst stays in control | Connectors with cached fixtures; analyst feedback on false alarms; no timing claim versus ACAPS |
| 6 | Blind-signed single-use credentials issued by the committee, so ACAPS cannot link an anonymous answer to a person | Experts in sensitive contexts | The honest answer to "anonymous from whom?". See `privacy-engineering.md`. | A written threat model (issuance timing, network metadata, revocation, scoring without linkage); question 7 answered |
| 7 | Voice-first answer on the device (speech to text on the phone; only text leaves) | Experts in the field | A spoken minute is easier than a text line in poor connectivity | On-device speech works offline in French and English; no audio is sent |
| 8 | SMS and WhatsApp reply formats | Experts with weak data | Contract already lists the channels | Channel cost and consent agreed; privacy review of message logs |
| 9 | Anticipatory-trigger export: a machine-readable "panel probability crossed X" signal for donors and agencies | Readers (UN agencies, INGOs, donors such as ECHO, FCDO, CERF, insurers) | Closes the impact chain. Trigger frameworks exist mostly for weather hazards, so start with a conflict-related partner who wants one. | A funder agrees to treat it as one input; legal review; the product still never acts alone |
| 10 | Machine panel member: a model forecaster, labelled as a model, scored like everyone else | Analysts | A baseline and a filler for thin contexts | It earns a track record before it gets weight; never mixed in silently; never expert-facing |
| 11 | Public timestamp anchoring of commitment roots (OpenTimestamps) with an independent verification page | Readers, committee | Gives an outside proof of timing. Not in the pilot build. | ACAPS wants outside timing proof; accepted service |
| 12 | Zero-knowledge group membership (Semaphore) and post-quantum protection of the registry (ML-KEM) and signed outcome attestations (ML-DSA) | Experts, committee | Research directions in `privacy-engineering.md`. None is in the pilot build. | A concrete threat that the pilot design cannot meet; security review |
| 13 | Per-country panel dashboard for the analyst: panel health and coverage gaps over time | Analysts, committee | Keeps panels balanced as they grow | Enough pulses to show a trend |

Not planned: engagement scores, streaks, public leaderboards of named people, an expert-facing chatbot, scores that decide who is approved or removed.
