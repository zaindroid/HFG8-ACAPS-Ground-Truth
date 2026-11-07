import { EvidenceLine, evidenceSummary } from "./Evidence";
import { PortalHeader } from "./PortalHeader";
import { useEffect, useState, type FormEvent } from "react";
import * as Slider from "@radix-ui/react-slider";
import {
  ArrowRight,
  BadgeCheck,
  Check,
  Fingerprint,
  LockKeyhole,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import {
  getCard,
  sealAnswer,
  mock,
  type Card,
  type Mask,
  type Answer,
} from "./api";
import { CopyButton } from "./LiveWorkspace";
import { safeUrl, validResult } from "./service";
import { en } from "./locales/en";
import { ProbeStep } from "./Probes";
import {
  probeForStep,
  plannedSteps,
  type ProbeAnswers,
  type ProbeFlow,
} from "./probe-flow";

function Probability({
  id,
  label,
  help,
  value,
  change,
}: {
  id: string;
  label: string;
  help: string;
  value: number;
  change: (value: number) => void;
}) {
  return (
    <div className="question">
      <div className="question-heading">
        <span className="field-label" id={`${id}-label`}>
          {label}
        </span>
        <output>
          {value}
          <span>%</span>
        </output>
      </div>
      <p className="help" id={`${id}-help`}>
        {help}
      </p>
      <Slider.Root
        className="slider"
        min={0}
        max={100}
        step={1}
        value={[value]}
        onValueChange={([value]) => change(value)}
        aria-labelledby={`${id}-label`}
        aria-describedby={`${id}-help`}
      >
        <Slider.Track className="track">
          <Slider.Range className="range" />
        </Slider.Track>
        <Slider.Thumb className="thumb" aria-label={label} />
      </Slider.Root>
      <div className="scale">
        <span>0% · Very unlikely</span>
        <span>100% · Very likely</span>
      </div>
    </div>
  );
}
export function ExpertCard({ token }: { token: string }) {
  const [card, setCard] = useState<Card | null>(null),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0);
  const [probability, setProbability] = useState(50),
    [panel, setPanel] = useState(50),
    [confidence, setConfidence] = useState(3),
    [source, setSource] = useState<Answer["source_tag"]>(null),
    [missing, setMissing] = useState(""),
    [mask, setMask] = useState<Mask>("anonymous"),
    [stance, setStance] = useState<Answer["stance"]>("estimate"),
    [changed, setChanged] = useState(false),
    [probeAnswers, setProbeAnswers] = useState<ProbeAnswers>({}),
    [step, setStep] = useState(1),
    [chain, setChain] = useState<string[]>([]);
  const [busy, setBusy] = useState(false),
    [receipt, setReceipt] = useState<Awaited<
      ReturnType<typeof sealAnswer>
    > | null>(null),
    [submitError, setSubmitError] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    setCard(null);
    getCard(token)
      .then((value) => {
        if (active) {
          setCard(value);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    document.title = "Expert pulse | Sealed Signals";
    return () => {
      active = false;
    };
  }, [token, reload]);
  const blind = card?.round !== 2;
  const flow = (card as { probe_flow?: ProbeFlow } | null)?.probe_flow;
  const core = {
    stance,
    probability: probability / 100,
    panelShare: panel / 100,
    confidence,
  };
  const currentProbe =
    step > 1 ? probeForStep(flow, step, core, probeAnswers, chain) : null;
  const totalSteps = plannedSteps(flow, core, probeAnswers);
  const onLastStep = step >= totalSteps || (step > 1 && !currentProbe); // Round one remains blind even if an older API includes a rating.
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || receipt) return;
    setBusy(true);
    setSubmitError("");
    try {
      setReceipt(
        await sealAnswer(token, {
          stance,
          probability: stance === "estimate" ? probability / 100 : null,
          panel_share_yes: stance === "estimate" ? panel / 100 : null,
          confidence: stance === "estimate" ? confidence : null,
          round: card?.round || 1,
          source_tag: source,
          mask,
          missing: missing.trim(),
          changed_mind: !blind && changed,
          probe_answers: stance === "estimate" ? probeAnswers : {},
        }),
      );
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <a className="skip-link" href="#expert-content">
        Skip to expert card
      </a>
      {location.pathname === "/expert" ? (
        <PortalHeader />
      ) : (
        <header className={`site-header ${mock ? "expert-demo-header" : ""}`}>
          <a className="brand" href={mock ? "/workspace" : "/"}>
            <span className="brand-mark">
              <LockKeyhole size={19} />
            </span>
            Sealed Signals
          </a>
          {mock ? (
            <nav aria-label="Demo navigation">
              <a href="/workspace">All pages</a>
              <a href="/stage">Stage</a>
              <a href="/calibration">Calibration</a>
            </nav>
          ) : (
            <span className="header-note">Independent expert perspective</span>
          )}
        </header>
      )}
      <main id="expert-content">
        <aside className="intro">
          <p className="eyebrow">Expert pulse </p>
          <h1>Your view, before the rating.</h1>
          <p>
            Forecast the risk before seeing the panel. Your chosen mask applies
            to this answer.
          </p>
          <div className="trust">
            <ShieldCheck size={20} />
            <span>
              One validation layer among others.
              <br />
              An ACAPS analyst decides what changes.
            </span>
          </div>
        </aside>
        <section className="card" aria-label="Expert response card">
          {error ? (
            <div className="state" role="alert">
              <h2>We couldn’t open this card.</h2>
              <p>{error}</p>
              <button onClick={() => setReload((v) => v + 1)}>Try again</button>
            </div>
          ) : !card ? (
            <div className="state" role="status">
              Opening your expert card…
            </div>
          ) : receipt ? (
            <div className="state receipt" role="status">
              <span className="success-mark">
                <Check size={28} />
              </span>
              <h2>{en.sealed}</h2>
              <p>
                Submitted. You’ll get the group outcome when this resolves. Your
                answer uses the <strong>{mask}</strong> mask. Only a group view
                with at least five answers can be published.
              </p>
              <div className="receipt-box">
                <span>
                  {mock
                    ? "Fixture receipt · not a live seal"
                    : "API commitment receipt"}
                </span>
                <time>
                  {new Date(receipt.committed_at).toLocaleString("en-GB", {
                    timeZone: "UTC",
                  })}{" "}
                  UTC
                </time>
                <span>Commitment</span>
                <code>{receipt.commitment}</code>
                <CopyButton
                  value={receipt.commitment}
                  label="Copy commitment"
                />
              </div>
              {mask !== "anonymous" && (
                <a href={`/me/${encodeURIComponent(token)}/calibration`}>
                  Opt in to private calibration
                </a>
              )}
              {mask === "anonymous" && (
                <p>
                  Anonymous answers have no identity link and cannot be claimed
                  later. A group outcome report is sent to panel members.
                </p>
              )}
            </div>
          ) : (
            <>
              <div className="card-top">
                <span>
                  {card.risk.country} / {card.risk.risk_id}
                </span>
                <span>Respond in your own time</span>
              </div>
              <div className="risk-context">
                <div className="risk-meta">
                  <span>Round {card.round}</span>
                  <span>Next {card.risk.horizon_months} months</span>
                  {blind ? (
                    <span className="blind-badge">
                      Rating hidden until after submission
                    </span>
                  ) : (
                    <span className="rating">
                      ACAPS probability:{" "}
                      {card.risk.probability_acaps || "Not supplied"}
                    </span>
                  )}
                </div>
                <h2>{card.risk.title}</h2>
                <details className="evidence">
                  <summary>
                    {card.pulse.evidence[0]
                      ? evidenceSummary(card.pulse.evidence[0])
                      : "Edition evidence"}
                  </summary>
                  {card.pulse.evidence.map((e, i) => (
                    <EvidenceLine key={i} value={e} />
                  ))}
                </details>
              </div>
              {!blind && (
                <section className="group-view">
                  <h3>How the panel answered</h3>
                  {card.group_view_if_round2 &&
                  validResult(card.group_view_if_round2) ? (
                    <>
                      <p>
                        {card.group_view_if_round2.n} synthetic answers ·
                        Equal-weight mean{" "}
                        {Math.round(card.group_view_if_round2.mean * 100)}%
                      </p>
                      <div
                        className="distribution"
                        aria-label="Panel probability distribution"
                      >
                        {card.group_view_if_round2.distribution.map((b) => (
                          <div key={b.bucket}>
                            <span className="bar-space">
                              <span
                                style={{
                                  height: `${(b.count / card.group_view_if_round2!.n) * 100}%`,
                                }}
                              />
                            </span>
                            <span>
                              {b.bucket
                                .split("-")
                                .map((v) => Math.round(Number(v) * 100))
                                .join("–")}
                              %
                            </span>
                            <strong>{b.count}</strong>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <p>
                      Group view withheld until at least five answers are
                      confirmed.
                    </p>
                  )}
                </section>
              )}
              <form onSubmit={submit}>
                <fieldset disabled={busy}>
                  <div
                    className="question stance-picker"
                    role="group"
                    aria-label="Your response"
                  >
                    <span className="field-label">Your response</span>
                    {(
                      [
                        ["estimate", "Give an estimate"],
                        ["outside_my_expertise", "Outside my expertise"],
                        ["not_enough_evidence", "Not enough evidence"],
                      ] as const
                    ).map(([value, label]) => (
                      <button
                        type="button"
                        key={value}
                        aria-pressed={stance === value}
                        onClick={() => setStance(value)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  {stance === "estimate" && (
                    <>
                      <Probability
                        id="probability"
                        label={en.probability}
                        help="Give your own estimate before considering anyone else’s."
                        value={probability}
                        change={setProbability}
                      />
                      <div className="question confidence-field">
                        <label htmlFor="confidence">
                          How confident are you in this estimate?
                        </label>
                        <select
                          id="confidence"
                          value={confidence}
                          onChange={(e) =>
                            setConfidence(Number(e.target.value))
                          }
                        >
                          {[
                            "Very uncertain",
                            "Somewhat uncertain",
                            "Moderately confident",
                            "Confident",
                            "Very confident",
                          ].map((label, i) => (
                            <option key={label} value={i + 1}>
                              {i + 1} · {label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <Probability
                        id="panel"
                        label={en.panel}
                        help="What share of this panel will put the probability above 0.5?"
                        value={panel}
                        change={setPanel}
                      />
                    </>
                  )}
                  {stance !== "estimate" && (
                    <p className="abstention-note">
                      Your response will be recorded without a probability or
                      confidence score. Abstentions are never scored.
                    </p>
                  )}
                  <div className="question">
                    <label htmlFor="missing">
                      What are we missing?{" "}
                      <span className="optional">Optional</span>
                    </label>
                    <p className="help" id="accuracy-prompt">
                      {card.accuracy_prompt ||
                        "Is this something you saw, read, or heard?"}
                    </p>
                    <div
                      className="source-picker"
                      role="group"
                      aria-label="Source of your observation"
                    >
                      {(["saw", "read", "heard"] as const).map((tag) => (
                        <button
                          type="button"
                          key={tag}
                          aria-pressed={source === tag}
                          onClick={() =>
                            setSource((v) => (v === tag ? null : tag))
                          }
                        >
                          {tag === "saw"
                            ? "I saw it"
                            : tag === "read"
                              ? "I read it"
                              : "I heard it"}
                        </button>
                      ))}
                    </div>
                    <textarea
                      id="missing"
                      aria-describedby="accuracy-prompt missing-help"
                      maxLength={240}
                      rows={2}
                      value={missing}
                      onChange={(e) => setMissing(e.target.value)}
                      placeholder="A signal, a local shift, a different perspective…"
                    />
                    <p className="help" id="missing-help">
                      Leave out names and identifying details.
                    </p>
                    <span className="char-count">{missing.length}/240</span>
                  </div>
                  {!blind && (
                    <label className="changed">
                      <input
                        type="checkbox"
                        checked={changed}
                        onChange={(e) => setChanged(e.target.checked)}
                      />{" "}
                      I changed my mind after seeing the panel
                    </label>
                  )}
                  {/* One step at a time, after the scored core. Steps 2 and 3 are chosen
                      from the answers above, so the question has to be answered before it
                      can be framed by anything that follows. */}
                  {step > 1 && currentProbe && (
                    <ProbeStep
                      probe={currentProbe}
                      answers={probeAnswers}
                      onChange={setProbeAnswers}
                      step={step}
                      total={totalSteps}
                    />
                  )}
                  <div className="question mask-question">
                    <span className="field-label" id="mask-label">
                      Choose your mask for this answer
                    </span>
                    <div
                      className="masks"
                      role="group"
                      aria-labelledby="mask-label"
                    >
                      {(["known", "pseudonym", "anonymous"] as Mask[])
                        .filter((m) => card.mask_options.includes(m))
                        .map((m, i) => {
                          const Icon = [BadgeCheck, UserRound, Fingerprint][i];
                          return (
                            <button
                              type="button"
                              key={m}
                              aria-pressed={mask === m}
                              onClick={() => setMask(m)}
                            >
                              <Icon size={19} />
                              <strong>{en.masks[m][0]}</strong>
                              <span>{en.masks[m][1]}</span>
                            </button>
                          );
                        })}
                    </div>
                    <p className="help">
                      {mask === "known"
                        ? "ACAPS can associate this answer with your invitation."
                        : mask === "pseudonym"
                          ? "Peers see a nickname, not your identity."
                          : "No pseudonym is shown. Your answer counts only in the aggregate."}{" "}
                      Public output is group-only. Distinctive wording can be
                      recognised by peers, even under a pseudonym. Anonymous
                      answers cannot be claimed later.
                    </p>
                    <details className="privacy-detail">
                      <summary>Who can see what?</summary>
                      <p>
                        Peers do not see answers before the round opens. After
                        reveal, peers may see pseudonymous reasons only when
                        that mask was chosen. Public output contains aggregates,
                        never individual answers or reasons.
                      </p>
                      <p>
                        The pilot uses a restricted identity registry with
                        logged access. Anonymous answers have no identity link.
                        The server stores the committed value; access controls,
                        rather than cryptography, restrict early staff access. A
                        commitment does not hide the answer from the operator.
                      </p>
                      <p>
                        At least five contributions is a disclosure rule, not an
                        anonymity guarantee. Distinctive reasons may still
                        identify a contributor to peers.
                      </p>
                    </details>
                  </div>
                  {submitError && (
                    <p role="alert" className="error-box">
                      {submitError} Your inputs are kept here.
                    </p>
                  )}
                  {/* Distinct keys matter: without them React patches one element's type
                      from "button" to "submit" during the click that advances the step, and
                      the browser then submits the form on step two. */}
                  {onLastStep ? (
                    <button key="submit" type="submit" className="seal-button">
                      <LockKeyhole size={18} />
                      {busy ? "Submitting…" : "Submit"}
                    </button>
                  ) : (
                    <button
                      key="continue"
                      type="button"
                      className="seal-button"
                      onClick={() => {
                        // The chain records the steps already shown, so the next lookup
                        // can read what was asked before it. Pushing the upcoming probe
                        // instead would make the lookup skip it as already seen.
                        if (currentProbe) setChain([...chain, currentProbe.id]);
                        setStep(step + 1);
                      }}
                    >
                      Continue
                      <ArrowRight size={18} />
                    </button>
                  )}
                  {step > 1 && (
                    <button
                      type="button"
                      className="text-button"
                      onClick={() => {
                        setChain(chain.slice(0, -1));
                        setStep(step - 1);
                      }}
                    >
                      Back
                    </button>
                  )}
                  <p className="seal-note">
                    A commitment records timing and consistency. The operator
                    can access the stored answer; it does not provide
                    confidentiality from the server.
                  </p>
                </fieldset>
              </form>
            </>
          )}
        </section>
      </main>
    </>
  );
}
