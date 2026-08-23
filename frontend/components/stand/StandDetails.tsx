"use client";

import { Activity, Clock, Droplets, Gauge, Layers, MapPin } from "lucide-react";

export default function StandDetails({ stand }: { stand: any }) {
  if (!stand) return null;
  const guide = stand.entry_guide;

  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-4 md:p-6 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-industrial-border">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2"><Layers className="w-5 h-5 text-industrial-accent" />Stand {stand.code}</h2>
          <p className="text-xs text-slate-400 mt-1">Life, condition, installation history and entry guide</p>
        </div>
        <span className="px-3 py-1 bg-green-950/50 text-green-400 border border-green-800 rounded-full text-xs font-semibold">{pretty(stand.current_status)}</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <Info icon={<Clock />} label="Total Stand Life" value={`${stand.lifetime_hours ?? 0} h`} />
        <Info icon={<Clock />} label="Current Campaign" value={`${stand.current_campaign_hours ?? 0} h`} />
        <Info icon={<MapPin />} label="Position ID" value={stand.current_position_id ?? "Spare"} />
        <Info icon={<Droplets />} label="Leakage" value={stand.leakage ? "YES" : "No"} warn={stand.leakage} />
        <Info icon={<Activity />} label="Vibration" value={stand.vibration ? "YES" : "No"} warn={stand.vibration} />
        <Info icon={<Gauge />} label="Entry Guide" value={guide ? guide.code : "Not fitted"} />
        <Info icon={<Gauge />} label="Guide Condition" value={guide?.condition ? pretty(guide.condition) : "—"} />
        <Info icon={<Clock />} label="Guide Life" value={guide ? `${guide.lifetime_hours} h` : "—"} />
      </div>

      {stand.condition_notes && (
        <div className="mt-4 border border-industrial-border bg-industrial-dark rounded-lg p-3 text-sm text-slate-300">
          <span className="text-slate-500">Latest condition note:</span> {stand.condition_notes}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 xl:grid-cols-3 gap-5">
        <HistoryPanel title="Preparation History">
          {stand.preparation_history?.length ? stand.preparation_history.map((h: any, i: number) => (
            <HistoryItem key={i}
              title={`${pretty(h.from_status)} → ${pretty(h.to_status)} • ${dateTime(h.changed_at)}`}
              detail={`Updated by: ${h.updated_by || "—"} • Remarks: ${h.remarks || "—"}`}
            />
          )) : <Empty text="No preparation status history recorded yet." />}
        </HistoryPanel>

        <HistoryPanel title="Stand Life History">
          {stand.history?.length ? stand.history.map((h: any, i: number) => (
            <HistoryItem key={i}
              title={`${dateTime(h.installed_at)} → ${h.removed_at ? dateTime(h.removed_at) : "Running"}`}
              detail={`Campaign: ${h.campaign_hours ?? stand.current_campaign_hours ?? 0} h • Installed by: ${h.installed_by || "—"} • Removed by: ${h.removed_by || "—"} • Reason: ${h.removal_reason || "—"}`}
            />
          )) : <Empty text="No stand history recorded yet." />}
        </HistoryPanel>

        <HistoryPanel title="Entry Guide History">
          {!guide && <Empty text="No entry guide fitted. Entry guides apply only at positions 2, 4, 6, 8 and 10." />}
          {guide && (
            <>
              <div className="mb-3 text-xs text-slate-400">Guide {guide.code} • {pretty(guide.condition)} • Current campaign {guide.current_campaign_hours ?? 0} h</div>
              {guide.condition_notes && <div className="mb-3 text-xs text-slate-400">Condition note: {guide.condition_notes}</div>}
              {guide.history?.length ? guide.history.map((h: any, i: number) => (
                <HistoryItem key={i}
                  title={`${dateTime(h.installed_at)} → ${h.removed_at ? dateTime(h.removed_at) : "Running"}`}
                  detail={`Campaign: ${h.campaign_hours ?? guide.current_campaign_hours ?? 0} h • Installed by: ${h.installed_by || "—"} • Removed by: ${h.removed_by || "—"} • Removal reason: ${h.removal_reason || "—"}`}
                />
              )) : <Empty text="No entry guide history recorded yet." />}
            </>
          )}
        </HistoryPanel>
      </div>
    </div>
  );
}

function pretty(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function dateTime(value: string) {
  return new Date(value).toLocaleString();
}

function Info({ icon, label, value, warn = false }: { icon: React.ReactNode; label: string; value: any; warn?: boolean }) {
  return <div className="bg-industrial-dark border border-industrial-border rounded-lg p-3"><div className="w-4 h-4 text-slate-500 mb-2">{icon}</div><div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div><div className={`font-semibold mt-1 ${warn ? "text-red-400" : "text-white"}`}>{value}</div></div>;
}

function HistoryPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><h3 className="text-sm font-semibold text-white mb-3">{title}</h3><div className="space-y-2">{children}</div></div>;
}

function HistoryItem({ title, detail }: { title: string; detail: string }) {
  return <div className="border border-industrial-border rounded-lg p-3 text-xs text-slate-300"><div>{title}</div><div className="text-slate-500 mt-1 leading-relaxed">{detail}</div></div>;
}

function Empty({ text }: { text: string }) {
  return <div className="text-xs text-slate-500">{text}</div>;
}
