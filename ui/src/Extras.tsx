import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { mock } from "./api";
import {
  sampleDataEnabled,
  sampleCalibration,
  sampleForecasts,
} from "./demo-data";
import { endpoint, api, type Calibration as Report } from "./service";
import { calibrationEnabled } from "./Programme";
import { CopyButton, Frame, Section } from "./LiveWorkspace";
import { en } from "./locales/en";

export function Stage() {
  const [invitation, setInvitation] = useState(
    mock ? `${location.origin}/e/demo` : "",
  );
  const [qr, setQr] = useState(mock ? invitation : "");
  const [error, setError] = useState("");
  const [presentation, setPresentation] = useState(false);
  const qrHost = qr ? new URL(qr).hostname : "";
  const computerOnly = ["localhost", "127.0.0.1", "[::1]"].includes(qrHost);
  return (
    <Frame
      title="Stage"
      subtitle="Jury access: display the QR invitation to the expert card."
    >
      {mock && sampleDataEnabled() && (
        <Section title="Invitations">
          <p className="panel-caption">
            These shared links are synthetic examples, not issued expert
            credentials.
          </p>
          <div className="sample-invitations">
            <a href="/e/demo">Open first-round card</a>
            <a href="/e/round2">Open optional round-two card</a>
            <a href="/e/empty">Preview unavailable invitation</a>
            <a href="/calibration">Open sample calibration</a>
          </div>
        </Section>
      )}
      <div className="stage-grid">
        <Section title="Open the expert card">
          <form
            className="stage-form"
            onSubmit={(e) => {
              e.preventDefault();
              setError("");
              try {
                const url = new URL(invitation);
                if (
                  !["http:", "https:"].includes(url.protocol) ||
                  !/^\/e\/[^/]+\/?$/.test(url.pathname) ||
                  url.username ||
                  url.password ||
                  url.search ||
                  url.hash
                )
                  throw new Error(
                    "Use a complete http or https invitation URL with the path /e/token.",
                  );
                if (!mock && /\/(demo|round2|empty)\/?$/.test(url.pathname))
                  throw new Error(
                    "Use a backend-issued expert invitation for API mode.",
                  );
                setQr(url.href);
              } catch (e) {
                setQr("");
                setError(
                  (e as Error).message || "Enter a valid invitation URL.",
                );
              }
            }}
          >
            <label htmlFor="invitation">{en.stage.invitation}</label>
            <input
              id="invitation"
              type="url"
              value={invitation}
              onChange={(e) => setInvitation(e.target.value)}
              placeholder="http://venue-host:5173/e/invitation-token"
              aria-describedby="invitation-help"
            />
            <p id="invitation-help" className="help">
              {mock
                ? "Demo invitation only: answers return fixture receipts."
                : "Paste a backend-issued invitation. Each expert needs their own invitation; this page does not issue credentials."}{" "}
              Use your LAN hostname or HTTPS deployment for phones. A 127.0.0.1
              link works only on this computer.
            </p>
            <button className="primary" type="submit">
              Generate QR
            </button>
          </form>
          {error && (
            <p role="alert" className="error-box">
              {error}
            </p>
          )}
          <div className="stage-instructions">
            <h3>Before inviting the panel</h3>
            <ol>
              <li>
                Connect the phone to the same Wi-Fi, or use a reachable HTTPS
                deployment.
              </li>
              <li>
                Replace the loopback hostname in the invitation with your
                machine’s LAN address.
              </li>
              <li>
                Test opening and sealing on two real phones before presenting.
              </li>
              <li>
                Keep invitations off public ledgers. They grant access to an
                expert card.
              </li>
            </ol>
            <a href="/desk">
              Open analyst desk <ArrowRight size={15} />
            </a>
          </div>
        </Section>
        <Section title="Scan to contribute">
          {qr ? (
            <div
              className={presentation ? "qr-panel presentation-qr" : "qr-panel"}
            >
              <p className="qr-address-note">
                {computerOnly
                  ? "Computer-only address. Replace it with your LAN address before inviting phones."
                  : "Network address supplied. Test it on both phones before presenting."}
              </p>
              <QRCodeSVG
                value={qr}
                size={256}
                marginSize={4}
                level="M"
                role="img"
                aria-label="QR code for the expert invitation shown below"
              />
              <p>
                {mock
                  ? "Synthetic panel demonstration"
                  : "Private expert invitation"}
              </p>
              <a
                className="invitation-link"
                href={qr}
                target="_blank"
                rel="noreferrer"
              >
                {qr}
              </a>
              <CopyButton value={qr} label="Copy invitation" />
              {qr !== invitation.trim() && (
                <p className="qr-address-note" role="status">
                  The QR still uses the previous link. Generate QR to apply your
                  changes.
                </p>
              )}
              <button
                aria-pressed={presentation}
                onClick={() => setPresentation((v) => !v)}
              >
                {presentation ? "Standard QR size" : "Enlarge QR"}
              </button>
            </div>
          ) : (
            <div className="empty-panel">
              <LockKeyhole size={28} />
              <p>Add a reachable invitation URL to generate a QR code.</p>
            </div>
          )}
        </Section>
      </div>
    </Frame>
  );
}
export function Calibration({ token }: { token: string }) {
  const [optedIn, setOptedIn] = useState(false),
    [report, setReport] = useState<Report | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [reload, setReload] = useState(0);
  useEffect(() => {
    if (!optedIn || !calibrationEnabled) return;
    let active = true;
    setBusy(true);
    setError("");
    const job = mock
      ? import("../../fixtures/GET_me_calibration.json").then((m) =>
          sampleDataEnabled() ? sampleCalibration : m.default,
        )
      : endpoint.calibration(token);
    job
      .then((value) => {
        if (active) setReport(value);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [token, optedIn, reload]);
  if(!calibrationEnabled) return <Frame title="Private calibration" subtitle="Separate, voluntary and switched off by default."><Section title="Calibration programme is off"><p>No calibration questions are included in a pulse. Experts must consent separately and see their own report first.</p><a href={`/c/${encodeURIComponent(token)}`}>Read the programme disclosure</a></Section></Frame>;
  return (
    <Frame
      title="Your calibration"
      subtitle="Private, optional feedback on resolved forecasts."
    >
      <p className="panel-caption">
        Available after five resolved forecasts. Answers without an identity link cannot be
        linked to this report or claimed later. Scores never gate expert
        approval.
      </p>
      {!optedIn ? (
        <Section title="Choose whether to view your report">
          <p>
            Opening this report is optional. Free-text observations and
            abstentions are never scored.
          </p>
          <p>We compare your probabilities with resolved outcomes. Only you see the report unless you separately consent to sharing. Participation never affects approval or forecast weights.</p>
          <button disabled={busy} onClick={async () => {setBusy(true);setError("");try{if(!mock)await api(`/me/${encodeURIComponent(token)}/calibration/opt-in`,{consent:true,disclosure_version:"forecast-calibration-1.0"});setOptedIn(true);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>
            I consent to private forecast calibration
          </button>
          {error&&<p role="alert">{error}</p>}
        </Section>
      ) : busy ? (
        <p role="status">Loading calibration…</p>
      ) : error ? (
        <Section title="Report unavailable">
          <p role="alert">
            {error} The service may withhold this report until five forecasts
            resolve.
          </p>
          <button onClick={() => setReload((v) => v + 1)}>Try again</button>
        </Section>
      ) : report && report.n_resolved >= 5 ? (
        <Section title="Resolved forecast calibration">
          <div className="ledger-stats">
            <div>
              <span>Resolved forecasts</span>
              <strong>{report.n_resolved}</strong>
            </div>
            <div>
              <span>Mean Brier score</span>
              <strong>{report.mean_brier.toFixed(2)}</strong>
              <small>Lower is better · 0 is perfect</small>
            </div>
          </div>
          <p className="panel-caption">
            Brier score is the squared difference between a forecast probability
            and its observed outcome. This report measures forecasts, not
            people. Timing comparisons with ACAPS ratings are not supported by
            the export.
          </p>
          <p className="panel-caption">
            A full calibration curve requires forecast-level observations.
          </p>
          {mock && sampleDataEnabled() && (
            <>
              <h3 className="subheading">Resolved forecasts</h3>
              <p className="panel-caption">
                Probabilities and dates are illustrative; outcomes come from the
                export. Each Brier value is (probability − outcome)².
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Risk / country</th>
                      <th>Forecast</th>
                      <th>Outcome</th>
                      <th>Brier score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sampleForecasts.map((f) => (
                      <tr key={f.risk_id}>
                        <td>
                          {f.risk_id}
                          <small>{f.country}</small>
                        </td>
                        <td>{Math.round(f.probability * 100)}%</td>
                        <td>
                          {f.outcome ? "Materialised" : "Not materialised"}
                        </td>
                        <td>{f.brier.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </Section>
      ) : (
        <Section title="Five resolutions required">
          <p>Your optional report will appear after five forecasts resolve.</p>
        </Section>
      )}
      {optedIn&&<button onClick={async()=>{setError("");try{if(!mock)await api(`/me/${encodeURIComponent(token)}/calibration/off`,{});setOptedIn(false);setReport(null);}catch(e){setError((e as Error).message);}}}>Switch my report off</button>}
    </Frame>
  );
}
