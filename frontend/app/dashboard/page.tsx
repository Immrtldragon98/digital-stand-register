"use client";

import { useEffect, useRef, useState } from "react";
import Header from "@/components/layout/Header";
import CurrentRunSummary from "@/components/dashboard/CurrentRunSummary";
import LineStatusGrid from "@/components/dashboard/LineStatusGrid";
import { API_BASE_URL, fetchApi, invalidateApiCache } from "@/lib/api";
import { DashboardSnapshot, isDashboard, readSnapshot, saveSnapshot } from "@/lib/dashboard-snapshot";
import { RefreshCw } from "lucide-react";

export default function DashboardPage() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [stale, setStale] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const refresh = useRef<() => void>(() => {});

  useEffect(() => {
    let active = true, busy = false, failures = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    try { setSnapshot(readSnapshot(window.localStorage, API_BASE_URL)); } catch { /* Browser storage unavailable. */ }
    async function load() {
      if (!active || busy) return;
      busy = true;
      clearTimeout(timer);
      setLoading(true);
      try {
        if (!navigator.onLine) throw new Error("You are offline. Reconnection will continue when your connection returns.");
        invalidateApiCache();
        const lines = await fetchApi("/dashboard/");
        if (!isDashboard(lines)) throw new Error("The server returned an unexpected response. Reconnecting automatically.");
        if (!active) return;
        const next = { savedAt: Date.now(), lines };
        setSnapshot(next); setStale(false); setError(null); failures = 0;
        try { saveSnapshot(window.localStorage, API_BASE_URL, next); } catch { /* Keep the in-memory copy. */ }
      } catch (e) {
        if (!active) return;
        failures++; setStale(true);
        setError(e instanceof Error ? e.message : "Cannot reach the server. Reconnecting automatically.");
      } finally {
        busy = false;
        if (active) {
          setLoading(false);
          timer = setTimeout(load, failures ? Math.min(30_000, 5000 * 2 ** Math.min(failures - 1, 3)) : 60_000);
        }
      }
    }
    const visible = () => { if (document.visibilityState === "visible") void load(); };
    refresh.current = () => { void load(); };
    window.addEventListener("online", load);
    document.addEventListener("visibilitychange", visible);
    void load();
    return () => { active = false; clearTimeout(timer); window.removeEventListener("online", load); document.removeEventListener("visibilitychange", visible); };
  }, []);

  const lines = snapshot?.lines || [];
  const running = lines.reduce((n, l) => n + l.positions.filter(p => p.current_stand).length, 0);
  const total = lines.reduce((n, l) => n + l.positions.length, 0);
  const updated = snapshot ? new Date(snapshot.savedAt).toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "No saved data yet";
  return <div className="flex-1 min-h-screen text-slate-100">
    <Header title="Digital Stand Register" />
    <main className="p-3 md:p-5 full-bleed">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div><h1 className="page-title">Running Stands</h1><p className="page-subtitle mt-1">Select a stand to view components and history.</p></div>
        <div className="flex items-center gap-3">
          <div className="text-right"><div className="text-sm text-slate-300">{snapshot ? <><span className="font-semibold text-white">{running}</span> / {total} installed{stale ? " · saved copy" : ""}</> : "Running count unavailable"}</div><div className="mt-0.5 text-[11px] text-slate-400">Last synced: {updated}</div></div>
          <button onClick={() => refresh.current()} disabled={loading} aria-label="Refresh running stands" className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-60"><RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />{loading ? "Connecting…" : "Refresh"}</button>
        </div>
      </div>
      {(stale || error) && <div role="status" className="mb-4 rounded-lg border border-amber-700/50 bg-amber-950/30 p-3 text-sm text-amber-200">
        {snapshot ? "Showing the last saved dashboard. Stand status and running hours may have changed. " : "Connecting to the server. The first connection can take about a minute. "}
        {error || "Checking for updated data…"} Stand changes require a live connection.
      </div>}
      {snapshot ? <><CurrentRunSummary lines={lines} asOf={snapshot.savedAt}/><LineStatusGrid lines={lines} asOf={snapshot.savedAt}/></> : <div aria-label="Waiting for running stands" aria-busy={loading} className="grid gap-4">{[1, 2, 3].map(i => <div key={i} className="mechanical-panel p-4"><div className="h-5 w-24 rounded bg-slate-700 animate-pulse mb-4" /><div className="h-28 rounded bg-slate-800 animate-pulse" /></div>)}</div>}
    </main>
  </div>;
}
