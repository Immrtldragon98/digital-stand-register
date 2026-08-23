"use client";

import { MapPin, Cpu } from "lucide-react";

export default function PositionMapMock() {
  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl mb-8">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Cpu className="w-5 h-5 text-industrial-accent" />
        Plant Grid Telemetry Map
      </h2>
      <div className="h-64 bg-industrial-dark border border-industrial-border rounded-lg flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px]"></div>
        <div className="flex flex-col items-center text-slate-400 gap-2">
          <MapPin className="w-8 h-8 text-industrial-accent animate-bounce" />
          <span className="text-xs font-mono uppercase tracking-widest">Interactive Plant Schematic Grid Active</span>
        </div>
      </div>
    </div>
  );
}