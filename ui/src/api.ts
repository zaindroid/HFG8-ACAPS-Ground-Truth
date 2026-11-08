import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint, type TrustStatus } from "./service";
import type { EvidenceRecord } from "./Evidence";
import cardFixture from "../../fixtures/GET_e_token.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import draftFixture from "../../fixtures/POST_e_token_answer_response.json";
import confirmFixture from "../../fixtures/POST_e_token_confirm_response.json";
import trustFixture from "../../fixtures/GET_trust_status.json";
export type Mask = "known" | "pseudonym" | "anonymous";
/** The confirmation screen's payload. Nothing is committed when this comes back: that is the
 *  point of the two steps, and it is why a link click cannot answer for anybody. */
export type AnswerDraft = typeof draftFixture;
export type SealReceipt = typeof confirmFixture;
/** What round 2 shows: the anonymised spread and the unattributed disagreement summary. Not the
 *  ACAPS band -- that first appears in the feedback message after the reveal. */
export type GroupView = {
  n: number;
  mean: number;
  spread: { min: number; max: number; iqr: number };
  distribution: { bucket: string; count: number }[];
  disagreement: {
    position: "lower" | "higher";
    n: number;
    summary: string;
    written_from: string;
    distance_from_mean: number;
  }[];
  acaps_band_shown: boolean;
};
export type Result = Omit<
  typeof resultFixture,
  "integrity_notes" | "probe_summary"
>;
export type Card = Omit<
  typeof cardFixture,
  "group_view_if_round2" | "risk" | "pulse"
> & {
  // The alert evidence is absent from the card until the expert has answered -- withheld with
  // the band, for the same reason (section 6a). Optional here, not empty.
  pulse: typeof cardFixture.pulse & { evidence?: EvidenceRecord[] };
  risk: typeof cardFixture.risk & {
    probability_acaps?: string;
    level?: string;
  };
  group_view_if_round2: GroupView | null;
};
export type Answer = {
  mask: Mask;
  stance: "estimate" | "outside_my_expertise" | "not_enough_evidence";
  /** One of five words, each printed with its percentage range. `probability` stays the optional
   *  exact number; with only a word the engine uses that band's midpoint and says so in every
   *  payload that carries the number. */
  likelihood_word?: string | null;
  against?: string;
  trigger_pick?: string | null;
  confidence: number | null;
  source_tag: "saw" | "read" | "heard" | null;
  probability: number | null;
  panel_share_yes: number | null;
  round: number;
  missing: string;
  changed_mind: boolean;
  probe_answers?: Record<string, string | string[]>;
};
export const mock = import.meta.env.VITE_MOCK === "1";
/** The public home states the stack rather than describing it, so fixture mode has to be able to
 *  state it too. Without this seam the landing page falls back to its engine-unreachable notice
 *  in every fixture-mode run -- including the ones the evidence screenshots come from -- and the
 *  first screen of the product would be a sentence about an engine that is not answering. */
export async function getTrustStatus(): Promise<TrustStatus> {
  if (!mock) return endpoint.trust();
  return structuredClone(trustFixture) as unknown as TrustStatus;
}

export async function getCard(token: string): Promise<Card> {
  if (!mock) return endpoint.card(token);
  await new Promise((resolve) => setTimeout(resolve, 200));
  if (token === "empty")
    throw new Error(
      "This invitation has no active pulse. Ask your analyst for a new link.",
    );
  const full = sampleDataEnabled() ? sampleResult : resultFixture;
  return structuredClone({
    ...cardFixture,
    blind: token !== "round2",
    // v3.4 took the band out of round 2 as well: the expert sees it once, in the feedback after
    // the deadline. Showing it here would anchor the revision round 2 exists to collect.
    risk: cardFixture.risk,
    round: token === "round2" ? 2 : 1,
    group_view_if_round2:
      token === "round2"
        ? {
            n: full.n,
            mean: full.mean,
            spread: full.spread,
            distribution: full.distribution,
            disagreement: (full.disagreement ??
              []) as GroupView["disagreement"],
            acaps_band_shown: false,
          }
        : null,
  });
}
/** Step one of two. Validates the answer, prices a word into a number, and returns the line the
 *  confirmation screen repeats back. Commits nothing, which is what makes a link click, a mail
 *  scanner or a link preview harmless. The old single call cast this response to the receipt
 *  shape, so the card read committed_at and commitment off a payload that has neither. */
export async function draftAnswer(
  token: string,
  answer: Answer,
): Promise<AnswerDraft> {
  if (!mock) return endpoint.answer(token, answer);
  await new Promise((resolve) => setTimeout(resolve, 200));
  return structuredClone(draftFixture);
}
/** Step two: the commitment. */
export async function confirmAnswer(
  token: string,
  confirmToken: string,
): Promise<SealReceipt> {
  if (!mock) return endpoint.confirm(token, confirmToken);
  await new Promise((resolve) => setTimeout(resolve, 200));
  return structuredClone(confirmFixture);
}
