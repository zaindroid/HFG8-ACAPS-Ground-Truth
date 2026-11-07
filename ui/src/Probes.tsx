import { GripVertical } from "lucide-react";
import type { Probe, ProbeAnswers } from "./probe-flow";

/**
 * The probes that follow the scored question.
 *
 * They are chosen by the engine from the risk record and this expert's own tags, so the card
 * is fixed before anyone else answers and nothing here can carry a peer's view. Their answers
 * feed themes and coverage; they never enter the published probability.
 *
 * Follow-ups open on the expert's own previous answer and on nothing else.
 */


const opens = (when: string | string[], value: unknown) =>
  typeof value === "string" &&
  (Array.isArray(when) ? when.includes(value) : when === value);

function Choice({
  probe,
  value,
  onChange,
}: {
  probe: Probe;
  value?: string | string[];
  onChange: (value: string) => void;
}) {
  const options = probe.options || [];
  const substantive = options.filter((o) => !o.dk);
  const dk = options.filter((o) => o.dk);
  const button = (option: { value: string; label: string }) => (
    <button
      key={option.value}
      type="button"
      aria-pressed={value === option.value}
      onClick={() => onChange(option.value)}
    >
      {option.label}
    </button>
  );
  return (
    <div className="probe-options" role="group" aria-label={probe.question}>
      {substantive.map(button)}
      {dk.length > 0 && <span className="probe-dk">{dk.map(button)}</span>}
    </div>
  );
}

function Rank({
  probe,
  value,
  onChange,
}: {
  probe: Probe;
  value?: string | string[];
  onChange: (value: string[]) => void;
}) {
  const options = probe.options || [];
  const order = Array.isArray(value) ? value : options.map((o) => o.value);
  const move = (from: number, to: number) => {
    if (to < 0 || to >= order.length) return;
    const next = [...order];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    onChange(next);
  };
  return (
    <ol className="probe-rank">
      {order.map((v, index) => {
        const option = options.find((o) => o.value === v);
        if (!option) return null;
        return (
          <li key={v}>
            <GripVertical size={15} aria-hidden="true" />
            <span>{option.label}</span>
            {/* Buttons rather than drag alone: dragging is unreachable by keyboard and
                awkward on a phone, which is where this card is answered. */}
            <span className="probe-rank-controls">
              <button
                type="button"
                aria-label={`Move ${option.label} up`}
                disabled={index === 0}
                onClick={() => move(index, index - 1)}
              >
                ↑
              </button>
              <button
                type="button"
                aria-label={`Move ${option.label} down`}
                disabled={index === order.length - 1}
                onClick={() => move(index, index + 1)}
              >
                ↓
              </button>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function One({
  probe,
  answers,
  set,
}: {
  probe: Probe;
  answers: ProbeAnswers;
  set: (id: string, value: string | string[]) => void;
}) {
  const value = answers[probe.id];
  const limit = probe.limit || 240;
  return (
    <div className="question probe">
      <span className="field-label" id={`${probe.id}-label`}>
        {probe.question}
      </span>
      {probe.help && (
        <p className="help" id={`${probe.id}-help`}>
          {probe.help}
        </p>
      )}
      {probe.kind === "choice" && (
        <Choice
          probe={probe}
          value={value}
          onChange={(v) => set(probe.id, v)}
        />
      )}
      {probe.kind === "rank" && (
        <Rank probe={probe} value={value} onChange={(v) => set(probe.id, v)} />
      )}
      {probe.kind === "text" && (
        <>
          <textarea
            id={probe.id}
            aria-labelledby={`${probe.id}-label`}
            aria-describedby={probe.help ? `${probe.id}-help` : undefined}
            maxLength={limit}
            rows={2}
            value={typeof value === "string" ? value : ""}
            onChange={(e) => set(probe.id, e.target.value)}
          />
          <span className="char-count">
            {(typeof value === "string" ? value.length : 0)}/{limit}
          </span>
        </>
      )}
      {probe.reveal_after && value && (
        <p className="probe-reveal" role="status">
          {probe.reveal_after}
        </p>
      )}
      {probe.follow_up && opens(probe.follow_up.when, value) && (
        <div className="probe-follow-up">
          <One
            probe={probe.follow_up as Probe}
            answers={answers}
            set={set}
          />
        </div>
      )}
    </div>
  );
}

export function ProbeStep({
  probe,
  answers,
  onChange,
  step,
  total,
}: {
  probe: Probe;
  answers: ProbeAnswers;
  onChange: (answers: ProbeAnswers) => void;
  step: number;
  total: number;
}) {
  const set = (id: string, value: string | string[]) =>
    onChange({ ...answers, [id]: value });
  return (
    <section className="probes" aria-label={`Step ${step} of ${total}`}>
      <p className="probe-count">
        Step {step} of {total}
      </p>
      <One probe={probe} answers={answers} set={set} />
      <p className="probe-intro">
        Chosen from what you have already answered, on this device. Nothing is
        sent until you seal, and none of this enters the group probability.
      </p>
    </section>
  );
}
