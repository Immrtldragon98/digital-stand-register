"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LineStatusGrid from "@/components/dashboard/LineStatusGrid";
import { fetchApi } from "@/lib/api";
import { RefreshCw } from "lucide-react";

export default function DashboardPage(){
  const[lines,setLines]=useState<any[]>([]);
  const[loading,setLoading]=useState(true);
  const[error,setError]=useState<string|null>(null);
  const load=async()=>{try{setError(null);setLines(await fetchApi("/dashboard/"))}catch(e){setError(e instanceof Error?e.message:"Could not load running lines")}finally{setLoading(false)}};
  useEffect(()=>{load()},[]);
  const running=lines.reduce((n,l)=>n+(l.positions||[]).filter((p:any)=>p.current_stand).length,0);
  return <div className="flex-1 min-h-screen text-slate-100">
    <Header title="Digital Stand Register"/>
    <main className="p-3 md:p-5 full-bleed">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h1 className="page-title">Running Stands</h1>
          <p className="page-subtitle mt-1">W1 · W2 · W3 — select a stand to view components and history.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-300"><span className="font-semibold text-white">{running}</span> / 30 running</div>
          <button onClick={load} aria-label="Refresh running stands" className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"><RefreshCw className="w-4 h-4"/>Refresh</button>
        </div>
      </div>
      {loading&&<div className="mechanical-panel p-4 text-slate-400 text-sm">Loading running lines…</div>}
      {error&&<div className="bg-red-950/30 border border-red-900 rounded-lg p-3 text-red-300 text-sm">{error}</div>}
      {!loading&&!error&&<LineStatusGrid lines={lines}/>} 
    </main>
  </div>;
}
