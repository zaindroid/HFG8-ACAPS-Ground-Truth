import { useEffect, useMemo, useState } from "react";
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
import countries from "world-atlas/countries-110m.json";
import type { FeatureCollection, Geometry } from "geojson";
import { sampleDataEnabled, sampleRisks } from "./demo-data";
import { mock } from "./api";
import { endpoint, type Risk } from "./service";
import { Frame, Section } from "./LiveWorkspace";
import { date } from "./desk-model";
import type { RadarStatus } from "./v2-types";
import { EditionHistory } from "./EditionHistory";

const world = feature(
  countries as unknown as Topology<{ countries: GeometryCollection }>,
  (countries as unknown as Topology<{ countries: GeometryCollection }>).objects
    .countries,
) as FeatureCollection<Geometry, { name: string }>;
const path = geoPath(
  geoNaturalEarth1().fitExtent(
    [
      [16, 8],
      [944, 430],
    ],
    world,
  ),
);
function normalise(name: string) {
  const names: Record<string, string> = {
    "democratic republic of the congo": "dem. rep. congo",
    "republic of the congo": "congo",
    "south sudan": "s. sudan",
    "central african republic": "central african rep.",
    "united states": "united states of america",
  };
  return names[name.toLowerCase()] || name.toLowerCase();
}
export function Radar() {
  const [risks, setRisks] = useState<Risk[]>([]),
    [status, setStatus] = useState<RadarStatus | null>(null),
    [query, setQuery] = useState(""),
    [level, setLevel] = useState("all"),
    [country, setCountry] = useState(""),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const jobs = mock
      ? Promise.all([
          import("../../fixtures/GET_risks.json").then((m) =>
            sampleDataEnabled()
              ? { ...m.default, risks: sampleRisks }
              : m.default,
          ),
          import("../../fixtures/GET_radar_status.json").then((m) => m.default),
        ])
      : Promise.all([endpoint.risks(), endpoint.radar()]);
    jobs
      .then(([list, meta]) => {
        if (active) {
          setRisks(list.risks);
          setStatus(meta as RadarStatus);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reload]);
  const visible = useMemo(
    () =>
      risks.filter(
        (r) =>
          (level === "all" || r.level === level) &&
          (!country || r.country === country) &&
          `${r.title} ${r.country} ${r.risk_id}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [risks, level, country, query],
  );
  const riskList =
    status?.risk_list ||
    (status?.source
      ? {
          source: status.source,
          n: status.n_risks || 0,
          fetched_at: status.fetched_at || "",
        }
      : null);
  const byCountry = new Map<string, Risk[]>();
  for (const risk of risks) {
    const key = normalise(risk.country);
    byCountry.set(key, [...(byCountry.get(key) || []), risk]);
  }
  return (
    <Frame
      title="Risk Radar"
      subtitle="Follow the Risk List. Invite independent expert validation."
    >
      <div className="radar-source">
        <span className="source-badge">
          Source:{" "}
          {riskList?.source === "acaps-api" || riskList?.source === "api"
            ? "ACAPS API"
            : riskList?.source === "csv"
              ? "CSV fallback"
              : "Awaiting source"}
        </span>
        {status && (
          <span>
            {risks.length} risks loaded · source dataset{" "}
            {riskList?.n ?? "Unknown"}
            <br />
            <small>
              Fetched{" "}
              {riskList?.fetched_at
                ? date(riskList.fetched_at)
                : "Not supplied"}
            </small>
          </span>
        )}
        <button disabled={loading} onClick={() => setReload((v) => v + 1)}>
          Refresh Radar
        </button>
      </div>
      {!!status?.editions?.length && (
        <div className="edition-sources">
          {status.editions.map((e) => (
            <span key={`${e.dataset}-${e.month}`}>
              {e.dataset === "inform-severity-index"
                ? "INFORM Severity"
                : "Humanitarian access"}{" "}
              · {e.month} · {e.source === "api" ? "API" : "Cached edition"}
            </span>
          ))}
        </div>
      )}
      <EditionHistory />
      {loading && <p role="status">Loading Risk Radar…</p>}
      {error && (
        <p className="error-box" role="alert">
          {error} Use Refresh Radar to retry. No local fixture fallback is used
          in API mode.
        </p>
      )}
      <Section title="Countries with active risks">
        <svg
          className="world-map"
          viewBox="0 0 960 456"
          role="group"
          aria-label="World map. Countries with loaded risks can be selected to filter the list."
        >
          {world.features.map((f) => {
            const matches = byCountry.get(normalise(f.properties.name)) || [];
            const name = matches[0]?.country;
            return (
              <path
                key={f.id || f.properties.name}
                d={path(f) || ""}
                className={
                  name === country
                    ? "map-country selected"
                    : matches.length
                      ? "map-country active"
                      : "map-country"
                }
                {...(name
                  ? {
                      tabIndex: 0,
                      role: "button",
                      "aria-label": `${name}, ${matches.length} risks`,
                      "aria-pressed": name === country,
                      onClick: () =>
                        setCountry((v) => (v === name ? "" : name)),
                      onKeyDown: (e: React.KeyboardEvent) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setCountry((v) => (v === name ? "" : name));
                        }
                      },
                    }
                  : {})}
              >
                <title>
                  {f.properties.name}
                  {matches.length ? `: ${matches.length} loaded risks` : ""}
                </title>
              </path>
            );
          })}
          <text x="16" y="450">
            Highlighted countries have loaded risk cards. Select a country to
            filter.
          </text>
        </svg>
        <p className="panel-caption">
          Country boundaries: Natural Earth via world-atlas. This map is a
          locator, not an endorsement of boundaries or status. Risk ratings are
          not crisis severity ratings.
        </p>
      </Section>
      <Section title="Risk List">
        <div className="radar-filters">
          <div>
            <label htmlFor="risk-search">Search risks</label>
            <input
              id="risk-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Country, title or risk ID"
            />
          </div>
          <div>
            <label htmlFor="risk-level">Risk level</label>
            <select
              id="risk-level"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
            >
              <option value="all">All levels</option>
              {["High", "Medium", "Low"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="country-filter">Country</label>
            <select
              id="country-filter"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            >
              <option value="">All countries</option>
              {Array.from(new Set(risks.map((r) => r.country)))
                .sort()
                .map((v) => (
                  <option key={v}>{v}</option>
                ))}
            </select>
          </div>
          <button
            onClick={() => {
              setQuery("");
              setLevel("all");
              setCountry("");
            }}
          >
            Clear filters
          </button>
        </div>
        <p className="panel-caption" role="status">
          {visible.length} matching risk{visible.length === 1 ? "" : "s"}
        </p>
        {visible.length ? (
          <div className="table-wrap">
            <table className="radar-table">
              <thead>
                <tr>
                  <th>Country / ID</th>
                  <th>Risk</th>
                  <th>Probability</th>
                  <th>Level</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((r) => (
                  <tr key={r.risk_id}>
                    <td>
                      {r.country}
                      <small>{r.risk_id}</small>
                    </td>
                    <td>{r.title}</td>
                    <td>{r.probability_acaps}</td>
                    <td>
                      <span className="rating">{r.level}</span>
                    </td>
                    <td>
                      <a
                        href={
                          mock && sampleDataEnabled() && r.risk_id !== "R1043"
                            ? `/ledger?risk_id=${encodeURIComponent(r.risk_id)}`
                            : `/desk?risk_id=${encodeURIComponent(r.risk_id)}`
                        }
                      >
                        {mock && sampleDataEnabled() && r.risk_id !== "R1043"
                          ? "View ledger history"
                          : "Review risk"}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          !loading && (
            <p>
              No risks match these filters. Clear filters to see the loaded
              list.
            </p>
          )
        )}
      </Section>
      <div className="radar-next">
        <a href="/apply">Apply as a synthetic expert</a>
        <a href="/committee">Committee review</a>
      </div>
      <details className="about-platform">
        <summary>About this validation layer</summary>
        <p>{platformDescription}</p>
      </details>
    </Frame>
  );
}
const platformDescription =
  "Sealed Signals is the Risk Radar platform ACAPS does not have: the live Risk List from the ACAPS API, with an expert loop, descriptive integrity notes and a public audit trail on top. An ACAPS analyst (or, in phase 2, an indicator doorbell) sends a one-minute question to the eight best-matched vetted experts. Experts answer on their phone behind a mask they choose, with ACAPS's rating hidden until after submission. Answers are committed with a timestamp, opened together, summarised as an equal-weight mean with spread and minority reasons, annotated with integrity notes the analyst reads, turned into a cited draft the analyst accepts, edits or rejects, and published as a group view on a ledger with an honesty box that states what fed into it, its limits and its misses. When the risk resolves, forecasts are scored committee-side and every panel member gets the group outcome report. Nothing publishes itself.";
