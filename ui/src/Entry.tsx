import { Journey, journey } from "./Journey";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowUpRight, LockKeyhole } from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { DemoSamples } from "./DemoSamples";
import { startDemoSession, workspaceDestination } from "./workspace-session";
import { getTrustStatus } from "./api";
import type { TrustStatus } from "./service";

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

/** The hero readout and the stack grid both render what /trust/status says, including each
 *  mechanism's own "guarantees" and "does not" sentence. MASTER_PROMPT 6c keeps those sentences
 *  in one place in the engine so that no surface can quietly make the stronger claim, and a
 *  landing page is the surface most tempted to. Nothing here is written down a second time. */
function useTrustStatus() {
  const [status, setStatus] = useState<TrustStatus | null>(null);
  const [unreachable, setUnreachable] = useState(false);
  useEffect(() => {
    let live = true;
    getTrustStatus()
      .then((value) => {
        if (live) setStatus(value);
      })
      .catch(() => {
        if (live) setUnreachable(true);
      });
    return () => {
      live = false;
    };
  }, []);
  return { status, unreachable };
}

function StackReadout({
  status,
  unreachable,
}: {
  status: TrustStatus | null;
  unreachable: boolean;
}) {
  // Every value on this panel is a string the engine chose. Naming a primitive here instead
  // would have gone stale the day the daily root moved from one public log to another, and the
  // page would have kept saying the old one in a confident typeface.
  const anchoring = status?.mechanisms.find(
    (mechanism) => mechanism.id === "anchoring",
  );
  const rows = status
    ? [
        {
          label: "Identity map",
          value: status.registry.suite,
          meta: `${status.registry.n_identities} identities, ${status.registry.access_log_count} attributed reads logged`,
        },
        {
          label: "Outcome attestations",
          value: status.attestation_key.scheme,
          meta: `committee key ${status.attestation_key.key_id}`,
        },
        {
          label: "Answer credentials",
          value: status.credentials.scheme,
          meta: `${status.credentials.n_issued} issued, ${status.credentials.n_spent} spent, reuse refused by nullifier`,
        },
        {
          label: anchoring ? anchoring.name : "Public timestamp",
          value: `${status.anchors.anchored} anchored, ${status.anchors.pending} pending`,
          meta: anchoring
            ? anchoring.guarantees
            : "A root proves nothing until the log returns its inclusion proof",
        },
        {
          label: "Membership proof",
          value: status.zk.scheme,
          meta: status.zk.proof_verifier,
        },
      ]
    : [];
  return (
    <div className="stack-readout">
      <p className="stack-readout-head">Read from the running engine</p>
      {unreachable ? (
        <p className="stack-note" role="status">
          Every line of this panel is read from the engine at /trust/status. It is
          not answering, so the panel shows nothing rather than a number from an
          earlier run.
        </p>
      ) : status ? (
        <dl className="stack-rows">
          {rows.map((row) => (
            <div key={row.label}>
              <dt>{row.label}</dt>
              <dd>{row.value}</dd>
              <dd className="stack-meta">{row.meta}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="stack-note" role="status">
          Reading the stack from the engine.
        </p>
      )}
    </div>
  );
}

function StackGrid({
  status,
  unreachable,
}: {
  status: TrustStatus | null;
  unreachable: boolean;
}) {
  const built = status?.mechanisms ?? [];
  const on = built.filter((mechanism) => mechanism.enabled).length;
  return (
    <section className="public-stack">
      <div className="public-section-heading">
        <div>
          <p>The stack</p>
          <h2>Every mechanism, with what it does not do.</h2>
        </div>
      </div>
      {unreachable ? (
        <p className="stack-note" role="status">
          These cards are the engine&rsquo;s own words about its mechanisms. It is
          not answering, so none are shown.
        </p>
      ) : built.length === 0 ? (
        <p className="stack-note" role="status">
          Reading the mechanisms from the engine.
        </p>
      ) : (
        <>
          <p className="stack-count">
            {built.length} built, {on} switched on. The flag state and both
            sentences on every card come from the engine, so this page cannot
            promise more than the mechanism itself does.
          </p>
          <div className="stack-grid">
            {built.map((mechanism) => (
              <article key={mechanism.id}>
                <p className="stack-card-head">
                  <span>
                    {mechanism.number} &middot; {mechanism.name}
                  </span>
                  <span
                    className={
                      mechanism.enabled ? "stack-flag on" : "stack-flag off"
                    }
                  >
                    {mechanism.flag
                      ? `${mechanism.flag} ${mechanism.enabled ? "on" : "off"}`
                      : "always on"}
                  </span>
                </p>
                <p className="stack-build">{mechanism.build}</p>
                <p className="stack-claim">
                  <strong>Guarantees</strong> {mechanism.guarantees}
                </p>
                <p className="stack-claim not">
                  <strong>Does not</strong> {mechanism.does_not}
                </p>
              </article>
            ))}
          </div>
          {/* Card 3 states the guarantee blind signatures make. On this build most tokens were
              blinded by the server on the demo path, which is weaker, and the engine says so in
              one sentence: it belongs next to the card, not on a page nobody reaches. */}
          <p className="stack-footnote">
            <strong>On this build&rsquo;s credentials.</strong>{" "}
            {status?.credentials.linkage_note}
          </p>
        </>
      )}
    </section>
  );
}

export function PublicHome() {
  useEffect(() => {
    document.title = "Sealed Signals \u00b7 Expert validation for risk analysis";
  }, []);
  const { status, unreachable } = useTrustStatus();
  return (
    <>
      <a className="skip-link" href="#public-content">
        Skip to content
      </a>
      {/* A landmark, not a bare paragraph: role="note" is not one, so the banner
          sat outside every landmark and tripped the page own axe check. */}
      <aside className="prototype-banner" aria-label="Prototype notice">
        Prototype for the ACAPS Ground Truth challenge. Not an ACAPS service.
        Expert panels and their answers are synthetic.
      </aside>
      <PortalHeader />
      <main id="public-content" className="public-home">
        <section className="public-hero">
          <div className="public-hero-copy">
            <h1>
              Commit.
              <br />
              Reveal.
              <br />
              Verify.
            </h1>
            <p>
              An expert&rsquo;s answer is salted and hashed before anyone can read
              it, spent with a single-use credential the server refuses twice, and
              opened at the round&rsquo;s deadline. An earlier opening is possible
              and is published as one, with the reason recorded.
            </p>
            <p>
              The resolved outcome is signed with ML-DSA-65 over the round&rsquo;s
              commitment root, and the day&rsquo;s root is entered into a public
              append-only transparency log. Checking any of it takes a hash function
              and this page, not our word for it.
            </p>
            <ProductLink to="/workspace">
              <span className="public-primary">
                Open the workspace <ArrowRight size={18} aria-hidden="true" />
              </span>
            </ProductLink>
          </div>
          <StackReadout status={status} unreachable={unreachable} />
        </section>

        <StackGrid status={status} unreachable={unreachable} />

        <section className="public-signal">
          <div className="public-section-heading">
            <div>
              <p>What opens a round</p>
              <h2>Fixed numeric rules over ACAPS&rsquo;s own monthly editions.</h2>
            </div>
          </div>
          <div className="signal-row">
            <div className="public-feature-static">
              <p>Latest alert &middot; Chad</p>
              <h2>Displacement from Sudan to Chad</h2>
              <p className="public-feature-figure">
                <span>6.1</span> &rarr; <strong>6.9</strong>
              </p>
              <p>
                INFORM severity, March to April 2026. The largest deterioration of
                123 crises that month, and the question that round put to the panel.
              </p>
            </div>
            <ul className="signal-points">
              <li>
                <strong>Thresholds, not a model.</strong> The engine differences two
                published editions and fires on the numbers, so the same input
                always gives the same alert and the rule that fired is shown with
                it.
              </li>
              <li>
                <strong>It proposes; a person opens.</strong> No round, question or
                published outcome starts without an analyst, and rejecting the panel
                costs them a written rationale that is published too.
              </li>
              <li>
                <strong>The first card hides the rating.</strong> An expert answers
                without seeing the number under test, because an anchor shown is an
                anchor answered.
              </li>
            </ul>
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
              <p>1 &middot; Spot the change</p>
              <h3>The alert engine watches ACAPS&rsquo;s own monthly editions</h3>
              <p>
                Fixed numeric rules over the INFORM severity and access editions. It
                proposes; it never opens a round by itself.
              </p>
            </article>
            <article>
              <p>2 &middot; Hear the experts</p>
              <h3>A small panel answers in about a minute</h3>
              <p>
                Each expert chooses a mask, and the follow-up questions are routed by
                role against the biases ACAPS names in its own brief.
              </p>
            </article>
            <article>
              <p>3 &middot; Make the call</p>
              <h3>An analyst accepts, edits or rejects</h3>
              <p>
                Nothing publishes itself. The group view carries the spread, the
                themes behind any disagreement, and the claims no record supports.
              </p>
            </article>
            <article>
              <p>4 &middot; Check the record</p>
              <h3>The decision ledger is the product</h3>
              <p>
                Commitments, the attestation, the anchor status and the registry
                access log, on one page anyone can read without an account.
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
          <a href="/stage">Stage & jury access</a>
          <a href="/calibration">Calibration report</a>
          <a href="/committee">Expert committee</a>
          <a href="/apply">Expert application</a>
        </div>
      </details>
    </Frame>
  );
}
