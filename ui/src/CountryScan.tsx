import { useEffect, useMemo, useState } from "react";
import { Check, LockKeyhole, ShieldCheck } from "lucide-react";
import { api } from "./service";
import { mock } from "./api";
import { Frame, CopyButton } from "./LiveWorkspace";
import "./scan.css";

// Country scan: "What are the three biggest risks in <country> that might worsen humanitarian
// outcomes in the next six months?" The expert taps up to three candidates in order of importance.
// ACAPS's own level is not on this screen; the order of the list is shuffled per link by the API.

type ScanCardPayload = {
  scan_id: string;
  question: string;
  max_picks: number;
  pick_note: string;
  candidates: { id: string; title: string }[];
  added_prompt: string;
  source_tags: string[];
  mask_options: { id: string; label: string; note?: string }[];
  mask_note: string;
  expires_at: string;
  already_answered: boolean;
};
type Draft = { confirm_token: string; summary: string; committed: boolean };
type Sealed = {
  committed_at: string;
  commitment: string;
  version: number;
  correction_allowed_until: string;
  message: string;
};
type Stance = "estimate" | "outside_my_expertise" | "not_enough_evidence";

const MOCK_CARD: ScanCardPayload = {
  scan_id: "S-TCD-demo",
  question:
    "What are the three biggest risks in Chad that might worsen humanitarian outcomes in the next six months?",
  max_picks: 3,
  pick_note: "Tap up to three, most important first.",
  candidates: [
    { id: "TCD007", title: "Floods in Chad" },
    {
      id: "R1066",
      title:
        "Escalating insecurity across the Lake Chad Basin increases displacement, protection risks and needs",
    },
    { id: "TCD002", title: "Drought in Chad" },
    {
      id: "R1043",
      title:
        "Escalating cross-border insecurity linked to the Sudan conflict increases protection risks and humanitarian needs in eastern Chad",
    },
    { id: "TCD001", title: "Complex crisis in Chad" },
    { id: "TCD004", title: "Displacement from CAR to Chad" },
    { id: "TCD003", title: "Conflict in Lac province" },
    { id: "TCD006", title: "Tibesti Conflict in Chad" },
  ],
  added_prompt: "A risk that is not on this list (optional)",
  source_tags: ["saw", "read", "heard"],
  mask_options: [
    { id: "known", label: "named to ACAPS" },
    { id: "pseudonym", label: "nickname to peers" },
    {
      id: "anonymous",
      label: "no identity kept",
      note: "you will not receive personal feedback on this answer",
    },
  ],
  mask_note:
    "In a panel of eight a distinctive reason may identify you to colleagues.",
  expires_at: "2026-11-09T09:00:00+00:00",
  already_answered: false,
};

function when(iso: string) {
  return (
    new Date(iso).toLocaleString("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    }) + " UTC"
  );
}

export function ScanCard({ token }: { token: string }) {
  const [card, setCard] = useState<ScanCardPayload | null>(null);
  const [error, setError] = useState("");
  const [picks, setPicks] = useState<string[]>([]);
  const [stance, setStance] = useState<Stance>("estimate");
  const [added, setAdded] = useState("");
  const [source, setSource] = useState<string | null>(null);
  const [mask, setMask] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [sealed, setSealed] = useState<Sealed | null>(null);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState("");

  useEffect(() => {
    document.title = "Country scan | Sealed Signals";
    if (mock) {
      setCard(MOCK_CARD);
      return;
    }
    api<ScanCardPayload>(`/s/${encodeURIComponent(token)}`)
      .then(setCard)
      .catch((e) => setError((e as Error).message));
  }, [token]);

  const titles = useMemo(
    () =>
      Object.fromEntries((card?.candidates || []).map((c) => [c.id, c.title])),
    [card],
  );

  function toggle(id: string) {
    setStance("estimate");
    setPicks((current) =>
      current.includes(id)
        ? current.filter((p) => p !== id)
        : current.length < (card?.max_picks || 3)
          ? [...current, id]
          : current,
    );
  }

  function abstain(value: Stance) {
    setStance((s) => (s === value ? "estimate" : value));
    setPicks([]);
  }

  async function review() {
    setFormError("");
    if (!mask) return setFormError("Choose how you appear for this answer.");
    if (stance === "estimate" && !picks.length && !added.trim())
      return setFormError(
        "Tap at least one risk, add one, or choose an abstention.",
      );
    if (added.trim() && !source)
      return setFormError("Say whether you saw, read or heard the added risk.");
    const body = {
      mask,
      stance,
      picks,
      added: added.trim() || null,
      source_tag: added.trim() ? source : null,
    };
    if (mock) {
      setDraft({
        confirm_token: "mock",
        summary: picks.map((p, i) => `${i + 1}. ${titles[p]}`).join("; "),
        committed: false,
      });
      return;
    }
    setBusy(true);
    try {
      setDraft(
        await api<Draft>(`/s/${encodeURIComponent(token)}/answer`, body),
      );
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!draft) return;
    if (mock) {
      setSealed({
        committed_at: new Date().toISOString(),
        commitment: "fixture receipt, not a live seal",
        version: 1,
        correction_allowed_until: MOCK_CARD.expires_at,
        message: "Thanks. You'll hear how the panel saw it after the deadline.",
      });
      return;
    }
    setBusy(true);
    try {
      setSealed(
        await api<Sealed>(`/s/${encodeURIComponent(token)}/confirm`, {
          confirm_token: draft.confirm_token,
        }),
      );
    } catch (e) {
      setFormError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="site-header">
        <a className="brand" href="/">
          <span className="brand-mark">
            <LockKeyhole size={19} />
          </span>
          Sealed Signals
        </a>
        <span className="header-note">Independent expert perspective</span>
      </header>
      <main id="expert-content" className="scan-main">
        <section className="card scan-card" aria-label="Country scan">
          {error ? (
            <div className="state" role="alert">
              <h2>We couldn’t open this scan.</h2>
              <p>{error}</p>
            </div>
          ) : !card ? (
            <div className="state" role="status">
              Opening the scan…
            </div>
          ) : sealed ? (
            <div className="state receipt" role="status">
              <span className="success-mark">
                <Check size={28} />
              </span>
              <h2>Recorded.</h2>
              <p>{sealed.message}</p>
              <div className="receipt-box">
                <span>Committed</span>
                <time>{when(sealed.committed_at)}</time>
                <span>Commitment</span>
                <code>{sealed.commitment}</code>
                <CopyButton value={sealed.commitment} label="Copy commitment" />
              </div>
              <p className="help">
                You can change this answer from the same link until{" "}
                {when(sealed.correction_allowed_until)}.
              </p>
            </div>
          ) : draft ? (
            <div className="scan-confirm">
              <h2>Check your answer</h2>
              {picks.length ? (
                <ol className="scan-confirm-list">
                  {picks.map((p) => (
                    <li key={p}>{titles[p]}</li>
                  ))}
                </ol>
              ) : (
                <p>
                  {stance === "estimate"
                    ? "No pick"
                    : stance === "outside_my_expertise"
                      ? "Outside my area"
                      : "Not enough evidence"}
                </p>
              )}
              {added.trim() && (
                <p className="help">
                  Added: {added.trim()} ({source})
                </p>
              )}
              <p className="help">
                Appears as:{" "}
                {card.mask_options.find((m) => m.id === mask)?.label}
              </p>
              <p className="help">Nothing is recorded until you confirm.</p>
              {formError && (
                <p role="alert" className="error-box">
                  {formError}
                </p>
              )}
              <button className="seal-button" onClick={confirm} disabled={busy}>
                Confirm
              </button>
              <button className="text-button" onClick={() => setDraft(null)}>
                Change
              </button>
            </div>
          ) : (
            <>
              <h1 className="scan-question">{card.question}</h1>
              <p className="help">{card.pick_note}</p>
              <ul className="scan-candidates">
                {card.candidates.map((c) => {
                  const rank = picks.indexOf(c.id);
                  const full = picks.length >= card.max_picks && rank < 0;
                  return (
                    <li key={c.id}>
                      <button
                        type="button"
                        className="scan-option"
                        aria-pressed={rank >= 0}
                        disabled={full}
                        onClick={() => toggle(c.id)}
                      >
                        <span className="scan-rank" aria-hidden="true">
                          {rank >= 0 ? rank + 1 : ""}
                        </span>
                        <span>{c.title}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
              <div className="scan-stances">
                <button
                  type="button"
                  aria-pressed={stance === "outside_my_expertise"}
                  onClick={() => abstain("outside_my_expertise")}
                >
                  Outside my area
                </button>
                <button
                  type="button"
                  aria-pressed={stance === "not_enough_evidence"}
                  onClick={() => abstain("not_enough_evidence")}
                >
                  Not enough evidence
                </button>
              </div>
              <details className="scan-added">
                <summary>{card.added_prompt}</summary>
                <textarea
                  value={added}
                  maxLength={200}
                  onChange={(e) => setAdded(e.target.value)}
                  aria-label={card.added_prompt}
                  rows={2}
                />
                <div
                  className="scan-sources"
                  role="group"
                  aria-label="Saw, read or heard"
                >
                  {card.source_tags.map((t) => (
                    <button
                      type="button"
                      key={t}
                      aria-pressed={source === t}
                      onClick={() => setSource(t)}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </details>
              <div
                className="scan-masks"
                role="group"
                aria-label="How you appear for this answer"
              >
                {card.mask_options.map((m) => (
                  <button
                    type="button"
                    key={m.id}
                    aria-pressed={mask === m.id}
                    onClick={() => setMask(m.id)}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <p className="help">
                {card.mask_note}
                {mask === "anonymous" &&
                  " You will not receive personal feedback on this answer."}
              </p>
              {formError && (
                <p role="alert" className="error-box">
                  {formError}
                </p>
              )}
              <button className="seal-button" onClick={review} disabled={busy}>
                Review and confirm
              </button>
              <p className="seal-note">
                <ShieldCheck size={16} /> ACAPS's own view appears after the
                deadline, {when(card.expires_at)}.
              </p>
            </>
          )}
        </section>
      </main>
    </>
  );
}

// -- analyst view: panel ranking beside ACAPS's own ------------------------------

type RankRow = {
  rank: number;
  id: string;
  title: string;
  kind: "acaps_risk" | "acaps_crisis";
  points: number;
  in_top3: number;
  first_choice: number;
  acaps_rank: number;
  acaps_view: {
    level?: string;
    inform_severity?: number | null;
    category?: string | null;
    note?: string | null;
  };
};
type ScanResult = {
  scan_id: string;
  question: string;
  country: string;
  n: number;
  n_ranking: number;
  abstentions: Record<string, number>;
  ranking: RankRow[];
  panel_top3: string[];
  acaps_top3: string[];
  overlap_with_acaps_top3: number;
  first_choice_agreement: number | null;
  notes?: { kind: string; id: string; text: string }[];
  added_risks: { count: number; themes: { theme: string; count: number }[] };
  verify_hash: string;
  reveal_status: string;
  revealed_reason: string;
  method: string;
};

function acapsLabel(row: RankRow) {
  if (row.kind === "acaps_risk")
    return `Risk List: ${row.acaps_view.level || "unrated"}`;
  return row.acaps_view.inform_severity != null
    ? `Crisis, INFORM ${row.acaps_view.inform_severity}`
    : "Crisis, no current INFORM score";
}

function Slope({ ranking }: { ranking: RankRow[] }) {
  const rowH = 46,
    w = 1120,
    left = 380,
    right = w - 460,
    top = 30;
  const short = (t: string) => (t.length > 34 ? t.slice(0, 33) + "…" : t);
  const h = top + ranking.length * rowH;
  const byAcaps = [...ranking].sort((a, b) => a.acaps_rank - b.acaps_rank);
  return (
    <svg
      className="scan-slope"
      viewBox={`0 0 ${w} ${h}`}
      role="img"
      aria-label="Panel ranking on the left, ACAPS's own order on the right; lines join the same risk."
    >
      <text x={left - 12} y={16} textAnchor="end" className="slope-head">
        Panel
      </text>
      <text x={right + 12} y={16} className="slope-head">
        ACAPS
      </text>
      {ranking.map((row) => {
        const y1 = top + (row.rank - 0.5) * rowH;
        const y2 = top + (row.acaps_rank - 0.5) * rowH;
        const hot = row.rank <= 3 || row.acaps_rank <= 3;
        const moved = row.rank <= 3 !== row.acaps_rank <= 3;
        return (
          <line
            key={row.id}
            x1={left}
            y1={y1}
            x2={right}
            y2={y2}
            className={
              moved ? "slope-line moved" : hot ? "slope-line hot" : "slope-line"
            }
          />
        );
      })}
      {ranking.map((row) => (
        <g key={`l-${row.id}`}>
          <circle
            cx={left}
            cy={top + (row.rank - 0.5) * rowH}
            r={6}
            className={row.rank <= 3 ? "dot hot" : "dot"}
          />
          <text
            x={left - 14}
            y={top + (row.rank - 0.5) * rowH + 5}
            textAnchor="end"
            className="slope-label"
          >
            {row.rank}. {short(row.title)}
          </text>
        </g>
      ))}
      {byAcaps.map((row) => (
        <g key={`r-${row.id}`}>
          <circle
            cx={right}
            cy={top + (row.acaps_rank - 0.5) * rowH}
            r={6}
            className={row.acaps_rank <= 3 ? "dot hot" : "dot"}
          />
          <text
            x={right + 14}
            y={top + (row.acaps_rank - 0.5) * rowH + 5}
            className="slope-label"
          >
            {row.acaps_rank}. {short(row.title)}
            <tspan className="slope-sub" dx={8}>
              {acapsLabel(row)}
            </tspan>
          </text>
        </g>
      ))}
    </svg>
  );
}

export function ScanResultView({ scanId }: { scanId: string }) {
  const [result, setResult] = useState<ScanResult | null>(null);
  const [state, setState] = useState("");
  const [verified, setVerified] = useState<boolean | null>(null);

  function load() {
    api<ScanResult>(`/scans/${encodeURIComponent(scanId)}/result`)
      .then(setResult)
      .catch(() =>
        setState(
          "This scan reveals at its deadline. Nothing is shown before then, to anyone.",
        ),
      );
  }
  useEffect(load, [scanId]);

  async function revealNow() {
    try {
      const r = await api<ScanResult>(
        `/scans/${encodeURIComponent(scanId)}/reveal`,
        { reason: "analyst_before_deadline" },
      );
      if (r.reveal_status === "revealed") setResult(r);
      else
        setState(
          "Insufficient panel: fewer than five answers. The answers are kept and nothing is revealed.",
        );
    } catch (e) {
      setState((e as Error).message);
    }
  }
  async function verify() {
    const r = await api<{ valid: boolean }>(
      `/scans/${encodeURIComponent(scanId)}/verify`,
      {},
    );
    setVerified(r.valid);
  }

  return (
    <Frame
      title="Country scan"
      subtitle={
        result?.question || "The panel's top three, beside ACAPS's own order."
      }
    >
      {!result ? (
        <div className="scan-wait">
          <p role="status">{state || "Loading…"}</p>
          <button onClick={revealNow}>
            Reveal now (demo; recorded as before the deadline)
          </button>
        </div>
      ) : (
        <div className="scan-result">
          <div className="scan-kpis">
            <div>
              <b>{result.n}</b>
              <span>answers committed</span>
            </div>
            <div>
              <b>{result.overlap_with_acaps_top3} of 3</b>
              <span>panel top three shared with ACAPS</span>
            </div>
            <div>
              <b>
                {result.first_choice_agreement != null
                  ? Math.round(result.first_choice_agreement * 100) + " %"
                  : "n/a"}
              </b>
              <span>chose the panel's first as their first</span>
            </div>
            <div>
              <b>
                {(result.abstentions.outside_my_expertise || 0) +
                  (result.abstentions.not_enough_evidence || 0)}
              </b>
              <span>abstained, never counted</span>
            </div>
          </div>
          <Slope ranking={result.ranking} />
          {!!result.notes?.length && (
            <ul className="scan-notes">
              {result.notes.map((n) => (
                <li key={n.kind + n.id} className={n.kind}>
                  {n.text}
                </li>
              ))}
            </ul>
          )}
          <p className="help">
            Risks added by experts: {result.added_risks.count}
            {result.added_risks.themes.length > 0 &&
              ` (${result.added_risks.themes.map((t) => t.theme).join(", ")})`}
            , held in the access-logged verification queue.
          </p>
          <p className="help">{result.method}</p>
          <div className="scan-verify">
            <button onClick={verify}>Verify</button>
            {verified != null && (
              <span className={verified ? "ok" : "bad"}>
                {verified
                  ? "Matches: these answers existed at this time and were not changed. Timing, not truth."
                  : "Does not match."}
              </span>
            )}
            <code>{result.verify_hash.slice(0, 16)}…</code>
          </div>
        </div>
      )}
    </Frame>
  );
}
