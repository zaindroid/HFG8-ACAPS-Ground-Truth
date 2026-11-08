import { ArrowRight, LockKeyhole } from "lucide-react";
import type { Result } from "./service";
import { validResult } from "./service";

export const journey = [
  {
    href: "/alerts",
    title: "Spot the change",
    text: "A change in ACAPS data raises a question.",
  },
  {
    href: "/expert",
    title: "Hear the experts",
    text: "Independent answers, sealed before reveal.",
  },
  {
    href: "/desk",
    title: "Make the call",
    text: "An analyst reviews the evidence and decides.",
  },
  {
    href: "/ledger",
    title: "Check the record",
    text: "Trace the decision, including the misses.",
  },
];
export function Journey({ active }: { active?: number }) {
  return (
    <nav className="decision-journey" aria-label="Decision journey">
      {journey.map((step, i) => (
        <a
          key={step.href}
          href={step.href}
          aria-current={active === i ? "step" : undefined}
        >
          <span className="journey-number">{i + 1}</span>
          <span>{step.title}</span>
          {i < 3 && <ArrowRight size={15} aria-hidden="true" />}
        </a>
      ))}
    </nav>
  );
}
export function DecisionSnapshot({
  rating,
  result,
}: {
  rating: string;
  result: Result | null;
}) {
  const visible = result && validResult(result);
  return (
    <section className="decision-snapshot" aria-label="Decision at a glance">
      <div>
        <span>ACAPS probability band</span>
        <strong>{rating}</strong>
        <small>Current assessment</small>
      </div>
      <div>
        <span>Independent panel</span>
        <strong>
          {visible ? (
            `${Math.round(result.mean * 100)}%`
          ) : (
            <>
              <LockKeyhole size={20} /> Sealed
            </>
          )}
        </strong>
        <small>
          {visible
            ? `Equal-weight mean · ${result.n} answers`
            : "Revealed together after five answers"}
        </small>
      </div>
      <div>
        <span>Forecast spread</span>
        <strong>
          {visible
            ? `${Math.round(result.spread.min * 100)}–${Math.round(result.spread.max * 100)}%`
            : "Awaiting reveal"}
        </strong>
        <small>
          {visible
            ? "Full range of panel estimates"
            : "Individual estimates stay hidden"}
        </small>
      </div>
      <div className="decision-owner">
        <span>Decision owner</span>
        <strong>The analyst</strong>
        <small>Accept, edit or reject</small>
      </div>
    </section>
  );
}
