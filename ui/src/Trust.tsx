/**
 * MASTER_PROMPT sections 6c and 6d, on the product surface.
 *
 * Every claim on this page is rendered from the engine's own payload, including the "guarantees"
 * and "does not" sentences. Nothing here restates them in the frontend's words, because a second
 * copy of a careful sentence is how a careful sentence turns into a loose one.
 */
import { useEffect, useState } from "react";
import { Check, LockKeyhole, Minus, RefreshCw } from "lucide-react";
import { Frame, Section } from "./LiveWorkspace";
import {
  endpoint,
  type AccessEntry,
  type AnchorRoot,
  type Mechanism,
  type PatternReport,
  type TrustStatus,
} from "./service";

type Loaded = {
  trust: TrustStatus;
  log: AccessEntry[];
  anchors: AnchorRoot[];
  patterns: PatternReport[];
  waiting: { panel_id: string; n_pulses_revealed: number }[];
  never: string;
};

function Guarantee({
  guarantees,
  does_not,
}: {
  guarantees: string;
  does_not: string;
}) {
  return (
    <dl className="guarantee">
      <div>
        <dt>Guarantees</dt>
        <dd>{guarantees}</dd>
      </div>
      <div>
        <dt>Does not</dt>
        <dd>{does_not}</dd>
      </div>
    </dl>
  );
}

function MechanismCard({ mechanism }: { mechanism: Mechanism }) {
  return (
    <article className="mechanism">
      <header>
        <span className="mechanism-number">{mechanism.number}</span>
        <h3>{mechanism.name}</h3>
        <span
          className={mechanism.enabled ? "flag-on" : "flag-off"}
          title={mechanism.flag || "always on"}
        >
          {mechanism.enabled ? <Check size={14} /> : <Minus size={14} />}
          {mechanism.flag
            ? `${mechanism.flag} ${mechanism.enabled ? "on" : "off"}`
            : "always on"}
        </span>
      </header>
      {/* Outside the header: inside it the flag chip squeezed this line into a narrow column. */}
      <p className="mechanism-build">{mechanism.build}</p>
      <Guarantee
        guarantees={mechanism.guarantees}
        does_not={mechanism.does_not}
      />
      <p className="mechanism-shows">Shown in: {mechanism.where_it_shows}</p>
    </article>
  );
}

export function Trust() {
  const [state, setState] = useState<Loaded | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError("");
    try {
      const [trust, log, anchors, patterns] = await Promise.all([
        endpoint.trust(),
        endpoint.accessLog(),
        endpoint.anchors(),
        endpoint.patterns(),
      ]);
      setState({
        trust,
        log: log.entries,
        anchors: anchors.roots,
        patterns: patterns.panels,
        waiting: patterns.not_yet,
        never: patterns.never,
      });
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Could not read the trust status.",
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <Frame
      title="Trust and privacy engineering"
      subtitle="What each mechanism guarantees, and what it does not. Eight mechanisms, and the panel-level pattern reports."
    >
      {error && (
        <section className="workspace-panel">
          <p role="alert">{error}</p>
          <button onClick={() => void load()} disabled={busy}>
            <RefreshCw size={15} /> Try again
          </button>
        </section>
      )}

      {state && (
        <>
          <Section title="The eight mechanisms">
            <div className="mechanism-grid">
              {state.trust.mechanisms.map((mechanism) => (
                <MechanismCard key={mechanism.id} mechanism={mechanism} />
              ))}
            </div>
            <p className="panel-note">
              We do not run a blockchain. We use two ideas from that world and
              say what each proves: the sealed envelope you can check later, and
              a public timestamp on a daily root.
            </p>
          </Section>

          <Section title="Identity registry">
            <p className="registry-lock">
              <LockKeyhole size={16} aria-hidden="true" />{" "}
              {state.trust.registry.lock_line}
            </p>
            <dl className="trust-figures">
              <div>
                <dt>Suite</dt>
                <dd>{state.trust.registry.suite}</dd>
              </div>
              <div>
                <dt>Key id</dt>
                <dd className="mono">
                  {state.trust.registry.key_id || "none"}
                </dd>
              </div>
              <div>
                <dt>Key holder</dt>
                <dd>{state.trust.registry.key_holder}</dd>
              </div>
              <div>
                <dt>Identities held</dt>
                <dd>{state.trust.registry.n_identities}</dd>
              </div>
            </dl>
            <Guarantee
              guarantees={state.trust.registry.guarantees}
              does_not={state.trust.registry.does_not}
            />
          </Section>

          <Section title={`Registry access log (${state.log.length})`}>
            {state.log.length === 0 ? (
              <p>No identity has been opened on this instance.</p>
            ) : (
              <table className="trust-table">
                <caption>
                  Every read of the identity map, with who asked and why. The
                  log is the control; it does not prevent an authorised read.
                </caption>
                <thead>
                  <tr>
                    <th scope="col">When</th>
                    <th scope="col">Who</th>
                    <th scope="col">Why</th>
                    <th scope="col">Record</th>
                  </tr>
                </thead>
                <tbody>
                  {state.log.map((entry, index) => (
                    <tr key={`${entry.at}-${index}`}>
                      <td className="mono">{entry.at}</td>
                      <td>{entry.who}</td>
                      <td>{entry.why}</td>
                      <td className="mono">{entry.expert_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Section>

          <Section title="Credentials">
            <dl className="trust-figures">
              <div>
                <dt>Scheme</dt>
                <dd>{state.trust.credentials.scheme}</dd>
              </div>
              <div>
                <dt>Issued</dt>
                <dd>{state.trust.credentials.n_issued}</dd>
              </div>
              <div>
                <dt>Spent</dt>
                <dd>{state.trust.credentials.n_spent}</dd>
              </div>
              <div>
                <dt>Issued unlinkably</dt>
                <dd>{state.trust.credentials.n_unlinkable_issued}</dd>
              </div>
            </dl>
            <p className="panel-note">{state.trust.credentials.linkage_note}</p>
          </Section>

          <Section title="Public timestamp">
            {state.anchors.length === 0 ? (
              <p>
                No commitments sealed yet, so there is no daily root to anchor.
              </p>
            ) : (
              <table className="trust-table">
                <caption>
                  One fingerprint per day over that day&rsquo;s sealed answers,
                  entered into the Sigstore public log. A pending root proves
                  nothing on its own.
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Day</th>
                    <th scope="col">Root</th>
                    <th scope="col">Commitments</th>
                    <th scope="col">Status</th>
                    <th scope="col">What it means</th>
                    <th scope="col">Public entry</th>
                  </tr>
                </thead>
                <tbody>
                  {state.anchors.map((root) => (
                    <tr key={root.day}>
                      <td>{root.day}</td>
                      <td className="mono">
                        {root.merkle_root.slice(0, 16)}&hellip;
                      </td>
                      <td>{root.n_commitments}</td>
                      <td>
                        <span
                          className={
                            root.status === "anchored" ? "flag-on" : "flag-off"
                          }
                        >
                          {root.status}
                        </span>
                      </td>
                      <td>{root.means}</td>
                      <td>
                        {root.verify_url ? (
                          <a
                            href={root.verify_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Log index {root.log_index}
                          </a>
                        ) : (
                          "None yet"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Section>

          <Section title="Outcome attestations">
            <dl className="trust-figures">
              <div>
                <dt>Scheme</dt>
                <dd>{state.trust.attestation_key.scheme}</dd>
              </div>
              <div>
                <dt>Public key id</dt>
                <dd className="mono">{state.trust.attestation_key.key_id}</dd>
              </div>
            </dl>
            <p className="panel-note">{state.trust.attestation_key.note}</p>
          </Section>

          <Section title="Pattern reports (panel-level)">
            <p className="panel-note">{state.never}</p>
            {state.patterns.length === 0 ? (
              <p>
                No report has opened yet. A report needs at least three revealed
                rounds on the same panel.
              </p>
            ) : (
              <div className="pattern-grid">
                {state.patterns.map((report) => (
                  <article className="pattern-report" key={report.panel_id}>
                    <header>
                      <h3>{report.panel_id}</h3>
                      <span>
                        {report.n_pulses_revealed} revealed · {report.n_experts}{" "}
                        members
                      </span>
                    </header>
                    {report.sentences.length === 0 ? (
                      <p className="pattern-quiet">Nothing here stands out.</p>
                    ) : (
                      <ul>
                        {report.sentences.map((sentence) => (
                          <li key={sentence}>{sentence}</li>
                        ))}
                      </ul>
                    )}
                    {report.by_affiliation.length > 0 && (
                      <ul className="pattern-affiliations">
                        {report.by_affiliation.map((group) => (
                          <li key={group.affiliation_tag}>
                            <strong>
                              {group.affiliation_tag} (n = {group.n})
                            </strong>{" "}
                            {group.sentence}
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                ))}
              </div>
            )}
            {state.waiting.length > 0 && (
              <p className="panel-note">
                Below the floor, so no report:{" "}
                {state.waiting
                  .map(
                    (row) =>
                      `${row.panel_id} (${row.n_pulses_revealed} revealed)`,
                  )
                  .join(", ")}
                .
              </p>
            )}
          </Section>

          <Section title="Zero-knowledge membership">
            <p className="panel-note">
              <strong>Proof verifier: {state.trust.zk.proof_verifier}.</strong>{" "}
              The group and the per-pulse nullifier are built and enforced; the
              Groth16 check is not, which is why the flag ships off.
            </p>
            <dl className="trust-figures">
              <div>
                <dt>Flag</dt>
                <dd>{state.trust.zk.enabled ? "FF_ZK on" : "FF_ZK off"}</dd>
              </div>
              <div>
                <dt>Groups</dt>
                <dd>{state.trust.zk.groups.length}</dd>
              </div>
              <div>
                <dt>Nullifiers used</dt>
                <dd>{state.trust.zk.n_nullifiers_used}</dd>
              </div>
            </dl>
            <Guarantee
              guarantees={state.trust.zk.guarantees}
              does_not={state.trust.zk.does_not}
            />
          </Section>
        </>
      )}
      {!state && !error && (
        <p role="status">Reading the trust status&hellip;</p>
      )}
    </Frame>
  );
}
