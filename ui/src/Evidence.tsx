import { safeUrl } from "./service";
export type EvidenceRecord = {
  source: string;
  url: string;
  dataset?: string;
  crisis_id?: string;
  metric?: string;
  month_from?: string;
  month_to?: string;
  before?: number;
  after?: number;
  delta?: number;
  rank_this_month?: number;
  n_crises_this_month?: number;
  indicator?: string;
  value?: number;
  // Null, not absent: a trigger completion rate is one published percentage with no baseline, and
  // the engine says so rather than writing a zero that renders as "40 versus 0 baseline".
  baseline?: number | null;
  z?: number | null;
};
export function evidenceSummary(e: EvidenceRecord) {
  if (typeof e.before === "number" && typeof e.after === "number")
    return `${e.source}: ${e.before} → ${e.after}${typeof e.delta === "number" ? ` (${e.delta >= 0 ? "+" : ""}${e.delta})` : ""}`;
  if (typeof e.value === "number" && typeof e.baseline === "number")
    return `${e.source}: ${e.value.toLocaleString("en-GB")} versus ${e.baseline.toLocaleString("en-GB")} baseline`;
  return e.source;
}
export function EvidenceLine({ value: e }: { value: EvidenceRecord }) {
  return (
    <div className="edition-evidence">
      <a href={safeUrl(e.url)} target="_blank" rel="noreferrer">
        {e.source}
      </a>
      <p>{evidenceSummary(e).slice(e.source.length + 2)}</p>
      {e.month_from && e.month_to && (
        <small>
          {e.month_from} → {e.month_to}
          {e.metric === "index"
            ? " · Severity index (0–10), not forecast probability"
            : ""}
        </small>
      )}
      {typeof e.rank_this_month === "number" && (
        <small>
          Change rank {e.rank_this_month} of {e.n_crises_this_month} crises
        </small>
      )}
    </div>
  );
}
