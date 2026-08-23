"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import EntryGuideForm from "@/components/entry-guides/EntryGuideForm";
import EntryGuideList from "@/components/entry-guides/EntryGuideList";
import GuideStats from "@/components/entry-guides/GuideStats";
import { fetchApi } from "@/lib/api";

export default function EntryGuidesPage() {
  const [guides, setGuides] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadGuides = async () => {
    try {
      setError("");
      const data = await fetchApi("/entry-guides/");
      setGuides(data);
      setStats({
        total_guides: data.length,
        active_guides: data.filter((g: any) => g.current_position_id).length,
        completed_guides: data.filter((g: any) => !g.current_position_id).length,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load entry guides");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGuides();
  }, []);

  const handleCreateGuide = async (formData: any) => {
    try {
      setError("");
      await fetchApi("/entry-guides/", {
        method: "POST",
        body: JSON.stringify(formData),
      });
      await loadGuides();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add entry guide");
    }
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Entry Guides" />
      <main className="p-4 md:p-6 flex-1">
        {error && <div className="mb-4 p-4 rounded-lg border border-red-800 bg-red-950/40 text-red-300">{error}</div>}
        {loading ? (
          <div className="text-slate-400 text-sm">Loading entry guides...</div>
        ) : (
          <>
            <GuideStats stats={stats} />
            <EntryGuideForm onSubmit={handleCreateGuide} />
            <EntryGuideList guides={guides} />
          </>
        )}
      </main>
    </div>
  );
}
