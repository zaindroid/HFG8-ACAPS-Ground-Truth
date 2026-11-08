import { useEffect, useState } from "react";
import { LockKeyhole } from "lucide-react";
import { api } from "./service";
import "./scan.css";

// The message an expert receives after the deadline: what their minute changed, from the record.
// No score, no ranking, and their own answer only if they ask for it.

type Impact = { headline: string; lines: string[] };
type FeedbackPayload = {
  reveal_status: string;
  message?: string;
  impact?: Impact;
  your_answer?: {
    likelihood_word?: string;
    probability?: number | null;
  } | null;
  your_answer_note?: string;
  reports_on?: boolean;
};

export function ThankYou({ token }: { token: string }) {
  const [data, setData] = useState<FeedbackPayload | null>(null);
  const [error, setError] = useState("");
  const [showMine, setShowMine] = useState(false);
  const [off, setOff] = useState(false);

  useEffect(() => {
    document.title = "Thank you | Sealed Signals";
    api<FeedbackPayload>(
      `/e/${encodeURIComponent(token)}/feedback${showMine ? "?show_mine=true" : ""}`,
    )
      .then(setData)
      .catch(() =>
        setError(
          "The panel's view opens at the deadline. Come back to this link then.",
        ),
      );
  }, [token, showMine]);

  async function reportsOff() {
    await api(`/e/${encodeURIComponent(token)}/reports-off`, {});
    setOff(true);
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
      <main className="scan-main">
        <section
          className="card scan-card thank-you"
          aria-label="What your answer changed"
        >
          {error ? (
            <p role="status">{error}</p>
          ) : !data ? (
            <p role="status">Opening…</p>
          ) : data.reveal_status !== "revealed" ? (
            <p>{data.message}</p>
          ) : (
            <>
              <h1 className="scan-question">
                {data.impact?.headline || "Thank you"}
              </h1>
              {data.impact?.lines.map((line) => (
                <p
                  key={line}
                  className={line.startsWith("“") ? "thank-quote" : undefined}
                >
                  {line}
                </p>
              ))}
              <div className="thank-actions">
                {!showMine ? (
                  <button
                    className="text-button"
                    onClick={() => setShowMine(true)}
                  >
                    Show my own answer
                  </button>
                ) : (
                  <p className="help">
                    {data.your_answer
                      ? `Your answer: ${data.your_answer.likelihood_word?.replace("_", " ") || ""}${
                          data.your_answer.probability != null
                            ? ` (${Math.round(data.your_answer.probability * 100)} %)`
                            : ""
                        }.`
                      : data.your_answer_note}
                  </p>
                )}
                {off || data.reports_on === false ? (
                  <p className="help">Outcome reports are off for you.</p>
                ) : (
                  <button className="text-button" onClick={reportsOff}>
                    Stop outcome reports
                  </button>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}
