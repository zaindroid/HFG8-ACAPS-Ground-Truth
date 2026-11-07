import { LockKeyhole } from "lucide-react";
import { endDemoSession } from "./workspace-session";

// The analyst's working shell: a fixed navy sidebar with the workspace on the right.
// Primary items are the steps of the loop; the rest sit under "More".
const primary: [string, string][] = [
  ["/workspace", "Situation"],
  ["/alerts", "Alerts"],
  ["/desk", "Analyst desk"],
  ["/expert", "Expert card"],
  ["/ledger", "Ledger"],
  ["/radar", "Radar"],
  ["/trust", "Trust"],
];
const secondary: [string, string][] = [
  ["/stage", "Stage"],
  ["/calibration", "Calibration"],
  ["/committee", "Committee"],
  ["/apply", "Apply as an expert"],
];
const risks: [string, string, string, string][] = [
  ["/desk", "Chad · R1043", "decision due today", "due"],
  ["/desk", "Lake Chad Basin · R1066", "panel answering", ""],
  ["/ledger", "Niger · R1018", "resolved", ""],
];

export function PortalHeader() {
  const path = location.pathname;
  const current = (href: string) =>
    path === href ||
    (href === "/calibration" && /^\/me\/[^/]+\/calibration\/?$/.test(path)) ||
    (href === "/alerts" && /^\/scans\//.test(path))
      ? "page"
      : undefined;
  return (
    <header className="e2-side">
      <a className="e2-brand" href="/workspace">
        <span className="e2-brand-mark" aria-hidden="true">
          <LockKeyhole size={15} />
        </span>
        <span>
          Sealed Signals
          <small aria-hidden="true">for the ACAPS Risk Radar</small>
        </span>
      </a>
      <nav aria-label="Main navigation" className="e2-nav">
        {primary.map(([href, label]) => (
          <a key={href} href={href} aria-current={current(href)}>
            {label}
            {href === "/alerts" && (
              <span className="e2-count" aria-hidden="true">
                3
              </span>
            )}
          </a>
        ))}
        <details className="e2-more">
          <summary>More</summary>
          {secondary.map(([href, label]) => (
            <a key={href} href={href} aria-current={current(href)}>
              {label}
            </a>
          ))}
        </details>
      </nav>
      <div className="e2-risks">
        <p>My risks</p>
        {risks.map(([href, name, status, kind]) => (
          <a key={name} href={href} className={kind ? "is-due" : undefined}>
            {name}
            <span>{status}</span>
          </a>
        ))}
      </div>
      <div className="e2-user">
        <span className="e2-avatar" aria-hidden="true">
          AH
        </span>
        <span className="e2-user-name">
          Alex Harper
          <small>Risk analyst · demo</small>
        </span>
        <button
          type="button"
          className="e2-signout"
          onClick={() => {
            endDemoSession();
            location.assign("/");
          }}
        >
          Log out
        </button>
      </div>
    </header>
  );
}
