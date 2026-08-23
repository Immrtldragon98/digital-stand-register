"use client";

import { useCallback, useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import StandAreaMap from "@/components/stand-area/StandAreaMap";
import { fetchApi } from "@/lib/api";

export default function StandAreaPage() {
  const [lines, setLines] = useState<any[]>([]);
  const [stands, setStands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [lineData, standData] = await Promise.all([
        fetchApi("/dashboard/"),
        fetchApi("/stands/"),
      ]);
      setLines(lineData);
      setStands(standData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load stand area");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Finishing Mill Stand Area" />
      <main className="p-4 md:p-6 flex-1">
        {loading && <div className="text-slate-400 font-mono text-sm">Loading stand area...</div>}
        {error && <div className="bg-red-950/40 border border-red-800 rounded-xl p-5 text-red-300">{error}</div>}
        {!loading && !error && <StandAreaMap lines={lines} stands={stands} onRefresh={load} />}
      </main>
    </div>
  );
}
