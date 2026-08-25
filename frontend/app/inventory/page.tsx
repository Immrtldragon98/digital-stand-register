"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Item = { id:number; name:string; quantity:number; minimum_quantity:number; location:string; remarks?:string|null; is_active:boolean };
const blank={code:"",description:"",material:"",quantity:0};

function splitItem(i:Item){
  const [code, materialFromName] = i.name.includes("|") ? i.name.split("|",2) : [i.name,""];
  const [description, materialFromRemarks] = (i.remarks||"").split("||",2);
  return {code:code.trim(),description:(description||"").trim(),material:(materialFromRemarks||materialFromName||"").trim()};
}

export default function InventoryPage(){
  const [items,setItems]=useState<Item[]>([]);
  const [form,setForm]=useState(blank);
  const [showAdd,setShowAdd]=useState(false);
  const [error,setError]=useState("");

  const load=async()=>{try{setError("");setItems(await fetchApi("/inventory/"));}catch(e){setError(e instanceof Error?e.message:"Could not load materials")}};
  useEffect(()=>{load()},[]);

  async function addMaterial(e:React.FormEvent){
    e.preventDefault();
    try{
      await fetchApi("/inventory/",{method:"POST",body:JSON.stringify({name:`${form.code}|${form.material}`,quantity:form.quantity,minimum_quantity:0,location:"Store",remarks:`${form.description}||${form.material}`})});
      setForm(blank);setShowAdd(false);await load();
    }catch(e){setError(e instanceof Error?e.message:"Could not add material")}
  }

  async function setQty(item:Item){
    const raw=window.prompt(`New quantity for ${splitItem(item).material || splitItem(item).code}`,String(item.quantity));
    if(raw===null)return;
    const qty=Number(raw); if(!Number.isFinite(qty)||qty<0)return;
    const operator=window.prompt("Updated by")?.trim(); if(!operator)return;
    const reason=window.prompt("Reason")?.trim()||"Stock update";
    try{await fetchApi(`/inventory/${item.id}/set-quantity`,{method:"POST",body:JSON.stringify({quantity:Math.floor(qty),operator,reason})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not update quantity")}
  }

  async function archive(item:Item){
    if(!window.confirm(`Remove ${splitItem(item).material || splitItem(item).code} from active materials list?`))return;
    try{await fetchApi(`/inventory/${item.id}`,{method:"DELETE"});await load();}catch(e){setError(e instanceof Error?e.message:"Could not remove material")}
  }

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Materials" />
    <main className="p-4 md:p-6 flex-1 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div><h1 className="text-xl font-bold text-white">Stand Materials</h1><p className="text-sm text-slate-400">Simple material register</p></div>
        <button onClick={()=>setShowAdd(v=>!v)} className="px-3 py-2 rounded bg-blue-600 hover:bg-blue-500 text-sm font-semibold">{showAdd?"Close":"+ Add Material"}</button>
      </div>
      {showAdd&&<form onSubmit={addMaterial} className="grid grid-cols-1 md:grid-cols-5 gap-2 border border-slate-700 rounded-lg p-3 bg-slate-900/50">
        <input className="input-class" placeholder="SAP / Material code" value={form.code} onChange={e=>setForm({...form,code:e.target.value})} required/>
        <input className="input-class md:col-span-2" placeholder="Description / specification" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/>
        <input className="input-class" placeholder="Material name" value={form.material} onChange={e=>setForm({...form,material:e.target.value})} required/>
        <div className="flex gap-2"><input className="input-class" type="number" min="0" placeholder="Qty" value={form.quantity} onChange={e=>setForm({...form,quantity:Number(e.target.value)})}/><button className="px-3 rounded bg-emerald-600 font-semibold">Save</button></div>
      </form>}
      {error&&<div className="text-red-300 text-sm">{error}</div>}
      <div className="overflow-x-auto border border-slate-700 rounded-lg bg-slate-950/30">
        <table className="w-full min-w-[900px] text-sm border-collapse">
          <thead className="bg-yellow-300 text-black"><tr><th className="border border-slate-500 px-3 py-2 text-left">SAP / Material Code</th><th className="border border-slate-500 px-3 py-2 text-left">Description / Specification</th><th className="border border-slate-500 px-3 py-2 text-left">Material</th><th className="border border-slate-500 px-3 py-2 text-center w-20">Qty</th><th className="border border-slate-500 px-3 py-2 text-center w-28">Action</th></tr></thead>
          <tbody>{items.map(item=>{const v=splitItem(item);return <tr key={item.id} className="even:bg-slate-900/50"><td className="border border-slate-700 px-3 py-2 font-semibold">{v.code}</td><td className="border border-slate-700 px-3 py-2">{v.description||"—"}</td><td className="border border-slate-700 px-3 py-2">{v.material||"—"}</td><td className="border border-slate-700 px-3 py-2 text-center font-bold">{item.quantity}</td><td className="border border-slate-700 px-2 py-1"><div className="flex justify-center gap-1"><button onClick={()=>setQty(item)} className="px-2 py-1 text-xs rounded border border-blue-700 text-blue-300">Qty</button><button onClick={()=>archive(item)} className="px-2 py-1 text-xs rounded border border-red-800 text-red-300">Remove</button></div></td></tr>})}</tbody>
        </table>
      </div>
    </main>
  </div>;
}
