import { Journey, journey } from "./Journey";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowUpRight, LockKeyhole, ScanSearch, UsersRound, Scale, Fingerprint, ShieldCheck, Sparkles, Globe2, KeyRound } from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { DemoSamples } from "./DemoSamples";
import { startDemoSession, workspaceDestination } from "./workspace-session";
import { loginSharedDemo, sharedDemo } from "./demo-invitations";
import "./landing.css";

function DemoLoginButton({
  children = "Login",
}: {
  children?: React.ReactNode;
}) {
  const [error, setError] = useState("");
  const [open, setOpen] = useState(() => sharedDemo && location.hash === "#access");
  const [code, setCode] = useState("");
  return (
    <>
      <button
        className="public-login"
        onClick={() => {
          if (sharedDemo) { setOpen(true); return; }
          try {
            startDemoSession();
            location.assign(
              workspaceDestination(
                new URLSearchParams(location.search).get("next"),
              ),
            );
          } catch {
            setError(
              "Allow session storage for this site to open the demo workspace.",
            );
          }
        }}
      >
        <LockKeyhole size={15} aria-hidden="true" />
        {children}
      </button>
      {error && (
        <p className="public-login-error" role="alert">
          {error}
        </p>
      )}
      {sharedDemo && open && <div className="lp-access-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setOpen(false); }}><form className="lp-access" onSubmit={async (event) => { event.preventDefault(); setError(""); try { await loginSharedDemo(code.trim()); startDemoSession(); location.assign(workspaceDestination(new URLSearchParams(location.search).get("next"))); } catch (failure) { setError((failure as Error).message); } }}><button type="button" className="lp-access-close" onClick={() => setOpen(false)} aria-label="Close">×</button><LockKeyhole size={24}/><h2>Open analyst demo</h2><p>Enter the access code shared with your team. Experts use their personal links without this code.</p><label>Demo access code<input autoFocus type="password" value={code} onChange={(event) => setCode(event.target.value)} required/></label>{error && <p role="alert" className="public-login-error">{error}</p>}<button className="lp-access-submit" type="submit">Continue <ArrowRight size={16}/></button></form></div>}
    </>
  );
}
function ProductLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <a
      href={to}
      onClick={(event) => {
        event.preventDefault();
        if (sharedDemo) { location.assign(`/?next=${encodeURIComponent(to)}#access`); return; }
        try {
          startDemoSession();
        } catch {
          /* session storage blocked: the destination's own gate explains what to do */
        }
        location.assign(to);
      }}
    >
      {children}
    </a>
  );
}
function PortalHeader() {
  return (
    <header className="public-header">
      <a className="sealed-wordmark" href="/">
        <span className="public-brand-icon"><LockKeyhole size={21} aria-hidden="true" /></span>
        <span className="public-brand-name">sealed signals<small>Expert validation for risk analysis</small></span>
      </a>
      <nav aria-label="Portal navigation">
        <a href="#how-it-works">How it works</a>
        <a href="#latest-signal">Latest signal</a>
        <a href="https://www.acaps.org/en/" target="_blank" rel="noreferrer">ACAPS website <ArrowUpRight size={13} aria-hidden="true" /></a>
      </nav>
      <DemoLoginButton />
    </header>
  );
}
function PortalFooter() {
  return (
    <footer className="public-footer">
      <div>
        <p className="sealed-wordmark-plain">Sealed Signals</p>
        <p>
          A prototype built for the ACAPS Ground Truth challenge, Hackathon for
          Good #8. Not an ACAPS service and not affiliated with ACAPS.
        </p>
      </div>
      <div>
        <p>
          Risk and severity figures come from the ACAPS Risk Radar export and
          the ACAPS API, used under ACAPS terms of use.
        </p>
        <a href="https://www.acaps.org/en/" target="_blank" rel="noreferrer">
          Official ACAPS website <ArrowUpRight size={14} aria-hidden="true" />
        </a>
      </div>
    </footer>
  );
}

export function PublicHome() {
  useEffect(() => { document.title = "Sealed Signals · Expert validation for risk analysis"; }, []);
  return <>
    <a className="skip-link" href="#public-content">Skip to content</a>
    <PortalHeader />
    <div className="public-utility"><span>Sealed Signals / ACAPS Ground Truth challenge</span><span>Powered by published ACAPS risk data</span></div>
    <main id="public-content" className="public-home lp-page">
      <section className="lp-hero">
        <div className="lp-hero-copy"><span className="lp-overline">EXPERT VALIDATION FOR RISK ANALYSIS</span><h1>See the signal.<br/><em>Test the judgement.</em></h1><p>A change in ACAPS data starts a focused review. The analyst chooses the risk, asks matched experts, and records the decision.</p><ProductLink to="/workspace"><span className="lp-primary">Explore the demo <ArrowRight size={19}/></span></ProductLink><small>Synthetic expert profiles and answers · no account needed</small></div>
        <div className="lp-hero-visual" id="latest-signal"><div className="lp-visual-head"><span>CHAD · APRIL 2026</span><span>01 / SIGNAL</span></div><div className="lp-visual-main"><span>INFORM SEVERITY</span><div className="lp-severity"><strong>6.1</strong><ArrowRight size={25}/><strong>6.9</strong></div><svg viewBox="0 0 520 160" role="img" aria-label="Severity rose from 6.1 to 6.9"><path d="M20 125H500M20 78H500M20 32H500" className="lp-grid"/><path d="M32 119C115 114 180 112 236 105S325 90 370 70S450 39 492 27" className="lp-line"/><circle cx="32" cy="119" r="6"/><circle cx="492" cy="27" r="7"/></svg><div className="lp-visual-caption"><span>Largest change among 123 crises</span><span>+0.8 points</span></div></div><div className="lp-visual-flow"><span><UsersRound size={17}/> 8 matched experts</span><span><Scale size={17}/> Analyst decides</span></div></div>
      </section>
      <section className="lp-workflow" id="how-it-works"><div className="lp-section-title"><span className="lp-overline">THE WORKFLOW</span><h2>From change to decision.</h2></div><div className="lp-flow-grid"><article><span className="lp-icon"><ScanSearch size={21}/></span><strong>01 · Detect</strong><p>A numeric rule flags a change in ACAPS data.</p></article><article><span className="lp-icon"><KeyRound size={21}/></span><strong>02 · Ask</strong><p>Matched experts get one personal, no-login link.</p></article><article><span className="lp-icon"><UsersRound size={21}/></span><strong>03 · Compare</strong><p>Independent answers open together as a group.</p></article><article><span className="lp-icon"><Fingerprint size={21}/></span><strong>04 · Decide</strong><p>The analyst records what changed and why.</p></article></div></section>
      <section className="lp-features"><div className="lp-section-title"><span className="lp-overline">WHAT MAKES IT DIFFERENT</span><h2>Built to make judgement visible.</h2></div><div className="lp-feature-grid"><article><ScanSearch size={20}/><div><h3>ACAPS data alerts</h3><span>In demo</span></div></article><article><KeyRound size={20}/><div><h3>Personal expert links</h3><span>In demo</span></div></article><article><ShieldCheck size={20}/><div><h3>Bias-aware questionnaire</h3><span>In demo</span></div></article><article><Scale size={20}/><div><h3>Mean, spread and dissent</h3><span>In demo</span></div></article><article><Globe2 size={20}/><div><h3>Country scan</h3><span>Live engine</span></div></article><article><Sparkles size={20}/><div><h3>Cited AI draft check</h3><span>Optional prototype</span></div></article><article><Fingerprint size={20}/><div><h3>Public timestamp log</h3><span>Pending submission</span></div></article><article><LockKeyhole size={20}/><div><h3>Quantum-safe identity</h3><span>Live engine</span></div></article></div></section>
      <section className="lp-cta"><div><span className="lp-overline">TRY THE COMPLETE CASE</span><h2>Choose a risk. Ask the panel. Make the call.</h2></div><ProductLink to="/workspace"><span className="lp-primary">Open analyst demo <ArrowRight size={18}/></span></ProductLink></section>
    </main>
    <aside className="prototype-banner" aria-label="Prototype notice">Hackathon prototype for the ACAPS Ground Truth challenge. Not an ACAPS service. Expert profiles and answers are synthetic.</aside>
    <PortalFooter />
  </>;
}
export function LoginRequired() {
  useEffect(() => {
    location.replace(
      `/?next=${encodeURIComponent(location.pathname + location.search)}`,
    );
  }, []);
  return (
    <main className="login-redirect">
      <p role="status">Opening the public website…</p>
      <a
        href={`/?next=${encodeURIComponent(location.pathname + location.search)}`}
      >
        Return to the public website
      </a>
    </main>
  );
}

export function WorkspaceHome() {
  return (
    <Frame
      title="From a signal to an accountable decision"
      subtitle="One question. Independent judgement. A record you can check."
    >
      <Journey />
      <section className="journey-intro">
        <div>
          <span>Chad · R1043</span>
          <h2>Displacement from Sudan to Chad</h2>
          <p>A rise in severity raises a question for the expert panel.</p>
          <a className="button-link primary" href="/alerts">
            Start with the alert <ArrowRight size={17} />
          </a>
        </div>
        <div className="intro-change">
          <span>INFORM Severity · March → April 2026</span>
          <strong>
            6.1 <ArrowRight size={28} /> 6.9
          </strong>
          <small>+0.8 points · largest deterioration among 123 crises</small>
        </div>
      </section>
      <div className="journey-overview">
        {journey.map((step, i) => (
          <a href={step.href} key={step.href}>
            <span className="journey-number">{i + 1}</span>
            <h2>{step.title}</h2>
            <p>{step.text}</p>
            <ArrowRight size={18} aria-hidden="true" />
          </a>
        ))}
      </div>
      <details className="workspace-support">
        <summary>Workspace data and supporting tools</summary>
        <DemoSamples />
        <div className="support-links">
          <a href="/radar">Risk Radar & metrics</a>
          <a href="/reach">Reach the panel</a>
          <a href="/stage">Stage & jury access</a>
          <a href="/calibration">Calibration report</a>
          <a href="/committee">Expert committee</a>
          <a href="/apply">Expert application</a>
        </div>
      </details>
    </Frame>
  );
}
