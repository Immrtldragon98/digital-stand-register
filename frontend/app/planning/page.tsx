"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";
import { getUser } from "@/lib/auth";

type Row={line:string;position_id:number;position:number;stand:string|null;installed_at:string|null;running_hours:number|null;target_life_hours:number|null;life_percent:number|null;historical_avg_days:number|null;historical_campaigns:number;ready_count:number;risk:string};

const riskClass=(risk:string)=>risk==="CRITICAL"?"text-red-300 bg-red-950/40 border-red-800":risk==="HIGH"?"text-orange-300 bg-orange-950/30 border-orange-800":risk==="WATCH"?"text-amber-300 bg-amber-950/30 border-amber-800":risk==="LOW"?"text-emerald-300 bg-emerald-950/30 border-emerald-800":"text-slate-400 bg-slate-900 border-slate-700";
const lifeText=(h:number|null)=>h==null?"—":`${Math.floor(h/24)}d ${Math.floor(h%24)}h`;
const lineLabel=(line:string)=>line==="W1"?"WRM1":line==="W2"?"WRM2":"WRM3";

export default function PlanningPage(){
  const [rows,setRows]=useState<Row[]>([]);const [error,setError]=useState("");const [loading,setLoading]=useState(true);const [saving,setSaving]=useState<number|null>(null);const [line,setLine]=useState("W1");const user=getUser();
  const load=async()=>{setLoading(true);try{setError("");setRows(await fetchApi("/planning/summary"));}catch(e:any){setError(e.message);}finally{setLoading(false)}};
  useEffect(()=>{load()},[]);
  const lineRows=useMemo(()=>rows.filter(r=>r.line===line).sort((a,b)=>a.position-b.position),[rows,line]);
  const priorities=useMemo(()=>lineRows.filter(r=>["CRITICAL","HIGH","WATCH"].includes(r.risk)).sort((a,b)=>(b.life_percent||0)-(a.life_percent||0)),[lineRows]);
  async function setTarget(row:Row){const raw=window.prompt(`Target life hours for ${lineLabel(row.line)} P${row.position}`,row.target_life_hours?String(row.target_life_hours):"");if(raw===null)return;const value=Number(raw);if(!Number.isFinite(value)||value<=0)return;setSaving(row.position_id);try{await fetchApi(`/planning/positions/${row.position_id}/target`,{method:"PATCH",body:JSON.stringify({target_life_hours:value})});await load();}catch(e:any){setError(e.message);}finally{setSaving(null)}}
  const metricRows=[
    {label:"Running stand",render:(r:Row)=><span className="font-bold text-white">{r.stand||"—"}</span>},
    {label:"Running life",render:(r:Row)=>lifeText(r.running_hours)},
    {label:"Target life",render:(r:Row)=><>{r.target_life_hours!=null?`${r.target_life_hours} h`:<span className="text-slate-600">Not set</span>}{user&&<button disabled={saving===r.position_id} onClick={()=>setTarget(r)} className="ml-1 text-blue-400 hover:text-blue-300">Edit</button>}</>},
    {label:"Life %",render:(r:Row)=>r.life_percent!=null?`${r.life_percent}%`:"—"},
    {label:"Historical avg",render:(r:Row)=>r.historical_avg_days!=null?`${r.historical_avg_days} d`:"—"},
    {label:"Ready",render:(r:Row)=><span className="font-bold">{r.ready_count}</span>},
    {label:"Risk",render:(r:Row)=><span className={`rounded border px-2 py-1 text-[10px] ${riskClass(r.risk)}`}>{r.risk.replace("_"," ")}</span>},
  ];
  return <div className="flex-1 min-h-screen bg-industrial-dark text-slate-100"><Header title="Planning"/><main className="p-4 md:p-5 space-y-4">
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div><h1 className="text-xl font-black text-white">Stand Life Planning</h1><p className="text-xs text-slate-400 mt-1">Running life, target, replacement readiness and risk — one line at a time.</p></div>
        <div className="flex items-center gap-2"><div className="flex rounded-lg border border-slate-700 bg-slate-950 p-1">{["W1","W2","W3"].map(x=><button key={x} onClick={()=>setLine(x)} className={`rounded px-4 py-2 text-xs font-bold ${line===x?"bg-blue-600 text-white":"text-slate-400 hover:text-white"}`}>{lineLabel(x)}</button>)}</div><button onClick={load} className="rounded border border-blue-800 px-3 py-2 text-xs text-blue-300">Refresh</button></div>
      </div>
    </section>
    {error&&<div className="rounded border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}
    {priorities.length>0&&<section className="rounded-xl border border-amber-900/70 bg-amber-950/10 p-3"><div className="flex flex-wrap items-center gap-2"><span className="text-xs font-bold text-amber-200">Attention:</span>{priorities.slice(0,5).map(r=><span key={`${r.line}-${r.position}`} className="rounded border border-slate-700 bg-slate-950/40 px-2 py-1 text-xs">P{r.position} · {r.stand||"—"} · <span className={r.risk==="CRITICAL"?"text-red-300":"text-amber-300"}>{r.risk}</span></span>)}</div></section>}
    <section className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/30">
      <table className="w-full min-w-[1050px] text-xs">
        <thead className="bg-slate-900 text-slate-400"><tr><th className="sticky left-0 z-10 bg-slate-900 p-3 text-left min-w-[130px]">{lineLabel(line)}</th>{Array.from({length:10},(_,i)=><th key={i+1} className="p-3 text-center min-w-[88px]">P{i+1}</th>)}</tr></thead>
        <tbody>{loading?<tr><td colSpan={11} className="p-5 text-center text-slate-500">Loading...</td></tr>:metricRows.map((m,idx)=><tr key={m.label} className="border-t border-slate-800"><td className="sticky left-0 z-10 bg-slate-950 p-3 font-semibold text-slate-400">{m.label}</td>{Array.from({length:10},(_,i)=>{const r=lineRows.find(x=>x.position===i+1);return <td key={i+1} className={`p-3 text-center ${idx===0?"bg-slate-900/20":""}`}>{r?m.render(r):"—"}</td>})}</tr>)}</tbody>
      </table>
    </section>
    <p className="text-[11px] text-slate-500">Historical average is supporting context only. Engineer-set target remains the planning reference.</p>
  </main></div>;
}
