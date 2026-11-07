import { useState } from "react";
import { Check, Link2 } from "lucide-react";
import { alertService, type Crisis } from "./alerts-service";
import { mock } from "./api";
import { endpoint, type Risk } from "./service";
import { sampleDataEnabled, sampleRisks } from "./demo-data";
import riskFixture from "../../fixtures/GET_risks.json";

export function RiskLink({
  crisis,
  onConfirmed,
}: {
  crisis: Crisis;
  onConfirmed: (record: Crisis) => void;
}) {
  const [risks, setRisks] = useState<Risk[] | null>(null),
    [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [confirmed, setConfirmed] = useState("");
  const [consent, setConsent] = useState(false);
  const risk = risks?.find((r) => r.risk_id === selected);
  async function load() {
    setBusy(true);
    setError("");
    setConsent(false);
    setConfirmed("");
    try {
      const rows = mock
        ? sampleDataEnabled()
          ? sampleRisks
          : riskFixture.risks
        : (await endpoint.risks()).risks;
      const active = rows.filter(
        (r) => r.status === "Active" && crisis.iso3.includes(r.country_iso),
      );
      setRisks(active);
      setSelected(
        active.find((r) => crisis.linked_risks.includes(r.risk_id))?.risk_id ||
          active[0]?.risk_id ||
          "",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details
      className="risk-link"
      onToggle={(e) => {
        if (e.currentTarget.open && risks === null && !busy && !error)
          void load();
      }}
    >
      <summary>
        <Link2 size={14} aria-hidden="true" />
        Review risk link
      </summary>
      <div className="risk-link-body">
        <p>
          Link this crisis to an active risk before routing a panel request.
        </p>
        <p>
          <strong>Recorded links:</strong>{" "}
          {crisis.linked_risks.join(", ") || "None"}
        </p>
        {busy && <p role="status">Checking risk link…</p>}
        {error && (
          <p className="error-box" role="alert">
            {error}
          </p>
        )}
        {risks?.length === 0 ? (
          <p>No active risks for this country are loaded.</p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!selected || !consent || busy) return;
              setBusy(true);
              setError("");
              setConfirmed("");
              void alertService
                .linkRisk(selected, crisis.crisis_id)
                .then((record) => {
                  setConfirmed(selected);
                  onConfirmed(record);
                })
                .catch((e) => setError(e.message))
                .finally(() => setBusy(false));
            }}
          >
            <label htmlFor="linked-risk">
              Active risk in {crisis.iso3.join(", ")}
            </label>
            <select
              id="linked-risk"
              value={selected}
              disabled={busy || !risks}
              onChange={(e) => {
                setSelected(e.target.value);
                setConsent(false);
                setConfirmed("");
              }}
            >
              <option value="" disabled>
                Select a risk
              </option>
              {risks?.map((r) => (
                <option key={r.risk_id} value={r.risk_id}>
                  {r.risk_id} · {r.country}
                </option>
              ))}
            </select>
            {risk && (
              <div className="risk-link-context">
                <strong>{risk.title}</strong>
                <span>Crisis drivers: {crisis.drivers.join(", ")}</span>
                <details>
                  <summary>Risk triggers</summary>
                  <ul>
                    {risk.triggers.map((t) => (
                      <li key={t.id}>{t.title}</li>
                    ))}
                  </ul>
                </details>
              </div>
            )}
            <label className="risk-link-consent">
              <input
                type="checkbox"
                checked={consent}
                disabled={busy || !risk}
                onChange={(e) => setConsent(e.target.checked)}
              />
              The geography and risk triggers match this crisis.
            </label>
            <div className="risk-link-actions">
              <button disabled={busy || !consent || !risk}>
                Confirm risk link
              </button>
              <button type="button" disabled={busy} onClick={() => void load()}>
                Refresh risks
              </button>
            </div>
            {confirmed && (
              <p className="risk-link-confirmed" role="status">
                <Check size={15} aria-hidden="true" /> {confirmed} linked to{" "}
                {crisis.crisis_id}.
              </p>
            )}
          </form>
        )}
      </div>
    </details>
  );
}
