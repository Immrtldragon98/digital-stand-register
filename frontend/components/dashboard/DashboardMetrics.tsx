"use client";

import { Layers, Cpu, Wrench, AlertTriangle } from "lucide-react";

export default function DashboardMetrics({ stats }: { stats: any }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Stands</span>
          <Layers className="w-4 h-4 text-industrial-accent" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.total_stands || 0}</div>
      </div>
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Units</span>
          <Cpu className="w-4 h-4 text-green-400" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.active_stands || 0}</div>
      </div>
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Operations Logged</span>
          <Wrench className="w-4 h-4 text-blue-400" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.total_operations || 0}</div>
      </div>
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">System Alerts</span>
          <AlertTriangle className="w-4 h-4 text-amber-400" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.system_alerts || 0}</div>
      </div>
    </div>
  );
}