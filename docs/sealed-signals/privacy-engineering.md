# Privacy engineering (repo page; not in the 3-minute pitch)

Updated for master prompt v3.4. Sections 1 and 2 are the pilot design. Section 3 is the hardening stack of
MASTER_PROMPT 6c as **built**, with the test that backs each claim. Section 4 is what v3.4 did to measurement, which
is mostly to remove it. Section 5 is the part that is honestly not finished.

Wording rule for all of it: every mechanism is described with the guarantee / does-not pair from
`trust-design.md`. Those sentences live in one place in the code, `engine/engine/hardening/flags.py`, and the API
and the UI render them from there rather than keeping a second copy. `GET /api/trust/status` returns all six.

1. **Who can learn what**: see MASTER_PROMPT.md section 1a.
2. **Pilot design**: restricted identity registry with logged access; stable internal ids; pseudonyms to peers;
   unattributed answers stored without an identity link, not claimable, and without personalised feedback
   (the product says pseudonymised, never anonymous); aggregates only to the public with n >= 5.

## 3. The hardening stack, as built

| # | Mechanism | Flag | Where the code is | Test evidence |
| --- | --- | --- | --- | --- |
| 1 | ML-KEM-768 + X25519 hybrid key establishment wrapping the AES-256-GCM key over the identity map (AES-256-GCM at rest) | `FF_PQ`, on | `hardening/registry.py` | `test_crypto.py::test_registry_round_trip_under_the_hybrid_kem`, `::test_registry_ciphertext_is_not_decryptable_without_the_committee_key`, `::test_registry_falls_back_and_says_so_when_the_flag_is_off` |
| 2 | ML-DSA-65 signature over each resolved outcome record | `FF_PQ`, on | `hardening/attest.py` | `::test_attestation_verifies_and_fails_on_a_flipped_byte`, `::test_attestation_fails_when_the_record_is_edited`, `::test_attestation_public_key_is_stable_across_instances` |
| 3 | RSA blind signatures, RFC 9474 RSABSSA-SHA384-PSS-Deterministic | `FF_BLIND`, on | `hardening/credentials.py` | `::test_blind_signature_verifies_as_standard_rsa_pss`, `::test_a_credential_cannot_be_spent_twice`, `::test_the_issuer_cannot_match_a_spent_token_to_an_approval` |
| 4 | Semaphore-shaped group membership | `FF_ZK`, **off** | `hardening/zk.py` | `::test_nullifier_rejects_a_second_answer`, `::test_the_verdict_never_claims_the_proof_was_checked` — see section 5 |
| 5 | Sigstore Rekor public timestamp of the daily commitment root | `FF_ANCHOR`, on | `hardening/anchors.py` | `::test_anchor_goes_pending_then_anchored`, `::test_an_unreachable_log_does_not_invent_an_anchor`, `::test_the_logged_entry_carries_only_the_root_and_a_valid_signature`, `::test_a_receipt_is_only_returned_for_a_commitment_in_that_root` |
| 6 | Registry access log | always on | `hardening/registry.py` | `::test_a_registry_read_appears_in_the_log`, `::test_an_unattributed_read_is_refused`, `::test_counting_identities_is_not_a_read` |
| 7 | End-to-end answer encryption: ML-KEM-768 + X25519 to the engine's key, HKDF-SHA256, AES-256-GCM, token and route as AAD; encrypted in the browser | `FF_E2E`, on | `hardening/e2e.py`, `ui/src/e2e.ts` | `test_e2e.py::test_draft_confirm_and_correct_round_trip_encrypted`, `::test_a_tampered_ciphertext_is_refused`, `::test_an_envelope_sealed_for_another_link_or_route_is_refused`, `::test_an_envelope_from_the_browser_module_opens_in_python` |

Notes that matter more than the table:

* **The blind signature is a real one.** The committee signs a value it cannot read, and the unblinded result passes
  an ordinary `cryptography` RSA-PSS verify — the test checks it that way on purpose, against a library that knows
  nothing about this codebase. The zero-length salt is what makes the deterministic variant deterministic; the PSS
  encoding is written out in `credentials.py` because the blinding has to happen on the encoded integer and no
  library exposes that step.
* **There are two issuance paths and they do not make the same claim.** `POST /api/credentials/issue` with
  `blinded` is the real one: the card blinds, the server signs, the card unblinds, and nothing the server stored
  names the token it later accepts. With `count` the server runs the client side itself for the demo, so it held
  the token id for an instant. That batch is marked `unlinkable: false`, and the committee view says which mix it
  is looking at rather than printing the unlinkability sentence over tokens that have not earned it.
* **An anchor is pending until the log returns a proof.** The status reads `anchored` only when Rekor returns an
  inclusion proof for the entry, either with the submission or on a later `GET /api/v1/log/entries/<uuid>`. Only the
  signed 32-byte root is logged. The entry format (a `hashedrekord` whose ECDSA P-256 signature verifies against the
  root) is tested locally; the pending-to-anchored transition is tested with an injected log, because a test suite
  should not depend on a public service being up.
* **The fallbacks are real code, not a skipped branch.** `FF_PQ` off encrypts with a data key stored beside the
  ciphertext and signs with an HMAC; `FF_BLIND` off issues a single-use HMAC token. Each says in its own payload
  which path ran. The flag-off fallbacks have their own tests.
* **Key material.** ML-KEM and ML-DSA keys are derived from `COMMITTEE_KEY` under separate labels, so the published
  key ids survive a restart. RSA has no seeded keygen in `cryptography`, so the credential issuer is generated per
  process and `GET /api/credentials/issuer` says so: a restart retires every token signed by the old issuer.

## 4. Measurement: what v3.4 took out, and what it put behind consent

The v3.2 build computed a response-pattern report per expert: calibration, overconfidence, extremity, agreement with
ACAPS, round-2 shift, source mix, abstention rate. It was committee-side, pseudonymous and descriptive, and it is
gone. The reason is one sentence from section 6d: **no measurement is hidden in a pulse.** Those numbers were
computed from answers given to a question that never said it was measuring the person answering it. Pseudonymising
the output does not fix that; it only decides who gets to read it.

What replaced it:

| v3.2 | v3.4 |
| --- | --- |
| `GET /committee/patterns/{pseudonym}` — one person's report | `GET /committee/patterns/{panel_id}` — sentences about the panel |
| `GET /me/{token}/patterns?opt_in=true` | removed; individual calibration lives only in the programme below |
| `GET /analyst/board` — pseudonyms ranked by Brier score | `GET /committee/scoring` — panels scored against the ACAPS band |
| seed questions, knowledge-gap and timing measures on the card (v3.3) | removed from the card entirely |

**Panel reports** (`hardening/patterns.py`). After three revealed rounds on the same panel: convergence after the
reveal, the spread over time, the abstention share, the source mix, and which expertise the panel does not have.
Affiliation-level sentences only where that affiliation has three members on the panel; everything smaller is merged
and the payload says it was merged. Descriptive, never causal — "UN-affiliated answers sat above the panel mean on 3
of 4 pulses" is allowed, "UN experts are optimistic" is not. No sentence may contain a pseudonym, and a test asserts
that over every seeded pseudonym.

**The calibration programme** (`hardening/calibration.py`, `FF_CALIBRATION`, **off**). The only mechanism in this
build that measures a person, and it ships off, so the default state of the system is one where nobody is measured.
Enrolment needs an explicit yes against the current disclosure version: consent does not carry across a change to
what is measured, and the engine refuses a consent quoting an older one. Items are short factual questions whose
answer ACAPS already holds — taken from the resolved rows of the export's own Status column, each carrying the record
it is adjudicated against — with a numeric confidence prompt, 50 to 100 %. A report exists only after 20 items, goes
to the expert first and alone, and is one paragraph in plain words. The committee sees it only after a second,
separate opt-in, and never as a weight. `off` at any time, and off means the report stops being produced.
`GET /calibration/disclosure` is readable with the flag off on purpose: what we would measure is not a secret, it is
the thing consent is given against.

Deliberately not built, and recommended against in writing: fictitious references (overclaiming foils),
response-time and edit-count measures, test–retest traps. Nothing a participant would recognise as deception if it
were explained to them afterwards.

Test evidence: `tests/hardening/test_patterns.py` — the floor, each sentence, the affiliation merge, that no
sentence names a person, that the module has no per-expert entry point left, and the programme's consent, floor,
switch-off and committee-counts behaviour.

## 4a. The card, and where a written line goes

Three changes in v3.4 are privacy decisions as much as usability ones.

* **Nothing commits on a link click.** `POST /e/{token}/answer` drafts and returns the line the confirmation screen
  repeats back; `POST /e/{token}/confirm` commits. A mail scanner, a link preview or a mistaken tap cannot answer on
  somebody's behalf, and the credential is spent by the confirmation rather than the draft.
* **The mask has no default.** A default mask is a decision about someone's confidentiality taken by whoever wrote
  the code, so the engine refuses an answer without one rather than guessing.
* **Correction until the deadline, with every version kept.** For an answer under the "no identity kept" mask the
  only handle is an edit key minted once with the confirmation; the server stores its hash. A token-to-answer map
  would have been simpler and would have reconstructed exactly the link that mask exists to prevent.

Where a written line ends up is now the central disclosure question, because a panel is eight people:

* A theme **two or more** experts raised keeps its words and appears in `missing_evidence`.
* A line **one** expert wrote keeps its count and loses its words: `missing_themes` reports it as held, and the text
  goes to the verification queue, read only with a who and a why, with every read logged.
* **Disagreement is unattributed and never verbatim** — a direction, a count, and the subject the notes were about,
  derived from themes. A group of one does not even get its subject named, because in a panel of eight the subject
  narrows it to a person.
* The counts of the card's closed follow-up questions are moderator-only, for the same reason: a one-of-eight option
  count read beside a distinctive line is the pair that identifies somebody.

The honesty box carries the standing line on every entry: *in a panel of eight a distinctive reason may identify its
author to colleagues; experts were told this before answering.* The card shows the same sentence, from the same
constant, next to the mask picker.

## 5. What is not built, and why the flag is off

**The zero-knowledge proof verifier.** The group tree, its published root and the per-pulse nullifier are built and
enforced: a second answer under the same nullifier is refused, server-side, and that is tested. The Groth16 check
that proves a nullifier belongs to the tree without naming the leaf is **not** implemented. It needs the circuit's
verification key and a BN254 pairing check, and the proof has to be generated in the browser; neither exists in
this build. So `verify` returns `cryptographic_verification: false`, names what it did and did not check, `FF_ZK`
ships off, and with the flag off no proof is accepted at all.

Without that verifier the mechanism cannot tell a real proof from a well-formed fake, so it guarantees
double-answer prevention and nothing else. The Trust page says this in those words. On stage it belongs in "what we
did not do and why", beside no public scores, no auto-decisions and no blockchain logic — not in the list of
things that work.

**Threat model still to write** for the credential path: issuance timing correlation, network metadata, revocation
of a credential, and scoring without linkage. Items 1 to 3 of the does-not column already name the first two as
out of scope; a paragraph each is owed.
