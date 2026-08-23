"use client";

import { useState } from "react";

export default function EntryGuideForm({ onSubmit }: { onSubmit: (data: any) => void }) {
  const [code, setCode] = useState("");
  const [condition, setCondition] = useState("OLD");
  const [notes, setNotes] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ code: code.trim(), condition, notes: notes.trim() || null });
    setCode("");
    setNotes("");
  };

  return (
    <form onSubmit={handleSubmit} className="bg-industrial-card border border-industrial-border rounded-xl p-5 mb-6 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-white">Add Entry Guide</h2>
        <p className="text-sm text-slate-400 mt-1">Entry guides are used only at positions 2, 4, 6, 8 and 10.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-slate-300 mb-2">Guide ID</label>
          <input value={code} onChange={(e) => setCode(e.target.value)} required className="w-full px-4 py-2 bg-industrial-dark border border-industrial-border rounded-lg text-white" placeholder="e.g. EG-4-03" />
        </div>
        <div>
          <label className="block text-sm text-slate-300 mb-2">Condition</label>
          <select value={condition} onChange={(e) => setCondition(e.target.value)} className="w-full px-4 py-2 bg-industrial-dark border border-industrial-border rounded-lg text-white">
            <option value="NEW">New</option>
            <option value="OLD">Old</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-slate-300 mb-2">Remarks</label>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} className="w-full px-4 py-2 bg-industrial-dark border border-industrial-border rounded-lg text-white" placeholder="Optional" />
        </div>
      </div>
      <button type="submit" className="px-5 py-2 bg-industrial-accent text-white rounded-lg font-medium">Add Guide</button>
    </form>
  );
}
