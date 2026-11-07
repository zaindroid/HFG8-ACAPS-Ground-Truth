# Q and A preparation (deck v6)

Lane C, 2026-11-07. Short answers for the questions the v6 deck is most likely to draw. Each answer states the limit. Where an answer depends on a feature flag, check the flag first. This adds to the table at the end of `demo-script.md` (v3.2).

## Challenge and fit

| Question | Answer |
|---|---|
| How does this answer ACAPS's question? | "Without costing experts their time or anonymity": one question, one tap, one minute, no sign-up, mask chosen per answer. Experts are reached in the channel they already use. |
| Why not a survey tool? | Surveys need an account or a link to a form, show no commit-and-reveal, and give the analyst no record of what was checked. Slide 9 has the table. |
| Why not a prediction market? | Prices are public, so people anchor on them. Markets need money and accounts, and the price is the output. We want independent first answers, then disagreement the analyst can read. |
| Does it work for forecasting as well as ground truthing? | The same loop: the question contract freezes event, place, threshold and deadline, then forecasts are scored at panel level when the risk resolves. |

## Experts and psychology

| Question | Answer |
|---|---|
| What stops experts from copying each other? | Answers are committed before anyone sees any, and opened together at the deadline. Reminders never state counts. Round 2 is optional and shows only an anonymised spread; the shift is measured. |
| Is it really anonymous? | No. The expert picks a mask per answer: named to ACAPS, nickname to peers, or no identity kept. Masks protect from peers and the public, not from ACAPS. We say pseudonymised. |
| Will experts really answer in a minute? | We measured card time on two phones over venue Wi-Fi (in the README). We do not claim real-expert response rates before the pilot. Retention in week 8 is a pilot measure. |
| Why six channels? | Experts in the field use what they already have. Every channel resolves to the same record and mask. Channel preference is a hypothesis until the pilot. |
| Is the bias design evidence-based? | Each item maps to a known effect: anchoring (Tversky and Kahneman), false precision and forced guessing, consider-the-opposite (Lord, Lepper and Preston). The accuracy-prompt link is looser: that work tested news sharing, not expert forecasts, so we say inspired by. We have not tested any of this on real experts. |
| Does the surprisingly-popular method work with 8 experts? | Not shown. The 2017 Nature paper used large samples, and its authors say the claims are theoretical and not guaranteed in practice. It is a labelled experiment on the desk; the equal-weight mean is the primary number. |
| Do you score or profile experts? | Never as a person. Calibration only with consent, the expert sees it first, and it is off at any time. Pattern reports describe panels. No leaderboard. |

## Analysts and verification

| Question | Answer |
|---|---|
| Can the machine change a rating? | No. Only the analyst's accept, edit or reject changes anything. Nothing publishes itself. |
| What if the model is wrong? | Default path is a deterministic template; the model loop is off unless stable. The Skeptic checks every number against a versioned record; a number off by any amount blocks the draft. |
| What is "absence is not falsity"? | A claim we cannot corroborate waits in a verification queue with its source tag. It is never silently dropped or silently published. |
| Is the alert engine really not a model? | It diffs ACAPS's monthly severity and access editions and ranks the changes by rule. In October to November 2026 the rules produce no alert; the engine says nothing in a quiet month. |

## Trust, security and claims

| Question | Answer |
|---|---|
| Who can read the answers? | ACAPS admins see answers with the mask the expert chose. The identity map is encrypted and every read is logged. The commitment proves timing, not secrecy from the operator. |
| Is this blockchain or quantum-safe? | No chain and no tokens. A daily hash goes to a public timestamp service (OpenTimestamps) and proves existence by that time. The identity map uses post-quantum key establishment against copy-now-decrypt-later. It does not protect against an admin holding the key. |
| How accurate is it? | We have no real expert data. The sensitivity test uses synthetic panels on 104 resolved risks. It tests the software, not experts. |
| Why do your numbers say 47 percent? | 27 of 58 resolved Medium risks materialised in ACAPS's Risk Radar export. High: 32 of 38 (84 percent). |
| What do you not claim? | Earlier warning than ACAPS, real expert accuracy, anonymity from ACAPS, secrecy from the operator, saved lives. We claim a better-stated probability and a traceable record. |

## Pilot and impact

| Question | Answer |
|---|---|
| What would the pilot look like? | One crisis (eastern Chad), eight experts with consent from the analyst's contacts, three months, ACAPS's Risk Radar manager as the analyst. |
| What do you measure? | Experts still answering in week 8, minutes per weekly update, panel mean against the rating on questions that resolve. |
| Cost and scale? | Hackathon build uses synthetic experts and offline cache; cost to run a pulse is the analyst's minutes. Scaling beyond one crisis is untested; say so. |
| Who owns the data? | The committee holds the key to the identity map; aggregates only at five or more answers, never an individual. Data-protection review is a pilot prerequisite, not done yet. |

## Honest gaps to say out loud if asked

- No real experts tested yet.
- Reach channels beyond email and the card may be demo-only; check the build.
- Expert card is now three steps in `lane/frontend`; the demo video shows the older screen.
- Data-protection review not done.
