import { useState } from "react";
import { mock } from "./api";
import {
  loadSampleWorkspace,
  clearSampleWorkspace,
  startSampleRound,
  sampleDataEnabled,
  sampleApplications,
} from "./demo-data";

export function DemoSamples() {
  const [error, setError] = useState("");
  if (!mock) return null;
  const enabled = sampleDataEnabled();
  function run(action: () => void) {
    try {
      action();
      location.reload();
    } catch {
      setError(
        "Sample data could not be saved in this tab. Allow session storage and retry.",
      );
    }
  }
  return (
    <section className="demo-samples" aria-labelledby="demo-samples-heading">
      <div>
        <h2 id="demo-samples-heading">Workspace data</h2>
        <p>
          {enabled
            ? `6 risk records · 8 panel estimates · 5 resolved forecasts · ${sampleApplications().length} applications`
            : "Load records across the workspace."}
        </p>
      </div>
      <div className="panel-actions">
        <button onClick={() => run(loadSampleWorkspace)}>
          {enabled ? "Reload records" : "Load records"}
        </button>
        {enabled && (
          <>
            <button onClick={() => run(startSampleRound)}>
              Start a fresh round
            </button>
            <button onClick={() => run(clearSampleWorkspace)}>
              Clear records
            </button>
          </>
        )}
      </div>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
