"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import DashboardMetrics from "@/components/dashboard/DashboardMetrics";
import LineStatusGrid from "@/components/dashboard/LineStatusGrid";
import QuickActions from "@/components/dashboard/QuickActions";
import RecentActivity from "@/components/dashboard/RecentActivity";
import { fetchApi } from "@/lib/api";

export default function DashboardPage() {
  const [lines, setLines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const dashboardData = await fetchApi("/dashboard/");
        setLines(dashboardData);
      } catch (err) {
        console.error("Failed to load dashboard:", err);

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dashboard"
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const totalPositions = lines.reduce(
    (total, line) => total + (line.positions?.length || 0),
    0
  );

  const activeStands = lines.reduce(
    (total, line) =>
      total +
      (line.positions?.filter(
        (position: any) => position.current_stand
      ).length || 0),
    0
  );

  const stats = {
    total_stands: totalPositions,
    active_stands: activeStands,
    total_operations: 0,
    system_alerts: 0,
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Plant Operations Dashboard" />

      <main className="p-6 flex-1">
        {loading && (
          <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
            Loading plant telemetry...
          </div>
        )}

        {error && (
          <div className="bg-red-950/40 border border-red-800 rounded-xl p-5 text-red-300">
            <p className="font-semibold">
              Dashboard connection failed
            </p>

            <p className="text-sm mt-2 font-mono">
              {error}
            </p>
          </div>
        )}

        {!loading && !error && (
          <>
            <DashboardMetrics stats={stats} />

            <LineStatusGrid lines={lines} />

            <RecentActivity logs={[]} />

            <QuickActions />
          </>
        )}
      </main>
    </div>
  );
}