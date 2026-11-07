import { useEffect, useState } from "react";
import {
  MapPin,
  LockKeyhole,
  Check,
  ArrowRight,
  UsersRound,
} from "lucide-react";
import { mock } from "./api";
import { endpoint, type Result, type Draft, type Pulse } from "./service";
import type { Match } from "./v2-types";
import matched from "../../fixtures/GET_panels_match.json";
import { GroupChart } from "./LiveWorkspace";
import { DraftRecommendation, DraftNarrative } from "./Grounding";

const label = (name: string) =>
  name.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
function Bars({
  rows,
  total,
}: {
  rows: { label: string; count: number; max?: number }[];
  total: number;
}) {
  return (
    <div className="panel-bars">
      {rows.map((row) => (
        <div className="panel-bar-row" key={row.label}>
          <span>{label(row.label)}</span>
          <div className="panel-bar-track">
            <span
              style={{
                width: `${Math.min(100, (row.count / Math.max(1, row.max || total)) * 100)}%`,
              }}
            />
          </div>
          <strong>
            {row.count}
            {row.max ? ` / ${row.max}` : ""}
          </strong>
        </div>
      ))}
    </div>
  );
}

export function PanelVisuals({
  riskId,
  arrived,
}: {
  riskId: string;
  arrived?: number;
}) {
  const [panel, setPanel] = useState<Match | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setPanel(null);
    setError("");
    (mock ? Promise.resolve(matched as Match) : endpoint.match(riskId))
      .then((value) => {
        if (active) {
          if (value.risk_id !== riskId)
            throw new Error("Panel details belong to another risk.");
          setPanel(value);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [riskId]);
  if (error)
    return (
      <p role="alert" className="error-box">
        {error}
      </p>
    );
  if (!panel) return <p role="status">Loading panel expertise…</p>;
  const responding =
    arrived === undefined ? panel.experts : panel.experts.slice(0, arrived);
  const regions = [
    ...new Set(
      panel.experts.map(
        (e) => e.region || e.geo_tags.join(", ") || "Not supplied",
      ),
    ),
  ];
  const themes = [
    ...new Set([
      ...panel.experts.flatMap((e) => e.theme_tags),
      ...panel.composition.gaps,
    ]),
  ];
  const current = arrived
    ? panel.experts[Math.min(arrived, panel.experts.length) - 1]
    : null;
  return (
    <section
      className="panel-visuals"
      aria-label="Panel locations and expertise"
    >
      <div className="panel-visual-heading">
        <strong>
          <UsersRound size={17} aria-hidden="true" /> {panel.experts.length}{" "}
          selected experts
        </strong>
        <span>
          {regions.length} locations ·{" "}
          {panel.n_approved_available || panel.experts.length} in the network
        </span>
      </div>
      {arrived !== undefined && (
        <p className="arrival-location" role="status">
          {current ? (
            <>
              <LockKeyhole size={15} aria-hidden="true" />
              Response {arrived} sealed ·{" "}
              {current.region || current.geo_tags.join(", ")} ·{" "}
              {current.theme_tags.join(", ")}
            </>
          ) : (
            "Waiting for the first response"
          )}
        </p>
      )}
      <div className="panel-visual-grid">
        <div>
          <h3>Where the panel is based</h3>
          <div className="location-lanes">
            {regions.map((region) => {
              const experts = panel.experts
                .map((e, i) => ({ e, i }))
                .filter(
                  ({ e }) =>
                    (e.region || e.geo_tags.join(", ") || "Not supplied") ===
                    region,
                );
              return (
                <div key={region}>
                  <span>
                    <MapPin size={13} aria-hidden="true" />
                    {region}
                  </span>
                  <div>
                    {experts.map(({ e, i }) => (
                      <span
                        key={e.pseudonym}
                        className={
                          arrived === undefined || i < arrived
                            ? "location-dot received"
                            : "location-dot"
                        }
                        aria-label={`${e.pseudonym}: ${arrived === undefined ? "selected" : i < arrived ? "sealed" : "waiting"}`}
                      >
                        <span className="sr-only">{e.pseudonym}</span>
                      </span>
                    ))}
                  </div>
                  <small>
                    {
                      experts.filter(
                        ({ i }) => arrived === undefined || i < arrived,
                      ).length
                    }{" "}
                    / {experts.length}
                  </small>
                </div>
              );
            })}
          </div>
        </div>
        <div>
          <h3>
            {arrived === undefined
              ? "Expertise represented"
              : "Expertise received so far"}
          </h3>
          <Bars
            total={panel.experts.length}
            rows={themes.map((theme) => ({
              label: theme,
              count: responding.filter((e) => e.theme_tags.includes(theme))
                .length,
            }))}
          />
          <p className="panel-viz-note">One expert may cover several themes.</p>
        </div>
      </div>
      <div className="panel-coverage-finding">
        <strong>
          {panel.composition.gaps.length
            ? `Panel selection gap: ${panel.composition.gaps.map(label).join(", ")}`
            : "Selected panel covers the required expertise"}
        </strong>
        <span>{panel.composition.theme_cover.map(label).join(" · ")}</span>
      </div>
      <details className="panel-roster">
        <summary>See locations and expertise for each expert</summary>
        <div>
          {panel.experts.map((e, i) => (
            <article
              key={e.pseudonym}
              className={arrived !== undefined && i >= arrived ? "waiting" : ""}
            >
              <span className="roster-initial">
                {e.pseudonym.slice(0, 1).toUpperCase()}
              </span>
              <div>
                <strong>{e.pseudonym}</strong>
                <span>{e.region || e.geo_tags.join(", ")}</span>
                <small>{e.theme_tags.map(label).join(" · ")}</small>
              </div>
              <small>
                {arrived === undefined
                  ? "Selected"
                  : i < arrived
                    ? "Sealed"
                    : "Waiting"}
              </small>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}

export function AnalysisWalkthrough({
  result,
  draft,
  pulse,
  reference,
}: {
  result: Result;
  draft: Draft;
  pulse: Pulse;
  reference: string;
}) {
  const [step, setStep] = useState(0);
  const steps = [
    "Read the spread",
    "Check coverage",
    "Review evidence",
    "Prepare the draft",
  ];
  const regions = result.agreement_by_region.filter(
    (r) => r.n >= 3 && r.mean !== null,
  );
  const checked = result.missing_themes.filter(
    (t) => t.corroboration === "corroborated",
  ).length;
  const pending = result.missing_themes.length - checked;
  return (
    <section className="analysis-walkthrough" aria-label="Analysis walkthrough">
      <div className="analysis-intro">
        <div>
          <span>After the reveal</span>
          <h2>From answers to a decision</h2>
        </div>
        <span>The analyst stays in control</span>
      </div>
      <nav className="analysis-steps" aria-label="Analysis steps">
        {steps.map((name, i) => (
          <button
            key={name}
            aria-current={step === i ? "step" : undefined}
            onClick={() => setStep(i)}
          >
            <span>
              {i < step ? <Check size={13} aria-hidden="true" /> : i + 1}
            </span>
            {name}
          </button>
        ))}
      </nav>
      <div className="analysis-step-content" key={step}>
        {step === 0 && (
          <>
            <h3>
              {Math.round(result.mean * 100)}% on average. The range matters
              too.
            </h3>
            <p>
              Estimates span {Math.round(result.spread.min * 100)}–
              {Math.round(result.spread.max * 100)}%. These dots represent
              grouped forecasts, not named experts.
            </p>
            <GroupChart result={result} reference={reference} />
          </>
        )}
        {step === 1 && (
          <>
            <h3>Different places can see different risks.</h3>
            <p>Regional views appear only with at least three estimates.</p>
            <div className="regional-comparison">
              {regions.map((r) => (
                <div key={r.region}>
                  <span>
                    {r.region}
                    <small>{r.n} estimates</small>
                  </span>
                  <div className="regional-track">
                    <span style={{ width: `${r.mean! * 100}%` }} />
                  </div>
                  <strong>{Math.round(r.mean! * 100)}%</strong>
                </div>
              ))}
              {regions.length === 0 && (
                <p>No region meets the display threshold.</p>
              )}
            </div>
            <PanelVisuals riskId={pulse.risk_id} />
          </>
        )}
        {step === 2 && (
          <>
            <h3>Repeated concerns still need evidence.</h3>
            <div className="theme-summary">
              <div>
                <strong>{checked}</strong>
                <span>corroborated themes</span>
              </div>
              <div>
                <strong>{pending}</strong>
                <span>themes awaiting checks</span>
              </div>
            </div>
            <div className="theme-evidence-list">
              {result.missing_themes.map((theme) => (
                <div key={theme.theme}>
                  <div>
                    <strong>{theme.theme}</strong>
                    <span>
                      {theme.count} mentions ·{" "}
                      {theme.origin === "single"
                        ? "one reported origin"
                        : "multiple reported origins"}
                    </span>
                  </div>
                  <span>
                    {theme.corroboration === "corroborated"
                      ? "Corroborated"
                      : "Needs checking"}
                  </span>
                </div>
              ))}
            </div>
            <p className="panel-viz-note">
              A repeated observation is not automatically an independent
              confirmation. These checks do not change the panel mean.
            </p>
          </>
        )}
        {step === 3 && (
          <>
            <h3>Evidence informs the draft. A person makes the call.</h3>
            <DraftRecommendation draft={draft} current={reference} />
            <DraftNarrative
              draft={draft}
              result={result}
              themes={result.missing_themes}
              evidence={pulse.evidence}
            />
            <div className="analyst-choice-preview">
              <span>Accept</span>
              <span>Edit</span>
              <span>Reject</span>
              <small>
                Available on the current round. This replay saves no decision.
              </small>
            </div>
          </>
        )}
      </div>
      <div className="analysis-step-actions">
        <button disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
          Previous
        </button>
        <span>
          {step + 1} of {steps.length}
        </span>
        <button
          className="primary"
          disabled={step === steps.length - 1}
          onClick={() => setStep((s) => s + 1)}
        >
          {step === 2 ? "Prepare draft preview" : "Next step"}
          <ArrowRight size={14} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
