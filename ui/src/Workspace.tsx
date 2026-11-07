import { ResponseProgress } from "./ResponseProgress";
import { scrollToDeskSection } from "./desk-navigation";
import { RevealOverview } from "./RevealOverview";
import { ArrivalForecast } from "./ArrivalForecast";
import { DeskContext, ContextSection } from "./DeskContext";
import { EvidenceLine } from "./Evidence";
import { useArrivalReplay } from "./useArrivalReplay";
import { PanelVisuals, AnalysisWalkthrough } from "./PanelVisuals";
import { Journey, DecisionSnapshot } from "./Journey";
import { LedgerRecord, LedgerColumns } from "./LedgerRecord";
import { sampleDataEnabled, sampleRisks } from "./demo-data";
import {
  DecisionUseFields,
  emptyDecisionUse,
  completeDecisionUse,
  OutcomeReportPanel,
  QuestionContractPanel,
} from "./V3Workflow";
import { PortalHeader } from "./PortalHeader";
import { VerificationTrail } from "./VerificationTrail";
import { HistoricalLedger } from "./HistoricalLedger";
import { bandRate, asPercent } from "./base-rates";
import { MethodChain, CoverageAdvice, spreadNote } from "./Method";
import { DraftNarrative, DraftRecommendation } from "./Grounding";
import { HonestyBox, IntegrityPanel, PanelMatch } from "./V2Panels";
import { GroupChart, Verification } from "./LiveWorkspace";
import { useEffect, useState, type ReactNode } from "react";
import {
  ArrowRight,
  Bell,
  Check,
  Copy,
  FileCheck2,
  Inbox,
  LockKeyhole,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { mock } from "./api";
import {
  date,
  draft,
  eligibleEntries,
  percent,
  pulse,
  readDecision,
  result,
  risk,
  storageKey,
  verifyFixture,
  type Decision,
} from "./desk-model";
import "./workspace.css";

function Panel({
  title,
  detail,
  children,
  className = "",
}: {
  title: string;
  detail?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`workspace-panel ${className}`}>
      <div className="panel-heading">
        <h2>{title}</h2>
        {detail && <span>{detail}</span>}
      </div>
      {children}
    </section>
  );
}
function Shell({
  page,
  children,
}: {
  page: "desk" | "ledger";
  children: ReactNode;
}) {
  return (
    <>
      <a className="skip-link" href="#workspace-content">
        Skip to content
      </a>
      <PortalHeader />
      <main id="workspace-content" className="workspace">
        {mock ? (
          children
        ) : (
          <Panel title="Live integration pending">
            <p>
              These screens currently support fixture mode. Set VITE_MOCK=1 and
              restart Vite to review them.
            </p>
          </Panel>
        )}
      </main>
    </>
  );
}
function ProbabilityChart() {
  return <GroupChart result={result} reference={risk.probability_acaps} />;
}
function Regions() {
  const safe = result.agreement_by_region.filter(
    (region) => region.n >= 3 && region.mean !== null,
  );
  return (
    <div className="region-layout">
      <svg
        viewBox="0 0 150 190"
        className="chad-map"
        role="img"
        aria-label="Schematic locator for eastern Chad; boundaries and locations are illustrative"
      >
        <path d="M57 9 L123 43 L119 95 L133 120 L118 148 L88 151 L72 179 L50 169 L48 149 L26 151 L18 132 L32 105 L30 60Z" />
        <circle cx="106" cy="112" r="5" />
        <circle cx="100" cy="91" r="5" />
        <text x="51" y="80">
          Chad
        </text>
      </svg>
      <div className="region-values">
        {safe.map((region) => (
          <div key={region.region}>
            <span>
              {region.region}
              <small>{region.n} answers</small>
            </span>
            <strong>{percent(region.mean!)}</strong>
          </div>
        ))}
        {spreadNote(result) && (
          <p className="region-note">{spreadNote(result)}</p>
        )}
        <p className="panel-caption">
          Other regions withheld below three answers. Map is a schematic
          locator, not a boundary dataset.
        </p>
      </div>
    </div>
  );
}
function Desk() {
  const [stage, setStage] = useState<"responses" | "interpret" | "decision">("responses");
  const [, setFrozenContract] = useState<
    import("./service").QuestionContract | null
  >(null);
  const [decision, setDecision] = useState(readDecision);
  // Saved decisions remain in the ledger; each desk visit starts a fresh arrival run.
  const [answers, setAnswers] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);
  const [decisionUse, setDecisionUse] = useState(emptyDecisionUse);
  const [note, setNote] = useState("");
  const [edit, setEdit] = useState(false);
  const [probability, setProbability] = useState("High");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [announcement, setAnnouncement] = useState("");
  const [deadlinePassed, setDeadlinePassed] = useState(false);
  const [insufficient, setInsufficient] = useState(false);
  const replay = useArrivalReplay(result.n);
  const shownAnswers = replay.active ? replay.count : answers;
  const shownRevealed = replay.active ? replay.revealed : revealed;
  function showStage(next: "responses" | "interpret" | "decision") {
    setStage(next);
    requestAnimationFrame(() => document.getElementById("case-stepper")?.scrollIntoView({ block: "start" }));
  }
  async function simulate(label: string, action: () => void) {
    setBusy(label);
    setError("");
    try {
      await new Promise((resolve) => setTimeout(resolve, 200));
      action();
    } catch {
      setError(
        "The demo could not save this decision. Please retry; your draft is still here.",
      );
    } finally {
      setBusy("");
    }
  }
  function decide(action: Decision["action"]) {
    if (!note.trim()) {
      setError("Add a decision note before continuing.");
      document.getElementById("decision-note")?.focus();
      return;
    }
    if (!completeDecisionUse(decisionUse)) {
      setError(
        "Add the decision, decision owner and deadline before continuing.",
      );
      document.getElementById(!decisionUse.what_decision.trim() ? "use-what_decision" : !decisionUse.for_whom.trim() ? "use-for_whom" : "use-by_when")?.focus();
      return;
    }
    void simulate("Saving decision", () => {
      const next: Decision = {
        action,
        probability:
          action === "edit" ? probability : draft.proposed_probability,
        note: note.trim(),
        decision_use: decisionUse,
        at: new Date().toISOString(),
      };
      sessionStorage.setItem(storageKey, JSON.stringify(next));
      setDecision(next);
      setEdit(false);
      showStage("decision");
      setAnnouncement(
        action === "reject"
          ? "Draft rejected. No ledger entry added."
          : "Decision saved. A simulated ledger entry is ready.",
      );
    });
  }
  return (
    <Shell page="desk">
      <div className="workspace-title">
        <div>
          <p className="eyebrow">Chad / {risk.risk_id}</p>
          <h1>Analyst desk</h1>
          <p>Review the panel. Decide what changes.</p>
        </div>
        <button
          onClick={() => {
            try {
              sessionStorage.removeItem(storageKey);
              replay.stop();
              setDecision(null);
              setAnswers(0);
              setRevealed(false);
              setHasDraft(false);
              setStage("responses");
              setDeadlinePassed(false);
              setInsufficient(false);
              setNote("");
              setEdit(false);
              setAnnouncement("Demo reset. No answers loaded.");
            } catch {
              setError("Browser session storage is unavailable.");
            }
          }}
        >
          <RotateCcw size={15} /> Reset round
        </button>
      </div>
      <Journey active={2} />
      <DecisionSnapshot
        rating={risk.probability_acaps}
        result={shownRevealed ? result : null}
      />
      <div className="risk-strip">
        <div>
          <span className="rating">{risk.level} risk</span>
          <h2>{risk.title}</h2>
        </div>
        <span>
          Six-month horizon
          <br />
          <small>Pulse {pulse.id}</small>
        </span>
      </div>
      <nav id="case-stepper" className="case-stepper" aria-label="Case progress">
        <a href="/alerts"><span>1</span> Signal</a>
        <button aria-current={stage === "responses" ? "step" : undefined} onClick={() => showStage("responses")}><span>2</span> Responses</button>
        <button aria-current={stage === "interpret" ? "step" : undefined} disabled={!shownRevealed} onClick={() => showStage("interpret")}><span>3</span> Interpret</button>
        <button aria-current={stage === "decision" ? "step" : undefined} disabled={!hasDraft} onClick={() => showStage("decision")}><span>4</span> Decide</button>
        <a href="/ledger" aria-disabled={!decision || decision.action === "reject"} onClick={e => { if (!decision || decision.action === "reject") e.preventDefault(); }}><span>5</span> Record</a>
      </nav>
      <div className="case-stage-heading">
        <div>
          <h2>{stage === "responses" ? "Collect independent answers" : stage === "interpret" ? "What does the panel tell us?" : "Make and record the call"}</h2>
          <p>{stage === "responses" ? "Answers stay sealed until the fixed deadline. The demo can load eight sample answers." : stage === "interpret" ? "Compare the mean with the spread, disagreements and missing evidence before deciding." : "Review the cited draft, name its intended use and record your rationale."}</p>
        </div>
        {stage === "interpret" && <button className="primary" onClick={() => { setHasDraft(true); showStage("decision"); }}>Continue to decision <ArrowRight size={15} /></button>}
        {stage === "decision" && decision && decision.action !== "reject" && <a className="button-link primary" href="/ledger">Open ledger record <ArrowRight size={15} /></a>}
      </div>
      {stage === "interpret" && (
        <div className="case-insight">
          <strong>{Math.round(result.mean * 100)}% is the panel average, not a consensus.</strong>
          <p>Estimates range from {Math.round(result.spread.min * 100)}% to {Math.round(result.spread.max * 100)}%. Read the disagreement and missing evidence before choosing what to change.</p>
        </div>
      )}
      {stage === "decision" && !decision && (
        <div className="case-insight">
          <strong>The draft proposes {draft.proposed_probability} probability.</strong>
          <p>Check its citations and open claims, then record what decision this assessment will inform, who owns it and when it is needed.</p>
        </div>
      )}
      <div data-stage={stage} className={`desk-grid demo-case ${replay.active ? "replaying" : ""}`}>
        <div className="desk-main">
          {replay.active && (
            <ArrivalForecast
              count={replay.count}
              reference={risk.probability_acaps}
            />
          )}
          <Panel
            className="response-panel"
            title={
              shownRevealed ? "Revealed responses" : "Sealed envelope tray"
            }
            detail={`${replay.active ? "Arrival replay" : "Round 1"} · ${shownAnswers} of ${result.n} answers`}
          >
            <ResponseProgress
              total={result.n}
              count={shownAnswers}
              revealed={shownRevealed}
            />
            <div className="panel-actions">
              {!replay.active ? (
                <button
                  disabled={!!busy}
                  onClick={() => {
                    replay.start();
                    setDeadlinePassed(false); setInsufficient(false);
                    scrollToDeskSection("arrival-forecast");
                  }}
                >
                  Simulate arrivals
                </button>
              ) : (
                <>
                  {replay.count < result.n && (
                    <button onClick={replay.pause}>
                      {replay.playing ? "Pause arrivals" : "Resume arrivals"}
                    </button>
                  )}
                  <button className="text-button" onClick={replay.stop}>
                    Close simulation
                  </button>
                </>
              )}
              <button
                className="primary"
                disabled={insufficient || !!busy || (replay.active && !shownRevealed && replay.count < result.n)}
                onClick={() => {
                  if (!replay.active && !shownRevealed && answers < 5) {
                    void simulate("Loading answers", () => {
                      setAnswers(result.n);
                      setAnnouncement("Eight demo answers loaded. Advance to the deadline to reveal them.");
                    });
                    return;
                  }
                  if (!deadlinePassed && !shownRevealed) { setDeadlinePassed(true); setAnnouncement("Simulation clock advanced to the fixed reveal deadline."); return; }
                  if (!shownRevealed && shownAnswers < 5) { setInsufficient(true); setAnnouncement("Insufficient panel. Answers remain sealed."); return; }
                  if (shownRevealed) {
                    if (!replay.active) {
                      setHasDraft(true);
                      setAnnouncement("Draft ready for analyst review.");
                    }
                    showStage("decision");
                  }
                  else if (replay.active) {
                    replay.reveal();
                    showStage("interpret");
                  } else
                    void simulate("Revealing", () => {
                      setRevealed(true);
                      setAnnouncement(
                        "Round one revealed. Eight answers in the group view.",
                      );
                      showStage("interpret");
                    });
                }}
              >
                {shownRevealed
                  ? replay.active
                    ? "Analyse responses"
                    : hasDraft ? "Go to decision" : "Prepare draft"
                  : deadlinePassed ? "Reveal answers" : shownAnswers >= 5 ? "Advance to deadline" : replay.active ? "Waiting for answers" : "Load 8 demo answers"}
              </button>
            </div>
            {(busy || announcement) && (
              <p className="desk-action-status" role="status">{busy || announcement}</p>
            )}
            {!replay.active && (
              <details className="round-tools">
                <summary>Round tools</summary>{" "}
                <button onClick={() => {setDeadlinePassed(true); if(shownAnswers<5)setInsufficient(true);}}>Advance to deadline</button>
                <button
                  disabled={!!busy || insufficient || replay.active || answers === result.n}
                  onClick={() =>
                    void simulate("Loading answers", () => {
                      setAnswers(result.n);
                      setAnnouncement(
                        "Eight synthetic answers loaded. Ready to reveal.",
                      );
                    })
                  }
                >
                  Load answers
                </button>
              </details>
            )}
            {replay.active && (
              <div className="arrival-progress" role="status">
                <span>
                  {replay.count === result.n
                    ? "All eight answers received"
                    : replay.playing
                      ? `Answer ${replay.count} of ${result.n} received · waiting for the next expert`
                      : "Arrivals paused"}
                </span>
                <progress
                  aria-label="Expert answers received"
                  value={replay.count}
                  max={result.n}
                />
              </div>
            )}
            <p className="panel-caption">
              {shownRevealed
                ? "Responses opened together. Continue to compare the forecasts and review the evidence."
                : "Answers open at the fixed deadline, only if at least five have responded."}
            </p>
            {insufficient && <p role="status">Insufficient panel: fewer than five responses at the deadline. Nothing is revealed.</p>}
          </Panel>
          {shownRevealed && <RevealOverview result={result} rationale={note} onRationale={setNote} />}
          <Panel title="Panel coverage" className="coverage-panel">
            {" "}
            <PanelVisuals
              riskId={risk.risk_id}
              arrived={
                replay.active
                  ? replay.count
                  : answers || (revealed ? undefined : 0)
              }
            />
          </Panel>
          {replay.active && shownRevealed && (
            <AnalysisWalkthrough
              result={result}
              draft={draft}
              pulse={pulse}
              reference={risk.probability_acaps}
              hasDecision={!!decision}
              onContinue={() => {
                replay.stop();
                setAnswers(result.n);
                setRevealed(true);
                setHasDraft(true);
                showStage("decision");
              }}
            />
          )}
          {(!replay.active || !shownRevealed) && (
            <Panel
              title="Expert forecast versus ACAPS"
              className="forecast-panel"
              detail={shownRevealed ? `n = ${result.n}` : "Sealed"}
            >
              {shownRevealed && result.n >= 5 ? (
                <ProbabilityChart />
              ) : (
                <div className="empty-panel">
                  <LockKeyhole size={24} />
                  <h3>Peer views stay hidden before reveal</h3>
                  <p>Reveal the round to see the group distribution.</p>
                </div>
              )}
            </Panel>
          )}
          {!replay.active && (
            <div id="current-draft">
              <Panel
                title="Draft update"
                detail={
                  decision
                    ? `${decision.action === "accept" ? "Accepted" : decision.action === "edit" ? "Edited" : "Rejected"}`
                    : "Analyst approval required"
                }
              >
                {!hasDraft ? (
                  <div className="empty-panel">
                    <FileCheck2 size={24} />
                    <p>
                      Build a cited draft from the revealed panel and indicator
                      evidence.
                    </p>
                    <button
                      disabled={!!busy || !revealed}
                      onClick={() =>
                        void simulate("Preparing draft", () => {
                          setHasDraft(true);
                          setAnnouncement("Draft ready for analyst review.");
                          scrollToDeskSection("current-draft");
                        })
                      }
                    >
                      Prepare draft
                    </button>
                  </div>
                ) : (
                  <>
                    <DraftRecommendation
                      draft={draft}
                      current={risk.probability_acaps}
                      proposed={
                        decision?.probability || draft.proposed_probability
                      }
                    />
                    <DraftNarrative
                      showFacts={false}
                      draft={draft}
                      themes={result.missing_themes}
                      result={result}
                      evidence={pulse.evidence}
                    />
                    <div className="citations">
                      {draft.citations.map((c) => (
                        <a
                          key={c.url}
                          href={c.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {c.text} <ArrowRight size={13} />
                        </a>
                      ))}
                    </div>
                    <Verification draft={draft} />
                    {decision ? (
                      <div className="decision-log">
                        <h3>Decision log</h3>
                        <p>
                          {decision.action === "reject"
                            ? "Rejected · no ledger entry added."
                            : "Approved for the ledger."}
                        </p>
                        <p>{decision.note}</p>
                        <time>{date(decision.at)}</time>
                        {decision.action !== "reject" && (
                          <a href="/ledger">
                            View public ledger <ArrowRight size={14} />
                          </a>
                        )}
                      </div>
                    ) : (
                      <div className="decision-form">
                        {error && <p className="workspace-message error" role="alert">{error}</p>}
                        <DecisionUseFields
                          value={decisionUse}
                          onChange={setDecisionUse}
                        />
                        <label htmlFor="decision-note">Decision note</label>
                        <textarea
                          id="decision-note"
                          maxLength={500}
                          value={note}
                          onChange={(e) => {
                            setNote(e.target.value);
                            setError("");
                          }}
                          placeholder="Explain your decision for the audit trail."
                        />
                        {edit && (
                          <div className="edit-row">
                            <label htmlFor="edited-probability">
                              Edited probability
                            </label>
                            <select
                              id="edited-probability"
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
                            <p className="panel-caption">
                              Risk level remains {draft.proposed_level}; the
                              current contract only allows editing probability.
                            </p>
                          </div>
                        )}
                        <div className="panel-actions">
                          {edit ? (
                            <>
                              <button
                                className="primary"
                                disabled={!!busy}
                                onClick={() => decide("edit")}
                              >
                                Save edited decision
                              </button>
                              <button onClick={() => setEdit(false)}>
                                Cancel edit
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                className="primary"
                                disabled={!!busy}
                                onClick={() => decide("accept")}
                              >
                                Accept draft
                              </button>
                              <button
                                disabled={!!busy}
                                onClick={() => setEdit(true)}
                              >
                                Edit probability
                              </button>
                              <button
                                disabled={!!busy}
                                onClick={() => decide("reject")}
                              >
                                Reject draft
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </Panel>
            </div>
          )}
        </div>
        <aside className="desk-side">
          <details className="case-reference">
            <summary>Question, evidence and method</summary>
          <DeskContext>
            <ContextSection label="Question">
              <QuestionContractPanel
                riskId={risk.risk_id}
                onFrozen={setFrozenContract}
              />
            </ContextSection>
            <ContextSection label="Panel details">
              <PanelMatch riskId={risk.risk_id} />
            </ContextSection>
            <ContextSection label="Review notes">
              <Panel title="Published evidence" className="evidence-panel">
                {pulse.evidence.map((e, i) => (
                  <EvidenceLine key={i} value={e} />
                ))}
              </Panel>
              {shownRevealed && <IntegrityPanel pulseId={pulse.id} />}
              <Panel title="Agreement by region">
                {shownRevealed ? (
                  <Regions />
                ) : (
                  <p>Regional views open after reveal.</p>
                )}
              </Panel>
              <Panel title="What this panel could not see">
                {shownRevealed ? (
                  <CoverageAdvice result={result} />
                ) : (
                  <p>Coverage observations open after reveal.</p>
                )}
              </Panel>
            </ContextSection>
            <ContextSection label="Method">
              <Panel title="How this number was reached">
                {shownRevealed ? (
                  <MethodChain
                    result={result}
                    reference={risk.probability_acaps}
                  />
                ) : (
                  <p>The method opens after reveal.</p>
                )}
              </Panel>
            </ContextSection>
            <ContextSection label="Outcome">
              <OutcomeReportPanel pulseId={pulse.id} />
            </ContextSection>
          </DeskContext>
          </details>
        </aside>
      </div>
    </Shell>
  );
}
function Ledger() {
  const [decision] = useState(readDecision);
  const [verified, setVerified] = useState(false),
    [busy, setBusy] = useState(false),
    [query, setQuery] = useState(
      new URLSearchParams(location.search).get("risk_id") || "",
    ),
    [message, setMessage] = useState("");
  const entry = eligibleEntries[0];
  const published = decision && decision.action !== "reject" && entry;
  const matches =
    published &&
    `${entry.risk_id} ${risk.country} ${risk.title}`
      .toLowerCase()
      .includes(query.toLowerCase());
  const historyMatches =
    sampleDataEnabled() &&
    sampleRisks.some(
      (r) =>
        r.risk_id !== risk.risk_id &&
        `${r.risk_id} ${r.country} ${r.title}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    );
  return (
    <Shell page="ledger">
      <div className="workspace-title">
        <div>
          <p className="eyebrow">Group views only</p>
          <h1>Public ledger</h1>
          <p>Sealed forecasts, analyst decisions and outcomes.</p>
        </div>
        <a className="button-link" href="/desk">
          Go to analyst desk <ArrowRight size={15} />
        </a>
      </div>
      <Journey active={3} />
      <div className="ledger-toolbar">
        <label htmlFor="ledger-search">Find a risk</label>
        <input
          id="ledger-search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by country or risk ID"
        />
      </div>
      <LedgerColumns />
      {matches ? (
        <LedgerRecord
          entry={entry}
          country={risk.country}
          checked={verified || undefined}
        >
          <Panel
            title={`${risk.country} / ${entry.risk_id}`}
            detail="Analyst approved"
            className="ledger-entry"
          >
            <h3>{risk.title}</h3>
            {entry.group_probability !== result.mean && (
              <p className="panel-caption">
                Stored ledger fixture: {percent(entry.group_probability)}.
                Current v3 round mean: {percent(result.mean)}. These fixtures
                disagree; Lane A must regenerate a consistent version before
                live use.
              </p>
            )}
            <div className="ledger-stats">
              <div>
                <span>Group probability</span>
                <strong>{percent(entry.group_probability)}</strong>
                <small>{result.n} synthetic contributions</small>
              </div>
              <div>
                <span>ACAPS probability</span>
                <strong>{decision.probability}</strong>
                <small>Risk level: {entry.acaps_level}</small>
                {/* The band's own record, so a reader can judge the rating
                    against what that band has done before. */}
                {bandRate(decision.probability) && (
                  <small>
                    {asPercent(bandRate(decision.probability)!.rate)} of{" "}
                    {bandRate(decision.probability)!.n} past{" "}
                    {decision.probability} risks materialised
                  </small>
                )}
              </div>
              <div>
                <span>Outcome</span>
                <strong className="small-stat">Unresolved</strong>
                <small>Not scored yet</small>
              </div>
            </div>
            <HonestyBox
              context={`${entry.risk_id} / ${entry.pulse_id}`}
              value={{
                ...entry.honesty!,
                decision_use:
                  decision?.decision_use || entry.honesty!.decision_use,
              }}
            />
            <VerificationTrail
              entry={entry}
              fixture
              decision={decision}
              receipt={verified ? { valid: true, anchor: null } : undefined}
            />
            <dl className="ledger-details">
              <div>
                <dt>Sealed at</dt>
                <dd>{date(entry.sealed_at)}</dd>
              </div>
              <div>
                <dt>Analyst decision</dt>
                <dd>
                  {decision.action === "edit" ? "Edited" : "Accepted"} ·{" "}
                  {date(decision.at)}
                </dd>
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
                className={verified ? "verified-button" : ""}
                disabled={busy || verified}
                onClick={async () => {
                  setBusy(true);
                  await new Promise((resolve) => setTimeout(resolve, 200));
                  const receipt = verifyFixture(entry.verify_hash);
                  setVerified(receipt.valid);
                  setMessage(
                    receipt.valid
                      ? "Fixture hash matched. No blockchain anchor is configured."
                      : "Hash did not match the fixture.",
                  );
                  setBusy(false);
                }}
              >
                {verified ? <Check size={16} /> : <ShieldCheck size={16} />}{" "}
                {busy
                  ? "Checking fixture…"
                  : verified
                    ? "Fixture verified"
                    : "Verify fixture hash"}
              </button>
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(entry.verify_hash);
                    setMessage("Verification hash copied.");
                  } catch {
                    setMessage(
                      "Copy unavailable. Select and copy the hash above.",
                    );
                  }
                }}
              >
                <Copy size={15} /> Copy hash
              </button>
            </div>
            <p className="panel-caption">
              Verification matches this entry against the fixture receipt. It is
              not a cryptographic proof or blockchain transaction. Anchor: none.
            </p>
          </Panel>
        </LedgerRecord>
      ) : historyMatches ? null : (
        <Panel
          title={
            published ? "No matching risks" : "No approved group views yet"
          }
        >
          <div className="empty-panel">
            <Inbox size={28} />
            <p>
              {published
                ? "Try a country name or risk ID such as Chad or R1043."
                : "Reveal the panel and accept or edit the draft on the analyst desk to add a simulated entry."}
            </p>
            {published ? (
              <button onClick={() => setQuery("")}>Clear search</button>
            ) : (
              <a href="/desk">
                Review pending pulse <ArrowRight size={14} />
              </a>
            )}
          </div>
        </Panel>
      )}
      <HistoricalLedger query={query} />
      <p className="panel-caption ledger-privacy">
        Only aggregates with at least five confirmed contributions are eligible.
        Historical entries retain resolved outcomes and their honesty data.
      </p>
      <p className="workspace-message" role="status">
        {message}
      </p>
    </Shell>
  );
}
export function Workspace({ page }: { page: "desk" | "ledger" }) {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const id = setTimeout(() => setReady(true), 100);
    return () => clearTimeout(id);
  }, []);
  useEffect(() => {
    document.title = `${page === "desk" ? "Analyst desk" : "Public ledger"} | Sealed Signals`;
  }, [page]);
  return ready ? (
    page === "desk" ? (
      <Desk />
    ) : (
      <Ledger />
    )
  ) : (
    <div className="workspace" role="status">
      Opening {page === "desk" ? "analyst desk" : "public ledger"}…
    </div>
  );
}
