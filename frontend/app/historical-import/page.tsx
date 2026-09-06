"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Kind="STAND_TRACKING"|"SPARE_USAGE"|"PROCESS_PARAMETERS";
type Preview={kind:string;filename:string;records:number;with_reasons?:number;spares?:number;lines?:string[];mapping?:Record<string,string>;date_from?:string;date_to?:string;note?:string};
type CardState={file:File|null;preview:Preview|null;loading:boolean;message:string;error:string};

const DATASETS:{kind:Kind;title:string;hint:string;example:string;accent:string}[]=[
  {kind:"STAND_TRACKING",title:"Stand Tracking History",hint:"Running stand snapshots are converted into inferred campaigns. This data stays separate from exact live DSR changes.",example:"Stand Tracking 2025.xlsx",accent:"blue"},
  {kind:"SPARE_USAGE",title:"Spare Utilization History",hint:"Daily spare consumption is stored only in the historical spare-usage dataset. All workbook sheets/time periods are read.",example:"Spare Utilized.xlsx",accent:"emerald"},
  {kind:"PROCESS_PARAMETERS",title:"WRM Process Parameters",hint:"Process conditions are stored separately for engineering correlation. Mapping: WRM3 → W1, WRM4 → W2, WRM5 → W3.",example:"WRM Parameter Report JUNE 2026.xlsx",accent:"purple"},
];

const blank=():CardState=>({file:null,preview:null,loading:false,message:"",error:""});

export default function HistoricalImportPage(){
  const [summary,setSummary]=useState<any>(null);
  const [states,setStates]=useState<Record<Kind,CardState>>({STAND_TRACKING:blank(),SPARE_USAGE:blank(),PROCESS_PARAMETERS:blank()});
  const loadSummary=async()=>{try{setSummary(await fetchApi("/historical/summary"));}catch{}};
  useEffect(()=>{loadSummary()},[]);
  const patch=(kind:Kind,part:Partial<CardState>)=>setStates(s=>({...s,[kind]:{...s[kind],...part}}));

  async function preview(kind:Kind){
    const s=states[kind];if(!s.file)return;patch(kind,{loading:true,error:"",message:"",preview:null});
    try{const fd=new FormData();fd.append("file",s.file);fd.append("expected_kind",kind);const r=await fetchApi("/historical/preview",{method:"POST",body:fd});patch(kind,{preview:r});}
    catch(e:any){patch(kind,{error:e.message});}finally{patch(kind,{loading:false});}
  }
  async function importData(kind:Kind){
    const s=states[kind];if(!s.file||!s.preview)return;
    if(!window.confirm(`Import ${s.preview.records} reviewed ${s.preview.kind.toLowerCase().replaceAll("_"," ")} records?`))return;
    patch(kind,{loading:true,error:""});
    try{const fd=new FormData();fd.append("file",s.file);fd.append("expected_kind",kind);const r=await fetchApi("/historical/import",{method:"POST",body:fd});patch(kind,{message:`Imported ${r.inserted}; skipped ${r.skipped} existing records.`});await loadSummary();}
    catch(e:any){patch(kind,{error:e.message});}finally{patch(kind,{loading:false});}
  }

  return <div className="flex-1 min-h-screen bg-industrial-dark text-slate-100"><Header title="Historical Data"/><main className="p-4 md:p-5 max-w-7xl space-y-4">
    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"><h1 className="text-xl font-black">Historical Reliability Data</h1><p className="mt-1 text-xs text-slate-400">Each source is intentionally imported into a different dataset. Stand history, spare usage and process parameters are never mixed into one table.</p></section>

    {summary&&<section className="grid grid-cols-1 md:grid-cols-3 gap-3">
      <div className="rounded-lg border border-blue-900/60 bg-blue-950/10 p-3"><div className="text-2xl font-black text-blue-300">{summary.campaigns}</div><div className="text-xs text-slate-400">Historical campaigns · {summary.campaign_files||0} file(s)</div></div>
      <div className="rounded-lg border border-emerald-900/60 bg-emerald-950/10 p-3"><div className="text-2xl font-black text-emerald-300">{summary.spare_usage_rows}</div><div className="text-xs text-slate-400">Spare usage rows · {summary.spare_files||0} file(s)</div></div>
      <div className="rounded-lg border border-purple-900/60 bg-purple-950/10 p-3"><div className="text-2xl font-black text-purple-300">{summary.process_observations}</div><div className="text-xs text-slate-400">Process observations · {summary.process_files||0} file(s)</div></div>
    </section>}

    <section className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      {DATASETS.map(ds=>{const s=states[ds.kind];return <div key={ds.kind} className="rounded-xl border border-slate-800 bg-slate-950/30 p-4 space-y-3">
        <div><div className="text-[10px] tracking-widest text-slate-500">SEPARATE DATASET</div><h2 className="font-bold text-white mt-1">{ds.title}</h2><p className="text-xs text-slate-500 mt-1 min-h-10">{ds.hint}</p></div>
        <div className="text-[11px] text-slate-600">Example: {ds.example}</div>
        <input type="file" accept=".xlsx" onChange={e=>patch(ds.kind,{file:e.target.files?.[0]||null,preview:null,message:"",error:""})} className="w-full text-xs text-slate-300 file:mr-2 file:rounded file:border-0 file:bg-slate-700 file:px-2 file:py-2 file:text-slate-100"/>
        <div className="flex gap-2"><button disabled={!s.file||s.loading} onClick={()=>preview(ds.kind)} className="rounded bg-blue-600 px-3 py-2 text-xs font-semibold disabled:opacity-40">{s.loading?"Working...":"Preview"}</button><button disabled={!s.preview||s.loading} onClick={()=>importData(ds.kind)} className="rounded bg-emerald-600 px-3 py-2 text-xs font-semibold disabled:opacity-40">Import reviewed</button></div>
        {s.preview&&<div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-xs space-y-1"><div className="font-bold text-white break-all">{s.preview.filename}</div><div>Detected: <span className="text-slate-200">{s.preview.kind.replaceAll("_"," ")}</span></div><div>Records: <b>{s.preview.records}</b></div>{s.preview.with_reasons!=null&&<div>Changes with remarks: {s.preview.with_reasons}</div>}{s.preview.spares!=null&&<div>Unique spares: {s.preview.spares}</div>}{s.preview.date_from&&<div>Period: {s.preview.date_from} → {s.preview.date_to}</div>}{s.preview.mapping&&<div className="text-purple-300">WRM3 → W1 · WRM4 → W2 · WRM5 → W3</div>}{s.preview.note&&<div className="text-amber-300">{s.preview.note}</div>}</div>}
        {s.message&&<div className="text-xs text-emerald-300">✓ {s.message}</div>}{s.error&&<div className="text-xs text-red-300">{s.error}</div>}
      </div>})}
    </section>

    <section className="rounded-xl border border-amber-900/60 bg-amber-950/10 p-4 text-xs text-slate-400"><b className="text-amber-200">Source hierarchy:</b> live DSR campaign records are exact and remain the source of truth. Historical stand sheets are inferred. Spare history and process parameters are independent evidence datasets used for planning and correlation.</section>
  </main></div>
}
