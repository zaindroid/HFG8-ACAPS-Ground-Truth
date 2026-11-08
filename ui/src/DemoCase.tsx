import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Activity, ArrowRight, ArrowLeft, Check, LockKeyhole, RotateCcw, ExternalLink, Smartphone, UserRound } from "lucide-react";
import { PortalHeader } from "./PortalHeader";
import { draft, readDecision, result, risk, storageKey, type Decision } from "./desk-model";
import { demoRisks, type DemoRisk } from "./demo-risk-data";
import { countDemoAnswers, invitationsForRisk, loadDemoState, resetDemoInvitations, sharedDemo } from "./demo-invitations";
import { bandFor, buildPanelResult, liveDirectory, livePanel, liveQuestion, liveSeats, type PanelResult } from "./live-panel";
import { type LiveAnalysis, type LiveSubmission, loadSubmissions } from "./live-seats";
import { ExpertRoster, LiveRoster, RiskSelect } from "./DemoRiskFlow";
import "./demo-case.css";

type Step = "signal" | "experts" | "panel" | "decision" | "record";
const steps: { id: Step; label: string }[] = [
  { id: "signal", label: "Risks" },
  { id: "experts", label: "Experts" },
  { id: "panel", label: "Responses" },
  { id: "decision", label: "Decision" },
  { id: "record", label: "Record" },
];
const pct = (n: number) => `${Math.round(n * 100)}%`;
const revealKey = "sealed-signals-demo-revealed-v1";
const sampleAnswersKey = "sealed-signals-demo-sample-answers-v1";
const recordHashKey = "sealed-signals-demo-record-hash-v1";
const liveRevealKey = "sealed-signals-live-revealed-v1";
const livePlayedKey = "sealed-signals-live-recorded-played-v1";
// The auto-advance off the seat screen fires once per run. Without this it would drag the
// analyst back out of Responses every time they stepped back to show the codes again.
const liveJumpedKey = "sealed-signals-live-jumped-v1";
async function fingerprint(value: Decision) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(value)));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function SeverityChart() {
  return <div className="dc-severity-chart">
    <div className="dc-chart-values"><span>Mar 2026<strong>6.1</strong></span><span className="dc-chart-change">+0.8</span><span>Apr 2026<strong>6.9</strong></span></div>
    <svg viewBox="0 0 700 220" role="img" aria-label="INFORM Severity rose from 6.1 in March 2026 to 6.9 in April 2026">
      <path className="dc-gridline" d="M34 45H666M34 105H666M34 165H666" />
      <path className="dc-trend" d="M45 162C150 157 220 149 295 144S390 134 445 111S555 66 655 48" />
      <circle cx="45" cy="162" r="7" /><circle cx="655" cy="48" r="8" />
    </svg>
    <div className="dc-chart-foot"><span>INFORM Severity Index · Chad</span><a href="https://www.acaps.org/en/countries/chad" target="_blank" rel="noreferrer">ACAPS source <ExternalLink size={14}/></a></div>
  </div>;
}

function Distribution({ panel, compact = false }: { panel: PanelResult; compact?: boolean }) {
  const max = Math.max(1, ...panel.distribution.map((item) => item.count));
  const low = Math.round(panel.spread.min * 100), high = Math.round(panel.spread.max * 100);
  return <div className={`dc-distribution ${compact ? "dc-compact" : ""}`} role="img" aria-label={`${panel.n_estimates} forecasts, average ${pct(panel.mean)}, range ${pct(panel.spread.min)} to ${pct(panel.spread.max)}`}>
    <div className="dc-bars">{panel.distribution.map((item) => <div className="dc-bar-cell" key={item.bucket}><span className="dc-bar-count">{item.count || ""}</span><span className="dc-bar" style={{ height: `${Math.max(5, (item.count / max) * 100)}%` }} /><span className="dc-bar-label">{Math.round(Number(item.bucket.split("-")[0]) * 100)}–{Math.round(Number(item.bucket.split("-")[1]) * 100)}%</span></div>)}</div>
    <div className="dc-range"><span>{low}%</span><div><i style={{ left: `${low}%`, right: `${100 - high}%` }} /><b style={{ left: `${Math.round(panel.mean * 100)}%` }} /></div><span>{high}%</span></div>
    <div className="dc-range-key"><span>Forecast range</span><strong>● Average {pct(panel.mean)}</strong></div>
  </div>;
}

function ResponseInsights({ analysis, legacy = false }: { analysis?: LiveAnalysis | null; legacy?: boolean }) {
  const regions = legacy ? result.agreement_by_region : analysis?.regions || [];
  const concerns = legacy
    ? result.missing_themes.filter((item) => !item.text_withheld).map((item) => ({ topic: item.theme, n: item.count }))
    : analysis?.concerns || [];
  return <section className="dc-insights" aria-label="Panel analysis">
    <div className="dc-insights-heading"><div><span className="dc-label">PANEL ANALYSIS</span><h2>Where the panel sees it differently</h2></div><span>Group patterns · no named answers</span></div>
    <div className="dc-insights-grid">
      <article className="dc-card dc-insight-card"><span className="dc-label">GEOGRAPHIC VIEW</span><h3>Regional forecasts</h3><div className="dc-region-list">{regions.map((row) => <div className="dc-region" key={row.region}><div><strong>{row.region}</strong><small>{row.n} estimates</small></div>{row.mean !== null && row.n >= 3 ? <><div className="dc-region-track"><i style={{ width: `${Math.round(row.mean * 100)}%` }}/></div><b>{pct(row.mean)}</b></> : <span className="dc-insight-muted">Withheld</span>}</div>)}</div><p className="dc-insight-foot">Regional averages appear with at least three estimates.</p></article>
      <article className="dc-card dc-insight-card"><span className="dc-label">AGREEMENT & DISAGREEMENT</span><h3>{legacy ? "Different readings of the risk" : "Where views align"}</h3>{legacy
        ? <div className="dc-dissent-list">{result.disagreement.map((item, i) => <p key={i}><span className={item.position === "higher" ? "dc-high" : "dc-low"}/>{item.summary}</p>)}</div>
        : <div className="dc-topic-list">{analysis?.topics.map((topic) => <div className="dc-topic" key={topic.topic}><div><strong>{topic.topic}</strong><small>{topic.n} relevant estimates</small></div>{topic.higher !== null && topic.lower !== null ? <><div className="dc-topic-track" role="img" aria-label={`${topic.higher} higher likelihood, ${topic.lower} lower likelihood`}><i style={{ width: `${topic.n ? topic.higher / topic.n * 100 : 0}%` }}/></div><span>{topic.lower && topic.higher ? "Split" : "Aligned"}</span></> : <span className="dc-insight-muted">Limited coverage</span>}</div>)}</div>}
        {!legacy && <p className="dc-insight-foot">Higher means at least 50% likelihood. Themes with fewer than three estimates show coverage only.</p>}</article>
      <article className="dc-card dc-insight-card dc-concerns"><span className="dc-label">WHAT EXPERTS SAY IS MISSING</span><h3>Check before deciding</h3><div className="dc-concern-list">{concerns.length ? concerns.map((item) => <div key={item.topic}><span className="dc-concern-dot"/><strong>{item.topic}</strong><span>{item.n} {item.n === 1 ? "mention" : "mentions"}</span></div>) : <p>No concern was recorded.</p>}</div><p className="dc-insight-foot">Mentions are signals to verify, not confirmed facts.{legacy ? " Single-expert wording remains withheld." : " Live notes are grouped by topic."}</p></article>
    </div>
  </section>;
}

function StepHeader({ step, risk: current, onBack, onAction }: { step: Step; risk: DemoRisk; onBack?: () => void; onAction?: () => void }) {
  const copy = {
    signal: ["01 / RISKS", "Select a risk", "Choose a current risk to review"],
    experts: ["02 / EXPERTS", "Choose experts", "Review available profiles"],
    panel: ["03 / RESPONSES", "Expert responses", current.live ? `Live round · ${liveDirectory.length} recorded answers, ${liveSeats.length} seats in the room` : "Round 1 · eight invited experts"],
    decision: ["04 / DECISION", "Make the call", "Review the result and record your decision"],
    record: ["05 / RECORD", "Decision record", `${current.country} · Risk ${current.risk_id}`],
  }[step];
  return <div className="dc-head"><div>{onBack && <button className="dc-back" onClick={onBack}><ArrowLeft size={15}/> Back</button>}<p className="dc-kicker">{copy[0]}</p><h1>{copy[1]}</h1><p className="dc-subtitle">{copy[2]}</p></div>{onAction ? <button className="dc-primary" onClick={onAction}>Review expert panel <ArrowRight size={17}/></button> : <span className="dc-case-tag">{current.risk_id} <span>·</span> {current.country.toUpperCase()}</span>}</div>;
}

/**
 * The live round's responses, arriving one at a time.
 *
 * The recorded five are played in rather than appearing at once, because the thing worth
 * watching is a panel filling up: a response is an event, and eight of them landing together
 * reads as a page load. The three seats then land when the people holding them actually
 * confirm, which is not something this screen controls -- it polls, and shows each one as it
 * arrives. No value is shown before the reveal, including to the analyst: the arrival says
 * that somebody answered, not what they said.
 */
const RECORDED_STEP_MS = 1200;
const LIVE_STEP_MS = 900;
/** The disclosure floor, same as the ledger's and the fixture validator's: no aggregate under five. */
const PANEL_FLOOR = 5;
function useLivePanel(active: boolean) {
  const [recorded, setRecorded] = useState(() => (sessionStorage.getItem(livePlayedKey) === "yes" ? liveDirectory.length : 0));
  const [submissions, setSubmissions] = useState<LiveSubmission[]>([]);
  const [liveEstimates, setLiveEstimates] = useState<number[] | null>(null);
  const [analysis, setAnalysis] = useState<LiveAnalysis | null>(null);
  const [shownLive, setShownLive] = useState(0);
  const [revealed, setRevealed] = useState(() => sessionStorage.getItem(liveRevealKey) === "yes");
  const [error, setError] = useState("");
  const played = recorded >= liveDirectory.length;
  useEffect(() => {
    if (!active || played) return;
    const timer = window.setTimeout(() => setRecorded((n) => {
      const next = Math.min(liveDirectory.length, n + 1);
      if (next === liveDirectory.length) sessionStorage.setItem(livePlayedKey, "yes");
      return next;
    }), RECORDED_STEP_MS);
    return () => window.clearTimeout(timer);
  }, [active, recorded, played]);
  useEffect(() => {
    if (!active) return;
    let alive = true;
    const refresh = () => loadSubmissions().then((value) => { if (alive) { setSubmissions(value.submissions); setLiveEstimates(value.liveEstimates); setAnalysis(value.analysis); setError(""); } }).catch((e) => { if (alive) setError((e as Error).message); });
    void refresh();
    const timer = window.setInterval(() => void refresh(), 2000);
    window.addEventListener("focus", refresh);
    return () => { alive = false; window.clearInterval(timer); window.removeEventListener("focus", refresh); };
  }, [active]);
  // The live answers queue behind the recorded ones and behind each other, so two arriving in
  // the same poll are still two separate events on screen.
  //
  // They also queue behind their own values. The server holds the three estimates back until all
  // three seats are in and then releases them sorted, so that no figure can be matched to the
  // person who gave it. Counting a row in before its value exists would mean the row lands, the
  // average sits still, and then the average jumps by three answers at once -- the opposite of
  // what the screen is for. So the walk is gated on the values being there: once they are, the
  // rows and the arithmetic advance together, one step each.
  const valuesReady = liveEstimates?.length || 0;
  useEffect(() => {
    if (!played || shownLive >= Math.min(submissions.length, valuesReady)) return;
    const timer = window.setTimeout(
      () => setShownLive((n) => Math.min(submissions.length, valuesReady, n + 1)),
      LIVE_STEP_MS,
    );
    return () => window.clearTimeout(timer);
  }, [played, shownLive, submissions.length, valuesReady]);
  useEffect(() => { if (shownLive > submissions.length) setShownLive(submissions.length); }, [submissions.length, shownLive]);
  const seated = submissions.slice(0, shownLive);
  // One arrival, one change. The recorded five are in the browser already, so their values can
  // be added as each lands. The three from the room arrive as a sorted set once all three are
  // in -- that is what keeps a value from being matched to the person who gave it -- and they
  // are added one at a time in that sorted order, so the room watches the number move three
  // times without any step saying whose answer moved it.
  const estimates = [
    ...liveDirectory.slice(0, recorded).map((expert) => expert.answer.probability),
    ...(liveEstimates || []).slice(0, shownLive),
  ];
  const complete = played && shownLive >= liveSeats.length;
  return {
    recorded, seated, shownLive, played, complete, revealed, error, analysis,
    shown: recorded + shownLive,
    // How many seats have actually confirmed, which runs ahead of how many have been counted
    // while the values are still held. The screen says both, because they are different facts.
    confirmed: submissions.length,
    total: liveDirectory.length + liveSeats.length,
    panel: buildPanelResult(estimates, recorded + shownLive),
    reveal() { sessionStorage.setItem(liveRevealKey, "yes"); setRevealed(true); },
    reset() {
      sessionStorage.removeItem(liveRevealKey);
      sessionStorage.removeItem(livePlayedKey);
      setRecorded(0); setShownLive(0); setSubmissions([]); setLiveEstimates(null); setAnalysis(null); setRevealed(false); setError("");
    },
  };
}
type LivePanelState = ReturnType<typeof useLivePanel>;

function LiveResponses({ live, onDecision }: { live: LivePanelState; onDecision: () => void }) {
  const feed = useRef<HTMLOListElement>(null);
  const arrivals = [
    ...liveDirectory.slice(0, live.recorded).map((expert) => ({ key: expert.expert_id, name: expert.pseudonym, detail: `${expert.affiliation_tag.toUpperCase()} · ${expert.region}`, live: false })),
    ...live.seated.map((item) => {
      const seat = liveSeats.find((candidate) => candidate.token === item.token);
      return { key: item.token, name: seat?.label || "Open seat", detail: `${seat?.expertise || "Live expert"} · ${seat?.region || "In the room"}`, live: true };
    }),
  ];
  useEffect(() => { feed.current?.lastElementChild?.scrollIntoView({ block: "nearest" }); }, [arrivals.length]);
  // The aggregate appears at five answers and not before. It is the same floor the rest of the
  // system uses -- the ledger refuses an aggregate under five, and so does fixture validation --
  // and it is what makes a figure that moves with each arrival safe to show: under five, a mean
  // that changes is close to reading out the answer that changed it.
  const counted = live.panel.n_estimates;
  const open = counted >= PANEL_FLOOR;
  const step = live.shown;
  return <div className="dc-panel-layout">
    <div className="dc-card dc-panel-primary"><div className="dc-card-top"><span className="dc-label">PANEL RESPONSES</span><span className="dc-pill">{live.revealed ? <><Check size={13}/> Recorded</> : open ? <><Activity size={13}/> Updating as answers arrive</> : <><LockKeyhole size={13}/> Held under {PANEL_FLOOR} answers</>}</span></div>
      {open
        ? <>
            <div className="dc-result-hero"><strong key={step}>{pct(live.panel.mean)}</strong><span>Average forecast<br/><b key={`n-${step}`}>{counted} of {live.total} answers counted</b></span></div>
            <Distribution key={step} panel={live.panel}/>
            <p className="dc-live-note">{live.complete
              ? `${liveSeats.length} of these answers were given in the room; the other ${liveDirectory.length} were recorded for this demo. Every answer counts the same in the average.`
              : `The average moves with every answer that lands. The ${liveSeats.length} answers from the room are counted in a fixed order that is not the order they were given, so no figure here can be traced to the person who gave it.`}</p>
          </>
        : <div className="dc-sealed"><div className="dc-envelopes" aria-label={`${live.shown} of ${live.total} answers in`}>{Array.from({ length: live.total }, (_, i) => <span key={i} className={i >= live.shown ? "waiting" : ""}>{i < live.shown ? <Check size={17}/> : <LockKeyhole size={14}/>}</span>)}</div><strong>{live.shown} of {live.total} in</strong><p>No average is shown under {PANEL_FLOOR} answers, because a figure that moved on the fourth would be close to reading it out.</p></div>}
      <ol className="dc-feed dc-feed-compact" ref={feed} aria-live="polite" aria-label="Responses as they arrive">
        {arrivals.map((item) => <li key={item.key} className={item.live ? "dc-feed-live" : ""}><span className="dc-feed-mark">{item.live ? <Smartphone size={15}/> : <UserRound size={15}/>}</span><span><strong>{item.name}</strong><small>{item.detail}</small></span><span className="dc-feed-state"><Check size={14}/> Counted</span></li>)}
        {Array.from({ length: Math.max(0, live.total - arrivals.length) }, (_, i) => {
          const seat = liveSeats[live.shownLive + i];
          const held = live.played && live.shownLive + i < live.confirmed;
          return <li key={`waiting-${i}`} className="dc-feed-waiting"><span className="dc-feed-mark"><LockKeyhole size={14}/></span><span><strong>{live.played ? `${seat?.label || "Open seat"} · ${held ? "confirmed" : "waiting"}` : "Waiting"}</strong><small>{!live.played ? "Recorded answer still loading" : held ? `Held until all ${liveSeats.length} seats are in` : "Nobody has confirmed this seat yet"}</small></span></li>;
        })}
      </ol>
    </div>
    <aside className="dc-card dc-panel-side"><span className="dc-label">LIVE ROUND</span><div className="dc-metric"><strong key={`c-${step}`}>{live.shown}/{live.total}</strong><span>answers confirmed</span></div><div className="dc-progress-track"><span style={{ width: `${(live.shown / live.total) * 100}%` }}/></div>
      <div className="dc-divider"/>
      <div className="dc-facts">
        <div><span>Average</span><strong key={`m-${step}`}>{open ? pct(live.panel.mean) : "—"}</strong></div>
        <div><span>Range</span><strong key={`r-${step}`}>{open ? `${pct(live.panel.spread.min)}–${pct(live.panel.spread.max)}` : "—"}</strong></div>
        <div><span>Recorded</span><strong>{live.recorded} of {liveDirectory.length}</strong></div>
        <div><span>Seats confirmed</span><strong key={`s-${live.confirmed}`}>{live.confirmed} of {liveSeats.length}</strong></div>
      </div>
      {live.error && <p className="dc-message" role="alert">{live.error}</p>}
      {live.revealed
        ? <button className="dc-primary dc-full" onClick={onDecision}>Make decision <ArrowRight size={17}/></button>
        : <button className="dc-primary dc-full" disabled={!live.complete} onClick={live.reveal}>{live.complete ? "Record this result" : live.confirmed < liveSeats.length ? `Waiting for ${liveSeats.length - live.confirmed} of ${liveSeats.length} seats` : "Counting the answers in" } <ArrowRight size={17}/></button>}
    </aside>
  </div>;
}

export function DemoCase({ initial = "signal" }: { initial?: Step }) {
  const [step, setStep] = useState<Step>(initial);
  const [selectedRisk, setSelectedRisk] = useState<DemoRisk>(demoRisks[0]);
  const [linksReady, setLinksReady] = useState(() => !sharedDemo && invitationsForRisk("R1043").length === 8);
  const [sampleLoaded, setSampleLoaded] = useState(() => sessionStorage.getItem(sampleAnswersKey) === "yes");
  const [confirmedCount, setConfirmedCount] = useState(() => countDemoAnswers("R1043"));
  const [revealed, setRevealed] = useState(() => sessionStorage.getItem(revealKey) === "yes" || !!readDecision());
  const [decision, setDecision] = useState<Decision | null>(readDecision);
  const [choice, setChoice] = useState<Decision["action"]>(() => readDecision()?.action || "accept");
  const [probability, setProbability] = useState(() => readDecision()?.probability || "High");
  const [use, setUse] = useState(() => readDecision()?.decision_use?.what_decision || "");
  const [owner, setOwner] = useState(() => readDecision()?.decision_use?.for_whom || "");
  const [deadline, setDeadline] = useState(() => readDecision()?.decision_use?.by_when || "");
  const [note, setNote] = useState(() => readDecision()?.note || "");
  const [message, setMessage] = useState("");
  const [verification, setVerification] = useState("");
  const isLive = !!selectedRisk.live;
  const live = useLivePanel(isLive && step === "panel");
  const panelResult: PanelResult = isLive ? live.panel : result;
  const proposed = isLive ? bandFor(live.panel.mean) : draft.proposed_probability;
  const opened = isLive ? live.revealed : revealed;
  const panelOpen = isLive || linksReady;
  const recordReady = !!decision && decision.action !== "reject";
  useEffect(() => { document.title = `${steps.find((s) => s.id === step)?.label} | Sealed Signals`; }, [step]);
  useEffect(() => { const refresh = async () => { try { const value = await loadDemoState("R1043"); setConfirmedCount(value.confirmedCount); setLinksReady(value.invitations.length === 8); } catch { /* The roster displays a retry when the shared server is unavailable. */ } }; void refresh(); window.addEventListener("focus", refresh); window.addEventListener("storage", refresh); const timer = sharedDemo ? window.setInterval(refresh, 3000) : undefined; return () => { window.removeEventListener("focus", refresh); window.removeEventListener("storage", refresh); if (timer) window.clearInterval(timer); }; }, []);
  const shownAnswers = sampleLoaded ? result.n : confirmedCount;
  function go(next: Step) {
    if (next === "panel" && !panelOpen) return;
    if (next === "decision" && !opened) return;
    if (next === "record" && !recordReady) return;
    setStep(next);
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  // Called by the seat screen once every code has been picked up. There is nothing left to do
  // on that screen at that point, and the first answers are about to land on this one.
  const jumpToResponses = useCallback(() => {
    sessionStorage.setItem(liveJumpedKey, "yes");
    setStep("panel");
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);
  function reset() {
    sessionStorage.removeItem(revealKey);
    sessionStorage.removeItem(sampleAnswersKey);
    sessionStorage.removeItem(storageKey);
    sessionStorage.removeItem(recordHashKey);
    sessionStorage.removeItem(liveJumpedKey);
    resetDemoInvitations(); live.reset();
    if (!sharedDemo) { setLinksReady(false); setConfirmedCount(0); } setSampleLoaded(false); setSelectedRisk(demoRisks[0]); setRevealed(false); setDecision(null); setChoice("accept"); setProbability("High"); setUse(""); setOwner(""); setDeadline(""); setNote(""); setMessage(""); setVerification(""); go("signal");
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!use.trim() || !owner.trim() || !deadline || !note.trim()) { setMessage("Complete all fields to save the decision."); return; }
    const next: Decision = { action: choice, probability: choice === "edit" ? probability : proposed, note: note.trim(), decision_use: { what_decision: use.trim(), for_whom: owner.trim(), by_when: deadline }, at: new Date().toISOString() };
    sessionStorage.setItem(storageKey, JSON.stringify(next));
    sessionStorage.setItem(recordHashKey, await fingerprint(next));
    setDecision(next); setMessage(""); setVerification("");
    if (choice !== "reject") { setStep("record"); window.scrollTo({ top: 0, behavior: "instant" }); } else setMessage("Decision saved. This case will not be published.");
  }
  async function verifyRecord() {
    if (!decision) return;
    const saved = sessionStorage.getItem(recordHashKey);
    setVerification(saved && saved === await fingerprint(decision)
      ? "Matches this browser's demo fingerprint. No independent timestamp is connected."
      : "This record does not match a saved demo fingerprint.");
  }
  return <><a className="skip-link" href="#case-content">Skip to content</a><PortalHeader/><main className="dc-shell" id="case-content">
    <div className="dc-utility"><span><span className="dc-status-dot"/> DEMO WORKSPACE</span><button onClick={reset}><RotateCcw size={14}/> {sharedDemo ? "Restart view" : "Reset case"}</button></div>
    <nav className="dc-steps" aria-label="Case steps">{steps.map((item, i) => <button key={item.id} className={step === item.id ? "active" : ""} aria-current={step === item.id ? "step" : undefined} disabled={(item.id === "panel" && !panelOpen) || (item.id === "decision" && !opened) || (item.id === "record" && !recordReady)} onClick={() => go(item.id)}><span>{String(i + 1).padStart(2, "0")}</span>{item.label}</button>)}</nav>
    {step === "signal" && <RiskSelect value={selectedRisk} onSelect={(next) => { setSelectedRisk(next); setLinksReady(next.risk_id === "R1043" ? linksReady : false); if (next.risk_id !== selectedRisk.risk_id) { sessionStorage.removeItem(storageKey); sessionStorage.removeItem(revealKey); setDecision(null); setRevealed(false); } }} onContinue={() => go("experts")}/>}
    {step === "experts" && (isLive
      ? <LiveRoster risk={selectedRisk} onBack={() => go("signal")} onContinue={() => go("panel")} onAllSeatsTaken={jumpToResponses}/>
      : <ExpertRoster risk={selectedRisk} onBack={() => go("signal")} onReady={() => setLinksReady(true)} onContinue={() => go("panel")}/>)}
    {step === "panel" && <section className="dc-view">
      <StepHeader step="panel" risk={selectedRisk} onBack={() => go("experts")}/>
      <div className="dc-question dc-card"><span className="dc-label">QUESTION</span><h2>{isLive ? liveQuestion.text : "Will cross-border armed incursions from Sudan significantly worsen protection and humanitarian needs in eastern Chad by 7 May 2027?"}</h2></div>
      {isLive ? <LiveResponses live={live} onDecision={() => go("decision")}/> : <div className="dc-panel-layout">
        <div className="dc-card dc-panel-primary"><div className="dc-card-top"><span className="dc-label">PANEL RESPONSES</span><span className="dc-pill"><LockKeyhole size={13}/> {revealed ? "Opened" : "Private until deadline"}</span></div>
          {revealed ? <><div className="dc-result-hero"><strong>{pct(result.mean)}</strong><span>Average forecast<br/><b>{result.n} sample responses</b></span></div><Distribution panel={result}/></> :
          <div className="dc-sealed"><div className="dc-envelopes" aria-label={`${shownAnswers} of ${result.n} answers ready`}>{Array.from({ length: result.n }, (_, i) => <span key={i} className={i >= shownAnswers ? "waiting" : ""}>{i < shownAnswers ? <Check size={17}/> : <LockKeyhole size={14}/>}</span>)}</div><strong>{shownAnswers} of {result.n} ready</strong><p>{sampleLoaded ? "Sample responses loaded for this demo." : `${confirmedCount} confirmed through personal links.`}</p>
            {!sampleLoaded ? <button className="dc-primary" onClick={() => { sessionStorage.setItem(sampleAnswersKey,"yes"); setSampleLoaded(true); }}>Load sample responses <ArrowRight size={17}/></button> : <button className="dc-primary" onClick={() => { sessionStorage.setItem(revealKey,"yes"); setRevealed(true); }}>Advance to reveal <ArrowRight size={17}/></button>}
          </div>}
        </div>
        <aside className="dc-card dc-panel-side"><span className="dc-label">ROUND 1</span><div className="dc-metric"><strong>{shownAnswers}/{result.n}</strong><span>answers ready</span></div><div className="dc-progress-track"><span style={{width:`${shownAnswers/result.n*100}%`}}/></div><div className="dc-divider"/><div className="dc-facts"><div><span>Panel</span><strong>8 invited experts</strong></div><div><span>Reveal</span><strong>At fixed deadline</strong></div></div>{revealed && <button className="dc-primary dc-full" onClick={() => go("decision")}>Make decision <ArrowRight size={17}/></button>}</aside>
      </div>}
      {isLive ? live.complete && live.analysis && <ResponseInsights analysis={live.analysis}/> : revealed && <ResponseInsights legacy/>}
    </section>}
    {step === "decision" && <section className="dc-view"><StepHeader step="decision" risk={selectedRisk} onBack={() => go("panel")}/><div className="dc-decision-layout"><div className="dc-card dc-evidence"><span className="dc-label">AT A GLANCE</span><div className="dc-compare"><div><span>Expert average</span><strong>{pct(panelResult.mean)}</strong></div><div><span>Expert range</span><strong>{pct(panelResult.spread.min)}–{pct(panelResult.spread.max)}</strong></div><div><span>Current rating</span><strong>{isLive ? selectedRisk.probability_acaps : risk.probability_acaps}</strong></div></div><Distribution panel={panelResult} compact/><div className="dc-divider"/><h3>Evidence to check</h3><ul className="dc-evidence-list">{(isLive ? livePanel.evidence_to_check : ["Night-time militia movements near Adré", "Registration backlog at Adré transit site"]).map((item) => <li key={item}>{item}</li>)}</ul><a href={isLive ? livePanel.source_url : draft.citations[0]?.url || "https://www.acaps.org/en/"} target="_blank" rel="noreferrer">View source <ExternalLink size={14}/></a></div><form className="dc-card dc-form" onSubmit={submit}><span className="dc-label">ANALYST DECISION</span><h2>Proposed rating: {proposed}</h2><fieldset className="dc-choice"><legend>Decision</legend>{([ ["accept",`Keep ${proposed}`], ["edit","Change rating"], ["reject","Reject proposal"] ] as const).map(([value,label]) => <label key={value} className={choice === value ? "selected" : ""}><input type="radio" name="decision" value={value} checked={choice === value} onChange={() => setChoice(value)}/>{label}</label>)}</fieldset>{choice === "edit" && <label className="dc-field">New probability rating<select value={probability} onChange={(e) => setProbability(e.target.value)}>{["Very Low","Low","Medium","High","Very High"].map((v) => <option key={v}>{v}</option>)}</select></label>}<div className="dc-field-grid"><label className="dc-field">Decision this informs<input required value={use} onChange={(e) => setUse(e.target.value)} placeholder="e.g. Pre-position relief supplies"/></label><label className="dc-field">Decision owner<input required value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="Name or team"/></label></div><label className="dc-field">Needed by<input required type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)}/></label><label className="dc-field">Reason for decision<textarea required rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Briefly explain your choice"/></label>{message && <p className="dc-message" role="status">{message}</p>}<button className="dc-primary dc-full" type="submit">Save decision <ArrowRight size={17}/></button></form></div></section>}
    {step === "record" && recordReady && <section className="dc-view"><StepHeader step="record" risk={selectedRisk} onBack={() => go("decision")}/><div className="dc-record-head dc-card"><div><span className="dc-label">GROUP RESULT</span><h2>{selectedRisk.short}</h2><span className="dc-record-meta">Risk {selectedRisk.risk_id} · Round 1 · {panelResult.n} responses</span></div><span className="dc-record-status"><Check size={16}/> Decision recorded</span></div><div className="dc-record-layout"><div className="dc-card dc-record-chart"><div className="dc-card-top"><span className="dc-label">EXPERT FORECASTS</span><strong>{pct(panelResult.mean)} average</strong></div><Distribution panel={panelResult}/></div><div className="dc-card dc-record-decision"><span className="dc-label">ANALYST DECISION</span><strong>{decision.probability}</strong><span>{decision.action === "edit" ? "Rating changed" : "Rating kept"}</span><div className="dc-divider"/><dl><div><dt>Decision</dt><dd>{decision.decision_use?.what_decision}</dd></div><div><dt>Owner</dt><dd>{decision.decision_use?.for_whom}</dd></div><div><dt>Needed by</dt><dd>{decision.decision_use?.by_when}</dd></div></dl></div></div><div className="dc-record-bottom dc-card"><div><span className="dc-label">DECISION NOTE</span><p>{decision.note}</p></div><div><span className="dc-label">STATUS</span><strong>Outcome pending</strong><p>Forecast can be assessed after {isLive ? new Date(liveQuestion.deadline).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" }) : "7 May 2027"}.</p><button className="dc-verify" onClick={() => void verifyRecord()}><Check size={15}/> Verify demo record</button>{verification && <p role="status">{verification}</p>}</div></div><div className="dc-record-foot"><span>Demo data · individual responses remain private</span><a href="/alerts">View signals <ArrowRight size={15}/></a></div></section>}
    {step === "record" && !recordReady && <section className="dc-card dc-empty"><h1>No published record</h1><p>Complete the analyst decision first.</p><button className="dc-primary" onClick={() => go(opened ? "decision" : "signal")}>Open case <ArrowRight size={16}/></button></section>}
    <footer className="dc-footer">Sealed Signals · Hackathon for Good prototype · Synthetic expert responses</footer>
  </main></>;
}
