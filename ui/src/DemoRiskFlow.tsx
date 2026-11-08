import { useEffect, useState } from "react";
import { ArrowRight, Check, Clipboard, ExternalLink, Mail, MessageCircle, Phone, UserRound } from "lucide-react";
import { type DemoExpert, type DemoRisk, demoRisks, expertsForRisk } from "./demo-risk-data";
import { type DemoInvitation, invitationsForRisk, issueDemoInvitations, loadDemoState, sharedDemo } from "./demo-invitations";
import { api } from "./service";
import { QRCodeSVG } from "qrcode.react";
import { LockKeyhole, Smartphone } from "lucide-react";
import { liveDirectory, liveSeats } from "./live-panel";
import { type LiveSeat, loadSeats } from "./live-seats";
import "./demo-risk-flow.css";

const channels = ["Email", "WhatsApp", "Signal", "SMS", "Scheduled call"] as const;
type Channel = (typeof channels)[number];
const channelIcon: Record<Channel, typeof Mail> = { Email: Mail, WhatsApp: MessageCircle, Signal: MessageCircle, SMS: MessageCircle, "Scheduled call": Phone };
const initialChannels: Channel[] = ["Email", "WhatsApp", "Email", "Signal", "SMS", "Email", "WhatsApp", "Scheduled call"];

function ProbabilityBand({ value }: { value: string }) {
  const selected = ["Very Low", "Low", "Medium", "High", "Very High"].indexOf(value);
  return <div className="dr-probability" aria-label={`ACAPS probability ${value}`}><div>{[0, 1, 2, 3, 4].map((i) => <i key={i} className={i <= selected ? "filled" : ""}/>)}</div><strong>{value}</strong></div>;
}

export function RiskSelect({ value, onSelect, onContinue }: { value: DemoRisk; onSelect: (risk: DemoRisk) => void; onContinue: () => void }) {
  // The live round leaves three of its eight places open, so the count the analyst sees is
  // the recorded profiles plus the seats somebody still has to take.
  const available = expertsForRisk(value).length + (value.live ? liveSeats.length : 0);
  return <section className="dr-view">
    <div className="dr-heading"><div><p className="dc-kicker">01 / CHOOSE A RISK</p><h1>Which risk needs another view?</h1><p>Select an active risk to review its current probability and available experts.</p></div><span className="dr-count">{demoRisks.length} ACTIVE RISKS</span></div>
    <div className="dr-risk-layout"><div className="dr-risk-list" aria-label="Active risks">{demoRisks.map((item) => <button key={item.risk_id} className={`dr-risk-row ${value.risk_id === item.risk_id ? "selected" : ""}`} aria-pressed={value.risk_id === item.risk_id} onClick={() => onSelect(item)}><span className="dr-risk-country">{item.country}<small>{item.risk_id}</small></span><span className="dr-risk-title">{item.short}{item.live && <em className="dr-live-tag">Live demo</em>}<small>{item.status} · {item.level} risk</small></span><ProbabilityBand value={item.probability_acaps}/><ArrowRight size={17} aria-hidden="true"/></button>)}</div>
      <aside className="dr-risk-detail"><span className="dc-label">SELECTED RISK</span><h2>{value.short}</h2><p className="dr-full-title">{value.title}</p><div className="dr-detail-metrics"><div><span>ACAPS probability</span><ProbabilityBand value={value.probability_acaps}/></div><div><span>Available experts</span><strong>{available}</strong></div></div><div className="dr-detail-source">{value.source} · {value.risk_id}</div><button className="dc-primary dc-full" onClick={onContinue}>Find experts <ArrowRight size={17}/></button></aside></div>
    {value.risk_id === "R1043" && <div className="dr-signal-strip"><span>APRIL 2026 SIGNAL</span><strong>Chad severity 6.1 <ArrowRight size={18}/> 6.9</strong><span>Largest increase among 123 crises</span></div>}
    {value.live && <div className="dr-signal-strip"><span>LIVE ROUND</span><strong>{liveDirectory.length} recorded <ArrowRight size={18}/> {liveSeats.length} open seats</strong><span>Three places are answered in the room, by QR code</span></div>}
  </section>;
}

function Profile({ expert, onClose }: { expert: DemoExpert; onClose: () => void }) {
  useEffect(() => { const close = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); }; window.addEventListener("keydown", close); return () => window.removeEventListener("keydown", close); }, [onClose]);
  return <div className="dr-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="dr-profile" role="dialog" aria-modal="true" aria-label={`${expert.pseudonym} profile`}><button className="dr-close" onClick={onClose} aria-label="Close profile">×</button><div className="dr-profile-avatar"><UserRound size={28}/></div><span className="dc-label">SAMPLE EXPERT PROFILE</span><h2>{expert.pseudonym}</h2><p>{expert.affiliation_tag.toUpperCase()} · {expert.region}</p><dl><div><dt>Specialties</dt><dd>{expert.theme_tags.join(" · ")}</dd></div><div><dt>Context coverage</dt><dd>{expert.geo_tags.join(", ")}</dd></div><div><dt>Risk match</dt><dd>{Math.round(expert.match * 100)}%</dd></div></dl><p className="dr-profile-note">Sample profile for the hackathon demo. Individual answers and scores are not shown to the analyst.</p><button className="dc-primary dc-full" onClick={onClose}>Back to experts</button></section></div>;
}

/**
 * The live round's roster: five recorded answers and three codes.
 *
 * A seat is not an invitation. An invitation names someone and goes to them; a seat is a place
 * on the panel that the first person to scan its code takes, which is the only way to put
 * people who are in the room on a panel without collecting their contact details first. What
 * the analyst needs to see here is which seats are free, so each tile reports its own state and
 * the code disappears once the seat is answered.
 */
export function LiveRoster({ risk, onBack, onContinue, onAllSeatsTaken }: { risk: DemoRisk; onBack: () => void; onContinue: () => void; onAllSeatsTaken?: () => void }) {
  const experts = expertsForRisk(risk);
  const [profile, setProfile] = useState<DemoExpert | null>(null);
  const tokens = liveSeats.map((seat) => seat.token);
  const [seats, setSeats] = useState<LiveSeat[]>(() => tokens.map((token) => ({ token, state: "open", mine: false })));
  const [message, setMessage] = useState("");
  const [moving, setMoving] = useState(false);
  useEffect(() => {
    let active = true;
    const refresh = () => loadSeats(tokens).then((value) => { if (active) { setSeats(value); setMessage(""); } }).catch((error) => { if (active) setMessage((error as Error).message); });
    void refresh();
    // Two seconds, because the point of the tile is that the room watches a seat turn while
    // somebody is answering on it.
    const timer = window.setInterval(() => void refresh(), 2000);
    window.addEventListener("focus", refresh);
    return () => { active = false; window.clearInterval(timer); window.removeEventListener("focus", refresh); };
  }, [risk.risk_id]);
  const submitted = seats.filter((seat) => seat.state === "submitted").length;
  // Every code has been picked up, so there is nothing left to watch here and the answers are
  // about to start landing on the next screen. Taken, not answered: somebody reading the
  // question on their phone has already left this screen with nothing to do, and waiting for
  // all three to submit would mean the first answers arrive while the room is still looking at
  // three QR codes. A beat first, so the jump is something the room sees rather than a flicker.
  const taken = submitted === liveSeats.length;
  useEffect(() => {
    if (!taken || !onAllSeatsTaken) return;
    setMoving(true);
    const timer = window.setTimeout(onAllSeatsTaken, 1400);
    return () => window.clearTimeout(timer);
  }, [taken, onAllSeatsTaken]);
  const stateCopy: Record<LiveSeat["state"], string> = { open: "Open · scan to join", in_use: "In use right now", submitted: "Answer confirmed" };
  return <section className="dr-view">
    <div className="dr-heading"><div><button className="dc-back" onClick={onBack}>← Back to risks</button><p className="dc-kicker">02 / EXPERTS</p><h1>Experts for {risk.country}</h1><p>{experts.length} answers are already recorded for this demo. The remaining {liveSeats.length} places are taken in the room.</p></div><div className="dr-roster-count"><strong>{experts.length + liveSeats.length}</strong><span>panel places</span></div></div>
    <div className={`dr-roster-top ${moving ? "dr-roster-moving" : ""}`}><div><strong>{moving ? "All three answers confirmed" : `${submitted} of ${liveSeats.length} answers confirmed`}</strong><span role="status">{moving ? "Opening responses and counting the answers into the charts." : "Each code admits one person. A seat in use cannot be taken by anyone else, and a seat that has been answered is closed for good."}</span></div><button className="dc-primary" onClick={onContinue}>Continue to responses <ArrowRight size={16}/></button></div>
    <div className="dr-seat-grid" aria-label="Open panel seats">
      {liveSeats.map((seat) => {
        const current = seats.find((item) => item.token === seat.token) || { token: seat.token, state: "open" as const, mine: false };
        const link = `${location.origin}/e/${seat.token}`;
        return <article className={`dr-seat dr-seat-${current.state}`} key={seat.token}>
          <div className="dr-seat-top"><span className="dc-label">{seat.label.toUpperCase()}</span><span className="dr-seat-state">{current.state === "submitted" ? <Check size={14}/> : current.state === "in_use" ? <Smartphone size={14}/> : <LockKeyhole size={14}/>}{stateCopy[current.state]}</span></div>
          <h2>{seat.expertise}</h2>
          <p>{seat.affiliation} · {seat.region}</p>
          <div className="dr-seat-code">
            {current.state === "submitted"
              ? <div className="dr-seat-done" role="status"><Check size={34}/><strong>Submitted</strong><span>This code no longer works.</span></div>
              : <><QRCodeSVG value={link} size={208} level="M" marginSize={2} title={`Join as ${seat.expertise}`}/>{current.state === "in_use" && <p className="dr-seat-held" role="status">Open on a device now</p>}</>}
          </div>
          <div className="dr-seat-foot">
            <a href={`/e/${seat.token}`} target="_blank" rel="noreferrer">Open seat <ExternalLink size={13}/></a>
          </div>
        </article>;
      })}
    </div>
    <div className="dr-expert-list dr-recorded-list">{experts.map((expert, index) => <article className="dr-expert-row dr-recorded-row" key={expert.expert_id}><button className="dr-expert-identity" onClick={() => setProfile(expert)}><span className="dr-avatar"><UserRound size={20}/></span><span><strong>{expert.pseudonym}</strong><small>{expert.affiliation_tag.toUpperCase()} · {expert.region} · {expert.theme_tags.join(", ")}</small></span></button><span className={`dr-match ${expert.geo_tags.includes(risk.country_iso) ? "direct" : "thematic"}`}>{expert.geo_tags.includes(risk.country_iso) ? "Country match" : "Thematic match"}</span><span className="dr-recorded-state"><Check size={14}/> Answer recorded for this demo</span><span className="dr-recorded-index">{index + 1} of {experts.length}</span></article>)}</div>
    <p className="dr-demo-note">{sharedDemo ? "The codes above resolve through the public demo address, so a phone in the room can open them." : "Without the shared demo server these codes only open in this browser. Start the shared demo to let phones join."}</p>
    <div className="dr-roster-footer"><span role="status">{message || `${submitted} of ${liveSeats.length} seats answered. Individual answers stay sealed until the panel is revealed.`}</span><button className="dc-primary" onClick={onContinue}>Continue to responses <ArrowRight size={17}/></button></div>
    {profile && <Profile expert={profile} onClose={() => setProfile(null)}/>}
  </section>;
}

export function ExpertRoster({ risk, onBack, onContinue, onReady }: { risk: DemoRisk; onBack: () => void; onContinue: () => void; onReady: () => void }) {
  const [experts, setExperts] = useState<DemoExpert[]>(() => expertsForRisk(risk));
  const [profile, setProfile] = useState<DemoExpert | null>(null);
  const [methods, setMethods] = useState<Record<string, Channel>>(() => Object.fromEntries(experts.map((expert, i) => [expert.expert_id, initialChannels[i % initialChannels.length]])));
  const [invitations, setInvitations] = useState<DemoInvitation[]>(() => invitationsForRisk(risk.risk_id));
  const [message, setMessage] = useState("");
  const [panelLoading, setPanelLoading] = useState(sharedDemo);
  useEffect(() => { let active = true; setExperts(expertsForRisk(risk)); if (sharedDemo && risk.risk_id === "R1043") { setPanelLoading(true); void api<{ experts: DemoExpert[] }>(`/panels/match?risk_id=${risk.risk_id}`).then((value) => { if (active) setExperts(value.experts); }).catch((error) => { if (active) setMessage((error as Error).message); }).finally(() => { if (active) setPanelLoading(false); }); } else setPanelLoading(false); return () => { active = false; }; }, [risk.risk_id]);
  useEffect(() => { let active = true; setMethods(Object.fromEntries(experts.map((expert, i) => [expert.expert_id, initialChannels[i % initialChannels.length]]))); void loadDemoState(risk.risk_id).then((value) => { if (!active) return; setInvitations(value.invitations); if (risk.risk_id === "R1043" && value.invitations.length === 8) onReady(); }).catch((error) => { if (active) setMessage((error as Error).message); }); return () => { active = false; }; }, [risk.risk_id, experts]);
  const issued = invitations.filter((item) => experts.some((expert) => expert.expert_id === item.expertId));
  const ready = experts.length >= 5 && issued.length === experts.length;
  async function generate() {
    try { const next = await issueDemoInvitations(risk.risk_id, experts.map((expert) => expert.expert_id)); setInvitations(next); onReady(); setMessage(`${next.length} personal demo links are ready. No messages were sent.`); }
    catch (error) { setMessage((error as Error).message || "Could not generate the links."); }
  }
  async function copy(token: string, expert: DemoExpert, method: Channel) {
    const link = `${location.origin}/e/${token}`;
    const note = method === "Scheduled call"
      ? `Call script for ${expert.pseudonym}: You are invited to answer one private question about eastern Chad. Your personal confirmation link is ${link}. You may decline or say STOP at any time.`
      : method === "Email"
        ? `Subject: Expert question · eastern Chad\n\nHello ${expert.pseudonym}, your knowledge of ${expert.theme_tags.join(" and ")} is relevant to a short risk question. Please use your personal link: ${link}\n\nYour answer is private until the panel deadline. Reply STOP to stop invitations.`
        : `${method} message for ${expert.pseudonym}: One short expert question about eastern Chad: ${link} Your answer stays private until the deadline. Reply STOP any time.`;
    try { await navigator.clipboard.writeText(note); setMessage(`${method} invitation copied for ${expert.pseudonym}. No message was sent.`); }
    catch { setMessage("Copy unavailable. Open the questionnaire and copy its address."); }
  }
  return <section className="dr-view"><div className="dr-heading"><div><button className="dc-back" onClick={onBack}>← Back to risks</button><p className="dc-kicker">02 / SELECT EXPERTS</p><h1>Experts for {risk.country}</h1><p>Review the suggested panel, choose a contact method, then create personal links.</p></div><div className="dr-roster-count"><strong>{experts.length}</strong><span>available profiles</span></div></div>
    <div className="dr-roster-top"><div><strong>{experts.length >= 5 ? "Panel ready" : "More experts needed"}</strong><span>{experts.length >= 5 ? "A panel needs at least five responses before results can be shown." : `Only ${experts.length} profiles match this risk in the demo directory; five are required.`}</span></div>{experts.length >= 5 && <button className="dc-primary" disabled={panelLoading} onClick={ready ? onContinue : generate}>{panelLoading ? "Loading panel…" : ready ? "Continue to responses" : `Generate ${experts.length} personal links`} <ArrowRight size={16}/></button>}</div>
    {experts.length ? <div className="dr-expert-list">{experts.map((expert) => { const invitation = issued.find((item) => item.expertId === expert.expert_id); const method = methods[expert.expert_id] || "Email"; const Icon = channelIcon[method]; return <article className="dr-expert-row" key={expert.expert_id}><button className="dr-expert-identity" onClick={() => setProfile(expert)}><span className="dr-avatar"><UserRound size={20}/></span><span><strong>{expert.pseudonym}</strong><small>{expert.affiliation_tag.toUpperCase()} · {expert.region} · {expert.theme_tags.join(", ")}</small></span></button><span className={`dr-match ${expert.geo_tags.includes(risk.country_iso) ? "direct" : "thematic"}`}>{expert.geo_tags.includes(risk.country_iso) ? "Country match" : "Thematic match"}</span><label className="dr-method"><span>Contact method</span><span><Icon size={15}/><select aria-label={`Contact method for ${expert.pseudonym}`} value={method} onChange={(event) => setMethods({ ...methods, [expert.expert_id]: event.target.value as Channel })}>{channels.map((channel) => <option key={channel}>{channel}</option>)}</select></span></label><div className="dr-invite-action">{invitation ? <><button onClick={() => void copy(invitation.token, expert, method)} title={`Copy ${method} invitation`}><Clipboard size={16}/> Copy invite</button><a href={`/e/${invitation.token}`} target="_blank" rel="noreferrer" title="Open expert questionnaire">Open <ExternalLink size={14}/></a></> : <span>Link pending</span>}</div></article>; })}</div> : <div className="dr-no-experts">No matching profiles in this sample directory. Choose another risk or add experts through the contact workflow.</div>}
    <p className="dr-demo-note">{sharedDemo ? "Links can open on another device through the public demo URL. No messages are sent automatically." : "Demo links work in this browser only. Live delivery requires server-issued invitations."}</p><div className="dr-roster-footer"><span role="status">{message || "Each expert receives a separate questionnaire. The current ACAPS rating stays hidden from them."}</span><button className="dc-primary" disabled={!ready} onClick={onContinue}>Continue to responses <ArrowRight size={17}/></button></div>{profile && <Profile expert={profile} onClose={() => setProfile(null)}/>}</section>;
}




