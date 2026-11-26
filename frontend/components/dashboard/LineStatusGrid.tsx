"use client";

import { useState } from "react";
import { fetchApi } from "@/lib/api";
import { apiDateMs, installationElapsedHours, runtimeHours, runtimeLabel } from "@/lib/runtime-display";
import StandDetails from "@/components/stand/StandDetails";

function date(v:unknown){if(!v)return"—";const d=new Date(apiDateMs(v));return Number.isNaN(d.getTime())?"—":d.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"2-digit"});}
const lineTone={bar:"bg-[#4EA1FF]",badge:"text-slate-100",header:"bg-[#151F2E]"};

export default function LineStatusGrid({lines,asOf=Date.now()}:{lines:any[];asOf?:number}){
  const[selected,setSelected]=useState<any>(null);const[error,setError]=useState("");
  if(!lines?.length)return <div className="text-slate-400 text-sm">No running lines mapped.</div>;
  async function open(s:any){if(!s?.id)return;try{setError("");setSelected(await fetchApi(`/stands/${s.id}`))}catch(e:any){setError(e.message||"Could not load stand")}}
  return <>
    {error&&<div className="mb-3 rounded-lg border border-red-900 bg-red-950/20 p-3 text-sm text-red-300">{error}</div>}
    <div className="grid gap-4">
      {lines.map(line=>{const tone=lineTone;return <section key={line.id} className="mechanical-panel overflow-hidden">
        <div className={`flex items-center justify-between px-4 py-3 border-b border-[#26354a] ${tone.header}`}>
          <div className="flex items-center gap-2"><span className={`h-8 w-1 rounded-full ${tone.bar}`}/><div><div className={`text-base font-bold ${tone.badge}`}>{line.name}</div><div className="text-xs text-slate-300">Installed stands · actual runtime tracked separately</div></div></div>
          <span className="rounded-full border border-slate-700/70 bg-slate-950/30 px-2.5 py-1 text-[10px] font-semibold text-slate-300">{line.positions?.length || 0} positions</span>
        </div>
        <div className="flex gap-2 overflow-x-auto p-2 md:grid md:grid-cols-10 md:gap-px md:bg-[#243247] md:p-px">
          {line.positions?.map((p:any)=>{const s=p.current_stand;const life=s?.life_percent;const attention=!!(s?.leakage||s?.vibration||s?.abnormal_sound);return <button key={p.id} disabled={!s} onClick={()=>open(s)} title={s?`${line.name} P${p.position_number} · ${s.code}`:`${line.name} P${p.position_number}`} className={`min-w-[118px] md:min-w-0 text-left p-2.5 bg-[#101827] hover:bg-[#151F2E] disabled:opacity-40 transition-colors ${attention?"ring-1 ring-inset ring-rose-500/60":""}`}>
            <div className="flex justify-between items-center gap-2"><span className="text-xs font-bold text-slate-300">P{p.position_number}</span>{attention?<span className="rounded-full bg-rose-500/15 px-1.5 py-0.5 text-[9px] font-bold text-rose-300">CHECK</span>:life!=null?<span className={`h-2 w-2 rounded-full ${life>=90?"bg-rose-400":life>=75?"bg-amber-400":"bg-emerald-400"}`}/>:null}</div>
            <div className="text-xl font-semibold text-white mt-1 truncate">{s?.code||"—"}</div>
            <div className="mt-1.5 space-y-0.5 text-xs text-slate-300">
              <div className="truncate"><span className="text-slate-400">Installed </span>{date(s?.installed_at)}</div>
              <div className="text-[11px] leading-snug"><span className="text-slate-400">Installed elapsed </span>{s?runtimeHours(installationElapsedHours(s,asOf)):"—"}</div>
              <div className="text-[11px] leading-snug"><span className="text-slate-400">Actual mill run </span>{s?runtimeLabel(s.campaign_hours,s.known_runtime_hours,s.runtime_complete):"—"}</div>
              {life!=null&&<div className={`font-semibold ${life>=90?"text-rose-300":life>=75?"text-amber-300":"text-emerald-300"}`}><span className="text-slate-400 font-normal">Life </span>{life}%</div>}
            </div>
            <div className="mt-2 flex flex-wrap gap-1 min-h-[18px]">
              {s?.leakage&&<span className="rounded bg-blue-500/15 px-1.5 py-0.5 text-[9px] font-bold text-blue-300">LEAK</span>}
              {s?.vibration&&<span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[9px] font-bold text-amber-300">VIB</span>}
              {s?.abnormal_sound&&<span className="rounded bg-rose-500/15 px-1.5 py-0.5 text-[9px] font-bold text-rose-300">SOUND</span>}
              {s&&!attention&&<span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-300">NORMAL</span>}
            </div>
          </button>})}
        </div>
      </section>})}
    </div>
    {selected&&<div className="fixed inset-0 z-[70] bg-black/65 flex items-end md:items-center justify-center md:p-5" onClick={()=>setSelected(null)}><div className="w-full md:max-w-4xl max-h-[92vh] overflow-auto rounded-t-xl md:rounded-xl bg-[#0f1725] border border-slate-700 p-4" onClick={e=>e.stopPropagation()}><div className="flex justify-end mb-3"><button onClick={()=>setSelected(null)} className="dsr-btn">Close</button></div><StandDetails stand={selected}/></div></div>}
  </>;
}
