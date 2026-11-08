import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  FileText,
  Gavel,
  Globe,
  Link2,
  Lock,
  LockOpen,
  MessageSquare,
  ScrollText,
  Send,
  ShieldCheck,
  Target,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { mock } from "./api";
import { api } from "./service";
import chainFixture from "../../fixtures/GET_risks_risk_id_chain.json";
import anchorsFixture from "../../fixtures/GET_anchors.json";
import "./audit-trail.css";

/* The process chain, for auditors. Every step of a risk is shown in plain words with its
   fingerprint and the fingerprint it is locked to. "Check in my browser" recomputes every
   fingerprint here, with the browser's own SHA-256, from exactly the data shown: the engine's
   own verdict is not taken on trust. "Try changing a step" edits a local copy only, to show
   what tampering looks like. Nothing on this page writes to the record. */

type Event = {
  seq: number;
  risk_id: string;
  kind: string;
  at: string;
  data: Record<string, unknown>;
  prev_hash: string;
  hash: string;
};
type Chain = {
  risk_id: string;
  events: Event[];
  verify: { intact: boolean; broken_at: number | null; length: number };
  hash_rule?: string;
  guarantees?: string;
  does_not?: string;
};
type Root = {
  day: string;
  status: string;
  merkle_root: string;
  verify_url?: string | null;
  log_index?: number | null;
};
type Check = { ok: boolean; brokenAt: number | null; perStep: boolean[] };

const STEP: Record<string, [LucideIcon, string]> = {
  alert_raised: [Bell, "Alert raised"],
  question_approved: [MessageSquare, "Question approved"],
  panel_invited: [Send, "Experts invited"],
  answers_sealed: [Lock, "Answers sealed"],
  revealed: [LockOpen, "Answers revealed"],
  draft_created: [FileText, "Draft created"],
  decision_recorded: [Gavel, "Analyst decision"],
  published: [ScrollText, "Published to the ledger"],
  outcome_resolved: [Target, "Outcome recorded"],
};

function detail(e: Event): string {
  const d = e.data;
  switch (e.kind) {
    case "alert_raised":
      return `${d.crisis_id ?? ""} severity ${d.old_value ?? "?"} to ${d.new_value ?? "?"}, ${d.month_from ?? ""} to ${d.month_to ?? ""}`;
    case "question_approved":
      return `Round ${d.pulse_id ?? ""} opened; the question is fixed from here`;
    case "panel_invited":
      return `${d.n_invited ?? "?"} personal links issued`;
    case "answers_sealed":
      return `${d.n_answers ?? "?"} answers sealed`;
    case "revealed":
      return `${d.n_answers ?? "?"} answers opened together`;
    case "draft_created":
      return "Cited draft written from the revealed answers";
    case "decision_recorded":
      return `Decision: ${d.decision ?? "recorded"}, with its reason fingerprinted`;
    case "published":
      return `Entry on the public ledger${d.decision ? `, ${d.decision}` : ""}`;
    case "outcome_resolved":
      return `Outcome: ${d.outcome ?? "recorded"}`;
    default:
      return e.kind.replace(/_/g, " ");
  }
}

// The engine's rule: sha256 over JSON with sorted keys and no spaces, of every field but hash.
function canonical(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  const obj = value as Record<string, unknown>;
  return `{${Object.keys(obj)
    .sort()
    .map((k) => `${JSON.stringify(k)}:${canonical(obj[k])}`)
    .join(",")}}`;
}
async function sha256(text: string): Promise<string> {
  const bytes = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return Array.from(new Uint8Array(bytes))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
async function check(events: Event[]): Promise<Check> {
  const perStep: boolean[] = [];
  let prev = "0".repeat(64);
  let brokenAt: number | null = null;
  for (const e of events) {
    const { hash, ...body } = e;
    const recomputed = await sha256(canonical(body));
    const ok = recomputed === hash && e.prev_hash === prev;
    perStep.push(ok && brokenAt === null);
    if (!ok && brokenAt === null) brokenAt = e.seq;
    prev = recomputed;
  }
  return { ok: brokenAt === null, brokenAt, perStep };
}
// The simulated edit: lower the first count the step holds, as someone hiding answers would.
function alter(data: Record<string, unknown>): Record<string, unknown> {
  const key = ["n_answers", "n_invited", "new_value"].find(
    (k) => typeof data[k] === "number",
  );
  if (key) return { ...data, [key]: (data[key] as number) - 2 };
  return { ...data, decision: "changed" };
}
const short = (h: string) => h.slice(0, 8);
const when = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

export function AuditTrail() {
  const [riskId] = useState("R1043");
  const [chain, setChain] = useState<Chain | null>(null);
  const [root, setRoot] = useState<Root | null>(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Check | null>(null);
  const [tampered, setTampered] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (mock) {
      setChain(chainFixture as unknown as Chain);
      const roots = (anchorsFixture as unknown as { roots: Root[] }).roots;
      setRoot(roots[0] || null);
      return;
    }
    api<Chain>(`/risks/${encodeURIComponent(riskId)}/chain`)
      .then(setChain)
      .catch((e) => setError((e as Error).message));
    api<{ roots: Root[] }>("/anchors")
      .then((r) => setRoot(r.roots[0] || null))
      .catch(() => setRoot(null));
  }, [riskId]);

  // A local copy with one step quietly changed, to show what an edit after the fact looks like.
  const shown: Event[] = !chain
    ? []
    : tampered && chain.events.length > 2
      ? chain.events.map((e, i) =>
          i === Math.min(3, chain.events.length - 2)
            ? { ...e, data: alter(e.data) }
            : e,
        )
      : chain.events;

  const runCheck = async (events: Event[]) => {
    setBusy(true);
    try {
      setResult(await check(events));
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    if (chain) void runCheck(shown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chain, tampered]);

  const intact = result ? result.ok : chain?.verify.intact;
  const n = shown.length;

  return (
    <Frame
      title="Audit trail"
      subtitle="Every step of a risk, locked to the one before. Check it yourself."
    >
      {error && (
        <p className="audit-error" role="alert">
          {error}
        </p>
      )}
      <section
        className={intact === false ? "audit-status broken" : "audit-status"}
        aria-live="polite"
      >
        <span className="audit-status-icon" aria-hidden="true">
          {intact === false ? (
            <AlertTriangle size={30} />
          ) : (
            <ShieldCheck size={30} />
          )}
        </span>
        <div>
          <h2>
            {intact === false
              ? `Chain broken at step ${(result?.brokenAt ?? 0) + 1}`
              : `Chain intact: ${n} of ${n} steps check`}
          </h2>
          <p>
            {tampered
              ? "One step was changed in this copy only. Every step after it no longer matches."
              : `Chad, ${riskId}. Recomputed in your browser from the data below, not taken from our server's word.`}
          </p>
        </div>
        <div className="audit-actions">
          <button
            type="button"
            onClick={() => runCheck(shown)}
            disabled={busy || !chain}
          >
            <CheckCircle2 size={17} aria-hidden="true" />
            {busy ? "Checking" : "Check in my browser"}
          </button>
          <button
            type="button"
            className={tampered ? "on" : ""}
            aria-pressed={tampered}
            onClick={() => setTampered((t) => !t)}
            disabled={!chain || (chain?.events.length ?? 0) < 3}
          >
            {tampered ? "Undo the change" : "Try changing a step"}
          </button>
        </div>
      </section>

      <ol className="audit-chain" aria-label="Steps of this risk">
        {shown.map((e, i) => {
          const [Icon, label] = STEP[e.kind] || [Link2, e.kind];
          const ok = result ? result.perStep[i] : true;
          return (
            <li key={e.seq} className={ok ? "audit-step" : "audit-step bad"}>
              <span className="audit-node" aria-hidden="true">
                <Icon size={20} />
              </span>
              <div className="audit-body">
                <div className="audit-head">
                  <b>
                    {i + 1}. {label}
                  </b>
                  <time dateTime={e.at}>{when(e.at)}</time>
                </div>
                <p>{detail(e)}</p>
                <div className="audit-hash">
                  <span title={e.hash}>
                    fingerprint <code>{short(e.hash)}</code>
                  </span>
                  <span title={e.prev_hash}>
                    locked to{" "}
                    <code>{i === 0 ? "start" : short(e.prev_hash)}</code>
                  </span>
                  <span className={ok ? "audit-ok" : "audit-bad"}>
                    {ok ? (
                      <>
                        <CheckCircle2 size={14} aria-hidden="true" /> checks
                      </>
                    ) : (
                      <>
                        <AlertTriangle size={14} aria-hidden="true" /> does not
                        match
                      </>
                    )}
                  </span>
                </div>
              </div>
            </li>
          );
        })}
        <li className="audit-step audit-log">
          <span className="audit-node" aria-hidden="true">
            <Globe size={20} />
          </span>
          <div className="audit-body">
            <div className="audit-head">
              <b>Public log</b>
              <span>{root ? root.day : ""}</span>
            </div>
            <p>
              Once a day the latest link goes into Sigstore Rekor, a public log
              nobody can edit.
            </p>
            <div className="audit-hash">
              {root?.verify_url ? (
                <a href={root.verify_url} target="_blank" rel="noreferrer">
                  Open the public entry
                  {root.log_index != null
                    ? `, log index ${root.log_index}`
                    : ""}
                </a>
              ) : (
                <span>
                  Today&rsquo;s entry: {root ? root.status : "not yet recorded"}
                  ; the link appears once the log confirms it.
                </span>
              )}
            </div>
          </div>
        </li>
      </ol>

      <section className="audit-foot">
        <div>
          <h3>What this proves</h3>
          <p>
            {chain?.guarantees ||
              "Any later change to a recorded step breaks the chain."}
          </p>
        </div>
        <div>
          <h3>What it does not</h3>
          <p>
            {chain?.does_not || "It does not prove the source data was right."}
          </p>
        </div>
        <div>
          <h3>How to check without us</h3>
          <p>
            Each fingerprint is SHA-256 over the step&rsquo;s data with sorted
            keys and no spaces, including the fingerprint before it. Any SHA-256
            tool gives the same result.
          </p>
        </div>
      </section>
    </Frame>
  );
}
