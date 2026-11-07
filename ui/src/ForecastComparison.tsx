import { useRef, useState, useEffect } from "react";
import type { Result } from "./service";
export function ForecastComparison({
  result,
  reference,
}: {
  result: Result;
  reference: string;
}) {
  const plot = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(560);
  useEffect(() => {
    const el = plot.current;
    if (!el) return;
    const update = () => setWidth(Math.max(280, el.clientWidth));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const pos = (p: number) => 40 + p * (width - 80);
  const assumed = (
    {
      "Very Low": 0.1,
      Low: 0.3,
      Medium: 0.5,
      High: 0.7,
      "Very High": 0.9,
    } as Record<string, number>
  )[reference];
  return (
    <section
      className="forecast-comparison"
      aria-label="Expert forecast versus ACAPS"
    >
      <div className="forecast-comparison-values">
        <div>
          <span>Expert average</span>
          <strong>{Math.round(result.mean * 100)}%</strong>
        </div>
        <div>
          <span>ACAPS assessment</span>
          <strong>{reference}</strong>
        </div>
      </div>
      <div ref={plot}>
        <svg
          viewBox={`0 0 ${width} 145`}
          role="img"
          aria-label={`Experts average ${Math.round(result.mean * 100)} percent, range ${Math.round(result.spread.min * 100)} to ${Math.round(result.spread.max * 100)} percent. ACAPS probability band ${reference}.`}
        >
          <line
            x1="40"
            x2={width - 40}
            y1="100"
            y2="100"
            className="comparison-axis"
          />
          {[0, 20, 40, 60, 80, 100].map((v) => (
            <g key={v}>
              <line
                x1={pos(v / 100)}
                x2={pos(v / 100)}
                y1="26"
                y2="100"
                className="comparison-grid"
              />
              <text x={pos(v / 100)} y="124" textAnchor="middle">
                {v}%
              </text>
            </g>
          ))}
          <line
            x1={pos(result.spread.min)}
            x2={pos(result.spread.max)}
            y1="44"
            y2="44"
            className="comparison-range"
          />
          <circle
            cx={pos(result.mean)}
            cy="44"
            r="7"
            className="comparison-mean"
          />
          {assumed !== undefined && (
            <>
              <line
                x1={pos(assumed)}
                x2={pos(assumed)}
                y1="15"
                y2="100"
                className="comparison-acaps"
              />
              <text x={pos(assumed) + 8} y="20">
                ACAPS {reference}
              </text>
            </>
          )}
          {result.distribution.flatMap((row, index) =>
            Array.from({ length: row.count }, (_, i) => (
              <circle
                key={`${index}-${i}`}
                cx={pos(
                  (index + 0.5) / Math.max(1, result.distribution.length),
                )}
                cy={88 - i * 11}
                r="4"
                className="comparison-estimate"
              />
            )),
          )}
        </svg>
      </div>
      <p>
        Dots show grouped expert estimates; the horizontal line shows their
        range. ACAPS provides a band, shown at an assumed position on this
        scale—not an exact percentage.
      </p>
    </section>
  );
}
