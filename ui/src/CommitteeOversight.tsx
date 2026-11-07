import { useState } from "react";
import { Section } from "./Panel";
import { api } from "./service";
import { mock } from "./api";
import { calibrationEnabled } from "./Programme";
import patterns from "../../fixtures/GET_committee_patterns_panel.json";
type PanelPattern=typeof patterns;
export function CommitteeOversight(){
 const [panel,setPanel]=useState("PAN-TCD"),[report,setReport]=useState<PanelPattern|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 return <Section title="Panel patterns and programme status"><p className="panel-caption">The committee reads about panels, not people. Descriptive patterns do not diagnose bias or change approval.</p><label htmlFor="patterns-panel">Panel ID</label><input id="patterns-panel" value={panel} onChange={e=>{setPanel(e.target.value);setReport(null);}}/><button disabled={busy||!panel.trim()} onClick={async()=>{setBusy(true);setError("");setReport(null);try{const value=mock?patterns:await api<PanelPattern>(`/committee/patterns/${encodeURIComponent(panel)}`);if(value.panel_id!==panel)throw new Error("The report belongs to another panel.");if(value.n_pulses<3)throw new Error("Patterns require at least three pulses.");setReport(value);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>Load panel patterns</button>{error&&<p role="alert">{error}</p>}{report&&<><h3>{report.n_pulses} pulses · {report.n_experts} panel members</h3><ul>{report.sentences.map((sentence,i)=><li key={i}>{sentence}</li>)}</ul><h3>Affiliation-level observations</h3><ul>{report.by_affiliation.filter(row=>row.n>=3).map((row,i)=><li key={i}>{row.affiliation_tag} ({row.n}): {row.sentence}</li>)}</ul><p className="panel-caption">Small affiliation groups are merged. Shared expertise and information can also produce similar answers.</p></>}
 <p>Calibration programme: <strong>{calibrationEnabled?"Enabled, consent required":"Off"}</strong></p><p className="panel-caption">No personal reports are shown here. Experts see private reports first; sharing requires a separate opt-in.</p>
 </Section>;
}
