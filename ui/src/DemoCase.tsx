import { useEffect, useState, type FormEvent } from "react";
import { ArrowRight, ArrowLeft, Check, LockKeyhole, RotateCcw, ExternalLink } from "lucide-react";
import { PortalHeader } from "./PortalHeader";
import { draft, readDecision, result, risk, storageKey, type Decision } from "./desk-model";
import { demoRisks, type DemoRisk } from "./demo-risk-data";
import { countDemoAnswers, invitationsForRisk, loadDemoState, resetDemoInvitations, sharedDemo } from "./demo-invitations";
import { ExpertRoster, RiskSelect } from "./DemoRiskFlow";
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

function Distribution({ compact = false }: { compact?: boolean }) {
  const max = Math.max(...result.distribution.map((item) => item.count));
  return <div className={`dc-distribution ${compact ? "dc-compact" : ""}`} role="img" aria-label={`Eight forecasts, average ${pct(result.mean)}, range ${pct(result.spread.min)} to ${pct(result.spread.max)}`}>
    <div className="dc-bars">{result.distribution.map((item) => <div className="dc-bar-cell" key={item.bucket}><span className="dc-bar-count">{item.count || ""}</span><span className="dc-bar" style={{ height: `${Math.max(5, (item.count / max) * 100)}%` }} /><span className="dc-bar-label">{Math.round(Number(item.bucket.split("-")[0]) * 100)}–{Math.round(Number(item.bucket.split("-")[1]) * 100)}%</span></div>)}</div>
    <div className="dc-range"><span>30%</span><div><i style={{ left: "30%", right: "10%" }} /><b style={{ left: "69%" }} /></div><span>90%</span></div>
    <div className="dc-range-key"><span>Forecast range</span><strong>● Average {pct(result.mean)}</strong></div>
  </div>;
}

function StepHeader({ step, onBack, onAction }: { step: Step; onBack?: () => void; onAction?: () => void }) {
  const copy = {
    signal: ["01 / RISKS", "Select a risk", "Choose a current risk to review"],
    experts: ["02 / EXPERTS", "Choose experts", "Review available profiles"],
    panel: ["03 / RESPONSES", "Expert responses", "Round 1 · eight invited experts"],
    decision: ["04 / DECISION", "Make the call", "Review the result and record your decision"],
    record: ["05 / RECORD", "Decision record", "Chad · Risk R1043"],
  }[step];
  return <div className="dc-head"><div>{onBack && <button className="dc-back" onClick={onBack}><ArrowLeft size={15}/> Back</button>}<p className="dc-kicker">{copy[0]}</p><h1>{copy[1]}</h1><p className="dc-subtitle">{copy[2]}</p></div>{onAction ? <button className="dc-primary" onClick={onAction}>Review expert panel <ArrowRight size={17}/></button> : <span className="dc-case-tag">R1043 <span>·</span> CHAD</span>}</div>;
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
  const recordReady = !!decision && decision.action !== "reject";
  useEffect(() => { document.title = `${steps.find((s) => s.id === step)?.label} | Sealed Signals`; }, [step]);
  useEffect(() => { const refresh = async () => { try { const value = await loadDemoState("R1043"); setConfirmedCount(value.confirmedCount); setLinksReady(value.invitations.length === 8); } catch { /* The roster displays a retry when the shared server is unavailable. */ } }; void refresh(); window.addEventListener("focus", refresh); window.addEventListener("storage", refresh); const timer = sharedDemo ? window.setInterval(refresh, 3000) : undefined; return () => { window.removeEventListener("focus", refresh); window.removeEventListener("storage", refresh); if (timer) window.clearInterval(timer); }; }, []);
  const shownAnswers = sampleLoaded ? result.n : confirmedCount;
  function go(next: Step) {
    if (next === "panel" && !linksReady) return;
    if (next === "decision" && !revealed) return;
    if (next === "record" && !recordReady) return;
    setStep(next);
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  function reset() {
    sessionStorage.removeItem(revealKey);
    sessionStorage.removeItem(sampleAnswersKey);
    sessionStorage.removeItem(storageKey);
    sessionStorage.removeItem(recordHashKey);
    resetDemoInvitations(); if (!sharedDemo) { setLinksReady(false); setConfirmedCount(0); } setSampleLoaded(false); setSelectedRisk(demoRisks[0]); setRevealed(false); setDecision(null); setChoice("accept"); setProbability("High"); setUse(""); setOwner(""); setDeadline(""); setNote(""); setMessage(""); setVerification(""); go("signal");
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!use.trim() || !owner.trim() || !deadline || !note.trim()) { setMessage("Complete all fields to save the decision."); return; }
    const next: Decision = { action: choice, probability: choice === "edit" ? probability : draft.proposed_probability, note: note.trim(), decision_use: { what_decision: use.trim(), for_whom: owner.trim(), by_when: deadline }, at: new Date().toISOString() };
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
    <nav className="dc-steps" aria-label="Case steps">{steps.map((item, i) => <button key={item.id} className={step === item.id ? "active" : ""} aria-current={step === item.id ? "step" : undefined} disabled={(item.id === "panel" && !linksReady) || (item.id === "decision" && !revealed) || (item.id === "record" && !recordReady)} onClick={() => go(item.id)}><span>{String(i + 1).padStart(2, "0")}</span>{item.label}</button>)}</nav>
    {step === "signal" && <RiskSelect value={selectedRisk} onSelect={(next) => { setSelectedRisk(next); setLinksReady(next.risk_id === "R1043" ? linksReady : false); if (next.risk_id !== selectedRisk.risk_id) { sessionStorage.removeItem(storageKey); sessionStorage.removeItem(revealKey); setDecision(null); setRevealed(false); } }} onContinue={() => go("experts")}/>}
    {step === "experts" && <ExpertRoster risk={selectedRisk} onBack={() => go("signal")} onReady={() => setLinksReady(true)} onContinue={() => go("panel")}/>}
    {step === "panel" && <section className="dc-view">
      <StepHeader step="panel" onBack={() => go("experts")}/>
      <div className="dc-question dc-card"><span className="dc-label">QUESTION</span><h2>Will cross-border armed incursions from Sudan significantly worsen protection and humanitarian needs in eastern Chad by 7 May 2027?</h2></div>
      <div className="dc-panel-layout">
        <div className="dc-card dc-panel-primary"><div className="dc-card-top"><span className="dc-label">PANEL RESPONSES</span><span className="dc-pill"><LockKeyhole size={13}/> {revealed ? "Opened" : "Private until deadline"}</span></div>
          {revealed ? <><div className="dc-result-hero"><strong>{pct(result.mean)}</strong><span>Average forecast<br/><b>{result.n} sample responses</b></span></div><Distribution/></> :
          <div className="dc-sealed"><div className="dc-envelopes" aria-label={`${shownAnswers} of ${result.n} answers ready`}>{Array.from({ length: result.n }, (_, i) => <span key={i} className={i >= shownAnswers ? "waiting" : ""}>{i < shownAnswers ? <Check size={17}/> : <LockKeyhole size={14}/>}</span>)}</div><strong>{shownAnswers} of {result.n} ready</strong><p>{sampleLoaded ? "Sample responses loaded for this demo." : `${confirmedCount} confirmed through personal links.`}</p>
            {!sampleLoaded ? <button className="dc-primary" onClick={() => { sessionStorage.setItem(sampleAnswersKey,"yes"); setSampleLoaded(true); }}>Load sample responses <ArrowRight size={17}/></button> : <button className="dc-primary" onClick={() => { sessionStorage.setItem(revealKey,"yes"); setRevealed(true); }}>Advance to reveal <ArrowRight size={17}/></button>}
          </div>}
        </div>
        <aside className="dc-card dc-panel-side"><span className="dc-label">ROUND 1</span><div className="dc-metric"><strong>{shownAnswers}/{result.n}</strong><span>answers ready</span></div><div className="dc-progress-track"><span style={{width:`${shownAnswers/result.n*100}%`}}/></div><div className="dc-divider"/><div className="dc-facts"><div><span>Panel</span><strong>8 invited experts</strong></div><div><span>Reveal</span><strong>At fixed deadline</strong></div></div>{revealed && <button className="dc-primary dc-full" onClick={() => go("decision")}>Make decision <ArrowRight size={17}/></button>}</aside>
      </div>
    </section>}    {step === "decision" && <section className="dc-view"><StepHeader step="decision" onBack={() => go("panel")}/><div className="dc-decision-layout"><div className="dc-card dc-evidence"><span className="dc-label">AT A GLANCE</span><div className="dc-compare"><div><span>Expert average</span><strong>{pct(result.mean)}</strong></div><div><span>Expert range</span><strong>{pct(result.spread.min)}–{pct(result.spread.max)}</strong></div><div><span>Current rating</span><strong>{risk.probability_acaps}</strong></div></div><Distribution compact/><div className="dc-divider"/><h3>Evidence to check</h3><ul className="dc-evidence-list"><li>Night-time militia movements near Adré</li><li>Registration backlog at Adré transit site</li></ul><a href={draft.citations[0]?.url || "https://www.acaps.org/en/"} target="_blank" rel="noreferrer">View source <ExternalLink size={14}/></a></div><form className="dc-card dc-form" onSubmit={submit}><span className="dc-label">ANALYST DECISION</span><h2>Proposed rating: {draft.proposed_probability}</h2><fieldset className="dc-choice"><legend>Decision</legend>{([ ["accept","Keep High"], ["edit","Change rating"], ["reject","Reject proposal"] ] as const).map(([value,label]) => <label key={value} className={choice === value ? "selected" : ""}><input type="radio" name="decision" value={value} checked={choice === value} onChange={() => setChoice(value)}/>{label}</label>)}</fieldset>{choice === "edit" && <label className="dc-field">New probability rating<select value={probability} onChange={(e) => setProbability(e.target.value)}>{["Very Low","Low","Medium","High","Very High"].map((v) => <option key={v}>{v}</option>)}</select></label>}<div className="dc-field-grid"><label className="dc-field">Decision this informs<input required value={use} onChange={(e) => setUse(e.target.value)} placeholder="e.g. Pre-position relief supplies"/></label><label className="dc-field">Decision owner<input required value={owner} onChange={(e) => setOwner(e.target.value)} placeholder="Name or team"/></label></div><label className="dc-field">Needed by<input required type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)}/></label><label className="dc-field">Reason for decision<textarea required rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Briefly explain your choice"/></label>{message && <p className="dc-message" role="status">{message}</p>}<button className="dc-primary dc-full" type="submit">Save decision <ArrowRight size={17}/></button></form></div></section>}
    {step === "record" && recordReady && <section className="dc-view"><StepHeader step="record" onBack={() => go("decision")}/><div className="dc-record-head dc-card"><div><span className="dc-label">GROUP RESULT</span><h2>Cross-border insecurity · Eastern Chad</h2><span className="dc-record-meta">Risk R1043 · Round 1 · {result.n} responses</span></div><span className="dc-record-status"><Check size={16}/> Decision recorded</span></div><div className="dc-record-layout"><div className="dc-card dc-record-chart"><div className="dc-card-top"><span className="dc-label">EXPERT FORECASTS</span><strong>{pct(result.mean)} average</strong></div><Distribution/></div><div className="dc-card dc-record-decision"><span className="dc-label">ANALYST DECISION</span><strong>{decision.probability}</strong><span>{decision.action === "edit" ? "Rating changed" : "Rating kept"}</span><div className="dc-divider"/><dl><div><dt>Decision</dt><dd>{decision.decision_use?.what_decision}</dd></div><div><dt>Owner</dt><dd>{decision.decision_use?.for_whom}</dd></div><div><dt>Needed by</dt><dd>{decision.decision_use?.by_when}</dd></div></dl></div></div><div className="dc-record-bottom dc-card"><div><span className="dc-label">DECISION NOTE</span><p>{decision.note}</p></div><div><span className="dc-label">STATUS</span><strong>Outcome pending</strong><p>Forecast can be assessed after 7 May 2027.</p><button className="dc-verify" onClick={() => void verifyRecord()}><Check size={15}/> Verify demo record</button>{verification && <p role="status">{verification}</p>}</div></div><div className="dc-record-foot"><span>Demo data · individual responses remain private</span><a href="/alerts">View signals <ArrowRight size={15}/></a></div></section>}
    {step === "record" && !recordReady && <section className="dc-card dc-empty"><h1>No published record</h1><p>Complete the analyst decision first.</p><button className="dc-primary" onClick={() => go(revealed ? "decision" : "signal")}>Open case <ArrowRight size={16}/></button></section>}
    <footer className="dc-footer">Sealed Signals · Hackathon for Good prototype · Synthetic expert responses</footer>
  </main></>;
}








