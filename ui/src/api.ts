import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint } from "./service";
import type { EvidenceRecord } from "./Evidence";
import cardFixture from "../../fixtures/GET_e_token.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import sealFixture from "../../fixtures/POST_e_token_answer_response.json";
export type Mask = "known" | "pseudonym" | "anonymous";
export type Result = Omit<typeof resultFixture, "integrity_notes">;
export type Card = Omit<
  typeof cardFixture,
  "group_view_if_round2" | "risk" | "pulse"
> & {
  pulse: Omit<typeof cardFixture.pulse, "evidence"> & {
    evidence: EvidenceRecord[];
  };
  risk: typeof cardFixture.risk & {
    probability_acaps?: string;
    level?: string;
  };
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
};
export const mock = import.meta.env.VITE_MOCK === "1";
export async function getCard(token: string): Promise<Card> {
  if (!mock) return endpoint.card(token);
  await new Promise((resolve) => setTimeout(resolve, 200));
  if (token === "empty")
    throw new Error(
      "This invitation has no active pulse. Ask your analyst for a new link.",
    );
  return structuredClone({
    ...cardFixture,
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
export async function sealAnswer(
  token: string,
  answer: Answer,
): Promise<typeof sealFixture> {
  if (!mock) return endpoint.answer(token, answer);
  await new Promise((resolve) => setTimeout(resolve, 300));
  // Fixture receipt only: this milestone does not implement cryptographic sealing.
  return structuredClone(sealFixture);
}
