"use client";
import Link from "next/link";
import { currentRunLeaders, runtimeHours } from "@/lib/runtime-display";
export default function CurrentRunSummary({lines,asOf}:{lines:any[];asOf:number}){
 const result=currentRunLeaders(lines,asOf);const elapsed=result.elapsedLeader;const measured=result.measuredLeader;
 return <section aria-label="Current stand run comparison" className="grid gap-3 md:grid-cols-2 mb-4">
  <article className="mechanical-panel p-4"><h2 className="text-xs font-semibold text-slate-400">Longest current installation</h2><div className="mt-2 text-lg font-bold text-white">{elapsed?`${elapsed.line} P${elapsed.position} · ${elapsed.stand}`:"Not available"}</div><div className="mt-1 text-xl font-bold text-sky-200">{elapsed?runtimeHours(elapsed.elapsed_hours):"No installation date"}</div><p className="mt-2 text-xs text-slate-400">Elapsed since installation at the last sync. Stoppages are included; this is not measured mill-running life.</p></article>
  <article className="mechanical-panel p-4"><h2 className="text-xs font-semibold text-slate-400">Longest fully measured current mill run</h2><div className="mt-2 text-lg font-bold text-white">{measured?`${measured.line} P${measured.position} · ${measured.stand}`:"Actual runtime not available"}</div>{measured&&<div className="mt-1 text-xl font-bold text-emerald-200">{runtimeHours(measured.actual_runtime_hours)}</div>}<p className="mt-2 text-xs text-slate-400">{result.measuredCount} of {result.installedCount} current campaigns have complete runtime coverage. Incomplete campaigns are excluded from this ranking.</p><Link href="/runtime" className="mt-2 inline-flex min-h-[36px] items-center text-xs text-sky-300">View mill start/stop records</Link></article>
 </section>;
}

