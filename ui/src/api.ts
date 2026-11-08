import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint, type SealReceipt } from "./service";
import type { EvidenceRecord } from "./Evidence";
import cardFixture from "../../fixtures/GET_e_token.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import draftFixture from "../../fixtures/POST_e_token_answer_response.json";
import confirmFixture from "../../fixtures/POST_e_token_confirm_response.json";
export type Mask = "known" | "pseudonym" | "anonymous";
export type Result = Omit<typeof resultFixture, "integrity_notes">;
export type Card = Omit<
  typeof cardFixture,
  "group_view_if_round2" | "risk" | "pulse"
> & {
  // The alert evidence is absent from the card until the expert has answered -- hidden with the
  // band, for the same reason (MASTER_PROMPT 6a). So it is optional here, not empty.
  pulse: typeof cardFixture.pulse & { evidence?: EvidenceRecord[] };
  // And the band is never on the card in either round. These stay optional only because an
  // older engine may still send them; nothing in the UI reads them.
  risk: typeof cardFixture.risk & {
    probability_acaps?: string;
    level?: string;
  };
  group_view_if_round2: GroupView | null;
};
/** What round 2 shows: the anonymised spread and the unattributed disagreement summary. Not the
 *  ACAPS band -- that first appears in the feedback message after the reveal. */
export type GroupView = {
  n: number;
  mean: number;
  spread: { min: number; max: number; iqr: number };
  distribution: { bucket: string; count: number }[];
  disagreement: Disagreement[];
  acaps_band_shown: boolean;
};
export type Disagreement = {
  position: "lower" | "higher";
  n: number;
  summary: string;
  written_from: string;
  distance_from_mean: number;
};
export type LikelihoodWord = (typeof cardFixture.likelihood_words)[number];
/** The confirmation screen's own payload. Nothing is committed when this comes back: that is the
 *  point of the two steps (v3.4, section 5). */
export type AnswerDraft = typeof draftFixture;
export type Answer = {
  mask: Mask;
  stance: "estimate" | "outside_my_expertise" | "not_enough_evidence";
  /** The one required input: one of five words. `probability` is the optional exact number for
   *  people who think in percentages; with only a word the engine uses the band midpoint and
   *  says so in every payload that carries the number. */
  likelihood_word: LikelihoodWord["id"] | null;
  confidence: "not sure" | "fairly sure" | "sure" | number | null;
  source_tag: "saw" | "read" | "heard" | null;
  probability: number | null;
  panel_share_yes: number | null;
  round: number;
  missing: string;
  against?: string;
  trigger_pick?: string | null;
  probe_answers?: Record<string, string | string[]>;
  changed_mind: boolean;
};
export const mock = import.meta.env.VITE_MOCK === "1";
/** What a round-2 card may see of the group: never the moderator-only integrity notes. The
 *  plain fixture no longer carries them and the sample does, so this handles both. */
function publicPart<T extends object>(value: T): Omit<T, "integrity_notes"> {
  const { integrity_notes: _moderatorOnly, ...rest } = value as T & {
    integrity_notes?: unknown;
  };
  return rest as Omit<T, "integrity_notes">;
}
export async function getCard(token: string): Promise<Card> {
  if (!mock) return endpoint.card(token);
  await new Promise((resolve) => setTimeout(resolve, 200));
  if (token === "empty")
    throw new Error(
      "This invitation has no active pulse. Ask your analyst for a new link.",
    );
  const full = publicPart(sampleDataEnabled() ? sampleResult : resultFixture);
  return structuredClone({
    ...cardFixture,
    round: token === "round2" ? 2 : 1,
    // Round 2 opens with the group and still no band. The mock mirrors that rather than adding
    // the rating back, which is what the old round-2 branch here did.
    group_view_if_round2:
      token === "round2"
        ? {
            n: full.n,
            mean: full.mean,
            spread: full.spread,
            distribution: full.distribution,
            disagreement: (full.disagreement ?? []) as Disagreement[],
            acaps_band_shown: false,
          }
        : null,
  });
}
/** Step one of two. Validates the answer, prices a word into a number, and hands back the line
 *  the confirmation screen repeats. Commits nothing: a link click cannot answer for anybody. */
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
