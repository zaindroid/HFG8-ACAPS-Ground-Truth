import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { mock } from "./api";
import { api } from "./service";

type DatasetEditions = { dataset: string; months: string[]; source?: string };
const names: Record<string, string> = {
  "inform-severity-index": "INFORM Severity",
  "humanitarian-access": "Humanitarian access",
};
const monthPattern = /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{4}$/;
const monthOrder = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];
const dateValue = (month: string) =>
  Number(month.slice(3)) * 12 + monthOrder.indexOf(month.slice(0, 3));
// These are complete dataset editions present in data/acaps-api/, not the longer crisis-only series.
const cached: DatasetEditions[] = [
  {
    dataset: "inform-severity-index",
    months: ["Mar2026", "Apr2026", "Oct2026", "Nov2026"],
    source: "cache",
  },
  { dataset: "humanitarian-access", months: ["Nov2026"], source: "cache" },
];
function parseEditions(value: unknown): DatasetEditions[] {
  if (!value || typeof value !== "object")
    throw new Error("The API did not return edition history.");
  const body = value as Record<string, unknown>;
  const rows = Array.isArray(body.editions)
    ? body.editions
    : Array.isArray(body.datasets)
      ? body.datasets
      : Object.entries(body)
          .filter(([key]) => key in names)
          .map(([dataset, months]) => ({ dataset, months }));
  if (
    !rows.length &&
    !Array.isArray(body.editions) &&
    !Array.isArray(body.datasets)
  )
    throw new Error("The API did not return months per dataset.");
  return rows.map((row: unknown) => {
    if (!row || typeof row !== "object")
      throw new Error("The edition history contains an unreadable dataset.");
    const item = row as Record<string, unknown>;
    if (
      typeof item.dataset !== "string" ||
      !Array.isArray(item.months) ||
      !item.months.every((m) => typeof m === "string" && monthPattern.test(m))
    )
      throw new Error("The edition history contains invalid dataset months.");
    return {
      dataset: item.dataset,
      months: [...new Set(item.months as string[])].sort(
        (a, b) => dateValue(b) - dateValue(a),
      ),
      source: typeof item.source === "string" ? item.source : undefined,
    };
  });
}
export function EditionHistory() {
  const [rows, setRows] = useState<DatasetEditions[] | null>(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState("");
  async function load() {
    setLoading(true);
    setError("");
    setRows(null);
    try {
      setRows(
        mock
          ? parseEditions({ editions: cached })
          : parseEditions(await api<unknown>("/radar/editions")),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <details
      className="edition-history"
      onToggle={(e) => {
        if (e.currentTarget.open && rows === null && !loading && !error)
          void load();
      }}
    >
      <summary>Edition history</summary>
      <div className="edition-history-body">
        <div className="edition-history-heading">
          <p>Available monthly datasets for the alert engine.</p>
          <button disabled={loading} onClick={() => void load()}>
            Refresh editions
          </button>
        </div>
        {loading && <p role="status">Loading editions…</p>}
        {error && (
          <p role="alert" className="error-box">
            {error}
          </p>
        )}
        {rows?.map((row) => (
          <section className="edition-history-row" key={row.dataset}>
            <div>
              <h2>{names[row.dataset] || row.dataset}</h2>
              <span>
                {row.months.length} editions
                {row.source
                  ? ` · ${row.source === "cache" ? "Cached" : row.source === "api" ? "API" : row.source}`
                  : ""}
              </span>
            </div>
            <div className="edition-months">
              {row.months.map((month) => (
                <a
                  key={month}
                  href={`https://api.acaps.org/api/v1/${encodeURIComponent(row.dataset)}/${month}/`}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`${names[row.dataset] || row.dataset} ${month} source edition`}
                >
                  {month}
                  <ArrowUpRight size={13} aria-hidden="true" />
                </a>
              ))}
            </div>
          </section>
        ))}
        {rows?.length === 0 && <p>No editions reported.</p>}
      </div>
    </details>
  );
}
