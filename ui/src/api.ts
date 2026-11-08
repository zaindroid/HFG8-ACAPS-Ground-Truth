import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint } from "./service";
import type { EvidenceRecord } from "./Evidence";
import cardFixture from "../../fixtures/GET_e_token.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import draftFixture from "../../fixtures/POST_e_token_answer_response.json";
import confirmFixture from "../../fixtures/POST_e_token_confirm_response.json";
import answerKeyFixture from "../../fixtures/GET_answer_key.json";
import { seal, type AnswerKey, type Route } from "./e2e";
export type Mask = "known" | "pseudonym" | "anonymous";
/** The confirmation screen's payload. Nothing is committed when this comes back: that is the
 *  point of the two steps, and it is why a link click cannot answer for anybody. */
export type AnswerDraft = typeof draftFixture;
export type SealReceipt = typeof confirmFixture & {
  /** Set by this client, not the engine: true when the draft and the confirmation both left this
   *  device encrypted to the engine's answer key. */
  sealed_on_device?: boolean;
};
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
let answerKey: Promise<AnswerKey | null> | null = null;
/** The engine's answer key, fetched once per page. Null when the engine has switched end-to-end
 *  encryption off or cannot serve the key: the body then goes plain and the card says nothing
 *  about encryption, rather than claiming what did not happen. */
function getAnswerKey(): Promise<AnswerKey | null> {
  if (!answerKey)
    answerKey = (
      mock
        ? Promise.resolve(structuredClone(answerKeyFixture) as AnswerKey)
        : endpoint.answerKey()
    )
      .then((key) => (key.enabled ? key : null))
      .catch(() => {
        answerKey = null;
        return null;
      });
  return answerKey;
}
/** The body as it leaves the device: an envelope when there is a key, the plain body otherwise.
 *  Fixture mode runs the same encryption, so the code path is exercised, and then drops it. */
async function outgoing<T>(body: T, token: string, route: Route) {
  const key = await getAnswerKey();
  if (!key) return { body, encrypted: false };
  return { body: await seal(body, token, route, key), encrypted: true };
}
let draftEncrypted = false;
/** Step one of two. Validates the answer, prices a word into a number, and returns the line the
 *  confirmation screen repeats back. Commits nothing, which is what makes a link click, a mail
 *  scanner or a link preview harmless. The old single call cast this response to the receipt
 *  shape, so the card read committed_at and commitment off a payload that has neither. */
export async function draftAnswer(
  token: string,
  answer: Answer,
): Promise<AnswerDraft> {
  const sent = await outgoing(answer, token, "draft");
  draftEncrypted = sent.encrypted;
  if (!mock) return endpoint.answer(token, sent.body);
  await new Promise((resolve) => setTimeout(resolve, 200));
  return structuredClone(draftFixture);
}
/** Step two: the commitment. */
export async function confirmAnswer(
  token: string,
  confirmToken: string,
): Promise<SealReceipt> {
  const sent = await outgoing({ confirm_token: confirmToken }, token, "confirm");
  const sealed_on_device = draftEncrypted && sent.encrypted;
  if (!mock)
    return { ...(await endpoint.confirm(token, sent.body)), sealed_on_device };
  await new Promise((resolve) => setTimeout(resolve, 200));
  return { ...structuredClone(confirmFixture), sealed_on_device };
}
