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
  name:string; used_at:string; quantity:string; minimum_quantity:string; expected_life_hours:string; observed_avg_life_hours:string;
};

const blank:FormState={name:"",used_at:"",quantity:"0",minimum_quantity:"0",expected_life_hours:"",observed_avg_life_hours:""};
const n=(v:string)=>Math.max(0,Number(v)||0);
const optional=(v:string)=>v.trim()===""?null:Math.max(0,Number(v));
const life=(h?:number|null)=>h==null?"—":h>=24?`${(h/24).toFixed(1)} d`:`${h.toFixed(0)} h`;
const pct=(v?:number|null)=>v==null?"—":`${v.toFixed(1)}%`;
const criticalRank:Record<string,number>={CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3,UNASSESSED:4};
const badge=(v?:string|null)=>v==="CRITICAL"?"border-red-800 bg-red-950/40 text-red-300":v==="HIGH"?"border-orange-800 bg-orange-950/30 text-orange-300":v==="MEDIUM"?"border-amber-800 bg-amber-950/20 text-amber-300":v==="LOW"?"border-emerald-800 bg-emerald-950/20 text-emerald-300":"border-slate-700 bg-slate-900 text-slate-400";

export default function InventoryPage(){
  const [items,setItems]=useState<Item[]>([]);
  const [form,setForm]=useState<FormState>(blank);
  const [editing,setEditing]=useState<Item|null>(null);
  const [showForm,setShowForm]=useState(false);
  const [error,setError]=useState("");
  const [query,setQuery]=useState("");
  const [sort,setSort]=useState<"AZ"|"CRITICAL"|"LOW_STOCK">("AZ");
  const [saving,setSaving]=useState(false);

  const load=async()=>{try{setError("");setItems(await fetchApi("/inventory/"));}catch(e){setError(e instanceof Error?e.message:"Could not load spare life data")}};
  useEffect(()=>{load()},[]);

  const shown=useMemo(()=>{
    const filtered=items.filter(i=>`${i.name} ${i.used_at||""} ${i.criticality||""}`.toLowerCase().includes(query.toLowerCase()));
    return [...filtered].sort((a,b)=>{
      if(sort==="CRITICAL") return (criticalRank[a.criticality||"UNASSESSED"]??9)-(criticalRank[b.criticality||"UNASSESSED"]??9)||a.name.localeCompare(b.name,undefined,{numeric:true});
      if(sort==="LOW_STOCK") return (a.availability_pct??999)-(b.availability_pct??999)||a.name.localeCompare(b.name,undefined,{numeric:true});
      return a.name.localeCompare(b.name,undefined,{numeric:true});
    });
  },[items,query,sort]);

  function openAdd(){setEditing(null);setForm(blank);setShowForm(true);}
  function openEdit(item:Item){setEditing(item);setForm({name:item.name,used_at:item.used_at||"",quantity:String(item.quantity),minimum_quantity:String(item.minimum_quantity||0),expected_life_hours:item.expected_life_hours?.toString()||"",observed_avg_life_hours:item.observed_avg_life_hours?.toString()||""});setShowForm(true);}

  async function saveSpare(e:React.FormEvent){
    e.preventDefault();setSaving(true);setError("");
    try{
      const payload={name:form.name.trim(),used_at:form.used_at.trim()||null,minimum_quantity:Math.floor(n(form.minimum_quantity)),expected_life_hours:optional(form.expected_life_hours),observed_avg_life_hours:optional(form.observed_avg_life_hours),location:"Store"};
      if(editing){
        await fetchApi(`/inventory/${editing.id}`,{method:"PATCH",body:JSON.stringify(payload)});
        const newQty=Math.floor(n(form.quantity));
        if(newQty!==editing.quantity){
          const operator=window.prompt("Updated by")?.trim();
          if(!operator) throw new Error("Quantity update cancelled because 'Updated by' was not entered.");
          await fetchApi(`/inventory/${editing.id}/set-quantity`,{method:"POST",body:JSON.stringify({quantity:newQty,operator,reason:"Spare register update"})});
        }
      }else{
        await fetchApi("/inventory/",{method:"POST",body:JSON.stringify({...payload,quantity:Math.floor(n(form.quantity)),remarks:null,reliability_pct:null,availability_pct:null,criticality:"UNASSESSED"})});
      }
      setShowForm(false);setEditing(null);setForm(blank);await load();
    }catch(e){setError(e instanceof Error?e.message:"Could not save spare")}finally{setSaving(false)}
  }

  async function quickQty(item:Item){
    const raw=window.prompt(`Store quantity for ${item.name}`,String(item.quantity));if(raw===null)return;
    const qty=Math.floor(Number(raw));if(!Number.isFinite(qty)||qty<0)return;
    const operator=window.prompt("Updated by")?.trim();if(!operator)return;
    try{await fetchApi(`/inventory/${item.id}/set-quantity`,{method:"POST",body:JSON.stringify({quantity:qty,operator,reason:"Store quantity update"})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not update quantity")}
  }

  async function archive(item:Item){if(!window.confirm(`Remove ${item.name} from active spare list?`))return;try{await fetchApi(`/inventory/${item.id}`,{method:"DELETE"});await load();}catch(e){setError(e instanceof Error?e.message:"Could not remove spare")}}

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Spare Life" />
    <main className="p-4 md:p-5 flex-1 space-y-3">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div><h1 className="text-xl font-bold text-white">Spare Life Register</h1><p className="text-xs text-slate-400 mt-1">Enter only plant facts. Availability, reliability and planning criticality are calculated automatically.</p></div>
        <button onClick={openAdd} className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-sm font-semibold">+ Add Spare</button>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3"><div className="font-bold text-white">Availability</div><div className="text-slate-500 mt-1">Store Qty ÷ Required Qty × 100</div></div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3"><div className="font-bold text-white">Reliability</div><div className="text-slate-500 mt-1">Observed Avg Life ÷ Expected Life × 100</div></div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/45 p-3"><div className="font-bold text-white">Criticality</div><div className="text-slate-500 mt-1">Calculated from the weaker of stock coverage and life performance.</div></div>
      </section>

      <div className="flex flex-col md:flex-row gap-2 md:items-center md:justify-between">
        <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search spare / used at" className="w-full md:max-w-md rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm"/>
        <select value={sort} onChange={e=>setSort(e.target.value as any)} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-xs"><option value="AZ">Sort: A → Z</option><option value="CRITICAL">Sort: Critical first</option><option value="LOW_STOCK">Sort: Lowest availability</option></select>
      </div>

      {showForm&&<form onSubmit={saveSpare} className="rounded-xl border border-blue-900/60 bg-slate-900/70 p-4">
        <div className="flex items-center justify-between mb-3"><div><div className="font-bold text-white">{editing?`Edit ${editing.name}`:"Add Spare"}</div><div className="text-[11px] text-slate-500">Enter source values only. Calculated fields update after save.</div></div><button type="button" onClick={()=>setShowForm(false)} className="text-xs px-3 py-1 rounded border border-slate-700">Close</button></div>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2 text-xs">
          <label className="col-span-2"><span className="text-slate-500">Spare name</span><input className="input-class mt-1 w-full" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required/></label>
          <label><span className="text-slate-500">Used at</span><input className="input-class mt-1 w-full" value={form.used_at} onChange={e=>setForm({...form,used_at:e.target.value})}/></label>
          <label><span className="text-slate-500">Store Qty</span><input className="input-class mt-1 w-full" type="number" min="0" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></label>
          <label><span className="text-slate-500">Required Qty</span><input className="input-class mt-1 w-full" type="number" min="0" value={form.minimum_quantity} onChange={e=>setForm({...form,minimum_quantity:e.target.value})}/></label>
          <label><span className="text-slate-500">Expected Life (h)</span><input className="input-class mt-1 w-full" type="number" min="0" value={form.expected_life_hours} onChange={e=>setForm({...form,expected_life_hours:e.target.value})}/></label>
          <label><span className="text-slate-500">Observed Avg Life (h)</span><input className="input-class mt-1 w-full" type="number" min="0" value={form.observed_avg_life_hours} onChange={e=>setForm({...form,observed_avg_life_hours:e.target.value})}/></label>
          <div className="col-span-2 md:col-span-3 xl:col-span-5 text-[10px] text-slate-500 flex items-center">Observed Avg can stay blank now; later it can come from actual stand/component history.</div>
          <button disabled={saving} className="rounded bg-emerald-600 hover:bg-emerald-500 px-4 py-2 font-semibold disabled:opacity-40">{saving?"Saving...":"Save"}</button>
        </div>
      </form>}

      {error&&<div className="rounded border border-red-900 bg-red-950/30 p-2 text-red-300 text-sm">{error}</div>}

      <div className="overflow-auto border border-slate-700 rounded-xl bg-slate-950/30 max-h-[calc(100vh-300px)]">
        <table className="w-full min-w-[1120px] text-xs border-collapse">
          <thead className="sticky top-0 z-10 bg-slate-800 text-slate-200"><tr>
            <th className="border border-slate-700 px-2 py-2 text-left">Spare</th><th className="border border-slate-700 px-2 py-2 text-left">Used At</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Store Qty</th><th className="border border-slate-700 px-2 py-2 text-center">Required Qty</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Availability</th><th className="border border-slate-700 px-2 py-2 text-center">Expected Life</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Observed Avg</th><th className="border border-slate-700 px-2 py-2 text-center">Reliability</th>
            <th className="border border-slate-700 px-2 py-2 text-center">Criticality</th><th className="border border-slate-700 px-2 py-2 text-center">Action</th>
          </tr></thead>
          <tbody>{shown.map(item=><tr key={item.id} className="even:bg-slate-900/45 hover:bg-slate-800/60">
            <td className="border border-slate-700 px-2 py-2 font-semibold text-white">{item.name}</td><td className="border border-slate-700 px-2 py-2">{item.used_at||"—"}</td>
            <td className="border border-slate-700 px-2 py-2 text-center font-black text-white">{item.quantity}</td><td className="border border-slate-700 px-2 py-2 text-center">{item.minimum_quantity||"—"}</td>
            <td className="border border-slate-700 px-2 py-2 text-center font-semibold">{pct(item.availability_pct)}</td><td className="border border-slate-700 px-2 py-2 text-center">{life(item.expected_life_hours)}</td>
            <td className="border border-slate-700 px-2 py-2 text-center">{life(item.observed_avg_life_hours)}</td><td className="border border-slate-700 px-2 py-2 text-center font-semibold">{pct(item.reliability_pct)}</td>
            <td className="border border-slate-700 px-2 py-2 text-center"><span className={`inline-flex rounded border px-2 py-1 text-[10px] font-bold ${badge(item.criticality)}`}>{item.criticality||"UNASSESSED"}</span></td>
            <td className="border border-slate-700 px-2 py-1"><div className="flex justify-center gap-1"><button onClick={()=>quickQty(item)} className="px-2 py-1 rounded border border-blue-700 text-blue-300">Qty</button><button onClick={()=>openEdit(item)} className="px-2 py-1 rounded border border-slate-600 text-slate-200">Edit</button><button onClick={()=>archive(item)} className="px-2 py-1 rounded border border-red-800 text-red-300">Remove</button></div></td>
          </tr>)}{shown.length===0&&<tr><td colSpan={10} className="p-6 text-center text-slate-500">No matching spares.</td></tr>}</tbody>
        </table>
      </div>
    </main>
  </div>;
}
