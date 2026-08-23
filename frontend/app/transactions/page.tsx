"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { fetchApi } from "@/lib/api";
import { ArrowLeftRight, CheckCircle2 } from "lucide-react";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTransactions() {
      try {
        const data = await fetchApi("/transactions");
        setTransactions(data);
      } catch (err) {
        console.error("Failed to load transactions:", err);
      } finally {
        setLoading(false);
      }
    }
    loadTransactions();
  }, []);

  return (
    <div className="flex-1 bg-industrial-dark min-h-screen text-slate-100 flex flex-col">
      <Header title="Plant Transactions Ledger" />
      <main className="p-6 flex-1">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
            Loading transaction history...
          </div>
        ) : (
          <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <ArrowLeftRight className="w-5 h-5 text-industrial-accent" />
              Active Transaction Logs
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-industrial-dark text-xs uppercase text-slate-400 border-b border-industrial-border">
                  <tr>
                    <th className="px-4 py-3">Transaction ID</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Asset / Unit</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-industrial-border">
                  {transactions && transactions.length > 0 ? (
                    transactions.map((tx, idx) => (
                      <tr key={idx} className="hover:bg-industrial-dark/50">
                        <td className="px-4 py-3 font-mono text-xs text-white">{tx.id || `TX-${idx + 100}`}</td>
                        <td className="px-4 py-3 font-medium text-slate-200">{tx.type || "Transfer"}</td>
                        <td className="px-4 py-3 text-slate-400">{tx.asset_id || "Stand Unit A"}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-950/50 text-green-400 border border-green-800 rounded-full text-xs">
                            <CheckCircle2 className="w-3 h-3" />
                            {tx.status || "Completed"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-400">
                          {new Date(tx.timestamp || Date.now()).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                        No transactions registered in the ledger.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}