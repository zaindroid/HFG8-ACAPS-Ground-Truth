import { useEffect, useState } from "react";
import { ArrowRight, Check, Clock3, Fingerprint, KeyRound, LockKeyhole, RefreshCw } from "lucide-react";
import { Frame } from "./LiveWorkspace";
import { api, type TrustStatus } from "./service";
import "./trust-overview.css";

type ChainEvent = { seq: number; kind: string; at: string; hash: string };
type Chain = { events: ChainEvent[]; verify: { intact: boolean; length: number }; head: string | null };
type Anchors = { roots: { day: string; status: string; log_url?: string | null }[] };
type Loaded = { trust: TrustStatus; chain: Chain; anchors: Anchors };

const names: Record<string, string> = {
  alert_raised: "Signal detected",
  question_approved: "Question approved",
  panel_invited: "Experts invited",
  answers_sealed: "Answers sealed",
  round_revealed: "Panel revealed",
  draft_created: "Draft checked",
  decision_recorded: "Decision recorded",
  published: "Record published",
  outcome_resolved: "Outcome recorded",
};

export function TrustOverview() {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    setBusy(true); setError("");
    try {
      const [trust, chain, anchors] = await Promise.all([
        api<TrustStatus>("/trust/status"),
        api<Chain>("/risks/R1043/chain"),
        api<Anchors>("/anchors"),
      ]);
      setLoaded({ trust, chain, anchors });
    } catch (failure) { setError((failure as Error).message); }
    finally { setBusy(false); }
  }
  useEffect(() => { void load(); }, []);
  const root = loaded?.anchors.roots.at(-1);
  const mechanisms = loaded?.trust.mechanisms || [];
  const active = (id: string) => mechanisms.find((item) => item.id === id)?.enabled;
  return <Frame title="Trust record" subtitle="How the engine protects answers and checks the case history.">
    {error && <div className="to-error" role="alert">{error} <button onClick={() => void load()}>Retry</button></div>}
    {!loaded && !error && <p role="status">Checking the trust engine…</p>}
    {loaded && <>
      <div className="to-toolbar"><span><span className="to-live"/> Live engine status</span><button onClick={() => void load()} disabled={busy}><RefreshCw size={15}/> Refresh</button></div>
      <div className="to-grid">
        <article><div className="to-icon"><KeyRound size={22}/></div><span>01 · IDENTITIES</span><h2>Protected</h2><p>Expert identity records use post-quantum key establishment.</p><strong>{active("pq_registry") ? "ML-KEM-768 active" : "Unavailable"}</strong></article>
        <article><div className="to-icon"><LockKeyhole size={22}/></div><span>02 · ANSWERS</span><h2>Encrypted</h2><p>The live expert card encrypts answers in the browser before sending.</p><strong>{active("e2e_answers") ? "Browser encryption active" : "Unavailable"}</strong></article>
        <article><div className="to-icon"><Fingerprint size={22}/></div><span>03 · PROCESS</span><h2>{loaded.chain.verify.intact ? "Intact" : "Needs review"}</h2><p>Each recorded step includes the fingerprint of the preceding step.</p><strong>{loaded.chain.verify.length} steps checked</strong></article>
        <article><div className="to-icon"><Clock3 size={22}/></div><span>04 · PUBLIC LOG</span><h2>{root?.status === "anchored" ? "Witnessed" : "Pending"}</h2><p>The day’s root is independently witnessed only after the public log accepts it.</p><strong>{root?.status === "anchored" ? "Public receipt available" : "No public receipt yet"}</strong></article>
      </div>
      <section className="to-chain"><div className="to-section-head"><div><span>R1043 · CHAD</span><h2>Case history</h2></div><div className={loaded.chain.verify.intact ? "to-valid" : "to-invalid"}><Check size={15}/>{loaded.chain.verify.intact ? "Chain checks" : "Chain broken"}</div></div>
        <ol>{loaded.chain.events.map((event) => <li key={event.seq}><span className="to-node">{event.seq + 1}</span><div><strong>{names[event.kind] || event.kind.replaceAll("_", " ")}</strong><small>{new Date(event.at).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</small></div></li>)}</ol>
      </section>
      <div className="to-next"><a href="/audit">Explore public ledger <ArrowRight size={16}/></a><a href="/trust/details">Technical details <ArrowRight size={16}/></a></div>
      <p className="to-note">This is a hash-chained record and a public transparency log, not a blockchain. It shows when records were committed; it cannot prove that an expert’s claim is true. The interactive demo case uses separate synthetic answers.</p>
    </>}
  </Frame>;
}
