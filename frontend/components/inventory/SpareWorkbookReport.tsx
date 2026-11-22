"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchApi } from "@/lib/api";
import PageLoading from "@/components/ui/PageLoading";

type PlanningRow = { name:string; monthly_target:number|null; ten_day_target:number|null; received:number; still_to_receive:number|null; extra_received:number|null };
type Usage = { usage_date:string; spare_name:string; quantity:number; source_cell:string; source_sheet:string };
type Detail = { usage_date:string; stand_code:string; spare_name:string; quantity:number; raw_name:string; source_row:number };
type Report = {
  available:boolean; source_file:string; latest_receipts_as_of:string; consumption_through:string;
  plans:{month:string; as_of:string|null; rows:PlanningRow[]}[];
  usage:Usage[]; detailed:Detail[]; usage_summary:{name:string;quantity:number;last_used:string;unit:string}[];
  discrepancies:{date:string;spare:string;matrix_quantity:number;detailed_quantity:number}[];
  counts:{matrix_rows:number;matrix_total:number;detailed_rows:number;detailed_total:number};
};
const quantity = (n:number|null|undefined) => n == null ? "Not set" : n.toLocaleString("en-IN");
const date = (d:string) => new Date(`${d}T12:00:00`).toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"});
const monthLabel = (m:string) => new Date(`${m}-01T12:00:00`).toLocaleDateString("en-IN",{month:"long",year:"numeric"});

export default function SpareWorkbookReport({view}:{view:"planning"|"consumption"}) {
  const [report,setReport] = useState<Report|null>(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");
  const [month,setMonth] = useState("");
  const [query,setQuery] = useState("");
  const [evidence,setEvidence] = useState<"totals"|"daily"|"stand">("totals");
  async function load() {
    setLoading(true);setError("");
    try { const data:Report = await fetchApi("/inventory/report");setReport(data);setMonth(m=>m||data.plans?.at(-1)?.month||""); }
    catch(e) { setError(e instanceof Error?e.message:"Could not load the spare report."); }
    finally { setLoading(false); }
  }
  useEffect(()=>{load()},[]);
  const plan = report?.plans.find(p=>p.month===month);
  const match = (name:string) => name.toLowerCase().includes(query.toLowerCase());
  const rows = useMemo(()=>plan?.rows.filter(r=>r.name.toLowerCase().includes(query.toLowerCase()))||[],[plan,query]);
  if (loading) return <div className="mechanical-panel"><PageLoading label="Loading spare requirements and consumption…"/></div>;
  if (error) return <div role="alert" className="mechanical-panel p-4 text-red-300"><p>{error}</p><button className="dsr-btn mt-3" onClick={load}>Retry spare report</button></div>;
  if (!report?.available) return <div className="mechanical-panel dsr-empty">No spare workbook has been imported.</div>;
  return <div className="space-y-3">
    <div className="mechanical-panel p-3 text-sm text-slate-300">
      {view==="planning" ? <><p>{plan?.as_of?<>Receipts reported as of <strong>{date(plan.as_of)}</strong>.</>:<>{monthLabel(month)} receipt summary; an exact update date was not recorded.</>} Received quantities are supplies recorded in the workbook; physical store stock was not provided.</p><p className="mt-1 text-xs text-slate-400">Still to receive = monthly target − received, with a minimum of zero. Extra received is shown separately. Blank targets remain “Not set”.</p></> : <><p>Consumption recorded through <strong>{date(report.consumption_through)}</strong>. November consumption was left blank in the workbook.</p><p className="mt-1 text-xs text-slate-400">Consolidated matrix totals are used for analytics. The supporting stand log is shown separately and is not added to these totals.</p></>}
    </div>
    <div className="mechanical-panel p-3 flex flex-wrap items-center gap-2">
      <input aria-label="Search spare report" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search spare name" className="input-class flex-1 min-w-[180px]"/>
      {view==="planning" ? <select aria-label="Requirement month" className="input-class sm:w-auto" value={month} onChange={e=>setMonth(e.target.value)}>{report.plans.map(p=><option key={p.month} value={p.month}>{monthLabel(p.month)}</option>)}</select> : <select aria-label="Consumption view" className="input-class sm:w-auto" value={evidence} onChange={e=>setEvidence(e.target.value as typeof evidence)}><option value="totals">Spare totals</option><option value="daily">Daily consumption</option><option value="stand">Supporting stand log</option></select>}
    </div>
    {view==="planning" ? <><div className="grid grid-cols-2 gap-2 sm:grid-cols-3"><Stat label="Spare types" value={plan?.rows.length||0}/><Stat label="Items still to receive" value={plan?.rows.filter(r=>(r.still_to_receive??0)>0).length||0}/><Stat label="Targets not supplied" value={plan?.rows.filter(r=>r.monthly_target==null).length||0}/></div>
      <Table headers={["Spare","Monthly target","10-day target","Received (recorded)","Still to receive","Extra received"]}>
        {rows.map(r=><tr key={r.name}><td className="dsr-td font-semibold text-white">{r.name}</td><td className="dsr-td">{quantity(r.monthly_target)}</td><td className="dsr-td">{quantity(r.ten_day_target)}</td><td className="dsr-td">{quantity(r.received)}</td><td className={`dsr-td ${(r.still_to_receive??0)>0?"text-amber-300 font-semibold":""}`}>{quantity(r.still_to_receive)}</td><td className="dsr-td">{quantity(r.extra_received)}</td></tr>)}
        {!rows.length&&<Empty columns={6}/>}
      </Table><p className="text-xs text-slate-400">Unit: pieces. The 10-day target is copied from the workbook. These columns describe procurement requirements, not current stock or spare life.</p></> : <>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3"><Stat label="Consolidated quantity used" value={report.counts.matrix_total}/><Stat label="Supporting log quantity" value={report.counts.detailed_total}/><Stat label="Same-item daily differences" value={report.discrepancies.length}/></div>
      {evidence==="totals" ? <Table headers={["Spare","Quantity used (pcs)","Last recorded use"]}>{report.usage_summary.filter(r=>match(r.name)).map(r=><tr key={r.name}><td className="dsr-td font-semibold text-white">{r.name}</td><td className="dsr-td">{quantity(r.quantity)}</td><td className="dsr-td">{date(r.last_used)}</td></tr>)}{!report.usage_summary.some(r=>match(r.name))&&<Empty columns={3}/>}</Table> : evidence==="daily" ? <Table headers={["Date","Spare","Used (pcs)","Source cell"]}>{report.usage.filter(r=>match(r.spare_name)).map((r,i)=><tr key={i}><td className="dsr-td whitespace-nowrap">{date(r.usage_date)}</td><td className="dsr-td">{r.spare_name}</td><td className="dsr-td">{quantity(r.quantity)}</td><td className="dsr-td">{r.source_cell}</td></tr>)}{!report.usage.some(r=>match(r.spare_name))&&<Empty columns={4}/>}</Table> : <Table headers={["Date","Stand","Spare / source description","Used (pcs)"]}>{report.detailed.filter(r=>match(`${r.spare_name} ${r.stand_code}`)).map((r,i)=><tr key={i}><td className="dsr-td whitespace-nowrap">{date(r.usage_date)}</td><td className="dsr-td font-semibold text-white">{r.stand_code}</td><td className="dsr-td">{r.spare_name}{r.raw_name!==r.spare_name&&<span className="block text-xs text-slate-500">Source: {r.raw_name}</span>}</td><td className="dsr-td">{quantity(r.quantity)}</td></tr>)}{!report.detailed.some(r=>match(`${r.spare_name} ${r.stand_code}`))&&<Empty columns={4}/>}</Table>}
      <details className="mechanical-panel p-3"><summary className="cursor-pointer text-sm text-amber-300">Source differences — {report.discrepancies.length} daily quantities need reconciliation</summary><p className="my-2 text-xs text-slate-400">The matrix also includes entry-guide consumption absent from the detailed stand log. Generic and specific component names remain separate.</p><Table headers={["Date","Spare","Matrix quantity","Stand log quantity"]}>{report.discrepancies.map((r,i)=><tr key={i}><td className="dsr-td">{date(r.date)}</td><td className="dsr-td">{r.spare}</td><td className="dsr-td">{r.matrix_quantity}</td><td className="dsr-td">{r.detailed_quantity}</td></tr>)}</Table></details>
    </>}
    <p className="text-[11px] text-slate-500">Source: {report.source_file}</p>
  </div>;
}
function Stat({label,value}:{label:string;value:number}) {return <div className="dsr-stat"><div className="dsr-stat-label">{label}</div><div className="dsr-stat-value">{quantity(value)}</div></div>}
function Table({headers,children}:{headers:string[];children:React.ReactNode}) {return <div className="dsr-table-wrap"><table className="dsr-table min-w-[600px]"><thead><tr>{headers.map(h=><th key={h} className="dsr-th">{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div>}
function Empty({columns}:{columns:number}) {return <tr><td colSpan={columns} className="dsr-empty">No matching records.</td></tr>}
