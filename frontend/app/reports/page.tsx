"use client";

import { useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { API_BASE_URL } from "@/lib/api";
import { Download, ShieldCheck } from "lucide-react";

export default function ReportsPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const downloadUrl = useMemo(() => `${API_BASE_URL}/reports/running-status.xlsx?year=${year}&month=${month}`, [year, month]);
  return <div className="dsr-page"><Header title="Reports"/><main className="dsr-main"><div className="full-bleed space-y-3">
    <div className="dsr-section-head"><div><div className="dsr-kicker">Export</div><h1 className="dsr-title">Monthly Reports</h1><p className="dsr-subtitle">Download W1, W2 and W3 running stand history for the selected month.</p></div></div>
    <section className="mechanical-panel p-4 md:p-5"><div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end"><div><div className="text-base font-bold text-white">Running Stand Status</div><div className="mt-1 text-sm text-slate-400">One Excel workbook with one sheet per line.</div></div><div className="grid grid-cols-2 sm:flex gap-2"><label><span className="metric-label">Year</span><input className="input-class mt-1 sm:w-28" type="number" min={2026} max={2100} value={year} onChange={e=>setYear(Number(e.target.value))}/></label><label><span className="metric-label">Month</span><select className="input-class mt-1 sm:w-28" value={month} onChange={e=>setMonth(Number(e.target.value))}>{Array.from({length:12},(_,i)=>i+1).map(m=><option key={m} value={m}>{String(m).padStart(2,"0")}</option>)}</select></label><a href={downloadUrl} className="dsr-btn-primary col-span-2 sm:self-end"><Download className="w-4 h-4"/>Download Excel</a></div></div></section>
    <section className="rounded-xl border border-emerald-900/50 bg-emerald-950/10 p-4"><div className="flex gap-3 items-start"><ShieldCheck className="w-5 h-5 text-emerald-300 mt-0.5"/><div><div className="font-bold text-white">Safe data retention</div><p className="mt-1 text-sm leading-6 text-slate-400">Reports are generated on demand. They do not delete running stands, history, component records or entry-guide history.</p></div></div></section>
  </div></main></div>;
}
