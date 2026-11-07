import { useEffect, useState, useRef, type CSSProperties } from "react";
import { ArrowRight, ArrowUpRight, Check, RefreshCw } from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { Journey } from "./Journey";
import { alertService, type Shift, type Crisis } from "./alerts-service";
import { RiskLink } from "./RiskLink";
import { crisisHistory } from "./base-rates";

/** What the Risk List already records against this crisis, joined on crisis_id.
    Context for whether the shift is new ground or a repeat. */
function CrisisRecord({
  id,
  connected = [],
}: {
  id: string;
  connected?: string[];
}) {
  const history = crisisHistory(id);
  // A cross-border driver carries its own Risk List history, which is the
  // inter-country half of the picture the national figure leaves out.
  const linked = connected
    .map((other) => ({ id: other, record: crisisHistory(other) }))
    .filter((item) => item.record);
  if (!history) return null;
  const { risks, resolved, materialised, examples } = history;
  return (
    <p className="crisis-record">
      <span>
        {risks} risk{risks === 1 ? "" : "s"} on the Risk List
        {resolved > 0 && (
          <>
            {" · "}
            {materialised} of {resolved} resolved{" "}
            {materialised === 1 ? "has" : "have"} materialised
          </>
        )}
      </span>
      {linked.length > 0 && (
        <span className="crisis-precedent">
          Connected across the border:{" "}
          {linked
            .map(
              (item) =>
                `${item.id} (${item.record!.risks} risks, ${item.record!.materialised} of ${item.record!.resolved} materialised)`,
            )
            .join("; ")}
        </span>
      )}
      {examples.length > 0 && (
        <span className="crisis-precedent">
          Most recent: {examples[0].risk_id} ({examples[0].level},{" "}
          {examples[0].status.toLowerCase()}, {examples[0].entered}) —{" "}
          {examples[0].title}
        </span>
      )}
    </p>
  );
}
function Trend({ crisis, event }: { crisis: Crisis; event: Shift }) {
  const plot = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(740);
  useEffect(() => {
    const el = plot.current;
    if (!el) return;
    const measure = () => setWidth(Math.max(280, el.clientWidth));
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const values = crisis.series;
  const x = (i: number) =>
      48 + (i * (width - 76)) / Math.max(1, values.length - 1),
    y = (v: number) => 190 - v * 15;
  const marked = values.findIndex((v) => v.month === event.month_to);
  return (
    <figure className="crisis-trend">
      <figcaption>
        <strong>Severity over time</strong>
        <span>INFORM Severity · 0–10 index</span>
      </figcaption>
      <div ref={plot}>
        <svg
          viewBox={`0 0 ${width} 240`}
          role="img"
          aria-label={`${crisis.crisis_name}. Severity increased from ${event.before} in ${event.month_from} to ${event.after} in ${event.month_to}.`}
        >
          <title>Monthly INFORM Severity</title>
          <desc>
            The dashed marker identifies the edition that triggered this alert.
            Severity uses a zero to ten index.
          </desc>
          {[0, 5, 10].map((v) => (
            <g key={v}>
              <line
                x1="48"
                x2={width - 28}
                y1={y(v)}
                y2={y(v)}
                className="trend-grid"
              />
              <text x="26" y={y(v) + 4}>
                {v}
              </text>
            </g>
          ))}
          <polyline
            points={values.map((v, i) => `${x(i)},${y(v.index)}`).join(" ")}
            className="trend-line"
          />
          {marked >= 0 && (
            <g>
              <line
                x1={x(marked)}
                x2={x(marked)}
                y1="30"
                y2="190"
                className="trend-marker"
              />
              {marked > 0 && (
                <circle
                  cx={x(marked - 1)}
                  cy={y(values[marked - 1].index)}
                  r="4"
                  className="severity-before-point"
                />
              )}
              <circle
                cx={x(marked)}
                cy={y(values[marked].index)}
                r="6"
                className="severity-moving-point"
                style={
                  {
                    "--point-x": `${marked > 0 ? x(marked - 1) - x(marked) : 0}px`,
                    "--point-y": `${marked > 0 ? y(values[marked - 1].index) - y(values[marked].index) : 0}px`,
                  } as CSSProperties
                }
              />
              <text x={x(marked) + 12} y="29">
                +{event.delta} · {event.month_to}
              </text>
            </g>
          )}
          {values.map(
            (v, i) =>
              (i === 0 || i === marked || i === values.length - 1) && (
                <text key={v.month} x={x(i)} y="218" textAnchor="middle">
                  {v.month}
                </text>
              ),
          )}
        </svg>
      </div>
      <details>
        <summary>View monthly values</summary>
        <div className="trend-values">
          {values.map((v) => (
            <span key={v.month}>
              {v.month} <strong>{v.index}</strong>
            </span>
          ))}
        </div>
      </details>
    </figure>
  );
}
export function Alerts() {
  const [events, setEvents] = useState<Shift[]>([]),
    [selected, setSelected] = useState("");
  const [crisisError, setCrisisError] = useState("");
  const [crisis, setCrisis] = useState<Crisis | null>(null),
    [busy, setBusy] = useState("Loading alerts"),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const [note, setNote] = useState(""),
    [dismissing, setDismissing] = useState(false);
  const event = events.find((e) => e.id === selected);
  async function action(label: string, task: () => Promise<void>) {
    setBusy(label);
    setError("");
    try {
      await task();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  useEffect(() => {
    let active = true;
    alertService
      .list()
      .then((rows) => {
        if (active) {
          setEvents(rows);
          setSelected(rows[0]?.id || "");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setBusy("");
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    let active = true;
    setCrisis(null);
    setCrisisError("");
    setDismissing(false);
    setNote("");
    if (event)
      alertService
        .crisis(event.crisis_id)
        .then((v) => {
          if (active && v.crisis_id === event.crisis_id) setCrisis(v);
        })
        .catch((e) => {
          if (active) setCrisisError(e.message);
        });
    return () => {
      active = false;
    };
  }, [event?.crisis_id, event?.id]);
  async function run(replaying: boolean) {
    await action(
      replaying ? "Replaying April" : "Checking current editions",
      async () => {
        const response = await alertService.run(replaying);
        setEvents(response.events);
        setSelected(response.events[0]?.id || "");
        setMessage(
          `${response.month_from} → ${response.month_to} · ${response.n_crises} crises checked. ${response.note || `${response.events.length} shifts flagged.`}`,
        );
      },
    );
  }
  function update(next: Shift) {
    if (!event || next.id !== event.id)
      throw new Error(
        "The API returned a different alert. Refresh before continuing.",
      );
    setEvents((rows) => rows.map((e) => (e.id === next.id ? next : e)));
  }
  return (
    <Frame
      title="Alerts"
      subtitle="The numbers raise the question. People make the call."
    >
      <Journey active={0} />
      <div className="alerts-toolbar">
        <div>
          <strong>Changes worth a closer look</strong>
          <p>ACAPS monthly editions · ranked by change</p>
        </div>
        <div>
          <button disabled={!!busy} onClick={() => void run(false)}>
            <RefreshCw size={15} aria-hidden="true" /> Run current editions
          </button>
          <button
            className="primary"
            disabled={!!busy}
            onClick={() => void run(true)}
          >
            Replay April <ArrowRight size={15} aria-hidden="true" />
          </button>
        </div>
      </div>
      {error && (
        <p role="alert" className="error-box">
          {error}
        </p>
      )}
      <p className="alert-status" role="status">
        {busy || message}
      </p>
      {!busy && !error && !events.length && (
        <section className="alerts-empty">
          <Check size={28} />
          <h2>No shifts crossed the rules</h2>
          <p>Try the April replay to inspect the Chad severity change.</p>
        </section>
      )}
      {!!events.length && (
        <>
          <div className="shift-list" aria-label="Ranked alerts">
            {events.map((e) => (
              <button
                key={e.id}
                className={
                  e.id === selected ? "shift-row selected" : "shift-row"
                }
                aria-pressed={e.id === selected}
                onClick={() => setSelected(e.id)}
              >
                <span className="shift-rank">{e.rank_this_month}</span>
                <span>
                  <strong>
                    {e.crisis_name === "(from crises.json)"
                      ? e.crisis_id
                      : e.crisis_name}
                  </strong>
                  <small>
                    {e.month_from} → {e.month_to} ·{" "}
                    {e.risk_id || "Risk not linked"}
                  </small>
                </span>
                <span className="shift-change">
                  {e.before ?? "—"} → {e.after ?? "—"}
                  <small>
                    {e.delta > 0 ? "+" : ""}
                    {e.delta} severity
                  </small>
                </span>
                <span className="shift-state">
                  {e.status === "pulsed"
                    ? "Panel requested"
                    : e.status === "dismissed"
                      ? "Dismissed"
                      : "Needs review"}
                </span>
                <ArrowUpRight size={18} aria-hidden="true" />
              </button>
            ))}
          </div>
          {event && (
            <section className="alert-detail" aria-label="Selected alert">
              <div className="alert-detail-heading">
                <div>
                  <span>
                    {event.crisis_id === "TCD005" ? "Chad · " : ""}
                    {event.crisis_id}
                  </span>
                  <h2>
                    {event.crisis_name === "(from crises.json)"
                      ? event.crisis_id
                      : event.crisis_name}
                  </h2>
                  <p>
                    {event.month_from} → {event.month_to}
                  </p>
                  <CrisisRecord
                    id={event.crisis_id}
                    connected={event.connected_crises}
                  />
                </div>
                <div className="severity-change">
                  <strong>
                    {event.before ?? "—"}
                    <ArrowRight size={25} aria-hidden="true" />
                    {event.after ?? "—"}
                  </strong>
                  <span>
                    {event.delta > 0 ? "+" : ""}
                    {event.delta} severity index
                  </span>
                </div>
              </div>
              <div className="alert-evidence-grid">
                <div>
                  {crisis ? (
                    <Trend crisis={crisis} event={event} />
                  ) : (
                    <p className="missing-history">
                      {crisisError || "Loading crisis history…"}
                    </p>
                  )}
                </div>
                <aside className="alert-facts">
                  <div>
                    <span>Rule triggered</span>
                    <strong>{event.rule_hit}</strong>
                  </div>
                  <div>
                    <span>Change rank</span>
                    <strong>
                      {event.rank_this_month} of {event.n_crises_this_month}{" "}
                      crises
                    </strong>
                  </div>
                  <div>
                    <span>Data reliability</span>
                    <strong>{event.reliability || "Not supplied"}</strong>
                  </div>
                  <details>
                    <summary>Component changes</summary>
                    {Object.entries(event.components || {}).map(
                      ([name, values]) => (
                        <p key={name}>
                          {name.replaceAll("_", " ")}{" "}
                          <strong>
                            {values[0]} → {values[1]}
                          </strong>
                        </p>
                      ),
                    )}
                  </details>
                  <a
                    href={`https://api.acaps.org/api/v1/inform-severity-index/${encodeURIComponent(event.month_to)}/`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    ACAPS source edition <ArrowUpRight size={14} />
                  </a>
                </aside>
              </div>
              {crisis && (
                <RiskLink
                  key={crisis.crisis_id}
                  crisis={crisis}
                  onConfirmed={(record) => {
                    setCrisis(record);
                    void action("Refreshing alert routing", async () => {
                      const rows = await alertService.list();
                      setEvents((previous) =>
                        previous.map(
                          (e) =>
                            rows.find(
                              (r) =>
                                r.id === e.id && r.crisis_id === e.crisis_id,
                            ) || e,
                        ),
                      );
                    });
                  }}
                />
              )}
              <div className="alert-decision">
                <div>
                  <strong>
                    {event.status === "pulsed"
                      ? "The panel has been requested"
                      : event.status === "dismissed"
                        ? "This change was dismissed"
                        : "Does this change need expert judgement?"}
                  </strong>
                  <p>Severity is an index, not a forecast probability.</p>
                </div>
                <div>
                  {event.status === "proposed" ? (
                    <>
                      <button
                        className="primary"
                        disabled={!!busy || !event.risk_id}
                        onClick={() =>
                          void action("Requesting panel", async () => {
                            const next = await alertService.pulse(event);
                            if (!next.pulse_id || next.status !== "pulsed")
                              throw new Error(
                                "The API did not confirm a panel request.",
                              );
                            update(next);
                            setMessage(
                              "Panel requested. Continue to the analyst desk.",
                            );
                          })
                        }
                      >
                        Ask experts <ArrowRight size={16} />
                      </button>
                      <button
                        disabled={!!busy}
                        onClick={() => setDismissing((v) => !v)}
                      >
                        Dismiss
                      </button>
                    </>
                  ) : event.pulse_id ? (
                    <a
                      className="button-link primary"
                      href={`/desk?risk_id=${encodeURIComponent(event.risk_id || "")}&pulse_id=${encodeURIComponent(event.pulse_id)}`}
                    >
                      Open analyst desk <ArrowRight size={16} />
                    </a>
                  ) : null}
                </div>
              </div>
              {dismissing && event.status === "proposed" && (
                <form
                  className="dismiss-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (note.trim())
                      void action("Saving dismissal", async () => {
                        const next = await alertService.dismiss(
                          event,
                          note.trim(),
                        );
                        if (next.status !== "dismissed")
                          throw new Error("The API did not confirm dismissal.");
                        update(next);
                        setDismissing(false);
                        setMessage("Alert dismissed with your note.");
                      });
                  }}
                >
                  <label htmlFor="dismiss-note">Why dismiss this change?</label>
                  <textarea
                    id="dismiss-note"
                    required
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                  <button disabled={!!busy || !note.trim()}>
                    Save dismissal
                  </button>
                </form>
              )}
            </section>
          )}
        </>
      )}
    </Frame>
  );
}
