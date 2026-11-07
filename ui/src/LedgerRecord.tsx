import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import type { LedgerEntry } from "./service";
export function LedgerColumns() {
  return (
    <>
      <p className="ledger-reading-guide">
        <strong>Outcome:</strong> did the forecast event happen?{" "}
        <strong>Receipt check:</strong> does the record match its receipt? Open
        a row to check.
      </p>
      <div className="ledger-columns" aria-hidden="true">
        <span>Record</span>
        <span>Panel</span>
        <span className="ledger-col-acaps">ACAPS</span>
        <span>Outcome</span>
        <span className="ledger-col-count">Answers</span>
        <span className="ledger-col-check">Receipt check</span>
        <span />
      </div>
    </>
  );
}
export function LedgerRecord({
  entry,
  country,
  checked,
  children,
}: {
  entry: LedgerEntry;
  country?: string;
  checked?: boolean;
  children: ReactNode;
}) {
  const outcome = entry.outcome?.replaceAll("_", " ") || "Unresolved";
  return (
    <details className="ledger-record" name="ledger-records">
      <summary>
        <span className="ledger-row-identity">
          <strong>{entry.risk_id}</strong>
          <span>{country || entry.pulse_id}</span>
        </span>
        <strong className="ledger-row-probability">
          {Math.round(entry.group_probability * 100)}%
        </strong>
        <span className="ledger-col-acaps">{entry.acaps_probability}</span>
        <span className="ledger-row-outcome">{outcome}</span>
        <span className="ledger-col-count">
          {entry.n ?? entry.honesty?.n ?? "—"}
        </span>
        <span className="ledger-col-check">
          {checked === true
            ? "Receipt matched"
            : checked === false
              ? "Receipt mismatch"
              : "Open to check"}
        </span>
        <ChevronDown size={17} aria-hidden="true" />
      </summary>
      <div className="ledger-record-detail">{children}</div>
    </details>
  );
}
