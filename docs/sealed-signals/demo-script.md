# Demo script: 3 minutes

Lane C. Revised for master prompt v3 (7 Nov). Total 180 seconds, about 390 spoken words. Practice Sat 16:00. Two rehearsals with the QR step before Sun 10:30.

What changed from the first version: the analyst sends the pulse (no doorbell in the headline); "submit" and "committed" replace "seal"; no claim that answers cannot be read; the headline number is the equal-weight mean with spread and a minority reason; integrity notes are descriptions; the proof chart is out of the 3 minutes; the close is the decision-oriented ledger and the outcome report; the countdown belongs to the jury exercise only.

## Roles

Names to be filled in.

- **Presenter (P):** speaks, stands at the screen, holds no device.
- **Driver (D):** at the laptop on `/desk`. Clicks Send pulse, Reveal, Accept, Verify. Says nothing except the cue words.
- **Phone (F):** holds the phone with the magic-link email. Calls "five" aloud when the desk tray shows five committed answers.

## Before the start (not in the 3 minutes)

1. `make seed`, then `make demo` once, offline. R1043 shows on `/desk`; panel match returns 8.
2. Question contract for R1043 is frozen (see `question-contract.md` and the review notes there).
3. Tabs open: `/desk`, `/ledger`. Backup screenshots in `slides/backup/`.
4. Phone: email with the magic link loaded; card tested at 375 px.
5. QR on slide 4 points to the live card URL. Test on two phones over venue Wi-Fi.
6. Desk footer reads the flags (proposal P6). Know them. Say only what is on.
7. Demo mode tops up to 8 with labelled synthetic answers if fewer than 5 are live (proposal P7). Confirm.
8. Fill the placeholders marked [read from screen] after a seeded run.

## The script

| Time | On screen | Speaker | Words |
|---|---|---|---|
| 0:00 to 0:15 | Slide 1: "47 %" | P | "ACAPS rates a risk Medium. Of the 58 Medium risks that have resolved, 27 happened and 31 did not. That is 47 percent. A donor cannot act on a coin flip. And the experts who could sharpen it are reached by chat, once, with no record." |
| 0:15 to 0:25 | `/desk` on R1043; D clicks Send pulse; phone shows the email | D clicks. P speaks. F holds up the phone. | "The analyst picks a risk: eastern Chad, R1043. One click sends a one-minute question to the eight best-matched experts. On a phone it looks like this." |
| 0:25 to 1:20 | Slide 4 with QR, then the desk tray | P | "Scan this. You are now the Chad panel. One minute, no login. ACAPS's rating is hidden until you submit, so your first number is yours. Choose how much ACAPS knows about you: your name, a nickname, or nothing. Submit." (about 20 s) Then, while answers land in the tray: "Each answer is committed with a timestamp. Nobody can change it afterwards, and nobody on the panel sees anyone else's. Our admins can see answers with the mask you chose. We say that plainly." F calls "five". |
| 1:20 to 1:40 | `/desk`: Reveal. Distribution, ACAPS line, spread, minority reason highlighted | D clicks Reveal. P speaks. | "Now we open them together. The panel mean is [read from screen], from [min] to [max]. ACAPS says High. One expert disagrees, and gives a reason. We show that reason next to the number instead of averaging it away." |
| 1:40 to 2:05 | Desk: integrity notes, cited draft with a queued claim, Accept | P; D clicks Accept on the word "accept". | "The analyst also sees notes about this round. They describe, they do not judge. For example: no displacement expert on this panel. Then a draft where every sentence names its source. One claim could not be checked, so it waits in a queue. Absence from our databases does not mean it is false. The analyst decides. Accept." |
| 2:05 to 2:35 | `/ledger`: entry, honesty box (decision use, misses), Verify turns green | P; D clicks Verify. | "This is the public page. The group view next to the ACAPS rating. How many people, how much they agreed, what we could not check. What decision this could inform, for whom, by when. And if the analyst overrules the panel, that is written here with the reason. Verify checks the round was not changed after the fact." |
| 2:35 to 2:50 | Outcome report screen or `/desk` scoring view | P | "Six months later the risk resolves. Every forecast is scored against the question we froze at the start. The scores stay with the committee. Everyone who answered gets the outcome. Nobody gets a streak or a time-in-app count." |
| 2:50 to 3:00 | Slide 8 | P | "ACAPS told us they should have a platform, and that the point is honesty about being wrong. This is ready for a supervised pilot of that workflow. The machine rings the doorbell, the panel answers, the analyst decides, the ledger remembers." |

Time check: the live step is 55 seconds. At 1:20 D clicks Reveal whatever the count. If fewer than 5 live answers are committed, demo mode adds synthetic answers and P says: "We are topping up with synthetic panelists so you see how it looks at eight." Do not skip this sentence.

If time runs short, cut the 2:35 beat first. Keep the ledger beat.

[read from screen] values: the mean, min and max in the reveal line. Never say a number the screen does not show.

## Cues that must not drift

- P says "accept" immediately before D clicks Accept.
- F says "five" aloud. P never claims a count the screen does not show.
- P says "synthetic" every time synthetic answers or a synthetic panel are on screen. The footer says it too.
- P never says "sealed from everyone", "nobody can read it", "nothing leaves your device", "proof", or "earlier than ACAPS".

## Fallback: pre-loaded synthetic answers

Trigger any one of these:
- Wi-Fi fails or the QR page does not load by 0:40.
- Fewer than 3 phones have submitted by 1:10.
- The live API is down.

Switch (D, one command or button): load the stored run from `make demo`, which replays R1043 with 8 synthetic answers.

What P says at the switch (read it): "The network has let us down, so I will use the recorded run with eight synthetic experts. Same code, same screens, pre-loaded answers." Then continue from 1:20.

Rules:
- Never claim answers are live.
- Footer and ledger entry read "synthetic".
- If the desk is down: screenshots in `slides/backup/`, 15 seconds longer. Drop the 2:35 beat.

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
