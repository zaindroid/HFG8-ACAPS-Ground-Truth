import { safeUrl } from "./service";
import { SeverityVisual } from "./SeverityVisual";
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
  baseline?: number;
  z?: number;
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
      {e.metric === "index" &&
      typeof e.before === "number" &&
      typeof e.after === "number" ? (
        <>
          <h3>
            The crisis severity index{" "}
            {e.after > e.before
              ? "increased"
              : e.after < e.before
                ? "decreased"
                : "stayed the same"}
          </h3>
          <SeverityVisual
            before={e.before}
            after={e.after}
            from={e.month_from}
            to={e.month_to}
          />
          <p>
            Why it matters: this change triggered a review by the expert panel.
          </p>
        </>
      ) : (
        <p>{evidenceSummary(e).slice(e.source.length + 2)}</p>
      )}
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
          {e.rank_this_month === 1
            ? "Largest recorded change"
            : `Change ranked ${e.rank_this_month}`}{" "}
          among {e.n_crises_this_month} crises in this comparison
        </small>
      )}
    </div>
  );
}
