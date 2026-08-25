"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LineStatusGrid from "@/components/dashboard/LineStatusGrid";
import { fetchApi } from "@/lib/api";

export default function DashboardPage() {
  const [lines, setLines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setError(null);
      setLines(await fetchApi("/dashboard/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load running lines");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const running = lines.reduce((n, line) => n + (line.positions || []).filter((p: any) => p.current_stand).length, 0);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Digital Stand Register" />
      <main className="p-4 md:p-6 flex-1">
        <div className="flex items-center justify-between mb-4 gap-3">
          <div>
            <h1 className="text-xl font-bold text-white">Running Lines</h1>
            <p className="text-sm text-slate-400">W1, W2 and W3 · {running} stands running</p>
          </div>
          <button onClick={load} className="px-3 py-2 text-sm rounded border border-slate-700 bg-slate-900 hover:bg-slate-800">Refresh</button>
        </div>
        {loading && <div className="text-slate-400 text-sm">Loading running lines...</div>}
        {error && <div className="bg-red-950/40 border border-red-800 rounded-lg p-4 text-red-300">{error}</div>}
        {!loading && !error && <LineStatusGrid lines={lines} />}
      </main>
    </div>
  );
}
