"use client";

import { Activity } from "lucide-react";

export default function RecentActivity({ logs }: { logs: any[] }) {
  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl mb-6">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-industrial-accent" />
        Recent System Activity Logs
      </h2>
      <div className="space-y-3">
        {logs && logs.length > 0 ? (
          logs.slice(0, 5).map((log, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-industrial-dark border border-industrial-border rounded-lg text-sm">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full bg-industrial-accent"></span>
                <span className="text-white font-medium">{log.action || log.message || "System Action"}</span>
              </div>
              <span className="text-xs text-slate-400">
                {new Date(log.timestamp || Date.now()).toLocaleTimeString()}
              </span>
            </div>
          ))
        ) : (
          <div className="text-slate-500 text-sm">No recent activity logs recorded.</div>
        )}
      </div>
    </div>
  );
}