# Demo script: three minutes

Lane C. Revised for master prompt v3.4 section 9a (8 Nov). Total 180 seconds, about 400 spoken words. The deck is `pitch/sealed-signals-slides.html`: six main slides after the title, then Q&A and fallback slides. Slide numbers below are positions in that file. The Q&A answers are in `judging-checklist.md`.

Spine line, said at the close: **easier to contribute to, easier to scrutinise, easier to trace.** Second line: the numbers raise the alert, people make the call, the record shows the misses.

## Roles

- **Presenter (P):** Sho Izuno. Speaks, stands at the screen, holds no device.
- **Driver (D):** at the laptop on the analyst desk. Clicks Replay April 2026, Approve pulse, Accept, Verify. Says nothing except the cue words.
- **Phone (F):** holds the phone showing the magic link. Tells P when the jury answers have arrived.

Zain Ul Haq and Saleeta Qadir take D and F in whichever order they rehearse. The assignment is fixed at the first rehearsal and written on the stage plan.

## Before the start (not in the three minutes)

1. `make demo` once, offline, from the repository root. Then `make dev`. The desk shows R1043, the seeded panel of eight, and four open guest links for the jury step.
2. The pulse window must close during the live step. The deadline watcher checks every 15 seconds (`deadline_watch` in `engine/engine/api.py`) and reveals at the deadline. Rehearse once to confirm how the desk sets a short window. The reveal is never forced by a count: with fewer than five answers at the deadline the round is "insufficient" and nothing is revealed. The seeded panel gives eight, so jury answers are additional.
3. QR on the "demo" step opens a guest link. Test on two phones over venue Wi-Fi.
4. Footer on the desk shows which paths ran. Say only what is on. Offline, the anchor shows pending, the keys are demo keys, and the zero-knowledge flag is off.
5. Open the fallback slides (19 and 20) in a second tab.

## The script

| Time | On screen | Speaker | Words |
|---|---|---|---|
| 0:00 to 0:20 | Deck slide 2, the problem | P | "ACAPS rates a risk Medium. Of the 58 Medium risks that have resolved, 27 happened. That is 47 percent, a coin flip, and it is where preparedness money starts. Between scheduled reviews, analysts check with experts by email and conversation. Those checks are not structured, not time-stamped, not auditable. And experts will not sign up to another portal." |
| 0:20 to 0:45 | Deck slide 3, the solution and the three must-haves | P | "Our answer is a one-minute expert loop on ACAPS's own data. Your three must-haves. Easy to use: one screen, one tap, no account. Expert-controlled anonymity: each expert picks a mask per answer, named to ACAPS, a nickname to peers, or no identity kept. Public anonymity: the public page shows aggregates of five or more, never an individual." |
| 0:45 to 1:00 | Desk, Alerts page. D clicks Replay April 2026, then Approve pulse on rank 1. | D clicks. P speaks. | "The engine compares ACAPS's own monthly editions. In April 2026 the severity index for displacement from Sudan to Chad rose from 6.1 to 6.9, the largest deterioration of 123 crises. No model. The analyst links it to R1043 and approves a question." |
| 1:00 to 1:25 | QR on screen. F shows the card on the phone. The jury scans. | P | "Scan this. You are the Chad panel. The question comes first: will more than 50,000 new arrivals be registered by 31 March. Pick a word, pick a mask, confirm. ACAPS's rating is hidden until you submit. Nothing is recorded until you confirm." |
| 1:25 to 1:40 | Desk: reveal at the deadline. Four columns: agreement, disagreement, missing evidence, analyst rationale. | P; D watches the reveal | "Answers open together at the deadline, not when five are in. The mean, the spread, and disagreement without names. Two experts expect displacement rather than attacks, and that stays beside the number." |
| 1:40 to 1:55 | Desk: cited draft with Skeptic marks; decision box. D clicks Accept after the three fields are filled. | P; D clicks on the word "accept". | "Every sentence in the draft cites a record, and a checker rejects any number that is not exactly in it. One claim waits in a queue, because absence from our databases is not falsity. The analyst writes what decision this informs, for whom, by when. Accept." |
| 1:55 to 2:00 | Public ledger entry; D clicks Verify. | D clicks. P speaks. | "The public record. Verify recomputes the round. It proves the timing, not the truth." |
| 2:00 to 2:20 | Deck slide 4, how it is built | P | "Six modules. Consent first: experts never sign up and can stop with one word. Nothing is measured about an expert without consent. The identity list is encrypted and every access is logged. Pseudonymised, not anonymous from ACAPS, and we say so." |
| 2:20 to 2:40 | Deck slide 5, the card against six biases | P | "The card is built against six biases that ACAPS's own brief names: no anchor, no forced guess, argue the opposite, saw read or heard, a mask per answer, an explicit submit." |
| 2:40 to 2:50 | Deck slide 6, why people can trust it | P | "Experts are never judged as people. Analysts see agreement, disagreement and what is missing, then decide on record. Readers see what fed into a rating and when it was wrong." |
| 2:50 to 3:00 | Deck slide 7, it runs; then slide 8, the close | P | "It runs from a clean clone, offline, in under a minute, and it is ready for a supervised pilot of this workflow. Easier to contribute to. Easier to scrutinise. Easier to trace." |

If time runs short, cut the 2:20 and 2:40 beats first. Keep the live demo and the close.

## Cues that must not drift

- P says "accept" immediately before D clicks Accept.
- P never claims a count or a number the screen does not show.
- P says "synthetic" whenever the seeded panel is on screen. The desk footer says it too.
- P never says "anonymous" about ACAPS's own access, "sealed from everyone", "nobody can read it", "quantum-proof", "unhackable", "anchored" while the receipt is pending, "signed by ACAPS" while the key is a demo key, or "proof" for the sensitivity test.
- P never says "earlier than ACAPS". The replay shows what the engine would have proposed.
- Crypto names stay out of the three minutes. The one exception is the Verify click.

## Fallback

Trigger any one of these:
- Wi-Fi fails or the QR page does not load by 1:10.
- The live API is down.
- The reveal has not come by 1:40.

Switch (D): open fallback slide 19 (revealed together at the deadline, disagreement unattributed) and slide 20 (cited draft, the decision, the public record). Same beats, same words from 1:25.

What P says at the switch (read it): "The network has let us down, so these are the recorded screens from the same run with the synthetic panel. Same code, same screens." Never claim the answers are live.

## Q and A

The eight likely questions and their answers are in `judging-checklist.md`. Backup slides: 16 (personas and where our modules sit in ACAPS's workflow), 17 (the cryptographic ledger: six mechanisms, each with what it proves and what it does not), 18 (scoring and calibration: forecasts, not people), 21 (sensitivity test).

Extra answers:

| Question | Answer |
|---|---|
| Is the alert about R1043? | It is about the Sudan-to-Chad displacement crisis, TCD005, which the analyst linked to R1043. R1043 is about cross-border insecurity. The pulse says what the alert measures. |
| Why trust the alert? | It is arithmetic on ACAPS's own monthly editions, ranked across all crises, with the rule shown. In a quiet month it says nothing: October to November 2026 produces no event. |
| Would this have warned ACAPS earlier? | We do not claim that. The April 2026 edition would have produced the proposal about five weeks before R1043 was entered on 2 June. Analysts may well have known, and the export has no structured rating history. |
| Is five answers anonymous? | No. Five is a disclosure rule for the public page. In a panel of eight a distinctive reason may identify its author to colleagues, and experts are told so before answering. |
| Do you profile experts? | No. The committee reads sentences about panels, never a person. Individual calibration is a separate programme, off by default, opt-in, and the expert sees it first. |
| Who decides "materialised"? | The frozen question contract. For R1043 the ACAPS Risk Radar manager sets the status, which means ACAPS judges its own rating. We disclose that. |
