import type { Draft, Result } from "./service";
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
}: {
  draft: Draft;
  themes?: Result["missing_themes"];
  result?: Result;
}) {
  const pending = pendingClaims(draft, themes, result);
  return (
    <>
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
      {pending.length > 0 && (
        <div className="to-verify">
          <h3>To verify before inclusion</h3>
          {pending.map((c) => (
            <p key={c.claim_id}>
              {c.claim_id}: {c.text}
            </p>
          ))}
          <p>
            These claims need exact provenance, compatible aggregate values or
            corroboration before approval. Uncorroborated does not mean false;
            absence from selected databases is not evidence of falsity.
          </p>
        </div>
      )}
    </>
  );
}
