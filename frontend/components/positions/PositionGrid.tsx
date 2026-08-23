"use client";

import { Compass, MapPin } from "lucide-react";

export default function PositionGrid({ positions }: { positions: any[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {positions && positions.length > 0 ? (
        positions.map((pos, idx) => (
          <div key={idx} className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <span className="font-bold text-white flex items-center gap-2">
                <Compass className="w-5 h-5 text-industrial-accent" />
                {pos.name}
              </span>
              <span className="text-xs px-2.5 py-1 bg-green-950/50 text-green-400 border border-green-800 rounded-full">
                Online
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <MapPin className="w-4 h-4 text-slate-500" />
              <span>Coords: {pos.coordinates || "N/A"}</span>
            </div>
          </div>
        ))
      ) : (
        <div className="col-span-3 text-slate-500 text-center py-8">No positions available in registry.</div>
      )}
    </div>
  );
}