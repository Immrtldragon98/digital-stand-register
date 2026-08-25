"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";
import { AuthUser, getUser, isAdmin } from "@/lib/auth";

type UserRow = { id:number; username:string; role_id:number; role:"ADMIN"|"OPERATOR" };

export default function UsersPage(){
  const [me,setMe]=useState<AuthUser|null>(null);
  const [users,setUsers]=useState<UserRow[]>([]);
  const [username,setUsername]=useState("");
  const [password,setPassword]=useState("");
  const [role,setRole]=useState<"ADMIN"|"OPERATOR">("OPERATOR");
  const [error,setError]=useState("");
  const [message,setMessage]=useState("");

  const load=async()=>{
    const current=getUser(); setMe(current);
    if(!isAdmin(current)) return;
    try{ setUsers(await fetchApi("/auth/users")); }
    catch(e){ setError(e instanceof Error?e.message:"Could not load users"); }
  };
  useEffect(()=>{ load(); },[]);

  async function addUser(e:React.FormEvent){
    e.preventDefault(); setError(""); setMessage("");
    try{
      await fetchApi("/auth/users",{method:"POST",body:JSON.stringify({username:username.trim(),password,role})});
      setUsername(""); setPassword(""); setRole("OPERATOR"); setMessage("User added."); await load();
    }catch(e){setError(e instanceof Error?e.message:"Could not add user");}
  }

  async function changeRole(user:UserRow,next:"ADMIN"|"OPERATOR"){
    setError("");
    try{await fetchApi(`/auth/users/${user.id}/role`,{method:"PATCH",body:JSON.stringify({role:next})});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not change role");}
  }

  async function resetPassword(user:UserRow){
    const password=window.prompt(`New password for ${user.username}:`);
    if(!password) return;
    try{await fetchApi(`/auth/users/${user.id}/password`,{method:"PATCH",body:JSON.stringify({password})});setMessage("Password updated.");}
    catch(e){setError(e instanceof Error?e.message:"Could not reset password");}
  }

  async function removeUser(user:UserRow){
    if(!window.confirm(`Delete ${user.username}?`)) return;
    try{await fetchApi(`/auth/users/${user.id}`,{method:"DELETE"});await load();}
    catch(e){setError(e instanceof Error?e.message:"Could not delete user");}
  }

  if(me && !isAdmin(me)) return <div className="flex-1 bg-industrial-dark text-slate-100 min-h-screen"><Header title="Users"/><main className="p-6 text-red-300">Admin access required.</main></div>;

  return <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
    <Header title="Users"/>
    <main className="p-4 md:p-6 flex-1 space-y-5">
      <div>
        <h1 className="text-xl font-bold">User Access</h1>
        <p className="text-sm text-slate-400 mt-1">Viewer = anyone with the link. Operators can edit plant data. Admins can also manage users and master data.</p>
      </div>
      {error&&<div className="p-3 border border-red-800 bg-red-950/40 rounded-lg text-red-300 text-sm">{error}</div>}
      {message&&<div className="p-3 border border-emerald-800 bg-emerald-950/30 rounded-lg text-emerald-300 text-sm">{message}</div>}
      <form onSubmit={addUser} className="bg-industrial-card border border-industrial-border rounded-xl p-4 grid grid-cols-1 md:grid-cols-4 gap-3">
        <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="Username" required className="input-class"/>
        <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Temporary password" required className="input-class"/>
        <select value={role} onChange={e=>setRole(e.target.value as any)} className="input-class"><option value="OPERATOR">Operator</option><option value="ADMIN">Admin</option></select>
        <button className="rounded-lg bg-blue-600 hover:bg-blue-500 font-semibold">Add User</button>
      </form>
      <div className="overflow-x-auto border border-industrial-border rounded-xl bg-industrial-card">
        <table className="w-full min-w-[700px] text-sm">
          <thead className="bg-slate-900"><tr><th className="text-left p-3">Username</th><th className="text-left p-3">Role</th><th className="text-left p-3">Actions</th></tr></thead>
          <tbody>{users.map(u=><tr key={u.id} className="border-t border-slate-800"><td className="p-3 font-semibold">{u.username}</td><td className="p-3"><select value={u.role} onChange={e=>changeRole(u,e.target.value as any)} className="bg-slate-950 border border-slate-700 rounded px-2 py-1"><option>OPERATOR</option><option>ADMIN</option></select></td><td className="p-3 flex gap-2"><button onClick={()=>resetPassword(u)} className="px-2 py-1 border border-slate-700 rounded">Reset Password</button><button onClick={()=>removeUser(u)} className="px-2 py-1 border border-red-800 text-red-300 rounded">Delete</button></td></tr>)}</tbody>
        </table>
      </div>
    </main>
  </div>;
}
