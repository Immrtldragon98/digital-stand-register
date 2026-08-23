"use client";

import {
  Cpu,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function LineStatusGrid({
  lines,
}: {
  lines: any[];
}) {
  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl mb-6">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Cpu className="w-5 h-5 text-industrial-accent" />
        Production Line Status
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {lines && lines.length > 0 ? (
          lines.map((line) => {
            const positions = line.positions || [];

            const activePositions = positions.filter(
              (position: any) => position.current_stand
            ).length;

            const totalPositions = positions.length;

            const operational =
              activePositions === totalPositions;

            return (
              <div
                key={line.id}
                className="bg-industrial-dark border border-industrial-border rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="font-bold text-white text-sm">
                    {line.name}
                  </span>

                  {operational ? (
                    <span className="flex items-center gap-1 text-xs px-2 py-1 bg-green-950/50 text-green-400 border border-green-800 rounded">
                      <CheckCircle2 className="w-3 h-3" />
                      Operational
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs px-2 py-1 bg-amber-950/50 text-amber-400 border border-amber-800 rounded">
                      <AlertCircle className="w-3 h-3" />
                      Attention
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="bg-industrial-card rounded-lg p-3">
                    <p className="text-xs text-slate-500">
                      Positions
                    </p>

                    <p className="text-xl font-bold text-white">
                      {totalPositions}
                    </p>
                  </div>

                  <div className="bg-industrial-card rounded-lg p-3">
                    <p className="text-xs text-slate-500">
                      Active
                    </p>

                    <p className="text-xl font-bold text-green-400">
                      {activePositions}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  {positions.map((position: any) => (
                    <div
                      key={position.id}
                      className="flex items-center justify-between border-t border-industrial-border pt-2"
                    >
                      <span className="text-xs text-slate-400">
                        Position {position.position_number}
                      </span>

                      <div className="text-right">
                        <p className="text-xs font-semibold text-white">
                          {position.current_stand?.code || "No Stand"}
                        </p>

                        <p className="text-[10px] text-slate-500">
                          {position.current_stand?.campaign_hours ?? 0} h
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-3 text-slate-500 text-sm">
            No production lines currently mapped.
          </div>
        )}
      </div>
    </div>
  );
}