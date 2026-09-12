"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";
import { getUser, isAdmin } from "@/lib/auth";

function bytes(v:number){if(!Number.isFinite(v))return"—";const u=["B","KB","MB","GB"];let n=v,i=0;while(n>=1024&&i<u.length-1){n/=1024;i++}return `${n.toFixed(i<2?0:1)} ${u[i]}`}
function uptime(v:number){const h=Math.floor(v/3600),m=Math.floor((v%3600)/60);return h?`${h}h ${m}m`:`${m}m`}

export default function SystemStatusPage(){
  const [data,setData]=useState<any>(null);const [error,setError]=useState("");const [loading,setLoading]=useState(true);const user=getUser();
  async function load(){setLoading(true);setError("");try{setData(await fetchApi("/system/status"));}catch(e:any){setError(e.message||"Could not load system status");}finally{setLoading(false)}}
  useEffect(()=>{if(isAdmin(user))load();else setLoading(false)},[]);
  if(!isAdmin(user))return <div className="dsr-page"><Header title="System Status"/><main className="dsr-main"><div className="mechanical-panel p-5 text-rose-300">Admin access required.</div></main></div>;
  return <div className="dsr-page"><Header title="System Status"/><main className="dsr-main"><div className="full-bleed space-y-4">
    <div className="dsr-section-head"><div><div className="dsr-kicker">Admin</div><h1 className="dsr-title">System Status</h1><p className="dsr-subtitle">Application health, database footprint and data counts.</p></div><button onClick={load} className="dsr-btn">Refresh</button></div>
    {loading&&<div className="dsr-empty">Checking system…</div>}{error&&<div className="rounded-lg border border-red-900 bg-red-950/25 p-3 text-sm text-red-300">{error}</div>}
    {data&&<>
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Metric label="API" value={data.api} tone="text-emerald-300"/>
        <Metric label="Database" value={data.database} tone="text-emerald-300"/>
        <Metric label="Database size" value={bytes(data.database_bytes)} tone="text-cyan-300"/>
        <Metric label="Backend peak memory" value={bytes(data.process_peak_memory_bytes)} tone="text-violet-300"/>
      </section>
      <section className="mechanical-panel overflow-hidden"><div className="dsr-panel-head"><div><div className="dsr-kicker">Stored data</div><div className="text-sm font-bold text-white">Record Counts</div></div><div className="text-xs text-slate-400">Uptime {uptime(data.process_uptime_seconds)}</div></div><div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-800">{Object.entries(data.counts||{}).map(([k,v])=><div key={k} className="bg-[#111827] p-4"><div className="text-2xl font-bold text-white">{v==null?"—":String(v)}</div><div className="mt-1 text-xs text-slate-400">{k.replaceAll("_"," ")}</div></div>)}</div></section>
      <div className="rounded-lg border border-slate-800 bg-slate-950/30 p-3 text-xs text-slate-400">{data.note}</div>
    </>}
  </div></main></div>;
}
function Metric({label,value,tone}:{label:string;value:string;tone:string}){return <div className="mechanical-panel p-4"><div className="metric-label">{label}</div><div className={`mt-2 text-xl font-bold ${tone}`}>{value}</div></div>}
