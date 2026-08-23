"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LineStatusGrid from "@/components/dashboard/LineStatusGrid";
import { fetchApi } from "@/lib/api";

export default function DashboardPage() {
  const [lines, setLines] = useState<any[]>([]);
  const [stands, setStands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setError(null);
        const [dashboardData, standData] = await Promise.all([
          fetchApi("/dashboard/"),
          fetchApi("/stands/"),
        ]);
        setLines(dashboardData);
        setStands(standData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load stand data");
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  const running = stands.filter((s) => s.current_status === "INSTALLED").length;
  const ready = stands.filter((s) => s.current_status === "READY").length;
  const pending = stands.filter((s) => ["YET_TO_READY", "PENDING", "GAUGING", "HYDROTEST"].includes(s.current_status)).length;
  const inp = stands.filter((s) => s.current_status === "INP").length;

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Stand Area Home" />
      <main className="p-4 md:p-6 flex-1 space-y-6">
        {loading && <div className="text-slate-400 text-sm">Loading stand status...</div>}
        {error && <div className="bg-red-950/40 border border-red-800 rounded-xl p-4 text-red-300">{error}</div>}

        {!loading && !error && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <Card label="Known Stands" value={stands.length} />
              <Card label="Running" value={running} />
              <Card label="Ready" value={ready} />
              <Card label="Work Pending" value={pending} />
              <Card label="INP" value={inp} />
            </div>

            <div className="bg-industrial-card border border-industrial-border rounded-xl p-4 md:p-6">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-white">Running Stands</h2>
                <p className="text-sm text-slate-400 mt-1">W1, W2 and W3 - 10 positions each.</p>
              </div>
              <LineStatusGrid lines={lines} />
            </div>

            <div className="text-sm text-slate-400">
              Use <b className="text-slate-200">Stand Status</b> to see spare preparation and stand life. Use <b className="text-slate-200">Change Stand</b> when a stand is replaced in a line.
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Card({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-4">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="text-2xl font-bold text-white mt-1">{value}</div>
    </div>
  );
}
