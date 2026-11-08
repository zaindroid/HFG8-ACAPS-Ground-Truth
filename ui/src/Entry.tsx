import { Journey, journey } from "./Journey";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Bell,
  Brain,
  EyeOff,
  Fingerprint,
  Lock,
  LockKeyhole,
  LockOpen,
  ScrollText,
  Send,
  Users,
  type LucideIcon,
} from "lucide-react";
import "./landing.css";
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
function ProductLink({
  to,
  children,
}: {
  to: string;
  children: React.ReactNode;
}) {
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
        Sealed Signals<span>Expert validation for risk analysis</span>
      </a>
      <nav aria-label="Portal navigation">
        <ProductLink to="/alerts">Risk alerts</ProductLink>
        <ProductLink to="/desk">Analyst desk</ProductLink>
        <ProductLink to="/ledger">Public ledger</ProductLink>
        <ProductLink to="/trust">Trust</ProductLink>
        <a href="/e/demo">Expert card</a>
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

const loop: [LucideIcon, string, string][] = [
  [Bell, "Alert", "ACAPS severity jumps"],
  [Send, "Ask", "8 matched experts"],
  [Lock, "Answer", "Sealed, rating hidden"],
  [LockOpen, "Reveal", "Opened together"],
  [ScrollText, "Record", "Analyst decides, on the record"],
];
const features: [LucideIcon, string, string, string][] = [
  [
    EyeOff,
    "Sealed until the deadline",
    "Nobody sees an answer early, not even ACAPS.",
    "navy",
  ],
  [
    Brain,
    "Bias checks built in",
    "Rating hidden, the opposite asked, rumours tagged.",
    "blue",
  ],
  [
    Users,
    "The minority stays visible",
    "Disagreement is shown, never averaged away.",
    "teal",
  ],
  [
    Fingerprint,
    "A record nobody can edit",
    "Public timestamp log; names under post-quantum encryption.",
    "purple",
  ],
];
// Eight sealed answers drop onto the scale, then open beside the ACAPS band. Positions are the
// demo round's own answers (mean 69%); the animation stops for prefers-reduced-motion.
const answers = [30, 45, 65, 75, 80, 82, 85, 90];
function SealedPanel() {
  return (
    <figure
      className="sealed-panel"
      aria-label="Eight sealed expert answers open together: the panel says 69 percent, ACAPS rates the risk High."
    >
      <div className="sealed-top">
        <span>Chad · cross-border insecurity</span>
        <span className="sealed-chip">8 of 8 sealed</span>
      </div>
      <div className="sealed-scale" aria-hidden="true">
        <div className="sealed-band">
          <span>ACAPS High</span>
        </div>
        {answers.map((value, i) => (
          <span
            key={i}
            className="sealed-dot"
            style={{ left: `${value}%`, animationDelay: `${0.25 * i}s` }}
          />
        ))}
        <div className="sealed-mean" style={{ left: "69%" }}>
          <span>69%</span>
        </div>
        <div className="sealed-axis">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
      </div>
      <figcaption>
        <span>
          <b>Panel 69%</b> · ACAPS High · 2 disagree, kept in
        </span>
      </figcaption>
    </figure>
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
      {/* A landmark, not a bare paragraph: role="note" is not one, so the banner
          sat outside every landmark and tripped the page's own axe check. */}
      <aside className="prototype-banner" aria-label="Prototype notice">
        Prototype for the ACAPS Ground Truth challenge. Not an ACAPS service.
        Expert panels and their answers are synthetic.
      </aside>
      <PortalHeader />
      <main id="public-content" className="public-home landing">
        <section className="landing-hero">
          <div className="landing-copy">
            <h1>
              One question.
              <br />
              Independent judgement.
            </h1>
            <p className="landing-lede">
              When ACAPS data shifts, a small expert panel checks the analysis.
              Answers stay sealed until the deadline.
            </p>
            <div className="landing-actions">
              <ProductLink to="/workspace">
                <span className="public-primary">
                  Open the workspace <ArrowRight size={18} aria-hidden="true" />
                </span>
              </ProductLink>
              <a className="landing-secondary" href="/e/demo">
                Try the expert card
              </a>
            </div>
          </div>
          <SealedPanel />
        </section>

        <section className="landing-loop" aria-labelledby="loop-title">
          <h2 id="loop-title" className="landing-h2">
            Five steps, one minute for each expert
          </h2>
          <ol className="landing-steps">
            {loop.map(([Icon, label, line]) => (
              <li key={label}>
                <span className="landing-step-icon">
                  <Icon size={22} aria-hidden="true" />
                </span>
                <strong>{label}</strong>
                <span>{line}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="landing-features" aria-labelledby="features-title">
          <h2 id="features-title" className="landing-h2">
            Built so the panel can be trusted
          </h2>
          <div className="landing-tiles">
            {features.map(([Icon, title, line, tone]) => (
              <article key={title} className={`landing-tile tone-${tone}`}>
                <span className="landing-tile-icon">
                  <Icon size={26} aria-hidden="true" />
                </span>
                <h3>{title}</h3>
                <p>{line}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-numbers" aria-label="In numbers">
          <div>
            <strong>1 min</strong>
            <span>per expert answer</span>
          </div>
          <div>
            <strong>5+</strong>
            <span>experts before any result</span>
          </div>
          <div>
            <strong>0</strong>
            <span>names in anything published</span>
          </div>
        </section>

        <section className="public-workspace-entry">
          <div>
            <LockKeyhole size={23} aria-hidden="true" />
            <h2>Sealed Signals workspace</h2>
            <p>Alerts, panels, the analyst desk and the public ledger.</p>
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
          <a href="/stage">Stage & jury access</a>
          <a href="/calibration">Calibration report</a>
          <a href="/committee">Expert committee</a>
          <a href="/apply">Expert application</a>
        </div>
      </details>
    </Frame>
  );
}
