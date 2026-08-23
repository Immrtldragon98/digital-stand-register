"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock login flow
    router.push("/dashboard");
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex items-center justify-center p-6">
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-8 shadow-2xl w-full max-w-md">
        <div className="flex flex-col items-center mb-6">
          <div className="p-3 bg-blue-950/50 border border-blue-800 rounded-full mb-3">
            <ShieldCheck className="w-8 h-8 text-industrial-accent" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-wide">Industrial Plant Portal</h1>
          <p className="text-xs text-slate-400 mt-1">Digital Stand Register Authentication</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-4 py-2.5 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
              placeholder="operator_id"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2.5 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-industrial-accent hover:bg-blue-600 text-white font-medium rounded-lg transition duration-200 shadow-md mt-2"
          >
            Authenticate Terminal
          </button>
        </form>
      </div>
    </div>
  );
}