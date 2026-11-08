# Submission: Sealed Signals

Team: Zain Ul Haq (backend), Saleeta Qadir (frontend), Sho Izuno (research and pitch).
Challenge: ACAPS "Ground Truth", Hackathon for Good #8, The Hague, 6–8 November 2026.
Repository: this one; the submitted state is the `main` branch after the pull request from `demo`, tagged `v1.0`.

Short description (for the submission form):

Sealed Signals gives ACAPS's expert checks a trail. A deterministic alert engine diffs ACAPS's own monthly severity and
access data and proposes which risk to ask about; the analyst approves a frozen question; the eight best-matched
experts receive it by email, WhatsApp, Signal, SMS, Teams or a call, with no sign-up and one link; they answer on one
screen in under a minute behind a mask they choose per answer; answers are committed with a timestamp and revealed
together at the deadline; a model-optional verification loop turns the panel view into a cited draft with every
number checked; the analyst accepts, edits or rejects, on record; and a public ledger shows the group view, what fed
into it, its limits and its misses, with a Verify action anyone can click. Experts are never ranked or scored as
people. The three must-haves of the brief are built: easy to use, expert-controlled anonymity, public anonymity.
Demo risk: R1043, eastern Chad, driven by the real April 2026 move in ACAPS's INFORM severity index.

Run: `make install && make demo` (offline, under 60 s), `make dev` for the full product on :18000. Evidence of the
test suite and the demo run is committed under `docs/evidence/`.
