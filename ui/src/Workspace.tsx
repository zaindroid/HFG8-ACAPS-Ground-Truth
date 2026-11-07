import { EvidenceLine } from "./Evidence";
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
  const [, setFrozenContract] = useState<
    import("./service").QuestionContract | null
  >(null);
  const [decision, setDecision] = useState(readDecision);
  const [answers, setAnswers] = useState(decision ? result.n : 0);
  const [revealed, setRevealed] = useState(!!decision);
  const [hasDraft, setHasDraft] = useState(!!decision);
  const [decisionUse, setDecisionUse] = useState(emptyDecisionUse);
  const [note, setNote] = useState("");
  const [edit, setEdit] = useState(false);
  const [probability, setProbability] = useState("High");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [announcement, setAnnouncement] = useState("");
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
      return;
    }
    if (!completeDecisionUse(decisionUse)) {
      setError(
        "Add the decision, decision owner and deadline before continuing.",
      );
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
              setDecision(null);
              setAnswers(0);
              setRevealed(false);
              setHasDraft(false);
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
        result={revealed ? result : null}
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
      <div className="desk-grid">
        <div className="desk-main">
          <Panel
            title="Sealed envelope tray"
            detail={`Round 1 · ${answers} of ${result.n} answers`}
          >
            <div
              className="envelope-tray"
              aria-label={`${answers} sealed synthetic answers`}
            >
              {Array.from({ length: result.n }, (_, i) => (
                <span
                  key={i}
                  className={i < answers ? "envelope filled" : "envelope"}
                >
                  {i < answers ? (
                    <LockKeyhole size={22} />
                  ) : (
                    <Inbox size={22} />
                  )}
                </span>
              ))}
            </div>
            <div className="panel-actions">
              <button
                disabled={!!busy || answers === result.n}
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
              <button
                className="primary"
                disabled={!!busy || answers < 5 || revealed}
                onClick={() =>
                  void simulate("Revealing", () => {
                    setRevealed(true);
                    setAnnouncement(
                      "Round one revealed. Eight answers in the group view.",
                    );
                  })
                }
              >
                Reveal round 1
              </button>
              <a href="/e/demo">
                Open expert card <ArrowRight size={14} />
              </a>
            </div>
            <p className="panel-caption">
              Answers stay sealed until the round is revealed. At least five are
              required.
            </p>
          </Panel>
          <Panel
            title="Panel distribution"
            detail={revealed ? `n = ${result.n}` : "Sealed"}
          >
            {revealed && result.n >= 5 ? (
              <ProbabilityChart />
            ) : (
              <div className="empty-panel">
                <LockKeyhole size={24} />
                <h3>Peer views stay hidden before reveal</h3>
                <p>Reveal the round to see the group distribution.</p>
              </div>
            )}
          </Panel>
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
                    })
                  }
                >
                  Prepare draft
                </button>
              </div>
            ) : (
              <>
                <DraftRecommendation draft={draft} current={risk.probability_acaps} proposed={decision?.probability || draft.proposed_probability}/>
                <DraftNarrative
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
                          Risk level remains {draft.proposed_level}; the current
                          contract only allows editing probability.
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
        <aside className="desk-side">
          <Panel title="ACAPS edition evidence">
            {pulse.evidence.map((e, i) => (
              <EvidenceLine key={i} value={e} />
            ))}
          </Panel>
          <details className="desk-support">
            <summary>Question, panel and supporting details</summary>
            <div>
              <QuestionContractPanel
                riskId={risk.risk_id}
                onFrozen={setFrozenContract}
              />
              <PanelMatch riskId={risk.risk_id} />
              {revealed && <IntegrityPanel pulseId={pulse.id} />}

              <Panel
                title="How this number was reached"
                detail={revealed ? "Seven steps" : "Sealed"}
              >
                {revealed ? (
                  <MethodChain
                    result={result}
                    reference={risk.probability_acaps}
                  />
                ) : (
                  <p className="empty-copy">
                    The method chain opens with the round.
                  </p>
                )}
              </Panel>
              <Panel
                title="Agreement by region"
                detail={revealed ? "Regional minimum n = 3" : "Sealed"}
              >
                {revealed ? (
                  <Regions />
                ) : (
                  <p className="empty-copy">
                    Regional views open with the round.
                  </p>
                )}
              </Panel>
              <Panel
                title="What this panel could not see"
                detail={revealed ? "Themes routed to expertise" : "Sealed"}
              >
                {revealed ? (
                  <CoverageAdvice result={result} />
                ) : (
                  <p className="empty-copy">Themes appear after reveal.</p>
                )}
              </Panel>
              <OutcomeReportPanel pulseId={pulse.id} />
            </div>
          </details>
        </aside>
      </div>
      {error && (
        <p className="workspace-message error" role="alert">
          {error}
        </p>
      )}
      <p className="workspace-message" role="status">
        {busy || announcement}
      </p>
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
        <LedgerRecord entry={entry} country={risk.country} checked={verified}>
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
