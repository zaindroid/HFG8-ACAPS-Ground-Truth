import type {
  Honesty,
  Integrity,
  Match,
  RadarStatus,
  Application,
  Approval,
} from "./v2-types";
import type fullRisk from "../../fixtures/GET_risks_R1043.json";
import type { Card, Answer, AnswerDraft, Mask } from "./api";
import type resultFixture from "../../fixtures/GET_pulses_result.json";
import type feedbackFixture from "../../fixtures/GET_e_token_feedback.json";
import type scoringFixture from "../../fixtures/GET_committee_scoring.json";
import type panelPatternFixture from "../../fixtures/GET_committee_patterns_panel.json";
import type queueFixture from "../../fixtures/GET_verification_queue.json";
// One fixture row cannot express a nullable column: R1043 happens to have a risk type and a
// trend and no materialisation, so `typeof` alone would make all three mandatory and reject the
// rows of the export that leave them blank. These four really are optional in the ACAPS CSV.
export type Risk = Omit<
  typeof fullRisk,
  | "risk_type"
  | "trend"
  | "materialised"
  | "probability_assumed_number"
  // served_from and generated_at belong to the envelope around a single risk, not to a risk. A
  // row inside /risks carries neither, so a type that demanded them could not describe the list.
  | "served_from"
  | "generated_at"
  | "triggers"
> & {
  risk_type: string | null;
  trend: string | null;
  materialised: string | null;
  probability_assumed_number: number | null;
  triggers: Trigger[];
  // ACAPS's narrative columns. R1043 fills all of them, so `typeof` alone would make them
  // mandatory and reject the many export rows that leave one blank. The expert card's follow-up
  // questions are built from these (engine/probes.py) and simply skip the ones a risk lacks.
  rationale: string | null;
  vulnerability: string | null;
  expected_exposure: string | null;
  expected_impact: string | null;
  priority_needs: string[];
  rationale_update: string | null;
};
/** A trigger with no published completion rate reports null, not zero -- see the engine's
 *  _trigger_evidence, which refuses to write a baseline nobody measured. */
export type Trigger = Omit<
  (typeof fullRisk.triggers)[number],
  "completion_rate"
> & { completion_rate: number | null };
export type Pulse = Card["pulse"];
/** The whole RoundResult, which is what the desk reads. The round-2 card sees only the small
 *  group view (api.ts `GroupView`). Moderator-only keys are not in here because the public
 *  result does not carry them. */
export type Result = Omit<
  typeof resultFixture,
  "integrity_notes" | "probe_summary"
> & {
  confidence_interval?: { lower: number; upper: number };
};
/** The message after the reveal, and the only place an expert sees ACAPS's band. */
export type Feedback = typeof feedbackFixture;
export type PanelScoring = typeof scoringFixture;
export type PanelPattern = typeof panelPatternFixture;
export type VerificationQueue = typeof queueFixture;
export type Draft = {
  id: string;
  risk_id: string;
  pulse_id: string;
  proposed_probability: string;
  proposed_level: string;
  rationale_md: string;
  citations?: { text: string; url: string }[];
  claims?: {
    claim_id: string;
    text: string;
    evidence_kind: string;
    evidence_ref: string;
    numbers: number[];
  }[];
  skeptic?: { claim_id: string; verdict: string; checks: string[] }[];
  missing_checks?: { theme: string; status: string }[];
  judge?: {
    coverage: number;
    numbers_match: number;
    overall: number;
    flagged_claim_ids: string[];
  };
  status: string;
  note: string | null;
  decided_at: string | null;
};
export type PanelRow = {
  panel_id: string;
  risk_ids: string[];
  n_pulses: number;
  n_answers: number;
  n_resolved: number;
  panel_brier: number | null;
  acaps_band_brier: number | null;
  status: string;
};
/** v3.4 replaced the per-expert board with panel-level scoring. There is no list of pseudonyms
 *  ranked by Brier score any more, on any screen: the only per-person numbers live inside the
 *  consent-gated calibration programme. */
export type Board = {
  panels: PanelRow[];
  divergence: { risk_id: string; panel: number; acaps: number }[];
  note: string;
  band_assumption?: string;
  empty_note?: string;
  served_from?: string;
  generated_at?: string;
};
export type LedgerEntry = {
  risk_id: string;
  pulse_id: string;
  n?: number;
  sealed_at: string;
  group_probability: number;
  acaps_probability: string;
  acaps_level: string;
  outcome: string | null;
  resolved_at: string | null;
  verify_hash: string;
  honesty?: Honesty;
};
export type Calibration = {
  expert_internal_id?: string;
  n_resolved: number;
  mean_brier: number;
  overconfidence?: number;
  note: string;
};
export type DecisionUse = {
  what_decision: string;
  for_whom: string;
  by_when: string;
};
export type QuestionContract = {
  risk_id: string;
  event: string;
  location: string;
  horizon_deadline: string;
  resolution_source: string;
  adjudication_rule: string;
  frozen_at?: string;
};
export type OutcomeReport = {
  pulse_id: string;
  group_mean: number;
  outcome: string;
  analyst_decision_summary: string;
  n?: number;
};
export type Mechanism = {
  number: number;
  id: string;
  name: string;
  flag: string | null;
  enabled: boolean;
  build: string;
  where_it_shows: string;
  guarantees: string;
  does_not: string;
};
export type TrustStatus = {
  flags: Record<string, boolean>;
  mechanisms: Mechanism[];
  registry: {
    encryption: string;
    suite: string;
    key_id: string | null;
    key_holder: string;
    n_identities: number;
    access_log_count: number;
    lock_line: string;
    guarantees: string;
    does_not: string;
  };
  attestation_key: { scheme: string; key_id: string; public_key: string | null; note: string };
  credentials: CredentialStatus;
  anchors: { days: number; anchored: number; pending: number };
  zk: {
    enabled: boolean;
    scheme: string;
    groups: { panel_id: string; root: string; size: number }[];
    n_nullifiers_used: number;
    proof_verifier: string;
    guarantees: string;
    does_not: string;
  };
};
export type CredentialStatus = {
  scheme: string;
  n_batches: number;
  n_issued: number;
  n_spent: number;
  n_unlinkable_issued: number;
  linked: boolean;
  linkage_note: string;
  guarantees?: string;
  does_not?: string;
};
export type AccessEntry = { who: string; why: string; expert_id: string; at: string };
export type AnchorRoot = {
  day: string;
  merkle_root: string;
  n_commitments: number;
  status: string;
  submitted_at: string | null;
  anchored_at: string | null;
  receipt: string | null;
  calendar: string | null;
  note: string;
  means: string;
};
export type Attestation = {
  risk_id: string;
  outcome: string;
  resolved_at: string;
  commitment_root: string;
  scheme: string;
  key_id: string;
  signature: string;
  does_not: string;
};
/** v3.4: the committee reads about panels, not people. The per-expert report this used to
 *  describe no longer exists on the committee side at all -- individual calibration lives only
 *  inside the consent-gated programme, which the expert sees first. */
export type PatternReport = {
  panel_id: string;
  n_pulses: number;
  n_pulses_revealed: number;
  n_experts: number;
  sentences: string[];
  by_affiliation: { affiliation_tag: string; n: number; sentence: string }[];
  never_per_person: boolean;
  never: string;
  note: string;
};
/** What the engine returns for a *confirmed* answer. `credential` and `zk` arrived with the v3.2
 *  hardening stack; `anchor` is the daily commitment root this answer landed in, pending until a
 *  calendar confirms it. There is no ACAPS band in here: v3.4 moved it to the feedback message
 *  after the reveal, and the receipt says so in `band_note`. */
export type SealReceipt = {
  committed_at: string;
  commitment: string;
  version: number;
  mask: string;
  pseudonym: string | null;
  correction_allowed_until: string | null;
  edit_key: string | null;
  edit_key_note: string;
  message: string;
  sealing_note: string;
  acaps_band_shown: boolean;
  band_note: string;
  credential: { spent: boolean; unlinkable?: boolean; scheme?: string; line: string } | null;
  zk: Record<string, unknown> | null;
  anchor: AnchorRoot | null;
  served_from: string;
  generated_at: string;
};
export type Correction = {
  committed_at: string;
  commitment: string;
  version: number;
  previous_versions_kept: number;
  correction_allowed_until: string | null;
  message: string;
};
export const apiBase = (import.meta.env.VITE_API_URL || "/api").replace(
  /\/$/,
  "",
);
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  try {
    const response = await fetch(`${apiBase}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal || AbortSignal.timeout(15000),
      cache: "no-store",
    });
    if (!response.ok)
      throw new ApiError(
        response.status,
        response.status === 404 || response.status === 501
          ? "This capability is not available on the connected API yet."
          : response.status === 409
            ? "This action conflicts with the current round. Refresh before trying again."
            : response.status === 410
              ? "This invitation has expired. Ask your analyst for a new link."
              : response.status === 403 || response.status === 401
                ? "This invitation does not have access."
                : `The API returned ${response.status}. Please retry.`,
      );
    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new Error(
      "Cannot reach the API. Check the connection and try again. Your inputs are kept here.",
    );
  }
}
export const endpoint = {
  radar: () => api<RadarStatus>("/radar/status"),
  apply: (body: Application) =>
    api<{ expert_id: string; status: string }>("/experts/apply", body),
  approve: (id: string) =>
    api<Approval>(`/experts/${encodeURIComponent(id)}/approve`, {}),
  match: (id: string) =>
    api<Match>(`/panels/match?risk_id=${encodeURIComponent(id)}`),
  integrity: (id: string) =>
    api<Integrity>(`/integrity/${encodeURIComponent(id)}`),
  risks: () => api<{ risks: Risk[] }>("/risks"),
  risk: (id: string) => api<Risk>(`/risks/${encodeURIComponent(id)}`),
  pulse: (id: string) => api<Pulse>(`/pulses/${encodeURIComponent(id)}`),
  create: (id: string) =>
    api<Pulse>("/pulses", { risk_id: id, reason: "analyst" }),
  doorbell: () =>
    api<{ shifts: unknown[]; pulses_fired: string[] }>(
      "/pulses/doorbell/run",
      {},
    ),
  result: (id: string) =>
    api<Result>(`/pulses/${encodeURIComponent(id)}/result`),
  reveal: (id: string) =>
    api<Result>(`/pulses/${encodeURIComponent(id)}/reveal`, {}),
  draft: (id: string) =>
    api<Draft>(`/pulses/${encodeURIComponent(id)}/draft`, {}),
  decision: (
    id: string,
    action: string,
    note: string,
    probability?: string,
    decisionUse?: DecisionUse,
  ) =>
    api<Draft>(`/drafts/${encodeURIComponent(id)}/decision`, {
      action,
      note,
      ...(decisionUse ? { decision_use: decisionUse } : {}),
      ...(action === "edit" ? { edited_probability: probability } : {}),
    }),
  board: () => api<Board>("/committee/scoring"),
  contract: (id: string, body: QuestionContract) =>
    api<QuestionContract>(`/risks/${encodeURIComponent(id)}/contract`, body),
  outcomeReport: (id: string) =>
    api<OutcomeReport>(`/pulses/${encodeURIComponent(id)}/outcome-report`),
  ledger: () => api<{ entries: LedgerEntry[]; k_min: number }>("/ledger"),
  verify: (hash: string) =>
    api<{ valid: boolean; sealed_at: string; anchor: string | null }>(
      "/ledger/verify",
      { verify_hash: hash },
    ),
  resolve: (id: string, outcome: string, resolved_at: string) =>
    api<{ scores_written: number; weights_updated: number }>(
      `/risks/${encodeURIComponent(id)}/resolve`,
      { outcome, resolved_at },
    ),
  calibration: (token: string) =>
    api<Calibration>(`/me/${encodeURIComponent(token)}/calibration`),
  // MASTER_PROMPT 6c and 6d. Typed loosely on purpose: the payloads carry their own guarantee and
  // does-not wording, and the Trust page renders whatever the engine states rather than a copy of
  // it held here, so the two cannot drift.
  trust: () => api<TrustStatus>("/trust/status"),
  accessLog: () =>
    api<{ entries: AccessEntry[]; n_reads: number; guarantees: string; does_not: string }>(
      "/committee/access-log",
    ),
  anchors: () => api<{ roots: AnchorRoot[]; enabled: boolean }>("/anchors"),
  credentialStatus: () => api<CredentialStatus>("/credentials/status"),
  // Panel-level since v3.4: the committee reads about panels, not people.
  patterns: () =>
    api<{
      panels: PanelPattern[];
      not_yet: { panel_id: string; n_pulses_revealed: number }[];
      min_pulses: number;
      min_per_affiliation: number;
      never: string;
    }>("/committee/patterns"),
  panelPattern: (panelId: string) =>
    api<PanelPattern>(`/committee/patterns/${encodeURIComponent(panelId)}`),
  scoring: () => api<PanelScoring>("/committee/scoring"),
  verificationQueue: (pulseId: string, who: string, why: string) =>
    api<VerificationQueue>(
      `/verification-queue/${encodeURIComponent(pulseId)}` +
        `?who=${encodeURIComponent(who)}&why=${encodeURIComponent(why)}`,
    ),
  feedback: (token: string) =>
    api<Feedback>(`/e/${encodeURIComponent(token)}/feedback`),
  attestation: (id: string) =>
    api<{
      attestation: Attestation;
      verification: { valid: boolean; checked: string; meaning: string };
      public_key: { scheme: string; key_id: string };
      anchor: AnchorRoot | null;
    }>(`/ledger/${encodeURIComponent(id)}/attestation`),
  card: (token: string) => api<Card>(`/e/${encodeURIComponent(token)}`),
  // Two calls, because v3.4 made them two: the draft commits nothing and the confirmation does.
  answer: (token: string, body: Answer) =>
    api<AnswerDraft>(`/e/${encodeURIComponent(token)}/answer`, body),
  confirm: (token: string, confirmToken: string) =>
    api<SealReceipt>(`/e/${encodeURIComponent(token)}/confirm`, {
      confirm_token: confirmToken,
    }),
};
export function safeUrl(value: string) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
/** Structural on purpose: the desk passes a whole RoundResult and the round-2 card passes the
 *  small group view, and both carry the three fields this checks. */
export function validResult(value: {
  n: number;
  mean: number;
  spread: { min: number; max: number; iqr: number };
}) {
  return (
    Number.isInteger(value.n) &&
    value.n >= 5 &&
    Number.isFinite(value.mean) &&
    value.mean >= 0 &&
    value.mean <= 1 &&
    value.spread?.min >= 0 &&
    value.spread.max <= 1 &&
    value.spread.min <= value.mean &&
    value.spread.max >= value.mean
  );
}
export const masks: Mask[] = ["known", "pseudonym", "anonymous"];
