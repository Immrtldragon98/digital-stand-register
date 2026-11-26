"use client";
import {useEffect,useRef,useState} from "react";
import Header from "@/components/layout/Header";
import {API_BASE_URL,ApiError,fetchApi,invalidateApiCache} from "@/lib/api";
import {AuthUser,getUser,isAdmin} from "@/lib/auth";
import {apiDateMs} from "@/lib/runtime-display";
import {FeedbackForm,FeedbackPayload,emptyFeedback,loadFeedbackDraft,saveFeedbackDraft,clearFeedbackDraft} from "@/lib/feedback-draft";

const statuses=["OPEN","IN_PROGRESS","RESOLVED","DECLINED"];
const label=(value:string)=>value.replaceAll("_"," ").toLowerCase().replace(/^./,x=>x.toUpperCase());
type Report=FeedbackForm & {id:number;reference:string;status:string;admin_notes:string;created_at:string;updated_at:string;updated_by:string|null};

export default function FeedbackPage(){
 const [form,setForm]=useState<FeedbackForm>(emptyFeedback),[pending,setPending]=useState<FeedbackPayload|null>(null),[ready,setReady]=useState(false),[online,setOnline]=useState(true),[draftFailed,setDraftFailed]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(""),[success,setSuccess]=useState(""),[user,setUser]=useState<AuthUser|null>(null);
 const [reports,setReports]=useState<Report[]>([]),[total,setTotal]=useState(0),[filter,setFilter]=useState("OPEN"),[kindFilter,setKindFilter]=useState(""),[offset,setOffset]=useState(0),[loading,setLoading]=useState(false),[listError,setListError]=useState("");
 const listSequence=useRef(0);
 useEffect(()=>{
  const sync=()=>setUser(getUser()),connection=()=>setOnline(navigator.onLine);sync();connection();
  try {const saved=loadFeedbackDraft(localStorage,API_BASE_URL);if(saved){setForm(saved.form);setPending(saved.pending);}else{const from=new URLSearchParams(window.location.search).get("from")||"";setForm({...emptyFeedback,reporter:getUser()?.username||"",page:from.startsWith("/")&&!from.startsWith("//")?from.split(/[?#]/)[0].slice(0,200):""});}}catch{setDraftFailed(true);}
  setReady(true);window.addEventListener("dsr-auth-change",sync);window.addEventListener("storage",sync);window.addEventListener("online",connection);window.addEventListener("offline",connection);
  return()=>{window.removeEventListener("dsr-auth-change",sync);window.removeEventListener("storage",sync);window.removeEventListener("online",connection);window.removeEventListener("offline",connection);};
 },[]);
 useEffect(()=>{if(!ready)return;try{setDraftFailed(!saveFeedbackDraft(localStorage,API_BASE_URL,{form,pending}));}catch{setDraftFailed(true);}},[form,pending,ready]);
 async function loadReports(){if(!isAdmin(user))return;const sequence=++listSequence.current;setLoading(true);setListError("");try{invalidateApiCache();const result=await fetchApi(`/feedback/?offset=${offset}&limit=25${filter?`&status=${filter}`:""}${kindFilter?`&kind=${kindFilter}`:""}`);if(sequence===listSequence.current){setReports(result.items);setTotal(result.total);}}catch(e){if(sequence===listSequence.current)setListError(e instanceof Error?e.message:"Could not load feedback.");}finally{if(sequence===listSequence.current)setLoading(false);}}
 useEffect(()=>{if(isAdmin(user))void loadReports();else{setReports([]);setTotal(0);}return()=>{listSequence.current++;};},[user,filter,kindFilter,offset]);
 function change(field:keyof FeedbackForm,value:string){setForm(previous=>({...previous,[field]:value}));setSuccess("");setError("");}
 async function submit(event:React.FormEvent){
  event.preventDefault();if(busy||!ready)return;if(!navigator.onLine){setError("You are offline. Keep this draft and submit when connected.");return;}
  setBusy(true);setError("");setSuccess("");
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),30000);
  try {
   const payload=pending||{...form,request_id:crypto.randomUUID()};setPending(payload);
   // Save the retry key before the network call, even if the tab is closed mid-request.
   try{saveFeedbackDraft(localStorage,API_BASE_URL,{form,pending:payload});}catch{/* Submission can work without storage. */}
   const result=await fetchApi("/feedback/",{method:"POST",body:JSON.stringify(payload),signal:controller.signal});
   setSuccess(`Received ${result.reference}. An admin can review your report.`);setPending(null);setForm({...emptyFeedback,reporter:form.reporter,page:form.page});
   try{clearFeedbackDraft(localStorage,API_BASE_URL);}catch{/* State is already cleared. */}
   if(isAdmin(user))void loadReports();
  }catch(e){
   if(e instanceof ApiError && e.status>=400 && e.status<500){setPending(null);setError(e.status===422?"Check the title and description lengths, then submit again.":e.message);}
   else setError("Submission was not confirmed. Retry this same report to check or save it without creating a duplicate.");
  }finally{clearTimeout(timeout);setBusy(false);}
 }
 const locked=busy||!!pending;
 return <div className="dsr-page"><Header title="Bugs and suggestions"/><main className="dsr-main"><div className="full-bleed space-y-5">
  <div><h1 className="dsr-title">Report a bug or suggest an improvement</h1><p className="dsr-subtitle">Tell us what happened or what would make the app more useful. Only admins can read submitted reports.</p></div>
  <form onSubmit={submit} className="mechanical-panel p-4 space-y-4 max-w-3xl">
   <div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm">Report type<select aria-label="Report type" value={form.kind} disabled={locked} onChange={e=>change("kind",e.target.value)} className="input-class mt-1 w-full"><option value="BUG">Bug</option><option value="SUGGESTION">Suggestion</option></select></label><label className="block text-sm">Your name (optional)<input value={form.reporter} disabled={locked} maxLength={80} onChange={e=>change("reporter",e.target.value)} className="input-class mt-1 w-full" autoComplete="name"/></label></div>
   <label className="block text-sm">Title<input required minLength={3} maxLength={160} value={form.title} disabled={locked} onChange={e=>change("title",e.target.value)} placeholder="Briefly describe the issue or idea" className="input-class mt-1 w-full"/></label>
   <label className="block text-sm">{form.kind==="BUG"?"What happened?":"What would you improve?"}<textarea required minLength={10} maxLength={5000} rows={6} value={form.description} disabled={locked} onChange={e=>change("description",e.target.value)} placeholder={form.kind==="BUG"?"Steps to reproduce, what you expected, and what actually happened. Include the exact error text if available.":"Describe the improvement and how it would help your work."} className="input-class mt-1 w-full"/></label>
   <label className="block text-sm">Affected page (optional)<input maxLength={200} value={form.page} disabled={locked} onChange={e=>change("page",e.target.value)} placeholder="/dashboard" className="input-class mt-1 w-full"/></label>
   <p className="text-xs text-slate-400">Do not include passwords or confidential information. Unsent text stays on this device; it is never submitted automatically.</p>
   {!online&&<p role="status" className="text-amber-200">Offline. You can prepare a draft now and submit after reconnecting.</p>}
   {draftFailed&&<p role="status" className="text-amber-200">Draft saving is unavailable in this browser. Keep this page open or copy your text.</p>}
   {error&&<p role="alert" className="text-rose-200">{error}</p>}{success&&<p role="status" className="text-emerald-200">{success}</p>}
   <div className="flex flex-wrap gap-3"><button className="dsr-btn-primary" disabled={!ready||busy||!online}>{busy?"Submitting…":pending?"Retry same report":"Submit report"}</button>{!busy&&<button type="button" className="dsr-btn" onClick={()=>{setPending(null);setForm({...emptyFeedback});setError("");setSuccess("");try{clearFeedbackDraft(localStorage,API_BASE_URL);}catch{}}}>Clear local draft</button>}</div>
   {pending&&!busy&&<p className="text-xs text-slate-400">Your text is locked while the submission is uncertain. Retry safely using the same report. Clearing the local draft does not remove a report already received.</p>}
  </form>
  {isAdmin(user)&&<section className="mechanical-panel p-4 space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-lg font-bold">Admin feedback inbox</h2><p className="text-xs text-slate-400">{total} matching reports · Reporter names are self-reported.</p></div><button disabled={loading} className="dsr-btn" onClick={()=>void loadReports()}>Refresh inbox</button></div>
   <div className="flex flex-wrap gap-3"><label className="text-sm">Status<select value={filter} onChange={e=>{setFilter(e.target.value);setOffset(0);}} className="input-class ml-2"><option value="">All statuses</option>{statuses.map(status=><option key={status} value={status}>{label(status)}</option>)}</select></label><label className="text-sm">Type<select value={kindFilter} onChange={e=>{setKindFilter(e.target.value);setOffset(0);}} className="input-class ml-2"><option value="">All types</option><option value="BUG">Bugs</option><option value="SUGGESTION">Suggestions</option></select></label></div>
   {listError&&<p role="alert" className="text-rose-200">{listError}</p>}{loading?<p role="status">Loading reports…</p>:reports.length?reports.map(report=><ReportCard key={`${report.id}-${report.updated_at}`} report={report} onSaved={loadReports}/>):<p className="text-slate-400">No reports match these filters.</p>}
   <div className="flex items-center gap-3"><button className="dsr-btn" disabled={loading||offset===0} onClick={()=>setOffset(value=>Math.max(0,value-25))}>Previous</button><span className="text-xs text-slate-400">{total?offset+1:0}–{Math.min(offset+25,total)} of {total}</span><button className="dsr-btn" disabled={loading||offset+25>=total} onClick={()=>setOffset(value=>value+25)}>Next</button></div>
  </section>}
 </div></main></div>;
}

function ReportCard({report,onSaved}:{report:Report;onSaved:()=>Promise<void>}){
 const [status,setStatus]=useState(report.status),[notes,setNotes]=useState(report.admin_notes),[busy,setBusy]=useState(false),[error,setError]=useState("");
 async function save(){setBusy(true);setError("");try{await fetchApi(`/feedback/${report.id}`,{method:"PATCH",body:JSON.stringify({status,admin_notes:notes})});await onSaved();}catch(e){setError(e instanceof Error?e.message:"Could not save. Refresh the inbox to verify the current status.");}finally{setBusy(false);}}
 return <article className="rounded border border-slate-700 p-4 space-y-3"><header><div className="text-xs text-slate-400">{report.reference} · {label(report.kind)} · {new Date(apiDateMs(report.created_at)).toLocaleString("en-IN")}</div><h3 className="font-bold break-words">{report.title}</h3><p className="text-xs text-slate-400 break-words">{report.reporter||"Name not provided"}{report.page?` · ${report.page}`:""}</p></header><p className="whitespace-pre-wrap break-words text-sm">{report.description}</p><div className="grid gap-3 sm:grid-cols-[180px_1fr]"><label className="text-sm">Status<select value={status} disabled={busy} onChange={e=>setStatus(e.target.value)} className="input-class mt-1 w-full">{statuses.map(value=><option key={value} value={value}>{label(value)}</option>)}</select></label><label className="text-sm">Admin notes<textarea maxLength={2000} rows={2} value={notes} disabled={busy} onChange={e=>setNotes(e.target.value)} className="input-class mt-1 w-full"/></label></div>{report.updated_by&&<p className="text-xs text-slate-400">Last updated by {report.updated_by}</p>}{error&&<p role="alert" className="text-rose-200">{error}</p>}<button className="dsr-btn" disabled={busy||(status===report.status&&notes===report.admin_notes)} onClick={()=>void save()}>{busy?"Saving…":"Save review"}</button></article>;
}
