# Sealed Signals — trust design

One page that says exactly what each mechanism guarantees, and what it does not. For the team, the README, the pitch Q&A,
and external reviewers. Wording here is the wording we use everywhere.

## 1. The ledger

A public record, one entry per panel question on a risk.

| Field | Meaning |
| --- | --- |
| Committed at | When the answers were locked, before anyone saw them |
| Group view | Equal-weight mean and spread of the panel's probabilities; disagreement as an unattributed one-line summary; missing-evidence themes |
| ACAPS band | ACAPS's own probability band at the time (Very Low … Very High) |
| Decision | What the analyst did with the draft: accept, edit, reject, and the "what decision, for whom, by when" line |
| Outcome | Materialised / not materialised, set by ACAPS when the question resolves |
| Verify | Recomputes the round's commitment hash; reports "matches" or "does not match" and states that this proves timing and consistency only |
| Honesty box | n experts; agreement; spread; expertise the panel lacked; claims corroborated / queued; share of relayed answers; this panel's hit rate and number of misses; a one-line caveat; the standing line "in a panel of eight a distinctive reason may identify its author to colleagues; experts were told this before answering"; "panel view rejected: analyst rationale" when that happened |

Never on the ledger: a name, a pseudonym, an individual answer, an individual score, or any integrity note about a person.

Why it builds trust: a donor, auditor or journalist sees what fed into a rating, including the times ACAPS or the panel
got it wrong. Misses are visible by design. The mentor's words: "we will get things wrong; the point is honesty about it."

## 2. Psychology: the biases we address and how

| Bias | What it does to panels | What we do | Evidence base |
| --- | --- | --- | --- |
| Anchoring effect (ACAPS brief: "focus on one piece of information") | People drift toward the first number they see | ACAPS's rating and the severity-change line are hidden until the expert has submitted; the band first appears in the feedback message | Tversky & Kahneman; Delphi independent first rounds |
| Groupthink, false consensus (ACAPS brief) | People copy the group or the loudest voice | Answers are committed and revealed together at a fixed deadline; round 2 is optional and shows only an anonymised spread; reminders never state counts | Delphi method |
| Availability cascade, recency, salience (ACAPS brief) | Things heard get reported as things seen | "Is this something you saw, read, or heard?" before the free-text line; the tag travels with the claim | Pennycook & Rand (accuracy prompts) |
| Confirmation bias (ACAPS brief; their mitigation: devil's advocacy) | People look for what confirms their view | Optional line "strongest reason this would NOT happen" | Lord, Lepper & Preston 1984 |
| Absence of evidence (ACAPS brief) / forced guessing | A slider makes people invent a number | "Outside my area" and "not enough evidence" are real answers and are never scored; missing-evidence column on the desk | Standard elicitation practice |
| Loud majority | The informed minority is averaged away | The dissenter's reason is shown beside the mean; "what share of the panel will say above 0.5?" runs as a labelled experiment to spot informed minorities | Prelec, Seung & McCoy 2017; Palley & Soll (peer prediction) |
| Overconfidence (ACAPS brief) | Experts stay miscalibrated without feedback | Every forecast is scored against the real outcome; everyone who answered gets the group outcome report; private calibration report opt-in after 5 resolutions; a separate consent-gated calibration programme with numeric confidence, expert sees it first, off at any time | Tetlock / Good Judgment Project |
| Institutional bias (ACAPS brief) / packed panels | One organisation or viewpoint dominates | Committee vetting (two approvals), expertise tags, composition cap (≤ 3 of 8 from one affiliation type), affiliation-level sentences at n ≥ 3, coverage-gap note when a trigger theme has no expert | Mentor's own concern; ACAPS brief |

What we do not claim: hiding the rating avoids displaying the anchor; it cannot guarantee cognitively independent judgement.
Integrity notes describe patterns; they never diagnose a person. Nothing on a pulse card measures the expert without
telling them: no seed questions, no fictitious references, no timing or edit-count measures. Calibration is a separate,
consented programme, and the expert sees their report before anyone else.

Lane C verifies every citation above before it goes on a slide.

## 3. Cryptography: what is built and what it proves

| Mechanism | Built? | What it guarantees | What it does not |
| --- | --- | --- | --- |
| Commit-and-reveal: SHA-256 of the answer plus a salt, with a timestamp, stored before anyone sees the answer; all answers opened together | Yes | An answer cannot be changed after submission; the time is verifiable; peers cannot see each other inside a round; ACAPS can prove "the panel said this before it happened" | Confidentiality from the operator (application access controls do that); truth of the answer |
| Masks: known / pseudonym / anonymous; pseudonym = HMAC of an internal id; restricted identity registry with logged access; anonymous answers carry no identity link and get no personalised feedback; public wording is always "pseudonymised" | Yes | Confidentiality from peers and the public, with defined, logged ACAPS access | Anonymity from ACAPS itself; anonymisation (deleting the registry does not anonymise linked answers or prose); protection against re-identification of a dissenter by their distinctive wording in a panel of 8 (the card and the honesty box say so) |
| Aggregates only above n = 5 | Yes | A disclosure rule that keeps individual answers out of public views | An anonymity guarantee |
| Blind-signed single-use credentials (RSA blind signatures, RFC 9474; one token per answer, reuse rejected) | Yes, `FF_BLIND` | A vetted panel member answered, unlinkable by ACAPS to the approval | Timing or network-metadata correlation; re-identification by distinctive wording |
| Zero-knowledge group membership (Semaphore v4, proof generated in the browser, nullifier per pulse) | Yes, `FF_ZK` (off until stable) | "A vetted member of this panel answered" without saying which; no double answers | Reputation portability |
| Public timestamp of daily commitment roots (Sigstore Rekor transparency log) | Yes, `FF_ANCHOR`, shows pending until the log returns an inclusion proof | Independent proof the commitments existed by that time | Who answered, or whether an answer is right; only the root is logged |
| Post-quantum: ML-KEM-768 (hybrid with X25519) for key establishment, AES-256-GCM for the identity registry at rest; ML-DSA-65 signatures on outcome attestations | Yes, `FF_PQ` | Long-horizon confidentiality of the identity map; outcome records provably issued by the committee key and unaltered | Confidentiality from an administrator who holds the key; truth of the outcome |
| End-to-end answer encryption: the expert card encrypts the answer in the browser to the engine's ML-KEM-768 + X25519 key, HKDF-SHA256 to AES-256-GCM, with the token and route as associated data | Yes, `FF_E2E` | The answer is readable only by the engine; a CDN, proxy or tunnel in between cannot read it or alter it undetected | Hiding the answer from the operator of the engine; protecting a compromised device or browser; a client that cannot fetch the key sends a plain body and shows no encryption line |
| Process chain: each step of a risk's process is an event in an append-only SHA-256 hash chain per risk (genesis 64 zeros, hash over canonical JSON of every field but the hash); each day's chain heads are extra leaves in that day's anchored root | Yes, `FF_CHAIN` | Any later change to a recorded step, or removal of one, breaks the chain and is detectable by anyone holding a published head | That the source data was right, only which edition and rule were used; it holds no names, contact details, pseudonyms, expert ids or free text |

We do not run a blockchain. We use two ideas from that world and say precisely what each proves: the sealed envelope
you can check later (commitments), and a public timestamp (each daily root entered into Sigstore Rekor, an append-only transparency log anyone can check).

Pattern reports are about panels, not people: convergence after reveal, spread over time, abstention share, source mix,
coverage gaps, and affiliation-level sentences at n ≥ 3. The committee never receives a sentence about an individual.
Individual calibration exists only inside the consent-gated programme, expert first, opt-in, off at any time.

## 4. Who can learn what

| Party | Before reveal | After reveal | Ever |
| --- | --- | --- | --- |
| The expert | their own answer | their answer, the group view, ACAPS's band, the analyst's decision | their private calibration (opt-in, off at any time; not for anonymous answers) |
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
4. **Answers are committed, revealed together at a fixed deadline, summarised plainly**: mean, spread, unattributed
   disagreement, missing evidence.
5. **Integrity notes describe, never accuse**: convergence after reveal, pseudonyms moving together, claims that may share
   an origin, missing expertise. The analyst reads them; nothing is penalised automatically.
6. **The draft cites a record or an aggregate for every sentence**; a checker rejects any number not exactly in the
   evidence and keeps uncorroborated claims in a verification queue, since absence from a database is not falsity.
7. **A person decides.** Accept, edit or reject, with the decision it informs. Nothing publishes itself. ACAPS's product
   changes only when an analyst says so: one validation layer among others.
8. **The ledger records it all, including the misses**, and when the analyst overruled a panel that turned out right.
9. **Scores are for forecasts, not people.** Panel-level to the committee; no public leaderboard; never used to approve
   or remove an expert in the pilot; feedback goes to everyone who answered; nothing is measured about a person without
   their consent, and they see it first.
10. **Synthetic experts only until ACAPS runs the pilot.** No real person is represented in the hackathon build.

One sentence: the numbers raise the alert, people make the call, and the record shows the misses.
