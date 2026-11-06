# Privacy engineering (repo page; not in the 3-minute pitch)

1. Who can learn what: see MASTER_PROMPT.md section 1a.
2. Pilot design: restricted identity registry with logged access; stable internal ids; pseudonyms to peers; `anonymous`
   answers stored without identity and not claimable; aggregates only to the public with n >= 5 (disclosure rule).
3. Phase 2, if anonymity from ACAPS itself is required: blind-signed single-use credentials issued by the committee.
   Threat model to write: issuance timing correlation, network metadata, revocation of a credential, scoring without linkage.
4. Research directions (one paragraph each, Lane C): zero-knowledge group membership (Semaphore) for reputation without
   identity; public timestamp anchoring of commitment roots (OpenTimestamps) for independent timing proof; post-quantum
   encryption of the identity registry (ML-KEM) and signed outcome attestations (ML-DSA) against long-horizon disclosure.
   What each guarantees, what it does not, and why none is in the pilot build.

## Research directions (Lane C)

Added 7 Nov. Each paragraph: what it is, what it guarantees, what it does not, why it is not in the pilot build. Source records were checked through search on 6-7 Nov; read the primary source before relying on a detail.

**Zero-knowledge group membership (Semaphore).** Semaphore is a protocol from Privacy & Scaling Explorations that lets a member of a group send a message, such as a vote, without revealing which member. Membership is a Merkle tree of identity commitments and a proof is checked against it; a nullifier prevents the same member signalling twice on one topic ([docs.semaphore.pse.dev](https://docs.semaphore.pse.dev/)). For us it could let an expert prove "I am an approved panel member" and keep a reputation without a name. It does not hide network metadata, it does not by itself stop the committee seeing who was added to the group, and it needs circuits and a browser prover that must run on weak phones. Not in the pilot: the restricted registry is simpler and the pilot panel is small and known to the committee.

**Public timestamp anchoring (OpenTimestamps).** The client hashes a file, sends the hash to calendar servers, which batch hashes into a Merkle tree and commit its root to Bitcoin; after confirmation, the proof can be checked with the file and a Bitcoin block header, and a calendar server cannot forge a timestamp ([OpenTimestamps, Wikipedia summary](https://en.wikipedia.org/wiki/OpenTimestamps); check opentimestamps.org for current operation). For us it would give an outside proof that a round's commitment root existed by a given time. It proves existence at a time. It says nothing about who answered or whether the content is true, and it needs outbound network access and a delay before confirmation. Not in the pilot: our own ledger timestamp already serves the analyst and the panel, and the demo must run offline.

**Post-quantum protection of the registry and outcome attestations.** In August 2024 NIST finalised FIPS 203 (ML-KEM, a key-encapsulation mechanism derived from CRYSTALS-Kyber) and FIPS 204 (ML-DSA, a signature scheme derived from CRYSTALS-Dilithium) (reported by several vendor summaries; confirm on nist.gov). The concern is "harvest now, decrypt later": an encrypted identity registry copied today could be read if large quantum computers arrive within the lifetime of the data. ML-KEM would protect registry keys; ML-DSA would sign outcome attestations. These address a long-horizon threat to confidentiality and integrity at rest. They do not fix access-control mistakes or insider access, which are the nearer risks. Not in the pilot: the registry is small, access is logged, and standard authenticated encryption at rest is adequate for a two-month supervised pilot. Revisit if ACAPS holds the registry for years.

**Blind-signed credentials (phase 2 path).** Chaum's blind signatures let an issuer sign a token without seeing its content, so the later holder cannot be linked to the issuance (Chaum, 1983, *Blind Signatures for Untraceable Payments*, DOI 10.1007/978-1-4757-0602-4_18). For us, the committee would issue single-use credentials to approved experts; an answer carries a credential and no identity. It would give anonymity from ACAPS itself. It does not remove timing correlation between issuance and use, network metadata, or the difficulty of scoring forecasts without linking them to a person. Threat model still to write (item 3 above). Not in the pilot, as v3 states.
