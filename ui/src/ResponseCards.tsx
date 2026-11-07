import { Inbox, LockKeyhole } from "lucide-react";
import type { Result } from "./service";
import type { CSSProperties } from "react";
function band(bucket: string) {
  const values = bucket.split("-").map(Number);
  return values.length === 2 && values.every(Number.isFinite)
    ? `${Math.round(values[0] * 100)}–${Math.round(values[1] * 100)}%`
    : bucket;
}
export function ResponseCards({
  total,
  count,
  revealed,
  result,
}: {
  total: number;
  count: number;
  revealed: boolean;
  result: Result;
}) {
  const bands = result.distribution.flatMap((row) =>
    Array.from({ length: row.count }, () => band(row.bucket)),
  );
  return (
    <>
      <div
        className="envelope-tray response-cards"
        role="group"
        aria-label={
          revealed
            ? `${total} revealed responses grouped by forecast band`
            : `${count} sealed synthetic answers`
        }
      >
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            className={`response-card ${i < count ? "filled" : ""} ${revealed ? "revealed" : ""}`}
            style={{ "--flip-delay": `${i * 55}ms` } as CSSProperties}
          >
            <div className="response-card-inner">
              <div className="response-card-front" aria-hidden={revealed}>
                {i < count ? (
                  <LockKeyhole size={21} aria-hidden="true" />
                ) : (
                  <Inbox size={21} aria-hidden="true" />
                )}
                <span>{i < count ? "Sealed" : "Waiting"}</span>
              </div>
              <div className="response-card-back" aria-hidden={!revealed}>
                <strong>{bands[i] || "No estimate"}</strong>
                <span>{bands[i] ? "Forecast band" : "Response recorded"}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      {revealed && (
        <p className="response-reveal-caption">
          Grouped forecast bands are now visible. These cards are not linked to
          expert identities.
        </p>
      )}
    </>
  );
}
