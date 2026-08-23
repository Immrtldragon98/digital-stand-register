"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import PositionGrid from "@/components/positions/PositionGrid";
import PositionMapMock from "@/components/positions/PositionMapMock";
import { fetchApi } from "@/lib/api";

export default function PositionsPage() {
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPositions() {
      try {
        const data = await fetchApi("/positions");
        setPositions(data);
      } catch (err) {
        console.error("Failed to load positions mapping:", err);
      } finally {
        setLoading(false);
      }
    }
    loadPositions();
  }, []);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Positions Mapping Grid" />
      <main className="p-6 flex-1">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
            Loading position map matrix...
          </div>
        ) : (
          <>
            <PositionMapMock />
            <PositionGrid positions={positions} />
          </>
        )}
      </main>
    </div>
  );
}