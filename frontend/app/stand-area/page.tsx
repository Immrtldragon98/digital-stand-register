"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import StandDetails from "@/components/stand/StandDetails";
import ComponentPreparationModal from "@/components/stand/ComponentPreparationModal";
import { fetchApi } from "@/lib/api";
import { AuthUser, canEdit, getUser, isAdmin } from "@/lib/auth";

const ORDER=["READY","HYDROTEST","GAUGING","PENDING","YET_TO_READY"];
const LABEL:Record<string,string>={READY:"Ready",HYDROTEST:"Hydrotest",GAUGING:"Gauging",PENDING:"Pending",YET_TO_READY:"Unstarted"};
const STYLE:Record<string,{row:string,label:string,card:string,button:string,dot:string}>={
  READY:{row:"border-emerald-800/70 bg-emerald-950/18",label:"text-emerald-300",card:"border-emerald-900/60 bg-emerald-950/16 hover:border-emerald-600",button:"border-emerald-700 text-emerald-200 hover:bg-emerald-950/50",dot:"bg-emerald-400"},
  HYDROTEST:{row:"border-blue-800/70 bg-blue-950/18",label:"text-blue-300",card:"border-blue-900/60 bg-blue-950/16 hover:border-blue-600",button:"border-blue-700 text-blue-200 hover:bg-blue-950/50",dot:"bg-blue-400"},
  GAUGING:{row:"border-violet-800/70 bg-violet-950/18",label:"text-violet-300",card:"border-violet-900/60 bg-violet-950/16 hover:border-violet-600",button:"border-violet-700 text-violet-200 hover:bg-violet-950/50",dot:"bg-violet-400"},
  PENDING:{row:"border-amber-800/70 bg-amber-950/18",label:"text-amber-300",card:"border-amber-900/60 bg-amber-950/16 hover:border-amber-600",button:"border-amber-700 text-amber-200 hover:bg-amber-950/50",dot:"bg-amber-400"},
  YET_TO_READY:{row:"border-slate-700 bg-slate-900/35",label:"text-slate-300",card:"border-slate-700 bg-slate-950/45 hover:border-slate-500",button:"border-slate-600 text-slate-200 hover:bg-slate-800",dot:"bg-slate-500"},
};
const NEXT:Record<string,string|undefined>={YET_TO_READY:"PENDING",GAUGING:"HYDROTEST",HYDROTEST:"READY"};
type Stand={id:number;code:string;current_status:string;lifetime_hours:number};

export default function StandAreaPage(){
  const [stands,setStands]=useState<Stand[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState("");const [saving,setSaving]=useState(false);const [selected,setSelected]=useState<any>(null);const [componentStand,setComponentStand]=useState<Stand|null>(null);const [user,setUser]=useState<AuthUser|null>(null);
  const load=async()=>{try{setError("");setStands(await fetchApi("/stands/"));}catch(e){setError(e instanceof Error?e.message:"Could not load stands");}finally{setLoading(false)}};
  useEffect(()=>{setUser(getUser());load()},[]);
  const groups=useMemo(()=>Object.fromEntries(ORDER.map(s=>[s,stands.filter(x=>x.current_status===s).sort((a,b)=>a.code.localeCompare(b.code,undefined,{numeric:true}))])),[stands]);

  async function advance(stand:Stand){
    if(!canEdit(user)){setError("Sign in as Admin or Operator to update stand readiness.");return;}
    if(stand.current_status==="PENDING"){setComponentStand(stand);return;}
    const target=NEXT[stand.current_status];if(!target)return;
    let who=user?.username||"";let remarks:string|null=null;
    if(["GAUGING","HYDROTEST","READY"].includes(target)){
      who=window.prompt(`Who completed ${LABEL[target]} for ${stand.code}?`,user?.username||"")?.trim()||"";if(!who)return;
      remarks=window.prompt("Remarks (optional)")?.trim()||null;
    }
    setSaving(true);
    try{await fetchApi("/operations/stands/status",{method:"POST",body:JSON.stringify({stand_code:stand.code,status:target,updated_by:who,remarks})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Update failed");}
    finally{setSaving(false)}
  }

  async function addStand(){
    if(!isAdmin(user)){setError("Admin access is required to add a new stand.");return;}
    const code=window.prompt("New stand code (example: 4E)")?.trim();if(!code)return;
    const life=Number(window.prompt("Existing life hours, if any","0")||"0");
    if(Number.isNaN(life)||life<0){setError("Life hours must be 0 or more.");return;}
    try{await fetchApi("/stands/",{method:"POST",body:JSON.stringify({code,initial_life_hours:life})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not add stand")}
  }

  async function openStand(stand:Stand){try{setSelected(await fetchApi(`/stands/${stand.id}`));}catch(e){setError(e instanceof Error?e.message:"Could not load stand")}}

  return <div className="dsr-page">
    <Header title="Stand Area"/>
    <main className="dsr-main">
      <div className="full-bleed space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-white">Stand Preparation</h1>
            <p className="text-sm text-slate-400 mt-1">Pending → Components → Gauging → Hydrotest → Ready</p>
          </div>
          <div className="flex gap-2">
            {isAdmin(user)&&<button onClick={addStand} className="dsr-btn-primary">+ New Stand</button>}
            <button onClick={load} className="dsr-btn">Refresh</button>
          </div>
        </div>

        {!user&&<div className="rounded-lg border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-400">Viewer mode · Sign in to update stands.</div>}
        {error&&<div className="rounded-lg border border-red-900 bg-red-950/25 p-3 text-sm text-red-300">{error}</div>}

        {loading?<div className="dsr-empty">Loading stand preparation...</div>:<div className="space-y-3">
          {ORDER.map(status=>{
            const style=STYLE[status];
            return <section key={status} className={`rounded-xl border ${style.row} p-3`}>
              <div className="grid grid-cols-1 md:grid-cols-[150px_1fr] gap-3 items-start">
                <div className="md:min-h-[86px] rounded-lg bg-black/10 px-3 py-3 flex md:flex-col items-center md:items-start justify-between md:justify-center">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`}/>
                    <span className={`text-sm font-bold ${style.label}`}>{LABEL[status]}</span>
                  </div>
                  <div className="text-xs text-slate-400 md:mt-1">{groups[status].length} stands</div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 2xl:grid-cols-10 gap-2 min-h-[86px]">
                  {groups[status].map((stand:Stand)=><div key={stand.id} className={`rounded-lg border ${style.card} p-2.5 min-w-0 transition-colors`}>
                    <button onClick={()=>openStand(stand)} className="w-full text-left">
                      <div className="text-lg font-bold text-white truncate">{stand.code}</div>
                      <div className="text-xs text-slate-400 mt-1">Life {Number(stand.lifetime_hours||0).toFixed(0)} h</div>
                    </button>
                    {canEdit(user)&&status==="PENDING"&&<button disabled={saving} onClick={()=>advance(stand)} className={`mt-2 w-full rounded-md border px-2 py-1.5 text-xs font-medium ${style.button}`}>Components</button>}
                    {canEdit(user)&&status!=="PENDING"&&NEXT[status]&&<button disabled={saving} onClick={()=>advance(stand)} className={`mt-2 w-full rounded-md border px-2 py-1.5 text-xs font-medium ${style.button}`}>→ {LABEL[NEXT[status]!]}</button>}
                  </div>)}
                  {groups[status].length===0&&<div className="col-span-full flex items-center justify-center rounded-lg border border-dashed border-slate-700/60 px-3 py-5 text-sm text-slate-500">No stands</div>}
                </div>
              </div>
            </section>
          })}
        </div>}
      </div>
    </main>

    {selected&&<div className="fixed inset-0 z-50 bg-black/70 flex items-end md:items-center justify-center md:p-5" onClick={()=>setSelected(null)}><div className="w-full md:max-w-4xl max-h-[92vh] overflow-auto rounded-t-2xl md:rounded-xl bg-[#0d131b] border border-slate-700 p-4" onClick={e=>e.stopPropagation()}><div className="flex justify-end mb-2"><button onClick={()=>setSelected(null)} className="dsr-btn">Close</button></div><StandDetails stand={selected}/></div></div>}
    {componentStand&&<ComponentPreparationModal stand={componentStand} onClose={()=>setComponentStand(null)} onComplete={load}/>} 
  </div>;
}
