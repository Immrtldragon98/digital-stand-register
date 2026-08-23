"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  Clock,
  Download,
  Droplets,
  Gauge,
  Layers,
  RefreshCcw,
  RotateCcw,
  Wrench,
} from "lucide-react";
import StandDetails from "@/components/stand/StandDetails";
import { API_BASE_URL, fetchApi } from "@/lib/api";

const PREP_ORDER = ["YET_TO_READY", "PENDING", "GAUGING", "HYDROTEST", "READY"];
const STATUS_LABEL: Record<string, string> = {
  YET_TO_READY: "Yet to Ready",
  PENDING: "Pending",
  GAUGING: "Gauging",
  HYDROTEST: "Hydrotest",
  READY: "Ready",
  INSTALLED: "Installed",
};

const STATUS_CLASS: Record<string, string> = {
  YET_TO_READY: "border-slate-700 bg-slate-900/60 text-slate-300",
  PENDING: "border-amber-800 bg-amber-950/30 text-amber-300",
  GAUGING: "border-violet-800 bg-violet-950/30 text-violet-300",
  HYDROTEST: "border-cyan-800 bg-cyan-950/30 text-cyan-300",
  READY: "border-emerald-800 bg-emerald-950/30 text-emerald-300",
};

type Props = {
  lines: any[];
  stands: any[];
  onRefresh: () => Promise<void> | void;
};

export default function StandAreaMap({ lines, stands, onRefresh }: Props) {
  const [selected, setSelected] = useState<any>(null);
  const [loadingStand, setLoadingStand] = useState(false);
  const [changeTarget, setChangeTarget] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("ALL");

  const metrics = useMemo(() => {
    const counts = Object.fromEntries(PREP_ORDER.map((x) => [x, 0]));
    stands.forEach((stand) => {
      if (counts[stand.current_status] !== undefined) counts[stand.current_status] += 1;
    });
    return {
      total: stands.length,
      installed: stands.filter((s) => s.current_status === "INSTALLED").length,
      ...counts,
    } as any;
  }, [stands]);

  const readyStands = useMemo(
    () => stands.filter((s) => s.current_status === "READY"),
    [stands]
  );

  const prepStands = useMemo(
    () =>
      stands
        .filter((s) => s.current_status !== "INSTALLED")
        .filter((s) => statusFilter === "ALL" || s.current_status === statusFilter)
        .sort((a, b) => a.code.localeCompare(b.code, undefined, { numeric: true })),
    [stands, statusFilter]
  );

  async function openStand(stand: any) {
    if (!stand?.id) return;
    setLoadingStand(true);
    setError(null);
    try {
      setSelected(await fetchApi(`/stands/${stand.id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load stand details");
    } finally {
      setLoadingStand(false);
    }
  }

  async function updatePreparationStatus(stand: any, status: string) {
    const updatedBy = window.prompt(`Who completed ${STATUS_LABEL[status]} for ${stand.code}?`)?.trim();
    if (!updatedBy) return;
    const remarks = window.prompt("Work completed / remarks (optional):")?.trim() || null;

    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await fetchApi("/operations/stands/status", {
        method: "POST",
        body: JSON.stringify({ stand_code: stand.code, status, updated_by: updatedBy, remarks }),
      });
      setMessage(`${stand.code} moved to ${STATUS_LABEL[status]} by ${updatedBy}.`);
      if (selected?.id === stand.id) {
        setSelected(await fetchApi(`/stands/${stand.id}`));
      }
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update stand status");
    } finally {
      setSaving(false);
    }
  }

  function downloadMonthlyStatus() {
    const now = new Date();
    window.open(
      `${API_BASE_URL}/reports/running-status.xlsx?year=${now.getFullYear()}&month=${now.getMonth() + 1}`,
      "_blank"
    );
  }

  async function submitStandChange(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!changeTarget) return;
    const form = new FormData(event.currentTarget);
    const replacement = String(form.get("replacement") || "");
    const changedBy = String(form.get("changed_by") || "").trim();
    const reason = String(form.get("reason") || "").trim();
    if (!replacement || !changedBy || !reason) {
      setError("Replacement stand, changed by and reason are required.");
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const condition = String(form.get("removed_condition") || "Normal");
      await fetchApi("/operations/stands/change", {
        method: "POST",
        body: JSON.stringify({
          position_id: changeTarget.position.id,
          removed_stand_code: changeTarget.stand.code,
          installed_stand_code: replacement,
          changed_by: changedBy,
          reason,
          notes: String(form.get("notes") || "") || null,
          removed_condition: condition,
          leakage: condition === "Leakage" || condition === "Leakage + Vibration",
          vibration: condition === "Vibration" || condition === "Leakage + Vibration",
        }),
      });
      setMessage(`${changeTarget.stand.code} changed to ${replacement}. Removed stand is now Pending.`);
      setChangeTarget(null);
      setSelected(null);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stand change failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">Live Stand Register</h2>
          <p className="text-sm text-slate-400 mt-1">3 lines × 10 positions, with spare preparation and stand-life tracking.</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={downloadMonthlyStatus} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-industrial-border bg-industrial-card hover:border-industrial-accent text-sm">
            <Download className="w-4 h-4" /> Download Monthly Excel
          </button>
          <button onClick={() => onRefresh()} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-industrial-border bg-industrial-card hover:border-industrial-accent text-sm">
            <RefreshCcw className="w-4 h-4" /> Refresh
          </button>
        </div>
      </div>

      {(message || error) && (
        <div className={`rounded-xl border p-4 text-sm ${error ? "border-red-800 bg-red-950/40 text-red-300" : "border-emerald-800 bg-emerald-950/30 text-emerald-300"}`}>
          {error || message}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-3">
        <Metric label="Total" value={metrics.total} />
        <Metric label="Installed" value={metrics.installed} />
        <Metric label="Yet to Ready" value={metrics.YET_TO_READY} />
        <Metric label="Pending" value={metrics.PENDING} />
        <Metric label="Gauging" value={metrics.GAUGING} />
        <Metric label="Hydrotest" value={metrics.HYDROTEST} />
        <Metric label="Ready" value={metrics.READY} />
      </div>

      <div className="bg-industrial-card border border-industrial-border rounded-xl p-4 md:p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2"><Layers className="w-5 h-5 text-industrial-accent" /> Running Line Status</h2>
        <div className="space-y-5">
          {lines.length === 0 && <div className="text-sm text-slate-500">No lines configured yet.</div>}
          {lines.map((line) => (
            <div key={line.id} className="bg-industrial-dark border border-industrial-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-white">{line.name}</h3>
                <span className="text-xs text-slate-400">10 positions</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 xl:grid-cols-10 gap-2">
                {line.positions?.map((position: any) => {
                  const stand = position.current_stand;
                  return (
                    <div key={position.id} className="min-w-0">
                      <button onClick={() => openStand(stand)} disabled={!stand} className="w-full min-h-28 rounded-lg border border-industrial-border bg-industrial-card hover:border-industrial-accent disabled:opacity-40 text-left p-3 transition">
                        <div className="text-[10px] text-slate-500 uppercase">Position {position.position_number}</div>
                        <div className="text-base font-bold text-white mt-1 truncate">{stand?.code || "Empty"}</div>
                        <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-2"><Clock className="w-3 h-3" />{stand?.campaign_hours ?? 0} h</div>
                        {stand?.leakage && <div className="text-[10px] text-amber-400 flex gap-1 items-center"><Droplets className="w-3 h-3" />Leakage</div>}
                        {stand?.vibration && <div className="text-[10px] text-red-400 flex gap-1 items-center"><Activity className="w-3 h-3" />Vibration</div>}
                        {position.entry_guide_applicable && <div className="text-[10px] text-blue-400 flex gap-1 items-center mt-1"><Gauge className="w-3 h-3" />Guide: {position.current_guide?.code || "None"}</div>}
                      </button>
                      {stand && (
                        <button onClick={() => setChangeTarget({ line, position, stand })} className="mt-1 w-full text-[10px] py-1.5 rounded border border-industrial-border text-slate-400 hover:text-white hover:border-industrial-accent">
                          Change stand
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-industrial-card border border-industrial-border rounded-xl p-4 md:p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Wrench className="w-5 h-5 text-industrial-accent" /> Spare / Preparation Area</h2>
            <p className="text-xs text-slate-400 mt-1">Workflow: Yet to Ready → Pending → Gauging → Hydrotest → Ready.</p>
          </div>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="bg-industrial-dark border border-industrial-border rounded-lg px-3 py-2 text-sm">
            <option value="ALL">All statuses</option>
            {PREP_ORDER.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {prepStands.map((stand) => {
            const currentIndex = PREP_ORDER.indexOf(stand.current_status);
            const next = currentIndex >= 0 && currentIndex < PREP_ORDER.length - 1 ? PREP_ORDER[currentIndex + 1] : null;
            return (
              <div key={stand.id} className={`rounded-xl border p-4 ${STATUS_CLASS[stand.current_status] || "border-industrial-border bg-industrial-dark"}`}>
                <div className="flex items-start justify-between gap-2">
                  <button onClick={() => openStand(stand)} className="text-left min-w-0">
                    <div className="font-bold text-white text-lg">{stand.code}</div>
                    <div className="text-xs mt-1">{STATUS_LABEL[stand.current_status] || stand.current_status}</div>
                    <div className="text-[11px] text-slate-400 mt-2">Life: {stand.lifetime_hours ?? 0} h</div>
                  </button>
                  {next && (
                    <button disabled={saving} onClick={() => updatePreparationStatus(stand, next)} className="shrink-0 inline-flex items-center gap-1 rounded-lg border border-current/30 px-2.5 py-2 text-[11px] hover:bg-white/5 disabled:opacity-50">
                      <RotateCcw className="w-3 h-3" /> {STATUS_LABEL[next]}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
          {prepStands.length === 0 && <div className="text-sm text-slate-500">No stands in this status.</div>}
        </div>
      </div>

      {changeTarget && (
        <div className="bg-industrial-card border border-industrial-accent/60 rounded-xl p-5 md:p-6">
          <div className="flex justify-between gap-3 mb-5">
            <div>
              <h2 className="text-lg font-bold text-white">Change Stand</h2>
              <p className="text-xs text-slate-400 mt-1">{changeTarget.line.name} • Position {changeTarget.position.position_number} • {changeTarget.stand.code} → replacement</p>
            </div>
            <button onClick={() => setChangeTarget(null)} className="text-sm text-slate-400 hover:text-white">Cancel</button>
          </div>
          <form onSubmit={submitStandChange} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Replacement stand">
              <select name="replacement" required className="input-class">
                <option value="">Select READY stand</option>
                {readyStands.map((stand) => <option key={stand.id} value={stand.code}>{stand.code}</option>)}
              </select>
            </Field>
            <Field label="Changed by / Operator">
              <input name="changed_by" required placeholder="Operator name" className="input-class" />
            </Field>
            <Field label="Reason">
              <select name="reason" required className="input-class">
                <option value="">Select reason</option>
                <option>Roll wear / size deviation</option>
                <option>Bearing issue</option>
                <option>Leakage</option>
                <option>Vibration</option>
                <option>Scheduled rotation</option>
                <option>Breakdown</option>
                <option>Other</option>
              </select>
            </Field>
            <Field label="Condition after removal">
              <select name="removed_condition" className="input-class">
                <option>Normal</option>
                <option>Leakage</option>
                <option>Vibration</option>
                <option>Leakage + Vibration</option>
                <option>Other</option>
              </select>
            </Field>
            <div className="md:col-span-2">
              <Field label="Observation / Notes">
                <textarea name="notes" rows={3} placeholder="Optional detailed observation" className="input-class" />
              </Field>
            </div>
            <div className="md:col-span-2 flex justify-end">
              <button disabled={saving || readyStands.length === 0} className="px-5 py-2.5 rounded-lg bg-industrial-accent text-black font-semibold disabled:opacity-50">
                {saving ? "Saving..." : "Confirm Stand Change"}
              </button>
            </div>
          </form>
        </div>
      )}

      {loadingStand && <div className="text-slate-400 text-sm">Loading stand life...</div>}
      {selected && <StandDetails stand={selected} />}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="bg-industrial-card border border-industrial-border rounded-xl p-4"><div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div><div className="text-2xl font-bold text-white mt-1">{value}</div></div>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="block text-xs text-slate-400 mb-1.5">{label}</span>{children}</label>;
}
