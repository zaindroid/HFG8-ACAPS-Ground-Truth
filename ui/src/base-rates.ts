// What the Risk List has actually done.
//
// Served by the engine at /api/insights, so the figures follow whatever export the engine
// is reading rather than a file baked in at build time. The bundled JSON stays as the
// starting value: it keeps mock mode and the offline demo working, and it means a chart
// never renders empty while the request is in flight. Hydration replaces it in place and
// notifies subscribers.
import { useSyncExternalStore } from "react";
import bundled from "./data/risk-insights.json";
import { api } from "./service";
import { mock } from "./api";

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
export type Insights = {
  source: string;
  live: boolean;
  totals: {
    risks: number;
    resolved: number;
    active: number;
    materialised: number;
    countries: number;
  };
  calibration: BandRate[];
  by_level: { label: string; n: number; materialised: number; rate: number }[];
  matrix: {
    probability: string;
    impact: number;
    n: number;
    materialised: number;
    rate: number | null;
  }[];
};

const fallback: Insights = {
  ...(bundled as unknown as Omit<Insights, "live">),
  live: false,
};

let current: Insights = fallback;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((listener) => listener());

/** Fetch the engine's figures once. Failure is not an error state: the bundled export
    is a truthful fallback, and the UI says which one it is showing. */
export async function hydrateInsights(): Promise<void> {
  if (mock) return;
  try {
    const live = await api<Omit<Insights, "live">>("/insights");
    if (!live?.calibration?.length) return;
    current = { ...live, live: true };
    emit();
  } catch {
    /* keep the bundled figures */
  }
}

export function useInsights(): Insights {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => current,
    () => current,
  );
}

export const insights = () => current;
export const totals = () => current.totals;
export const bands = () => current.calibration;

/** Reported only where enough risks have resolved to mean anything. */
const MIN_RESOLVED = 10;

/**
 * How often risks in a stated probability band went on to materialise.
 * Null when the band is unknown or rests on too few resolved risks.
 */
export function bandRate(label: string | null | undefined): BandRate | null {
  if (!label) return null;
  const band = current.calibration.find((b) => b.label === label);
  return band && band.n >= MIN_RESOLVED ? band : null;
}

/** The band midpoint the five-point scale implies, which is not the observed rate. */
export function bandMidpoint(label: string | null | undefined): number | null {
  return current.calibration.find((b) => b.label === label)?.expected ?? null;
}

/** What the Risk List already records against a crisis, by its ACAPS crisis_id.
    Only the bundled export carries this; the engine does not serve it yet. */
export function crisisHistory(
  id: string | null | undefined,
): CrisisHistory | null {
  if (!id) return null;
  const byCrisis = (bundled as unknown as { by_crisis?: Record<string, CrisisHistory> })
    .by_crisis;
  const record = byCrisis?.[id];
  return record && record.risks > 0 ? record : null;
}

export const asPercent = (value: number) => `${Math.round(value * 100)}%`;
