"use client";

import { FileText } from "lucide-react";

function label(value: string | null | undefined) {
  if (!value) return "—";
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function EntryGuideList({ guides }: { guides: any[] }) {
  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-5">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5 text-industrial-accent" />
        Entry Guide List
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-industrial-dark text-slate-400 border-b border-industrial-border">
            <tr>
              <th className="px-4 py-3">Guide ID</th>
              <th className="px-4 py-3">New / Old</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Position</th>
              <th className="px-4 py-3">Life</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-industrial-border">
            {guides.length > 0 ? guides.map((guide) => (
              <tr key={guide.id} className="hover:bg-industrial-dark/50">
                <td className="px-4 py-3 font-semibold text-white">{guide.code}</td>
                <td className="px-4 py-3">{label(guide.condition)}</td>
                <td className="px-4 py-3">{label(guide.current_status)}</td>
                <td className="px-4 py-3">{guide.current_position_id ?? "Not installed"}</td>
                <td className="px-4 py-3">{Number(guide.lifetime_hours || 0).toFixed(1)} h</td>
              </tr>
            )) : (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-500">No entry guides added yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
