// The live demo panel: five fixed answers plus three seats taken by people in the room.
//
// Why this is a separate module from demo-data. The Chad case is a recorded walk-through: its
// result is a fixture, and loading it is a button press. This panel has to aggregate answers
// that do not exist until someone in the audience submits one, so the result is computed here
// from whatever the eight seats actually hold. Everything else about the demo is unchanged.
import panel from "./data/live-panel.json";

export type LiveSeat = (typeof panel.seats)[number];
export type LiveDirectoryExpert = (typeof panel.directory)[number];
export type LiveProbe = {
  id: string;
  kind: "choice" | "text";
  question: string;
  help?: string;
  limit?: number;
  role?: string;
  options?: { value: string; label: string; dk?: boolean }[];
};

export const livePanel = panel;
export const liveRiskId = panel.risk_id;
export const liveSeats: LiveSeat[] = panel.seats;
export const liveDirectory: LiveDirectoryExpert[] = panel.directory;
/** Two, and the card asks both. The engine's own cap is the same; see probes.card_flow. */
export const liveProbes = panel.questions as LiveProbe[];
export const liveQuestion = panel.question;
export function seatProfile(token: string): LiveSeat | null {
  return liveSeats.find((seat) => seat.token === token) || null;
}
export function isLiveSeatToken(token: string) {
  return !!seatProfile(token);
}

export type PanelResult = {
  n: number;
  n_estimates: number;
  mean: number;
  spread: { min: number; max: number; iqr: number };
  distribution: { bucket: string; count: number }[];
};
const buckets = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"];
function quartile(sorted: number[], q: number) {
  if (!sorted.length) return 0;
  const at = (sorted.length - 1) * q;
  const low = Math.floor(at);
  const high = Math.ceil(at);
  return sorted[low] + (sorted[high] - sorted[low]) * (at - low);
}
/**
 * The group result over every estimate the panel holds.
 *
 * Plain arithmetic over all eight: the five fixed answers and the three from the room count
 * the same, so the people who scanned a code can see their own answer move the number. An
 * abstention is counted in `n` and left out of the mean, which is what the engine does too.
 */
export function buildPanelResult(values: number[], n: number): PanelResult {
  const estimates = values.filter((value) => Number.isFinite(value));
  const sorted = [...estimates].sort((a, b) => a - b);
  const mean = estimates.length
    ? estimates.reduce((sum, value) => sum + value, 0) / estimates.length
    : 0;
  return {
    n,
    n_estimates: estimates.length,
    mean,
    spread: {
      min: sorted[0] ?? 0,
      max: sorted[sorted.length - 1] ?? 0,
      iqr: quartile(sorted, 0.75) - quartile(sorted, 0.25),
    },
    distribution: buckets.map((bucket) => {
      const [from, to] = bucket.split("-").map(Number);
      return {
        bucket,
        // The top bucket is closed at 1.0; every other one takes its lower bound only, so a
        // value on a boundary is counted once.
        count: estimates.filter(
          (value) => value >= from && (to === 1 ? value <= to : value < to),
        ).length,
      };
    }),
  };
}
/**
 * The midpoint of each likelihood word.
 *
 * An expert who picks "Likely" has not given a number, and the mean has to use something. The
 * midpoint of the band is an assumption, which is why the result says so rather than hiding it.
 */
export const wordMidpoint: Record<string, number> = {
  very_unlikely: 0.05,
  unlikely: 0.225,
  even: 0.5,
  likely: 0.775,
  very_likely: 0.95,
};
export function estimateFrom(probability: number | null, word?: string | null) {
  if (probability !== null && Number.isFinite(probability)) return probability;
  return word && word in wordMidpoint ? wordMidpoint[word] : null;
}
const bands: [number, string][] = [
  [0.8, "Very High"],
  [0.6, "High"],
  [0.4, "Medium"],
  [0.2, "Low"],
];
/** The band this mean proposes, so the decision step has something to accept or change. */
export function bandFor(mean: number) {
  return bands.find(([floor]) => mean >= floor)?.[1] || "Very Low";
}
