"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LineStatusGrid from "@/components/dashboard/LineStatusGrid";
import { fetchApi } from "@/lib/api";

export default function DashboardPage(){
  const [lines,setLines]=useState<any[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState<string|null>(null);
  const load=async()=>{try{setError(null);setLines(await fetchApi("/dashboard/"));}catch(e){setError(e instanceof Error?e.message:"Could not load running lines");}finally{setLoading(false)}};
  useEffect(()=>{load()},[]);
  const running=lines.reduce((n,l)=>n+(l.positions||[]).filter((p:any)=>p.current_stand).length,0);
  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Digital Stand Register" />
    <main className="p-3 md:p-4 flex-1">
      <section className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-blue-950/25 p-4 mb-3">
        <div className="flex items-center justify-between gap-3">
          <div><div className="text-[10px] uppercase tracking-[0.2em] text-blue-400 font-bold">Finishing Mill</div><h1 className="text-xl font-black text-white mt-1">Running Lines</h1><p className="text-xs text-slate-400 mt-1">W1 · W2 · W3</p></div>
          <div className="flex items-center gap-4"><div className="text-right"><div className="text-3xl font-black text-emerald-400">{running}</div><div className="text-[10px] text-slate-400 uppercase">stands running</div></div><button onClick={load} className="px-3 py-2 text-xs rounded-lg border border-blue-800/60 bg-blue-950/30 hover:bg-blue-900/40">Refresh</button></div>
        </div>
      </section>
      {loading&&<div className="text-slate-400 text-sm">Loading running lines...</div>}
      {error&&<div className="bg-red-950/40 border border-red-800 rounded-lg p-3 text-red-300 text-sm">{error}</div>}
      {!loading&&!error&&<LineStatusGrid lines={lines}/>} 
    </main>
  </div>;
}
