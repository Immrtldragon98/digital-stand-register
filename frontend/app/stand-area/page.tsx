"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

const ORDER = ["READY", "HYDROTEST", "GAUGING", "PENDING", "YET_TO_READY"];
const LABEL: Record<string,string> = { READY:"Ready", HYDROTEST:"Hydrotest", GAUGING:"Gauging", PENDING:"Pending", YET_TO_READY:"Yet to Ready" };
const COLORS: Record<string,string> = {
  READY:"border-emerald-700 bg-emerald-950/25 text-emerald-300",
  HYDROTEST:"border-blue-700 bg-blue-950/25 text-blue-300",
  GAUGING:"border-violet-700 bg-violet-950/25 text-violet-300",
  PENDING:"border-orange-700 bg-orange-950/25 text-orange-300",
  YET_TO_READY:"border-slate-700 bg-slate-900/40 text-slate-300",
};
const NEXT: Record<string,string|undefined> = { YET_TO_READY:"PENDING", PENDING:"GAUGING", GAUGING:"HYDROTEST", HYDROTEST:"READY" };

type Stand = { id:number; code:string; current_status:string; lifetime_hours:number };

export default function StandAreaPage() {
  const [stands,setStands] = useState<Stand[]>([]);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");
  const [saving,setSaving] = useState(false);

  const load = async () => {
    try { setError(""); setStands(await fetchApi("/stands/")); }
    catch(e){ setError(e instanceof Error ? e.message : "Could not load stands"); }
    finally{ setLoading(false); }
  };
  useEffect(()=>{ load(); },[]);

  const groups = useMemo(()=>Object.fromEntries(ORDER.map(s=>[s, stands.filter(x=>x.current_status===s).sort((a,b)=>a.code.localeCompare(b.code,undefined,{numeric:true}))])),[stands]);

  async function advance(stand:Stand){
    const target = NEXT[stand.current_status];
    if(!target) return;
    let who = "System";
    let remarks:string|null = null;
    if(["GAUGING","HYDROTEST","READY"].includes(target)){
      who = window.prompt(`Who completed ${LABEL[target]} for ${stand.code}?`)?.trim() || "";
      if(!who) return;
      remarks = window.prompt("Remarks (optional)")?.trim() || null;
    }
    setSaving(true); setError("");
    try{
      await fetchApi("/operations/stands/status",{method:"POST",body:JSON.stringify({stand_code:stand.code,status:target,updated_by:who,remarks})});
      await load();
    }catch(e){ setError(e instanceof Error ? e.message : "Update failed"); }
    finally{ setSaving(false); }
  }

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Stand Area" />
      <main className="p-4 md:p-6 flex-1 space-y-4">
        <div>
          <h1 className="text-xl font-bold text-white">Stand Preparation Status</h1>
          <p className="text-sm text-slate-400 mt-1">Yet to Ready → Pending → Gauging → Hydrotest → Ready</p>
        </div>
        {error && <div className="p-3 rounded-lg border border-red-800 bg-red-950/40 text-red-300">{error}</div>}
        {loading ? <div className="text-sm text-slate-400">Loading...</div> : ORDER.map(status => (
          <section key={status} className={`border rounded-xl p-3 ${COLORS[status]}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="font-bold uppercase tracking-wide text-sm">{LABEL[status]}</div>
              <div className="text-xs">{groups[status].length} stands</div>
            </div>
            <div className="overflow-x-auto">
              <div className="flex gap-2 min-w-max">
                {groups[status].map((stand:Stand)=>(
                  <div key={stand.id} className="w-36 rounded-lg border border-current/20 bg-black/10 px-3 py-2">
                    <div className="font-bold text-white text-base">{stand.code}</div>
                    <div className="text-[10px] text-slate-400">Life {stand.lifetime_hours ?? 0} h</div>
                    {NEXT[status] && <button disabled={saving} onClick={()=>advance(stand)} className="mt-2 w-full rounded border border-current/30 px-2 py-1 text-[11px] hover:bg-white/5 disabled:opacity-50">→ {LABEL[NEXT[status]!]}</button>}
                  </div>
                ))}
                {groups[status].length===0 && <div className="text-xs text-slate-500 py-2">No stands</div>}
              </div>
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}
