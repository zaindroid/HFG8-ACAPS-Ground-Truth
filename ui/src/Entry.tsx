import { Journey, journey } from "./Journey";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowUpRight, LockKeyhole } from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { DemoSamples } from "./DemoSamples";
import { startDemoSession, workspaceDestination } from "./workspace-session";

function DemoLoginButton({
  children = "Login",
}: {
  children?: React.ReactNode;
}) {
  const [error, setError] = useState("");
  return (
    <>
      <button
        className="public-login"
        onClick={() => {
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
    </>
  );
}
function ProductLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <a
      href={to}
      onClick={(event) => {
        event.preventDefault();
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
  useEffect(() => {
    document.title = "Sealed Signals · Expert validation for risk analysis";
  }, []);
  return (
    <>
      <a className="skip-link" href="#public-content">
        Skip to content
      </a>
      <PortalHeader />
      <div className="public-utility"><span>Home / Ground Truth prototype</span><span>Based on ACAPS published risk data</span></div>
      {/* A landmark, not a bare paragraph: role="note" is not one, so the banner
          sat outside every landmark and tripped the page's own axe check. */}
      <aside className="prototype-banner" aria-label="Prototype notice">
        Prototype for the ACAPS Ground Truth challenge. Not an ACAPS service.
        Expert panels and their answers are synthetic.
      </aside>
      <main id="public-content" className="public-home">
        <section className="public-hero">
          <div className="public-hero-copy">
            <h1>
              <span>See the signal.</span>
              <span>Test the <em>story.</em></span>
            </h1>
            <p>
              When the numbers change, analysts need a clear way to test what
              they mean. Sealed Signals brings independent expert judgement
              into the review and keeps a trace of the decision.
            </p>
            <ProductLink to="/workspace">
              <span className="public-primary">
                Open the analyst workspace <ArrowRight size={18} aria-hidden="true" />
              </span>
            </ProductLink>
            <small className="public-hero-footnote">Demo prototype · synthetic expert panel · no ACAPS account needed</small>
          </div>
          <div id="latest-signal" className="public-feature-static">
            <p>Featured signal / Eastern Chad</p>
            <h2>When severity rises, what should change?</h2>
            <div className="public-feature-chart" role="img" aria-label="INFORM Severity increased from 6.1 in March to 6.9 in April 2026">
              <svg viewBox="0 0 420 148" preserveAspectRatio="none" aria-hidden="true"><path d="M20 112 C80 108 112 104 155 97 S235 91 279 72 S360 49 400 30"/><circle cx="20" cy="112" r="6"/><circle cx="400" cy="30" r="7"/></svg>
              <div><span>March 2026 <strong>6.1</strong></span><span>April 2026 <strong>6.9</strong></span></div>
            </div>
            <p>INFORM Severity · largest deterioration among 123 crises that month. The analyst decides whether to ask the panel.</p>
          </div>
        </section>

        <section id="how-it-works" className="public-research">
          <div className="public-section-heading">
            <div>
              <p>How it works</p>
              <h2>From a signal to an accountable decision.</h2>
            </div>
          </div>
          <div className="portal-steps">
            <article>
              <p>1 · Spot the change</p>
              <h3>The alert engine watches ACAPS&rsquo;s own monthly editions</h3>
              <p>
                Fixed numeric rules over the INFORM severity and access
                editions. It proposes; it never opens a round by itself.
              </p>
            </article>
            <article>
              <p>2 · Hear the experts</p>
              <h3>A small panel answers in about a minute</h3>
              <p>
                Each expert chooses a mask. The first round hides the current
                rating so it cannot anchor an independent answer.
              </p>
            </article>
            <article>
              <p>3 · Make the call</p>
              <h3>An analyst accepts, edits or rejects</h3>
              <p>
                Nothing publishes itself. Rejecting the panel requires a
                rationale, and the rationale is published too.
              </p>
            </article>
            <article>
              <p>4 · Check the record</p>
              <h3>The group view goes on a public ledger</h3>
              <p>
                With the spread, the coverage gaps, the unchecked claims and a
                hash anyone can verify against the sealed answers.
              </p>
            </article>
          </div>
        </section>

        <section className="public-workspace-entry">
          <div>
            <LockKeyhole size={23} aria-hidden="true" />
            <h2>Sealed Signals workspace</h2>
            <p>
              Risk alerts, panel management, the analyst desk and the decision
              ledger.
            </p>
          </div>
          <DemoLoginButton />
        </section>
      </main>
      <PortalFooter />
    </>
  );
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
