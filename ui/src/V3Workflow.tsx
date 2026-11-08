import { useEffect, useState } from "react";
import {
  MapPin,
  CalendarDays,
  ShieldCheck,
  Target,
  LockKeyhole,
} from "lucide-react";
import { mock } from "./api";
import { sampleDataEnabled, sampleResult, sampleBoard } from "./demo-data";
import {
  endpoint,
  validResult,
  type DecisionUse,
  type QuestionContract,
  type OutcomeReport,
  type Board,
} from "./service";
import { Section } from "./LiveWorkspace";
import contractExample from "../../fixtures/POST_risks_contract_request.json";
import resultExample from "../../fixtures/GET_pulses_result.json";
import reportExample from "../../fixtures/GET_pulses_outcome_report.json";

export const emptyDecisionUse = (): DecisionUse => ({
  what_decision: "",
  for_whom: "",
  by_when: "",
});
export function completeDecisionUse(value: DecisionUse) {
  return !!(
    value.what_decision.trim() &&
    value.for_whom.trim() &&
    /^\d{4}-\d{2}-\d{2}$/.test(value.by_when)
  );
}
export function DecisionUseFields({
  value,
  onChange,
}: {
  value: DecisionUse;
  onChange: (value: DecisionUse) => void;
}) {
  return (
    <fieldset className="decision-use-fields">
      <legend>What decision could this inform?</legend>
      {(
        [
          ["what_decision", "Decision to inform"],
          ["for_whom", "Decision owner"],
          ["by_when", "Decision needed by"],
        ] as const
      ).map(([key, label]) => (
        <div key={key}>
          <label htmlFor={`use-${key}`}>{label}</label>
          <input
            id={`use-${key}`}
            type={key === "by_when" ? "date" : "text"}
            maxLength={240}
            value={value[key]}
            onChange={(e) => onChange({ ...value, [key]: e.target.value })}
          />
        </div>
      ))}
    </fieldset>
  );
}

export function QuestionContractPanel({
  riskId,
  onFrozen,
}: {
  riskId: string;
  onFrozen: (value: QuestionContract | null) => void;
}) {
  const [value, setValue] = useState<QuestionContract>({
    risk_id: riskId,
    ...(riskId === "R1043"
      ? contractExample
      : {
          event: "",
          location: "",
          horizon_deadline: "",
          resolution_source: "",
          adjudication_rule: "",
        }),
  });
  const [frozen, setFrozen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    onFrozen(null);
  }, [riskId, onFrozen]);
  return (
    <Section title="Question being forecast">
      <div className={`question-status ${frozen ? "confirmed" : ""}`}>
        <LockKeyhole size={15} aria-hidden="true" />
        {frozen ? "Confirmed" : "Awaiting analyst confirmation"}
      </div>
      <div className="question-at-glance">
        <div className="forecast-event">
          <h3>
            <Target size={20} aria-hidden="true" /> Will this happen?
          </h3>
          <p>{value.event || "Define the event this panel will forecast."}</p>
        </div>
        <dl>
          <div>
            <dt>
              <MapPin size={19} aria-hidden="true" /> Where
            </dt>
            <dd>{value.location || "Not defined"}</dd>
          </div>
          <div>
            <dt>
              <CalendarDays size={19} aria-hidden="true" /> By when
            </dt>
            <dd>
              {/^\d{4}-\d{2}-\d{2}$/.test(value.horizon_deadline) &&
              Number.isFinite(Date.parse(value.horizon_deadline)) ? (
                <time dateTime={value.horizon_deadline}>
                  {new Intl.DateTimeFormat("en-GB", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    timeZone: "UTC",
                  }).format(new Date(value.horizon_deadline))}
                </time>
              ) : (
                value.horizon_deadline || "Not defined"
              )}
            </dd>
          </div>
          <div>
            <dt>
              <ShieldCheck size={19} aria-hidden="true" /> How we check it
            </dt>
            <dd>{value.resolution_source || "Not defined"}</dd>
          </div>
        </dl>
      </div>
      <p className="question-next">
        {frozen
          ? "Forecasts will be checked against this confirmed question."
          : "Confirm these rules before scoring the forecasts."}
      </p>
      <details className="question-editor">
        <summary>Edit question and resolution rules</summary>
        <form
          className="contract-form"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              const saved = mock
                ? { ...value, frozen_at: new Date().toISOString() }
                : await endpoint.contract(riskId, value);
              if (
                saved.risk_id !== riskId ||
                !saved.frozen_at ||
                !Number.isFinite(Date.parse(saved.frozen_at)) ||
                (
                  [
                    "event",
                    "location",
                    "horizon_deadline",
                    "resolution_source",
                    "adjudication_rule",
                  ] as const
                ).some((key) => saved[key] !== value[key])
              )
                throw new Error(
                  "The API did not confirm this frozen contract. Scoring remains disabled; Lane A must return the versioned contract and frozen_at.",
                );
              setFrozen(true);
              onFrozen(saved);
            } catch (e) {
              setError((e as Error).message);
              onFrozen(null);
            } finally {
              setBusy(false);
            }
          }}
        >
          <fieldset disabled={frozen || busy}>
            {(
              [
                ["event", "Event definition"],
                ["location", "Location"],
                ["horizon_deadline", "Horizon deadline"],
                ["resolution_source", "Resolution source"],
                ["adjudication_rule", "Adjudication rule"],
              ] as const
            ).map(([key, label]) => (
              <div key={key}>
                <label htmlFor={`contract-${key}`}>{label}</label>
                <input
                  id={`contract-${key}`}
                  required
                  type={key === "horizon_deadline" ? "date" : "text"}
                  value={value[key]}
                  maxLength={700}
                  onChange={(e) =>
                    setValue({ ...value, [key]: e.target.value })
                  }
                />
              </div>
            ))}
            <button type="submit">
              {busy ? "Freezing contract…" : "Freeze question contract"}
            </button>
          </fieldset>
        </form>
      </details>
      {error && <p role="alert">{error}</p>}
      {frozen && (
        <p role="status">
          {mock
            ? "Demo contract frozen locally · synthetic workflow only."
            : "Contract frozen and confirmed by the API."}
        </p>
      )}
    </Section>
  );
}

export function OutcomeReportPanel({ pulseId }: { pulseId: string }) {
  const [report, setReport] = useState<OutcomeReport | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    setReport(null);
    setError("");
  }, [pulseId]);
  return (
    <Section title="Group outcome report">
      <p className="panel-caption">
        Every panel member receives the group outcome when the risk resolves.
        This is separate from optional private calibration.
      </p>
      <button
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError("");
          setReport(null);
          try {
            const [value, result] = mock
              ? sampleDataEnabled()
                ? [
                    {
                      ...reportExample,
                      outcome: "pending",
                      group_mean: sampleResult.mean,
                      analyst_decision_summary:
                        "Synthetic analyst decision recorded. This active round has no observed outcome yet and has not been scored.",
                    },
                    sampleResult,
                  ]
                : [reportExample, resultExample]
              : await Promise.all([
                  endpoint.outcomeReport(pulseId),
                  endpoint.result(pulseId),
                ]);
            if (
              value.pulse_id !== pulseId ||
              result.pulse_id !== pulseId ||
              !validResult(result) ||
              !Number.isFinite(value.group_mean) ||
              value.group_mean !== result.mean
            )
              throw new Error(
                "The group outcome is unavailable or does not match a confirmed group of at least five.",
              );
            setReport(value);
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Loading outcome…" : "Open group outcome report"}
      </button>
      {error && <p role="alert">{error}</p>}
      {report && (
        <div className="outcome-report">
          <p>
            {mock && "Synthetic report · "}Equal-weight group mean:{" "}
            {Math.round(report.group_mean * 100)}%
          </p>
          <p>Outcome: {report.outcome.replaceAll("_", " ")}</p>
          <p>{report.analyst_decision_summary}</p>
          <p className="panel-caption">
            Aggregate disclosure rule: at least five estimates. No individual
            answer or rationale is public.
          </p>
        </div>
      )}
    </Section>
  );
}

export function CommitteeScoring() {
  const [value, setValue] = useState<Board | null>(() =>
      mock && sampleDataEnabled() ? sampleBoard : null,
    ),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <Section title="Committee-side forecast review">
      <p className="panel-caption">
        Forecasts are scored after a frozen question contract resolves.
        Abstentions and free text are never scored. Scores never gate approval.
        The backend must enforce committee authorization; this demo button does
        not grant a role.
      </p>
      <button
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            setValue(
              mock && sampleDataEnabled()
                ? sampleBoard
                : mock
                  ? (await import("../../fixtures/GET_committee_scoring.json"))
                      .default
                  : await endpoint.board(),
            );
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Loading forecasts…" : "Load committee scoring"}
      </button>
      {error && <p role="alert">{error}</p>}
      {value && (
        <div className="table-wrap">
          <table>
            <thead>
              {/* Panels, not people: v3.4 scores the forecast, and a per-expert
                  leaderboard is the thing it deliberately removed. */}
              <tr>
                <th>Panel</th>
                <th>Risk</th>
                <th>Resolved</th>
                <th>Panel Brier</th>
                <th>ACAPS band Brier</th>
              </tr>
            </thead>
            <tbody>
              {value.panels.map((panel) => (
                <tr key={panel.panel_id}>
                  <td>{panel.panel_id}</td>
                  {/* A panel can be asked about more than one risk, so the engine reports the
                      list. One row per panel, with the risks it was asked about. */}
                  <td>{panel.risk_ids.join(", ")}</td>
                  <td>{panel.n_resolved}</td>
                  <td>
                    {panel.panel_brier === null
                      ? panel.status
                      : panel.panel_brier.toFixed(2)}
                  </td>
                  <td>
                    {panel.acaps_band_brier === null
                      ? "—"
                      : panel.acaps_band_brier.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="panel-caption">
            {mock && sampleDataEnabled()
              ? "These are synthetic sample forecast scores."
              : "These values are supplied by the backend."}{" "}
            Equal-weight mean remains primary. Secondary weights start equal,
            shrink toward a prior and are capped at twice the median; the
            backend must implement those rules.
          </p>
        </div>
      )}
    </Section>
  );
}
