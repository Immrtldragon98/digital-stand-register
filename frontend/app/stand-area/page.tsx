"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import StandDetails from "@/components/stand/StandDetails";
import { fetchApi } from "@/lib/api";
import { AuthUser, canEdit, getUser, isAdmin } from "@/lib/auth";

const ORDER=["READY","HYDROTEST","GAUGING","PENDING","YET_TO_READY"];
const LABEL:Record<string,string>={READY:"Ready",HYDROTEST:"Hydrotest",GAUGING:"Gauging",PENDING:"Pending",YET_TO_READY:"Yet to Ready"};
const COLORS:Record<string,string>={READY:"border-emerald-700/70 bg-emerald-950/20 text-emerald-300",HYDROTEST:"border-blue-700/70 bg-blue-950/20 text-blue-300",GAUGING:"border-violet-700/70 bg-violet-950/20 text-violet-300",PENDING:"border-orange-700/70 bg-orange-950/20 text-orange-300",YET_TO_READY:"border-slate-700 bg-slate-900/40 text-slate-300"};
const NEXT:Record<string,string|undefined>={YET_TO_READY:"PENDING",PENDING:"GAUGING",GAUGING:"HYDROTEST",HYDROTEST:"READY"};
type Stand={id:number;code:string;current_status:string;lifetime_hours:number};

export default function StandAreaPage(){
  const [stands,setStands]=useState<Stand[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [saving,setSaving]=useState(false);
  const [selected,setSelected]=useState<any>(null);
  const [user,setUser]=useState<AuthUser|null>(null);

  const load=async()=>{try{setError("");setStands(await fetchApi("/stands/"));}catch(e){setError(e instanceof Error?e.message:"Could not load stands");}finally{setLoading(false)}};
  useEffect(()=>{setUser(getUser());load()},[]);
  const groups=useMemo(()=>Object.fromEntries(ORDER.map(s=>[s,stands.filter(x=>x.current_status===s).sort((a,b)=>a.code.localeCompare(b.code,undefined,{numeric:true}))])),[stands]);

  async function advance(stand:Stand){
    if(!canEdit(user)){setError("Sign in as Admin or Operator to update stand readiness.");return;}
    const target=NEXT[stand.current_status];if(!target)return;
    let who=user?.username||"";let remarks:string|null=null;
    if(["GAUGING","HYDROTEST","READY"].includes(target)){
      who=window.prompt(`Who completed ${LABEL[target]} for ${stand.code}?`,user?.username||"")?.trim()||"";
      if(!who)return;
      remarks=window.prompt("Remarks (optional)")?.trim()||null;
    }
    setSaving(true);
    try{await fetchApi("/operations/stands/status",{method:"POST",body:JSON.stringify({stand_code:stand.code,status:target,updated_by:who,remarks})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Update failed");}
    finally{setSaving(false)}
  }

  async function addStand(){
    if(!isAdmin(user)){setError("Admin access is required to add a new stand.");return;}
    const code=window.prompt("New stand code (example: 4E)")?.trim();
    if(!code)return;
    const lifeText=window.prompt("Existing life hours, if any (leave blank for 0)","0")?.trim()||"0";
    const life=Number(lifeText);
    if(Number.isNaN(life)||life<0){setError("Life hours must be 0 or more.");return;}
    try{await fetchApi("/stands/",{method:"POST",body:JSON.stringify({code,initial_life_hours:life})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not add stand");}
  }

  async function openStand(stand:Stand){try{setSelected(await fetchApi(`/stands/${stand.id}`));}catch(e){setError(e instanceof Error?e.message:"Could not load stand")}}

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Stand Area" />
    <main className="p-3 md:p-4 flex-1 space-y-2 overflow-hidden">
      <div className="flex items-center justify-between gap-3">
        <div><h1 className="text-lg font-bold">Stand Preparation</h1><p className="text-xs text-slate-400">Yet to Ready → Pending → Gauging → Hydrotest → Ready</p></div>
        <div className="flex gap-2">
          {isAdmin(user)&&<button onClick={addStand} className="text-xs px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 font-semibold">+ New Stand</button>}
          <button onClick={load} className="text-xs px-3 py-1.5 rounded border border-slate-700">Refresh</button>
        </div>
      </div>
      {!user&&<div className="text-[11px] text-slate-500">Viewer mode · Sign in to make changes.</div>}
      {error&&<div className="text-xs p-2 rounded border border-red-800 text-red-300">{error}</div>}
      {loading?<div className="text-sm text-slate-400">Loading...</div>:<div className="space-y-1.5">
        {ORDER.map(status=><section key={status} className={`border rounded-xl p-2 ${COLORS[status]}`}>
          <div className="grid gap-1.5 min-h-[72px]" style={{gridTemplateColumns:"repeat(16,minmax(0,1fr))"}}>
            <div className="col-span-2 rounded-lg bg-black/10 px-2 flex flex-col justify-center"><div className="font-black uppercase text-xs">{LABEL[status]}</div><div className="text-[10px] opacity-70">{groups[status].length} stands</div></div>
            {groups[status].map((stand:Stand)=><div key={stand.id} className="min-w-0 rounded-lg border border-white/15 bg-slate-950/35 px-1.5 py-1.5 flex flex-col justify-between">
              <button onClick={()=>openStand(stand)} className="text-left min-w-0"><div className="font-black text-white text-sm truncate">{stand.code}</div><div className="text-[9px] text-slate-400 truncate">{Number(stand.lifetime_hours||0).toFixed(1)} h</div></button>
              {canEdit(user)&&NEXT[status]&&<button disabled={saving} onClick={()=>advance(stand)} className="mt-1 text-[9px] rounded border border-white/20 py-1 truncate hover:bg-white/10">→ {LABEL[NEXT[status]!]}</button>}
            </div>)}
          </div>
        </section>)}
      </div>}
    </main>
    {selected&&<div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-5" onClick={()=>setSelected(null)}><div className="max-w-3xl w-full max-h-[88vh] overflow-auto rounded-xl bg-slate-950 border border-slate-700 p-4" onClick={e=>e.stopPropagation()}><div className="flex justify-end mb-2"><button onClick={()=>setSelected(null)} className="text-xs border border-slate-700 px-3 py-1 rounded">Close</button></div><StandDetails stand={selected}/></div></div>}
  </div>;
}
