import type {
  Honesty,
  Integrity,
  Match,
  RadarStatus,
  Application,
  Approval,
} from "./v2-types";
import type fullRisk from "../../fixtures/GET_risks_R1043.json";
import type resultFixture from "../../fixtures/GET_pulses_result.json";
import type { Card, Answer, AnswerDraft, SealReceipt, Mask } from "./api";
import type feedbackFixture from "../../fixtures/GET_e_token_feedback.json";
import type { AnswerKey, Envelope } from "./e2e";
import { demoAccessHeaders, sharedDemo } from "./demo-invitations";
export type Risk = Omit<
  typeof fullRisk,
  | "risk_type"
  | "trend"
  | "materialised"
  | "probability_assumed_number"
  | "rationale"
  | "vulnerability"
  | "expected_exposure"
  | "expected_impact"
  | "rationale_update"
  | "triggers"
  | "served_from"
  | "generated_at"
> & {
  // One fixture row cannot express a nullable column: R1043 fills all of these and most rows of
  // the export leave at least one blank. served_from and generated_at belong to the envelope
  // around a single risk, not to a risk inside a list.
  risk_type: string | null;
  trend: string | null;
  materialised: string | null;
  probability_assumed_number: number | null;
  rationale: string | null;
  vulnerability: string | null;
  expected_exposure: string | null;
  expected_impact: string | null;
  rationale_update: string | null;
  triggers: Trigger[];
  served_from?: string;
  generated_at?: string;
};
/** A trigger with no published completion rate reports null, not zero: the engine refuses to
 *  write a baseline nobody measured. R1043 has one on every trigger, so deriving the type from
 *  that row alone made the field mandatory and rejected most of the export. */
export type Trigger = Omit<
  (typeof fullRisk.triggers)[number],
  "completion_rate" | "sources"
> & {
  completion_rate: number | null;
  sources: { text: string; url: string }[];
};
export type Pulse = Card["pulse"];
/** The whole RoundResult, which is what the desk reads. The round-2 card sees only the small
 *  group view (api.ts `GroupView`). Moderator-only keys are absent because the public result
 *  does not carry them. */
export type Result = Omit<
  typeof resultFixture,
  "integrity_notes" | "probe_summary"
> & {
  integrity_notes?: { kind: string; text: string; evidence: string }[];
  confidence_interval?: { lower: number; upper: number };
};
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
export type Board = {
  // v3.4 scores panels, not people: /analyst/board became /committee/scoring and the
  // per-expert rows went with it, deliberately -- "scores are for forecasts, not people".
  panels: {
    panel_id: string;
    // A panel can be asked about more than one risk, so the engine reports the list rather than
    // one id, and counts the rounds and answers behind the score.
    risk_ids: string[];
    n_pulses: number;
    n_answers: number;
    n_resolved: number;
    panel_brier: number | null;
    acaps_band_brier: number | null;
    status: string;
  }[];
  divergence: { risk_id: string; panel: number; acaps: number }[];
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
  attestation_key: {
    scheme: string;
    key_id: string;
    public_key: string | null;
    note: string;
  };
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
export type AnchorRoot = {
  day: string;
  merkle_root: string;
  n_commitments: number;
  status: string;
  submitted_at: string | null;
  anchored_at: string | null;
  receipt: string | null;
  log: string | null;
  entry_uuid: string | null;
  log_index: number | null;
  integrated_at: string | null;
  verify_url: string | null;
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
export type AccessEntry = {
  who: string;
  why: string;
  expert_id: string;
  at: string;
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

export const apiBase = (import.meta.env.VITE_API_URL || "/api").replace(
  /\/$/,
  "",
);
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    /** The engine's own code for the refusal, when it sent one, for a screen to branch on. */
    public reason?: string,
  ) {
    super(message);
  }
}
/**
 * The sentence to show for a refusal.
 *
 * The engine sends `line` for a person and `message` for a developer. Prefer `line`: the
 * fallbacks below are written without knowing what happened, and a generic sentence about
 * "the current round" was both internal vocabulary and, in the most common case, wrong about
 * what the reader should do next.
 */
async function refusal(response: Response): Promise<{ line: string; reason?: string }> {
  let detail: unknown = null;
  try {
    detail = (await response.json())?.detail ?? null;
  } catch {
    /* A refusal with no body, or one that is not JSON, falls through to the status wording. */
  }
  if (detail && typeof detail === "object") {
    const body = detail as { line?: string; message?: string; reason?: string };
    if (body.line) return { line: body.line, reason: body.reason };
  }
  const status = response.status;
  return {
    line:
      status === 404 || status === 501
        ? "This capability is not available on the connected API yet."
        : status === 409
          ? // Reached only when the engine sent no line of its own. It says what is true of
            // every 409 on this path -- something about the question has already moved on --
            // without guessing which, and without telling anyone to refresh.
            "This question has already moved on, so it cannot take this. Open your link again to see where it stands."
          : status === 410
            ? "This invitation has expired. Ask your analyst for a new link."
            : status === 403 || status === 401
              ? "This invitation does not have access."
              : `The API returned ${status}. Please retry.`,
  };
}
export async function api<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  try {
    const response = await fetch(`${apiBase}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(sharedDemo ? demoAccessHeaders() : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal || AbortSignal.timeout(15000),
      cache: "no-store",
    });
    if (!response.ok) {
      const { line, reason } = await refusal(response);
      throw new ApiError(response.status, line, reason);
    }
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
  /** `force` is the recorded override for a reveal before pulse.expires_at. The engine refuses
   *  a plain reveal until then, and the result says revealed_reason: "analyst_before_deadline"
   *  when this was used, so no screen can claim a deadline reveal that was not one. */
  reveal: (id: string, force = false) =>
    api<Result>(
      `/pulses/${encodeURIComponent(id)}/reveal`,
      force ? { force: true } : {},
    ),
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
  // The comment above this type says the route moved; the call did not, so the scoring view
  // asked for a path the engine 404s.
  board: () => api<Board>("/committee/scoring"),
  // Reach (MASTER_PROMPT 6e). `transport` is `recorded` on every row in this build: the bodies
  // are composed in full and nothing is sent, because no gateway account exists here. Whatever
  // the desk shows has to say that, so the wording travels in the payload.
  reachStatus: () =>
    api<{
      channels: {
        channel: string;
        name: string;
        flag: string | null;
        enabled: boolean;
        built: string;
        reply: string;
        falls_back_to: string | null;
        off_note: string | null;
        transport: string;
      }[];
      cadence: Record<string, string | number>;
      contacts: { n_contacts: number; reachable: number; consented: number };
      charter: string;
      transport_note: string;
      guarantees: string;
      does_not: string;
    }>("/reach/status"),
  reachSend: (pulseId: string, body: Record<string, unknown> = {}) =>
    api<{
      n_sent: number;
      n_refused: number;
      sent: {
        expert_id: string;
        channel: string;
        transport: string;
        body: string;
      }[];
      refused: { expert_id: string; why: string }[];
      transport_note: string;
    }>(`/reach/pulses/${encodeURIComponent(pulseId)}/send`, body),
  reachDelivery: (pulseId: string) =>
    api<{
      pulse_id: string;
      channels: {
        channel: string;
        sent: number;
        answered: number;
        transport: string;
      }[];
      sent: number;
      answered: number;
      relayed: number;
      transport_note: string;
    }>(`/reach/pulses/${encodeURIComponent(pulseId)}/delivery`),
  closeTheLoop: (pulseId: string) =>
    api<{
      n_sent: number;
      sent: { expert_id: string; body: string }[];
      note: string;
    }>(`/reach/pulses/${encodeURIComponent(pulseId)}/close-the-loop`, {}),
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
  card: (token: string) => api<Card>(`/e/${encodeURIComponent(token)}`),
  // Two calls since v3.4: POST /answer drafts and commits nothing -- it is the route a link
  // click or a mail scanner can reach -- and POST /confirm is the commitment. The single typed
  // response here described the receipt, which this route does not return.
  // Either body may arrive as an end-to-end encrypted envelope (e2e.ts); the engine opens it and
  // carries on exactly as with the plain one.
  answer: (token: string, body: Answer | Envelope) =>
    api<AnswerDraft>(`/e/${encodeURIComponent(token)}/answer`, body),
  confirm: (token: string, body: { confirm_token: string } | Envelope) =>
    api<SealReceipt>(`/e/${encodeURIComponent(token)}/confirm`, body),
  answerKey: () => api<AnswerKey>("/answer-key"),
  /** After the reveal, and the only place an expert sees ACAPS's band. */
  feedback: (token: string) =>
    api<typeof feedbackFixture>(`/e/${encodeURIComponent(token)}/feedback`),
  // The hardening stack, for the Trust page (MASTER_PROMPT 6c and 6d). Typed loosely on purpose:
  // every payload carries its own guarantee and does-not wording and the page renders whatever
  // the engine states, so the two cannot drift into different promises.
  trust: () => api<TrustStatus>("/trust/status"),
  accessLog: () =>
    api<{
      entries: AccessEntry[];
      n_reads: number;
      guarantees: string;
      does_not: string;
    }>("/committee/access-log"),
  anchors: () => api<{ roots: AnchorRoot[]; enabled: boolean }>("/anchors"),
  credentialStatus: () => api<CredentialStatus>("/credentials/status"),
  patterns: () =>
    api<{
      panels: PatternReport[];
      not_yet: { panel_id: string; n_pulses_revealed: number }[];
      min_pulses: number;
      min_per_affiliation: number;
      never: string;
    }>("/committee/patterns"),
  attestation: (id: string) =>
    api<{
      attestation: Attestation;
      verification: { valid: boolean; checked: string; meaning: string };
      public_key: { scheme: string; key_id: string };
      anchor: AnchorRoot | null;
    }>(`/ledger/${encodeURIComponent(id)}/attestation`),
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
