"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type VItem={index:number;state:"SAFE"|"REVIEW"|"CONFLICT";message:string;action:any};
type KDoc={id:number;filename:string;category:string;uploaded_by:string;created_at:string;chunks:number};

export default function ImportReportPage() {
  const [text,setText]=useState(""); const [result,setResult]=useState<any>(null); const [validation,setValidation]=useState<any>(null); const [selected,setSelected]=useState<number[]>([]); const [error,setError]=useState(""); const [loading,setLoading]=useState(false); const [confirming,setConfirming]=useState(false); const [done,setDone]=useState<any>(null); const [openReview,setOpenReview]=useState<number|null>(null); const [dismissed,setDismissed]=useState<number[]>([]);
  const [docs,setDocs]=useState<KDoc[]>([]); const [category,setCategory]=useState("ROD_QUALITY"); const [file,setFile]=useState<File|null>(null); const [uploading,setUploading]=useState(false); const [uploadMsg,setUploadMsg]=useState("");

  const loadDocs=async()=>{try{setDocs(await fetchApi("/knowledge/"));}catch{/* keep report import usable if knowledge DB is not migrated yet */}};
  useEffect(()=>{loadDocs()},[]);

  async function uploadDoc(e:React.FormEvent){e.preventDefault();if(!file)return;setUploading(true);setUploadMsg("");setError("");try{const fd=new FormData();fd.append("category",category);fd.append("file",file);const r=await fetchApi("/knowledge/upload",{method:"POST",body:fd});setUploadMsg(`${r.filename} indexed (${r.chunks} chunks)`);setFile(null);await loadDocs();}catch(e:any){setError(e.message);}finally{setUploading(false);}}
  async function analyse(){ setLoading(true);setError("");setResult(null);setValidation(null);setDone(null);setOpenReview(null);setDismissed([]); try{const r=await fetchApi("/import-report/analyse",{method:"POST",body:JSON.stringify({text})});setResult(r);const v=await fetchApi("/import-report/validate",{method:"POST",body:JSON.stringify({actions:r.actions})});setValidation(v);setSelected(v.items.filter((x:VItem)=>x.state==="SAFE").map((x:VItem)=>x.index));}catch(e:any){setError(e.message);}finally{setLoading(false);} }
  async function confirm(){ if(!result||!validation)return; const actions=validation.items.filter((x:VItem)=>selected.includes(x.index)&&x.state==="SAFE").map((x:VItem)=>x.action); if(!actions.length)return; if(!window.confirm(`Apply ${actions.length} safe update(s) to Digital Stand Register?`))return; setConfirming(true);setError(""); try{const r=await fetchApi("/import-report/confirm",{method:"POST",body:JSON.stringify({actions})});setDone(r);const v=await fetchApi("/import-report/validate",{method:"POST",body:JSON.stringify({actions:result.actions})});setValidation(v);setSelected([]);}catch(e:any){setError(e.message);}finally{setConfirming(false);} }
  const badge=(s:string)=>s==="SAFE"?"bg-emerald-950 text-emerald-300 border-emerald-800":s==="REVIEW"?"bg-amber-950 text-amber-300 border-amber-800":"bg-red-950 text-red-300 border-red-800";
  return <main className="p-4 md:p-5 max-w-7xl mx-auto space-y-5">
    <div><h1 className="text-xl font-bold text-white">Import & Knowledge</h1><p className="text-xs text-slate-400">Shift reports update DSR. Plant documents build the evidence base for future RAG analysis.</p></div>

    <section className="rounded-xl border border-slate-800 bg-slate-900/45 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3"><div><h2 className="font-bold text-white">Plant Knowledge</h2><p className="text-xs text-slate-400 mt-1">Import rod quality, emulsion, spare-usage and RCA/FMEA documents. Files are converted to searchable text chunks; raw binary files are not stored in Neon.</p></div><span className="text-[10px] rounded bg-blue-950 text-blue-300 px-2 py-1">RAG foundation</span></div>
      <form onSubmit={uploadDoc} className="grid grid-cols-1 md:grid-cols-[180px_1fr_auto] gap-2 items-center">
        <select value={category} onChange={e=>setCategory(e.target.value)} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm"><option value="ROD_QUALITY">Rod Quality</option><option value="EMULSION">Emulsion</option><option value="SPARE_USAGE">Spare Usage</option><option value="FMEA_RCA">FMEA / RCA</option><option value="SHIFT_REPORT">Shift Report</option><option value="OTHER">Other</option></select>
        <input type="file" accept=".txt,.md,.csv,.xlsx,.pdf,.docx" onChange={e=>setFile(e.target.files?.[0]||null)} className="text-xs text-slate-300 file:mr-3 file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-slate-100"/>
        <button disabled={!file||uploading} className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">{uploading?"Indexing...":"Import Document"}</button>
      </form>
      {uploadMsg&&<div className="text-xs text-emerald-300">✓ {uploadMsg}</div>}
      {docs.length>0&&<div className="overflow-x-auto"><table className="w-full text-xs"><thead className="text-slate-500"><tr><th className="text-left py-1">Document</th><th className="text-left">Category</th><th className="text-center">Chunks</th><th className="text-left">Imported by</th></tr></thead><tbody>{docs.slice(0,8).map(d=><tr key={d.id} className="border-t border-slate-800"><td className="py-1.5 text-slate-200">{d.filename}</td><td>{d.category.replaceAll("_"," ")}</td><td className="text-center">{d.chunks}</td><td>{d.uploaded_by}</td></tr>)}</tbody></table></div>}
      <p className="text-[11px] text-slate-500">Next intelligence layer: retrieve relevant chunks + stand history + spare usage + process data, then ask the LLM for evidence-backed correlations. The LLM will not be allowed to invent causes or write plant data.</p>
    </section>

    <section className="space-y-3">
      <div><h2 className="font-bold text-white">Shift Report</h2><p className="text-xs text-slate-400">Paste shift / WhatsApp report → Analyse → Check → Confirm.</p></div>
      <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Paste stand report here..." className="w-full h-44 rounded-xl bg-slate-950 border border-slate-700 p-4 text-sm text-slate-100 outline-none focus:border-blue-500" />
      <button disabled={!text.trim()||loading} onClick={analyse} className="px-5 py-2 rounded-lg bg-blue-600 disabled:opacity-40 text-white text-sm font-semibold">{loading?"Analysing...":"Analyse Report"}</button>
    </section>

    {error&&<div className="rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}
    {result&&validation&&<section className="space-y-3">
      <div className="flex flex-wrap gap-2 text-xs"><span className="px-2 py-1 rounded bg-slate-800 text-slate-200">{result.provider==="gemini"?"Gemini AI":"Template parser"}</span><span className="px-2 py-1 rounded bg-emerald-950 text-emerald-300">{validation.counts.SAFE} Safe</span><span className="px-2 py-1 rounded bg-amber-950 text-amber-300">{validation.counts.REVIEW} Review</span><span className="px-2 py-1 rounded bg-red-950 text-red-300">{validation.counts.CONFLICT} Conflict</span></div>
      <div className="overflow-x-auto rounded-xl border border-slate-800"><table className="w-full text-xs"><thead className="bg-slate-900 text-slate-400"><tr><th className="p-2 w-16">Action</th><th className="p-2 text-left">Check</th><th className="p-2 text-left">Type</th><th className="p-2 text-left">Stand</th><th className="p-2 text-left">Line / Position</th><th className="p-2 text-left">What DSR found</th></tr></thead><tbody>{validation.items.map((x:VItem)=><>
        <tr key={`row-${x.index}`} className={`border-t border-slate-800 text-slate-200 ${dismissed.includes(x.index)?"opacity-40":""}`}><td className="p-2">{x.state==="SAFE"?<input type="checkbox" checked={selected.includes(x.index)} onChange={e=>setSelected(e.target.checked?[...selected,x.index]:selected.filter(i=>i!==x.index))}/>:x.state==="REVIEW"?<button onClick={()=>setOpenReview(openReview===x.index?null:x.index)} className="px-2 py-1 rounded border border-amber-700 text-amber-300 hover:bg-amber-950/50">{openReview===x.index?"Close":"Resolve"}</button>:<span className="text-red-400">Blocked</span>}</td><td className="p-2"><span className={`px-2 py-1 rounded border ${badge(x.state)}`}>{x.state}</span></td><td className="p-2 font-semibold">{x.action.type}</td><td className="p-2">{x.action.stand||`${x.action.stand_removed||"?"} → ${x.action.stand_fixed||"?"}`}</td><td className="p-2">{x.action.line?`${x.action.line}${x.action.position?` / ${x.action.position}`:""}`:"—"}</td><td className="p-2 max-w-md">{x.message}</td></tr>
        {openReview===x.index&&x.state==="REVIEW"&&<tr key={`review-${x.index}`} className="border-t border-slate-800 bg-amber-950/10"><td colSpan={6} className="p-3"><div className="flex flex-wrap items-center gap-3"><div className="text-amber-200 font-semibold">Review required</div><div className="text-slate-300">{x.message}</div>{x.action.type?.startsWith("ENTRY_GUIDE")&&<Link href="/entry-guides" className="px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-500">Open Entry Guides</Link>}<button onClick={()=>{setDismissed(dismissed.includes(x.index)?dismissed.filter(i=>i!==x.index):[...dismissed,x.index]);setOpenReview(null);}} className="px-3 py-1.5 rounded border border-slate-700 text-slate-300 hover:bg-slate-800">{dismissed.includes(x.index)?"Restore":"Ignore this item"}</button></div><div className="mt-2 text-[11px] text-slate-500">Review items are never written automatically. Resolve them manually, then re-analyse the report if needed.</div></td></tr>}
      </>)}</tbody></table></div>
      {result.warnings?.map((w:string,i:number)=><div key={i} className="text-xs text-amber-300">⚠ {w}</div>)}
      <div className="flex items-center gap-3"><button disabled={!selected.length||confirming} onClick={confirm} className="px-5 py-2 rounded-lg bg-emerald-600 disabled:opacity-40 text-white text-sm font-semibold">{confirming?"Updating...":`Confirm ${selected.length} Safe Update${selected.length===1?"":"s"}`}</button><span className="text-xs text-slate-500">Safe items can be applied. Review items require resolution.</span></div>
      {done&&<div className="rounded-lg border border-emerald-900 bg-emerald-950/25 p-3 text-sm text-emerald-300">Updated {done.updated} item(s). Stand Area and History now use the new data.</div>}
    </section>}
  </main>;
}
