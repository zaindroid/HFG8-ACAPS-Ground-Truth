import type { Result } from "./service";
import { bandRate } from "./base-rates";

type IntegrityNote = { kind: string; text: string; evidence: string };

const pct = (value: number) => `${Math.round(value * 100)}%`;

/** How far apart the regions are, when the gap is wide enough to matter.
    A single national figure reports none of the regions it averages. */
export function spreadNote(result: Result): string | null {
  const shown = (result.agreement_by_region || []).filter(
    (region) => region.n >= 3 && region.mean !== null,
  );
  if (shown.length < 2) return null;
  const means = shown.map((region) => region.mean as number);
  const range = Math.max(...means) - Math.min(...means);
  if (range <= 0.1) return null;
  const high = shown.find((r) => r.mean === Math.max(...means))!;
  const low = shown.find((r) => r.mean === Math.min(...means))!;
  return `${pct(range)} between ${high.region} and ${low.region}. Experts inside one country do not see one situation, and the national mean of ${pct(result.mean)} reports neither of them.`;
}

/**
 * Which expertise a raised theme calls for. A plain keyword table rather than a
 * model, so the analyst can see why a theme was routed the way it was and argue
 * with it. Order matters: the first match wins.
 */
const TOPICS: { tag: string; words: string[] }[] = [
  { tag: "displacement", words: ["refugee", "displace", "camp", "influx", "arrival", "return"] },
  { tag: "conflict", words: ["militia", "attack", "raid", "armed", "shelling", "drone", "incursion", "clash"] },
  { tag: "humanitarian access", words: ["access", "road", "rains", "seasonal", "convoy", "crossing", "border post"] },
  { tag: "food security", words: ["food", "harvest", "market", "price", "crop", "livestock"] },
  { tag: "health", words: ["health", "clinic", "cholera", "disease", "outbreak", "measles"] },
  { tag: "WASH", words: ["water", "sanitation", "wash", "latrine", "borehole"] },
  { tag: "protection", words: ["protection", "gbv", "child", "abuse", "trafficking", "detention"] },
  { tag: "shelter", words: ["shelter", "housing", "site", "tent"] },
];

export function topicFor(theme: string): string | null {
  const text = theme.toLowerCase();
  for (const topic of TOPICS) {
    if (topic.words.some((word) => text.includes(word))) return topic.tag;
  }
  return null;
}

/**
 * Every step between the sealed answers and the proposed band, with what each one
 * returned. Steps that changed nothing say so: the headline stays the equal-weight
 * mean, and the rest are checks around it rather than a formula that replaces it.
 */
export function MethodChain({
  result,
  reference,
}: {
  result: Result;
  reference: string;
}) {
  const past = bandRate(reference);
  const weightShift = Math.abs(result.weighted_mean - result.mean);
  const steps = [
    {
      name: "Sealed answers opened together",
      value: `${result.n} answers`,
      note: "Each committed with a timestamp before anyone saw another. No answer can change after the fact.",
    },
    {
      name: "Equal-weight mean",
      value: pct(result.mean),
      note: "The published group view. Every answer counts once, whatever the expert's record.",
      headline: true,
    },
    {
      name: "Reliability-weighted mean",
      value: pct(result.weighted_mean),
      note:
        weightShift < 0.005
          ? "Weighting by past accuracy moved the figure by less than a point. Shown for comparison; it does not replace the headline."
          : `Weighting by past accuracy moves the figure by ${pct(weightShift)}. Shown for comparison; it does not replace the headline.`,
    },
    {
      name: "Surprisingly-popular check",
      value: result.sp_experiment.answer === "yes" ? "Flagged" : "Not flagged",
      note:
        result.sp_experiment.answer === "yes"
          ? "More experts answered yes than the panel predicted would. That can mark an informed minority, so the minority reason is shown beside the mean."
          : "The answer share matched what the panel predicted. No minority signal.",
      experimental: true,
    },
    {
      name: "Dissent index",
      value: result.dissent_index?.toFixed(2) ?? "Not supplied",
      note:
        result.dissent_index === undefined
          ? "Not returned for this round."
          : result.dissent_index >= 0.3
            ? "The panel is meaningfully divided. A single number hides that, which is why the spread and the minority reason travel with it."
            : "The panel broadly agrees.",
    },
    {
      name: "Spread across the panel",
      value: `${pct(result.spread.min)}–${pct(result.spread.max)}`,
      note: `Interquartile range ${pct(result.spread.iqr)}. The published view carries this range, not the mean alone.`,
    },
    {
      name: "Mapped to the ACAPS band",
      value: reference,
      note: past
        ? `Bands are numeric by assumption. Of ${past.n} resolved ${reference} risks, ${pct(past.rate)} materialised.`
        : "Bands are mapped to numbers by assumption, not official thresholds.",
    },
  ];
  return (
    <>
      <p className="insights-lede">
        Seven steps run between the sealed answers and the proposed band. The
        published figure stays the equal-weight mean; the rest are checks
        around it, and each one reports what it found even when it found
        nothing.
      </p>
      <ol className="method-chain">
        {steps.map((step) => (
          <li key={step.name} className={step.headline ? "headline" : undefined}>
            <div className="method-head">
              <span className="method-name">
                {step.name}
                {step.experimental && (
                  <span className="method-tag">experimental</span>
                )}
                {step.headline && (
                  <span className="method-tag published">published</span>
                )}
              </span>
              <strong>{step.value}</strong>
            </div>
            <p>{step.note}</p>
          </li>
        ))}
      </ol>
      <p className="panel-caption">
        Nothing here changes a rating on its own. The analyst accepts, edits or
        rejects the draft that follows.
      </p>
    </>
  );
}

/**
 * Themes the panel raised, routed to the expertise each one calls for, so the
 * analyst can see which second opinion would close the gap.
 */
export function CoverageAdvice({ result }: { result: Result }) {
  const themes = result.missing_themes || [];
  // integrity_notes ships in the round fixture but is not on the shared Result
  // contract, so it is narrowed here rather than by editing the contract.
  const notes =
    (result as Result & { integrity_notes?: IntegrityNote[] })
      .integrity_notes || [];
  const gaps = notes.filter((note) => note.kind === "coverage_gap");
  if (!themes.length && !gaps.length) return null;

  const routed = themes.map((theme) => ({
    ...theme,
    topic: topicFor(theme.theme),
  }));
  const byTopic = new Map<string, number>();
  for (const item of routed) {
    if (item.topic)
      byTopic.set(item.topic, (byTopic.get(item.topic) || 0) + item.count);
  }
  const ranked = [...byTopic.entries()].sort((a, b) => b[1] - a[1]);
  const unrouted = routed.filter((item) => !item.topic);
  const thin = routed.filter(
    (item) => item.corroboration !== "corroborated" && item.topic,
  );

  return (
    <>
      <p className="insights-lede">
        Every theme an expert raised, routed by keyword to the expertise it
        calls for. The routing is a plain word list, not a model, so it can be
        overruled.
      </p>
      <ul className="theme-routing">
        {routed.map((item) => (
          <li key={item.theme}>
            <span className="theme-text">{item.theme}</span>
            <span className="theme-meta">
              <span className="theme-tag">{item.topic || "unrouted"}</span>
              <span>
                {item.count} mention{item.count === 1 ? "" : "s"} ·{" "}
                {item.origin === "single" ? "one expert" : "several experts"} ·{" "}
                {item.corroboration}
              </span>
            </span>
          </li>
        ))}
      </ul>
      {ranked.length > 0 && (
        <div className="second-opinion">
          <h3>Where a second opinion would help most</h3>
          <p>
            {ranked[0][1]} of the {routed.reduce((sum, i) => sum + i.count, 0)}{" "}
            mentions point at <strong>{ranked[0][0]}</strong>
            {ranked.length > 1 && `, then ${ranked[1][0]}`}. An expert tagged{" "}
            {ranked[0][0]} would speak to the largest unexamined group.
          </p>
          {thin.length > 0 && (
            <p>
              {thin.length} of these themes{" "}
              {thin.length === 1 ? "is" : "are"} single-source or unchecked, so
              they stay in the verification queue rather than entering the
              draft. Absence from a database is not evidence that a thing is
              untrue.
            </p>
          )}
          {unrouted.length > 0 && (
            <p>
              {unrouted.length} theme{unrouted.length === 1 ? "" : "s"} matched
              no keyword and {unrouted.length === 1 ? "needs" : "need"} routing
              by hand.
            </p>
          )}
        </div>
      )}
      {gaps.length > 0 && (
        <div className="coverage-gaps">
          <h3>Gaps the panel build already flagged</h3>
          {gaps.map((gap) => (
            <p key={gap.text}>
              {gap.text} <span className="theme-meta">{gap.evidence}</span>
            </p>
          ))}
        </div>
      )}
    </>
  );
}

/**
 * Variation inside the country, and the cross-border reach of the panel itself.
 * A single national figure hides both.
 */
export function RegionalSpread({
  result,
  countries = [],
}: {
  result: Result;
  countries?: string[];
}) {
  const shown = (result.agreement_by_region || []).filter(
    (region) => region.n >= 3 && region.mean !== null,
  );
  const withheld = (result.agreement_by_region || []).length - shown.length;
  const means = shown.map((region) => region.mean as number);
  const range = means.length > 1 ? Math.max(...means) - Math.min(...means) : 0;
  const high = shown.find((r) => r.mean === Math.max(...means));
  const low = shown.find((r) => r.mean === Math.min(...means));
  return (
    <>
      {shown.length ? (
        <>
          {shown.map((region) => (
            <p className="region-line" key={region.region}>
              {region.region}
              <span className="region-bar" aria-hidden="true">
                <span style={{ width: `${(region.mean as number) * 100}%` }} />
              </span>
              <strong>{pct(region.mean as number)}</strong>
              <span>{region.n} answers</span>
            </p>
          ))}
          {range > 0.1 && high && low && (
            <p className="region-note">
              {pct(range)} between {high.region} and {low.region}. Experts
              inside one country do not see one situation, and the national
              mean of {pct(result.mean)} reports neither of them.
            </p>
          )}
          {countries.length > 1 && (
            <p className="region-note">
              This risk spans {countries.join(", ")}, so the panel is drawn
              across the border rather than from the affected country alone.
            </p>
          )}
        </>
      ) : (
        <p>Regional views open after reveal.</p>
      )}
      <p className="panel-caption">
        Other regions withheld below three answers
        {withheld > 0
          ? `: ${withheld} here, where fewer answers would identify the respondent.`
          : "."}
      </p>
    </>
  );
}
