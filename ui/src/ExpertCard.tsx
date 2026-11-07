import { useEffect, useState, type FormEvent } from "react";
import { Check, ChevronDown, LockKeyhole } from "lucide-react";
import { getCard, prepareAnswer, sealAnswer, mock, type Answer, type Card, type Mask, type PendingAnswer, type CommitmentReceipt } from "./api";
import { endpoint } from "./service";
import "./expert34.css";

const words = [
  {id:"very_unlikely",label:"Very unlikely",range:"Under 10%"},
  {id:"unlikely",label:"Unlikely",range:"10–35%"},
  {id:"even",label:"Even chance",range:"35–65%"},
  {id:"likely",label:"Likely",range:"65–90%"},
  {id:"very_likely",label:"Very likely",range:"Over 90%"},
];
const masks: {id:Mask;label:string}[] = [{id:"known",label:"Named to ACAPS"},{id:"pseudonym",label:"Nickname to peers"},{id:"anonymous",label:"No identity kept"}];
type Saved = { answer: Answer; receipt: CommitmentReceipt; versions: {answer:Answer;receipt:CommitmentReceipt}[] };
function readSaved(token:string): Saved|null { try { return JSON.parse(sessionStorage.getItem(`ss-expert34-${token}`)||"null"); } catch { return null; } }
export function ExpertCard({token}:{token:string}) {
  const [card,setCard]=useState<Card|null>(null),[error,setError]=useState(""),[reload,setReload]=useState(0),[busy,setBusy]=useState(false);
  const [word,setWord]=useState<string|null>(null),[exact,setExact]=useState(""),[stance,setStance]=useState<Answer["stance"]>("estimate"),[mask,setMask]=useState<Mask|null>(null);
  const [confidence,setConfidence]=useState(""),[source,setSource]=useState<Answer["source_tag"]>(null),[note,setNote]=useState(""),[against,setAgainst]=useState(""),[trigger,setTrigger]=useState(""),[changed,setChanged]=useState("");
  const [saved,setSaved]=useState<Saved|null>(()=>mock?readSaved(token):null),[editing,setEditing]=useState(false),[pending,setPending]=useState<{draft:PendingAnswer;answer:Answer}|null>(null);
  const [now,setNow]=useState(Date.now());
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[]);
  useEffect(()=>{let active=true;setError("");getCard(token).then(value=>{if(active)setCard(value);}).catch(e=>{if(active)setError(e.message);});document.title="Expert question | Sealed Signals";return()=>{active=false;};},[token,reload]);
  const deadline=card?.correction_allowed_until||card?.pulse.expires_at;
  const closed=!!deadline && Number.isFinite(Date.parse(deadline)) && now>=Date.parse(deadline);
  const round=card?.round||1;
  const group=card?.group_view_if_round2;
  async function submit(event:FormEvent) {
    event.preventDefault();setError("");
    if(closed){setError("This response window has closed.");return;}
    if(!mask){setError("Choose how your answer is shared.");return;}
    if(stance==="estimate"&&!word&&exact===""){setError("Choose a likelihood or enter an exact percentage.");return;}
    if(exact!==""&&(!Number.isFinite(Number(exact))||Number(exact)<0||Number(exact)>100)){setError("Enter a percentage between 0 and 100.");return;}
    const answer:Answer={mask,stance,likelihood_word:stance==="estimate"&&exact===""?word:null,probability:stance==="estimate"&&exact!==""?Number(exact)/100:null,confidence:confidence?Number(confidence):null,source_tag:source,missing:note.trim(),against:against.trim(),trigger_pick:trigger||null,panel_share_yes:null,round,changed_mind:round===2&&changed==="revise"};
    setBusy(true);
    try{ const draft=editing?{confirm_token:"correction",summary:`Replace your previous answer with ${stance==="estimate"?exact!==""?`${exact}%`:words.find(w=>w.id===word)?.label:stance.replaceAll("_"," ")}. Previous versions are retained.`,committed:false,message:"",served_from:"live",generated_at:new Date().toISOString()}:await prepareAnswer(token,answer);if(!draft.confirm_token)throw new Error("The API did not return a confirmation token. Your answer has not been confirmed.");setPending({draft,answer}); }
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  async function confirm() {
    if(!pending||closed)return;setBusy(true);setError("");
    try{
      const receipt=editing&&!mock?await endpoint.correctAnswer(token,pending.answer):await sealAnswer(token,pending.draft.confirm_token);
      if(!receipt.commitment||!Number.isFinite(Date.parse(receipt.committed_at)))throw new Error("The API did not confirm a commitment. Your inputs are kept here.");
      const next:Saved={answer:pending.answer,receipt:{...receipt,version:(saved?.receipt.version||0)+1},versions:saved?[...saved.versions,{answer:saved.answer,receipt:saved.receipt}]:[]};
      if(mock)sessionStorage.setItem(`ss-expert34-${token}`,JSON.stringify(next));setSaved(next);setPending(null);setEditing(false);
    }catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  function edit() {if(!saved)return;setWord(saved.answer.likelihood_word||null);setExact(saved.answer.probability===null?"":String(saved.answer.probability*100));setStance(saved.answer.stance);setMask(saved.answer.mask);setNote(saved.answer.missing);setConfidence(saved.answer.confidence?String(saved.answer.confidence):"");setSource(saved.answer.source_tag);setAgainst(saved.answer.against||"");setTrigger(saved.answer.trigger_pick||"");setEditing(true);}
  return <main className="expert34" id="expert-content">
    {!card?<div role={error?"alert":"status"}><h1>{error?"Could not open this question":"Opening your question…"}</h1>{error&&<><p>{error}</p><button onClick={()=>setReload(r=>r+1)}>Try again</button></>}</div>:
    saved&&!editing?<section className="expert34-thanks" aria-label="Answer confirmed"><Check size={30} aria-hidden="true"/><h1>Thanks. Your answer is confirmed.</h1><p>You’ll hear how the panel saw it after the deadline.</p>{saved.answer.mask==="anonymous"&&<p>No identity is kept with this answer, so no personal feedback will be sent.</p>}<p className="expert34-meta">Version {saved.receipt.version} · {saved.versions.length} previous versions retained</p><button disabled={closed} onClick={edit}>{closed?"Response window closed":"Change my answer"}</button><small>{deadline&&`Corrections until ${new Date(deadline).toLocaleString("en-GB")}`}</small></section>:
    pending?<section aria-label="Confirm your answer"><p className="expert34-from">{card.pulse.asked_by}</p><h1>Confirm your answer</h1><p>{card.pulse.question?.text||card.risk.title}</p><div className="expert34-confirm-summary">{pending.draft.summary}</div><p className="expert34-meta">Nothing is committed until you confirm.</p>{error&&<p role="alert">{error}</p>}<div className="expert34-actions"><button className="primary" disabled={busy||closed} onClick={()=>void confirm()}>{busy?"Confirming…":"Confirm answer"}</button><button disabled={busy} onClick={()=>setPending(null)}>Change my answer</button></div>{closed&&<p role="alert">The response window has closed.</p>}</section>:
    <form onSubmit={submit}>
      <p className="expert34-from">A question from {card.pulse.asked_by||"your ACAPS analyst"}</p>
      <h1>{card.pulse.question?.text||card.risk.title}</h1>
      <p className="expert34-meta">{card.pulse.question?.location||card.risk.country}{deadline&&<> · Respond by <time dateTime={deadline}>{new Date(deadline).toLocaleString("en-GB",{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"})}</time></>}</p>
      {round===2&&group&&group.n>=5&&<section className="expert34-group" aria-label="Panel spread"><h2>How the panel saw it</h2><div className="expert34-distribution">{group.distribution.map(bucket=><div key={bucket.bucket}><span>{Math.round(Number(bucket.bucket.split("-")[0])*100)}–{Math.round(Number(bucket.bucket.split("-")[1])*100)}%</span><span style={{height:`${Math.max(2,bucket.count*12)}px`}}/><strong>{bucket.count}</strong></div>)}</div>{group.disagreement?.map((d,i)=><p key={i}>{d.summary}</p>)}<label>Still your answer?<select value={changed} onChange={e=>setChanged(e.target.value)}><option value="">Choose</option><option value="keep">Keep</option><option value="revise">Revise</option></select></label></section>}
      <fieldset disabled={busy||closed}><legend className="sr-only">Your forecast</legend>
        <div className="expert34-words" role="group" aria-label="Likelihood">{words.map(item=><button type="button" key={item.id} aria-pressed={stance==="estimate"&&word===item.id&&exact===""} onClick={()=>{setWord(item.id);setExact("");setStance("estimate");}}><strong>{item.label}</strong><span>{item.range}</span></button>)}</div>
        <div className="expert34-abstain">{([["outside_my_expertise","Outside my area"],["not_enough_evidence","Not enough evidence"]] as const).map(([value,label])=><button type="button" key={value} aria-pressed={stance===value} onClick={()=>setStance(value)}>{label}</button>)}</div>
        <details className="expert34-optional"><summary>Exact number or add a note <ChevronDown size={14} aria-hidden="true"/></summary>
          <label>Exact likelihood (%)<input type="number" min="0" max="100" step="any" value={exact} onChange={e=>{setExact(e.target.value);setWord(null);setStance("estimate");}}/></label>
          <label>How sure are you? (optional)<select value={confidence} onChange={e=>setConfidence(e.target.value)}><option value="">Not specified</option><option value="1">Not sure</option><option value="3">Fairly sure</option><option value="5">Sure</option></select></label>
          <label>What are we missing?<textarea maxLength={240} value={note} onChange={e=>setNote(e.target.value)}/></label>
          <label>Strongest reason this would NOT happen<textarea maxLength={240} value={against} onChange={e=>setAgainst(e.target.value)}/></label>
          <div role="group" aria-label="Source of your note" className="expert34-source">{(["saw","read","heard"] as const).map(s=><button type="button" key={s} aria-pressed={source===s} onClick={()=>setSource(source===s?null:s)}>{s}</button>)}</div>
          <label>Which trigger would move your view most?<select value={trigger} onChange={e=>setTrigger(e.target.value)}><option value="">Not specified</option>{card.risk.triggers.map(t=><option key={t.id} value={t.id}>{t.title}</option>)}</select></label>
          {round===2&&<label>What changed your mind?<input maxLength={240} value={note} onChange={e=>setNote(e.target.value)}/></label>}
        </details>
        <div className="expert34-masks" role="group" aria-label="How your answer is shared">{masks.map(item=><button type="button" key={item.id} aria-pressed={mask===item.id} onClick={()=>setMask(item.id)}>{item.label}</button>)}</div>
        <p className="expert34-privacy">In a panel of eight, a distinctive reason may identify you to colleagues.{mask==="anonymous"&&" No identity is kept with this answer; you will not receive personal feedback."}</p>
        {error&&<p role="alert">{error}</p>}
        <button className="primary expert34-submit" type="submit">{busy?"Preparing…":editing?"Review correction":"Submit"}<LockKeyhole size={15} aria-hidden="true"/></button>
      </fieldset>
      {closed&&<p role="status">This response window has closed.</p>}
      <details className="expert34-charter"><summary>Who sees what and how to stop</summary><p>Your response helps an ACAPS analyst review this defined question. Peers see no answers before the deadline. The public sees group results only. The server stores committed answers; commitments prove consistency, not truth or secrecy from the operator. No hidden tests or personal rankings.</p><p>You can reply STOP to your analyst at any time. You can correct your answer until the deadline; previous versions are retained. Participation and optional calibration are separate.</p></details>
    </form>}
  </main>;
}
