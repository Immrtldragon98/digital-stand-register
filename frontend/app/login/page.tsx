"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { setSession } from "@/lib/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  async function submit(path: "login" | "bootstrap-admin") {
    if (!username.trim() || !password) {
      setError("Enter username and password.");
      return;
    }
    setBusy(true); setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/auth/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password, role: "ADMIN" }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Sign in failed");
      setSession(data.access_token, data.user);
      router.push("/dashboard");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed");
    } finally { setBusy(false); }
  }

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex items-center justify-center p-6">
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-7 shadow-2xl w-full max-w-md">
        <div className="flex flex-col items-center mb-6">
          <div className="p-3 bg-blue-950/50 border border-blue-800 rounded-full mb-3">
            <ShieldCheck className="w-8 h-8 text-industrial-accent" />
          </div>
          <h1 className="text-xl font-bold text-white">Sign In to Edit</h1>
          <p className="text-sm text-slate-400 mt-1 text-center">Anyone with the link can view. Admins and operators sign in to make changes.</p>
        </div>
        {error && <div className="mb-4 p-3 rounded-lg border border-red-800 bg-red-950/40 text-red-300 text-sm">{error}</div>}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Username</label>
            <input value={username} onChange={(e)=>setUsername(e.target.value)} className="w-full px-4 py-2.5 bg-industrial-dark border border-industrial-border rounded-lg text-white" autoComplete="username" />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Password</label>
            <input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} className="w-full px-4 py-2.5 bg-industrial-dark border border-industrial-border rounded-lg text-white" autoComplete="current-password" />
          </div>
          <button disabled={busy} onClick={()=>submit("login")} className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg disabled:opacity-50">
            {busy ? "Please wait..." : "Sign In"}
          </button>
          <div className="pt-3 border-t border-slate-800">
            <p className="text-[11px] text-slate-500 mb-2">First setup only — works only while no user accounts exist.</p>
            <button disabled={busy} onClick={()=>submit("bootstrap-admin")} className="w-full py-2 border border-slate-700 hover:border-blue-500 text-slate-300 rounded-lg text-sm disabled:opacity-50">
              Create First Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
