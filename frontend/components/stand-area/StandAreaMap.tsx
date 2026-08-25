"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Clock, Download, RefreshCcw } from "lucide-react";
import StandDetails from "@/components/stand/StandDetails";
import { API_BASE_URL, fetchApi } from "@/lib/api";

const STATUS_ORDER = ["READY", "HYDROTEST", "GAUGING", "PENDING", "YET_TO_READY"];
const LABEL: Record<string, string> = {
  READY: "Ready",
  HYDROTEST: "Hydrotest",
  GAUGING: "Gauging",
  PENDING: "Pending",
  YET_TO_READY: "Yet to Ready",
};
const ROW_STYLE: Record<string, string> = {
  READY: "border-emerald-800/70 bg-emerald-950/20",
  HYDROTEST: "border-blue-800/70 bg-blue-950/20",
  GAUGING: "border-violet-800/70 bg-violet-950/20",
  PENDING: "border-orange-800/70 bg-orange-950/20",
  YET_TO_READY: "border-slate-700 bg-slate-900/30",
};
const TEXT_STYLE: Record<string, string> = {
  READY: "text-emerald-400",
  HYDROTEST: "text-blue-400",
  GAUGING: "text-violet-400",
  PENDING: "text-orange-400",
  YET_TO_READY: "text-slate-400",
};
const NEXT: Record<string, string | null> = {
  YET_TO_READY: "PENDING",
  PENDING: "GAUGING",
  GAUGING: "HYDROTEST",
  HYDROTEST: "READY",
  READY: null,
};

type Props = { lines: any[]; stands: any[]; onRefresh: () => Promise<void> | void };

export default function StandAreaMap({ lines, stands, onRefresh }: Props) {
  const [selected, setSelected] = useState<any>(null);
  const [loadingStand, setLoadingStand] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const grouped = useMemo(() => {
    const result: Record<string, any[]> = Object.fromEntries(STATUS_ORDER.map((s) => [s, []]));
    stands.forEach((stand) => {
      if (result[stand.current_status]) result[stand.current_status].push(stand);
    });
    STATUS_ORDER.forEach((s) => result[s].sort((a, b) => a.code.localeCompare(b.code, undefined, { numeric: true })));
    return result;
  }, [stands]);

  async function openStand(stand: any) {
    if (!stand?.id) return;
    setLoadingStand(true); setError(null);
    try { setSelected(await fetchApi(`/stands/${stand.id}`)); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load stand details"); }
    finally { setLoadingStand(false); }
  }

  async function moveForward(stand: any) {
    const next = NEXT[stand.current_status];
    if (!next) return;
    let updatedBy = "System";
    let remarks: string | null = null;
    if (["GAUGING", "HYDROTEST", "READY"].includes(next)) {
      updatedBy = window.prompt(`Who completed ${LABEL[next]} for ${stand.code}?`)?.trim() || "";
      if (!updatedBy) return;
      remarks = window.prompt("Remarks (optional):")?.trim() || null;
    }
    setSaving(true); setError(null); setMessage(null);
    try {
      await fetchApi("/operations/stands/status", {
        method: "POST",
        body: JSON.stringify({ stand_code: stand.code, status: next, updated_by: updatedBy, remarks }),
      });
      setMessage(`${stand.code} moved to ${LABEL[next]}.`);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    } finally { setSaving(false); }
  }

  function downloadMonthlyStatus() {
    const now = new Date();
    window.open(`${API_BASE_URL}/reports/running-status.xlsx?year=${now.getFullYear()}&month=${now.getMonth() + 1}`, "_blank");
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">Stand Area</h2>
          <p className="text-sm text-slate-400">Preparation flow only. Removed running stands return to Pending.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={downloadMonthlyStatus} className="px-3 py-2 text-xs rounded-lg border border-slate-700 hover:border-blue-500 flex items-center gap-2"><Download className="w-3.5 h-3.5" /> Excel</button>
          <button onClick={() => onRefresh()} className="px-3 py-2 text-xs rounded-lg border border-slate-700 hover:border-blue-500 flex items-center gap-2"><RefreshCcw className="w-3.5 h-3.5" /> Refresh</button>
        </div>
      </div>

      {(message || error) && <div className={`rounded-lg border px-3 py-2 text-sm ${error ? "border-red-800 text-red-300" : "border-emerald-800 text-emerald-300"}`}>{error || message}</div>}

      <section className="space-y-2">
        {STATUS_ORDER.map((status) => (
          <div key={status} className={`rounded-xl border p-3 ${ROW_STYLE[status]}`}>
            <div className="flex items-center gap-3">
              <div className={`w-28 shrink-0 font-bold text-sm ${TEXT_STYLE[status]}`}>{LABEL[status]}</div>
              <div className="flex gap-2 overflow-x-auto flex-1 pb-1">
                {grouped[status].map((stand) => {
                  const next = NEXT[status];
                  return (
                    <div key={stand.id} className="shrink-0 flex items-center gap-2 border border-slate-700/70 bg-slate-950/40 rounded-lg pl-3 pr-1.5 py-1.5">
                      <button onClick={() => openStand(stand)} className="text-left">
                        <div className="font-bold text-white text-sm">{stand.code}</div>
                        <div className="text-[10px] text-slate-500">{stand.lifetime_hours ?? 0} h</div>
                      </button>
                      {next && <button disabled={saving} onClick={() => moveForward(stand)} className={`text-[10px] px-2 py-1 rounded border border-slate-600 hover:bg-white/5 ${TEXT_STYLE[next]}`}>{LABEL[next]}</button>}
                    </div>
                  );
                })}
                {!grouped[status].length && <span className="text-xs text-slate-500 py-2">No stands</span>}
              </div>
              <div className={`text-xs shrink-0 ${TEXT_STYLE[status]}`}>{grouped[status].length}</div>
            </div>
          </div>
        ))}
      </section>

      {loadingStand && <div className="text-xs text-slate-400">Loading stand details...</div>}
      {selected && (
        <div className="space-y-2">
          <div className="flex justify-end"><button onClick={() => setSelected(null)} className="text-xs text-slate-400 hover:text-white">Close details</button></div>
          <StandDetails stand={selected} />
        </div>
      )}
    </div>
  );
}
