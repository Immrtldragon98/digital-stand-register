"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchApi } from "@/lib/api";
import { getUser } from "@/lib/auth";

type ComponentRow={
  component_type_id:number;
  name:string;
  required_qty:number|null;
  new_qty:number;
  reused_qty:number;
  carried_life_hours:number|null;
  expected_life_hours:number|null;
  criticality:string|null;
  is_extra:boolean;
};

export default function ComponentPreparationModal({stand,onClose,onComplete}:{stand:any;onClose:()=>void;onComplete:()=>Promise<void>|void}){
  const [rows,setRows]=useState<ComponentRow[]>([]);
  const [loading,setLoading]=useState(true);
  const [saving,setSaving]=useState(false);
  const [error,setError]=useState("");
  const [notes,setNotes]=useState("");
  const user=getUser();

  useEffect(()=>{
    (async()=>{
      try{
        const d=await fetchApi(`/stands/${stand.id}/components`);
        setRows(d.components||[]);
        setNotes(d.notes||"");
      }catch(e:any){setError(e.message);}finally{setLoading(false);}
    })();
  },[stand.id]);

  const filled=useMemo(()=>rows.filter(r=>(r.new_qty||0)+(r.reused_qty||0)>0).length,[rows]);
  const complete=useMemo(()=>rows.filter(r=>r.required_qty!==null).every(r=>(r.new_qty||0)+(r.reused_qty||0)===r.required_qty),[rows]);

  function change(id:number,key:"new_qty"|"reused_qty"|"carried_life_hours",value:string){
    const n=value===""?null:Math.max(0,Number(value)||0);
    setRows(v=>v.map(r=>r.component_type_id===id?{...r,[key]:n}:r));
  }

  async function save(skip:boolean){
    setSaving(true);setError("");
    try{
      await fetchApi(`/stands/${stand.id}/components`,{
        method:"POST",
        body:JSON.stringify({
          prepared_by:user?.username||"Operator",
          notes,
          skip,
          items:skip?[]:rows.map(r=>({
            component_type_id:r.component_type_id,
            new_qty:r.new_qty||0,
            reused_qty:r.reused_qty||0,
            carried_life_hours:(r.reused_qty||0)>0?r.carried_life_hours:null,
          })),
        }),
      });
      await fetchApi("/operations/stands/status",{
        method:"POST",
        body:JSON.stringify({
          stand_code:stand.code,
          status:"GAUGING",
          updated_by:user?.username||"Operator",
          remarks:skip?"Components skipped before gauging":"Components saved before gauging",
        }),
      });
      await onComplete();
      onClose();
    }catch(e:any){setError(e.message||"Could not save components");}finally{setSaving(false);}
  }

  return <div className="fixed inset-0 z-[60] bg-black/75 flex items-center justify-center p-4" onClick={onClose}>
    <div className="w-full max-w-5xl max-h-[90vh] overflow-auto rounded-xl border border-slate-700 bg-slate-950 p-4" onClick={e=>e.stopPropagation()}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-blue-400 font-bold">Before Gauging</div>
          <h2 className="text-lg font-black text-white">Stand {stand.code} · Components</h2>
          <p className="text-xs text-slate-400 mt-1">Enter new and reused quantities. Previous life is optional and only needed when you know the reused component life.</p>
        </div>
        <button onClick={onClose} className="text-xs px-3 py-1 rounded border border-slate-700">Close</button>
      </div>

      {error&&<div className="mb-3 rounded border border-red-900 bg-red-950/30 p-2 text-xs text-red-300">{error}</div>}

      {loading?<div className="p-6 text-sm text-slate-500">Loading component list...</div>:<>
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full min-w-[860px] text-xs">
            <thead className="bg-slate-900 text-slate-400">
              <tr><th className="p-2 text-left">Component</th><th>Required</th><th>New</th><th>Old / Reused</th><th>Previous life (h)</th><th>Check</th></tr>
            </thead>
            <tbody>{rows.map(r=>{
              const total=(r.new_qty||0)+(r.reused_qty||0);
              const ok=r.required_qty==null?total>0:total===r.required_qty;
              return <tr key={r.component_type_id} className="border-t border-slate-800">
                <td className="p-2 font-semibold text-white">{r.name}{r.is_extra&&<span className="ml-2 text-[9px] text-blue-300">EVEN STAND EXTRA</span>}</td>
                <td className="p-2 text-center">{r.required_qty??"As fitted"}</td>
                <td className="p-2 text-center"><input type="number" min="0" value={r.new_qty||0} onChange={e=>change(r.component_type_id,"new_qty",e.target.value)} className="w-16 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-center"/></td>
                <td className="p-2 text-center"><input type="number" min="0" value={r.reused_qty||0} onChange={e=>change(r.component_type_id,"reused_qty",e.target.value)} className="w-16 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-center"/></td>
                <td className="p-2 text-center"><input type="number" min="0" disabled={(r.reused_qty||0)===0} value={r.carried_life_hours??""} onChange={e=>change(r.component_type_id,"carried_life_hours",e.target.value)} placeholder={(r.reused_qty||0)>0?"optional":"—"} className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-center disabled:opacity-35"/></td>
                <td className={`p-2 text-center font-bold ${ok?"text-emerald-300":"text-slate-600"}`}>{ok?"✓":"—"}</td>
              </tr>;
            })}</tbody>
          </table>
        </div>

        <div className="mt-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex-1">
            <input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Component remarks (optional)" className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-xs"/>
            <div className={`mt-1 text-[10px] ${complete?"text-emerald-400":"text-slate-500"}`}>{filled} component types recorded · {complete?"Required quantities complete":"Partial data is allowed"}</div>
          </div>
          <div className="flex gap-2">
            <button disabled={saving} onClick={()=>save(true)} className="rounded border border-slate-600 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-900 disabled:opacity-40">Skip → Gauging</button>
            <button disabled={saving} onClick={()=>save(false)} className="rounded bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-500 disabled:opacity-40">Save → Gauging</button>
          </div>
        </div>
      </>}
    </div>
  </div>;
}
