"use client";

import { useState } from "react";
import { fetchApi } from "@/lib/api";
import StandDetails from "@/components/stand/StandDetails";

function run(v:unknown){
  const h=Number(v??0);
  if(!Number.isFinite(h)||h<=0)return"0 h";
  const d=Math.floor(h/24),r=Math.floor(h%24);
  return d?`${d}d ${r}h`:`${Math.floor(h)} h`;
}
function date(v:unknown){
  if(!v)return"—";
  const d=new Date(String(v));
  return Number.isNaN(d.getTime())?"—":d.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"2-digit"});
}

export default function LineStatusGrid({lines}:{lines:any[]}){
  const[selected,setSelected]=useState<any>(null);
  const[error,setError]=useState("");
  if(!lines?.length)return <div className="text-slate-400 text-sm">No running lines mapped.</div>;
  async function open(s:any){if(!s?.id)return;try{setError("");setSelected(await fetchApi(`/stands/${s.id}`))}catch(e:any){setError(e.message||"Could not load stand")}}
  return <>
    {error&&<div className="mb-3 rounded-lg border border-red-900 bg-red-950/20 p-3 text-sm text-red-300">{error}</div>}
    <div className="grid gap-4">
      {lines.map(line=><section key={line.id} className="mechanical-panel overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <div className="flex items-center gap-2"><span className="status-dot bg-emerald-400"/><span className="text-base font-semibold text-white">{line.name}</span><span className="text-xs text-slate-400">Running line</span></div>
          <span className="text-xs text-slate-400">10 positions</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 md:grid-cols-10 divide-x divide-y md:divide-y-0 divide-slate-800">
          {line.positions?.map((p:any)=>{
            const s=p.current_stand;const life=s?.life_percent;
            return <button key={p.id} disabled={!s} onClick={()=>open(s)} className="min-w-0 text-left p-3 bg-[#111418] hover:bg-[#171b20] disabled:opacity-40 transition-colors">
              <div className="flex justify-between items-center gap-2"><span className="text-xs font-semibold text-slate-400">P{p.position_number}</span>{life!=null&&<span className={`status-dot ${life>=90?"bg-rose-400":life>=75?"bg-amber-400":"bg-emerald-400"}`}/>}</div>
              <div className="text-lg font-semibold text-white mt-2 truncate">{s?.code||"—"}</div>
              <div className="mt-2 space-y-1 text-xs text-slate-400">
                <div className="truncate"><span className="text-slate-500">Installed </span>{date(s?.installed_at)}</div>
                <div className="truncate"><span className="text-slate-500">Running </span>{run(s?.campaign_hours)}</div>
                {life!=null&&<div className={life>=90?"text-rose-300":life>=75?"text-amber-300":"text-emerald-300"}><span className="text-slate-500">Life </span>{life}%</div>}
              </div>
            </button>
          })}
        </div>
      </section>)}
    </div>
    {selected&&<div className="fixed inset-0 z-[70] bg-black/65 flex items-end md:items-center justify-center md:p-5" onClick={()=>setSelected(null)}><div className="w-full md:max-w-4xl max-h-[92vh] overflow-auto rounded-t-xl md:rounded-xl bg-[#0f1318] border border-slate-700 p-4" onClick={e=>e.stopPropagation()}><div className="flex justify-end mb-3"><button onClick={()=>setSelected(null)} className="text-sm border border-slate-700 px-3 py-1.5 rounded-md text-slate-200">Close</button></div><StandDetails stand={selected}/></div></div>}
  </>;
}
