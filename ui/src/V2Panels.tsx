import { useEffect, useRef, useState } from "react";
import { mock } from "./api";
import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint } from "./service";
import { percent } from "./desk-model";
import { Section } from "./LiveWorkspace";
import type { Honesty, Integrity, Match } from "./v2-types";

export function HonestyBox({
  value,
  context,
}: {
  value?: Honesty;
  context?: string;
}) {
  if (!value || value.n < 5)
    return (
      <div className="honesty-box">
        <h3>What fed into this view</h3>
        <p>
          Honesty details are unavailable. This entry needs a confirmed group of
          at least five.
        </p>
      </div>
    );
  return (
    <section
      className="honesty-box"
      aria-label={`Public honesty box${context ? ` · ${context}` : ""}`}
    >
      <h3>What fed into this view</h3>
      <p className="panel-caption">{value.reidentification_note || "In a panel of eight, a distinctive reason may identify its author to colleagues; experts are told this before answering."}</p>
      <p className="panel-caption">Extended panel (confirmed relayed answers): {value.relayed_share === undefined ? "Not reported" : percent(value.relayed_share)}{value.channel_mix && ` · Channels: ${Object.entries(value.channel_mix).map(([channel,n])=>`${channel} ${n}`).join(", ")}`}</p>
      <div className="honesty-grid">
        <div>
          <span>Contributions</span>
          <strong>{value.n}</strong>
        </div>
        <div>
          <span>Agreement</span>
          <strong>{percent(value.agreement)}</strong>
        </div>
        <div>
          <span>Forecast spread</span>
          <strong>
            {percent(value.spread[0])}–{percent(value.spread[1])}
          </strong>
        </div>
        <div>
          <span>Claims corroborated</span>
          <strong>
            {value.claims_corroborated} / {value.claims_total}
          </strong>
        </div>
        <div>
          <span>Past panel hit rate</span>
          <strong>
            {value.panel_hit_rate === null
              ? "No track record yet"
              : percent(value.panel_hit_rate)}
          </strong>
          <small>Includes misses</small>
        </div>
        <div>
          <span>Coverage gaps</span>
          <strong>
            {value.coverage_gaps.length
              ? value.coverage_gaps.join("; ")
              : "None reported"}
          </strong>
        </div>
      </div>
      <div className="honesty-grid">
        <div>
          <span>Claims in verification queue</span>
          <strong>
            {value.claims_in_verification_queue ?? "Not supplied"}
          </strong>
        </div>
        <div>
          <span>Recorded misses</span>
          <strong>{value.misses ?? "Not supplied"}</strong>
        </div>
      </div>
      <div className="decision-use-summary">
        <h4>What decision could this inform?</h4>
        {value.decision_use ? (
          <dl>
            <div>
              <dt>Decision</dt>
              <dd>{value.decision_use.what_decision}</dd>
            </div>
            <div>
              <dt>For whom</dt>
              <dd>{value.decision_use.for_whom}</dd>
            </div>
            <div>
              <dt>By when</dt>
              <dd>{value.decision_use.by_when}</dd>
            </div>
          </dl>
        ) : (
          <p>Decision-use context not supplied.</p>
        )}
      </div>
      {value.panel_view_rejected && (
        <div className="decision-rejection">
          <h4>Panel view rejected by the analyst</h4>
          <p>{value.analyst_rationale || "Analyst rationale not supplied."}</p>
        </div>
      )}
      <p className="caveat">{value.caveat}</p>
      <p className="panel-caption">
        One validation layer among others. This view does not automatically
        change an ACAPS product. Five contributions is a disclosure rule, not an
        anonymity guarantee.
      </p>
    </section>
  );
}
export function IntegrityPanel({ pulseId }: { pulseId: string }) {
  const [value, setValue] = useState<Integrity | null>(null),
    [error, setError] = useState(""),
    [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    setValue(null);
    setError("");
    const job = mock
      ? import("../../fixtures/GET_integrity_pulse.json").then((m) =>
          sampleDataEnabled()
            ? { ...m.default, integrity_notes: sampleResult.integrity_notes }
            : m.default,
        )
      : endpoint.integrity(pulseId);
    job
      .then((v) => {
        if (active) setValue(v);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [pulseId, reload]);
  return (
    <Section title="Integrity notes">
      <p className="panel-caption">
        Moderator-only observations for analyst review. These are not diagnoses.
        No automatic penalties or changes to aggregation follow from a note.
      </p>
      {error ? (
        <>
          <p role="alert">{error}</p>
          <button onClick={() => setReload((v) => v + 1)}>
            Retry integrity checks
          </button>
        </>
      ) : value ? (
        <>
          <div className="integrity-notes">
            {value.integrity_notes?.length ? (
              value.integrity_notes.map((item, i) => (
                <article key={i}>
                  <h3>{item.kind.replaceAll("_", " ")}</h3>
                  <p>{item.text}</p>
                  <p className="panel-caption">Evidence: {item.evidence}</p>
                </article>
              ))
            ) : (
              <p>No descriptive notes supplied for this round.</p>
            )}
          </div>
        </>
      ) : (
        <p role="status">Loading integrity checks…</p>
      )}
    </Section>
  );
}
export function PanelMatch({ riskId }: { riskId: string }) {
  const generation = useRef(0);
  const [value, setValue] = useState<Match | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  async function load() {
    const ticket = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const response = mock
        ? (await import("../../fixtures/GET_panels_match.json")).default
        : await endpoint.match(riskId);
      if (response.risk_id !== riskId)
        throw new Error(
          "The API returned a panel for a different risk. Please retry.",
        );
      if (ticket === generation.current) setValue(response);
    } catch (e) {
      if (ticket === generation.current) setError((e as Error).message);
    } finally {
      if (ticket === generation.current) setLoading(false);
    }
  }
  useEffect(() => {
    generation.current++;
    setValue(null);
    setError("");
    setLoading(false);
    return () => {
      generation.current++;
    };
  }, [riskId]);
  return (
    <Section title="Panel matching">
      <p>
        Approved experts matched by geography and theme. Affiliation cap: three
        of eight. Mean Brier is the squared error of their past forecasts
        against what actually happened, so lower is better and 0.25 is chance.
        "Correct when band missed" counts the times they were on the correct
        side of even odds while the ACAPS band for that risk was not.
      </p>
      <button disabled={loading || !riskId} onClick={() => void load()}>
        {loading ? "Matching experts…" : "Preview matched panel"}
      </button>
      {error && (
        <p role="alert" className="error-box">
          {error}
        </p>
      )}
      {value && (
        <>
          <div className="composition-banner">
            Composition check:{" "}
            {value.composition.ok ? "passes" : "needs review"}
            <br />
            Geographic spread: {value.composition.geo_spread.join(", ")}
            <br />
            Themes covered: {value.composition.theme_cover.join(", ")}
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Synthetic pseudonym</th>
                  <th>Match</th>
                  <th>Coverage area</th>
                  <th>Expertise</th>
                  <th>Years</th>
                </tr>
              </thead>
              <tbody>
                {value.experts.map((e) => {
                  return (
                    <tr key={e.pseudonym}>
                      <td>{e.pseudonym}</td>
                      <td>{percent(e.match)}</td>
                      <td>
                        {e.region || e.geo_tags.join(", ")}
                        {e.languages?.length ? (
                          <small>{e.languages.join(", ")}</small>
                        ) : null}
                      </td>
                      <td>
                        {e.theme_tags.join(", ")}
                        {e.affiliation_tag ? (
                          <small>{e.affiliation_tag}</small>
                        ) : null}
                      </td>
                      <td>{e.years_experience ?? "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {value.composition.gaps.length > 0 && (
            <p className="caveat">
              Coverage gaps: {value.composition.gaps.join("; ")}
            </p>
          )}
        </>
      )}
    </Section>
  );
}
