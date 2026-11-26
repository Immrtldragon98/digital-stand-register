"use client";
import {useEffect,useState} from "react";
import {fetchApi} from "@/lib/api";
import {apiDateMs,runtimeHours} from "@/lib/runtime-display";
import {canEdit,getUser} from "@/lib/auth";
export default function PreparationTimer({stand}:{stand:any}){
 const [cycle,setCycle]=useState<any>(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
 async function load(){try{setCycle(await fetchApi(`/plant/preparations/${stand.id}`));}catch{setError("Preparation measurement is unavailable. Refresh before starting.");}}
 useEffect(()=>{void load();},[stand.id]);
 async function start(){setBusy(true);setError("");try{setCycle(await fetchApi(`/plant/preparations/${stand.id}/start`,{method:"POST"}));}catch(e){setError(e instanceof Error?e.message:"Could not start measurement. Refresh to verify.");}finally{setBusy(false);}}
 if(stand.current_status==="INSTALLED")return null;
 return <section className="preparation-timer"><div><b>Preparation measurement</b><p>{cycle?`${cycle.finished_at?"Completed":"Started"} · ${new Date(apiDateMs(cycle.started_at)).toLocaleString("en-IN")}${cycle.finished_at?` · ${runtimeHours((apiDateMs(cycle.finished_at)-apiDateMs(cycle.started_at))/3600000)}`:" · closes when this stand reaches Ready"}`:"No measured cycle yet. Start when preparation work begins; elapsed time includes pauses."}</p>{error&&<p role="alert" className="text-amber-200">{error}</p>}</div>{canEdit(getUser())&&stand.current_status!=="READY"&&(!cycle||cycle.finished_at)&&<button disabled={busy||!!error} onClick={()=>void start()} className="dsr-btn">{busy?"Starting…":"Start preparation"}</button>}</section>;
}
