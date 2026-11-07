import type { Draft, Result } from "./service";
import { validResult } from "./service";
import type { EvidenceRecord } from "./Evidence";
import { UsersRound, ChartNoAxesCombined } from "lucide-react";
import { SeverityVisual } from "./SeverityVisual";
export function DraftRecommendation({
  draft,
  current,
  proposed = draft.proposed_probability,
}: {
  draft: Draft;
  current: string;
  proposed?: string;
}) {
  return (
    <div className="draft-recommendation">
      <span>Proposed assessment</span>
      <h3>
        {current === proposed
          ? `Keep probability ${proposed}`
          : `Change probability from ${current} to ${proposed}`}
      </h3>
      <p>ACAPS probability band · Risk level: {draft.proposed_level}</p>
    </div>
  );
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
  evidence = [],
  showFacts = true,
}: {
  draft: Draft;
  themes?: Result["missing_themes"];
  result?: Result;
  evidence?: EvidenceRecord[];
  showFacts?: boolean;
}) {
  const pending = pendingClaims(draft, themes, result);
  const edition = evidence.find(
    (e) =>
      e.metric === "index" &&
      typeof e.before === "number" &&
      typeof e.after === "number",
  );
  const hasPanel = !!result && validResult(result);
  const hasSummary = hasPanel || !!edition;
  return (
    <>
      {hasSummary && showFacts && (
        <section
          className="draft-support"
          aria-label="What supports this assessment"
        >
          <h3>What supports this</h3>
          <div className="draft-facts">
            {hasPanel && (
              <div>
                <UsersRound size={18} aria-hidden="true" />
                <div>
                  <span>Expert forecast</span>
                  <strong>{Math.round(result!.mean * 100)}%</strong>
                  <p>
                    Average forecast from {result!.n_estimates ?? result!.n}{" "}
                    estimates
                  </p>
                </div>
              </div>
            )}
            {edition && (
              <div>
                <ChartNoAxesCombined size={18} aria-hidden="true" />
                <div>
                  <span>Observed severity</span>
                  <SeverityVisual
                    before={edition.before!}
                    after={edition.after!}
                    from={edition.month_from}
                    to={edition.month_to}
                  />
                </div>
              </div>
            )}
          </div>
          <p className="draft-facts-caption">
            Forecast = what may happen. Severity = what has been observed.
          </p>
        </section>
      )}
      <div className="draft-plain-summary">
        <h3>What this means</h3>
        {hasPanel && (
          <p>
            Experts estimate a{" "}
            <strong>{Math.round(result!.mean * 100)}% chance</strong> of the
            defined event. This is an average forecast, not a vote count.
          </p>
        )}
        {edition && (
          <p>
            ACAPS recorded a change in severity. It provides context for the
            review, not a probability of what happens next.
          </p>
        )}
      </div>
      <details className="draft-wording">
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
                  {hasPanel && /:mean$/.test(claim.evidence_ref)
                    ? `The average expert estimate is ${Math.round(result!.mean * 100)}%, based on ${result!.n_estimates ?? result!.n} forecasts.`
                    : edition &&
                        claim.evidence_kind === "indicator" &&
                        claim.numbers.includes(edition.before!) &&
                        claim.numbers.includes(edition.after!)
                      ? `ACAPS recorded severity of ${edition.before} before this edition and ${edition.after} afterward, on a scale from 0 to 10.`
                      : claim.text}
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
          <p>
            {pending.length}{" "}
            {pending.length === 1 ? "claim needs" : "claims need"} evidence or
            corroboration before inclusion.
          </p>
          <details>
            <summary>Review these claims</summary>
            {pending.map((c) => (
              <p key={c.claim_id}>
                {c.claim_id}: {c.text}
              </p>
            ))}
          </details>
          <p>
            Unverified does not mean false. These claims are excluded from the
            draft.
          </p>
        </div>
      )}
    </>
  );
}
