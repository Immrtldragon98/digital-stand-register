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

  const loadGuides = async () => {
    try {
      const data = await fetchApi("/entry-guides");
      setGuides(data);
      setStats({
        total_guides: data.length,
        active_guides: data.filter((g: any) => g.status === "Active" || !g.status).length,
        completed_guides: data.filter((g: any) => g.status === "Completed").length,
      });
    } catch (err) {
      console.error("Failed to fetch entry guides:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGuides();
  }, []);

  const handleCreateGuide = async (formData: any) => {
    try {
      await fetchApi("/entry-guides", {
        method: "POST",
        body: JSON.stringify(formData),
      });
      loadGuides();
    } catch (err) {
      console.error("Failed to create entry guide:", err);
    }
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Entry Guides Management" />
      <main className="p-6 flex-1">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
            Loading entry guides registry...
          </div>
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