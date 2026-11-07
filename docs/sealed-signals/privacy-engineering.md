# Privacy engineering and hardening

Repo page. Not in the 3-minute pitch beyond one sentence. Lane C, revised for master prompt v3.2 (7 Nov): every item below is now built behind a flag (master prompt 6c, 6d). This page states, for each, the guarantee, what it does not do, what the demo build actually runs, and the questions Lane A must answer before the wording goes on screen. Source records were checked through search on 6-7 Nov; read the primary source before relying on a detail.

Wording rule: on a slide, in the UI and on stage, every hardening item is described with its "guarantees / does not" sentence from `trust-design.md`, and only when its flag is on in that run.

## 1. Who can learn what

See master prompt section 1a and `trust-design.md` section 4. In one line: peers see nothing before the reveal; ACAPS admins see answers with the mask the expert chose; `anonymous` answers carry no identity; the public sees aggregates only; commitments do not hide answers from the operator.

## 2. The six mechanisms

| # | Mechanism | Flag | Guarantee | Does not | What the demo runs (to be stated by Lane A) |
|---|---|---|---|---|---|
| 1 | ML-KEM-768 hybrid encryption of the identity registry | `FF_PQ` | Long-horizon confidentiality of the identity map against copy-now, decrypt-later | Protect against an administrator who holds the key, or against access-control mistakes | Which library; where the key lives; what "hybrid" means (hybrid with what) |
| 2 | ML-DSA-65 signature on each resolved ledger entry | `FF_PQ` | The outcome record was signed by the committee key and not altered since | The truth of the outcome; anything about the key holder beyond that key | Who holds the signing key. In a hackathon build it is a demo key, not ACAPS's. Say so. |
| 3 | Blind-signed single-use credentials (RFC 9474) | `FF_BLIND` | An answer comes from a vetted panel member and ACAPS cannot link the token to the approval | Hide timing, network metadata or distinctive wording; see section 3 | Whether submission is separated from the personal magic link |
| 4 | Zero-knowledge panel membership (Semaphore v4) | `FF_ZK` (off until stable) | "A member of this panel answered", without saying which; one answer per pulse | Reputation portability | Off unless stable. Never claim it when off. |
| 5 | Daily timestamp anchoring (OpenTimestamps) | `FF_ANCHOR` | Independent proof the commitments existed by that time | Anything else | Status is "pending" until a Bitcoin confirmation arrives, which takes hours. Offline it stays pending. |
| 6 | Registry access log | on | ACAPS access to identities is defined and visible | Prevention of access by an authorised admin | Whether the log can be altered by an admin |

### Sources

- Post-quantum standards: NIST FIPS 203 (ML-KEM) and FIPS 204 (ML-DSA), both published 13 Aug 2024 ([FIPS 203](https://csrc.nist.gov/pubs/fips/203/final), [FIPS 204](https://csrc.nist.gov/pubs/fips/204/final)). NIST's pages carry planning notes about future corrections; check them before printing a version claim.
- Blind signatures: Chaum 1983 (*Blind Signatures for Untraceable Payments*, DOI 10.1007/978-1-4757-0602-4_18); implementation standard [RFC 9474, RSA Blind Signatures](https://www.rfc-editor.org/rfc/rfc9474) (IRTF, informational, Oct 2023; RSABSSA, used in Privacy Pass).
- Semaphore: [docs.semaphore.pse.dev](https://docs.semaphore.pse.dev/). Groups are Merkle trees of identity commitments; the nullifier blocks a second signal within one scope. The v4.0.0 audit by PSE (March 2024) is public; the Veridise audit covers v3 only.
- Anchoring: OpenTimestamps ([summary](https://en.wikipedia.org/wiki/OpenTimestamps); see opentimestamps.org). Calendar servers batch hashes into a Merkle tree and commit its root to Bitcoin; a calendar cannot forge a timestamp.

### Library caution (for Lane A)

Master prompt 6c names `kyber-py` and `dilithium-py`. Their own pages say they are educational pure-Python code that is not constant-time and carry a caution against use in real cryptographic applications ([kyber-py](https://github.com/GiacomoPope/kyber-py), [dilithium-py](https://pypi.org/project/dilithium-py/)). They pass the NIST known-answer tests, which shows correctness, not side-channel resistance. For a synthetic hackathon demo that is acceptable if the page says so. For a real pilot, use an audited library (for example liboqs) and hold keys in a proper key store. The README and the UI line should say "demo keys, reference implementation".

## 3. Threat model for blind-signed credentials

The master prompt asked for this (issuance timing, network metadata, revocation, scoring). Our reading, for Lane A to confirm or correct.

**What the scheme gives.** The committee signs a blinded token when an expert is approved. The expert unblinds it on their device and spends one token per answer. The server verifies the signature and rejects reuse. Because of blinding, the committee cannot match a spent token to the approval, even if it keeps all records.

**What can still link an answer to a person:**

1. **The magic link.** The card is opened with a personal link, `/e/{token}`, that identifies the expert. If the answer is posted to `/e/{token}/answer`, the server sees who submitted and when, and blind credentials add nothing. For the `anonymous` mask to mean anonymous from ACAPS, the answer must go to an endpoint that does not know the magic link: separate request, no cookie, no logged IP, no shared session. **This is the main open question (Q-A1).**
2. **Network metadata.** IP address, timing and user agent can identify a person on a panel of 8. A relay or a delay does not fix it. State it.
3. **Issuance timing.** If tokens are issued to one expert at a time and spent soon after, the order of events can link them. Batch issuance at approval and a delay between issue and spend reduce this. With a 2-month pilot and about 8 experts the anonymity set is small.
4. **Small anonymity set.** Among 8 panel members, "a vetted member answered" is a weak statement if only 3 are active that week. Also, the first expert to spend a token may be the only one awake in a time zone.
5. **Distinctive wording and content.** A free-text line can identify the author to peers or to ACAPS. The card says so. A credential does not help.
6. **Revocation.** To remove a compromised expert you cannot revoke a token you cannot link. You can refuse to issue new tokens and let the old ones expire. Say so.
7. **Scoring without linkage.** An `anonymous` answer cannot be scored per person, so it cannot feed that person's calibration or pattern report. That is a feature: `anonymous` means no track record. The honesty box should say how many answers in a round were anonymous and therefore unscored.
8. **Pattern reports vs anonymity.** Section 6d reports are per pseudonym. `anonymous` answers carry no pseudonym and must never be included. Test it.

**Wording for the card (one line):** "Answered with a one-time vetted credential. ACAPS cannot link it to your approval. Timing and wording can still identify you on a small panel." This follows the "guarantees / does not" rule.

## 4. Per-expert response-pattern reports (6d): the privacy view

The reports are sentences about each expert's behaviour (calibration, extremity, agreement after reveal, round-2 shift, source mix, abstention, answer latency, co-movement partners), shown to the committee and, opt-in, to the expert. Concerns, for the team:

- **Pseudonym is not anonymity.** The pseudonym is an HMAC of the internal id. The committee holds the registry, so a "per pseudonym" report is a report about a named person. Treat it as personal data: tell experts at sign-up, get consent, allow them to see their own report, and let them opt out of being profiled. The pilot needs a consent text; ACAPS legal should review (question to Alex).
- **Answer latency is a time-based metric.** The brief's "Should not" row says engagement metrics must not be the goal, and our hard rule 4 says no time-in-app. Latency is not time-in-app, but it measures responsiveness. Recommend dropping it or keeping it out of anything shown to the committee. (Proposal P22.)
- **Co-movement partners** names a pair of people as moving together. The v3 rule is that integrity notes describe patterns and do not diagnose a person. A note naming a partner is closer to an accusation. Recommend showing co-movement only as an aggregate at panel level ("two pairs on this panel moved together after reveal") on the desk, not per expert.
- **Small numbers.** After 3 pulses, a share like "4 of 5" is noise. Show the counts and the sentence "too few to say" under 5 pulses, and never present a pattern as a trait.
- **Never a score, never used to approve or remove, never public, never on free text.** Keep these four in the report footer and in tests.
- **Group interpretation.** An expert who "moves toward ACAPS's band in round 2" may simply be learning. The sentence must say what happened, not why.

## 5. What we say on a slide

One sentence, if asked in Q&A: "Answers are committed with a timestamp and anchored daily to an independent public timestamp. Anonymous answers carry a one-time credential ACAPS cannot link to your approval, and we list what that does not cover. The identity map is encrypted with a post-quantum scheme, every read is logged, and outcomes are signed. Each of these is on the trust page with its limit." Never say "unhackable", "anonymous from everyone", or "quantum-proof".

## 6. Questions for Lane A

- **Q-A1.** Is the `anonymous` submission separate from the personal magic link, with no logged IP? If not, do not show the credential line for that mask.
- **Q-A2.** What does "hybrid" mean for ML-KEM-768, and where does the committee key live in the demo?
- **Q-A3.** Who holds the ML-DSA key in the demo? The UI line should say "demo key".
- **Q-A4.** Does the demo run offline with the anchor `pending`? Then the ledger must say "pending", and nobody says "anchored" on stage.
- **Q-A5.** Are `anonymous` answers excluded from 6d reports and from calibration? Is there a test?
- **Q-A6.** Can an admin edit or delete rows in the registry access log?
