import { useState } from "react";
import { CommitteeScoring } from "./V3Workflow";
import { CommitteeOversight } from "./CommitteeOversight";
import { mock } from "./api";
import {
  sampleDataEnabled,
  sampleApplications,
  saveSampleApplication,
  saveSampleApproval,
  type SampleApplication,
} from "./demo-data";
import { Frame, Section } from "./LiveWorkspace";
import { endpoint } from "./service";
import type { Approval } from "./v2-types";

const themes = [
  "conflict",
  "displacement",
  "flood",
  "earthquake",
  "epidemic",
  "food",
  "access",
  "political",
  "economic",
];
export function Apply() {
  const [geo, setGeo] = useState("TCD, SDN"),
    [selected, setSelected] = useState<string[]>(["conflict"]),
    [affiliation, setAffiliation] = useState("think-tank"),
    [languages, setLanguages] = useState("en, fr"),
    [channel, setChannel] = useState("email"),
    [synthetic, setSynthetic] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [receipt, setReceipt] = useState<{
      expert_id: string;
      status: string;
    } | null>(null);
  return (
    <Frame
      title="Expert application"
      subtitle="Geographic knowledge and thematic expertise. Reviewed by ACAPS."
    >
      <div className="application-layout">
        <Section
          title={
            receipt
              ? "Application received"
              : "Tell the committee about your expertise"
          }
        >
          {receipt ? (
            <div role="status">
              <p>
                Application {receipt.expert_id}: {receipt.status}.
              </p>
              <p>
                Two distinct committee approvals are required before a
                credential can be issued. No access has been granted yet.
              </p>
              <a
                href={`/committee?expert_id=${encodeURIComponent(receipt.expert_id)}`}
              >
                Review synthetic application
              </a>
            </div>
          ) : (
            <form
              className="gateway-form"
              onSubmit={async (e) => {
                e.preventDefault();
                setError("");
                const geo_tags = geo
                  .split(",")
                  .map((v) => v.trim().toUpperCase())
                  .filter(Boolean);
                const langs = languages
                  .split(",")
                  .map((v) => v.trim().toLowerCase())
                  .filter(Boolean);
                if (
                  !geo_tags.length ||
                  geo_tags.some((v) => !/^[A-Z]{3}$/.test(v)) ||
                  !selected.length ||
                  !langs.length ||
                  langs.some((v) => !/^[a-z]{2,3}$/.test(v))
                ) {
                  setError(
                    "Use three-letter country codes, choose a theme and enter language codes such as en or fr.",
                  );
                  return;
                }
                setBusy(true);
                try {
                  const value =
                    mock && sampleDataEnabled()
                      ? saveSampleApplication({
                          geo_tags,
                          theme_tags: selected,
                          affiliation_tag: affiliation,
                          languages: langs,
                          channel,
                        })
                      : mock
                        ? (
                            await import("../../fixtures/POST_experts_apply_response.json")
                          ).default
                        : await endpoint.apply({
                            geo_tags,
                            theme_tags: selected,
                            affiliation_tag: affiliation,
                            languages: langs,
                            channel,
                          });
                  setReceipt(value);
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setBusy(false);
                }
              }}
            >
              {mock && sampleDataEnabled() && (
                <button
                  type="button"
                  onClick={() => {
                    setGeo("TCD, SDN");
                    setSelected(["conflict", "displacement"]);
                    setAffiliation("research");
                    setLanguages("en, fr");
                    setChannel("email");
                    setSynthetic(true);
                  }}
                >
                  Use sample application
                </button>
              )}
              <label htmlFor="geo-tags">
                Geographic expertise · ISO country codes
              </label>
              <input
                id="geo-tags"
                value={geo}
                onChange={(e) => setGeo(e.target.value)}
                placeholder="TCD, SDN"
                required
              />
              <fieldset className="theme-picker">
                <legend>Thematic expertise</legend>
                {themes.map((t) => (
                  <label key={t}>
                    <input
                      type="checkbox"
                      checked={selected.includes(t)}
                      onChange={() =>
                        setSelected((v) =>
                          v.includes(t) ? v.filter((x) => x !== t) : [...v, t],
                        )
                      }
                    />
                    {t}
                  </label>
                ))}
              </fieldset>
              <label htmlFor="affiliation">Affiliation type</label>
              <select
                id="affiliation"
                value={affiliation}
                onChange={(e) => setAffiliation(e.target.value)}
              >
                {[
                  "think-tank",
                  "research",
                  "journalism",
                  "ngo",
                  "un-agency",
                  "anticipatory-action",
                  "independent",
                ].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
              <label htmlFor="languages">Language codes</label>
              <input
                id="languages"
                value={languages}
                onChange={(e) => setLanguages(e.target.value)}
                required
              />
              <label htmlFor="channel">Preferred invitation channel</label>
              <select
                id="channel"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
              >
                <option value="email">Email magic link</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="sms">SMS</option>
              </select>
              <label className="changed">
                <input
                  type="checkbox"
                  required
                  checked={synthetic}
                  onChange={(e) => setSynthetic(e.target.checked)}
                />{" "}
                This is a synthetic expert application. No real personal data.
              </label>
              {error && (
                <p className="error-box" role="alert">
                  {error}
                </p>
              )}
              <button
                type="submit"
                disabled={busy || !synthetic}
                className="primary"
              >
                {busy ? "Sending application…" : "Apply for committee review"}
              </button>
            </form>
          )}
        </Section>
        <Section title="A moderated trust gateway">
          <p>
            Experts are professionals who track crises: analysts, journalists,
            researchers and early-warning practitioners.
          </p>
          <ol className="gateway-steps">
            <li>Declare geographic and thematic expertise.</li>
            <li>ACAPS committee reviews credentials and track of work.</li>
            <li>Two admins approve; the backend issues a credential.</li>
            <li>Panels draw from approved experts with composition limits.</li>
          </ol>
          <p className="panel-caption">
            The current application contract collects tags only. Credential
            evidence collection and delivery of email invitations are backend
            handoff items; this form does not ask for real names or email
            addresses.
          </p>
          {mock && (
            <p className="caveat">
              Fixture demo. Applications are not sent to ACAPS.
            </p>
          )}
        </Section>
      </div>
    </Frame>
  );
}
export function Committee() {
  const samples = mock && sampleDataEnabled();
  const initialId =
    new URLSearchParams(location.search).get("expert_id") ||
    (samples ? "X-SAMPLE-001" : "");
  const initialApplication = samples
    ? sampleApplications().find((a) => a.expert_id === initialId)
    : undefined;
  const [applications, setApplications] = useState<SampleApplication[]>(() =>
    samples ? sampleApplications() : [],
  );
  const [id, setId] = useState(initialId),
    [receipt, setReceipt] = useState<Approval | null>(
      initialApplication
        ? {
            expert_id: initialId,
            status: initialApplication.status,
            approved_by: initialApplication.approved_by,
          }
        : null,
    ),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [admin, setAdmin] = useState("synthetic-admin-a"),
    [votes, setVotes] = useState<string[]>(
      initialApplication?.approved_by || [],
    );
  const approved = receipt?.status === "approved";
  return (
    <Frame
      title="Committee review"
      subtitle="Two distinct ACAPS admins approve an expert before credential issuance."
    >
      <div className="mode-banner">
        Moderator-only workspace. Committee access requires authenticated admin
        identity from the backend; this page does not grant access.
      </div>
      {samples && (
        <Section title="Applications">
          <p className="panel-caption">
            Synthetic records stored in this tab. Select one to review its tags
            and approval progress.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Application</th>
                  <th>Expertise</th>
                  <th>Status</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((a) => (
                  <tr key={a.expert_id}>
                    <td>
                      {a.expert_id}
                      <small>{a.pseudonym}</small>
                    </td>
                    <td>
                      {a.geo_tags.join(", ")}
                      <small>{a.theme_tags.join(", ")}</small>
                    </td>
                    <td>
                      {a.status} · {a.approved_by.length}/2 approvals
                    </td>
                    <td>
                      <button
                        onClick={() => {
                          setId(a.expert_id);
                          setReceipt({
                            expert_id: a.expert_id,
                            status: a.status,
                            approved_by: a.approved_by,
                          });
                          setVotes(a.approved_by);
                          setAdmin(
                            a.approved_by.includes("synthetic-admin-a")
                              ? "synthetic-admin-b"
                              : "synthetic-admin-a",
                          );
                          setError("");
                        }}
                      >
                        Review {a.expert_id}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
      <Section title="Review an application">
        <p>
          {samples
            ? "Review the selected sample application. Approval changes are saved in this tab and never issue real credentials."
            : "The current API has no applications-list route. Open an application by the ID returned when it was submitted."}
        </p>
        <div className="live-toolbar">
          <label htmlFor="application-id">Application ID</label>
          <input
            id="application-id"
            value={id}
            onChange={(e) => {
              setId(e.target.value);
              setReceipt(null);
              setVotes([]);
              setError("");
            }}
            placeholder="X-0009"
          />
          {mock && (
            <>
              <label htmlFor="demo-admin">Synthetic admin</label>
              <select
                id="demo-admin"
                value={admin}
                onChange={(e) => setAdmin(e.target.value)}
              >
                <option value="synthetic-admin-a">Synthetic admin A</option>
                <option value="synthetic-admin-b">Synthetic admin B</option>
              </select>
            </>
          )}
          <button
            className="primary"
            disabled={
              busy || !id.trim() || approved || (mock && votes.includes(admin))
            }
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                if (mock) {
                  const next = Array.from(new Set([...votes, admin]));
                  setVotes(next);
                  const approval = {
                    expert_id: id,
                    status: next.length >= 2 ? "approved" : "applied",
                    approved_by: next,
                  };
                  setReceipt(samples ? saveSampleApproval(id, next) : approval);
                  if (samples) setApplications(sampleApplications());
                } else {
                  setReceipt(await endpoint.approve(id.trim()));
                }
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Recording approval…" : "Record my approval"}
          </button>
        </div>
        {error && (
          <p className="error-box" role="alert">
            {error}
          </p>
        )}
        {receipt && (
          <div className="decision-log" role="status">
            <h3>
              {approved
                ? "Expert approved"
                : receipt.approved_by?.length === 0
                  ? "Awaiting first approval"
                  : "Awaiting second approval"}
            </h3>
            <p>
              Status: {receipt.status}.{" "}
              {receipt.approved_by
                ? `${receipt.approved_by.length} distinct approvals recorded.`
                : receipt.approvals !== undefined
                  ? `${receipt.approvals} approvals recorded.`
                  : "Approval count not supplied by the API."}
            </p>
            <p>
              {mock
                ? "Synthetic approval replay only. No credential was issued."
                : approved
                  ? "The backend reports approval. Credential delivery is handled by the backend."
                  : "No credential can be assumed until the backend reports approval."}
            </p>
          </div>
        )}
      </Section>
      <p className="panel-caption">
        This UI never treats two clicks by the same admin as two independent
        approvals. No credential or approval count is invented in API mode.
      </p>
      <CommitteeScoring />
      <CommitteeOversight />
    </Frame>
  );
}
