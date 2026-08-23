"use client";

import { FileText, CheckCircle2, Clock } from "lucide-react";

export default function GuideStats({ stats }: { stats: any }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Guides</span>
          <FileText className="w-4 h-4 text-industrial-accent" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.total_guides || 0}</div>
      </div>
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Guides</span>
          <Clock className="w-4 h-4 text-blue-400" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.active_guides || 0}</div>
      </div>
      <div className="bg-industrial-card border border-industrial-border rounded-xl p-5 shadow-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Completed Guides</span>
          <CheckCircle2 className="w-4 h-4 text-green-400" />
        </div>
        <div className="text-2xl font-bold text-white">{stats?.completed_guides || 0}</div>
      </div>
    </div>
  );
}