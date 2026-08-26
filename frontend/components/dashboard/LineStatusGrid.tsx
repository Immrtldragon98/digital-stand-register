"use client";

function formatRunTime(hoursValue: unknown) {
  const hours = Number(hoursValue ?? 0);
  if (!Number.isFinite(hours) || hours <= 0) return "0 h";
  const days = Math.floor(hours / 24);
  const remainingHours = Math.floor(hours % 24);
  if (days === 0) return `${hours.toFixed(hours < 10 ? 1 : 0)} h`;
  return `${days}d ${remainingHours}h`;
}

export default function LineStatusGrid({ lines }: { lines: any[] }) {
  if (!lines?.length) return <div className="text-slate-500 text-sm">No running lines mapped.</div>;

  return (
    <div className="grid gap-3">
      {lines.map((line) => (
        <section key={line.id} className="rounded-xl border border-slate-800 bg-slate-900/45 p-3">
          <div className="grid grid-cols-[52px_repeat(10,minmax(72px,1fr))] gap-2 items-stretch">
            <div className="rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col items-center justify-center">
              <div className="text-lg font-black text-blue-400">{line.name}</div>
              <div className="text-[10px] text-emerald-400 mt-1">10 / 10</div>
            </div>
            {line.positions?.map((position: any) => {
              const stand = position.current_stand;
              return (
                <div key={position.id} className="min-w-0 rounded-lg border border-slate-700 bg-slate-950/45 px-2 py-2 hover:border-blue-500 transition-colors">
                  <div className="text-[9px] uppercase tracking-wide text-slate-500">P{position.position_number}</div>
                  <div className="text-sm font-bold text-white truncate mt-0.5">{stand?.code || "—"}</div>
                  <div className="text-[9px] text-slate-400 mt-1 truncate" title={`${stand?.campaign_hours ?? 0} running hours`}>
                    Run: {formatRunTime(stand?.campaign_hours)}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
