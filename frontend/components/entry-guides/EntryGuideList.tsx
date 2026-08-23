"use client";

import { FileText } from "lucide-react";

export default function EntryGuideList({ guides }: { guides: any[] }) {
  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5 text-industrial-accent" />
        Registered Entry Guides Registry
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-industrial-dark text-xs uppercase text-slate-400 border-b border-industrial-border">
            <tr>
              <th className="px-4 py-3">Guide Number</th>
              <th className="px-4 py-3">Target Location</th>
              <th className="px-4 py-3">Asset ID</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-industrial-border">
            {guides && guides.length > 0 ? (
              guides.map((guide, idx) => (
                <tr key={idx} className="hover:bg-industrial-dark/50">
                  <td className="px-4 py-3 font-medium text-white">{guide.guide_number}</td>
                  <td className="px-4 py-3 text-slate-400">{guide.target_location}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">{guide.asset_id}</td>
                  <td className="px-4 py-3">
                    <span className="px-2.5 py-1 bg-blue-950/50 text-blue-400 border border-blue-800 rounded-full text-xs">
                      {guide.status || "Active"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">
                    {new Date(guide.created_at || Date.now()).toLocaleDateString()}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  No entry guides found in system.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}