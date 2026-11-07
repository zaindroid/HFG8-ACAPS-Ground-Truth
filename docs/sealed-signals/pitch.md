# Pitch

Lane C. Revised for master prompt v3.2 (7 Nov). Three minutes, eight slides. Timing and stage actions are in `demo-script.md`. This file holds the slide text, the speaker notes and the submission paragraph. Slides are built from `slides/index.html`.

Style: white background, one accent colour (deep teal), large type, one idea per slide, no emoji, no stock photos, no gradients.

## Slide text

1. **Problem.** Headline: "47 %". Line: "of Medium-rated ACAPS risks materialised. A coin flip." Small: "27 of 58 resolved Medium risks. High-rated: 32 of 38 (84 %). Source: ACAPS Risk Radar export."
2. **What ACAPS told us.** Four short lines, quoted or paraphrased as recorded: "Experts are informed professionals, not sources on the ground." "Experts apply; a committee approves." "There is no platform. Risk Radar is a dataset and an API." "We will get things wrong, like a prediction market; the point is honesty about it."
3. **The loop.** Eight stages in one row: alert engine (ACAPS monthly data, analyst approves), matched panel, committed answers, integrity notes, cited draft, analyst decision, ledger with honesty box, scoring. Caption: "The machine rings the doorbell, the panel answers, the analyst decides, the ledger remembers."
4. **Demo.** QR code and the text "Scan. You are the Chad panel. About a minute." (The 60-second countdown is part of the jury exercise only.) Before the QR: one line on the alert, "ACAPS's own severity index for the Sudan-to-Chad displacement crisis rose the most of 123 crises in April. The engine proposes a question; the analyst approves." Small: "Risk R1043, eastern Chad. Synthetic experts are labelled."
5. **Sensitivity test (backup slide).** The sensitivity chart. Caption: "Tests the software on 104 resolved risks with synthetic panels. Says nothing about real experts. No claim about timing." (Numbers from Lane A's sensitivity output.)
6. **Integrity and honesty.** Four lines: "Rating hidden until submission (anchoring)." "Equal-weight mean with spread and minority reasons." "Notes for the analyst that describe, not judge." "Honesty box: limits, misses, the decision it could inform." Footer: "One validation layer among others. Commitments prove timing, not secrecy from the operator. Hardening is built, each item with its limit: see the trust page."
7. **Impact and stakeholders.** Five names: analysts, experts, readers, committee, affected people. Line per group, one phrase each. Footer: "Better probability, earlier decision, anticipatory funds, pre-positioned aid. Evidence strongest for floods and drought; conflict is the open test."
8. **Ready for a supervised pilot of this workflow.** Pilot: "Two months, one committee, eight experts, one country. Measures: panel mean vs ACAPS Probability band on questions that resolve, minutes saved per update, experts still answering in week 8." Team: Zain Ul Haq (backend) | (frontend: name to add) | Sho Izuno (research and pitch).

## Speaker notes

- Slide 1 (0:00): Say the numbers, then the point. "A donor cannot act on a coin flip."
- Slide 2: skip when time is short. The quotes go on the slide; read at most the last one.
- Slide 3: do not read the eight stages. Point at the row; name only the ones the demo shows.
- Slide 4 (0:25): the QR. The live minute starts here.
- Slide 5: backup. Use it in Q&A if asked about evidence. Say "synthetic" in the same breath.
- Slide 6: bring in only if asked about bias. Backup slide.
- Slide 7: backup for Q and A.
- Slide 8 (2:55): the close. Mentor quote first, then the tagline.

Two appendix slides, in `slides/hardening.html` (six mechanisms with guarantee and limit; what we did not do and why), are for Q&A and for the written submission. They are outside the 8-slide deck. The 3-minute pitch uses slides 1, 4 and 8 on screen, and the live product in between. Slides 2, 3, 5, 6 and 7 are for the written submission, Q and A and the committee, and for a longer slot if the schedule changes.

## Submission description (one paragraph, for the repo form)

Sealed Signals is the Risk Radar platform ACAPS does not have: the live Risk List from the ACAPS API, with an expert loop, descriptive integrity notes and a public audit trail on top. An ACAPS analyst (or, in phase 2, an indicator doorbell) sends a one-minute question to the eight best-matched vetted experts. Experts answer on their phone behind a mask they choose, with ACAPS's rating hidden until after submission. Answers are committed with a timestamp, opened together, summarised as an equal-weight mean with spread and minority reasons, annotated with integrity notes the analyst reads, turned into a cited draft the analyst accepts, edits or rejects, and published as a group view on a ledger with an honesty box that states what fed into it, its limits and its misses. When the risk resolves, forecasts are scored committee-side and every panel member gets the group outcome report. Nothing publishes itself. The demo uses synthetic experts and the real ACAPS Risk Radar export. It is ready for a supervised pilot of this workflow.

## Lines to avoid

- "Revolutionary", "AI-powered", "game-changing". Say what it does.
- "Accurate experts". We have no real expert data.
- "Sealed", "nobody can read it", "nothing leaves the device". v3 states who can learn what.
- "Proof" for the synthetic test. Say "sensitivity test".
- "Earlier than ACAPS". The export has no structured rating history.
- "Pilot-ready Monday". Say "ready for a supervised pilot of this workflow".
- Crypto names (OpenTimestamps, ML-KEM, ML-DSA, hardware notary) in the three minutes. The hardening stack is built (v3.2) and lives on the appendix slides and the trust page.
- "Unhackable", "anonymous from everyone", "quantum-proof", "anchored" when the receipt is pending, "signed by ACAPS" when the key is a demo key.
- "Saves lives". We claim a better probability. See `impact.md` part 3.
- Any claim that a feature runs when its flag is off.
