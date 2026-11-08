import { Journey, journey } from "./Journey";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  EyeOff,
  FileCheck2,
  Fingerprint,
  LockKeyhole,
  MailCheck,
  Scale,
  UserRound,
} from "lucide-react";
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
        Sealed Signals<span>Expert validation for risk analysis</span>
      </a>
      <nav aria-label="Portal navigation">
        <ProductLink to="/alerts">Risk alerts</ProductLink>
        <ProductLink to="/desk">Analyst desk</ProductLink>
        <ProductLink to="/ledger">Public ledger</ProductLink>
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
      <main id="public-content" className="public-home">
        <section className="public-hero">
          <div className="public-hero-copy">
            <h1>
              One question.
              <br />
              Independent judgement.
            </h1>
            <p>
              When ACAPS severity data shifts, Sealed Signals asks a small panel
              of humanitarian experts whether the analysis still holds. Answers
              are sealed until the round opens, aggregated as a group view, and
              published with their own limitations.
            </p>
            <ProductLink to="/workspace">
              <span className="public-primary">
                Open the workspace <ArrowRight size={18} aria-hidden="true" />
              </span>
            </ProductLink>
          </div>
          <div className="public-feature-static">
            <p>Latest alert · Chad</p>
            <h2>Displacement from Sudan to Chad</h2>
            <p className="public-feature-figure">
              <span className="num">6.1</span> &rarr;{" "}
              <strong className="num">6.9</strong>
            </p>
            <p>
              INFORM severity, March to April 2026. The largest deterioration of
              123 crises that month, and the question that round put to the
              panel.
            </p>
          </div>
        </section>

        <section className="public-research">
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

        <section className="public-additions">
          <div className="public-section-heading">
            <div>
              <p>New in this version</p>
              <h2>The same purpose, with safeguards you can check.</h2>
            </div>
          </div>
          <p className="public-additions-lead">
            The point has not changed: better decisions for people living with
            the risk, made with the experts closest to it. What is new is the
            machinery that makes asking them safe, quick and open to scrutiny.
          </p>
          <div className="public-additions-grid">
            {[
              {
                icon: Fingerprint,
                title: "A record nobody can edit later",
                text: "Each answer gets a digital fingerprint the moment it is confirmed. Anyone can press Verify on the public ledger and see that the published group view still matches the answers it came from.",
              },
              {
                icon: UserRound,
                title: "Experts choose how they appear",
                text: "Answer by answer: under their name, under a nickname, or with no identity kept at all. Answers with no identity kept are stored without any link to a person and cannot be traced back afterwards.",
              },
              {
                icon: MailCheck,
                title: "No account, no password",
                text: "One personal link reaches the expert, and that is the whole sign-up. Nothing to install and nothing to remember, on the phone they already use.",
              },
              {
                icon: EyeOff,
                title: "Built so nobody follows the crowd",
                text: "The current rating stays hidden until after the expert answers, so it cannot pull them towards it. “Outside my area” and “not enough evidence” are real answers and are never scored, so nobody is pushed into a guess.",
              },
              {
                icon: Scale,
                title: "The disagreement is published too",
                text: "The panel’s view is a plain average, shown with its full spread and the reasons of the people who disagreed, without names. Nothing is published from fewer than five answers.",
              },
              {
                icon: FileCheck2,
                title: "Every figure checked before a person decides",
                text: "The draft update names a source for each claim, and any number that does not match the record it points at is flagged rather than quietly corrected. An analyst then accepts, edits or rejects it, with the reasons on the record.",
              },
            ].map(({ icon: Icon, title, text }) => (
              <article key={title}>
                <Icon size={21} aria-hidden="true" />
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
          <p className="public-additions-note">
            The Chad alert above was found by plain arithmetic over ACAPS&rsquo;s
            own monthly severity data, with no AI model anywhere in it. Expert
            panels and their answers in this prototype are synthetic.
          </p>
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
          <a href="/stage">Stage & jury access</a>
          <a href="/calibration">Calibration report</a>
          <a href="/committee">Expert committee</a>
          <a href="/apply">Expert application</a>
        </div>
      </details>
    </Frame>
  );
}
