# Team checklist before the freeze (Sun 2026-11-08 10:30)

Lane C, 2026-11-07. One page for Zain, Saleeta and Sho. Details are in `pitch-v6-script.md`, `qa-prep.md` and `citations.md`.

## Deck v6 wording (Zain, `demo` branch)

1. s8 title "Proof it runs, not promises": change to "It runs." (rule: no "proof" for the synthetic test)
2. s9 row "quantum-safe at rest": change to "encrypted at rest, post-quantum key establishment", backup slides only
3. s2 and s7 chips with SHA-256, ML-DSA-65, ML-KEM-768, OpenTimestamps: move to the Q and A slides or shrink to one line
4. s7 chip "anchored OpenTimestamps": say "anchored" only when the receipt is no longer pending
5. s8 "Five independent model reviews": change to "five model-assisted design reviews" or drop
6. s5 citation: "Pennycook and Rand accuracy prompt" becomes "inspired by"; that work tested news sharing
7. Pilot length: the deck says 3 months, the old `pitch.md` says 2 months; use 3

## Product and demo (Saleeta)

8. The expert card is three steps in `lane/frontend`. The demo video (`slides/motion-v2`) shows the older screen; recapture after the final merge.
9. Confirm which of the six Reach channels run in the build. The pitch names email, WhatsApp, Signal, SMS and Teams; say only what runs.

## Pitch (Sho)

10. Rehearse the 354-word script against the clock (target 175 seconds, 5 seconds spare).
11. Decide demo placement: after the pitch (script as written) or inside it (cut s6, s8, s4).
12. Read the Lord et al. abstract; the page was blocked today.
13. Get the ACAPS 2016 cognitive-biases brief from the organisers, or drop it from the s5 footer.
14. Fill the QR code and `proof.png` placeholders if the v6 deck uses them.

## Decisions for the team

- Merge the motion-v2 deck (`slides/motion-v2`) into v6, or keep v6 only?
- Who presents and who drives the demo?
