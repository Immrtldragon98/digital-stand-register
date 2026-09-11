"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Summary = {
  data:{campaigns:number;spare_usage_rows:number;process_observations:number};
  line_stats:any[]; weak_positions:any[]; cause_pareto:any[]; repeat_low_life:any[]; top_spares:any[]; process_screen:any[]; method_note:string;
};

type Chat = {role:"user"|"assistant"; text:string};
const fmt=(v:any,suffix="")=>v===null||v===undefined?"—":`${v}${suffix}`;
const clean=(s:string)=>(s||"").replaceAll("_"," ");

export default function IntelligencePage(){
  const [data,setData]=useState<Summary|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [question,setQuestion]=useState("");
  const [asking,setAsking]=useState(false);
  const [chat,setChat]=useState<Chat[]>([{role:"assistant",text:"Ask me about a stand position, weak positions, common causes or spare usage. Example: Investigate W1 P8."}]);

  const load=async()=>{setLoading(true);setError("");try{setData(await fetchApi("/intelligence/summary"));}catch(e:any){setError(e.message||"Could not load intelligence");}finally{setLoading(false);}};
  useEffect(()=>{load()},[]);

  const attention=useMemo(()=>{
    if(!data) return [];
    return [...data.weak_positions].filter((x:any)=>x.vs_position_baseline_pct<0).slice(0,5);
  },[data]);

  async function ask(text?:string){
    const q=(text??question).trim(); if(!q||asking)return;
    setQuestion(""); setChat(c=>[...c,{role:"user",text:q}]); setAsking(true);
    try{
      const up=q.toUpperCase();
      const line=up.match(/\bW([123])\b/)?.[0];
      const posMatch=up.match(/\bP(?:OSITION\s*)?(10|[1-9])\b/) || up.match(/\bPOSITION\s*(10|[1-9])\b/);
      let answer="";
      if(line&&posMatch){
        const pos=Number(posMatch[1]);
        const r=await fetchApi(`/investigation/position?line=${line}&position=${pos}`);
        if(!r.campaigns){answer=`${line} P${pos}: no measurable historical campaigns yet. Keep collecting stand-change history before drawing a life conclusion.`;}
        else{
          const cause=r.causes?.[0]; const weak=r.early_campaigns?`${r.early_campaigns} early-life campaign${r.early_campaigns===1?"":"s"}`:"no early-life campaigns";
          answer=`${line} P${pos}: ${r.campaigns} campaigns, average life ${fmt(r.avg_days," d")}, median ${fmt(r.median_days," d")}, ${weak}. ${cause?`Most common recorded cause: ${clean(cause.cause)} (${cause.count}). `:""}${r.stand_codes?.[0]?`Lowest-life repeated stand in this position: ${r.stand_codes[0].stand} (${fmt(r.stand_codes[0].avg_days," d")} avg). `:""}Treat process/spare links as screening evidence, not confirmed root cause.`;
        }
      } else if(/WEAK|LOW LIFE|WORST|ATTENTION/.test(up) && data){
        const rows=data.weak_positions.filter((x:any)=>x.vs_position_baseline_pct<0).slice(0,5);
        answer=rows.length?`Positions needing attention: ${rows.map((x:any)=>`${x.line} P${x.position} (${x.vs_position_baseline_pct}% vs same-position baseline)`).join(", ")}. Investigate one by asking, for example, “Investigate ${rows[0].line} P${rows[0].position}”.`:`No below-baseline positions are available from the imported history yet.`;
      } else if(/CAUSE|FAIL|WHY/.test(up) && data){
        answer=data.cause_pareto.length?`Most frequent recorded removal causes: ${data.cause_pareto.slice(0,5).map((x:any)=>`${clean(x.cause)} (${x.count})`).join(", ")}. These are historical frequencies, not proof of root cause for the current stand.`:`No usable removal-cause history is available yet.`;
      } else if(/SPARE|CONSUM/.test(up) && data){
        answer=data.top_spares.length?`Highest historical spare usage: ${data.top_spares.slice(0,5).map((x:any)=>`${x.spare} (${x.quantity})`).join(", ")}. Use Spare Life for current stock coverage and availability.`:`No historical spare-usage records are available yet.`;
      } else {
        answer="I can investigate a specific line/position or summarize weak positions, causes and spare usage. Try: “Investigate W1 P8”, “Which positions are weak?”, “What are common failure causes?” or “Show top spare consumption”.";
      }
      setChat(c=>[...c,{role:"assistant",text:answer}]);
    }catch(e:any){setChat(c=>[...c,{role:"assistant",text:e.message||"Could not investigate that request."}]);}
    finally{setAsking(false);}
  }

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Stand Intelligence" />
    <main className="p-4 md:p-5 flex-1 space-y-4 max-w-[1500px] w-full">
      <div className="flex items-start justify-between gap-3"><div><h1 className="text-xl font-black text-white">Stand Intelligence</h1><p className="text-xs text-slate-400 mt-1">One place to ask questions and see what needs attention. Calculations come from plant data; conclusions remain engineering decisions.</p></div><button onClick={load} className="px-3 py-2 rounded-lg border border-slate-700 bg-slate-900 text-xs">Refresh</button></div>
      {loading&&<div className="text-sm text-slate-400">Loading stand history...</div>}
      {error&&<div className="rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-[1.2fr_.8fr] gap-4">
        <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800"><div className="font-bold text-white">Ask Stand Intelligence</div><div className="text-[11px] text-slate-500 mt-1">Start with the stand or position you want to understand.</div></div>
          <div className="p-4 space-y-3 max-h-[420px] overflow-auto">{chat.map((m,i)=><div key={i} className={`text-sm leading-relaxed rounded-lg p-3 ${m.role==="user"?"ml-10 bg-blue-600/20 border border-blue-800 text-blue-100":"mr-6 bg-slate-950/55 border border-slate-800 text-slate-200"}`}>{m.text}</div>)}{asking&&<div className="text-xs text-slate-500">Investigating…</div>}</div>
          <div className="border-t border-slate-800 p-3">
            <div className="flex gap-2"><input value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==="Enter")ask();}} placeholder="Example: Investigate W2 P9" className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500"/><button onClick={()=>ask()} disabled={asking} className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-semibold">Ask</button></div>
            <div className="flex flex-wrap gap-2 mt-2">{["Which positions are weak?","What are common failure causes?","Show top spare consumption"].map(x=><button key={x} onClick={()=>ask(x)} className="text-[10px] px-2 py-1 rounded border border-slate-700 text-slate-400 hover:text-white">{x}</button>)}</div>
          </div>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/45 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800"><div className="font-bold text-white">Needs Attention</div><div className="text-[11px] text-slate-500 mt-1">Lowest life versus the same position across W1/W2/W3.</div></div>
          <div className="p-3 space-y-2">{attention.length?attention.map((x:any)=><button key={`${x.line}-${x.position}`} onClick={()=>ask(`Investigate ${x.line} P${x.position}`)} className="w-full text-left rounded-lg border border-slate-800 bg-slate-950/40 p-3 hover:border-blue-700"><div className="flex items-center justify-between"><span className="font-bold text-white">{x.line} · P{x.position}</span><span className="text-amber-300 text-xs font-bold">{x.vs_position_baseline_pct}%</span></div><div className="text-[11px] text-slate-500 mt-1">Avg {fmt(x.avg_days," d")} · {x.campaigns} campaigns · Click to investigate</div></button>):<div className="text-xs text-slate-500 p-2">No below-baseline positions available yet.</div>}</div>
        </section>
      </div>

      {data&&<section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {data.line_stats.map((x:any)=><div key={x.line} className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"><div className="text-blue-300 font-black">{x.line}</div><div className="grid grid-cols-2 gap-3 mt-2 text-xs"><div><span className="text-slate-500">Avg life</span><div className="font-bold text-white">{fmt(x.avg_days," d")}</div></div><div><span className="text-slate-500">Campaigns</span><div className="font-bold text-white">{x.campaigns}</div></div></div></div>)}
      </section>}

      <div className="text-[10px] text-slate-600">Detailed Investigation remains available behind the assistant when a line and position are selected; it no longer needs a separate menu item.</div>
    </main>
  </div>;
}
