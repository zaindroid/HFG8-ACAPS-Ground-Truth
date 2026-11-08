import { LockKeyhole } from "lucide-react";
import { endDemoSession } from "./workspace-session";

export function PortalHeader() {
  const path = location.pathname;
  return (
    <header className="site-header workspace-header portal-header">
      <div className="portal-topline">
        <a className="brand" href="/workspace">
          <span className="brand-mark">
            <LockKeyhole size={19} />
          </span>
          Sealed Signals
        </a>
        <span className="portal-purpose">Expert validation workspace</span>
        <button
          className="portal-signout"
          onClick={() => {
            endDemoSession();
            location.assign("/");
          }}
        >
          Log out
        </button>
      </div>
      <div className="portal-navigation">
        <nav aria-label="Main navigation">
          {[
            ["/alerts", "Alerts"],
            ["/expert", "Expert card"],
            ["/desk", "Analyst desk"],
            ["/ledger", "Ledger"],
          ].map(([href, label]) => (
            <a
              key={href}
              href={href}
              aria-current={
                path === href ||
                (href === "/calibration" &&
                  /^\/me\/[^/]+\/calibration\/?$/.test(path))
                  ? "page"
                  : undefined
              }
            >
              {label}
            </a>
          ))}
          <details className="workspace-menu">
            <summary>More</summary>
            <div>
              {[
                ["/workspace", "Overview"],
                ["/radar", "Radar"],
                ["/calibration", "Calibration"],
                ["/stage", "Stage"],
                ["/committee", "Committee"],
                ["/trust", "Trust and privacy"],
                ["/apply", "Apply as an expert"],
              ].map(([href, label]) => (
                <a
                  href={href}
                  key={href}
                  aria-current={path === href ? "page" : undefined}
                >
                  {label}
                </a>
              ))}
            </div>
          </details>
        </nav>
      </div>
    </header>
  );
}
