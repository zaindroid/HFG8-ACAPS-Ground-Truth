import type {
  Honesty,
  Integrity,
  Match,
  RadarStatus,
  Application,
  Approval,
} from "./v2-types";
import type fullRisk from "../../fixtures/GET_risks_R1043.json";
import type { Card, Answer, Mask } from "./api";
export type Risk = typeof fullRisk;
export type Pulse = Card["pulse"];
export type Result = NonNullable<Card["group_view_if_round2"]> & {
  n_estimates?: number;
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
  super_estimators: {
    pseudonym: string;
    n: number;
    mean_brier: number;
    weight: number;
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
  board: () => api<Board>("/analyst/board"),
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
  answer: (token: string, body: Answer) =>
    api<{
      committed_at: string;
      commitment: string;
      generated_at: string;
      served_from: string;
    }>(`/e/${encodeURIComponent(token)}/answer`, body),
};
export function safeUrl(value: string) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
export function validResult(value: Result) {
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
