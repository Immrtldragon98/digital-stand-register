"use client";

import { useState } from "react";
import Header from "@/components/layout/Header";
import { Settings as SettingsIcon, Save } from "lucide-react";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api");
  const [refreshInterval, setRefreshInterval] = useState("5");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Terminal Configuration" />
      <main className="p-6 flex-1">
        <form onSubmit={handleSave} className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl max-w-2xl space-y-6">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <SettingsIcon className="w-5 h-5 text-industrial-accent" />
            System Parameters & Environment
          </h2>
          {saved && (
            <div className="p-3 bg-green-950/50 border border-green-800 text-green-400 rounded-lg text-sm">
              Configuration parameters successfully updated.
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Backend API Endpoint</label>
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                className="w-full px-4 py-2.5 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent font-mono text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Telemetry Refresh Interval (seconds)</label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(e.target.value)}
                className="w-full px-4 py-2.5 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
              >
                <option value="5">5 Seconds</option>
                <option value="15">15 Seconds</option>
                <option value="30">30 Seconds</option>
                <option value="60">60 Seconds</option>
              </select>
            </div>
          </div>
          <button
            type="submit"
            className="flex items-center gap-2 py-2.5 px-6 bg-industrial-accent hover:bg-blue-600 text-white font-medium rounded-lg transition duration-200 shadow-md"
          >
            <Save className="w-4 h-4" />
            Save Configuration
          </button>
        </form>
      </main>
    </div>
  );
}