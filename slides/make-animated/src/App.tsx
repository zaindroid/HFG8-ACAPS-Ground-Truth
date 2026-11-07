import { useCallback, useEffect, useState, type CSSProperties, type ReactNode } from "react";

const TOTAL_SLIDES = 8;

function SlideFrame({
  children,
  number,
  nodeId,
  dark = false,
  className = "",
}: {
  children: ReactNode;
  number: number;
  nodeId: string;
  dark?: boolean;
  className?: string;
}) {
  return (
    <article
      className={`slide ${dark ? "slide-dark" : "slide-light"} ${className}`}
      data-node-id={nodeId}
      aria-label={`Slide ${number} of ${TOTAL_SLIDES}`}
    >
      <div className="slide-orbit" aria-hidden="true">
        <i />
        <i />
        <i />
      </div>
      {children}
      <p className="slide-number">
        {number} / {TOTAL_SLIDES}
      </p>
    </article>
  );
}

function SlideOne() {
  return (
    <SlideFrame number={1} nodeId="3:27" className="problem-slide">
      <div className="problem-main">
        <p className="kicker">Problem</p>
        <p className="mega-number">
          <span>47</span>
          <small>%</small>
        </p>
        <h1>of Medium-rated ACAPS risks materialised. A coin flip.</h1>
        <p className="source">
          27 of 58 resolved Medium risks. High-rated: 32 of 38 (84 %). Source: ACAPS Risk Radar
          export.
        </p>
      </div>
      <aside className="rating-panel">
        <p className="panel-title">Materialised, by rating</p>
        <div className="chart">
          <div className="reference-line">
            <span>50 %</span>
          </div>
          <div className="bar-row">
            <span>High</span>
            <div className="bar-line">
              <i style={{ "--bar-width": "84%" } as CSSProperties} />
              <b>84 %</b>
            </div>
          </div>
          <div className="bar-row">
            <span>Medium</span>
            <div className="bar-line">
              <i style={{ "--bar-width": "47%" } as CSSProperties} />
              <b>47 %</b>
            </div>
          </div>
        </div>
      </aside>
    </SlideFrame>
  );
}

function SlideTwo() {
  const points = [
    "Experts are informed professionals, not sources on the ground.",
    "Experts apply. A committee approves.",
    "Risk Radar is a dataset and an API. It should have a platform.",
  ];
  return (
    <SlideFrame number={2} nodeId="3:43" className="insight-slide">
      <aside className="quote-panel">
        <span className="quote-mark">“</span>
        <blockquote>
          We will get things wrong, like a prediction market; the point is honesty about it.
        </blockquote>
        <cite>ACAPS mentor, interview notes, 2026-11-06</cite>
      </aside>
      <div className="insight-main">
        <p className="kicker">What ACAPS told us</p>
        <h1>No platform exists. Honesty is the point.</h1>
        <div className="point-list">
          {points.map((point, index) => (
            <p key={point} style={{ "--i": index } as CSSProperties}>
              {point}
            </p>
          ))}
        </div>
      </div>
    </SlideFrame>
  );
}

function SlideThree() {
  const steps = [
    "Analyst trigger",
    "Matched panel",
    "Committed answers",
    "Integrity notes",
    "Cited draft",
    "Analyst decision",
    "Ledger and honesty box",
    "Scoring",
  ];
  return (
    <SlideFrame number={3} nodeId="3:57" className="loop-slide">
      <header>
        <p className="kicker">The loop</p>
        <h1>
          The machine rings the doorbell, the panel answers, the analyst decides, the ledger
          remembers.
        </h1>
      </header>
      <div className="step-grid">
        {steps.map((step, index) => (
          <div className="step-wrap" key={step}>
            <div
              className={`step-card ${index === 5 ? "active" : ""}`}
              style={{ "--i": index } as CSSProperties}
            >
              <b>{index + 1}</b>
              <span>{step}</span>
            </div>
            {index !== 3 && index !== 7 && <span className="step-arrow">→</span>}
          </div>
        ))}
      </div>
      <p className="loop-note">Nothing changes an ACAPS product unless the analyst accepts.</p>
    </SlideFrame>
  );
}

function SlideFour() {
  return (
    <SlideFrame number={4} nodeId="3:92" dark className="demo-slide">
      <p className="kicker">Demo</p>
      <div className="demo-grid">
        <div className="qr-placeholder">
          <div className="scan-line" aria-hidden="true" />
          <span>QR code to the live expert card goes here</span>
        </div>
        <div className="demo-copy">
          <h1>Scan. You are the Chad panel.</h1>
          <h2>About a minute. No login.</h2>
          <p>Risk R1043, eastern Chad. Synthetic experts are labelled.</p>
        </div>
      </div>
    </SlideFrame>
  );
}

function SlideFive() {
  const statements = [
    "Tests the software.",
    "Says nothing about real experts.",
    "No claim about timing versus ACAPS.",
  ];
  return (
    <SlideFrame number={5} nodeId="3:100" className="proof-slide">
      <div className="proof-copy">
        <p className="kicker">Proof (backup slide)</p>
        <h1>A sensitivity test on all 104 resolved ACAPS risks, with synthetic panels.</h1>
        <div className="point-list proof-points">
          {statements.map((statement, index) => (
            <p key={statement} style={{ "--i": index } as CSSProperties}>
              {statement}
            </p>
          ))}
        </div>
      </div>
      <div className="proof-placeholder">
        <div className="proof-pulse" aria-hidden="true" />
        <strong>reports/proof.png goes here</strong>
        <span>Lane A produces it by Sat 20:00.</span>
      </div>
    </SlideFrame>
  );
}

function SlideSix() {
  const rows = [
    ["Anchoring", "ACAPS's rating is hidden until the expert submits (anchoring)."],
    ["Aggregate", "Equal-weight mean, with spread and minority reasons."],
    [
      "Analyst notes",
      "Notes for the analyst: convergence, shared origin, coverage gaps. They describe; they do not judge.",
    ],
    [
      "Honesty box",
      "Honesty box on every ledger entry: limits, misses, the decision it could inform.",
    ],
  ];
  return (
    <SlideFrame number={6} nodeId="3:113" className="integrity-slide">
      <header>
        <p className="kicker">Integrity and honesty</p>
        <h1>We describe bias to the analyst and state our limits in public.</h1>
      </header>
      <div className="integrity-rows">
        {rows.map(([label, copy], index) => (
          <div className="integrity-row" key={label} style={{ "--i": index } as CSSProperties}>
            <strong>{label}</strong>
            <p>{copy}</p>
          </div>
        ))}
      </div>
      <footer>
        One validation layer among others. Commitments prove timing, not secrecy from the operator.
      </footer>
    </SlideFrame>
  );
}

function SlideSeven() {
  const stakeholders = [
    ["Analysts", "A cited draft instead of a blank page"],
    ["Experts", "The outcome, for a minute of their time"],
    ["Readers", "The basis, limits and misses behind each rating"],
    ["Committee", "An audit trail for who joined"],
    ["Affected people", "Possible earlier preparation. Not yet shown."],
  ];
  return (
    <SlideFrame number={7} nodeId="3:127" className="impact-slide">
      <div className="impact-copy">
        <p className="kicker">Impact and stakeholders</p>
        <h1>A probability with its basis.</h1>
        <p>
          Anticipatory-action evidence is strongest for floods and drought. Conflict is the open
          test.
        </p>
      </div>
      <div className="stakeholder-panel">
        {stakeholders.map(([label, copy], index) => (
          <div
            className={`stakeholder-row ${index === 4 ? "caution" : ""}`}
            key={label}
            style={{ "--i": index } as CSSProperties}
          >
            <strong>{label}</strong>
            <p>{copy}</p>
          </div>
        ))}
      </div>
    </SlideFrame>
  );
}

function SlideEight() {
  const metrics = [
    ["2", "months"],
    ["1", "committee"],
    ["8", "experts"],
    ["1", "country"],
  ];
  const questions = [
    "How does the panel mean compare with the rating on questions that resolve?",
    "Minutes saved per weekly update.",
    "Experts still answering in week 8.",
  ];
  return (
    <SlideFrame number={8} nodeId="3:144" dark className="pilot-slide">
      <header>
        <p className="kicker">December pilot and team</p>
        <h1>Ready for a supervised pilot of this workflow.</h1>
      </header>
      <div className="metrics">
        {metrics.map(([number, label], index) => (
          <div className="metric" key={label} style={{ "--i": index } as CSSProperties}>
            <strong>{number}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="pilot-questions">
        {questions.map((question, index) => (
          <p key={question} style={{ "--i": index } as CSSProperties}>
            {question}
          </p>
        ))}
      </div>
      <p className="team">
        Team: Zain Ul Haq (backend) | Saleeta Qadir (frontend) | Sho Izuno (research and pitch).
        Hackathon for Good #8, ACAPS Ground Truth.
      </p>
    </SlideFrame>
  );
}

const slides = [
  <SlideOne />,
  <SlideTwo />,
  <SlideThree />,
  <SlideFour />,
  <SlideFive />,
  <SlideSix />,
  <SlideSeven />,
  <SlideEight />,
];

export default function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [animationKey, setAnimationKey] = useState(0);

  const goTo = useCallback((index: number) => {
    setCurrentSlide((index + TOTAL_SLIDES) % TOTAL_SLIDES);
    setAnimationKey((key) => key + 1);
  }, []);

  const next = useCallback(() => goTo(currentSlide + 1), [currentSlide, goTo]);
  const previous = useCallback(() => goTo(currentSlide - 1), [currentSlide, goTo]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowRight" || event.key === "PageDown") next();
      if (event.key === "ArrowLeft" || event.key === "PageUp") previous();
      if (event.key === " ") {
        event.preventDefault();
        setIsAutoPlaying((playing) => !playing);
      }
      if (event.key === "Home") goTo(0);
      if (event.key === "End") goTo(TOTAL_SLIDES - 1);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goTo, next, previous]);

  useEffect(() => {
    if (!isAutoPlaying) return;
    const timer = window.setInterval(next, 9000);
    return () => window.clearInterval(timer);
  }, [isAutoPlaying, next]);

  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen?.();
    } else {
      await document.exitFullscreen?.();
    }
  };

  return (
    <main className="deck">
      <div className="slide-shell" key={`${currentSlide}-${animationKey}`}>
        {slides[currentSlide]}
      </div>

      <nav className="deck-controls" aria-label="Presentation controls">
        <button type="button" onClick={previous} aria-label="Previous slide">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m15 18-6-6 6-6" />
          </svg>
        </button>
        <div className="progress-dots">
          {slides.map((_, index) => (
            <button
              type="button"
              className={currentSlide === index ? "active" : ""}
              onClick={() => goTo(index)}
              aria-label={`Go to slide ${index + 1}`}
              aria-current={currentSlide === index ? "page" : undefined}
              key={index}
            />
          ))}
        </div>
        <button type="button" onClick={next} aria-label="Next slide">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m9 18 6-6-6-6" />
          </svg>
        </button>
        <span className="control-divider" />
        <button
          type="button"
          onClick={() => setIsAutoPlaying((playing) => !playing)}
          aria-label={isAutoPlaying ? "Pause autoplay" : "Start autoplay"}
          className={isAutoPlaying ? "control-active" : ""}
        >
          {isAutoPlaying ? (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M9 7v10M15 7v10" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m9 7 8 5-8 5V7Z" className="fill-icon" />
            </svg>
          )}
        </button>
        <button
          type="button"
          onClick={() => setAnimationKey((key) => key + 1)}
          aria-label="Replay animation"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4.9 9a8 8 0 1 1-.2 5M4 5v5h5" />
          </svg>
        </button>
        <button type="button" onClick={toggleFullscreen} aria-label="Toggle fullscreen">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" />
          </svg>
        </button>
      </nav>

      <div className="keyboard-hint">← → to navigate · space to autoplay</div>
      <div className="sr-only" aria-live="polite">
        Slide {currentSlide + 1} of {TOTAL_SLIDES}
      </div>
    </main>
  );
}
