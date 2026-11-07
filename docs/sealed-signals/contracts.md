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
| 2026-11-07 | v3.3: Reach module (Contact, Delivery, SeedItem; routes /reach/*, /inbound/*), one-screen expert card spec, PatternReport gains seed_accuracy, perceived_vs_actual_gap, meta_accuracy, test_retest_delta, median_latency_s | Zain | all lanes |
| 2026-11-07 | v3.4: Answer gains likelihood_word, against, trigger_pick, relayed/relayed_by/confirmed_by_expert_at, corrected_at; probability and confidence optional; Pulse gains question{} and reveal_status; RoundResult: minority_rationales → disagreement[] (unattributed) + missing_evidence[] + verification_queue_count; PatternReport/SeedItem removed → PanelPattern, CalibrationItem, CalibrationEnrolment, Charter; Contact: coverage_area, consent{}, preferences_set_by, stopped; routes /e/{token}/confirm, PUT /e/{token}/answer, /e/{token}/relayed-confirm, /e/{token}/feedback, /committee/scoring (replaces /analyst/board), /committee/patterns/{panel_id}, /me/{token}/calibration/opt-in | Zain | all lanes |
| 2026-11-07 | v3.4.1: section 0b personas and workflow quotes filled from the organisers' pack; docs/sealed-signals/personas.md added; no contract change | Zain | Lane C, Lane B (persona slide, coverage filter wording) |
| 2026-11-07 | v3.4.2: main merged into demo; root CLAUDE.md, AGENTS.md, SUBMISSION.md, CHANGELOG.md, docs/evidence/, scripts/capture_evidence.sh; master prompt 0d (repo is the prototype score; submission procedure) | Zain | all lanes |
