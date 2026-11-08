// The card behind a QR code: one seat on the live panel, taken by whoever scans it.
//
// It is the same question and the same answer shape as a named invitation. What differs is who
// it belongs to. An invitation is addressed; a seat is claimed, so the card has to hold the
// seat while it is open, refuse a second person who scans the same code, give the seat back if
// it is abandoned, and close it for good once an answer is confirmed. All of that is the
// claim/heartbeat/release contract in live-seats.ts; this file is the screen over it.
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Check, ChevronDown, LockKeyhole, Smartphone } from "lucide-react";
import type { Answer, Mask } from "./demo-api";
import { liveProbes, liveQuestion, seatProfile, wordMidpoint } from "./live-panel";
import {
  HEARTBEAT_MS,
  claimSeat,
  heartbeatSeat,
  releaseSeat,
  submitSeatAnswer,
  type SeatReceipt,
} from "./live-seats";
import "./expert34.css";

const words = [
  { id: "very_unlikely", label: "Very unlikely", range: "Under 10%" },
  { id: "unlikely", label: "Unlikely", range: "10–35%" },
  { id: "even", label: "Even chance", range: "35–65%" },
  { id: "likely", label: "Likely", range: "65–90%" },
  { id: "very_likely", label: "Very likely", range: "Over 90%" },
];
const masks: { id: Mask; label: string }[] = [
  { id: "known", label: "Named to ACAPS" },
  { id: "pseudonym", label: "Nickname to peers" },
  { id: "anonymous", label: "No identity kept" },
];

export function LiveSeatCard({ token }: { token: string }) {
  const seat = seatProfile(token);
  const [held, setHeld] = useState<"claiming" | "held" | "refused">("claiming");
  const [refusal, setRefusal] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [word, setWord] = useState<string | null>(null);
  const [exact, setExact] = useState("");
  const [stance, setStance] = useState<Answer["stance"]>("estimate");
  const [mask, setMask] = useState<Mask | null>(null);
  const [confidence, setConfidence] = useState("");
  const [probeAnswers, setProbeAnswers] = useState<Record<string, string>>({});
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState<Answer | null>(null);
  const [receipt, setReceipt] = useState<SeatReceipt | null>(null);
  const submitted = useRef(false);

  useEffect(() => {
    document.title = "Expert question | Sealed Signals";
  }, []);

  // Claim, then renew while the card is on screen. A card that stops renewing -- a closed tab,
  // a phone put away -- lets the lease run out and the seat opens for the next person.
  useEffect(() => {
    if (!seat || receipt) return;
    let alive = true;
    setHeld("claiming");
    setRefusal("");
    claimSeat(token)
      .then(() => {
        if (alive) setHeld("held");
      })
      .catch((e) => {
        if (alive) {
          setHeld("refused");
          setRefusal((e as Error).message);
        }
      });
    const timer = window.setInterval(() => {
      void heartbeatSeat(token).catch(() => {
        /* One missed renewal is inside the lease; a run of them is meant to lose the seat. */
      });
    }, HEARTBEAT_MS);
    const letGo = () => {
      if (!submitted.current) releaseSeat(token, true);
    };
    window.addEventListener("pagehide", letGo);
    return () => {
      alive = false;
      window.clearInterval(timer);
      window.removeEventListener("pagehide", letGo);
      if (!submitted.current) releaseSeat(token);
    };
  }, [token, seat, receipt, attempt]);

  const probe = useCallback(
    (id: string, value: string) => setProbeAnswers((current) => ({ ...current, [id]: value })),
    [],
  );

  if (!seat)
    return (
      <main className="expert34">
        <h1>This code is not in use</h1>
        <p className="expert34-meta">Ask the analyst for one of the codes on screen.</p>
      </main>
    );

  const deadlineText = new Date(liveQuestion.deadline).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  function prepare(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!mask) {
      setError("Choose how your answer is shared.");
      return;
    }
    if (stance === "estimate" && !word && exact === "") {
      setError("Choose a likelihood or enter an exact percentage.");
      return;
    }
    if (exact !== "" && (!Number.isFinite(Number(exact)) || Number(exact) < 0 || Number(exact) > 100)) {
      setError("Enter a percentage between 0 and 100.");
      return;
    }
    // A word is not a number, and the group average needs one. The midpoint of the band is the
    // assumption, carried with the word itself so the result can say which it used.
    const chosen = stance !== "estimate" ? null : exact !== "" ? Number(exact) / 100 : wordMidpoint[word || ""] ?? null;
    setPending({
      mask,
      stance,
      likelihood_word: stance === "estimate" && exact === "" ? word : null,
      probability: chosen,
      confidence: confidence ? Number(confidence) : null,
      source_tag: null,
      missing: note.trim(),
      panel_share_yes: null,
      round: 1,
      changed_mind: false,
      probe_answers: probeAnswers,
    });
  }
  async function confirm() {
    if (!pending) return;
    setBusy(true);
    setError("");
    try {
      const value = await submitSeatAnswer(token, pending);
      submitted.current = true;
      setReceipt(value);
      setPending(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const summary = pending
    ? `${pending.stance === "estimate" ? (pending.probability !== null ? `${Math.round(pending.probability * 100)}% likelihood` : "No estimate") : pending.stance.replaceAll("_", " ")} · ${pending.mask === "known" ? "named to ACAPS" : pending.mask === "pseudonym" ? "nickname to peers" : "no identity kept"}`
    : "";

  return (
    <main className="expert34" id="expert-content">
      <div className="seat-badge">
        <span>
          <Smartphone size={14} aria-hidden="true" /> {seat.label} · live panel
        </span>
        <strong>{seat.expertise}</strong>
        <small>
          {seat.affiliation} · {seat.region}
        </small>
      </div>
      {receipt ? (
        <section className="expert34-thanks" aria-label="Answer confirmed">
          <Check size={30} aria-hidden="true" />
          <h1>Thanks. Your answer is confirmed.</h1>
          <p>
            It joins the panel now. The group result is shown on the analyst screen once all
            eight answers are in; no individual answer is shown with it.
          </p>
          <p className="expert34-meta">This seat is now closed, and its code no longer works.</p>
          <small>Confirmed {new Date(receipt.committed_at).toLocaleString("en-GB")}</small>
        </section>
      ) : held === "claiming" ? (
        <section aria-label="Taking this seat">
          <h1>Opening your question…</h1>
          <p className="expert34-meta">Checking that this seat is free.</p>
        </section>
      ) : held === "refused" ? (
        <section aria-label="Seat unavailable">
          <h1>This seat is taken</h1>
          <p role="alert">{refusal}</p>
          <p className="expert34-meta">
            Each code admits one person. If the screen still shows this one as open, try again.
          </p>
          <button className="primary" onClick={() => setAttempt((n) => n + 1)}>
            Try this seat again
          </button>
        </section>
      ) : pending ? (
        <section aria-label="Confirm your answer">
          <p className="expert34-from">A question from your ACAPS analyst</p>
          <h1>Confirm your answer</h1>
          <p>{liveQuestion.text}</p>
          <div className="expert34-confirm-summary">{summary}</div>
          <p className="expert34-meta">
            Nothing is committed until you confirm. Once confirmed, this seat closes.
          </p>
          {error && <p role="alert">{error}</p>}
          <div className="expert34-actions">
            <button className="primary" disabled={busy} onClick={() => void confirm()}>
              {busy ? "Confirming…" : "Confirm answer"}
            </button>
            <button disabled={busy} onClick={() => setPending(null)}>
              Change my answer
            </button>
          </div>
        </section>
      ) : (
        <form onSubmit={prepare}>
          <p className="expert34-from">A question from your ACAPS analyst</p>
          <h1>{liveQuestion.text}</h1>
          <p className="expert34-meta">
            {liveQuestion.location} · Outcome assessed on {deadlineText}
          </p>
          <fieldset disabled={busy}>
            <legend className="sr-only">Your forecast</legend>
            <div className="expert34-words" role="group" aria-label="Likelihood">
              {words.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  aria-pressed={stance === "estimate" && word === item.id && exact === ""}
                  onClick={() => {
                    setWord(item.id);
                    setExact("");
                    setStance("estimate");
                  }}
                >
                  <strong>{item.label}</strong>
                  <span>{item.range}</span>
                </button>
              ))}
            </div>
            <div className="expert34-abstain">
              {(
                [
                  ["outside_my_expertise", "Outside my area"],
                  ["not_enough_evidence", "Not enough evidence"],
                ] as const
              ).map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  aria-pressed={stance === value}
                  onClick={() => setStance(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            {/* Two follow-ups, and no more. They were written from this risk's own record and
                read by a person before being committed; both ask about direction and sequence
                rather than a figure, because a question that invents a threshold nobody tracks
                cannot be answered honestly or scored later. */}
            {stance === "estimate" && (
              <section className="seat-probes" aria-label="Follow-up questions">
                {liveProbes.map((item) => (
                  <div key={item.id}>
                    <p className="seat-probe-question">{item.question}</p>
                    {item.help && <p className="expert34-meta">{item.help}</p>}
                    {item.kind === "choice" ? (
                      <label>
                        <span className="sr-only">{item.question}</span>
                        <select
                          value={probeAnswers[item.id] || ""}
                          onChange={(event) => probe(item.id, event.target.value)}
                          aria-label={item.question}
                        >
                          <option value="">Choose one</option>
                          {(item.options || []).map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : (
                      <label>
                        <span className="sr-only">{item.question}</span>
                        <textarea
                          maxLength={item.limit || 240}
                          value={probeAnswers[item.id] || ""}
                          onChange={(event) => probe(item.id, event.target.value)}
                          aria-label={item.question}
                        />
                      </label>
                    )}
                  </div>
                ))}
              </section>
            )}
            <details className="expert34-optional">
              <summary>
                Exact number or add a note <ChevronDown size={14} aria-hidden="true" />
              </summary>
              <label>
                Exact likelihood (%)
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="any"
                  value={exact}
                  onChange={(event) => {
                    setExact(event.target.value);
                    setWord(null);
                    setStance("estimate");
                  }}
                />
              </label>
              <label>
                How sure are you? (optional)
                <select value={confidence} onChange={(event) => setConfidence(event.target.value)}>
                  <option value="">Not specified</option>
                  <option value="1">Not sure</option>
                  <option value="3">Fairly sure</option>
                  <option value="5">Sure</option>
                </select>
              </label>
              <label>
                What are we missing?
                <textarea
                  maxLength={240}
                  value={note}
                  onChange={(event) => setNote(event.target.value)}
                />
              </label>
            </details>
            <div className="expert34-masks" role="group" aria-label="How your answer is shared">
              {masks.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  aria-pressed={mask === item.id}
                  onClick={() => setMask(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <p className="expert34-privacy">
              In a panel of eight, a distinctive reason may identify you to colleagues.
              {mask === "anonymous" && " No identity is kept with this answer."}
            </p>
            {error && <p role="alert">{error}</p>}
            <button className="primary expert34-submit" type="submit">
              Review and submit <LockKeyhole size={15} aria-hidden="true" />
            </button>
          </fieldset>
          <details className="expert34-charter">
            <summary>Who sees what</summary>
            <p>
              Your answer joins seven others on one question. Nobody sees an individual answer:
              the analyst sees the group average and its spread, and the public record carries
              the group result only. You are not told ACAPS's own rating before you answer,
              because it would anchor your estimate.
            </p>
            <p>
              This seat belongs to you while this page is open. If you close it without
              submitting, the seat opens again for someone else and nothing of yours is kept.
            </p>
          </details>
        </form>
      )}
    </main>
  );
}
