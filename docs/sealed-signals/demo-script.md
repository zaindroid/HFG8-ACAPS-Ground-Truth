# Demo script: 3 minutes

Lane C. Revised for master prompt v3.2 (7 Nov). Total 180 seconds, about 390 spoken words. Practice Sat 16:00. Two rehearsals with the QR step before Sun 10:30.

What changed from the first version: the opening is the Risk Alert Engine replay of April 2026, with the analyst approving the pulse; "submit" and "committed" replace "seal"; no claim that answers cannot be read; the headline number is the equal-weight mean with spread and a minority reason; integrity notes are descriptions; the proof chart is out of the 3 minutes; the close is the decision-oriented ledger and the outcome report; the countdown belongs to the jury exercise only.

## Roles

Team: Zain Ul Haq (backend), (frontend: name to add), Sho Izuno (research and pitch). Role assignments not yet decided: names for Presenter (P), Driver (D) and Phone (F) to be filled in.

- **Presenter (P):** speaks, stands at the screen, holds no device.
- **Driver (D):** at the laptop on `/desk`. Clicks Send pulse, Reveal, Accept, Verify. Says nothing except the cue words.
- **Phone (F):** holds the phone with the magic-link email. Calls "five" aloud when the desk tray shows five committed answers.

## Before the start (not in the 3 minutes)

1. `make seed`, then `make demo` once, offline. R1043 shows on `/desk`; panel match returns 8.
2. Question contract for R1043 is frozen (see `question-contract.md` and the review notes there).
3. Tabs open: `/desk`, `/ledger`. Backup screenshots in `slides/backup/`.
4. Phone: email with the magic link loaded; card tested at 375 px.
5. QR on slide 4 points to the live card URL. Test on two phones over venue Wi-Fi.
6. Desk footer reads the flags (proposal P6): `FF_PQ`, `FF_BLIND`, `FF_ZK`, `FF_ANCHOR`, `FF_AGENTS`. Know them. Say only what is on. Offline, the anchor is pending, the signing key is a demo key and ZK is off. Do not say "anchored", "signed by ACAPS" or "zero-knowledge" in that case.
7. Demo mode tops up to 8 with labelled synthetic answers if fewer than 5 are live (proposal P7). Confirm.
8. Fill the placeholders marked [read from screen] after a seeded run.
9. Alerts: use **Replay April 2026**, not "Run engine" on the current month. In our reading of the rules, the October to November 2026 editions produce no alert (0 of 122 crises), so a live run would show an empty list. If asked, say so: "In a quiet month the engine says nothing. That is the point." Check that Lane A's rules give the same.
10. Say "largest rise", not "largest move": by absolute change PAK007 (a fall of 0.9) is larger than TCD005 (a rise of 0.8). Say "the displacement crisis", not "R1043": the alert is on TCD005 and the analyst has confirmed the link.

## The script

| Time | On screen | Speaker | Words |
|---|---|---|---|
| 0:00 to 0:15 | Slide 1: "47 %" | P | "ACAPS rates a risk Medium. Of the 58 Medium risks that have resolved, 27 happened and 31 did not. That is 47 percent. A donor cannot act on a coin flip. And the experts who could sharpen it are reached by chat, once, with no record." |
| 0:15 to 0:35 | `/desk` Alerts page. D clicks Replay April 2026. TCD005 appears first, with the rule that fired and the edition reliability. D clicks Approve pulse. The phone shows the email. | D clicks. P speaks. F holds up the phone. | "ACAPS publishes a severity index for every crisis each month. The engine compares two months. In April, the index for the Sudan-to-Chad displacement crisis rose from 6.1 to 6.9, the largest rise of 123 crises. It is arithmetic on ACAPS's own data, no model. The analyst approves a question to the eight best-matched experts for R1043, eastern Chad." F shows the phone.
| 0:35 to 1:25 | Slide 4 with QR, then the desk tray | P | "Scan this. You are now the Chad panel. One minute, no login. ACAPS's rating is hidden until you submit, so your first number is yours. Choose how much ACAPS knows about you: your name, a nickname, or nothing. Submit." (about 20 s) Then, while answers land in the tray: "Each answer is committed with a timestamp. Nobody can change it afterwards, and nobody on the panel sees anyone else's. Our admins can see answers with the mask you chose. We say that plainly." F calls "five". |
| 1:25 to 1:45 | `/desk`: Reveal. Distribution, ACAPS line, spread, minority reason highlighted | D clicks Reveal. P speaks. | "Now we open them together. The panel mean is [read from screen], from [min] to [max]. ACAPS says High. One expert disagrees, and gives a reason. We show that reason next to the number instead of averaging it away." |
| 1:45 to 2:10 | Desk: integrity notes, cited draft with a queued claim, Accept | P; D clicks Accept on the word "accept". | "The analyst also sees notes about this round. They describe, they do not judge. For example: no displacement expert on this panel. Then a draft where every sentence names its source. One claim could not be checked, so it waits in a queue. Absence from our databases does not mean it is false. The analyst decides. Accept." |
| 2:10 to 2:40 | `/ledger`: entry, honesty box (decision use, misses), Verify turns green | P; D clicks Verify. | "This is the public page. The group view next to the ACAPS rating. How many people, how much they agreed, what we could not check. What decision this could inform, for whom, by when. And if the analyst overrules the panel, that is written here with the reason. Verify checks the round was not changed after the fact." [Only if the flags are on, add: "The outcome carries the committee's signature, and the daily timestamp shows anchored or pending. Pending is normal for hours."] |
| 2:40 to 2:50 | Outcome report screen or `/desk` scoring view | P | "Six months later the risk resolves. Every forecast is scored against the question we froze at the start. The scores stay with the committee. Everyone who answered gets the outcome. Nobody gets a streak or a time-in-app count." |
| 2:50 to 3:00 | Slide 8 | P | "ACAPS told us they should have a platform, and that the point is honesty about being wrong. This is ready for a supervised pilot of that workflow. The machine rings the doorbell, the panel answers, the analyst decides, the ledger remembers." |

Time check: the live step is 55 seconds. At 1:25 D clicks Reveal whatever the count. If fewer than 5 live answers are committed, demo mode adds synthetic answers and P says: "We are topping up with synthetic panelists so you see how it looks at eight." Do not skip this sentence.

If time runs short, cut the 2:40 beat first. Keep the ledger beat.

[read from screen] values: the mean, min and max in the reveal line. Never say a number the screen does not show.

## Cues that must not drift

- P says "accept" immediately before D clicks Accept.
- F says "five" aloud. P never claims a count the screen does not show.
- P says "synthetic" every time synthetic answers or a synthetic panel are on screen. The footer says it too.
- P never says "sealed from everyone", "nobody can read it", "nothing leaves your device", "proof", or "earlier than ACAPS".

## Fallback: pre-loaded synthetic answers

Trigger any one of these:
- Wi-Fi fails or the QR page does not load by 0:50.
- Fewer than 3 phones have submitted by 1:15.
- The live API is down.

Switch (D, one command or button): load the stored run from `make demo`, which replays R1043 with 8 synthetic answers.

What P says at the switch (read it): "The network has let us down, so I will use the recorded run with eight synthetic experts. Same code, same screens, pre-loaded answers." Then continue from 1:25.

Rules:
- Never claim answers are live.
- Footer and ledger entry read "synthetic".
- If the desk is down: screenshots in `slides/backup/`, 15 seconds longer. Drop the 2:40 beat.

## Q and A: likely questions

| Question | Answer |
|---|---|
| Who can read the answers? | ACAPS admins can see answers with the mask the expert chose; `anonymous` answers carry no identity. The identity registry is restricted and logged. Peers see nothing until the round closes. The commitment proves timing and consistency, not secrecy from the operator. The table is in the repo. |
| How do you stop a packed panel? | Panels are matched by tag, capped at 3 of 8 per affiliation type, and a coverage gap appears in public. The committee approves each expert with two admins. The analyst decides; nothing publishes itself. We cannot prove independence. |
| Does this change an ACAPS rating by itself? | No. Only the analyst's accept, edit or reject. [mentor] |
| Is it accurate? | We have no real expert data. We tested the pipeline on all 104 resolved risks with synthetic panels, with several scenarios including shared bias and pure noise. That tests the software. |
| Is 5 answers anonymous? | No. Five is a disclosure rule. On a small panel a distinctive reason can be recognised by peers, and the card says so. |
| Why would experts stay? | They hear the outcome and see their view was used. We will measure it in the pilot. No streaks. |
| What if the model is wrong? | By default there is no model: the draft is a fixed template. The agent loop is off unless stable. Every sentence is traceable. |
| What about impact? | We claim a better-stated probability. The chain to funding and mortality is in our impact note with its weak links. |
| Who decides "materialised"? | The frozen question contract. For R1043 the ACAPS Risk Radar manager sets the status. That is ACAPS judging its own rating; we disclose it. |
| Why should we trust the alert? | It is arithmetic on ACAPS's own published monthly editions: the change in each crisis's severity index and access score, ranked across all crises, with the rule shown and editable. No model. It proposes; the analyst approves or dismisses with a note. |
| Is the alert about R1043? | It is about the Sudan-to-Chad displacement crisis (TCD005), which the analyst linked to R1043. R1043 is about cross-border insecurity. The pulse says what the alert measures. |
| Would this have warned ACAPS earlier? | We do not claim that. The April 2026 edition would have produced the proposal about five weeks before R1043 was entered on 2 June. Analysts may well have known, and there is no structured rating history to compare. It shows what the engine would have proposed. |
| Can ACAPS tell who sent an anonymous answer? | An anonymous answer carries a one-time credential that ACAPS cannot link to the approval. That does not cover timing, network details or distinctive wording on a small panel, and the card says so. [Say this only if the answer is submitted apart from the personal link; see P21.] |
| Is this quantum-safe? | The identity map is encrypted with a post-quantum scheme (ML-KEM-768 hybrid) against copy-now, decrypt-later. It does not protect against an administrator who holds the key, and every read is logged. We use reference libraries and demo keys in the hackathon build. |
| Do you use a blockchain? | No chain logic and no tokens. We publish a daily hash of the commitments to a public timestamp service (OpenTimestamps), which proves they existed by then. Nothing else. |
| Do you profile experts? | Committee-side pattern reports are descriptive sentences, opt-in for the expert, never a score, never public, never used to approve or remove anyone in the pilot. They need a consent text. |
