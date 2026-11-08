# Evidence

Outputs of the test suite and the demo run, regenerated at the Sunday freeze by `scripts/capture_evidence.sh` from a
clean clone.

| File | What it shows |
| --- | --- |
| `make-check.txt` | pytest results for the engine (unit, loop, alerts, hardening), the UI production build, fixture validation |
| `make-demo.txt` | transcript of the offline loop on R1043: alert replay, pulse, eight commitments, reveal, draft with Skeptic verdicts, decision, ledger entry, Verify, resolve, scores |
| `tree.txt` | the repository tree at the freeze |
| `screens/` | the expert screen, the analyst desk (Alerts, Reach, reveal view, draft) and the public ledger, at 375 px and 1920 px |
| `phones.md` | measured time and taps for the expert screen on two real phones over the venue Wi-Fi |
| `sensitivity.png` | the sensitivity test chart on the 104 resolved risks, labelled as a software test |
