"use client";
import { useState } from "react";
import { fetchApi } from "@/lib/api";

export default function ImportReportPage() {
  const [text,setText]=useState(""); const [result,setResult]=useState<any>(null); const [error,setError]=useState(""); const [loading,setLoading]=useState(false);
  async function analyse(){ setLoading(true);setError("");setResult(null); try{setResult(await fetchApi("/import-report/analyse",{method:"POST",body:JSON.stringify({text})}));}catch(e:any){setError(e.message);}finally{setLoading(false);} }
  return <main className="p-5 max-w-6xl mx-auto space-y-4">
    <div><h1 className="text-xl font-bold text-white">Import Report</h1><p className="text-xs text-slate-400">Paste the shift / WhatsApp report. Nothing changes until you confirm.</p></div>
    <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Paste stand report here..." className="w-full h-64 rounded-xl bg-slate-950 border border-slate-700 p-4 text-sm text-slate-100 outline-none focus:border-blue-500" />
    <button disabled={!text.trim()||loading} onClick={analyse} className="px-5 py-2 rounded-lg bg-blue-600 disabled:opacity-40 text-white text-sm font-semibold">{loading?"Analysing...":"Analyse Report"}</button>
    {error&&<div className="rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}
    {result&&<section className="space-y-3">
      <div className="flex gap-3 text-xs"><span className="px-2 py-1 rounded bg-emerald-950 text-emerald-300">{result.actions.length} detected</span><span className="px-2 py-1 rounded bg-slate-800 text-slate-300">Preview only</span></div>
      <div className="overflow-x-auto rounded-xl border border-slate-800"><table className="w-full text-xs"><thead className="bg-slate-900 text-slate-400"><tr><th className="p-2 text-left">Action</th><th className="p-2 text-left">Stand</th><th className="p-2 text-left">Line / Position</th><th className="p-2 text-left">Details</th></tr></thead><tbody>{result.actions.map((a:any,i:number)=><tr key={i} className="border-t border-slate-800 text-slate-200"><td className="p-2 font-semibold">{a.type}</td><td className="p-2">{a.stand||`${a.stand_removed} → ${a.stand_fixed}`}</td><td className="p-2">{a.line?`${a.line}${a.position?` / ${a.position}`:""}`:"—"}</td><td className="p-2">{a.status||a.reason||"—"}</td></tr>)}</tbody></table></div>
      {result.warnings?.map((w:string,i:number)=><div key={i} className="text-xs text-amber-300">⚠ {w}</div>)}
      <div className="text-xs text-slate-500">Next step: database validation + Safe / Review / Conflict confirmation. This version cannot write imported actions yet.</div>
    </section>}
  </main>;
}
