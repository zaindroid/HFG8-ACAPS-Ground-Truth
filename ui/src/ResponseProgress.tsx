export function ResponseProgress({
  total,
  count,
  revealed,
}: {
  total: number;
  count: number;
  revealed: boolean;
}) {
  const completion =
    total > 0 ? Math.round(Math.min(1, Math.max(0, count / total)) * 100) : 0;
  return (
    <div
      className="response-progress"
      role="group"
      aria-label={`${count} of ${total} expert responses ${revealed ? "revealed" : "received"}`}
    >
      <strong>
        {count}
        <small> / {total} responses</small>
      </strong>
      <div className="response-ticks" aria-hidden="true">
        {Array.from({ length: total }, (_, i) => (
          <span key={i} className={i < count ? "filled" : ""} />
        ))}
      </div>
      <span className="response-completion">{completion}% received</span>
      <span>
        {count === 0
          ? "Waiting for responses"
          : revealed
            ? "Group view open"
            : count === total
              ? "Ready to reveal"
              : "Answers stay sealed"}
      </span>
    </div>
  );
}
