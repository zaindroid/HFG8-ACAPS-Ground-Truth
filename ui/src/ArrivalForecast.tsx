import result from "../../fixtures/GET_pulses_result.json";

// An illustrative arrival order, never sent to the API or linked to roster identities. The shape
// below is the order answers come in; the values are fitted to the round it illustrates, so its
// final mean and range are the round's own. They used to be typed in, and the comment claiming
// they matched the group result stopped being true the moment the engine's mean moved.
const shape = [0.73, 0.9, 0.58, 0.78, 0.3, 0.56, 0.79, 0.88];
export const arrivalEstimates = (() => {
  const low = Math.min(...shape);
  const high = Math.max(...shape);
  // Map the shape onto the round's spread, then shift it so the mean lands on the round's mean.
  const stretched = shape.map(
    (value) =>
      result.spread.min +
      ((value - low) / (high - low)) * (result.spread.max - result.spread.min),
  );
  const drift =
    result.mean - stretched.reduce((sum, v) => sum + v, 0) / stretched.length;
  return stretched.map(
    (value) => Math.round(Math.min(1, Math.max(0, value + drift)) * 100) / 100,
  );
})();

export function ArrivalForecast({
  count,
  reference,
}: {
  count: number;
  reference: string;
}) {
  const referencePosition = (
    {
      "Very Low": 0.1,
      Low: 0.3,
      Medium: 0.5,
      High: 0.7,
      "Very High": 0.9,
    } as Record<string, number>
  )[reference];
  const received = arrivalEstimates.slice(0, Math.max(0, count));
  const mean = received.length
    ? received.reduce((sum, value) => sum + value, 0) / received.length
    : null;
  return (
    <section
      id="arrival-forecast"
      className="workspace-panel arrival-forecast"
      aria-label="Simulation forecast"
    >
      <div className="panel-heading">
        <h2>Panel forecast vs ACAPS</h2>
        <span>{received.length} estimates received</span>
      </div>
      <div className="arrival-comparison-values">
        <div className="arrival-forecast-value">
          <strong>{mean === null ? "—" : `${Math.round(mean * 100)}%`}</strong>
          <span>
            {mean === null
              ? "Waiting for the first estimate"
              : "Running mean of simulated estimates"}
          </span>
        </div>
        <div className="arrival-acaps-reference">
          <span>ACAPS forecast</span>
          <strong>{reference}</strong>
          <small>Fixed assessment</small>
        </div>
      </div>
      <svg
        viewBox="0 0 500 100"
        role="img"
        aria-label={
          mean === null
            ? `No panel forecast yet. ACAPS probability band ${reference}.`
            : `Running simulation forecast ${Math.round(mean * 100)} percent. ACAPS probability band ${reference}.`
        }
      >
        <line x1="30" x2="470" y1="48" y2="48" className="chart-axis" />
        {referencePosition !== undefined && (
          <g className="arrival-reference-marker">
            <line
              x1={30 + referencePosition * 440}
              x2={30 + referencePosition * 440}
              y1="20"
              y2="56"
              stroke="#8b703b"
              strokeDasharray="4 4"
            />
            <text x={30 + referencePosition * 440} y="13" textAnchor="middle">
              ACAPS {reference}
            </text>
          </g>
        )}
        {[0, 25, 50, 75, 100].map((value) => (
          <g key={value}>
            <line
              x1={30 + value * 4.4}
              x2={30 + value * 4.4}
              y1="43"
              y2="53"
              className="chart-axis"
            />
            <text x={30 + value * 4.4} y="84" textAnchor="middle">
              {value}%
            </text>
          </g>
        ))}
        {received.map((value, i) => (
          <circle
            key={i}
            cx={30 + value * 440}
            cy="48"
            r="4"
            className="arrival-estimate-dot"
          />
        ))}
        {mean !== null && (
          <g
            className="arrival-mean-marker"
            style={{ transform: `translate(${30 + mean * 440}px, 28px)` }}
          >
            <line y1="0" y2="20" stroke="var(--accent)" />
            <circle r="8" fill="var(--accent)" />
            <title>Running mean: {Math.round(mean * 100)}%</title>
          </g>
        )}
      </svg>
      <p>
        {received.length
          ? `Latest estimate: ${Math.round(received.at(-1)! * 100)}%. Each reply can move the group forecast up or down.`
          : "Start the simulation to watch the forecast take shape."}
      </p>
      <small>
        ACAPS band position is illustrative, not an official percentage. The
        saved group result opens on reveal.
      </small>
    </section>
  );
}
