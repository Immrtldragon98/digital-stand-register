"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Stand = { id: number; code: string; current_status: string };
type PositionRow = { id: number; lineName: string; positionNumber: number; currentStand: string };

export default function OperationsPage() {
  const [stands, setStands] = useState<Stand[]>([]);
  const [positions, setPositions] = useState<PositionRow[]>([]);
  const [positionId, setPositionId] = useState("");
  const [replacement, setReplacement] = useState("");
  const [changedBy, setChangedBy] = useState("");
  const [reason, setReason] = useState("");
  const [condition, setCondition] = useState("Normal");
  const [notes, setNotes] = useState("");
  const [timeMode, setTimeMode] = useState<"now" | "custom">("now");
  const [customTime, setCustomTime] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setError("");
      const [lineData, standData] = await Promise.all([fetchApi("/dashboard/"), fetchApi("/stands/")]);
      const mapped: PositionRow[] = [];
      lineData.forEach((line: any) => line.positions?.forEach((pos: any) => {
        if (pos.current_stand) mapped.push({ id: pos.id, lineName: line.name, positionNumber: pos.position_number, currentStand: pos.current_stand.code });
      }));
      setPositions(mapped);
      setStands(standData);
      if (!positionId && mapped.length) setPositionId(String(mapped[0].id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load stand data");
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  const selectedPosition = useMemo(() => positions.find((p) => p.id === Number(positionId)), [positions, positionId]);
  const readyStands = stands.filter((s) => s.current_status === "READY");

  const submitChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPosition || !replacement || !changedBy.trim() || !reason) {
      setError("Select position, replacement stand, name and reason.");
      return;
    }
    if (timeMode === "custom" && !customTime) {
      setError("Select the stand change date and time.");
      return;
    }
    setSubmitting(true); setError(""); setMessage("");
    try {
      const changedAt = timeMode === "custom" ? new Date(customTime).toISOString() : null;
      await fetchApi("/operations/stands/change", {
        method: "POST",
        body: JSON.stringify({
          position_id: selectedPosition.id,
          removed_stand_code: selectedPosition.currentStand,
          installed_stand_code: replacement,
          changed_by: changedBy.trim(), reason, changed_at: changedAt,
          notes: notes.trim() || null, removed_condition: condition,
          leakage: condition === "Leakage" || condition === "Leakage + Vibration",
          vibration: condition === "Vibration" || condition === "Leakage + Vibration",
        }),
      });
      setMessage(`${selectedPosition.currentStand} changed to ${replacement}. Removed stand moved to Pending.`);
      setReplacement(""); setChangedBy(""); setReason(""); setNotes(""); setTimeMode("now"); setCustomTime("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Stand change failed");
    } finally { setSubmitting(false); }
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Change Stand" />
      <main className="p-4 md:p-6 flex-1">
        <div className="max-w-4xl bg-industrial-card border border-industrial-border rounded-xl p-5 md:p-6">
          <h2 className="text-xl font-bold text-white">Record Stand Change</h2>
          <p className="text-sm text-slate-400 mt-1 mb-5">Choose position, replacement, person, reason and time.</p>
          {error && <div className="mb-4 p-3 rounded-lg border border-red-800 bg-red-950/40 text-red-300">{error}</div>}
          {message && <div className="mb-4 p-3 rounded-lg border border-green-800 bg-green-950/40 text-green-300">{message}</div>}
          {loading ? <div className="text-slate-400">Loading...</div> : (
            <form onSubmit={submitChange} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Line and position"><select value={positionId} onChange={(e) => setPositionId(e.target.value)} className="input-class">{positions.map((p) => <option key={p.id} value={p.id}>{p.lineName} - Pos {p.positionNumber} - {p.currentStand}</option>)}</select></Field>
              <Field label="Replacement stand"><select value={replacement} onChange={(e) => setReplacement(e.target.value)} required className="input-class"><option value="">Select Ready stand</option>{readyStands.map((s) => <option key={s.id} value={s.code}>{s.code}</option>)}</select></Field>
              <Field label="Changed by"><input value={changedBy} onChange={(e) => setChangedBy(e.target.value)} required placeholder="Operator / technician name" className="input-class" /></Field>
              <Field label="Reason"><select value={reason} onChange={(e) => setReason(e.target.value)} required className="input-class"><option value="">Select reason</option><option>Roll wear / size deviation</option><option>Bearing issue</option><option>Leakage</option><option>Vibration</option><option>Scheduled rotation</option><option>Breakdown</option><option>Other</option></select></Field>
              <Field label="Change time"><div className="flex gap-2"><button type="button" onClick={() => setTimeMode("now")} className={`px-3 py-2 rounded border ${timeMode === "now" ? "border-blue-500 bg-blue-950/40" : "border-slate-700"}`}>Now</button><button type="button" onClick={() => setTimeMode("custom")} className={`px-3 py-2 rounded border ${timeMode === "custom" ? "border-blue-500 bg-blue-950/40" : "border-slate-700"}`}>Custom date</button></div>{timeMode === "custom" && <input type="datetime-local" value={customTime} onChange={(e) => setCustomTime(e.target.value)} className="input-class mt-2" required />}</Field>
              <Field label="Removed stand condition"><select value={condition} onChange={(e) => setCondition(e.target.value)} className="input-class"><option>Normal</option><option>Leakage</option><option>Vibration</option><option>Leakage + Vibration</option><option>Other</option></select></Field>
              <div className="md:col-span-2"><Field label="Remarks"><input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional observation" className="input-class" /></Field></div>
              <div className="md:col-span-2 flex items-center justify-between gap-3 flex-wrap pt-2"><div className="text-sm text-slate-400">Removed stand automatically goes to Pending.</div><button disabled={submitting} type="submit" className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold disabled:opacity-50">{submitting ? "Saving..." : "Save Stand Change"}</button></div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label className="block text-sm text-slate-300 mb-2">{label}</label>{children}</div>;
}
