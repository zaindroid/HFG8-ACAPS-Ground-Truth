// Walking the three-step card.
//
// Every decision here reads the expert's own answers on this card and nothing else. The
// rules arrive with the card and are evaluated on the device, so no partial answer leaves
// the phone before the Seal and the branching still works on a bad connection.

export type Probe = {
  id: string;
  kind: "choice" | "text" | "rank";
  question: string;
  help?: string;
  limit?: number;
  reveal_after?: string;
  options?: { value: string; label: string; dk?: boolean }[];
  follow_up?: Omit<Probe, "follow_up"> & { when: string | string[] };
};
export type Rule = {
  step: number;
  probe: string;
  after?: string;
  otherwise?: boolean;
  why?: string;
  when?: {
    gap_at_least?: number;
    confidence_at_most?: number;
    probability_at_least?: number;
    probability_at_most?: number;
    answered?: boolean;
  };
};
export type ProbeFlow = {
  max_steps: number;
  bank: Record<string, Probe>;
  rules: Rule[];
  note?: string;
};
export type ProbeAnswers = Record<string, string | string[]>;

/** The core answers a rule may read. All of them are this expert's own. */
export type CoreState = {
  stance: string;
  probability: number;
  panelShare: number;
  confidence: number;
};

function matches(rule: Rule, core: CoreState, previousAnswer?: string | string[]) {
  if (rule.otherwise) return true;
  const when = rule.when;
  if (rule.after && !when) return true;
  if (!when) return false;
  // The expert's own estimate against their own guess at the panel: a gap means they
  // believe they hold a view the others do not. No peer value is involved.
  if (when.gap_at_least !== undefined) {
    return Math.abs(core.probability - core.panelShare) >= when.gap_at_least;
  }
  if (when.confidence_at_most !== undefined)
    return core.confidence <= when.confidence_at_most;
  if (when.probability_at_least !== undefined)
    return core.probability >= when.probability_at_least;
  if (when.probability_at_most !== undefined)
    return core.probability <= when.probability_at_most;
  if (when.answered !== undefined) {
    const given =
      typeof previousAnswer === "string"
        ? previousAnswer.trim().length > 0
        : Array.isArray(previousAnswer) && previousAnswer.length > 0;
    return given === when.answered;
  }
  return false;
}

/**
 * Which probe this step lands on, or null when the flow should end.
 * `chain` is the probes already shown, so step 3 can read what step 2 asked.
 */
export function probeForStep(
  flow: ProbeFlow | undefined,
  step: number,
  core: CoreState,
  answers: ProbeAnswers,
  chain: string[],
): Probe | null {
  if (!flow?.rules?.length) return null;
  // An abstention is a complete answer. Asking two more questions after it is how a
  // one-minute card turns into a survey.
  if (core.stance !== "estimate") return null;
  const previousId = chain[chain.length - 1];
  for (const rule of flow.rules) {
    if (rule.step !== step) continue;
    if (rule.after && rule.after !== previousId) continue;
    if (chain.includes(rule.probe)) continue;
    if (!matches(rule, core, previousId ? answers[previousId] : undefined)) continue;
    const probe = flow.bank[rule.probe];
    if (probe) return probe;
  }
  return null;
}

/** How many steps this card will actually run, so progress can be honest about it. */
export function plannedSteps(
  flow: ProbeFlow | undefined,
  core: CoreState,
  answers: ProbeAnswers,
): number {
  if (core.stance !== "estimate") return 1;
  // Simulated from an empty chain, not from where the expert currently is. Walking the
  // live chain would re-ask step 2 with step 2 already in it, find nothing, and report a
  // one-step card -- which also flips the button to Submit before the end.
  let total = 1;
  const walked: string[] = [];
  for (let step = 2; step <= (flow?.max_steps || 1); step++) {
    const probe = probeForStep(flow, step, core, answers, walked);
    if (!probe) break;
    walked.push(probe.id);
    total = step;
  }
  return total;
}
