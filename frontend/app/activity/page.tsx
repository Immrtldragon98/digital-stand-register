"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Row = {
  date: string;
  activity: string;
  stand: string;
  done_by: string;
  details: string;
};

type StageEvent = { date: string; done_by: string; details: string };
type StandSummary = {
  stand: string;
  gauging?: StageEvent;
  hydrotest?: StageEvent;
  ready?: StageEvent;
  latest: number;
};

function StageCell({ event }: { event?: StageEvent }) {
  if (!event) return <span className="text-slate-600">—</span>;
  return (
    <div className="leading-tight">
      <div className="font-semibold text-slate-100">{event.done_by || "—"}</div>
      <div className="mt-1 text-[10px] text-slate-500">{new Date(event.date).toLocaleString()}</div>
    </div>
  );
}

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

  const readiness = useMemo(() => {
    const map = new Map<string, StandSummary>();
    for (const row of rows) {
      if (!["Gauging", "Hydrotest", "Ready"].includes(row.activity)) continue;
      const key = row.stand;
      const stamp = new Date(row.date).getTime();
      const item = map.get(key) || { stand: key, latest: stamp };
      item.latest = Math.max(item.latest, stamp);
      const event = { date: row.date, done_by: row.done_by, details: row.details };
      if (row.activity === "Gauging" && !item.gauging) item.gauging = event;
      if (row.activity === "Hydrotest" && !item.hydrotest) item.hydrotest = event;
      if (row.activity === "Ready" && !item.ready) item.ready = event;
      map.set(key, item);
    }
    return Array.from(map.values()).sort((a, b) => b.latest - a.latest);
  }, [rows]);

  const changes = useMemo(() => rows.filter((r) => r.activity === "Stand Change"), [rows]);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="History" />
      <main className="p-4 md:p-6 flex-1 space-y-5">
        <div>
          <h1 className="text-xl font-bold text-white">Stand Work History</h1>
          <p className="text-sm text-slate-400">One row per stand for Gauging, Hydrotest and Ready. Stand changes stay separate.</p>
        </div>

        {error && <div className="text-red-300">{error}</div>}

        <section>
          <div className="mb-2 flex items-end justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold text-white">Readiness History</h2>
              <p className="text-[11px] text-slate-500">Latest recorded completion for each stand.</p>
            </div>
            <div className="text-[11px] text-slate-500">{readiness.length} stands</div>
          </div>
          <div className="overflow-x-auto border border-industrial-border rounded-lg bg-industrial-card">
            <table className="w-full min-w-[820px] text-sm border-collapse">
              <thead className="bg-slate-800 text-slate-200">
                <tr>
                  <th className="border border-slate-700 px-3 py-2 text-left w-[120px]">Stand</th>
                  <th className="border border-slate-700 px-3 py-2 text-left">Gauging</th>
                  <th className="border border-slate-700 px-3 py-2 text-left">Hydrotest</th>
                  <th className="border border-slate-700 px-3 py-2 text-left">Ready</th>
                  <th className="border border-slate-700 px-3 py-2 text-left">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {readiness.map((row) => {
                  const remarks = row.ready?.details || row.hydrotest?.details || row.gauging?.details || "";
                  return (
                    <tr key={row.stand} className="even:bg-slate-900/40">
                      <td className="border border-slate-800 px-3 py-3 font-black text-white">{row.stand}</td>
                      <td className="border border-slate-800 px-3 py-3"><StageCell event={row.gauging} /></td>
                      <td className="border border-slate-800 px-3 py-3"><StageCell event={row.hydrotest} /></td>
                      <td className="border border-slate-800 px-3 py-3"><StageCell event={row.ready} /></td>
                      <td className="border border-slate-800 px-3 py-3 text-slate-300">{remarks || "—"}</td>
                    </tr>
                  );
                })}
                {!loading && readiness.length === 0 && <tr><td colSpan={5} className="p-5 text-center text-slate-500">No readiness history yet.</td></tr>}
                {loading && <tr><td colSpan={5} className="p-5 text-center text-slate-400">Loading...</td></tr>}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <div className="mb-2">
            <h2 className="text-sm font-bold text-white">Stand Changes</h2>
            <p className="text-[11px] text-slate-500">Removed → replacement stand, operator and reason.</p>
          </div>
          <div className="overflow-x-auto border border-industrial-border rounded-lg bg-industrial-card">
            <table className="w-full min-w-[760px] text-sm border-collapse">
              <thead className="bg-slate-800 text-slate-200"><tr><th className="border border-slate-700 px-3 py-2 text-left">Date & Time</th><th className="border border-slate-700 px-3 py-2 text-left">Stand Change</th><th className="border border-slate-700 px-3 py-2 text-left">Done By</th><th className="border border-slate-700 px-3 py-2 text-left">Reason / Remarks</th></tr></thead>
              <tbody>
                {changes.map((row, i) => <tr key={`${row.date}-${i}`} className="even:bg-slate-900/40"><td className="border border-slate-800 px-3 py-2 whitespace-nowrap">{new Date(row.date).toLocaleString()}</td><td className="border border-slate-800 px-3 py-2 font-semibold text-white">{row.stand}</td><td className="border border-slate-800 px-3 py-2">{row.done_by}</td><td className="border border-slate-800 px-3 py-2">{row.details || "—"}</td></tr>)}
                {!loading && changes.length === 0 && <tr><td colSpan={4} className="p-5 text-center text-slate-500">No stand changes recorded yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
