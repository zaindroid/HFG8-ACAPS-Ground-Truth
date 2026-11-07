import { ChartColumnIncreasing, MessagesSquare, SearchCheck, NotebookPen } from "lucide-react";
import type { Result } from "./service";
export function RevealOverview({result,rationale,onRationale}:{result:Result;rationale:string;onRationale:(value:string)=>void}) {
  return <section id="reveal-overview" className="reveal-overview" aria-label="Four-column reveal review">
    <div className="reveal-overview-heading"><h2>What the panel tells us</h2><p>Interpret · evaluate evidence and plausibility</p></div>
    <div className="reveal-columns">
      <article><ChartColumnIncreasing size={21} aria-hidden="true"/><h3>Agreement</h3><strong>{Math.round(result.mean*100)}%</strong><p>Equal-weight mean · {result.n_estimates??result.n} estimates</p><small>Range {Math.round(result.spread.min*100)}–{Math.round(result.spread.max*100)}%. Agreement is not proof.</small></article>
      <article><MessagesSquare size={21} aria-hidden="true"/><h3>Disagreement</h3>{result.disagreement?.length?result.disagreement.map((item,i)=><p key={i}>{item.summary}</p>):<p>No unattributed disagreement summary supplied.</p>}<small>Summaries are unattributed. Distinctive original wording stays in the verification queue.</small></article>
      <article><SearchCheck size={21} aria-hidden="true"/><h3>Missing evidence</h3>{result.missing_evidence?.length?<ul>{result.missing_evidence.map((item,i)=><li key={i}>{item.theme} <small>({item.n} mentions)</small></li>)}</ul>:<p>No missing-evidence summary supplied.</p>}<small>{result.verification_queue_count??0} items await verification. Unverified does not mean false.</small></article>
      <article><NotebookPen size={21} aria-hidden="true"/><h3>Analyst rationale</h3><label htmlFor="reveal-rationale">What should change, and why?</label><textarea id="reveal-rationale" maxLength={500} value={rationale} onChange={e=>onRationale(e.target.value)} placeholder="Record how you weighed agreement, disagreement and gaps."/><small>This note carries into your decision. Nothing publishes automatically.</small></article>
    </div>
  </section>;
}
