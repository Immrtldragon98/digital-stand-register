"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";
import { Activity as ActivityIcon } from "lucide-react";

export default function ActivityPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadActivityLogs() {
      try {
        const data = await fetchApi("/activity-logs");
        setLogs(data);
      } catch (err) {
        console.error("Failed to load activity logs:", err);
      } finally {
        setLoading(false);
      }
    }
    loadActivityLogs();
  }, []);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="System Activity Audit Trail" />
      <main className="p-6 flex-1">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
            Loading telemetry audit logs...
          </div>
        ) : (
          <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <ActivityIcon className="w-5 h-5 text-industrial-accent" />
              Complete Plant Activity Stream
            </h2>
            <div className="space-y-3">
              {logs && logs.length > 0 ? (
                logs.map((log, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-industrial-dark border border-industrial-border rounded-lg text-sm">
                    <div className="flex items-center gap-3">
                      <span className="w-2.5 h-2.5 rounded-full bg-industrial-accent animate-pulse"></span>
                      <div>
                        <p className="text-white font-medium">{log.action || log.message || "System Operation Event"}</p>
                        <p className="text-xs text-slate-400 font-mono mt-0.5">ID: {log.id || `LOG-${idx + 500}`}</p>
                      </div>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      {new Date(log.timestamp || Date.now()).toLocaleString()}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 text-center py-8">No activity logs recorded in the system audit trail.</div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}