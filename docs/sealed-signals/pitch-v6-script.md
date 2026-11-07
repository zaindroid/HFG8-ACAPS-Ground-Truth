# Pitch script for deck v6 (3 minutes)

Lane C. Written 2026-11-07 against the `demo` branch deck (`pitch/sealed-signals-slides.html`, v6) and master prompt v3.4. This replaces the timing in `pitch.md` and `demo-script.md` (v3.2), which still describe an 8-slide deck and a live demo inside the 3 minutes.

Assumption: the live demo happens after the pitch, so these 3 minutes are slides only. If the demo stays inside the 3 minutes, use the cut list at the bottom.

## Slide order and timing

354 spoken words, about 175 seconds at a calm pace. Slide 9 (comparison table) is not shown in the pitch; it stays as a backup for Q and A. Slide numbers are the deck's ids (s0 to s11).

| Time | Slide | Words | Speaker |
|---|---|---|---|
| 0:00 to 0:05 | s0 Title | 10 | We are Zain, Saleeta and Sho. This is Sealed Signals. |
| 0:05 to 0:20 | s1 47 % | 43 | ACAPS rates a risk Medium. Of the 58 Medium risks that have resolved, 27 happened. That is 47 percent. A donor cannot act on a coin flip, and the experts who could sharpen it are reached by email and chat, with no record. |
| 0:20 to 0:45 | s2 System | 50 | Here is the whole system. An alert engine reads ACAPS's own monthly data. An analyst approves one question. It reaches the expert where they already are. They answer in a minute, we open all answers together, check every number, and a person decides. Teal is arithmetic. Amber is a person. |
| 0:45 to 1:05 | s3 Alert engine | 41 | The alert is arithmetic, no model. In April 2026 the severity index for displacement from Sudan to Chad rose from 6.1 to 6.9, the largest rise of 123 crises. The engine links it to an active risk and proposes the question. |
| 1:05 to 1:20 | s4 Reach | 24 | Experts never sign up. One magic link goes out by email, WhatsApp, Signal, SMS or Teams, and every reply lands in the same record. |
| 1:20 to 1:45 | s5 Psychology | 46 | The card is designed against bias. ACAPS's rating is hidden until you answer, so no anchoring. Words with printed ranges, so no false precision. We ask for the strongest reason it would not happen. You choose your own mask. And nobody sees anybody until the deadline. |
| 1:45 to 2:00 | s6 Verification | 29 | Every claim in the draft is checked against a versioned record by a Skeptic and a Judge. Anything unchecked waits in a queue. The analyst accepts, edits or rejects. |
| 2:00 to 2:20 | s7 Trust | 34 | The public ledger shows the group view, the limits and the misses, with a Verify button anyone can click. We say what we do not claim: it proves timing, not secrecy from the operator. |
| 2:20 to 2:35 | s8 Runs | 42 | It runs. The engine reproduced the April move from cached data, and the full loop finishes in under a minute from a clean clone. The sensitivity test on 104 resolved risks uses synthetic panels, so it tests the software, not the experts. |
| 2:35 to 2:52 | s10 Pilot | 25 | We are ready for a supervised pilot of this workflow: one crisis, eight experts, three months, with the ACAPS Risk Radar manager as the analyst. |
| 2:52 to 3:00 | s11 Close | 10 | Easier to contribute to. Easier to scrutinise. Easier to trace. |

Facts used, all from the deck and the ACAPS export: 27 of 58 resolved Medium risks (46.6 percent, rounds to 47); TCD005 index 6.1 to 6.9, March to April 2026, rank 1 of 123 by rise; 104 resolved risks in the sensitivity test.

## Checks the deck still needs (against the repo's own "Lines to avoid")

1. **s8 title "Proof it runs, not promises."** Rule: no "proof" for the synthetic test. Suggest "It runs." The script above does not say it.
2. **s9 row "quantum-safe at rest".** Rule: no "quantum-proof". Suggest "encrypted at rest, post-quantum key establishment" and keep it on the backup slides.
3. **s2 and s7 show crypto names** (SHA-256, ML-DSA-65, OpenTimestamps, ML-KEM-768) on main slides. Rule: none in the 3 minutes. Nobody reads them aloud in this script, but a judge can read them. Move to the Q and A slides or shrink to one line.
4. **s7 chip "anchored OpenTimestamps".** Say "anchored" only when the receipt is no longer pending. Otherwise "timestamp pending".
5. **s3 headline "found the real April 2026 move".** Safe if read as "would have proposed". Do not add "earlier than ACAPS".
6. **s8 "Five independent model reviews".** Judges may read this as a claim of validation. Suggest "five model-assisted design reviews" or drop it.
7. **s5 citation mapping.** "Saw, read or heard" tagging is credited to the Pennycook and Rand accuracy prompt. That paper is about prompting people to think about accuracy, not about tagging the source type. Suggest "inspired by", or credit source monitoring instead. See `citations.md`.
8. **Pilot length.** The deck says 3 months; `pitch.md` (v3.2) says 2 months. Use the deck's 3 months and update `pitch.md`.
9. **Channels.** s4 lists six channels including voice. Say aloud only the channels that run in the build, and check the flags before the pitch.
10. **Name.** "Sealed Signals" stays as the name. Never explain it as "sealed means secret".

## Cut list if the demo stays inside the 3 minutes

Cut first: s6 (verification), then s8 (runs), then s4 (reach). Keep s1, s2, s3, s5, s10, s11. That frees about 55 seconds.

## Cues that must not drift

- Say "largest rise", not "largest move" (by absolute change a fall in PAK007 is larger).
- Say "synthetic" every time the sensitivity test or synthetic experts are mentioned.
- Never say "sealed from everyone", "nobody can read it", "nothing leaves your device", "proof", "earlier than ACAPS", "accurate experts".
