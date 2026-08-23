"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";
import { Activity as ActivityIcon } from "lucide-react";

export default function ActivityPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadActivityLogs() {
      try {
        setError("");
        const data = await fetchApi("/activity/");
        setLogs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load history");
      } finally {
        setLoading(false);
      }
    }
    loadActivityLogs();
  }, []);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="History" />
      <main className="p-4 md:p-6 flex-1">
        {error && <div className="mb-4 p-4 rounded-lg border border-red-800 bg-red-950/40 text-red-300">{error}</div>}
        {loading ? (
          <div className="text-slate-400 text-sm">Loading history...</div>
        ) : (
          <div className="bg-industrial-card border border-industrial-border rounded-xl p-5">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <ActivityIcon className="w-5 h-5 text-industrial-accent" />
              Recent Work History
            </h2>
            <div className="space-y-3">
              {logs.length > 0 ? logs.map((log, idx) => (
                <div key={idx} className="p-4 bg-industrial-dark border border-industrial-border rounded-lg text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-white font-medium">{log.action || log.message || "Work recorded"}</p>
                    <span className="text-xs text-slate-400">{new Date(log.timestamp || Date.now()).toLocaleString()}</span>
                  </div>
                </div>
              )) : <div className="text-slate-500 py-6">No history recorded yet.</div>}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
