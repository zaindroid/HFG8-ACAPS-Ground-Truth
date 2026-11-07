import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint } from "./service";
import type { EvidenceRecord } from "./Evidence";
import cardFixture from "../../fixtures/GET_e_token.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import sealFixture from "../../fixtures/POST_e_token_answer_response.json";
import confirmFixture from "../../fixtures/POST_e_token_confirm_response.json";
export type PendingAnswer = typeof sealFixture;
export type CommitmentReceipt = typeof confirmFixture;
export type Mask = "known" | "pseudonym" | "anonymous";
export type Result = Omit<typeof resultFixture, "integrity_notes">;
export type Card = Omit<
  typeof cardFixture,
  "group_view_if_round2" | "risk" | "pulse" | "mask_options"
> & {
  pulse: Omit<typeof cardFixture.pulse, "evidence"> & {
    evidence: EvidenceRecord[];
  };
  risk: typeof cardFixture.risk & {
    probability_acaps?: string;
    level?: string;
    horizon_months?: number;
  };
  mask_options: (Mask | { id: string; label: string; note?: string })[];
  accuracy_prompt?: string;
  group_view_if_round2: Result | null;
};
export type Answer = {
  mask: Mask;
  stance: "estimate" | "outside_my_expertise" | "not_enough_evidence";
  confidence: number | null;
  source_tag: "saw" | "read" | "heard" | null;
  probability: number | null;
  panel_share_yes: number | null;
  round: number;
  missing: string;
  changed_mind: boolean;
  probe_answers?: Record<string, string | string[]>;
  likelihood_word?: string | null;
  against?: string;
  trigger_pick?: string | null;
};
export const mock = import.meta.env.VITE_MOCK === "1";
export async function getCard(token: string): Promise<Card> {
  if (!mock) {
    const value = await endpoint.card(token);
    return { ...value, pulse: { ...value.pulse, evidence: value.pulse.evidence || [] } };
  }
  await new Promise((resolve) => setTimeout(resolve, 200));
  if (token === "empty")
    throw new Error(
      "This invitation has no active pulse. Ask your analyst for a new link.",
    );
  return structuredClone({
    ...cardFixture,
    pulse: { ...cardFixture.pulse, evidence: [] },
    blind: token !== "round2",
    risk:
      token === "round2"
        ? { ...cardFixture.risk, probability_acaps: "High", level: "High" }
        : cardFixture.risk,
    round: token === "round2" ? 2 : 1,
    group_view_if_round2:
      token === "round2"
        ? (({ integrity_notes, ...publicResult }) => publicResult)(
            sampleDataEnabled() ? sampleResult : resultFixture,
          )
        : null,
  });
}
export async function prepareAnswer(
  token: string,
  answer: Answer,
): Promise<PendingAnswer> {
  if (!mock) return endpoint.answer(token, answer);
  await new Promise((resolve) => setTimeout(resolve, 300));
  // Fixture receipt only: this milestone does not implement cryptographic sealing.
  return { ...structuredClone(sealFixture), summary: `${answer.stance === "estimate" ? answer.probability !== null ? `${Math.round(answer.probability*100)}% likelihood` : answer.likelihood_word?.replaceAll("_", " ") || "No estimate" : answer.stance.replaceAll("_", " ")} · ${answer.mask === "known" ? "named to ACAPS" : answer.mask === "pseudonym" ? "nickname to peers" : "no identity kept"}` };
}
export async function sealAnswer(token: string, confirmToken: string): Promise<CommitmentReceipt> {
  if (!mock) return endpoint.confirmAnswer(token, confirmToken);
  return structuredClone(confirmFixture);
}
