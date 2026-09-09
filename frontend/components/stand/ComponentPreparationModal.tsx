"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchApi } from "@/lib/api";
import { getUser } from "@/lib/auth";

type ComponentRow = {
  component_type_id: number;
  name: string;
  required_qty: number | null;
  new_qty: number;
  reused_qty: number;
  carried_life_hours: number | null;
  is_extra: boolean;
};

export default function ComponentPreparationModal({ stand, onClose, onComplete }: { stand: any; onClose: () => void; onComplete: () => Promise<void> | void }) {
  const [rows, setRows] = useState<ComponentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notes, setNotes] = useState("");
  const user = getUser();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchApi(`/stands/${stand.id}/components`);
        setRows(data.components || []);
        setNotes(data.notes || "");
      } catch (e: any) {
        setError(e.message || "Could not load components");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [stand.id]);

  const filled = useMemo(() => rows.filter((row) => (row.new_qty || 0) + (row.reused_qty || 0) > 0).length, [rows]);

  function change(id: number, key: "new_qty" | "reused_qty", value: string) {
    const amount = Math.max(0, Number(value) || 0);
    setRows((current) => current.map((row) => row.component_type_id === id ? { ...row, [key]: amount } : row));
  }

  async function save(skip: boolean) {
    setSaving(true);
    setError("");
    try {
      const componentBody = {
        prepared_by: user?.username || "Operator",
        notes,
        skip,
        items: skip ? [] : rows.map((row) => ({
          component_type_id: row.component_type_id,
          new_qty: row.new_qty || 0,
          reused_qty: row.reused_qty || 0,
          carried_life_hours: row.carried_life_hours,
        })),
      };
      await fetchApi(`/stands/${stand.id}/components`, {
        method: "POST",
        body: JSON.stringify(componentBody),
      });
      await fetchApi("/operations/stands/status", {
        method: "POST",
        body: JSON.stringify({
          stand_code: stand.code,
          status: "GAUGING",
          updated_by: user?.username || "Operator",
          remarks: skip ? "Components skipped before gauging" : "Components saved before gauging",
        }),
      });
      await onComplete();
      onClose();
    } catch (e: any) {
      setError(e.message || "Could not save components");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[60] bg-black/75 flex items-center justify-center p-4" onClick={onClose}>
      <div className="w-full max-w-4xl max-h-[90vh] overflow-auto rounded-xl border border-slate-700 bg-slate-950 p-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-blue-400 font-bold">Before Gauging</div>
            <h2 className="text-lg font-black text-white">Stand {stand.code} · Components</h2>
            <p className="text-xs text-slate-400 mt-1">Record what was fitted, or skip this step. Save/Skip moves the stand to Gauging.</p>
          </div>
          <button onClick={onClose} className="text-xs px-3 py-1 rounded border border-slate-700">Close</button>
        </div>

        {error && <div className="mb-3 rounded border border-red-900 bg-red-950/30 p-2 text-xs text-red-300">{error}</div>}

        {loading ? <div className="p-6 text-sm text-slate-500">Loading component list...</div> : <>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-xs">
              <thead className="bg-slate-900 text-slate-400"><tr><th className="p-2 text-left">Component</th><th className="p-2">Required</th><th className="p-2">New</th><th className="p-2">Old / Reused</th><th className="p-2">Check</th></tr></thead>
              <tbody>{rows.map((row) => {
                const total = (row.new_qty || 0) + (row.reused_qty || 0);
                const complete = row.required_qty == null ? total > 0 : total === row.required_qty;
                return <tr key={row.component_type_id} className="border-t border-slate-800">
                  <td className="p-2 font-semibold text-white">{row.name}{row.is_extra && <span className="ml-2 text-[9px] text-blue-300">EVEN STAND EXTRA</span>}</td>
                  <td className="p-2 text-center">{row.required_qty ?? "As used"}</td>
                  <td className="p-2 text-center"><input type="number" min="0" value={row.new_qty || 0} onChange={(e) => change(row.component_type_id, "new_qty", e.target.value)} className="w-16 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-center" /></td>
                  <td className="p-2 text-center"><input type="number" min="0" value={row.reused_qty || 0} onChange={(e) => change(row.component_type_id, "reused_qty", e.target.value)} className="w-16 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-center" /></td>
                  <td className={`p-2 text-center font-bold ${complete ? "text-emerald-300" : "text-slate-600"}`}>{complete ? "✓" : "—"}</td>
                </tr>;
              })}</tbody>
            </table>
          </div>

          <div className="mt-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex-1">
              <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Component remarks (optional)" className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-xs" />
              <div className="mt-1 text-[10px] text-slate-500">{filled} component types recorded. You can save partial information or skip.</div>
            </div>
            <div className="flex gap-2">
              <button disabled={saving} onClick={() => save(true)} className="rounded border border-slate-600 px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-900 disabled:opacity-40">Skip → Gauging</button>
              <button disabled={saving} onClick={() => save(false)} className="rounded bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-500 disabled:opacity-40">Save → Gauging</button>
            </div>
          </div>
        </>}
      </div>
    </div>
  );
}
