"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Item = {
  id:number; name:string; quantity:number; minimum_quantity:number; location:string; is_active:boolean;
  expected_life_hours?:number|null; observed_avg_life_hours?:number|null; reliability_pct?:number|null; availability_pct?:number|null;
  criticality?:string|null; used_at?:string|null;
};

type FormState = {
  name:string; quantity:number; used_at:string; expected_life_hours:string; reliability_pct:string; availability_pct:string; criticality:string;
};

const blank:FormState={name:"",quantity:0,used_at:"",expected_life_hours:"",reliability_pct:"",availability_pct:"",criticality:"MEDIUM"};
const numOrNull=(v:string)=>v.trim()===""?null:Number(v);
const life=(h?:number|null)=>h==null?"—":h>=24?`${(h/24).toFixed(1)} d`:`${h.toFixed(0)} h`;

export default function InventoryPage(){
  const [items,setItems]=useState<Item[]>([]);
  const [form,setForm]=useState<FormState>(blank);
  const [showAdd,setShowAdd]=useState(false);
  const [error,setError]=useState("");
  const [query,setQuery]=useState("");

  const load=async()=>{try{setError("");setItems(await fetchApi("/inventory/"));}catch(e){setError(e instanceof Error?e.message:"Could not load spare life data")}};
  useEffect(()=>{load()},[]);

  const shown=useMemo(()=>items.filter(i=>`${i.name} ${i.used_at||""} ${i.criticality||""}`.toLowerCase().includes(query.toLowerCase())),[items,query]);

  async function addSpare(e:React.FormEvent){
    e.preventDefault();
    try{
      await fetchApi("/inventory/",{method:"POST",body:JSON.stringify({
        name:form.name.trim(),quantity:form.quantity,minimum_quantity:0,location:"Store",
        expected_life_hours:numOrNull(form.expected_life_hours),observed_avg_life_hours:null,reliability_pct:numOrNull(form.reliability_pct),
        availability_pct:numOrNull(form.availability_pct),criticality:form.criticality,used_at:form.used_at||null
      })});
      setForm(blank);setShowAdd(false);await load();
    }catch(e){setError(e instanceof Error?e.message:"Could not add spare")}
  }

  async function setQty(item:Item){
    const raw=window.prompt(`New quantity for ${item.name}`,String(item.quantity)); if(raw===null)return;
    const qty=Number(raw); if(!Number.isFinite(qty)||qty<0)return;
    const operator=window.prompt("Updated by")?.trim(); if(!operator)return;
    const reason=window.prompt("Reason")?.trim()||"Stock update";
    try{await fetchApi(`/inventory/${item.id}/set-quantity`,{method:"POST",body:JSON.stringify({quantity:Math.floor(qty),operator,reason})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not update quantity")}
  }

  async function edit(item:Item){
    const expected=window.prompt("Expected life hours (blank = unknown)",item.expected_life_hours?.toString()||""); if(expected===null)return;
    const reliability=window.prompt("Reliability % (blank = unknown)",item.reliability_pct?.toString()||""); if(reliability===null)return;
    const availability=window.prompt("Availability % (blank = unknown)",item.availability_pct?.toString()||""); if(availability===null)return;
    const criticality=window.prompt("Criticality: LOW / MEDIUM / HIGH / CRITICAL",item.criticality||"MEDIUM")?.trim().toUpperCase(); if(!criticality)return;
    const usedAt=window.prompt("Used at / component / stand area",item.used_at||""); if(usedAt===null)return;
    try{await fetchApi(`/inventory/${item.id}`,{method:"PATCH",body:JSON.stringify({expected_life_hours:numOrNull(expected),reliability_pct:numOrNull(reliability),availability_pct:numOrNull(availability),criticality,used_at:usedAt||null})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not update spare")}
  }

  async function archive(item:Item){
    if(!window.confirm(`Remove ${item.name} from active spare list?`))return;
    try{await fetchApi(`/inventory/${item.id}`,{method:"DELETE"});await load();}catch(e){setError(e instanceof Error?e.message:"Could not remove spare")}
  }

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Spare Life" />
    <main className="p-4 md:p-5 flex-1 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div><h1 className="text-xl font-bold text-white">Spare Life Register</h1><p className="text-xs text-slate-400">Life, reliability, availability and criticality. Unknown values stay blank until evidence exists.</p></div>
        <button onClick={()=>setShowAdd(v=>!v)} className="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-sm font-semibold">{showAdd?"Close":"+ Add Spare"}</button>
      </div>

      <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search spare / used at / criticality" className="w-full max-w-md rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm"/>

      {showAdd&&<form onSubmit={addSpare} className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-2 border border-slate-700 rounded-lg p-3 bg-slate-900/50 text-xs">
        <input className="input-class col-span-2" placeholder="Spare name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/>
        <input className="input-class" placeholder="Used at" value={form.used_at} onChange={e=>setForm({...form,used_at:e.target.value})}/>
        <input className="input-class" type="number" min="0" placeholder="Qty" value={form.quantity} onChange={e=>setForm({...form,quantity:Number(e.target.value)})}/>
        <input className="input-class" type="number" min="0" placeholder="Expected life h" value={form.expected_life_hours} onChange={e=>setForm({...form,expected_life_hours:e.target.value})}/>
        <input className="input-class" type="number" min="0" max="100" placeholder="Reliability %" value={form.reliability_pct} onChange={e=>setForm({...form,reliability_pct:e.target.value})}/>
        <input className="input-class" type="number" min="0" max="100" placeholder="Availability %" value={form.availability_pct} onChange={e=>setForm({...form,availability_pct:e.target.value})}/>
        <select className="input-class" value={form.criticality} onChange={e=>setForm({...form,criticality:e.target.value})}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select>
        <button className="px-3 py-2 rounded bg-emerald-600 font-semibold">Save</button>
      </form>}

      {error&&<div className="text-red-300 text-sm">{error}</div>}
      <div className="overflow-auto border border-slate-700 rounded-lg bg-slate-950/30 max-h-[calc(100vh-210px)]">
        <table className="w-full min-w-[1020px] text-xs border-collapse">
          <thead className="sticky top-0 bg-slate-800 text-slate-200"><tr>
            <th className="border border-slate-700 px-2 py-2 text-left">Spare</th><th className="border border-slate-700 px-2 py-2 text-left">Used At</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Qty</th><th className="border border-slate-700 px-2 py-2 text-center">Expected Life</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Observed Avg</th><th className="border border-slate-700 px-2 py-2 text-center">Reliability</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Availability</th><th className="border border-slate-700 px-2 py-2 text-center">Criticality</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Action</th>
          </tr></thead>
          <tbody>{shown.map(item=><tr key={item.id} className="even:bg-slate-900/50 hover:bg-slate-800/60">
            <td className="border border-slate-700 px-2 py-2 font-semibold text-white">{item.name}</td><td className="border border-slate-700 px-2 py-2">{item.used_at||"—"}</td>
            <td className="border border-slate-700 px-2 py-2 text-center font-bold">{item.quantity}</td><td className="border border-slate-700 px-2 py-2 text-center">{life(item.expected_life_hours)}</td>
            <td className="border border-slate-700 px-2 py-2 text-center">{life(item.observed_avg_life_hours)}</td><td className="border border-slate-700 px-2 py-2 text-center">{item.reliability_pct==null?"—":`${item.reliability_pct.toFixed(1)}%`}</td>
            <td className="border border-slate-700 px-2 py-2 text-center">{item.availability_pct==null?"—":`${item.availability_pct.toFixed(1)}%`}</td><td className="border border-slate-700 px-2 py-2 text-center font-bold">{item.criticality||"MEDIUM"}</td>
            <td className="border border-slate-700 px-2 py-1"><div className="flex justify-center gap-1"><button onClick={()=>setQty(item)} className="px-2 py-1 rounded border border-blue-700 text-blue-300">Qty</button><button onClick={()=>edit(item)} className="px-2 py-1 rounded border border-slate-600 text-slate-200">Edit</button><button onClick={()=>archive(item)} className="px-2 py-1 rounded border border-red-800 text-red-300">Remove</button></div></td>
          </tr>)}</tbody>
        </table>
      </div>
    </main>
  </div>;
}
