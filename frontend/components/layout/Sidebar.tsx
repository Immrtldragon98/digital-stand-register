"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Home, Wrench, Factory, Package, History, Users, LogIn, LogOut, ClipboardPaste, Database, BrainCircuit, ChevronDown, ChevronRight, FileText, Menu, X, Settings2 } from "lucide-react";
import { AuthUser, clearSession, getUser, isAdmin } from "@/lib/auth";

export default function Sidebar(){
 const pathname=usePathname(); const router=useRouter();
 const [user,setUser]=useState<AuthUser|null>(null); const [manageOpen,setManageOpen]=useState(false); const [mobileOpen,setMobileOpen]=useState(false);
 useEffect(()=>{const sync=()=>setUser(getUser());sync();window.addEventListener("dsr-auth-change",sync);window.addEventListener("storage",sync);return()=>{window.removeEventListener("dsr-auth-change",sync);window.removeEventListener("storage",sync)}},[]);
 useEffect(()=>{setMobileOpen(false);if(["/entry-guides","/reports","/import-report","/historical-import","/users","/planning"].includes(pathname))setManageOpen(true)},[pathname]);
 const primary=[
  {name:"Home",href:"/dashboard",icon:Home,tone:"text-blue-300"},
  {name:"Stand Area",href:"/stand-area",icon:Factory,tone:"text-amber-300"},
  {name:"Stand Change",href:"/operations",icon:Wrench,tone:"text-rose-300"},
  {name:"Spare Life",href:"/inventory",icon:Package,tone:"text-emerald-300"},
  {name:"History",href:"/activity",icon:History,tone:"text-violet-300"},
  {name:"Intelligence",href:"/intelligence",icon:BrainCircuit,tone:"text-cyan-300"}
 ];
 const manage=[{name:"Entry Guides",href:"/entry-guides",icon:Settings2},{name:"Reports",href:"/reports",icon:FileText},...(user?[{name:"Import Report",href:"/import-report",icon:ClipboardPaste},{name:"Historical Data",href:"/historical-import",icon:Database}]:[]),...(isAdmin(user)?[{name:"Users",href:"/users",icon:Users}]:[])];
 const active=(href:string)=>pathname===href||(href==="/intelligence"&&pathname==="/investigation");
 const item=(i:any)=>{const I=i.icon;const isActive=active(i.href);return <Link key={i.href} href={i.href} className={`nav-item ${isActive?"nav-item-active":""}`}><I className={`w-4 h-4 shrink-0 ${isActive?(i.tone||"text-blue-300"):"text-slate-500"}`}/><span>{i.name}</span></Link>};
 const logout=()=>{clearSession();setUser(null);router.push("/dashboard")};
 const panel=<><div><div className="brand-lockup"><div className="brand-mark"><span/></div><div><div className="brand-title">Digital Stand Register</div><div className="brand-subtitle">Finishing Mill</div></div></div><div className="nav-label">Main</div><nav className="space-y-1">{primary.map(item)}</nav><button onClick={()=>setManageOpen(v=>!v)} className="manage-toggle"><span>Manage</span>{manageOpen?<ChevronDown className="w-4 h-4"/>:<ChevronRight className="w-4 h-4"/>}</button>{manageOpen&&<nav className="space-y-1 mt-1">{manage.map(item)}</nav>}</div><div className="sidebar-account">{user?<><div className="px-2 mb-2"><div className="text-sm font-semibold text-slate-100">{user.username}</div><div className="text-xs text-slate-400">{user.role==="ADMIN"?"Administrator":"Operator"}</div></div><button onClick={logout} className="account-action"><LogOut className="w-4 h-4"/>Sign out</button></>:<Link href="/login" className="account-action text-sky-300"><LogIn className="w-4 h-4"/>Sign in to edit</Link>}</div></>;
 return <><aside className="desktop-sidebar">{panel}</aside><header className="mobile-topbar"><button aria-label="Open navigation" onClick={()=>setMobileOpen(true)} className="mobile-menu-btn"><Menu className="w-5 h-5"/></button><div><div className="text-sm font-semibold text-white">Digital Stand Register</div><div className="text-xs text-slate-400">Finishing Mill</div></div></header>{mobileOpen&&<div className="mobile-nav-overlay" onClick={()=>setMobileOpen(false)}><aside className="mobile-drawer" onClick={e=>e.stopPropagation()}><button aria-label="Close navigation" onClick={()=>setMobileOpen(false)} className="drawer-close"><X className="w-5 h-5"/></button>{panel}</aside></div>}<nav className="mobile-bottom-nav">{primary.slice(0,5).map(i=>{const I=i.icon;return <Link key={i.href} href={i.href} className={`mobile-nav-item ${active(i.href)?i.tone:""}`}><I className="w-5 h-5"/><span>{i.name.replace("Stand ","")}</span></Link>})}<Link href="/intelligence" className={`mobile-nav-item ${active("/intelligence")?"text-cyan-300":""}`}><BrainCircuit className="w-5 h-5"/><span>AI</span></Link></nav></>;
}
