"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import StandDetails from "@/components/stand/StandDetails";
import ComponentPreparationModal from "@/components/stand/ComponentPreparationModal";
import { fetchApi } from "@/lib/api";
import { AuthUser, canEdit, getUser, isAdmin } from "@/lib/auth";

const ORDER=["READY","HYDROTEST","GAUGING","PENDING","YET_TO_READY"];
const LABEL:Record<string,string>={READY:"Ready",HYDROTEST:"Hydrotest",GAUGING:"Gauging",PENDING:"Pending",YET_TO_READY:"Unstarted"};
const META:Record<string,{bar:string,text:string}>={READY:{bar:"bg-emerald-400",text:"text-emerald-300"},HYDROTEST:{bar:"bg-blue-400",text:"text-blue-300"},GAUGING:{bar:"bg-violet-400",text:"text-violet-300"},PENDING:{bar:"bg-amber-400",text:"text-amber-300"},YET_TO_READY:{bar:"bg-slate-500",text:"text-slate-400"}};
const NEXT:Record<string,string|undefined>={YET_TO_READY:"PENDING",GAUGING:"HYDROTEST",HYDROTEST:"READY"};
type Stand={id:number;code:string;current_status:string;lifetime_hours:number};

export default function StandAreaPage(){
  const [stands,setStands]=useState<Stand[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState("");const [saving,setSaving]=useState(false);const [selected,setSelected]=useState<any>(null);const [componentStand,setComponentStand]=useState<Stand|null>(null);const [user,setUser]=useState<AuthUser|null>(null);
  const load=async()=>{try{setError("");setStands(await fetchApi("/stands/"));}catch(e){setError(e instanceof Error?e.message:"Could not load stands");}finally{setLoading(false)}};
  useEffect(()=>{setUser(getUser());load()},[]);
  const groups=useMemo(()=>Object.fromEntries(ORDER.map(s=>[s,stands.filter(x=>x.current_status===s).sort((a,b)=>a.code.localeCompare(b.code,undefined,{numeric:true}))])),[stands]);
  async function advance(stand:Stand){if(!canEdit(user)){setError("Sign in as Admin or Operator to update stand readiness.");return;}if(stand.current_status==="PENDING"){setComponentStand(stand);return;}const target=NEXT[stand.current_status];if(!target)return;let who=user?.username||"";let remarks:string|null=null;if(["GAUGING","HYDROTEST","READY"].includes(target)){who=window.prompt(`Who completed ${LABEL[target]} for ${stand.code}?`,user?.username||"")?.trim()||"";if(!who)return;remarks=window.prompt("Remarks (optional)")?.trim()||null;}setSaving(true);try{await fetchApi("/operations/stands/status",{method:"POST",body:JSON.stringify({stand_code:stand.code,status:target,updated_by:who,remarks})});await load();}catch(e){setError(e instanceof Error?e.message:"Update failed");}finally{setSaving(false)}}
  async function addStand(){if(!isAdmin(user)){setError("Admin access is required to add a new stand.");return;}const code=window.prompt("New stand code (example: 4E)")?.trim();if(!code)return;const life=Number(window.prompt("Existing life hours, if any","0")||"0");if(Number.isNaN(life)||life<0){setError("Life hours must be 0 or more.");return;}try{await fetchApi("/stands/",{method:"POST",body:JSON.stringify({code,initial_life_hours:life})});await load();}catch(e){setError(e instanceof Error?e.message:"Could not add stand")}}
  async function openStand(stand:Stand){try{setSelected(await fetchApi(`/stands/${stand.id}`));}catch(e){setError(e instanceof Error?e.message:"Could not load stand")}}

  return <div className="dsr-page"><Header title="Stand Area"/><main className="dsr-main"><div className="full-bleed space-y-3">
    <div className="dsr-section-head"><div><div className="dsr-kicker">Workshop flow</div><h1 className="dsr-title">Stand Preparation</h1><p className="dsr-subtitle">Pending → Components → Gauging → Hydrotest → Ready</p></div><div className="flex gap-2">{isAdmin(user)&&<button onClick={addStand} className="dsr-btn-primary">+ New Stand</button>}<button onClick={load} className="dsr-btn">Refresh</button></div></div>
    {!user&&<div className="dsr-chip">Viewer mode · sign in to update stands</div>}
    {error&&<div className="rounded-lg border border-red-900 bg-red-950/25 p-3 text-xs text-red-300">{error}</div>}
    {loading?<div className="dsr-empty">Loading stand preparation...</div>:<div className="grid gap-3 xl:grid-cols-5 md:grid-cols-2 grid-cols-1">
      {ORDER.map(status=><section key={status} className="mechanical-panel overflow-hidden"><div className="h-1 w-full bg-slate-800"><div className={`h-full ${META[status].bar}`} style={{width:`${Math.min(100,Math.max(10,groups[status].length*12))}%`}}/></div><div className="px-3 py-3 border-b border-slate-800 flex items-center justify-between"><div><div className={`text-[10px] uppercase tracking-[.16em] font-black ${META[status].text}`}>{LABEL[status]}</div><div className="text-[10px] text-slate-600 mt-1">{groups[status].length} stands</div></div></div><div className="p-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-2 xl:grid-cols-2 gap-2 min-h-[110px]">{groups[status].map((stand:Stand)=><div key={stand.id} className="rounded-lg border border-slate-800 bg-[#0a0f15] p-2 min-w-0"><button onClick={()=>openStand(stand)} className="w-full text-left"><div className="text-base font-black text-white truncate">{stand.code}</div><div className="metric-label mt-1">Total Life</div><div className="text-[10px] text-slate-400">{Number(stand.lifetime_hours||0).toFixed(0)} h</div></button>{canEdit(user)&&status==="PENDING"&&<button disabled={saving} onClick={()=>advance(stand)} className="mt-2 w-full dsr-btn-primary !px-2 !py-1.5 !text-[9px]">Components →</button>}{canEdit(user)&&status!=="PENDING"&&NEXT[status]&&<button disabled={saving} onClick={()=>advance(stand)} className="mt-2 w-full dsr-btn !px-2 !py-1.5 !text-[9px]">{LABEL[NEXT[status]!]} →</button>}</div>)}{groups[status].length===0&&<div className="col-span-full dsr-empty !p-4">No stands</div>}</div></section>)}
    </div>}
  </div></main>
  {selected&&<div className="fixed inset-0 z-50 bg-black/75 flex items-end md:items-center justify-center md:p-5" onClick={()=>setSelected(null)}><div className="w-full md:max-w-4xl max-h-[92vh] overflow-auto rounded-t-2xl md:rounded-xl bg-[#0b1016] border border-slate-700 p-4" onClick={e=>e.stopPropagation()}><div className="flex justify-end mb-2"><button onClick={()=>setSelected(null)} className="dsr-btn">Close</button></div><StandDetails stand={selected}/></div></div>}
  {componentStand&&<ComponentPreparationModal stand={componentStand} onClose={()=>setComponentStand(null)} onComplete={load}/>} 
  </div>;
}
