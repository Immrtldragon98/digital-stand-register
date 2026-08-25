"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Guide={id:number;code:string;condition:string;current_status:string;current_position_id:number|null;lifetime_hours:number;condition_notes?:string|null};
type Pos={id:number;label:string};

export default function EntryGuidesPage(){
  const [guides,setGuides]=useState<Guide[]>([]); const [positions,setPositions]=useState<Pos[]>([]);
  const [code,setCode]=useState(""); const [condition,setCondition]=useState("OLD"); const [notes,setNotes]=useState("");
  const [installGuide,setInstallGuide]=useState(""); const [installPos,setInstallPos]=useState("");
  const [error,setError]=useState(""); const [message,setMessage]=useState(""); const [loading,setLoading]=useState(true);

  const load=async()=>{try{setError("");const [g,l]=await Promise.all([fetchApi("/entry-guides/"),fetchApi("/dashboard/")]);setGuides(g);const p:Pos[]=[];l.forEach((line:any)=>line.positions?.forEach((x:any)=>{if([2,4,6,8,10].includes(x.position_number))p.push({id:x.id,label:`${line.name} - P${x.position_number}`})}));setPositions(p);}catch(e){setError(e instanceof Error?e.message:"Could not load entry guides");}finally{setLoading(false)}};
  useEffect(()=>{load()},[]);

  const ready=useMemo(()=>guides.filter(g=>g.current_status==="READY"),[guides]);
  const installed=useMemo(()=>guides.filter(g=>g.current_status==="INSTALLED"),[guides]);

  const add=async(e:React.FormEvent)=>{e.preventDefault();try{setError("");await fetchApi("/entry-guides/",{method:"POST",body:JSON.stringify({code:code.trim(),condition,notes:notes.trim()||null})});setCode("");setNotes("");setMessage("Entry guide added as Ready.");await load();}catch(e){setError(e instanceof Error?e.message:"Could not add guide")}};
  const install=async(e:React.FormEvent)=>{e.preventDefault();const who=window.prompt("Installed by / operator name")?.trim();if(!who)return;try{await fetchApi("/entry-guides/install",{method:"POST",body:JSON.stringify({guide_code:installGuide,position_id:Number(installPos),operator_name:who})});setMessage(`${installGuide} installed.`);setInstallGuide("");setInstallPos("");await load();}catch(e){setError(e instanceof Error?e.message:"Install failed")}};
  const remove=async(g:Guide)=>{const who=window.prompt(`Who removed ${g.code}?`)?.trim();if(!who)return;const reason=window.prompt("Why was it removed?")?.trim();if(!reason)return;try{await fetchApi("/entry-guides/remove",{method:"POST",body:JSON.stringify({guide_code:g.code,removed_by:who,removal_reason:reason})});setMessage(`${g.code} removed to Pending.`);await load();}catch(e){setError(e instanceof Error?e.message:"Remove failed")}};
  const markReady=async(g:Guide)=>{const who=window.prompt(`Who made ${g.code} ready?`)?.trim();if(!who)return;try{await fetchApi("/entry-guides/ready",{method:"POST",body:JSON.stringify({guide_code:g.code,updated_by:who})});setMessage(`${g.code} is Ready.`);await load();}catch(e){setError(e instanceof Error?e.message:"Update failed")}};

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Entry Guides" />
    <main className="p-4 md:p-5 flex-1 space-y-3">
      <div className="flex items-center justify-between"><div><h1 className="text-lg font-bold">Entry Guide Register</h1><p className="text-xs text-slate-400">Used only at positions 2, 4, 6, 8 and 10. Life is tracked automatically.</p></div><div className="text-xs text-slate-400">{installed.length} running · {ready.length} ready · {guides.length} total</div></div>
      {(error||message)&&<div className={`text-xs px-3 py-2 rounded border ${error?"border-red-800 text-red-300":"border-emerald-800 text-emerald-300"}`}>{error||message}</div>}

      <div className="grid xl:grid-cols-2 gap-3">
        <form onSubmit={add} className="border border-slate-800 rounded-xl bg-slate-900/40 p-3 grid grid-cols-[1fr_120px_1fr_auto] gap-2 items-end">
          <Field label="Guide ID"><input className="input-class" value={code} onChange={e=>setCode(e.target.value)} placeholder="EG-4-01" required/></Field>
          <Field label="New / Old"><select className="input-class" value={condition} onChange={e=>setCondition(e.target.value)}><option value="NEW">New</option><option value="OLD">Old</option></select></Field>
          <Field label="Remarks"><input className="input-class" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Optional"/></Field>
          <button className="h-[42px] px-4 rounded-lg bg-blue-600 font-semibold">Add</button>
        </form>

        <form onSubmit={install} className="border border-slate-800 rounded-xl bg-slate-900/40 p-3 grid grid-cols-[1fr_1fr_auto] gap-2 items-end">
          <Field label="Ready guide"><select className="input-class" value={installGuide} onChange={e=>setInstallGuide(e.target.value)} required><option value="">Select</option>{ready.map(g=><option key={g.id} value={g.code}>{g.code}</option>)}</select></Field>
          <Field label="Install at"><select className="input-class" value={installPos} onChange={e=>setInstallPos(e.target.value)} required><option value="">Select position</option>{positions.map(p=><option key={p.id} value={p.id}>{p.label}</option>)}</select></Field>
          <button className="h-[42px] px-4 rounded-lg bg-emerald-600 font-semibold">Install</button>
        </form>
      </div>

      {loading?<div className="text-sm text-slate-400">Loading...</div>:<div className="overflow-auto border border-slate-800 rounded-xl">
        <table className="w-full text-xs border-collapse">
          <thead className="bg-slate-900 text-slate-400"><tr><th className="p-2 text-left">Guide</th><th>New/Old</th><th>Status</th><th>Position ID</th><th>Life</th><th className="text-left">Remarks</th><th>Action</th></tr></thead>
          <tbody>{guides.map(g=><tr key={g.id} className="border-t border-slate-800 hover:bg-slate-900/50"><td className="p-2 font-bold text-white">{g.code}</td><td className="text-center">{g.condition}</td><td className="text-center"><span className={`px-2 py-1 rounded ${g.current_status==="INSTALLED"?"bg-cyan-950 text-cyan-300":g.current_status==="READY"?"bg-emerald-950 text-emerald-300":"bg-orange-950 text-orange-300"}`}>{g.current_status}</span></td><td className="text-center">{g.current_position_id??"—"}</td><td className="text-center">{Number(g.lifetime_hours||0).toFixed(1)} h</td><td className="p-2 text-slate-400">{g.condition_notes||"—"}</td><td className="p-2 text-center">{g.current_status==="INSTALLED"?<button onClick={()=>remove(g)} className="px-2 py-1 rounded border border-orange-700 text-orange-300">Remove</button>:g.current_status!=="READY"?<button onClick={()=>markReady(g)} className="px-2 py-1 rounded border border-emerald-700 text-emerald-300">Mark Ready</button>:<span className="text-slate-600">Ready</span>}</td></tr>)}</tbody>
        </table>
      </div>}
    </main>
  </div>;
}

function Field({label,children}:{label:string;children:React.ReactNode}){return <div><label className="block text-[10px] uppercase tracking-wide text-slate-500 mb-1">{label}</label>{children}</div>}
