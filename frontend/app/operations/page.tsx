"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Stand = { id: number; code: string; current_status: string };

type PositionRow = {
  id: number;
  lineName: string;
  positionNumber: number;
  currentStand: string;
};

export default function OperationsPage() {
  const [stands, setStands] = useState<Stand[]>([]);
  const [positions, setPositions] = useState<PositionRow[]>([]);
  const [positionId, setPositionId] = useState("");
  const [replacement, setReplacement] = useState("");
  const [changedBy, setChangedBy] = useState("");
  const [reason, setReason] = useState("");
  const [condition, setCondition] = useState("Normal");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setError("");
      const [lineData, standData] = await Promise.all([
        fetchApi("/dashboard/"),
        fetchApi("/stands/"),
      ]);
      const mapped: PositionRow[] = [];
      lineData.forEach((line: any) =>
        line.positions?.forEach((pos: any) => {
          if (pos.current_stand) {
            mapped.push({
              id: pos.id,
              lineName: line.name,
              positionNumber: pos.position_number,
              currentStand: pos.current_stand.code,
            });
          }
        })
      );
      setPositions(mapped);
      setStands(standData);
      if (!positionId && mapped.length) setPositionId(String(mapped[0].id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load stand data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const selectedPosition = useMemo(
    () => positions.find((p) => p.id === Number(positionId)),
    [positions, positionId]
  );

  const readyStands = stands.filter((s) => s.current_status === "READY");

  const submitChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPosition || !replacement || !changedBy.trim() || !reason) {
      setError("Select the position, replacement stand, operator and reason.");
      return;
    }

    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      await fetchApi("/operations/stands/change", {
        method: "POST",
        body: JSON.stringify({
          position_id: selectedPosition.id,
          removed_stand_code: selectedPosition.currentStand,
          installed_stand_code: replacement,
          changed_by: changedBy.trim(),
          reason,
          notes: notes.trim() || null,
          removed_condition: condition,
          leakage: condition === "Leakage" || condition === "Leakage + Vibration",
          vibration: condition === "Vibration" || condition === "Leakage + Vibration",
        }),
      });
      setMessage(`${selectedPosition.currentStand} changed to ${replacement}. Removed stand moved to Pending.`);
      setReplacement("");
      setChangedBy("");
      setReason("");
      setNotes("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stand change failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Change Stand" />
      <main className="p-4 md:p-6 flex-1">
        <div className="max-w-4xl bg-industrial-card border border-industrial-border rounded-xl p-5 md:p-6">
          <div className="mb-5">
            <h2 className="text-xl font-bold text-white">Record a Stand Change</h2>
            <p className="text-sm text-slate-400 mt-1">Choose where the stand is changing, who changed it and why.</p>
          </div>

          {error && <div className="mb-4 p-4 rounded-lg border border-red-800 bg-red-950/40 text-red-300">{error}</div>}
          {message && <div className="mb-4 p-4 rounded-lg border border-green-800 bg-green-950/40 text-green-300">{message}</div>}

          {loading ? <div className="text-slate-400">Loading stand data...</div> : (
            <form onSubmit={submitChange} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-300 mb-2">Line and position</label>
                <select value={positionId} onChange={(e) => setPositionId(e.target.value)} className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-white">
                  {positions.map((p) => <option key={p.id} value={p.id}>{p.lineName} - Position {p.positionNumber} - {p.currentStand}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-300 mb-2">Replacement stand</label>
                <select value={replacement} onChange={(e) => setReplacement(e.target.value)} required className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-white">
                  <option value="">Select Ready stand</option>
                  {readyStands.map((s) => <option key={s.id} value={s.code}>{s.code}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-300 mb-2">Changed by</label>
                <input value={changedBy} onChange={(e) => setChangedBy(e.target.value)} required placeholder="Operator / technician name" className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-white" />
              </div>

              <div>
                <label className="block text-sm text-slate-300 mb-2">Reason</label>
                <select value={reason} onChange={(e) => setReason(e.target.value)} required className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-white">
                  <option value="">Select reason</option>
                  <option>Roll wear / size deviation</option>
                  <option>Bearing issue</option>
                  <option>Leakage</option>
                  <option>Vibration</option>
                  <option>Scheduled rotation</option>
                  <option>Breakdown</option>
                  <option>Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-300 mb-2">Removed stand condition</label>
                <select value={condition} onChange={(e) => setCondition(e.target.value)} className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-white">
                  <option>Normal</option><option>Leakage</option><option>Vibration</option><option>Leakage + Vibration</option><option>Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-300 mb-2">Remarks</label>
                <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional observation" className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-white" />
              </div>

              <div className="md:col-span-2 flex items-center justify-between gap-3 flex-wrap pt-2">
                <div className="text-sm text-slate-400">Removed stand will automatically go to Pending.</div>
                <button disabled={submitting} type="submit" className="px-6 py-3 rounded-lg bg-industrial-accent text-white font-semibold disabled:opacity-50">{submitting ? "Saving..." : "Save Stand Change"}</button>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
