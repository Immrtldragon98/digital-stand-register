"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Row = {
  date: string;
  activity: string;
  stand: string;
  done_by: string;
  details: string;
};

export default function ActivityPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchApi("/activity/")
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="History" />
      <main className="p-4 md:p-6 flex-1">
        <div className="mb-4">
          <h1 className="text-xl font-bold text-white">Stand Work History</h1>
          <p className="text-sm text-slate-400">Stand changes plus Gauging, Hydrotest and Ready completion only.</p>
        </div>
        {error && <div className="mb-3 text-red-300">{error}</div>}
        <div className="overflow-x-auto border border-industrial-border rounded-lg bg-industrial-card">
          <table className="w-full min-w-[820px] text-sm border-collapse">
            <thead className="bg-slate-800 text-slate-200">
              <tr>
                <th className="border border-slate-700 px-3 py-2 text-left">Date & Time</th>
                <th className="border border-slate-700 px-3 py-2 text-left">Activity</th>
                <th className="border border-slate-700 px-3 py-2 text-left">Stand</th>
                <th className="border border-slate-700 px-3 py-2 text-left">Done By</th>
                <th className="border border-slate-700 px-3 py-2 text-left">Reason / Remarks</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={`${row.date}-${i}`} className="even:bg-slate-900/40">
                  <td className="border border-slate-800 px-3 py-2 whitespace-nowrap">{new Date(row.date).toLocaleString()}</td>
                  <td className="border border-slate-800 px-3 py-2 font-medium">{row.activity}</td>
                  <td className="border border-slate-800 px-3 py-2 font-semibold">{row.stand}</td>
                  <td className="border border-slate-800 px-3 py-2">{row.done_by}</td>
                  <td className="border border-slate-800 px-3 py-2">{row.details || "—"}</td>
                </tr>
              ))}
              {!loading && rows.length === 0 && <tr><td colSpan={5} className="p-5 text-center text-slate-500">No stand work history yet.</td></tr>}
              {loading && <tr><td colSpan={5} className="p-5 text-center text-slate-400">Loading...</td></tr>}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
