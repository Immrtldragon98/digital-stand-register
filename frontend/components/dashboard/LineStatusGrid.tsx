"use client";

import { useState } from "react";
import { fetchApi } from "@/lib/api";
import StandDetails from "@/components/stand/StandDetails";

function formatRunTime(hoursValue: unknown) {
  const hours = Number(hoursValue ?? 0);
  if (!Number.isFinite(hours) || hours <= 0) return "0 h";
  const days = Math.floor(hours / 24);
  const remainingHours = Math.floor(hours % 24);
  if (days === 0) return `${hours.toFixed(hours < 10 ? 1 : 0)} h`;
  return `${days}d ${remainingHours}h`;
}

function formatInstalledDate(value: unknown) {
  if (!value) return "—";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit", year: "2-digit" });
}

export default function LineStatusGrid({ lines }: { lines: any[] }) {
  const [selected,setSelected]=useState<any>(null);const [error,setError]=useState("");
  if (!lines?.length) return <div className="text-slate-500 text-sm">No running lines mapped.</div>;
  async function openStand(stand:any){if(!stand?.id)return;try{setError("");setSelected(await fetchApi(`/stands/${stand.id}`));}catch(e:any){setError(e.message||"Could not load stand details")}}

  return <>
    {error&&<div className="mb-2 rounded border border-red-900 bg-red-950/30 p-2 text-xs text-red-300">{error}</div>}
    <div className="grid gap-3">
      {lines.map((line) => (
        <section key={line.id} className="rounded-xl border border-slate-800 bg-slate-900/45 p-3">
          <div className="grid grid-cols-[52px_repeat(10,minmax(82px,1fr))] gap-2 items-stretch">
            <div className="rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col items-center justify-center">
              <div className="text-lg font-black text-blue-400">{line.name}</div>
              <div className="text-[10px] text-emerald-400 mt-1">10 / 10</div>
            </div>
            {line.positions?.map((position: any) => {
              const stand = position.current_stand;
              return <button key={position.id} disabled={!stand} onClick={()=>openStand(stand)} className="text-left min-w-0 rounded-lg border border-slate-700 bg-slate-950/45 px-2 py-2 hover:border-blue-500 transition-colors disabled:cursor-default disabled:hover:border-slate-700">
                  <div className="text-[9px] uppercase tracking-wide text-slate-500">P{position.position_number}</div>
                  <div className="text-sm font-bold text-white truncate mt-0.5">{stand?.code || "—"}</div>
                  <div className="text-[9px] text-slate-400 mt-1 truncate">Installed: {formatInstalledDate(stand?.installed_at)}</div>
                  <div className="text-[9px] text-slate-400 truncate" title={`${stand?.campaign_hours ?? 0} running hours`}>Run: {formatRunTime(stand?.campaign_hours)}</div>
                  {stand?.life_percent!=null&&<div className={`text-[9px] font-semibold truncate ${stand.life_percent>=90?"text-red-300":stand.life_percent>=75?"text-amber-300":"text-emerald-300"}`}>Life: {stand.life_percent}%</div>}
                </button>;
            })}
          </div>
        </section>
      ))}
    </div>
    {selected&&<div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-5" onClick={()=>setSelected(null)}><div className="max-w-4xl w-full max-h-[90vh] overflow-auto rounded-xl bg-slate-950 border border-slate-700 p-4" onClick={e=>e.stopPropagation()}><div className="flex justify-end mb-2"><button onClick={()=>setSelected(null)} className="text-xs border border-slate-700 px-3 py-1 rounded">Close</button></div><StandDetails stand={selected}/></div></div>}
  </>;
}
