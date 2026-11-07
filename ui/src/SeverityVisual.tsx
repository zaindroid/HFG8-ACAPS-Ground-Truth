import { useState, useRef, useEffect, type CSSProperties } from "react";
export function SeverityVisual({
  before,
  after,
  from,
  to,
}: {
  before: number;
  after: number;
  from?: string;
  to?: string;
}) {
  const [play, setPlay] = useState(0);
  const root = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!root.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.35 },
    );
    observer.observe(root.current);
    return () => observer.disconnect();
  }, []);
  const limit = (value: number) => Math.max(0, Math.min(100, value * 10));
  const delta = Math.round((after - before) * 100) / 100;
  return (
    <div ref={root} className="severity-visual">
      <div className="severity-values">
        <strong>
          {before}
          <small>{from?.replace(/(\D+)(\d+)/, "$1 $2") || "Previous"}</small>
        </strong>
        <span>
          {delta > 0 ? "+" : ""}
          {delta} points
        </span>
        <strong>
          {after}
          <small>{to?.replace(/(\D+)(\d+)/, "$1 $2") || "Current"}</small>
        </strong>
      </div>
      <div
        className="severity-scale"
        role="img"
        aria-label={`Severity index changed from ${before} to ${after} on a zero to ten scale`}
      >
        <span className="severity-scale-line" />
        <span
          className="severity-old-dot"
          style={{ left: `${limit(before)}%` }}
        />
        <span
          key={play}
          className={`severity-travelling-dot ${visible ? "moving" : ""}`}
          style={
            {
              "--severity-from": `${limit(before)}%`,
              left: `${limit(after)}%`,
            } as CSSProperties
          }
        />
      </div>
      <div className="severity-scale-labels">
        <span>0 · lower severity</span>
        <span>10 · higher severity</span>
      </div>
      <button
        type="button"
        className="motion-replay"
        onClick={() => setPlay((p) => p + 1)}
      >
        Replay change
      </button>
    </div>
  );
}
