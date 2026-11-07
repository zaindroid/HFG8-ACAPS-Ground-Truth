import React, { Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import { mock } from "./api";
import { hydrateInsights } from "./base-rates";
import { ExpertCard } from "./ExpertCard";
import { LiveWorkspace, Frame } from "./LiveWorkspace";
import { PublicHome, LoginRequired, WorkspaceHome } from "./Entry";
import { hasWorkspaceSession } from "./workspace-session";
const Alerts = lazy(() =>
  import("./Alerts").then((m) => ({ default: m.Alerts })),
);
const Stage = lazy(() =>
  import("./Extras").then((m) => ({ default: m.Stage })),
);
const Calibration = lazy(() =>
  import("./Extras").then((m) => ({ default: m.Calibration })),
);
const Radar = lazy(() => import("./Radar").then((m) => ({ default: m.Radar })));
import { Apply, Committee } from "./Gateway";
const Reach = lazy(() => import("./Reach").then(m=>({default:m.Reach})));
const ContactPreferences = lazy(() => import("./Reach").then(m=>({default:m.ContactPreferences})));
const CalibrationProgramme = lazy(() => import("./Programme").then(m=>({default:m.CalibrationProgramme})));
import "./theme.css";
import "./styles.css";
import "./workspace.css";
import "./polish.css";
import "./v2.css";
import "./portal.css";
import "./entry.css";
import "./v3.css";
import "./verification-trail.css";
import "./ledger-list.css";
import "./journey.css";
import "./risk-insights.css";
import "./draft-summary.css";
import "./panel-visuals.css";
import "./desk-flow.css";
import "./desk-layout.css";
import "./brand-bridge.css";

const MockWorkspace = lazy(() =>
  import("./Workspace").then((m) => ({ default: m.Workspace })),
);
class Boundary extends React.Component<
  { children: React.ReactNode },
  { error: boolean }
> {
  state = { error: false };
  static getDerivedStateFromError() {
    return { error: true };
  }
  render() {
    return this.state.error ? (
      <Frame
        title="This view could not load"
        subtitle="The response may not match the current contract."
      >
        <p role="alert">
          Refresh to retry. Unsaved inputs may need to be entered again.
        </p>
        <button onClick={() => location.reload()}>Reload page</button>
      </Frame>
    ) : (
      this.props.children
    );
  }
}
function Router() {
  const path = location.pathname;
  if (path === "/") return <PublicHome />;
  if (path === "/login") return <PublicHome />;
  // V3 expert invitations remain no-login links. Team tools use the demo entry gate.
  const expert = /^\/e\/([^/]+)\/?$/.exec(path);
  if (expert) return <ExpertCard token={expert[1]} />;
  const calibration = /^\/me\/([^/]+)\/calibration\/?$/.exec(path);
  const preferences = /^\/preferences\/([^/]+)\/?$/.exec(path);
  if(preferences) return <ContactPreferences id={preferences[1]}/>;
  const programme = /^\/c\/([^/]+)\/?$/.exec(path);
  if(programme) return <CalibrationProgramme token={programme[1]}/>;
  if (calibration) return <Calibration token={calibration[1]} />;
  if (!hasWorkspaceSession()) return <LoginRequired />;
  if (/^\/(countries|analysis|topics|search)(\/|$)/.test(path))
    return <WorkspaceRedirect />;
  if (path === "/workspace") return <WorkspaceHome />;
  if (path === "/alerts") return <Alerts />;
  if (path === "/reach") return <Reach />;
  if (path === "/radar") return <Radar />;
  if (path === "/expert")
    return mock ? (
      <ExpertCard token="demo" />
    ) : (
      <Frame
        title="Expert card"
        subtitle="Open the personal invitation sent by your analyst."
      >
        <p>
          Each expert receives their own no-login invitation. The live workspace
          does not create a shared invitation.
        </p>
        <a href="/stage">Open Stage to display an issued invitation</a>
      </Frame>
    );
  if (path === "/calibration")
    return mock ? (
      <Calibration token="demo" />
    ) : (
      <Frame
        title="Private calibration"
        subtitle="Optional feedback after at least five resolved forecasts."
      >
        <p>
          Open your private report from your personal invitation. Anonymous
          answers cannot be linked to calibration or claimed later.
        </p>
      </Frame>
    );
  if (path === "/desk" || path === "/ledger") {
    const page = path === "/desk" ? "desk" : "ledger";
    return mock ? <MockWorkspace page={page} /> : <LiveWorkspace page={page} />;
  }
  if (path === "/stage") return <Stage />;
  if (path === "/apply") return <Apply />;
  if (path === "/committee") return <Committee />;
  return (
    <Frame
      title="Page not found"
      subtitle="Open Risk Radar to find the right view."
    >
      <a href="/radar">Go to Risk Radar</a>
    </Frame>
  );
}
function WorkspaceRedirect() {
  React.useEffect(() => {
    location.replace("/workspace");
  }, []);
  return (
    <main className="login-redirect">
      <p role="status">Opening the task workspace…</p>
      <a href="/workspace">Open workspace</a>
    </main>
  );
}
void hydrateInsights();

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Boundary>
      <Suspense
        fallback={
          <div className="workspace" role="status">
            Opening workspace…
          </div>
        }
      >
        <Router />
      </Suspense>
    </Boundary>
  </React.StrictMode>,
);
