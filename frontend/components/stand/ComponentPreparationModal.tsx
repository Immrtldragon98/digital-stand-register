"use client";
import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import {ApiError,fetchApi} from "@/lib/api";
import {getUser} from "@/lib/auth";
import {confirmationKey,forgetConfirmationKey} from "@/lib/confirmation-key";
import {runtimeLabel} from "@/lib/runtime-display";
type Asset={id:number;code:string;condition:string;measured_life_hours:number|null;known_runtime_hours:number;life_complete:boolean};
type ComponentRow={component_type_id:number;name:string;required_qty:number|null;asset_ids:number[];available_assets:Asset[];stock_quantity:number|null;inventory_item_id:number|null;is_extra:boolean};
type Pending={body:string;key:string};
export default function ComponentPreparationModal({stand,onClose,onComplete}:{stand:any;onClose:()=>void;onComplete:()=>Promise<void>|void}){
 const[rows,setRows]=useState<ComponentRow[]>([]),[loading,setLoading]=useState(true),[saving,setSaving]=useState(false),[error,setError]=useState(""),[notes,setNotes]=useState(""),[pending,setPending]=useState<Pending|null>(null);
 const user=getUser();
 useEffect(()=>{let active=true;(async()=>{try{const data=await fetchApi(`/stands/${stand.id}/components`);if(active){setRows((data.components||[]).map((r:ComponentRow)=>({...r,asset_ids:r.asset_ids||[],available_assets:r.available_assets||[]})));setNotes(data.notes||"");}}catch(e){if(active)setError(e instanceof Error?e.message:"Could not load components");}finally{if(active)setLoading(false)}})();return()=>{active=false}},[stand.id]);
 const count=useMemo(()=>rows.reduce((sum,row)=>sum+row.asset_ids.length,0),[rows]);
 function toggle(type:number,id:number){if(saving||pending)return;setRows(current=>current.map(row=>row.component_type_id===type?{...row,asset_ids:row.asset_ids.includes(id)?row.asset_ids.filter(x=>x!==id):[...row.asset_ids,id]}:row));}
 async function finish(update:Pending){
  try {await fetchApi("/operations/stands/status",{method:"POST",body:update.body,headers:{"Idempotency-Key":update.key}});forgetConfirmationKey("component-stage",update.body);setPending(null);await onComplete();onClose();}
  catch(e){if(e instanceof ApiError&&e.status>=400&&e.status<500&&e.status!==408)setPending(null);throw e;}
 }
 async function save(skip:boolean){
  if(saving)return;setSaving(true);setError("");
  try{
   if(pending){
    try{await fetchApi(`/operations/commands/${pending.key}`);forgetConfirmationKey("component-stage",pending.body);setPending(null);await onComplete();onClose();return;}
    catch(e){if(!(e instanceof ApiError)||e.status!==404)throw e;}
    await finish(pending);return;
   }
   if(skip&&!notes.trim())throw new Error("Enter the reason for skipping component tracking.");
   if(!skip&&!count)throw new Error("Select the fitted component identities or explicitly skip tracking with a reason.");
   const items=rows.map(row=>{const selected=row.available_assets.filter(a=>row.asset_ids.includes(a.id));return {component_type_id:row.component_type_id,new_qty:selected.filter(a=>a.condition==="NEW").length,reused_qty:selected.filter(a=>a.condition==="REUSED").length,carried_life_hours:null,asset_ids:row.asset_ids};});
   await fetchApi(`/stands/${stand.id}/components`,{method:"POST",body:JSON.stringify({prepared_by:user?.username||"Operator",notes:notes.trim()||null,skip,items:skip?[]:items})});
   const body=JSON.stringify({stand_code:stand.code,status:"GAUGING",updated_by:user?.username||"Operator",remarks:skip?"Component tracking explicitly skipped: "+notes.trim():"Component identities saved; new stock issued on finalization"});
   const update={body,key:confirmationKey("component-stage",body)};setPending(update);await finish(update);
  }catch(e){setError(e instanceof Error?e.message:"Could not save component preparation");}finally{setSaving(false)}
 }
 return <div className="fixed inset-0 z-[60] bg-black/70 flex items-end md:items-center justify-center md:p-4" onClick={()=>{if(!saving)onClose()}}><section role="dialog" aria-modal="true" aria-label="Stand component preparation" className="w-full max-w-5xl max-h-[92vh] overflow-auto rounded-t-2xl md:rounded-xl border border-slate-700 bg-[#0f1725]" onClick={e=>e.stopPropagation()}>
  <div className="border-b border-slate-800 p-4 flex items-start justify-between gap-3"><div><div className="dsr-kicker">Before Gauging</div><h2 className="text-xl font-bold text-white">Stand {stand.code} · component identities</h2><p className="mt-2 text-sm text-slate-400">Select every new or reused component fitted. Life follows the physical identity; new-part stock is deducted once when Gauging is saved.</p><Link className="inline-block text-sm text-sky-300 mt-2" href="/components">Open component register and stock mapping</Link></div><button disabled={saving} onClick={onClose} className="dsr-btn">Close</button></div>
  <div className="p-4 space-y-3">{error&&<div role="alert" className="rounded-lg border border-red-900 p-3 text-red-300">{error}</div>}{pending&&<div role="status" className="rounded-lg border border-amber-800 p-3 text-amber-200">The previous update may already be saved. Check its result before editing preparation. No write is replayed automatically.</div>}
   {loading?<div className="dsr-empty">Loading identities…</div>:<><div className="space-y-3">{rows.map(row=>{const selected=row.available_assets.filter(a=>row.asset_ids.includes(a.id));const newCount=selected.filter(a=>a.condition==="NEW").length;return <fieldset disabled={saving||!!pending} key={row.component_type_id} className="rounded-lg border border-slate-800 p-3"><legend className="text-sm font-bold text-white px-1">{row.name}{row.is_extra?" · entry-guide extra":""}</legend><p className="text-xs text-slate-400 mb-2">Required: {row.required_qty??"as fitted"} · Selected: {selected.length} ({newCount} new, {selected.length-newCount} reused) · New-part stock: {row.inventory_item_id==null?"not mapped":row.stock_quantity==null?"not recorded":row.stock_quantity}</p><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{row.available_assets.map(asset=><label key={asset.id} className="flex gap-2 items-start rounded border border-slate-700 p-2 text-xs text-slate-300"><input type="checkbox" checked={row.asset_ids.includes(asset.id)} onChange={()=>toggle(row.component_type_id,asset.id)}/><span><b className="text-white">{asset.code}</b> · {asset.condition}<span className="block text-slate-400">{runtimeLabel(asset.measured_life_hours,asset.known_runtime_hours,asset.life_complete)}</span></span></label>)}{!row.available_assets.length&&<p className="text-xs text-amber-200">No available identities. Ask an admin to register the physical parts; do not invent them from quantities.</p>}</div></fieldset>})}</div>
   <label className="block"><span className="metric-label">Preparation note / required reason if skipping</span><input maxLength={1000} disabled={saving||!!pending} className="input-class" value={notes} onChange={e=>setNotes(e.target.value)}/></label><p className="text-xs text-slate-400">{count} identities selected. Missing historical life stays unknown. Saved partial tracking is not a claim that every required component is fitted.</p><div className="flex flex-wrap justify-end gap-2">{pending?<button disabled={saving} className="dsr-btn-primary" onClick={()=>save(false)}>{saving?"Checking…":"Check previous update"}</button>:<><button disabled={saving} className="dsr-btn" onClick={()=>save(true)}>Skip with reason → Gauging</button><button disabled={saving} className="dsr-btn-primary" onClick={()=>save(false)}>{saving?"Saving…":"Save identities → Gauging"}</button></>}</div></>}
  </div>
 </section></div>;
}
