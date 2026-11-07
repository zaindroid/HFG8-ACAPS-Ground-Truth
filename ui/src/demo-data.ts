import risk from "../../fixtures/GET_risks_R1043.json";
import result from "../../fixtures/GET_pulses_result.json";
import draft from "../../fixtures/POST_pulses_draft_response.json";
import ledger from "../../fixtures/GET_ledger.json";
import board from "../../fixtures/GET_committee_scoring.json";
import historicalRisks from "./data/demo-risks.json";
import { hasWorkspaceSession } from "./workspace-session";
import type {
  Risk,
  LedgerEntry,
  Calibration,
  Draft,
  Board,
  DecisionUse,
} from "./service";
import type { Application, Approval } from "./v2-types";

export const demoDataKey = "sealed-signals-samples-v1";
const decisionKey = "sealed-signals-demo-decision-v1";
const applicationsKey = "sealed-signals-sample-applications-v1";
export const sampleDecisionUse: DecisionUse = {
  what_decision: "Pre-position shelter and cash in Ouaddaï",
  for_whom: "NGO preparedness lead, eastern Chad",
  by_when: "2026-11-20",
};
export const sampleResult = {
  ...result,
  integrity_notes: result.integrity_notes.filter(
    (n) => n.kind !== "coverage_gap",
  ),
};
const claims = draft.claims
  .filter((c) => c.claim_id !== "C2" && c.claim_id !== "C4")
  .map((c) =>
    c.claim_id === "C1"
      ? {
          ...c,
          text: "The equal-weight panel mean is 0.69 from eight estimates. This is panel judgement, not an observed outcome.",
          evidence_ref: "P-0001:mean",
          numbers: [0.69, 8],
        }
      : {
          ...c,
          text: "ACAPS INFORM Severity increased from 6.1 in March 2026 to 6.9 in April 2026 for displacement from Sudan to Chad, a change of 0.8 points.",
          evidence_ref: "inform-severity-index:TCD005:Mar2026:Apr2026",
          numbers: [6.1, 6.9, 0.8],
        },
  );
export const sampleDraft = {
  ...draft,
  citations: [
    {
      text: "ACAPS INFORM Severity · Chad · April 2026",
      url: "https://api.acaps.org/api/v1/inform-severity-index/Apr2026/",
    },
  ],
  judge: {
    ...draft.judge,
    coverage: 1,
    numbers_match: 1,
    overall: 1,
    flagged_claim_ids: [],
  },
  claims,
  rationale_md: claims.map((c) => c.text).join("\n\n"),
  skeptic: draft.skeptic
    .filter((c) => c.claim_id !== "C2" && c.claim_id !== "C4")
    .map((c) =>
      c.claim_id === "C1"
        ? {
            ...c,
            checks: [
              "Equal-weight mean 0.69 and count 8 match the panel record exactly.",
            ],
          }
        : {
            ...c,
            checks: [
              "Before 6.1, after 6.9 and delta 0.8 match the ACAPS edition evidence on the pulse.",
            ],
          },
    ),
} satisfies Draft;
export const sampleRisks: Risk[] = [risk, ...historicalRisks];
const estimates = [0.8, 0.7, 0.65, 0.7, 0.4];
export const sampleForecasts = historicalRisks.map((r, i) => ({
  risk_id: r.risk_id,
  country: r.country,
  probability: estimates[i],
  outcome: r.status === "Materialised" ? 1 : 0,
  resolved_at: `2026-10-${String(12 + i * 3).padStart(2, "0")}`,
  brier: (estimates[i] - (r.status === "Materialised" ? 1 : 0)) ** 2,
}));
const meanBrier =
  sampleForecasts.reduce((sum, f) => sum + f.brier, 0) / sampleForecasts.length;
const accuracy =
  sampleForecasts.filter((f) => (f.probability >= 0.5 ? 1 : 0) === f.outcome)
    .length / sampleForecasts.length;
const certainty =
  sampleForecasts.reduce(
    (sum, f) => sum + Math.max(f.probability, 1 - f.probability),
    0,
  ) / sampleForecasts.length;
export const sampleCalibration: Calibration = {
  n_resolved: sampleForecasts.length,
  mean_brier: meanBrier,
  overconfidence: certainty - accuracy,
  note: "Synthetic forecast probabilities and illustrative dates; outcomes use the repository’s Risk Radar export.",
};
export const sampleBoard: Board = {
  ...board,
  divergence: [{ risk_id: risk.risk_id, panel: sampleResult.mean, acaps: 0.7 }],
};
export const sampleCurrentEntry: LedgerEntry = {
  ...ledger.entries[0],
  group_probability: sampleResult.mean,
  honesty: {
    ...ledger.entries[0].honesty,
    coverage_gaps: [],
    claims_in_verification_queue: 2,
    decision_use: sampleDecisionUse,
    caveat:
      "Two raised themes await verification and are excluded from the draft.",
  },
};
export const sampleHistory: LedgerEntry[] = sampleForecasts.map((f, i) => ({
  risk_id: f.risk_id,
  pulse_id: `P-SAMPLE-${i + 1}`,
  sealed_at: `2026-04-${String(10 + i * 3).padStart(2, "0")}T09:00:00Z`,
  group_probability: f.probability,
  acaps_probability: historicalRisks[i].probability_acaps,
  acaps_level: historicalRisks[i].level,
  outcome: f.outcome === 1 ? "materialised" : "not_materialised",
  resolved_at: `${f.resolved_at}T00:00:00Z`,
  verify_hash: (i + 1).toString(16).padStart(64, "0"),
  honesty: {
    ...ledger.entries[1].honesty,
    n: 8,
    agreement: 0.75,
    spread: [
      Math.max(0, f.probability - 0.2),
      Math.min(1, f.probability + 0.2),
    ],
    panel_hit_rate: accuracy,
    misses: 1,
    coverage_gaps: [],
    decision_use: {
      what_decision:
        i === 3
          ? "Keep a contingency reserve"
          : "Review preparedness allocation",
      for_whom: `Synthetic ${f.country} preparedness team`,
      by_when: `2026-05-${String(10 + i * 3).padStart(2, "0")}`,
    },
    panel_view_rejected: i === 3,
    analyst_rationale:
      i === 3
        ? "The synthetic analyst retained the existing probability after reviewing indicators. The panel’s higher estimate did not materialise."
        : null,
    caveat:
      "Five resolved forecasts in the track record; one miss is included.",
  },
}));
export type SampleApplication = Application & {
  expert_id: string;
  pseudonym: string;
  status: string;
  approved_by: string[];
};
const initialApplications: SampleApplication[] = [
  {
    expert_id: "X-SAMPLE-001",
    pseudonym: "river-ibis",
    geo_tags: ["TCD", "SDN"],
    theme_tags: ["conflict", "displacement"],
    affiliation_tag: "research",
    languages: ["en", "fr"],
    channel: "email",
    status: "applied",
    approved_by: [],
  },
  {
    expert_id: "X-SAMPLE-002",
    pseudonym: "calm-reed",
    geo_tags: ["HTI"],
    theme_tags: ["food", "access"],
    affiliation_tag: "ngo",
    languages: ["en", "fr"],
    channel: "email",
    status: "applied",
    approved_by: ["synthetic-admin-a"],
  },
  {
    expert_id: "X-SAMPLE-003",
    pseudonym: "clear-acacia",
    geo_tags: ["YEM"],
    theme_tags: ["displacement", "access"],
    affiliation_tag: "journalism",
    languages: ["en", "ar"],
    channel: "email",
    status: "approved",
    approved_by: ["synthetic-admin-a", "synthetic-admin-b"],
  },
];
export function loadSampleWorkspace() {
  if (import.meta.env.VITE_MOCK !== "1") return;
  sessionStorage.setItem(demoDataKey, "on");
  sessionStorage.setItem(applicationsKey, JSON.stringify(initialApplications));
  sessionStorage.setItem(
    decisionKey,
    JSON.stringify({
      action: "accept",
      probability: "High",
      note: "Synthetic analyst decision: retain High, record the preparedness decision and keep the single-source observation in verification.",
      decision_use: sampleDecisionUse,
      at: "2026-11-07T09:30:00Z",
    }),
  );
}
export function sampleDataEnabled() {
  if (import.meta.env.VITE_MOCK !== "1") return false;
  try {
    if (sessionStorage.getItem(demoDataKey) === null && hasWorkspaceSession()) {
      const previousDecision = sessionStorage.getItem(decisionKey);
      loadSampleWorkspace();
      if (previousDecision)
        sessionStorage.setItem(decisionKey, previousDecision);
      else
        sessionStorage.removeItem(decisionKey);
    }
    return sessionStorage.getItem(demoDataKey) === "on";
  } catch {
    return false;
  }
}
export function clearSampleWorkspace() {
  sessionStorage.setItem(demoDataKey, "off");
  sessionStorage.removeItem(decisionKey);
  sessionStorage.removeItem(applicationsKey);
}
export function startSampleRound() {
  sessionStorage.removeItem(decisionKey);
}
export function sampleApplications(): SampleApplication[] {
  try {
    return (
      JSON.parse(sessionStorage.getItem(applicationsKey) || "null") ||
      structuredClone(initialApplications)
    );
  } catch {
    return structuredClone(initialApplications);
  }
}
export function saveSampleApplication(body: Application) {
  const rows = sampleApplications();
  const item: SampleApplication = {
    ...body,
    expert_id: `X-SAMPLE-${String(rows.length + 1).padStart(3, "0")}`,
    pseudonym: `sample-expert-${rows.length + 1}`,
    status: "applied",
    approved_by: [],
  };
  sessionStorage.setItem(applicationsKey, JSON.stringify([...rows, item]));
  return item;
}
export function saveSampleApproval(
  id: string,
  approved_by: string[],
): Approval {
  const rows = sampleApplications();
  const value = {
    expert_id: id,
    status: approved_by.length >= 2 ? "approved" : "applied",
    approved_by,
  };
  sessionStorage.setItem(
    applicationsKey,
    JSON.stringify(
      rows.map((r) => (r.expert_id === id ? { ...r, ...value } : r)),
    ),
  );
  return value;
}
