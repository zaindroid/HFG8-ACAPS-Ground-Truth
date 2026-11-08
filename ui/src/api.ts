import { sampleDataEnabled, sampleResult } from "./demo-data";
import { endpoint } from "./service";
import type { EvidenceRecord } from "./Evidence";
import cardFixture from "../../fixtures/GET_e_token.json";
import resultFixture from "../../fixtures/GET_pulses_result.json";
import sealFixture from "../../fixtures/POST_e_token_answer_response.json";
import confirmFixture from "../../fixtures/POST_e_token_confirm_response.json";
import { getDemoInvitation, markDemoAnswered, sharedDemo, type DemoInvitation } from "./demo-invitations";
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
  if (token.startsWith("demo-")) {
    let invitation: DemoInvitation | null = getDemoInvitation(token);
    if (sharedDemo) {
      const response = await fetch(`/api/demo/invitations/${encodeURIComponent(token)}`, { cache: "no-store" });
      invitation = response.ok ? (await response.json() as { invitation: DemoInvitation }).invitation : null;
    }
    if (!invitation) throw new Error("This demo invitation is unavailable or expired. Ask the analyst for a new link.");
    if (invitation.riskId !== "R1043") throw new Error("This demo risk does not have a complete question yet.");
    return structuredClone({
      ...cardFixture,
      blind: true,
      correction_allowed_until: invitation.expiresAt,
      pulse: {
        ...cardFixture.pulse,
        asked_by: "ACAPS analyst · demo",
        expires_at: invitation.expiresAt,
        evidence: [],
        question: {
          ...cardFixture.pulse.question,
          event: "Cross-border armed incursions from Sudan significantly worsen protection and humanitarian needs",
          location: "Eastern Chad",
          threshold: "Significant deterioration in protection and humanitarian needs",
          deadline: "2027-05-07",
          text: "Will cross-border armed incursions from Sudan significantly worsen protection and humanitarian needs in eastern Chad by 7 May 2027?",
        },
      },
      group_view_if_round2: null,
    });
  }
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
  const confirmToken = crypto.randomUUID();
  sessionStorage.setItem(`ss-demo-pending-${token}`, JSON.stringify({ confirmToken, answer }));
  return { ...structuredClone(sealFixture), confirm_token: confirmToken, summary: `${answer.stance === "estimate" ? answer.probability !== null ? `${Math.round(answer.probability*100)}% likelihood` : answer.likelihood_word?.replaceAll("_", " ") || "No estimate" : answer.stance.replaceAll("_", " ")} · ${answer.mask === "known" ? "named to ACAPS" : answer.mask === "pseudonym" ? "nickname to peers" : "no identity kept"}` };
}
export async function sealAnswer(token: string, confirmToken: string): Promise<CommitmentReceipt> {
  if (!mock) return endpoint.confirmAnswer(token, confirmToken);
  const raw = sessionStorage.getItem(`ss-demo-pending-${token}`);
  if (!raw) throw new Error("The prepared answer is no longer available. Review and submit it again.");
  const pending = JSON.parse(raw) as { confirmToken: string; answer: Answer };
  if (pending.confirmToken !== confirmToken) throw new Error("The confirmation link does not match this answer.");
  if (sharedDemo) {
    const response = await fetch(`/api/demo/invitations/${encodeURIComponent(token)}/answer`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ answer: pending.answer }) });
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || "The shared demo could not confirm this answer.");
    sessionStorage.removeItem(`ss-demo-pending-${token}`);
    return value as CommitmentReceipt;
  }
  const salt = crypto.randomUUID();
  const payload = new TextEncoder().encode(JSON.stringify({ answer: pending.answer, salt }));
  const digest = await crypto.subtle.digest("SHA-256", payload);
  const commitment = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  sessionStorage.removeItem(`ss-demo-pending-${token}`);
  markDemoAnswered(token);
  return { ...structuredClone(confirmFixture), committed_at: new Date().toISOString(), commitment, correction_allowed_until: getDemoInvitation(token)?.expiresAt || new Date(Date.now() + 14 * 86400000).toISOString(), message: "Answer confirmed. This demo fingerprint is local to your browser." };
}
