# Contracts

The canonical text lives in MASTER_PROMPT.md sections 4 and 5; this file only records changes.

| Date | Change | Announced by | Affects |
| --- | --- | --- | --- |
| 2026-11-06 | v1 contracts and routes as in MASTER_PROMPT.md | Zain | all lanes |
| 2026-11-06 | DraftUpdate gains claims[], skeptic[], missing_checks[], judge{}, repair_rounds (analyst-side verification loop, FF_AGENTS) | Zain | A, B (desk draft card) |
| 2026-11-06 | v2 after mentor interview: Expert tags/status, Panel composition, Answer confidence/source_tag/blind round, RoundResult.integrity + theme origin/corroboration, LedgerEntry.honesty, Calibration.overconfidence; routes /radar/status, /experts/apply, /experts/{id}/approve, /panels/match, /integrity/{pulse_id} | Zain | all lanes |
| 2026-11-06 | v3 after external reviews: Answer stance/panel_share_yes/committed_at; RoundResult mean+spread primary, sp_experiment, integrity_notes; LedgerEntry.honesty decision_use + panel_view_rejected; QuestionContract, OutcomeReport; scoring committee-side; routes /risks/{id}/contract, /pulses/{id}/outcome-report | Zain | all lanes |
| 2026-11-07 | v3.1: Risk Alert Engine on ACAPS monthly editions; Crisis, Edition, SeverityPoint, RiskCrisisLink, ShiftEvent; routes /crises, /radar/editions, /alerts/*, /risks/{id}/link; Pulse.reason adds "alert" with the INFORM record as evidence; external feeds dropped | Zain | all lanes |
| 2026-11-07 | v3.2: hardening stack built behind flags (PQ registry + attestations, blind credentials, ZK membership, anchoring, access log) and per-expert pattern reports; new routes under /credentials, /registry, /committee, /ledger/{id}/attestation, /anchors; Credential, Attestation, AnchorRoot, PatternReport models | Zain | all lanes |
