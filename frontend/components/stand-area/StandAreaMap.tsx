"use client";

import { useMemo, useState } from "react";
import StandDetails from "@/components/stand/StandDetails";
import { fetchApi } from "@/lib/api";

const STATUS_ORDER = ["READY", "HYDROTEST", "GAUGING", "PENDING", "YET_TO_READY"];
const LABEL: Record<string,string> = { READY:"Ready", HYDROTEST:"Hydrotest", GAUGING:"Gauging", PENDING:"Pending", YET_TO_READY:"Yet to Ready" };
const NEXT: Record<string,string|null> = { READY:null, HYDROTEST:"READY", GAUGING:"HYDROTEST", PENDING:"GAUGING", YET_TO_READY:"PENDING" };
const STYLE: Record<string,string> = {
  READY:"border-emerald-700/70 bg-emerald-950/20 text-emerald-300",
  HYDROTEST:"border-blue-700/70 bg-blue-950/20 text-blue-300",
  GAUGING:"border-violet-700/70 bg-violet-950/20 text-violet-300",
  PENDING:"border-orange-700/70 bg-orange-950/20 text-orange-300",
  YET_TO_READY:"border-slate-700 bg-slate-900/40 text-slate-300",
};

type Props = { lines:any[]; stands:any[]; onRefresh:()=>Promise<void>|void };

export default function StandAreaMap({ stands, onRefresh }: Props) {
  const [selected,setSelected]=useState<any>(null);
  const [saving,setSaving]=useState(false);
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");

  const grouped = useMemo(() => {
    const out:Record<string,any[]> = Object.fromEntries(STATUS_ORDER.map(s=>[s,[]]));
    stands.forEach(s=>{ if(out[s.current_status]) out[s.current_status].push(s); });
    STATUS_ORDER.forEach(k=>out[k].sort((a,b)=>a.code.localeCompare(b.code,undefined,{numeric:true})));
    return out;
  },[stands]);

  async function openStand(stand:any){
    try{ setError(""); setSelected(await fetchApi(`/stands/${stand.id}`)); }
    catch(e){ setError(e instanceof Error?e.message:"Could not load stand"); }
  }

  async function advance(stand:any){
    const next=NEXT[stand.current_status]; if(!next) return;
    let updatedBy="System"; let remarks:string|null=null;
    if(["GAUGING","HYDROTEST","READY"].includes(next)){
      updatedBy=window.prompt(`Who completed ${LABEL[next]} for ${stand.code}?`)?.trim()||"";
      if(!updatedBy) return;
      remarks=window.prompt("Remarks (optional)")?.trim()||null;
    }
    setSaving(true); setError(""); setMessage("");
    try{
      await fetchApi("/operations/stands/status",{method:"POST",body:JSON.stringify({stand_code:stand.code,status:next,updated_by:updatedBy,remarks})});
      setMessage(`${stand.code} → ${LABEL[next]}`); await onRefresh();
    }catch(e){setError(e instanceof Error?e.message:"Update failed");}
    finally{setSaving(false);}
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white">Stand Preparation</h2>
          <p className="text-xs text-slate-400">Yet to Ready → Pending → Gauging → Hydrotest → Ready</p>
        </div>
        <button onClick={()=>onRefresh()} className="text-xs px-3 py-2 rounded border border-slate-700 hover:border-blue-500">Refresh</button>
      </div>

      {(message||error)&&<div className={`text-xs px-3 py-2 rounded border ${error?"border-red-800 text-red-300":"border-emerald-800 text-emerald-300"}`}>{error||message}</div>}

      <div className="space-y-2">
        {STATUS_ORDER.map(status=>(
          <section key={status} className={`rounded-xl border p-2.5 ${STYLE[status]}`}>
            <div className="grid gap-1.5 items-stretch" style={{gridTemplateColumns:"repeat(16,minmax(0,1fr))"}}>
              <div className="col-span-2 flex flex-col justify-center px-2 min-w-0">
                <div className="text-xs font-black uppercase tracking-wide">{LABEL[status]}</div>
                <div className="text-[10px] opacity-70">{grouped[status].length} stands</div>
              </div>
              {grouped[status].map(stand=>(
                <div key={stand.id} className="min-w-0 rounded-lg border border-white/15 bg-slate-950/40 p-1.5 flex flex-col justify-between">
                  <button onClick={()=>openStand(stand)} className="text-left min-w-0">
                    <div className="text-sm font-black text-white truncate">{stand.code}</div>
                    <div className="text-[9px] text-slate-400 truncate">{Number(stand.lifetime_hours||0).toFixed(1)} h</div>
                  </button>
                  {NEXT[status]&&<button disabled={saving} onClick={()=>advance(stand)} className="mt-1 text-[9px] leading-none py-1 rounded border border-white/20 hover:bg-white/10 truncate">→ {LABEL[NEXT[status]!]}</button>}
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>

      {selected&&(
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-6" onClick={()=>setSelected(null)}>
          <div className="w-full max-w-3xl max-h-[85vh] overflow-auto bg-slate-950 border border-slate-700 rounded-xl p-4" onClick={e=>e.stopPropagation()}>
            <div className="flex justify-end mb-2"><button onClick={()=>setSelected(null)} className="text-xs px-3 py-1 rounded border border-slate-700">Close</button></div>
            <StandDetails stand={selected}/>
          </div>
        </div>
      )}
    </div>
  );
}
