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
  baseline?: number | null;
  z?: number | null;
  note?: string;
};
export function evidenceSummary(e: EvidenceRecord) {
  if (typeof e.before === "number" && typeof e.after === "number")
    return `${e.source}: ${e.before} → ${e.after}${typeof e.delta === "number" ? ` (${e.delta >= 0 ? "+" : ""}${e.delta})` : ""}`;
  if (typeof e.value === "number" && typeof e.baseline === "number")
    return `${e.source}: ${e.value.toLocaleString("en-GB")} versus ${e.baseline.toLocaleString("en-GB")} baseline`;
  return e.source;
}
export function EvidenceLine({ value: e }: { value: EvidenceRecord }) {
  const severity =
    e.metric === "index" &&
    typeof e.before === "number" &&
    typeof e.after === "number";
  return (
    <div className="edition-evidence">
      {severity ? (
        <>
          <h3>
            Recorded crisis severity{" "}
            {e.after! > e.before!
              ? "rose"
              : e.after! < e.before!
                ? "fell"
                : "was unchanged"}
          </h3>
          <SeverityVisual
            before={e.before!}
            after={e.after!}
            from={e.month_from}
            to={e.month_to}
          />
          <p>
            {e.after !== e.before
              ? "This change prompted the expert review. "
              : "Published context for the expert review. "}
            These monthly readings stay fixed as replies arrive.
          </p>
          <small>
            Severity describes crisis conditions, on a scale of 0–10. Expert
            forecasts open after reveal.
          </small>
        </>
      ) : (
        <>
          <a href={safeUrl(e.url)} target="_blank" rel="noreferrer">
            {e.source}
          </a>
          <p>{evidenceSummary(e).slice(e.source.length + 2)}</p>
        </>
      )}
      {severity && (
        <details className="evidence-source">
          <summary>Source and comparison</summary>
          <a href={safeUrl(e.url)} target="_blank" rel="noreferrer">
            {e.source}
          </a>
          {typeof e.rank_this_month === "number" && (
            <p>
              Change ranked {e.rank_this_month} among {e.n_crises_this_month}{" "}
              crises in this comparison.
            </p>
          )}
        </details>
      )}
      {!severity && e.month_from && e.month_to && (
        <small>
          {e.month_from} → {e.month_to}
          {e.metric === "index"
            ? " · Severity index (0–10), not forecast probability"
            : ""}
        </small>
      )}
      {!severity && typeof e.rank_this_month === "number" && (
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
