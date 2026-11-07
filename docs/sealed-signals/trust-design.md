# Sealed Signals — trust design

One page that says exactly what each mechanism guarantees, and what it does not. For the team, the README, the pitch Q&A,
and external reviewers. Wording here is the wording we use everywhere.

## 1. The ledger

A public record, one entry per panel question on a risk.

| Field | Meaning |
| --- | --- |
| Committed at | When the answers were locked, before anyone saw them |
| Group view | Equal-weight mean and spread of the panel's probabilities; the minority's reason, if any |
| ACAPS band | ACAPS's own probability band at the time (Very Low … Very High) |
| Decision | What the analyst did with the draft: accept, edit, reject, and the "what decision, for whom, by when" line |
| Outcome | Materialised / not materialised, set by ACAPS when the question resolves |
| Verify | Recomputes the round's commitment hash; reports "matches" or "does not match" and states that this proves timing and consistency only |
| Honesty box | n experts; agreement; spread; expertise the panel lacked; claims corroborated / queued; this panel's hit rate and number of misses; a one-line caveat; "panel view rejected: analyst rationale" when that happened |

Never on the ledger: a name, a pseudonym, an individual answer, an individual score, or any integrity note about a person.

Why it builds trust: a donor, auditor or journalist sees what fed into a rating, including the times ACAPS or the panel
got it wrong. Misses are visible by design. The mentor's words: "we will get things wrong; the point is honesty about it."

## 2. Psychology: the biases we address and how

| Bias | What it does to panels | What we do | Evidence base |
| --- | --- | --- | --- |
| Anchoring | People drift toward the first number they see | ACAPS's rating is hidden until the expert has submitted their own | Tversky & Kahneman; Delphi independent first rounds |
| Herding / groupthink | People copy the group or the loudest voice | Answers are committed and revealed together; round 2 is optional and shows only an anonymised spread | Delphi method |
| Overclaiming | Things heard get reported as things seen | "Is this something you saw, read, or heard?" before the free-text line; the tag travels with the claim | Pennycook & Rand (accuracy prompts) |
| Forced guessing | A slider makes people invent a number | "Outside my expertise" and "not enough evidence" are real answers and are never scored | Standard elicitation practice |
| Loud majority | The informed minority is averaged away | The dissenter's reason is shown beside the mean; "what share of the panel will say above 0.5?" runs as a labelled experiment to spot informed minorities | Prelec, Seung & McCoy 2017; Palley & Soll (peer prediction) |
| Overconfidence | Experts stay miscalibrated without feedback | Every forecast is scored against the real outcome; everyone who answered gets the group outcome report; private calibration report opt-in after 5 resolutions | Tetlock / Good Judgment Project |
| Packed or skewed panels | One organisation or viewpoint dominates | Committee vetting (two approvals), expertise tags, composition cap (≤ 3 of 8 from one affiliation type), coverage-gap note when a trigger theme has no expert | Mentor's own concern |

What we do not claim: hiding the rating avoids displaying the anchor; it cannot guarantee cognitively independent judgement.
Integrity notes describe patterns; they never diagnose a person.

Lane C verifies every citation above before it goes on a slide.

## 3. Cryptography: what is built and what it proves

| Mechanism | Built? | What it guarantees | What it does not |
| --- | --- | --- | --- |
| Commit-and-reveal: SHA-256 of the answer plus a salt, with a timestamp, stored before anyone sees the answer; all answers opened together | Yes | An answer cannot be changed after submission; the time is verifiable; peers cannot see each other inside a round; ACAPS can prove "the panel said this before it happened" | Confidentiality from the operator (application access controls do that); truth of the answer |
| Masks: known / pseudonym / anonymous; pseudonym = HMAC of an internal id; restricted identity registry with logged access; anonymous answers stored without identity | Yes | Confidentiality from peers and the public, with defined, logged ACAPS access | Anonymity from ACAPS itself; protection against re-identification of a dissenter by their distinctive wording in a panel of 8 (the card says so) |
| Aggregates only above n = 5 | Yes | A disclosure rule that keeps individual answers out of public views | An anonymity guarantee |
| Blind-signed single-use credentials (RSA blind signatures, RFC 9474; one token per answer, reuse rejected) | Yes, `FF_BLIND` | A vetted panel member answered, unlinkable by ACAPS to the approval | Timing or network-metadata correlation; re-identification by distinctive wording |
| Zero-knowledge group membership (Semaphore v4, proof generated in the browser, nullifier per pulse) | Yes, `FF_ZK` (off until stable) | "A vetted member of this panel answered" without saying which; no double answers | Reputation portability |
| Timestamp anchoring of daily commitment roots (OpenTimestamps) | Yes, `FF_ANCHOR`, shows pending until confirmed | Independent proof the commitments existed by that time | Anything else; no tokens, no chain logic, no cost |
| Post-quantum: ML-KEM-768 hybrid encryption of the identity registry; ML-DSA-65 signatures on outcome attestations | Yes, `FF_PQ` | Long-horizon confidentiality of the identity map; outcome records provably issued by the committee key and unaltered | Confidentiality from an administrator who holds the key; truth of the outcome |

We do not run a blockchain. We use two ideas from that world and say precisely what each proves: the sealed envelope
you can check later (commitments), and a public timestamp (anchoring of daily roots on Bitcoin via OpenTimestamps).

Per-expert response-pattern reports (calibration, overconfidence, extremity, agreement after reveal, round-2 shift,
source mix, abstention) are descriptive sentences for the committee and, opt-in, for the expert. Never a score, never
public, never a reason to approve or remove anyone in the pilot.

## 4. Who can learn what

| Party | Before reveal | After reveal | Ever |
| --- | --- | --- | --- |
| The expert | their own answer | their answer and the group view | their private calibration (opt-in) |
| Peers | nothing | anonymised spread; pseudonymous reasons if the author chose "pseudonym" | never a name |
| ACAPS admins | that an answer exists | answers with the mask the expert chose | the identity registry, with logged access |
| The public | nothing | aggregates with n ≥ 5, honesty box, outcomes | never an individual |
| The server | stores the committed value encrypted at rest | everything admins see | the registry, under access logging |

## 5. How the whole system stays trustworthy

1. **The alert is arithmetic on ACAPS's own data.** Month-over-month change in ACAPS's severity and access indices, ranked
   across all crises, with the rule that fired shown. No model, no black box. It proposes; an analyst approves.
2. **The panel is vetted and balanced.** Committee approval with two admins; expertise tags; composition cap; a coverage
   note when the panel lacks a relevant expertise.
3. **Each expert controls their visibility**, and we state the limit of what that visibility protects.
4. **Answers are sealed, revealed together, summarised plainly**: mean, spread, dissent.
5. **Integrity notes describe, never accuse**: convergence after reveal, pseudonyms moving together, claims that may share
   an origin, missing expertise. The analyst reads them; nothing is penalised automatically.
6. **The draft cites a record or an aggregate for every sentence**; a checker rejects any number not exactly in the
   evidence and keeps uncorroborated claims in a verification queue, since absence from a database is not falsity.
7. **A person decides.** Accept, edit or reject, with the decision it informs. Nothing publishes itself. ACAPS's product
   changes only when an analyst says so: one validation layer among others.
8. **The ledger records it all, including the misses**, and when the analyst overruled a panel that turned out right.
9. **Scores are for forecasts, not people.** Committee-side only; no public leaderboard; never used to approve or remove
   an expert in the pilot; feedback goes to everyone who answered.
10. **Synthetic experts only until ACAPS runs the pilot.** No real person is represented in the hackathon build.

One sentence: the numbers raise the alert, people make the call, and the record shows the misses.
