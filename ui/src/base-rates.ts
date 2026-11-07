// What the Risk List has actually done, derived from data/acaps-risk-list.csv by
// scripts/fetch_acaps_risk_list.py. Kept free of JSX and of imports from the page
// modules, so every screen can read the same numbers without an import cycle.
import insights from "./data/risk-insights.json";

export type BandRate = {
  label: string;
  n: number;
  materialised: number;
  rate: number;
  expected: number;
};
export type CrisisHistory = {
  risks: number;
  resolved: number;
  materialised: number;
  active: number;
  examples: {
    risk_id: string;
    title: string;
    level: string;
    status: string;
    entered: string;
  }[];
};

export const totals = insights.totals;
export const bands = insights.calibration as BandRate[];

/** Reported only where enough risks have resolved to mean anything. */
const MIN_RESOLVED = 10;

/**
 * How often risks in a stated probability band went on to materialise.
 * Null when the band is unknown or rests on too few resolved risks.
 */
export function bandRate(label: string | null | undefined): BandRate | null {
  if (!label) return null;
  const band = bands.find((b) => b.label === label);
  return band && band.n >= MIN_RESOLVED ? band : null;
}

/** The band midpoint the five-point scale implies, which is not the observed rate. */
export function bandMidpoint(label: string | null | undefined): number | null {
  const band = bands.find((b) => b.label === label);
  return band ? band.expected : null;
}

/** What the Risk List already records against a crisis, by its ACAPS crisis_id. */
export function crisisHistory(id: string | null | undefined): CrisisHistory | null {
  if (!id) return null;
  const record = (insights.by_crisis as Record<string, CrisisHistory>)[id];
  return record && record.risks > 0 ? record : null;
}

export const asPercent = (value: number) => `${Math.round(value * 100)}%`;
