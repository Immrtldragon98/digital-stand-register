"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";

type Stand = {
  id: number;
  code: string;
  current_location: string;
  current_status: string;
  current_position_id: number | null;
};

export default function OperationsPage() {
  const [stands, setStands] = useState<Stand[]>([]);
  const [standCode, setStandCode] = useState("");
  const [positionId, setPositionId] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadStands = async () => {
    try {
      const data = await fetchApi("/stands/");
      setStands(data);
    } catch (err) {
      console.error("Failed to load stands:", err);
      setError(
        err instanceof Error ? err.message : "Failed to load stands"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStands();
  }, []);

  const executeOperation = async (
    operation: "install" | "remove" | "ready"
  ) => {
    if (!standCode.trim()) {
      setError("Please enter a stand code.");
      return;
    }

    setSubmitting(true);
    setMessage("");
    setError("");

    try {
      if (operation === "install") {
        if (!positionId.trim()) {
          setError("Position ID is required for installation.");
          return;
        }

        await fetchApi("/operations/stands/install", {
          method: "POST",
          body: JSON.stringify({
            stand_code: standCode.trim(),
            position_id: Number(positionId),
          }),
        });

        setMessage(`Stand ${standCode} successfully installed.`);
      }

      if (operation === "remove") {
        await fetchApi("/operations/stands/remove", {
          method: "POST",
          body: JSON.stringify({
            stand_code: standCode.trim(),
          }),
        });

        setMessage(`Stand ${standCode} removed and sent to WIP.`);
      }

      if (operation === "ready") {
        await fetchApi("/operations/stands/mark-ready", {
          method: "POST",
          body: JSON.stringify({
            stand_code: standCode.trim(),
          }),
        });

        setMessage(`Stand ${standCode} marked ready.`);
      }

      await loadStands();
    } catch (err) {
      console.error("Operation failed:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Operation failed."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Plant Operations" />

      <main className="p-6 flex-1 space-y-6">

        <section className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold text-white mb-6">
            Stand Lifecycle Operations
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Stand Code
              </label>

              <input
                type="text"
                value={standCode}
                onChange={(e) => setStandCode(e.target.value)}
                placeholder="e.g. 5A"
                className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Position ID
              </label>

              <input
                type="number"
                value={positionId}
                onChange={(e) => setPositionId(e.target.value)}
                placeholder="Required for installation"
                className="w-full px-4 py-3 bg-industrial-dark border border-industrial-border rounded-lg text-slate-100 focus:outline-none focus:border-industrial-accent"
              />
            </div>

          </div>

          <div className="flex flex-wrap gap-3 mt-6">

            <button
              disabled={submitting}
              onClick={() => executeOperation("install")}
              className="px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              Install Stand
            </button>

            <button
              disabled={submitting}
              onClick={() => executeOperation("remove")}
              className="px-5 py-3 rounded-lg bg-orange-600 hover:bg-orange-700 disabled:opacity-50 font-medium"
            >
              Remove Stand
            </button>

            <button
              disabled={submitting}
              onClick={() => executeOperation("ready")}
              className="px-5 py-3 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 font-medium"
            >
              Mark Ready
            </button>

          </div>

          {message && (
            <div className="mt-5 p-4 rounded-lg border border-green-800 bg-green-950/40 text-green-400">
              {message}
            </div>
          )}

          {error && (
            <div className="mt-5 p-4 rounded-lg border border-red-800 bg-red-950/40 text-red-400">
              {error}
            </div>
          )}
        </section>

        <section className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">

          <h2 className="text-lg font-semibold text-white mb-4">
            Current Stand Status
          </h2>

          {loading ? (
            <div className="py-10 text-center text-slate-400">
              Loading stand registry...
            </div>
          ) : stands.length === 0 ? (
            <div className="py-10 text-center text-slate-500">
              No stands found.
            </div>
          ) : (
            <div className="overflow-x-auto">

              <table className="w-full text-left text-sm">

                <thead className="bg-industrial-dark text-xs uppercase text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Stand</th>
                    <th className="px-4 py-3">Location</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Position</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-industrial-border">

                  {stands.map((stand) => (
                    <tr
                      key={stand.id}
                      className="hover:bg-industrial-dark/50"
                    >
                      <td className="px-4 py-3 font-semibold text-white">
                        {stand.code}
                      </td>

                      <td className="px-4 py-3 text-slate-300">
                        {stand.current_location}
                      </td>

                      <td className="px-4 py-3">
                        <span className="px-2.5 py-1 rounded-full text-xs border">
                          {stand.current_status}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-slate-400">
                        {stand.current_position_id ?? "—"}
                      </td>
                    </tr>
                  ))}

                </tbody>

              </table>

            </div>
          )}

        </section>

      </main>
    </div>
  );
}