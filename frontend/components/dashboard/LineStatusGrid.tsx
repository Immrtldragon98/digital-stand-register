"use client";

export default function LineStatusGrid({ lines }: { lines: any[] }) {
  if (!lines?.length) return <div className="text-slate-500 text-sm">No running lines mapped.</div>;

  return (
    <div className="space-y-3 mb-5">
      {lines.map((line) => (
        <div key={line.id} className="bg-industrial-card border border-industrial-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-white">{line.name}</h3>
            <span className="text-xs text-slate-400">10 stands</span>
          </div>
          <div className="overflow-x-auto pb-1">
            <div className="flex gap-2 min-w-max">
              {line.positions?.map((position: any) => (
                <div key={position.id} className="w-28 shrink-0 rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2">
                  <div className="text-[10px] text-slate-500">Pos {position.position_number}</div>
                  <div className="text-base font-bold text-white mt-0.5">{position.current_stand?.code || "—"}</div>
                  <div className="text-[10px] text-slate-400 mt-1">{position.current_stand?.campaign_hours ?? 0} h</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
