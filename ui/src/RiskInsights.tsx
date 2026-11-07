import { useState } from "react";
import { Section } from "./LiveWorkspace";
import insights from "./data/risk-insights.json";

type Band = {
  label: string;
  n: number;
  materialised: number;
  rate: number;
  expected: number;
};
type Cell = {
  probability: string;
  impact: number;
  n: number;
  materialised: number;
  rate: number | null;
};

const bands = insights.calibration as Band[];
const matrix = insights.matrix as Cell[];
const totals = insights.totals;
const impacts = [1, 2, 3, 4, 5];
const probabilities = ["Very High", "High", "Medium", "Low", "Very Low"];
const pct = (value: number) => `${Math.round(value * 100)}%`;

// Chart geometry. Bands are ordinal, so they are evenly spaced rather than plotted on a scale.
const W = 560;
const H = 250;
const TOP = 28;
const FLOOR = 176;
const LEFT = 44;
const STEP = (W - LEFT - 24) / bands.length;
const x = (index: number) => LEFT + STEP * (index + 0.5);
const y = (rate: number) => FLOOR - rate * (FLOOR - TOP);

function Calibration() {
  return (
    <Section title="Has the rating matched what happened?">
      <p className="insights-lede">
        Each of ACAPS's five probability bands, set against how often those
        risks went on to materialise. Based on the {totals.resolved} risks in
        the Risk List that have resolved.
      </p>
      {/* Scrolls at narrow widths, so it must be reachable by keyboard. */}
      <div
        className="chart-scroll"
        tabIndex={0}
        role="group"
        aria-label="Calibration chart, scrolls sideways on small screens"
      >
          <svg
            className="calibration-chart"
            viewBox={`0 0 ${W} ${H}`}
            role="img"
            aria-label={`Observed materialisation by stated probability band. ${bands
              .map((b) => `${b.label}: ${pct(b.rate)} of ${b.n} risks`)
              .join(". ")}.`}
          >
          {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
            <g key={tick}>
              <line
                x1={LEFT}
                x2={W - 16}
                y1={y(tick)}
                y2={y(tick)}
                className="chart-grid"
              />
              <text x={LEFT - 8} y={y(tick) + 4} textAnchor="end">
                {pct(tick)}
              </text>
            </g>
          ))}
          <line
            x1={LEFT}
            x2={W - 16}
            y1={FLOOR}
            y2={FLOOR}
            className="chart-axis"
          />

          {/* Reference: where each band would land if its midpoint were exact. */}
          <polyline
            className="acaps-line"
            fill="none"
            points={bands.map((b, i) => `${x(i)},${y(b.expected)}`).join(" ")}
          />

          {bands.map((band, index) => (
            <g key={band.label}>
              <title>
                {band.label}: {band.materialised} of {band.n} resolved risks
                materialised ({pct(band.rate)}). Band midpoint{" "}
                {pct(band.expected)}.
              </title>
              <line
                x1={x(index)}
                x2={x(index)}
                y1={y(band.expected)}
                y2={y(band.rate)}
                className="gap-line"
              />
              <circle
                cx={x(index)}
                cy={y(band.expected)}
                r="5"
                className="expected-dot"
              />
              <circle
                cx={x(index)}
                cy={y(band.rate)}
                r="7"
                className="observed-dot"
              />
              {/* Keep the value clear of the reference line: below the dot when the
                  band over-stated the risk, above it when it under-stated. */}
              <text
                x={x(index)}
                y={
                  band.rate >= band.expected
                    ? y(band.rate) - 14
                    : y(band.rate) + 22
                }
                textAnchor="middle"
                className="observed-value"
              >
                {pct(band.rate)}
              </text>
              <text
                x={x(index)}
                y={FLOOR + 20}
                textAnchor="middle"
                className="band-name"
              >
                {band.label}
              </text>
              <text x={x(index)} y={FLOOR + 36} textAnchor="middle">
                {band.n} risks
              </text>
            </g>
          ))}
        </svg>
      </div>
      <ul className="calibration-legend">
        <li>
          <svg width="16" height="16" aria-hidden="true">
            <circle cx="8" cy="8" r="7" className="observed-dot" />
          </svg>
          Share that materialised
        </li>
        <li>
          <svg width="26" height="16" aria-hidden="true">
            <line x1="0" y1="8" x2="26" y2="8" className="acaps-line" />
            <circle cx="13" cy="8" r="5" className="expected-dot" />
          </svg>
          If the band midpoint were exact
        </li>
      </ul>
      <p className="panel-caption">
        The two highest bands land close to their midpoints, so a High rating
        already carries real information. Medium is the exception: it resolves
        at {pct(bands[2].rate)} rather than {pct(bands[2].expected)}, and it
        holds {bands[2].n} of the {totals.resolved} resolved risks — the largest
        group, and the one where an independent view is worth most. Very Low
        rests on {bands[0].n} risks, too few to read.
      </p>
    </Section>
  );
}

function Matrix() {
  const populated = matrix.filter((cell) => cell.n > 0);
  const step = (rate: number | null) =>
    rate === null ? "empty" : `r${Math.min(5, Math.floor(rate * 5) + 1)}`;
  return (
    <Section title="Where the resolved risks sit">
      <p className="insights-lede">
        ACAPS's own grid: stated probability against expected impact. The number
        is how many resolved risks fall in that cell, the shade how many of them
        materialised.
      </p>
      <div className="matrix">
        <span />
        {impacts.map((impact) => (
          <span className="matrix-head" key={impact}>
            <span className="head-word">Impact&nbsp;</span>
            {impact}
          </span>
        ))}
        {probabilities.map((probability) => (
          <Row key={probability} probability={probability} step={step} />
        ))}
      </div>
      <div className="matrix-scale">
        <span className="scale-label">
          Share that materialised — lighter is lower, darker is higher
        </span>
        <span className="steps" aria-hidden="true">
          {[1, 2, 3, 4, 5].map((n) => (
            <span key={n} style={{ background: `var(--seq-${n})` }} />
          ))}
        </span>
        <span className="scale-ends" aria-hidden="true">
          <span>0%</span>
          <span>100%</span>
        </span>
      </div>
      <p className="panel-caption">
        {populated.length} of 25 cells hold any resolved risk, so the grid is
        thinner than it looks. The densest cell is Medium probability with
        impact 3. Empty cells are left blank rather than shaded, because no
        outcome has been observed there.
      </p>
    </Section>
  );
}

function Row({
  probability,
  step,
}: {
  probability: string;
  step: (rate: number | null) => string;
}) {
  return (
    <>
      <span className="matrix-side">{probability}</span>
      {impacts.map((impact) => {
        const cell = matrix.find(
          (c) => c.probability === probability && c.impact === impact,
        );
        const empty = !cell || cell.n === 0;
        return (
          <div
            key={impact}
            className={`matrix-cell ${empty ? "empty" : step(cell!.rate)}`}
            title={
              empty
                ? `${probability}, impact ${impact}: no resolved risks`
                : `${probability}, impact ${impact}: ${cell!.materialised} of ${cell!.n} materialised`
            }
          >
            {empty ? (
              <span aria-label="no resolved risks">–</span>
            ) : (
              <>
                <strong>{cell!.n}</strong>
                <span>{pct(cell!.rate as number)}</span>
              </>
            )}
          </div>
        );
      })}
    </>
  );
}

export function RiskInsights() {
  const [tableOpen, setTableOpen] = useState(false);
  return (
    <div className="insights">
      <div className="stat-row">
        <div>
          <span>Risks in the list</span>
          <strong>{totals.risks}</strong>
        </div>
        <div>
          <span>Resolved outcomes</span>
          <strong>{totals.resolved}</strong>
        </div>
        <div>
          <span>Countries covered</span>
          <strong>{totals.countries}</strong>
        </div>
      </div>
      <Calibration />
      <Matrix />
      {/* Rows are mounted only while open: a closed <details> still keeps its
          rows in the DOM, which would join the page's other tables. */}
      <details
        className="insights-table"
        onToggle={(event) => setTableOpen(event.currentTarget.open)}
      >
        <summary>Show these figures as a table</summary>
        {tableOpen && (
          <div className="table-wrap">
          <table>
            <caption className="panel-caption">
              Resolved risks by stated probability band.
            </caption>
            <thead>
              <tr>
                <th>Probability band</th>
                <th>Resolved risks</th>
                <th>Materialised</th>
                <th>Share</th>
                <th>Band midpoint</th>
              </tr>
            </thead>
            <tbody>
              {bands.map((band) => (
                <tr key={band.label}>
                  <td>{band.label}</td>
                  <td>{band.n}</td>
                  <td>{band.materialised}</td>
                  <td>{pct(band.rate)}</td>
                  <td>{pct(band.expected)}</td>
                </tr>
              ))}
              </tbody>
            </table>
          </div>
        )}
      </details>
      <p className="panel-caption">
        Source: {insights.source}, fetched into{" "}
        <code>data/acaps-risk-list.csv</code>. Figures cover resolved risks
        only; {totals.active} are still active and are not counted.
      </p>
    </div>
  );
}
