# Submission: Sealed Signals

Team: Zain Ul Haq (backend), Saleeta Qadir (frontend), Sho Izuno (research and pitch).
Challenge: ACAPS "Ground Truth", Hackathon for Good #8, The Hague, 6–8 November 2026.
Repository: this one. The submitted state is the `main` branch, tagged `v1.0`.

Live, and the fastest way to judge it without installing anything:

| What | Where |
| --- | --- |
| The product | <https://sealed-signals.zaindroid.me> |
| What is running there | `/version` reports the commit, the branch and when the process started |
| Ask a panel, end to end | `/ask` -- pick the risk, see who can speak to it, send each expert their own link, three QR seats for the room |
| The analyst desk on the demo round | `/desk?risk_id=R1043&pulse_id=P-0001` |
| An expert's card, no login | `/api/demo/links` lists the synthetic invitations; open any `card_url` |
| The public ledger and Verify | `/ledger` |
| Every mechanism with what it does not do | `/trust`, and `/api/trust/status` for the same words as JSON |

The round on the live site is sealed until its deadline, which is how it is meant to behave. To see the revealed
group view, open the round early and accept that the record will say so:
`curl -X POST .../api/pulses/P-0001/reveal -H 'content-type: application/json' -d '{"force": true}'`, which writes
`revealed_reason: "analyst_before_deadline"` into the published result.

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

Run it yourself: `make install && make demo` (offline, under 60 s), or `make dev` for the full product on :18000.
`make check` runs everything a merge has to pass. On the submitted commit that is 282 engine tests, 66 fixture-mode
browser tests, 39 against a running API, and 79 fixtures validated. Evidence of the test suite and the demo run is
committed under `docs/evidence/`.

What we do not claim, in the product's own words rather than ours. The hardening stack is eight mechanisms and each
one states what it does not do, on `/trust` and in `engine/engine/hardening/flags.py`: the zero-knowledge membership
proof ships with `FF_ZK` off because the Groth16 verifier is not implemented, so only its nullifier check is real;
Reach composes every message and sends none, because no SMS, WhatsApp or SMTP credential exists in this build, and
every channel reports `transport: "recorded"` rather than a delivered tick; a daily Merkle root is entered into
Sigstore Rekor and reads `pending` until the log returns an inclusion proof, which proves nothing until it does; and
the calibration programme is off until an expert reads the disclosure and opts in. Expert panels and their answers
are synthetic throughout.
