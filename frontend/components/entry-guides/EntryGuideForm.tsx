"use client";

import { useState } from "react";

export default function EntryGuideForm({ onSubmit }: { onSubmit: (data: any) => void }) {
  const [guideNumber, setGuideNumber] = useState("");
  const [targetLocation, setTargetLocation] = useState("");
  const [assetId, setAssetId] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ guide_number: guideNumber, target_location: targetLocation, asset_id: assetId });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl mb-6 flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-white">Create New Entry Guide</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Guide Number</label>
          <input
            type="text"
            value={guideNumber}
            onChange={(e) => setGuideNumber(e.target.value)}
            required
            className="w-full px-4 py-2 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
            placeholder="e.g. EG-2026-001"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Target Location</label>
          <input
            type="text"
            value={targetLocation}
            onChange={(e) => setTargetLocation(e.target.value)}
            required
            className="w-full px-4 py-2 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
            placeholder="e.g. Bay 3 Sector A"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Asset ID</label>
          <input
            type="text"
            value={assetId}
            onChange={(e) => setAssetId(e.target.value)}
            required
            className="w-full px-4 py-2 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
            placeholder="Asset UUID"
          />
        </div>
      </div>
      <button
        type="submit"
        className="self-end py-2 px-6 bg-industrial-accent hover:bg-blue-600 text-white font-medium rounded-lg transition duration-200 shadow-md"
      >
        Submit Guide
      </button>
    </form>
  );
}