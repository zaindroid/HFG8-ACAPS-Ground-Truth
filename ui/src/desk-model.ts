import risk from "../../fixtures/GET_risks_R1043.json";
import pulse from "../../fixtures/POST_pulses_response.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import draftFixture from "../../fixtures/POST_pulses_draft_response.json";
import boardFixture from "../../fixtures/GET_committee_scoring.json";
import ledgerFixture from "../../fixtures/GET_ledger.json";
import verification from "../../fixtures/POST_ledger_verify_response.json";

import {
  sampleDataEnabled,
  sampleResult,
  sampleDraft,
  sampleBoard,
  sampleCurrentEntry,
  sampleHistory,
} from "./demo-data";
const samples = sampleDataEnabled();
export const result = samples ? sampleResult : resultFixture;
export const draft = samples ? sampleDraft : draftFixture;
export const board = samples ? sampleBoard : boardFixture;
export const demoLedger = samples
  ? { entries: [sampleCurrentEntry, ...sampleHistory], k_min: 5 }
  : ledgerFixture;
export { risk, pulse };
export type Decision = {
  action: "accept" | "edit" | "reject";
  probability: string;
  decision_use?: import("./service").DecisionUse;
  note: string;
  at: string;
};
export const storageKey = "sealed-signals-demo-decision-v1";
export function readDecision(): Decision | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(storageKey) || "null");
    return value &&
      ["accept", "edit", "reject"].includes(value.action) &&
      typeof value.note === "string" &&
      typeof value.at === "string" &&
      ["Very Low", "Low", "Medium", "High", "Very High"].includes(
        value.probability,
      )
      ? value
      : null;
  } catch {
    return null;
  }
}
// V2 carries the public contribution count inside the honesty box.
export const eligibleEntries = demoLedger.entries.filter(
  (entry) => (entry.honesty?.n || 0) >= Math.max(5, demoLedger.k_min),
);
export function verifyFixture(hash: string) {
  const entry = eligibleEntries.find((item) => item.verify_hash === hash);
  return entry
    ? { ...verification, sealed_at: entry.sealed_at }
    : { ...verification, valid: false };
}
export const percent = (v: number) => `${Math.round(v * 100)}%`;
export const date = (v: string) =>
  `${new Date(v).toLocaleString("en-GB", { timeZone: "UTC" })} UTC`;
