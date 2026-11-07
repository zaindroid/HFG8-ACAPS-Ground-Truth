import { ResponseProgress } from "./ResponseProgress";
import { DeskContext, ContextSection } from "./DeskContext";
import { EvidenceLine } from "./Evidence";
import { PanelVisuals } from "./PanelVisuals";
import { Journey, DecisionSnapshot } from "./Journey";
import { LedgerRecord, LedgerColumns } from "./LedgerRecord";
import {
  DecisionUseFields,
  emptyDecisionUse,
  completeDecisionUse,
  QuestionContractPanel,
  OutcomeReportPanel,
} from "./V3Workflow";
import { PortalHeader } from "./PortalHeader";
import { bandRate, asPercent } from "./base-rates";
import { MethodChain, CoverageAdvice, RegionalSpread } from "./Method";
import { Section } from "./Panel";
import { VerificationTrail } from "./VerificationTrail";
import {
  DraftNarrative,
  DraftRecommendation,
  pendingClaims,
} from "./Grounding";
import { HonestyBox, IntegrityPanel, PanelMatch } from "./V2Panels";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowRight, Check, Copy, LockKeyhole, Radio } from "lucide-react";
import {
  apiBase,
  endpoint,
  safeUrl,
  validResult,
  type Draft,
  type LedgerEntry,
  type Pulse,
  type Result,
  type Risk,
  type QuestionContract,
} from "./service";
import { date, percent } from "./desk-model";
import "./workspace.css";

export function Frame({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  useEffect(() => {
    document.title = `${title} | Sealed Signals`;
  }, [title]);
  return (
    <>
      <a className="skip-link" href="#page-content">
        Skip to content
      </a>
      <PortalHeader />
      <main id="page-content" className="workspace live-workspace">
        <div className="workspace-title">
          <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
        </div>
        {children}
      </main>
    </>
  );
}
export { Section } from "./Panel";
export function CopyButton({
  value,
  label = "Copy",
}: {
  value: string;
  label?: string;
}) {
  const [status, setStatus] = useState("");
  return (
    <span className="copy-control">
      <button
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(value);
            setStatus("Copied");
          } catch {
            setStatus("Copy unavailable. Select the text to copy it.");
          }
        }}
      >
        <Copy size={15} />
        {label}
      </button>
      <span role="status">{status}</span>
    </span>
  );
}
export function GroupChart({
  result,
  reference,
}: {
  result: Result;
  reference: string;
}) {
  if (!validResult(result))
    return (
      <p>
        Group view withheld until at least five contributions are confirmed.
      </p>
    );
  const acaps = (
    {
      "Very Low": 0.1,
      Low: 0.3,
      Medium: 0.5,
      High: 0.7,
      "Very High": 0.9,
    } as Record<string, number>
  )[reference];
  const past = bandRate(reference);
  return (
    <>
      <div className="stat-row">
        <div>
          <span>Equal-weight mean</span>
          <strong>{percent(result.mean)}</strong>
        </div>
        <div>
          <span>Contributions</span>
          <strong>{result.n}</strong>
        </div>
        <div>
          <span>ACAPS probability band</span>
          <strong className="small-stat">{reference}</strong>
        </div>
      </div>
      <svg
        className="probability-chart"
        viewBox="0 0 560 185"
        role="img"
        aria-label={`Panel probability ${percent(result.mean)}, ${result.n} answers. ACAPS ${reference}.`}
      >
        <line x1="40" y1="134" x2="520" y2="134" className="chart-axis" />
        {[0, 20, 40, 60, 80, 100].map((v) => (
          <g key={v}>
            <line
              x1={40 + v * 4.8}
              x2={40 + v * 4.8}
              y1="24"
              y2="134"
              className="chart-grid"
            />
            <text x={40 + v * 4.8} y="155" textAnchor="middle">
              {v}%
            </text>
          </g>
        ))}
        {acaps !== undefined && (
          <>
            <line
              x1={40 + acaps * 480}
              x2={40 + acaps * 480}
              y1="20"
              y2="134"
              className="acaps-line"
            />
            <text x={40 + acaps * 480 - 8} y="16" textAnchor="end">
              ACAPS
            </text>
          </>
        )}
        {/* What this band has actually done, which the assumed midpoint above is not. */}
        {past && (
          <>
            <line
              x1={40 + past.rate * 480}
              x2={40 + past.rate * 480}
              y1="20"
              y2="134"
              className="base-rate-line"
            />
            <text x={40 + past.rate * 480 + 8} y="16" textAnchor="start">
              Past rate
            </text>
          </>
        )}
        {result.distribution.flatMap((b) =>
          Array.from({ length: Math.min(50, b.count) }, (_, i) => {
            const [lo, hi] = b.bucket.split("-").map(Number);
            return (
              <circle
                key={`${b.bucket}-${i}`}
                cx={40 + ((lo + hi) / 2) * 480}
                cy={118 - i * 20}
                r="6"
                className="panel-dot"
              />
            );
          }),
        )}
        <g stroke="var(--accent)" strokeWidth="2">
          <line
            x1={40 + result.spread.min * 480}
            x2={40 + result.spread.max * 480}
            y1="42"
            y2="42"
          />
          {[result.spread.min, result.spread.max].map((v) => (
            <line key={v} x1={40 + v * 480} x2={40 + v * 480} y1="36" y2="48" />
          ))}
        </g>
        {result.confidence_interval && (
          <g stroke="var(--accent)" strokeWidth="2">
            <line
              x1={40 + 480 * result.confidence_interval.lower}
              x2={40 + 480 * result.confidence_interval.upper}
              y1="42"
              y2="42"
            />
            {[
              result.confidence_interval.lower,
              result.confidence_interval.upper,
            ].map((v) => (
              <line
                key={v}
                x1={40 + 480 * v}
                x2={40 + 480 * v}
                y1="36"
                y2="48"
              />
            ))}
          </g>
        )}
        <circle
          cx={40 + result.mean * 480}
          cy="42"
          r="7"
          className="weighted-dot"
        />
        <text x="280" y="180" textAnchor="middle">
          Probability of materialisation within six months
        </text>
      </svg>
      <p className="panel-caption">
        Dots show bucket counts. Dashed line: ACAPS scale mapped to probability.
        Upper marker: equal-weight mean. Whisker: minimum to maximum forecast.
        ACAPS Probability bands are mapped to numbers by assumption, not
        official numeric thresholds.
        {past &&
          ` Past rate: of ${past.n} resolved ${reference} risks in the Risk List, ${asPercent(past.rate)} materialised.`}
        {!result.confidence_interval &&
          " Confidence intervals are unavailable."}
      </p>
      <div className="aggregate-detail">
        <p>
          Forecast spread: {percent(result.spread.min)}–
          {percent(result.spread.max)} · IQR {percent(result.spread.iqr)}.
          Secondary weighted mean: {percent(result.weighted_mean)}.
        </p>
        <h3>Minority reasons</h3>
        {result.disagreement.length ? (
          result.disagreement.map((reason: { summary?: string } | string, i: number) => (
            <p key={i}>{typeof reason === "string" ? reason : reason.summary}</p>
          ))
        ) : (
          <p>No minority reasons supplied.</p>
        )}
        <details>
          <summary>Experimental comparison</summary>
          <p className="panel-caption">
            SP: {result.sp_experiment.answer === "yes" ? "Yes" : "No"}.
            Experimental; does not replace the equal-weight mean. Method:{" "}
            {result.sp_experiment.method}.
          </p>
        </details>
      </div>
      <details>
        <summary>Distribution data</summary>
        <table>
          <thead>
            <tr>
              <th>Probability bucket</th>
              <th>Answers</th>
            </tr>
          </thead>
          <tbody>
            {result.distribution.map((b) => (
              <tr key={b.bucket}>
                <td>{b.bucket}</td>
                <td>{b.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  );
}
export function Verification({ draft }: { draft: Draft }) {
  return (
    <details className="draft-verification">
      <summary>Evidence checks · {draft.claims?.length || 0} claims</summary>
      <p className="panel-caption">
        These checks compare draft claims with their cited records. They do not
        measure the chance that the forecast is correct.
      </p>
      {draft.judge ? (
        <>
          <div className="stat-row">
            <div>
              <span>Citation coverage</span>
              <strong>{percent(draft.judge.coverage)}</strong>
            </div>
            <div>
              <span>Numbers match</span>
              <strong>{percent(draft.judge.numbers_match)}</strong>
            </div>
            <div>
              <span>Automated review score</span>
              <strong>{percent(draft.judge.overall)}</strong>
            </div>
          </div>
          {draft.claims?.map((claim) => (
            <div
              className={
                draft.judge!.flagged_claim_ids.includes(claim.claim_id)
                  ? "claim flagged"
                  : "claim"
              }
              key={claim.claim_id}
            >
              <strong>
                {claim.claim_id} ·{" "}
                {draft.skeptic?.find((s) => s.claim_id === claim.claim_id)
                  ?.verdict || "Not checked"}
              </strong>
              <p>{claim.text}</p>
              <small>
                {claim.evidence_kind}: {claim.evidence_ref}
              </small>
              {draft.skeptic
                ?.find((s) => s.claim_id === claim.claim_id)
                ?.checks.map((check, i) => (
                  <p key={i}>{check}</p>
                ))}
            </div>
          ))}
        </>
      ) : (
        <p className="panel-caption">
          Skeptic verdicts and Judge scores have not been supplied. Review the
          cited evidence before deciding.
        </p>
      )}
      {draft.missing_checks?.map((check) => (
        <p key={check.theme}>
          {check.theme}: {check.status}
        </p>
      ))}
    </details>
  );
}
function LiveDesk() {
  const [risks, setRisks] = useState<Risk[]>([]),
    [selected, setSelected] = useState(
      new URLSearchParams(location.search).get("risk_id") || "",
    );
  const [pulse, setPulse] = useState<Pulse | null>(null),
    [group, setGroup] = useState<Result | null>(null),
    [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState("Loading risks"),
    [message, setMessage] = useState(""),
    [connection, setConnection] = useState("Connecting");
  const [decisionUse, setDecisionUse] = useState(emptyDecisionUse);
  const [frozenContract, setFrozenContract] = useState<QuestionContract | null>(
    null,
  );
  const [note, setNote] = useState(""),
    [edit, setEdit] = useState(false),
    [probability, setProbability] = useState("High"),
    [pulseId, setPulseId] = useState(
      new URLSearchParams(location.search).get("pulse_id") || "",
    );
  const [outcome, setOutcome] = useState("materialised"),
    [resolvedAt, setResolvedAt] = useState(""),
    [confirmResolve, setConfirmResolve] = useState(false);
  async function run(label: string, task: () => Promise<void>) {
    setBusy(label);
    setError("");
    try {
      await task();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function load() {
    await run("Loading risks", async () => {
      const response = await endpoint.risks();
      setRisks(response.risks);
      setSelected((previous) =>
        response.risks.some((r) => r.risk_id === previous)
          ? previous
          : response.risks[0]?.risk_id || "",
      );
    });
  }
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    let active = true;
    const events = new EventSource(`${apiBase}/events`);
    events.onopen = () => setConnection("Connected");
    events.onerror = () =>
      setConnection(
        events.readyState === EventSource.CLOSED
          ? "Unavailable · refresh answers manually"
          : "Disconnected · retrying automatically",
      );
    const onEvent = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (event.type === "pulse_fired") {
          setMessage(
            `A new pulse is available: ${data.pulse_id || "refresh the pulse list"}.`,
          );
          return;
        }
        if (data.pulse_id && pulse && data.pulse_id !== pulse.id) return;
        if (
          event.type === "answer_sealed" &&
          pulse &&
          Number.isInteger(data.n_answers) &&
          data.n_answers >= 0
        )
          setPulse((p) => (p ? { ...p, n_answers: data.n_answers } : p));
        if (event.type === "round_revealed" && pulse)
          void endpoint
            .result(pulse.id)
            .then((value) => {
              if (active && validResult(value) && value.pulse_id === pulse.id)
                setGroup(value);
            })
            .catch(() => {
              if (active)
                setMessage("Round changed. Refresh the result to retrieve it.");
            });
        if (event.type === "draft_decided")
          setMessage(
            "An analyst decision was recorded. Refresh the ledger to view it.",
          );
        if (event.type === "risk_resolved") {
          setMessage(
            "Risk resolved. Refresh the group outcome report. Private calibration is opt-in after five resolutions.",
          );
        }
      } catch {
        setMessage(
          "An unreadable event was ignored. Refresh to check the current state.",
        );
      }
    };
    for (const type of [
      "pulse_fired",
      "answer_sealed",
      "round_revealed",
      "draft_decided",
      "risk_resolved",
    ])
      events.addEventListener(type, onEvent as EventListener);
    return () => {
      active = false;
      events.close();
    };
  }, [pulse?.id]);
  const risk = risks.find((r) => r.risk_id === selected);
  function clearRound(value: Pulse) {
    if (value.risk_id !== selected)
      throw new Error(
        "The API returned a pulse for another risk. Select that risk before opening it.",
      );
    setPulse(value);
    setGroup(null);
    setDraft(null);
    setNote("");
    setEdit(false);
  }
  async function decision(action: "accept" | "edit" | "reject") {
    if (!draft) return;
    if (!note.trim()) {
      setError("Add a decision note before continuing.");
      document.getElementById("live-note")?.focus();
      return;
    }
    if (!completeDecisionUse(decisionUse)) {
      setError(
        "Add the decision, decision owner and deadline before continuing.",
      );
      return;
    }
    await run("Saving analyst decision", async () => {
      const value = await endpoint.decision(
        draft.id,
        action,
        note.trim(),
        probability,
        decisionUse,
      );
      setDraft(value);
      setMessage(`Draft ${value.status}. The ledger follows the API decision.`);
    });
  }
  return (
    <Frame
      title="Analyst desk"
      subtitle="Independent answers. Cited evidence. Your decision."
    >
      <Journey active={2} />
      <DecisionSnapshot
        rating={risk?.probability_acaps || "Awaiting risk"}
        result={group}
      />
      <details className="connection-detail">
        <summary>Connection status</summary>
        <div className="mode-banner">
          <Radio size={16} />
          <span>API mode · Events: {connection}</span>
        </div>
      </details>
      <div className="live-toolbar">
        <label htmlFor="risk-select">Risk</label>
        <select
          id="risk-select"
          value={selected}
          disabled={!!busy}
          onChange={(e) => {
            setSelected(e.target.value);
            setPulse(null);
            setGroup(null);
            setDraft(null);
          }}
        >
          <option value="" disabled>
            Select a risk
          </option>
          {risks.map((r) => (
            <option value={r.risk_id} key={r.risk_id}>
              {r.country} / {r.risk_id}
            </option>
          ))}
        </select>
        <button disabled={!!busy} onClick={() => void load()}>
          Refresh risks
        </button>
        <button
          disabled={!!busy || !selected}
          onClick={() =>
            void run("Creating pulse", async () =>
              clearRound(await endpoint.create(selected)),
            )
          }
        >
          Ask panel
        </button>
        {import.meta.env.VITE_FF_DOORBELL === "1" && (
          <button
            disabled={!!busy}
            onClick={() =>
              void run("Checking indicators", async () => {
                const value = await endpoint.doorbell();
                setMessage(
                  `${value.shifts.length} shifts detected; ${value.pulses_fired.length} pulses fired.`,
                );
                if (value.pulses_fired[0]) {
                  setPulseId(value.pulses_fired[0]);
                  clearRound(await endpoint.pulse(value.pulses_fired[0]));
                }
              })
            }
          >
            Run phase-2 doorbell
          </button>
        )}
      </div>
      {error && (
        <div className="error-box" role="alert">
          <p>{error}</p>
          <button onClick={() => setError("")}>Dismiss</button>
        </div>
      )}
      <p className="workspace-message" role="status">
        {busy || message}
      </p>
      {risk ? (
        <>
          <div className="risk-strip">
            <div>
              <span className="rating">{risk.level} risk</span>
              <h2>{risk.title}</h2>
            </div>
            <span>{risk.horizon_months}-month horizon</span>
          </div>
          <div className="desk-grid">
            <div className="desk-main">
              <Section title="Expert responses" className="response-panel">
                <div className="live-toolbar">
                  <label htmlFor="pulse-id">Pulse ID</label>
                  <input
                    id="pulse-id"
                    value={pulseId}
                    onChange={(e) => setPulseId(e.target.value)}
                    placeholder="Open an existing pulse"
                  />
                  <button
                    disabled={!!busy || !pulseId.trim()}
                    onClick={() =>
                      void run("Opening pulse", async () => {
                        const value = await endpoint.pulse(pulseId.trim());
                        if (value.risk_id !== selected)
                          throw new Error(
                            "This pulse belongs to another risk. Select that risk first.",
                          );
                        clearRound(value);
                      })
                    }
                  >
                    Open pulse
                  </button>
                </div>
                {pulse ? (
                  <>
                    <p>
                      {pulse.id} · Round {pulse.round} · {pulse.n_answers}{" "}
                      sealed answers
                    </p>
                    {group && validResult(group) ? (
                      <ResponseProgress
                        total={group.n}
                        count={group.n}
                        revealed
                      />
                    ) : (
                      <ResponseProgress
                        total={Math.max(8, pulse.n_answers)}
                        count={pulse.n_answers}
                        revealed={false}
                      />
                    )}
                    <div className="panel-actions">
                      <button
                        className="primary"
                        disabled={!!busy || pulse.n_answers < 5 || !!group}
                        onClick={() =>
                          void run("Revealing round", async () => {
                            const value = await endpoint.reveal(pulse.id);
                            if (value.pulse_id !== pulse.id)
                              throw new Error(
                                "The API returned a result for a different pulse. Refresh the selected pulse.",
                              );
                            if (!validResult(value))
                              throw new Error(
                                "Group view withheld: at least five contributions are required.",
                              );
                            setGroup(value);
                          })
                        }
                      >
                        Reveal round
                      </button>
                      <button
                        disabled={!!busy}
                        onClick={() =>
                          void run("Refreshing panel", async () =>
                            setPulse(await endpoint.pulse(pulse.id)),
                          )
                        }
                      >
                        Refresh answers
                      </button>
                      <button
                        disabled={!!busy}
                        onClick={() =>
                          void run("Opening result", async () => {
                            const value = await endpoint.result(pulse.id);
                            if (value.pulse_id !== pulse.id)
                              throw new Error(
                                "The API returned a result for a different pulse. Refresh the selected pulse.",
                              );
                            if (!validResult(value))
                              throw new Error(
                                "Group view withheld: fewer than five contributions.",
                              );
                            setGroup(value);
                          })
                        }
                      >
                        Refresh result
                      </button>
                    </div>
                    <p className="panel-caption">
                      At least five answers are required to reveal.
                    </p>
                  </>
                ) : (
                  <p>
                    Ask the panel or open a pulse to begin. No answers have been
                    loaded.
                  </p>
                )}
              </Section>
              <Section title="Panel coverage" className="coverage-panel">
                <PanelVisuals riskId={selected} />
              </Section>
              <Section
                title="Expert forecast versus ACAPS"
                className="forecast-panel"
              >
                {group ? (
                  <GroupChart
                    result={group}
                    reference={risk.probability_acaps}
                  />
                ) : (
                  <div className="empty-panel">
                    <LockKeyhole size={24} />
                    <p>The group view stays sealed until reveal.</p>
                  </div>
                )}
              </Section>
              <Section title="Draft update" className="decision-panel">
                {!draft ? (
                  <button
                    disabled={!!busy || !group || !pulse}
                    onClick={() =>
                      void run("Preparing cited draft", async () => {
                        const value = await endpoint.draft(pulse!.id);
                        setDraft(value);
                        setProbability(value.proposed_probability);
                      })
                    }
                  >
                    Prepare draft
                  </button>
                ) : (
                  <>
                    <DraftRecommendation
                      draft={draft}
                      current={risk.probability_acaps}
                    />
                    <DraftNarrative
                      showFacts={false}
                      draft={draft}
                      themes={group?.missing_themes}
                      result={group || undefined}
                      evidence={pulse?.evidence}
                    />
                    <div className="citations">
                      {draft.citations
                        ?.filter((c) => safeUrl(c.url))
                        .map((c) => (
                          <a
                            href={safeUrl(c.url)}
                            key={c.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {c.text}
                          </a>
                        ))}
                    </div>
                    <Verification draft={draft} />
                    {draft.status === "draft" ? (
                      <div className="decision-form">
                        {pendingClaims(
                          draft,
                          group?.missing_themes,
                          group || undefined,
                        ).length > 0 && (
                          <button
                            disabled={!!busy}
                            onClick={() =>
                              void run("Refreshing checked draft", async () =>
                                setDraft(await endpoint.draft(pulse!.id)),
                              )
                            }
                          >
                            Request refreshed draft
                          </button>
                        )}
                        <DecisionUseFields
                          value={decisionUse}
                          onChange={setDecisionUse}
                        />
                        <label htmlFor="live-note">Decision note</label>
                        <textarea
                          id="live-note"
                          maxLength={500}
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                        />
                        {edit && (
                          <>
                            <label htmlFor="live-probability">
                              Edited probability
                            </label>
                            <select
                              id="live-probability"
                              value={probability}
                              onChange={(e) => setProbability(e.target.value)}
                            >
                              {[
                                "Very Low",
                                "Low",
                                "Medium",
                                "High",
                                "Very High",
                              ].map((v) => (
                                <option key={v}>{v}</option>
                              ))}
                            </select>
                          </>
                        )}
                        <div className="panel-actions">
                          <button
                            disabled={
                              !!busy ||
                              pendingClaims(
                                draft,
                                group?.missing_themes,
                                group || undefined,
                              ).length > 0
                            }
                            className="primary"
                            onClick={() =>
                              void decision(edit ? "edit" : "accept")
                            }
                          >
                            {edit ? "Save edited decision" : "Accept draft"}
                          </button>
                          <button
                            disabled={!!busy}
                            onClick={() => setEdit((v) => !v)}
                          >
                            {edit ? "Cancel edit" : "Edit probability"}
                          </button>
                          <button
                            disabled={!!busy}
                            onClick={() => void decision("reject")}
                          >
                            Reject draft
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="decision-log">
                        <h3>Decision log</h3>
                        <p>
                          {draft.status}: {draft.note}
                        </p>
                        {draft.decided_at && (
                          <time>{date(draft.decided_at)}</time>
                        )}
                        <a href="/ledger">
                          Open public ledger <ArrowRight size={15} />
                        </a>
                      </div>
                    )}
                  </>
                )}
              </Section>
              {draft &&
                ["accepted", "edited", "rejected"].includes(draft.status) && (
                  <>
                    <Section title="Resolve and score">
                      <p>
                        Record the observed outcome when this forecast resolves.
                      </p>
                      <div className="resolution-form">
                        <label htmlFor="outcome">Observed outcome</label>
                        <select
                          id="outcome"
                          value={outcome}
                          onChange={(e) => setOutcome(e.target.value)}
                        >
                          <option value="materialised">Materialised</option>
                          <option value="not_materialised">
                            Not materialised
                          </option>
                        </select>
                        <label htmlFor="resolved-at">
                          Resolution date (UTC)
                        </label>
                        <input
                          id="resolved-at"
                          type="date"
                          max={new Date().toISOString().slice(0, 10)}
                          value={resolvedAt}
                          onChange={(e) => setResolvedAt(e.target.value)}
                        />
                        <label className="changed">
                          <input
                            type="checkbox"
                            checked={confirmResolve}
                            onChange={(e) =>
                              setConfirmResolve(e.target.checked)
                            }
                          />{" "}
                          I confirm this is an observed outcome.
                        </label>
                        <button
                          disabled={
                            !!busy ||
                            !confirmResolve ||
                            !resolvedAt ||
                            frozenContract?.risk_id !== selected
                          }
                          onClick={() =>
                            void run("Resolving and scoring", async () => {
                              if (
                                !frozenContract ||
                                frozenContract.risk_id !== selected
                              )
                                throw new Error(
                                  "Freeze the question contract before scoring.",
                                );
                              const value = await endpoint.resolve(
                                selected,
                                outcome,
                                `${resolvedAt}T00:00:00Z`,
                              );
                              setMessage(
                                `${value.scores_written} scores written; ${value.weights_updated} reliability weights updated.`,
                              );
                              setConfirmResolve(false);
                            })
                          }
                        >
                          Resolve risk and score forecasts
                        </button>
                        {!frozenContract && (
                          <p className="panel-caption">
                            Scoring is disabled until the API confirms a frozen
                            question contract. Abstentions and free text are
                            never scored.
                          </p>
                        )}
                      </div>
                    </Section>
                  </>
                )}
            </div>
            <aside className="desk-side">
              <DeskContext>
                <ContextSection label="Question">
                  <QuestionContractPanel
                    key={selected}
                    riskId={selected}
                    onFrozen={setFrozenContract}
                  />
                </ContextSection>
                <ContextSection label="Panel details">
                  <PanelMatch riskId={selected} />
                </ContextSection>
                <ContextSection label="Review notes">
                  <Section
                    title="Published evidence"
                    className="evidence-panel"
                  >
                    {pulse?.evidence.length ? (
                      pulse.evidence.map((e, i) => (
                        <EvidenceLine key={i} value={e} />
                      ))
                    ) : (
                      <p>No pulse evidence loaded.</p>
                    )}
                  </Section>
                  {pulse && group && <IntegrityPanel pulseId={pulse.id} />}
                  <Section title="Agreement by region">
                    {group ? (
                      <RegionalSpread
                        result={group}
                        countries={risk?.country ? [risk.country] : []}
                      />
                    ) : (
                      <p>Regional views open after reveal.</p>
                    )}
                  </Section>
                  <Section title="What this panel could not see">
                    {group ? (
                      <CoverageAdvice result={group} />
                    ) : (
                      <p>Coverage observations open after reveal.</p>
                    )}
                  </Section>
                </ContextSection>
                <ContextSection label="Method">
                  <Section title="How this number was reached">
                    {group ? (
                      <MethodChain
                        result={group}
                        reference={risk?.probability_acaps || ""}
                      />
                    ) : (
                      <p>The method opens after reveal.</p>
                    )}
                  </Section>
                </ContextSection>
                <ContextSection label="Outcome">
                  {pulse ? (
                    <OutcomeReportPanel key={pulse.id} pulseId={pulse.id} />
                  ) : (
                    <p>Open a pulse to review its outcome.</p>
                  )}
                </ContextSection>
              </DeskContext>
            </aside>
          </div>
        </>
      ) : (
        !busy && (
          <Section title="No active risks">
            <p>No risk cards are available. Refresh to check again.</p>
          </Section>
        )
      )}
    </Frame>
  );
}
function LiveLedger() {
  const [entries, setEntries] = useState<LedgerEntry[]>([]),
    [hidden, setHidden] = useState(0),
    [query, setQuery] = useState(""),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [receipts, setReceipts] = useState<
    Record<string, { valid: boolean; anchor: string | null }>
  >({});
  async function load() {
    setBusy("Loading ledger");
    setError("");
    setReceipts({});
    try {
      const value = await endpoint.ledger();
      const checked = await Promise.all(
        value.entries.map(async (entry) => {
          if (typeof entry.honesty?.n === "number")
            return {
              ...entry,
              n:
                typeof entry.n === "number"
                  ? Math.min(entry.n, entry.honesty.n)
                  : entry.honesty.n,
            };
          if (typeof entry.n === "number") return entry;
          try {
            const result = await endpoint.result(entry.pulse_id);
            return {
              ...entry,
              n:
                validResult(result) && result.pulse_id === entry.pulse_id
                  ? result.n
                  : 0,
            };
          } catch {
            return { ...entry, n: 0 };
          }
        }),
      );
      const safe = checked.filter(
        (e) => Number.isInteger(e.n) && e.n! >= Math.max(5, value.k_min || 5),
      );
      setEntries(safe);
      setHidden(checked.length - safe.length);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  useEffect(() => {
    void load();
  }, []);
  return (
    <Frame
      title="Public ledger"
      subtitle="Group forecasts, analyst decisions and observed outcomes."
    >
      <Journey active={3} />
      <div className="ledger-toolbar">
        <label htmlFor="search">Find a risk</label>
        <input
          id="search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Risk ID"
        />
        <button disabled={!!busy} onClick={() => void load()}>
          Refresh ledger
        </button>
      </div>
      {error && (
        <p className="error-box" role="alert">
          {error}
        </p>
      )}
      <p role="status" className="workspace-message">
        {busy || message}
      </p>
      <LedgerColumns />
      {entries
        .filter((e) => e.risk_id.toLowerCase().includes(query.toLowerCase()))
        .map((entry) => (
          <LedgerRecord
            key={`${entry.risk_id}-${entry.pulse_id}`}
            entry={entry}
            checked={receipts[entry.verify_hash]?.valid}
          >
            <Section title={`${entry.risk_id} / ${entry.pulse_id}`}>
              <div className="ledger-stats">
                <div>
                  <span>Group probability</span>
                  <strong>{percent(entry.group_probability)}</strong>
                  <small>{entry.n} contributions</small>
                </div>
                <div>
                  <span>ACAPS probability</span>
                  <strong>{entry.acaps_probability}</strong>
                  <small>Risk level: {entry.acaps_level}</small>
                  {/* The band's own record, so a reader can judge the rating
                      against what that band has done before. */}
                  {bandRate(entry.acaps_probability) && (
                    <small>
                      {asPercent(bandRate(entry.acaps_probability)!.rate)} of{" "}
                      {bandRate(entry.acaps_probability)!.n} past{" "}
                      {entry.acaps_probability} risks materialised
                    </small>
                  )}
                </div>
                <div>
                  <span>Outcome</span>
                  <strong className="small-stat">
                    {entry.outcome?.replaceAll("_", " ") || "Unresolved"}
                  </strong>
                  {entry.resolved_at && (
                    <small>{date(entry.resolved_at)}</small>
                  )}
                </div>
              </div>
              <VerificationTrail
                entry={entry}
                receipt={receipts[entry.verify_hash]}
              />
              <HonestyBox
                value={entry.honesty}
                context={`${entry.risk_id} / ${entry.pulse_id}`}
              />
              <dl className="ledger-details">
                <div>
                  <dt>Sealed at</dt>
                  <dd>{date(entry.sealed_at)}</dd>
                </div>
                <div>
                  <dt>Verification hash</dt>
                  <dd>
                    <code>{entry.verify_hash}</code>
                  </dd>
                </div>
              </dl>
              <div className="panel-actions">
                <button
                  disabled={!!busy}
                  className={
                    receipts[entry.verify_hash]?.valid ? "verified-button" : ""
                  }
                  onClick={async () => {
                    setBusy("Verifying ledger entry");
                    setError("");
                    setMessage("");
                    setReceipts((previous) => {
                      const next = { ...previous };
                      delete next[entry.verify_hash];
                      return next;
                    });
                    try {
                      const receipt = await endpoint.verify(entry.verify_hash);
                      if (
                        typeof receipt.valid !== "boolean" ||
                        (receipt.anchor !== null &&
                          typeof receipt.anchor !== "string")
                      )
                        throw new Error(
                          "The API returned an unreadable verification receipt. This record has not been verified.",
                        );
                      const timeMatches =
                        Number.isFinite(Date.parse(receipt.sealed_at)) &&
                        Date.parse(receipt.sealed_at) ===
                          Date.parse(entry.sealed_at);
                      const valid = receipt.valid && timeMatches;
                      setReceipts((v) => ({
                        ...v,
                        [entry.verify_hash]: { ...receipt, valid },
                      }));
                      setMessage(
                        valid
                          ? "API reports a valid ledger entry."
                          : receipt.valid && !timeMatches
                            ? "Verification failed. The receipt timestamp does not match this ledger entry."
                            : "Verification failed. The API reports a hash mismatch.",
                      );
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy("");
                    }
                  }}
                >
                  {receipts[entry.verify_hash]?.valid && <Check size={16} />}
                  Verify entry
                </button>
                <CopyButton value={entry.verify_hash} label="Copy hash" />
              </div>
            </Section>
          </LedgerRecord>
        ))}
      {!busy &&
        !error &&
        entries.filter((e) =>
          e.risk_id.toLowerCase().includes(query.toLowerCase()),
        ).length === 0 && (
          <Section
            title={query ? "No matching risks" : "No eligible ledger entries"}
          >
            <p>
              {query
                ? "Try another risk ID."
                : "Entries appear after analyst approval and require at least five confirmed contributions."}
            </p>
          </Section>
        )}
      {hidden > 0 && (
        <p className="panel-caption">
          {hidden} entries withheld because five contributions could not be
          confirmed.
        </p>
      )}
    </Frame>
  );
}
export function LiveWorkspace({ page }: { page: "desk" | "ledger" }) {
  return page === "desk" ? <LiveDesk /> : <LiveLedger />;
}
