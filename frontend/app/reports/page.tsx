"use client";

import { useMemo, useState } from "react";
import Header from "@/components/layout/Header";
import { API_BASE_URL } from "@/lib/api";
import { Download, ShieldCheck } from "lucide-react";

export default function ReportsPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const downloadUrl = useMemo(
    () => `${API_BASE_URL}/reports/running-status.xlsx?year=${year}&month=${month}`,
    [year, month]
  );

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Reports" />
      <main className="p-6 flex-1 space-y-6">
        <section className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
            <div>
              <h2 className="text-lg font-semibold text-white">Monthly Running Stand Status</h2>
              <p className="text-xs text-slate-400 mt-1">
                Generates W1/W2/W3 running status directly from stand installation history.
              </p>
            </div>
            <div className="flex flex-wrap gap-3 items-end">
              <label className="text-xs text-slate-400">
                Year
                <input
                  className="mt-1 block w-28 bg-industrial-dark border border-industrial-border rounded-lg px-3 py-2 text-slate-100"
                  type="number"
                  min={2026}
                  max={2100}
                  value={year}
                  onChange={(e) => setYear(Number(e.target.value))}
                />
              </label>
              <label className="text-xs text-slate-400">
                Month
                <select
                  className="mt-1 block bg-industrial-dark border border-industrial-border rounded-lg px-3 py-2 text-slate-100"
                  value={month}
                  onChange={(e) => setMonth(Number(e.target.value))}
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>{String(m).padStart(2, "0")}</option>
                  ))}
                </select>
              </label>
              <a
                href={downloadUrl}
                className="flex items-center gap-2 px-4 py-2 bg-industrial-accent text-slate-950 font-semibold rounded-lg"
              >
                <Download className="w-4 h-4" />
                Download Excel
              </a>
            </div>
          </div>
        </section>

        <section className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
          <div className="flex gap-3 items-start">
            <ShieldCheck className="w-5 h-5 text-green-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-white">Data retention is manual and safe</h3>
              <p className="text-sm text-slate-400 mt-1 leading-6">
                There is no automatic deletion. Running stands and their active installations are never removed by report cleanup.
                Excel reports are generated on demand and are not stored on the server, so downloading a report does not grow database storage.
                Stand lifetime hours, stand-change history, preparation history and entry-guide history remain available for traceability.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
