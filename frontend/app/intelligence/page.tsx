"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Summary = {
  data:{campaigns:number;spare_usage_rows:number;process_observations:number};
  line_stats:any[]; weak_positions:any[]; cause_pareto:any[]; repeat_low_life:any[]; top_spares:any[]; process_screen:any[]; method_note:string;
};

const fmt=(v:any,suffix="")=>v===null||v===undefined?"—":`${v}${suffix}`;
const causeName=(s:string)=>(s||"").replaceAll("_"," ");

export default function IntelligencePage(){
  const [data,setData]=useState<Summary|null>(null); const [error,setError]=useState(""); const [loading,setLoading]=useState(true);
  const load=async()=>{setLoading(true);setError("");try{setData(await fetchApi("/intelligence/summary"));}catch(e:any){setError(e.message||"Could not load intelligence");}finally{setLoading(false);}};
  useEffect(()=>{load()},[]);
  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Campaign Intelligence" />
    <main className="p-4 md:p-5 flex-1 space-y-4">
      <div className="flex items-start justify-between gap-3"><div><h1 className="text-xl font-black text-white">Stand Life Intelligence</h1><p className="text-xs text-slate-400 mt-1">Historical campaigns + spare usage + WRM process parameters. Use this for screening and planning, not automatic root-cause conclusions.</p></div><button onClick={load} className="px-3 py-2 rounded-lg border border-slate-700 bg-slate-900 text-xs">Refresh</button></div>
      {loading&&<div className="text-sm text-slate-400">Loading reliability history...</div>}
      {error&&<div className="rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}
      {data&&<>
        <section className="grid grid-cols-3 gap-3">
          {[['Historical campaigns',data.data.campaigns],['Spare usage records',data.data.spare_usage_rows],['Process observations',data.data.process_observations]].map(([k,v])=><div key={String(k)} className="rounded-xl border border-slate-800 bg-slate-900/45 p-4"><div className="text-[10px] uppercase tracking-wide text-slate-500">{k}</div><div className="text-2xl font-black text-white mt-1">{v}</div></div>)}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800"><h2 className="font-bold text-white">Line Baseline</h2><p className="text-[11px] text-slate-500">Completed inferred campaigns from historical daily running-status records.</p></div>
          <div className="grid grid-cols-1 md:grid-cols-3">{data.line_stats.map(x=><div key={x.line} className="p-4 border-b md:border-b-0 md:border-r last:border-r-0 border-slate-800"><div className="text-lg font-black text-blue-300">{x.line}</div><div className="mt-2 grid grid-cols-3 gap-2 text-xs"><div><span className="text-slate-500">Campaigns</span><div className="font-bold">{x.campaigns}</div></div><div><span className="text-slate-500">Avg life</span><div className="font-bold">{fmt(x.avg_days,' d')}</div></div><div><span className="text-slate-500">Median</span><div className="font-bold">{fmt(x.median_days,' d')}</div></div></div></div>)}</div>
        </section>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden"><div className="px-4 py-3 border-b border-slate-800"><h2 className="font-bold">Positions Below Historical Baseline</h2><p className="text-[11px] text-slate-500">Compared with the same position across all three lines.</p></div><table className="w-full text-xs"><thead className="text-slate-500 bg-slate-950/50"><tr><th className="p-2 text-left">Line</th><th>P</th><th>Campaigns</th><th>Avg</th><th>Vs baseline</th></tr></thead><tbody>{data.weak_positions.map((x,i)=><tr key={i} className="border-t border-slate-800"><td className="p-2 font-semibold">{x.line}</td><td className="text-center">{x.position}</td><td className="text-center">{x.campaigns}</td><td className="text-center">{fmt(x.avg_days,' d')}</td><td className={`text-center font-bold ${x.vs_position_baseline_pct<0?'text-amber-300':'text-emerald-300'}`}>{fmt(x.vs_position_baseline_pct,'%')}</td></tr>)}</tbody></table></section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden"><div className="px-4 py-3 border-b border-slate-800"><h2 className="font-bold">Removal Cause Pareto</h2><p className="text-[11px] text-slate-500">Normalized from historical remarks; unspecified remarks are excluded.</p></div><div className="p-3 space-y-2">{data.cause_pareto.length?data.cause_pareto.map((x,i)=>{const max=data.cause_pareto[0]?.count||1;return <div key={i}><div className="flex justify-between text-xs"><span>{causeName(x.cause)}</span><span className="font-bold">{x.count}</span></div><div className="h-1.5 bg-slate-800 rounded mt-1"><div className="h-1.5 bg-blue-500 rounded" style={{width:`${Math.max(3,(x.count/max)*100)}%`}}/></div></div>}):<div className="text-xs text-slate-500">Import historical stand tracking to populate cause analysis.</div>}</div></section>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden"><div className="px-4 py-3 border-b border-slate-800"><h2 className="font-bold">Repeated Low-Life Stand Codes</h2><p className="text-[11px] text-slate-500">Lowest historical averages among stand codes with at least 3 completed campaigns.</p></div><table className="w-full text-xs"><thead className="text-slate-500 bg-slate-950/50"><tr><th className="p-2 text-left">Stand</th><th>Campaigns</th><th>Avg life</th><th>Median</th></tr></thead><tbody>{data.repeat_low_life.map((x,i)=><tr key={i} className="border-t border-slate-800"><td className="p-2 font-bold">{x.stand}</td><td className="text-center">{x.campaigns}</td><td className="text-center">{fmt(x.avg_days,' d')}</td><td className="text-center">{fmt(x.median_days,' d')}</td></tr>)}</tbody></table></section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden"><div className="px-4 py-3 border-b border-slate-800"><h2 className="font-bold">Historical Spare Consumption</h2><p className="text-[11px] text-slate-500">Highest total quantities in the imported spare-usage register.</p></div><table className="w-full text-xs"><thead className="text-slate-500 bg-slate-950/50"><tr><th className="p-2 text-left">Spare</th><th className="text-right p-2">Qty used</th></tr></thead><tbody>{data.top_spares.map((x,i)=><tr key={i} className="border-t border-slate-800"><td className="p-2">{x.spare}</td><td className="p-2 text-right font-bold">{x.quantity}</td></tr>)}</tbody></table></section>
        </div>

        <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden"><div className="px-4 py-3 border-b border-slate-800"><h2 className="font-bold">Process Screening — Early Campaigns</h2><p className="text-[11px] text-slate-500">Early = campaign life ≤60% of that line's historical median. Difference is an association only.</p></div>{data.process_screen.length?<table className="w-full text-xs"><thead className="text-slate-500 bg-slate-950/50"><tr><th className="p-2 text-left">Line</th><th className="text-left">Parameter</th><th>Overall avg</th><th>Early avg</th><th>Difference</th><th>Samples</th></tr></thead><tbody>{data.process_screen.map((x,i)=><tr key={i} className="border-t border-slate-800"><td className="p-2 font-bold">{x.line}</td><td>{x.parameter}</td><td className="text-center">{x.overall_avg}</td><td className="text-center">{x.early_campaign_avg}</td><td className="text-center font-bold">{fmt(x.difference_pct,'%')}</td><td className="text-center">{x.early_samples}</td></tr>)}</tbody></table>:<div className="p-4 text-xs text-slate-500">Import WRM parameter history and stand history to activate process screening.</div>}</section>
        <div className="rounded-lg border border-amber-900/50 bg-amber-950/15 p-3 text-[11px] text-amber-200">{data.method_note}</div>
      </>}
    </main>
  </div>;
}
