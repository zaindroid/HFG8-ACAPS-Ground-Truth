import type { Draft, Result } from "./service";
import {validResult} from "./service";
import type {EvidenceRecord} from "./Evidence";
import {ArrowRight, UsersRound, ChartNoAxesCombined} from "lucide-react";
export function DraftRecommendation({draft,current,proposed=draft.proposed_probability}:{draft:Draft;current:string;proposed?:string}){
 return <div className="draft-recommendation"><span>Proposed assessment</span><h3>{current===proposed?`Keep probability ${proposed}`:`Change probability from ${current} to ${proposed}`}</h3><p>ACAPS probability band · Risk level: {draft.proposed_level}</p></div>;
}
export function pendingClaims(
  draft: Draft,
  themes: Result["missing_themes"] = [],
  result?: Result,
) {
  return (draft.claims || []).filter((claim) => {
    const index = /missing_themes\[(\d+)\]/.exec(claim.evidence_ref);
    const theme = index ? themes[Number(index[1])] : null;
    const check = theme
      ? draft.missing_checks?.find((c) => c.theme === theme.theme)?.status
      : undefined;
    return (
      /weighted_probability$/.test(claim.evidence_ref) ||
      (claim.evidence_kind === "panel" &&
        /:mean$/.test(claim.evidence_ref) &&
        !!result &&
        (claim.evidence_ref !== `${result.pulse_id}:mean` ||
          !claim.numbers.includes(result.mean) ||
          claim.numbers.some(
            (number) => number !== result.mean && number !== result.n,
          ))) ||
      check === "uncorroborated" ||
      (theme &&
        ["single-source", "uncorroborated", "not checked"].includes(
          theme.corroboration,
        ))
    );
  });
}
export function DraftNarrative({
  draft,
  themes,
  result,
  evidence=[],
}: {
  draft: Draft;
  themes?: Result["missing_themes"];
  result?: Result;
  evidence?:EvidenceRecord[];
}) {
  const pending = pendingClaims(draft, themes, result);
  const edition=evidence.find(e=>e.metric==="index"&&typeof e.before==="number"&&typeof e.after==="number");
  const hasPanel=!!result&&validResult(result);
  const hasSummary=hasPanel||!!edition;
  return (
    <>
      {hasSummary&&<section className="draft-support" aria-label="What supports this assessment"><h3>What supports this</h3><div className="draft-facts">
        {hasPanel&&<div><UsersRound size={18} aria-hidden="true"/><div><span>Expert forecast</span><strong>{Math.round(result!.mean*100)}%</strong><p>Average forecast from {result!.n} estimates</p></div></div>}
        {edition&&<div><ChartNoAxesCombined size={18} aria-hidden="true"/><div><span>Observed severity</span><strong>{edition.before}<ArrowRight size={18} aria-hidden="true"/>{edition.after}</strong><p>{edition.month_from?.replace(/(\D+)(\d+)/,"$1 $2")} → {edition.month_to?.replace(/(\D+)(\d+)/,"$1 $2")} · index out of 10</p></div></div>}
      </div><p className="draft-facts-caption">The forecast estimates what may happen. Severity describes the crisis already observed.</p></section>}
      {/* Open by default: the summary above puts the recommendation first, but the
          analyst still has to be able to read the wording they are approving. */}
      <details className="draft-wording" open>
        <summary>Read the drafted wording</summary>
      <div className="draft-text">
        {draft.claims?.length ? (
          draft.claims
            .filter((c) => !pending.includes(c))
            .map((claim) => (
              <p key={claim.claim_id}>
                <span className="claim-kind">
                  {claim.evidence_kind === "panel"
                    ? "Panel judgement"
                    : claim.evidence_kind === "indicator"
                      ? "Observed indicator"
                      : "Source claim"}
                </span>
                {claim.text}
              </p>
            ))
        ) : (
          <p>{draft.rationale_md}</p>
        )}
      </div>
      </details>
      {pending.length > 0 && (
        <div className="to-verify">
          <h3>To verify before inclusion</h3>
          <p>{pending.length} {pending.length===1?"claim needs":"claims need"} evidence or corroboration before inclusion.</p><details><summary>Review these claims</summary>{pending.map((c) => (
            <p key={c.claim_id}>
              {c.claim_id}: {c.text}
            </p>
          ))}</details>
          <p>
            Unverified does not mean false. These claims are excluded from the draft.
          </p>
        </div>
      )}
    </>
  );
}
