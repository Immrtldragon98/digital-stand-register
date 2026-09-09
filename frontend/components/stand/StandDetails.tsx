"use client";

import { useState } from "react";
import { Activity, Clock, Droplets, Gauge, Layers, MapPin } from "lucide-react";

export default function StandDetails({ stand }: { stand: any }) {
  const [tab,setTab]=useState<"overview"|"components"|"history">("overview");
  if (!stand) return null;
  const guide = stand.entry_guide;
  const prep = stand.component_preparation;

  return <div className="bg-industrial-card border border-industrial-border rounded-xl p-4 md:p-5 shadow-xl">
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-industrial-border">
      <div><h2 className="text-lg font-bold text-white flex items-center gap-2"><Layers className="w-5 h-5 text-industrial-accent" />Stand {stand.code}</h2><p className="text-xs text-slate-400 mt-1">Running condition and preparation details</p></div>
      <span className="px-3 py-1 bg-green-950/50 text-green-400 border border-green-800 rounded-full text-xs font-semibold">{pretty(stand.current_status)}</span>
    </div>

    <div className="flex gap-1 rounded-lg border border-slate-800 bg-slate-950/60 p-1 mb-4 w-fit">
      {[['overview','Overview'],['components','Components'],['history','History']].map(([key,label])=><button key={key} onClick={()=>setTab(key as any)} className={`px-3 py-1.5 rounded text-xs font-semibold ${tab===key?'bg-blue-600 text-white':'text-slate-400 hover:text-white'}`}>{label}</button>)}
    </div>

    {tab==="overview"&&<>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <Info icon={<Clock />} label="Total Stand Life" value={`${stand.lifetime_hours ?? 0} h`} />
        <Info icon={<Clock />} label="Current Campaign" value={`${stand.current_campaign_hours ?? 0} h`} />
        <Info icon={<MapPin />} label="Position" value={stand.position_number ? `P${stand.position_number}` : "Spare"} />
        <Info icon={<Droplets />} label="Leakage" value={stand.leakage ? "YES" : "No"} warn={stand.leakage} />
        <Info icon={<Activity />} label="Vibration" value={stand.vibration ? "YES" : "No"} warn={stand.vibration} />
        <Info icon={<Gauge />} label="Entry Guide" value={guide ? guide.code : "Not fitted"} />
        <Info icon={<Gauge />} label="Guide Condition" value={guide?.condition ? pretty(guide.condition) : "—"} />
        <Info icon={<Clock />} label="Guide Life" value={guide ? `${guide.lifetime_hours} h` : "—"} />
      </div>
      {stand.condition_notes&&<div className="mt-4 border border-industrial-border bg-industrial-dark rounded-lg p-3 text-sm text-slate-300"><span className="text-slate-500">Latest condition note:</span> {stand.condition_notes}</div>}
    </>}

    {tab==="components"&&<div>
      {!prep?<Empty text="No component preparation was recorded for this stand yet."/>:prep.state==="SKIPPED"?<div className="rounded-lg border border-amber-800/60 bg-amber-950/20 p-3 text-sm text-amber-200">Components were skipped before gauging for this preparation cycle.</div>:<>
        <div className="mb-3 text-xs text-slate-400">Prepared by <b className="text-slate-200">{prep.prepared_by||"—"}</b>{prep.notes?` · ${prep.notes}`:""}</div>
        <div className="overflow-x-auto rounded-lg border border-slate-800"><table className="w-full min-w-[900px] text-xs"><thead className="bg-slate-900 text-slate-400"><tr><th className="p-2 text-left">Component</th><th>New</th><th>Reused</th><th>Running</th><th>Total Life</th><th>Expected</th><th>Life Used</th><th>Status</th><th>Criticality</th></tr></thead><tbody>{prep.items?.map((x:any,i:number)=>{const pct=lifePercent(x.estimated_total_life_hours,x.expected_life_hours);const health=healthLabel(pct);return <tr key={i} className="border-t border-slate-800"><td className="p-2 font-semibold text-white">{x.name}</td><td className="text-center">{x.new_qty}</td><td className="text-center">{x.reused_qty}</td><td className="text-center">{fmtHours(x.current_campaign_hours)}</td><td className="text-center">{fmtHours(x.estimated_total_life_hours)}</td><td className="text-center">{x.expected_life_hours?fmtHours(x.expected_life_hours):"—"}</td><td className="text-center">{pct===null?"—":`${pct}%`}</td><td className={`text-center font-bold ${healthClass(health)}`}>{health}</td><td className="text-center">{x.criticality||"—"}</td></tr>})}</tbody></table></div>
        <p className="mt-2 text-[10px] text-slate-500">Total life = previous reused life + current stand campaign. If previous life was not entered, total life shows only the current campaign. Expected life and criticality stay blank until engineering values are configured.</p>
      </>}
    </div>}

    {tab==="history"&&<div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <HistoryPanel title="Preparation History">{stand.preparation_history?.length ? stand.preparation_history.map((h:any,i:number)=><HistoryItem key={i} title={`${pretty(h.from_status)} → ${pretty(h.to_status)} • ${dateTime(h.changed_at)}`} detail={`Updated by: ${h.updated_by||"—"} • Remarks: ${h.remarks||"—"}`}/>) : <Empty text="No preparation status history recorded yet."/>}</HistoryPanel>
      <HistoryPanel title="Stand Life History">{stand.history?.length ? stand.history.map((h:any,i:number)=><HistoryItem key={i} title={`${dateTime(h.installed_at)} → ${h.removed_at?dateTime(h.removed_at):"Running"}`} detail={`Campaign: ${h.campaign_hours ?? stand.current_campaign_hours ?? 0} h • Installed by: ${h.installed_by||"—"} • Removed by: ${h.removed_by||"—"} • Reason: ${h.removal_reason||"—"}`}/>) : <Empty text="No stand history recorded yet."/>}</HistoryPanel>
      <HistoryPanel title="Entry Guide History">{!guide?<Empty text="No entry guide fitted."/>:<>{guide.history?.length?guide.history.map((h:any,i:number)=><HistoryItem key={i} title={`${dateTime(h.installed_at)} → ${h.removed_at?dateTime(h.removed_at):"Running"}`} detail={`Campaign: ${h.campaign_hours ?? guide.current_campaign_hours ?? 0} h • Removal reason: ${h.removal_reason||"—"}`}/>):<Empty text="No entry guide history recorded yet."/>}</>}</HistoryPanel>
    </div>}
  </div>;
}

function pretty(value:string){return value.replaceAll("_"," ").toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());}
function dateTime(value:string){return new Date(value).toLocaleString();}
function fmtHours(v:any){const n=Number(v);return Number.isFinite(n)?`${n.toFixed(n<10?1:0)} h`:"—";}
function lifePercent(total:any,expected:any){const t=Number(total),e=Number(expected);if(!Number.isFinite(t)||!Number.isFinite(e)||e<=0)return null;return Math.round((t/e)*100);}
function healthLabel(pct:number|null){if(pct===null)return "—";if(pct>=100)return "OVER LIFE";if(pct>=90)return "REPLACE SOON";if(pct>=70)return "WATCH";return "GOOD";}
function healthClass(label:string){return label==="OVER LIFE"?"text-red-300":label==="REPLACE SOON"?"text-orange-300":label==="WATCH"?"text-amber-300":label==="GOOD"?"text-emerald-300":"text-slate-500";}
function Info({icon,label,value,warn=false}:{icon:React.ReactNode;label:string;value:any;warn?:boolean}){return <div className="bg-industrial-dark border border-industrial-border rounded-lg p-3"><div className="w-4 h-4 text-slate-500 mb-2">{icon}</div><div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div><div className={`font-semibold mt-1 ${warn?"text-red-400":"text-white"}`}>{value}</div></div>}
function HistoryPanel({title,children}:{title:string;children:React.ReactNode}){return <div><h3 className="text-sm font-semibold text-white mb-3">{title}</h3><div className="space-y-2">{children}</div></div>}
function HistoryItem({title,detail}:{title:string;detail:string}){return <div className="border border-industrial-border rounded-lg p-3 text-xs text-slate-300"><div>{title}</div><div className="text-slate-500 mt-1 leading-relaxed">{detail}</div></div>}
function Empty({text}:{text:string}){return <div className="text-xs text-slate-500">{text}</div>}
