"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type Item = { id:number; name:string; quantity:number; minimum_quantity:number; location:string; remarks?:string|null; is_active:boolean };
type Tx = { id:number; item_id:number; item_name:string; quantity_before:number; quantity_change:number; quantity_after:number; operator:string; reason:string; transaction_type:string; created_at:string };
const blank = { name:"", quantity:0, minimum_quantity:0, location:"", remarks:"" };

export default function InventoryPage() {
  const [items,setItems]=useState<Item[]>([]); const [history,setHistory]=useState<Tx[]>([]);
  const [form,setForm]=useState(blank); const [edit,setEdit]=useState<number|null>(null);
  const [adjust,setAdjust]=useState<{item:Item;mode:"delta"|"set";value:number}|null>(null);
  const [operator,setOperator]=useState(""); const [reason,setReason]=useState(""); const [error,setError]=useState("");

  const load=async()=>{try{const [inventory,transactions]=await Promise.all([fetchApi("/inventory/"),fetchApi("/inventory/transactions?limit=100")]);setItems(inventory);setHistory(transactions);}catch(e:any){setError(e.message)}};
  useEffect(()=>{load()},[]);

  const save=async(e:React.FormEvent)=>{e.preventDefault();setError("");try{if(edit){const{quantity:_q,...details}=form;await fetchApi(`/inventory/${edit}`,{method:"PATCH",body:JSON.stringify(details)});}else{await fetchApi("/inventory/",{method:"POST",body:JSON.stringify(form)});}setForm(blank);setEdit(null);await load();}catch(e:any){setError(e.message)}};
  const openAdjustment=(item:Item,mode:"delta"|"set",value:number)=>{setAdjust({item,mode,value});setOperator("");setReason("");setError("")};
  const submitAdjustment=async(e:React.FormEvent)=>{e.preventDefault();if(!adjust)return;if(!operator.trim()||!reason.trim()){setError("Name and reason are required.");return;}try{const path=adjust.mode==="set"?`/inventory/${adjust.item.id}/set-quantity`:`/inventory/${adjust.item.id}/quantity`;const body=adjust.mode==="set"?{quantity:Math.max(0,Math.floor(adjust.value)),operator:operator.trim(),reason:reason.trim()}:{delta:Math.trunc(adjust.value),operator:operator.trim(),reason:reason.trim()};await fetchApi(path,{method:"POST",body:JSON.stringify(body)});setAdjust(null);await load();}catch(e:any){setError(e.message)}};
  const archive=async(item:Item)=>{if(!confirm(`Archive ${item.name}?`))return;try{await fetchApi(`/inventory/${item.id}`,{method:"DELETE"});await load();}catch(e:any){setError(e.message)}};

  return <div className="p-4 md:p-6 space-y-4">
    <div><h1 className="text-2xl font-bold text-white">Materials</h1><p className="text-sm text-slate-400">Simple stock sheet for stand-area materials.</p></div>
    {error&&<div className="text-red-300 text-sm">{error}</div>}

    <form onSubmit={save} className="border border-slate-700 rounded-lg overflow-hidden bg-industrial-card">
      <div className="grid grid-cols-1 md:grid-cols-6 gap-px bg-slate-700">
        <input className="bg-slate-950 px-3 py-2 text-white" placeholder="Material / SAP code" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} required />
        {!edit?<input className="bg-slate-950 px-3 py-2 text-white" type="number" min="0" placeholder="Qty" value={form.quantity} onChange={e=>setForm({...form,quantity:+e.target.value})}/>:<div className="bg-slate-950 px-3 py-2 text-slate-500">Qty unchanged</div>}
        <input className="bg-slate-950 px-3 py-2 text-white" type="number" min="0" placeholder="Min qty" value={form.minimum_quantity} onChange={e=>setForm({...form,minimum_quantity:+e.target.value})}/>
        <input className="bg-slate-950 px-3 py-2 text-white" placeholder="Location" value={form.location} onChange={e=>setForm({...form,location:e.target.value})} required />
        <input className="bg-slate-950 px-3 py-2 text-white md:col-span-1" placeholder="Description / spec" value={form.remarks} onChange={e=>setForm({...form,remarks:e.target.value})}/>
        <button className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3 py-2">{edit?"Update":"Add"}</button>
      </div>
      {edit&&<button type="button" onClick={()=>{setEdit(null);setForm(blank)}} className="m-2 text-xs text-slate-400">Cancel edit</button>}
    </form>

    {adjust&&<form onSubmit={submitAdjustment} className="border border-blue-700 rounded-lg p-3 bg-blue-950/10 grid md:grid-cols-5 gap-2 items-end">
      <div><label className="text-xs text-slate-400">Material</label><div className="text-white font-semibold py-2">{adjust.item.name}</div></div>
      <div><label className="text-xs text-slate-400">{adjust.mode==="set"?"New qty":"Change"}</label><input className="input-class" type="number" value={adjust.value} onChange={e=>setAdjust({...adjust,value:Number(e.target.value)})}/></div>
      <div><label className="text-xs text-slate-400">Done by</label><input className="input-class" value={operator} onChange={e=>setOperator(e.target.value)} required/></div>
      <div><label className="text-xs text-slate-400">Reason</label><input className="input-class" value={reason} onChange={e=>setReason(e.target.value)} placeholder="Issued / received" required/></div>
      <div className="flex gap-2"><button className="bg-blue-600 px-3 py-2 rounded text-white">Save</button><button type="button" onClick={()=>setAdjust(null)} className="border border-slate-700 px-3 py-2 rounded">Cancel</button></div>
    </form>}

    <div className="overflow-x-auto border border-slate-700 rounded-lg bg-industrial-card">
      <table className="w-full min-w-[850px] text-sm border-collapse">
        <thead className="bg-slate-800 text-slate-200"><tr><th className="border border-slate-700 p-2 text-left">Material / SAP Code</th><th className="border border-slate-700 p-2 text-left">Description / Specification</th><th className="border border-slate-700 p-2">Qty</th><th className="border border-slate-700 p-2">Min</th><th className="border border-slate-700 p-2">Location</th><th className="border border-slate-700 p-2">Status</th><th className="border border-slate-700 p-2">Action</th></tr></thead>
        <tbody>{items.map(i=><tr key={i.id} className="even:bg-slate-900/40"><td className="border border-slate-800 p-2 font-semibold text-white">{i.name}</td><td className="border border-slate-800 p-2 text-slate-300">{i.remarks||"—"}</td><td className="border border-slate-800 p-2 text-center font-bold">{i.quantity}</td><td className="border border-slate-800 p-2 text-center">{i.minimum_quantity}</td><td className="border border-slate-800 p-2 text-center">{i.location}</td><td className={`border border-slate-800 p-2 text-center ${i.quantity===0?"text-red-400":i.quantity<=i.minimum_quantity?"text-orange-400":"text-emerald-400"}`}>{i.quantity===0?"OUT":i.quantity<=i.minimum_quantity?"LOW":"OK"}</td><td className="border border-slate-800 p-1"><div className="flex gap-1 justify-center"><button onClick={()=>openAdjustment(i,"delta",-1)} className="px-2 py-1 border border-slate-700 rounded">−1</button><button onClick={()=>openAdjustment(i,"delta",1)} className="px-2 py-1 border border-slate-700 rounded">+1</button><button onClick={()=>openAdjustment(i,"set",i.quantity)} className="px-2 py-1 border border-slate-700 rounded">Qty</button><button onClick={()=>{setEdit(i.id);setForm({name:i.name,quantity:i.quantity,minimum_quantity:i.minimum_quantity,location:i.location,remarks:i.remarks||""})}} className="px-2 py-1 border border-slate-700 rounded">Edit</button><button onClick={()=>archive(i)} className="px-2 py-1 border border-red-900 text-red-400 rounded">Archive</button></div></td></tr>)}</tbody>
      </table>
    </div>

    <details className="border border-slate-700 rounded-lg bg-industrial-card"><summary className="cursor-pointer p-3 font-semibold text-white">Stock History ({history.length})</summary><div className="overflow-x-auto"><table className="w-full min-w-[850px] text-sm"><thead className="bg-slate-800"><tr><th className="p-2 text-left">Date</th><th>Material</th><th>Before</th><th>Change</th><th>After</th><th>Done By</th><th className="text-left">Reason</th></tr></thead><tbody>{history.map(tx=><tr key={tx.id} className="border-t border-slate-800"><td className="p-2 whitespace-nowrap">{new Date(tx.created_at).toLocaleString()}</td><td className="text-center">{tx.item_name}</td><td className="text-center">{tx.quantity_before}</td><td className="text-center">{tx.quantity_change>0?"+":""}{tx.quantity_change}</td><td className="text-center">{tx.quantity_after}</td><td className="text-center">{tx.operator}</td><td className="p-2">{tx.reason}</td></tr>)}</tbody></table></div></details>
  </div>
}
