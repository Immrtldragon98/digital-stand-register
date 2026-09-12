"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Clock, Droplets, Gauge, Layers, MapPin, Plus, Volume2 } from "lucide-react";
import { fetchApi } from "@/lib/api";
import { getUser } from "@/lib/auth";

type EventRow={id:number;category:string;event_type:string;severity:string;component_name?:string|null;duration_minutes?:number|null;description?:string|null;action_taken?:string|null;event_at:string;recorded_by:string};

export default function StandDetails({ stand }: { stand: any }) {
  const [tab,setTab]=useState<"overview"|"components"|"events"|"history">("overview");
  const [events,setEvents]=useState<EventRow[]>([]);
  const [loadingEvents,setLoadingEvents]=useState(false);
  const [showEventForm,setShowEventForm]=useState(false);
  const [savingEvent,setSavingEvent]=useState(false);
  const [savingCondition,setSavingCondition]=useState(false);
  const [eventError,setEventError]=useState("");
  const [condition,setCondition]=useState({leakage:!!stand?.leakage,vibration:!!stand?.vibration,abnormal_sound:!!stand?.abnormal_sound});
  const [eventForm,setEventForm]=useState({category:"OBSERVATION",event_type:"",severity:"LOW",component_name:"",duration_minutes:"",description:"",action_taken:""});
  const user=getUser();
  if (!stand) return null;
  const guide = stand.entry_guide;
  const prep = stand.component_preparation;

  async function loadEvents(){setLoadingEvents(true);try{setEvents(await fetchApi(`/stand-events/stand/${stand.id}`));}catch(e:any){setEventError(e.message||"Could not load events");}finally{setLoadingEvents(false)}}
  useEffect(()=>{loadEvents()},[stand.id]);
  const campaignEvents=useMemo(()=>events.filter(e=>!stand.current_installed_at||new Date(e.event_at)>=new Date(stand.current_installed_at)),[events,stand.current_installed_at]);

  async function toggleCondition(key:"leakage"|"vibration"|"abnormal_sound"){
    if(!user||savingCondition)return;
    const next=!condition[key];
    const note=next?window.prompt(`Short note for ${key.replaceAll("_"," ")} (optional)`)?.trim()||null:null;
    setSavingCondition(true);setEventError("");
    try{
      const result=await fetchApi(`/stands/${stand.id}/condition`,{method:"PATCH",body:JSON.stringify({[key]:next,notes:note})});
      setCondition({leakage:!!result.leakage,vibration:!!result.vibration,abnormal_sound:!!result.abnormal_sound});
      await loadEvents();
    }catch(e:any){setEventError(e.message||"Could not update condition");}finally{setSavingCondition(false)}
  }

  async function saveEvent(e:React.FormEvent){e.preventDefault();if(!eventForm.event_type.trim())return;setSavingEvent(true);setEventError("");try{await fetchApi(`/stand-events/stand/${stand.id}`,{method:"POST",body:JSON.stringify({category:eventForm.category,event_type:eventForm.event_type.trim(),severity:eventForm.severity,component_name:eventForm.component_name.trim()||null,duration_minutes:eventForm.duration_minutes?Number(eventForm.duration_minutes):null,description:eventForm.description.trim()||null,action_taken:eventForm.action_taken.trim()||null})});setEventForm({category:"OBSERVATION",event_type:"",severity:"LOW",component_name:"",duration_minutes:"",description:"",action_taken:""});setShowEventForm(false);await loadEvents();}catch(err:any){setEventError(err.message||"Could not save event");}finally{setSavingEvent(false)}}

  const attention=condition.leakage||condition.vibration||condition.abnormal_sound;
  return <div className="mechanical-panel p-4 md:p-5">
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
      <div><h2 className="text-lg font-bold text-white flex items-center gap-2"><Layers className="w-5 h-5 text-sky-400" />Stand {stand.code}</h2><p className="text-xs text-slate-300 mt-1">Running condition, components, events and life history</p></div>
      <span className={`px-3 py-1 rounded-full border text-xs font-semibold ${attention?"bg-rose-950/40 text-rose-300 border-rose-800":"bg-emerald-950/40 text-emerald-300 border-emerald-800"}`}>{attention?"Needs attention":"Running normal"}</span>
    </div>

    <div className="flex gap-1 rounded-lg border border-slate-800 bg-slate-950/60 p-1 mb-4 w-fit max-w-full overflow-x-auto">
      {[['overview','Overview'],['components','Components'],['events','Events'],['history','History']].map(([key,label])=><button key={key} onClick={()=>setTab(key as any)} className={`px-3 py-2 rounded text-xs font-semibold whitespace-nowrap ${tab===key?'bg-blue-600 text-white':'text-slate-300 hover:text-white'}`}>{label}</button>)}
    </div>

    {eventError&&<div className="mb-3 rounded-lg border border-red-900 bg-red-950/25 p-3 text-xs text-red-300">{eventError}</div>}

    {tab==="overview"&&<>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <Info icon={<Clock />} label="Installed" value={stand.current_installed_at?shortDate(stand.current_installed_at):"—"} />
        <Info icon={<Clock />} label="Current Campaign" value={fmtHours(stand.current_campaign_hours)} />
        <Info icon={<Clock />} label="Total Stand Life" value={fmtHours(stand.lifetime_hours)} />
        <Info icon={<MapPin />} label="Position" value={stand.position_number ? `P${stand.position_number}` : "Spare"} />
        <Info icon={<Droplets />} label="Leakage" value={condition.leakage ? "YES" : "No"} warn={condition.leakage} />
        <Info icon={<Activity />} label="Vibration" value={condition.vibration ? "YES" : "No"} warn={condition.vibration} />
        <Info icon={<Volume2 />} label="Abnormal Sound" value={condition.abnormal_sound ? "YES" : "No"} warn={condition.abnormal_sound} />
        <Info icon={<Gauge />} label="Entry Guide" value={guide ? guide.code : "Not fitted"} />
      </div>
      {user&&stand.current_status==="INSTALLED"&&<div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/35 p-3"><div className="text-sm font-semibold text-white">Quick running condition</div><div className="mt-1 text-xs text-slate-400">Tap a condition when observed. Tap again after it is cleared. Each change is kept in the campaign event history.</div><div className="mt-3 flex flex-wrap gap-2"><ConditionButton label="Leakage" active={condition.leakage} onClick={()=>toggleCondition("leakage")} disabled={savingCondition}/><ConditionButton label="Vibration" active={condition.vibration} onClick={()=>toggleCondition("vibration")} disabled={savingCondition}/><ConditionButton label="Abnormal sound" active={condition.abnormal_sound} onClick={()=>toggleCondition("abnormal_sound")} disabled={savingCondition}/></div></div>}
      {stand.condition_notes&&<div className="mt-4 border border-slate-800 bg-slate-950/40 rounded-lg p-3 text-sm text-slate-300"><span className="text-slate-400">Latest condition note:</span> {stand.condition_notes}</div>}
    </>}

    {tab==="components"&&<div>
      {!prep?<Empty text="No component preparation was recorded for this stand yet."/>:prep.state==="SKIPPED"?<div className="rounded-lg border border-amber-800/60 bg-amber-950/20 p-3 text-sm text-amber-200">Components were skipped before gauging for this preparation cycle.</div>:<>
        <div className="mb-3 text-xs text-slate-300">Prepared by <b className="text-white">{prep.prepared_by||"—"}</b>{prep.notes ? ` · ${prep.notes}` : ""}</div>
        <div className="overflow-x-auto rounded-lg border border-slate-800"><table className="w-full min-w-[900px] text-xs"><thead className="bg-slate-900 text-slate-300"><tr><th className="p-2 text-left">Component</th><th>New</th><th>Reused</th><th>Running</th><th>Total Life</th><th>Expected</th><th>Life Used</th><th>Status</th><th>Criticality</th></tr></thead><tbody>{prep.items?.map((x:any,i:number)=>{const pct=lifePercent(x.estimated_total_life_hours,x.expected_life_hours);const health=healthLabel(pct);return <tr key={i} className="border-t border-slate-800"><td className="p-2 font-semibold text-white">{x.name}</td><td className="text-center">{x.new_qty}</td><td className="text-center">{x.reused_qty}</td><td className="text-center">{fmtHours(x.current_campaign_hours)}</td><td className="text-center">{fmtHours(x.estimated_total_life_hours)}</td><td className="text-center">{x.expected_life_hours?fmtHours(x.expected_life_hours):"—"}</td><td className="text-center">{pct===null?"—":`${pct}%`}</td><td className={`text-center font-bold ${healthClass(health)}`}>{health}</td><td className="text-center">{x.criticality||"—"}</td></tr>})}</tbody></table></div>
        <p className="mt-2 text-[11px] text-slate-400">Total life = previous reused life + current campaign. Expected life remains an engineering target, not an AI guess.</p>
      </>}
    </div>}

    {tab==="events"&&<div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"><div><h3 className="text-sm font-semibold text-white">Running Campaign Events</h3><p className="text-xs text-slate-400 mt-1">Breakdowns, observations, quality issues and component events for this run.</p></div>{user&&stand.current_status==="INSTALLED"&&<button onClick={()=>setShowEventForm(v=>!v)} className="dsr-btn-primary"><Plus className="w-4 h-4"/>{showEventForm?"Close":"Log Event"}</button>}</div>
      {showEventForm&&<form onSubmit={saveEvent} className="rounded-xl border border-slate-800 bg-slate-950/35 p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"><Field label="Category"><select className="input-class" value={eventForm.category} onChange={e=>setEventForm({...eventForm,category:e.target.value})}><option>OBSERVATION</option><option>BREAKDOWN</option><option>COMPONENT</option><option>QUALITY</option><option>MAINTENANCE</option></select></Field><Field label="Event"><input className="input-class" value={eventForm.event_type} onChange={e=>setEventForm({...eventForm,event_type:e.target.value})} placeholder="Internal leakage / bearing / sound..." required/></Field><Field label="Severity"><select className="input-class" value={eventForm.severity} onChange={e=>setEventForm({...eventForm,severity:e.target.value})}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>STOPPAGE</option></select></Field><Field label="Component"><input className="input-class" value={eventForm.component_name} onChange={e=>setEventForm({...eventForm,component_name:e.target.value})} placeholder="Optional"/></Field><Field label="Downtime min"><input className="input-class" type="number" min="0" value={eventForm.duration_minutes} onChange={e=>setEventForm({...eventForm,duration_minutes:e.target.value})}/></Field><div className="sm:col-span-2 lg:col-span-3"><Field label="Description"><input className="input-class" value={eventForm.description} onChange={e=>setEventForm({...eventForm,description:e.target.value})} placeholder="What was observed?"/></Field></div><div className="sm:col-span-2 lg:col-span-3"><Field label="Action taken"><input className="input-class" value={eventForm.action_taken} onChange={e=>setEventForm({...eventForm,action_taken:e.target.value})} placeholder="Inspection / adjusted / continued running..."/></Field></div><div className="flex items-end"><button disabled={savingEvent} className="dsr-btn-primary w-full">{savingEvent?"Saving...":"Save Event"}</button></div></form>}
      {loadingEvents?<div className="dsr-empty">Loading events...</div>:campaignEvents.length?<div className="space-y-2">{campaignEvents.map(e=><div key={e.id} className="rounded-lg border border-slate-800 bg-slate-950/35 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2"><span className={`rounded border px-2 py-1 text-[10px] font-bold ${severityClass(e.severity)}`}>{e.severity}</span><span className="text-sm font-semibold text-white">{pretty(e.event_type)}</span>{e.component_name&&<span className="text-xs text-sky-300">· {e.component_name}</span>}</div><span className="text-xs text-slate-400">{dateTime(e.event_at)}</span></div><div className="mt-2 text-xs text-slate-400">{e.category.replaceAll('_',' ')}{e.duration_minutes!=null?` · ${e.duration_minutes} min`:""} · {e.recorded_by}</div>{e.description&&<div className="mt-2 text-sm text-slate-300">{e.description}</div>}{e.action_taken&&<div className="mt-1 text-xs text-emerald-300">Action: {e.action_taken}</div>}</div>)}</div>:<Empty text="No events recorded in this running campaign."/>}
    </div>}

    {tab==="history"&&<div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <HistoryPanel title="Preparation History">{stand.preparation_history?.length ? stand.preparation_history.map((h:any,i:number)=><HistoryItem key={i} title={`${pretty(h.from_status)} → ${pretty(h.to_status)} • ${dateTime(h.changed_at)}`} detail={`Updated by: ${h.updated_by||"—"} • ${h.remarks||"No remarks"}`}/>) : <Empty text="No preparation status history recorded yet."/>}</HistoryPanel>
      <HistoryPanel title="Stand Life History">{stand.history?.length ? stand.history.map((h:any,i:number)=><HistoryItem key={i} title={`${dateTime(h.installed_at)} → ${h.removed_at?dateTime(h.removed_at):"Running"}`} detail={`Campaign: ${h.campaign_hours ?? stand.current_campaign_hours ?? 0} h • Removed by: ${h.removed_by||"—"} • Reason: ${h.removal_reason||"—"}`}/>) : <Empty text="No stand history recorded yet."/>}</HistoryPanel>
      <HistoryPanel title="Entry Guide History">{!guide?<Empty text="No entry guide fitted."/>:<>{guide.history?.length?guide.history.map((h:any,i:number)=><HistoryItem key={i} title={`${dateTime(h.installed_at)} → ${h.removed_at?dateTime(h.removed_at):"Running"}`} detail={`Campaign: ${h.campaign_hours ?? guide.current_campaign_hours ?? 0} h • Removal reason: ${h.removal_reason||"—"}`}/>):<Empty text="No entry guide history recorded yet."/>}</>}</HistoryPanel>
    </div>}
  </div>;
}

function pretty(value:string){return (value||"").replaceAll("_"," ").toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());}
function dateTime(value:string){return new Date(value).toLocaleString();}
function shortDate(value:string){return new Date(value).toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"2-digit"});}
function fmtHours(v:any){const n=Number(v);return Number.isFinite(n)?`${n.toFixed(n<10?1:0)} h`:"—";}
function lifePercent(total:any,expected:any){const t=Number(total),e=Number(expected);if(!Number.isFinite(t)||!Number.isFinite(e)||e<=0)return null;return Math.round((t/e)*100);}
function healthLabel(pct:number|null){if(pct===null)return "—";if(pct>=100)return "OVER LIFE";if(pct>=90)return "REPLACE SOON";if(pct>=70)return "WATCH";return "GOOD";}
function healthClass(label:string){return label==="OVER LIFE"?"text-red-300":label==="REPLACE SOON"?"text-orange-300":label==="WATCH"?"text-amber-300":label==="GOOD"?"text-emerald-300":"text-slate-400";}
function severityClass(v:string){return v==="STOPPAGE"?"border-red-700 bg-red-950/40 text-red-300":v==="HIGH"?"border-orange-700 bg-orange-950/35 text-orange-300":v==="MEDIUM"?"border-amber-700 bg-amber-950/25 text-amber-300":"border-slate-700 bg-slate-900 text-slate-300";}
function Info({icon,label,value,warn=false}:{icon:React.ReactNode;label:string;value:any;warn?:boolean}){return <div className="bg-slate-950/35 border border-slate-800 rounded-lg p-3"><div className="w-4 h-4 text-slate-400 mb-2">{icon}</div><div className="text-[11px] font-medium text-slate-400">{label}</div><div className={`font-semibold mt-1 ${warn?"text-rose-300":"text-white"}`}>{value}</div></div>}
function ConditionButton({label,active,onClick,disabled}:{label:string;active:boolean;onClick:()=>void;disabled:boolean}){return <button disabled={disabled} onClick={onClick} className={`min-h-[44px] rounded-lg border px-4 py-2 text-sm font-semibold ${active?"border-rose-700 bg-rose-950/35 text-rose-200":"border-slate-700 bg-slate-900/60 text-slate-200 hover:border-slate-500"}`}>{active?"● ":"○ "}{label}</button>}
function HistoryPanel({title,children}:{title:string;children:React.ReactNode}){return <div><h3 className="text-sm font-semibold text-white mb-3">{title}</h3><div className="space-y-2">{children}</div></div>}
function HistoryItem({title,detail}:{title:string;detail:string}){return <div className="border border-slate-800 rounded-lg p-3 text-xs text-slate-300"><div>{title}</div><div className="text-slate-400 mt-1 leading-relaxed">{detail}</div></div>}
function Field({label,children}:{label:string;children:React.ReactNode}){return <label className="block"><span className="metric-label">{label}</span><div className="mt-1.5">{children}</div></label>}
function Empty({text}:{text:string}){return <div className="dsr-empty">{text}</div>}
