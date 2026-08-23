"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type Item = {
  id: number;
  name: string;
  quantity: number;
  minimum_quantity: number;
  location: string;
  remarks?: string | null;
  is_active: boolean;
};

type Tx = {
  id: number;
  item_id: number;
  item_name: string;
  quantity_before: number;
  quantity_change: number;
  quantity_after: number;
  operator: string;
  reason: string;
  transaction_type: string;
  created_at: string;
};

const blank = { name: "", quantity: 0, minimum_quantity: 0, location: "", remarks: "" };

export default function InventoryPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [history, setHistory] = useState<Tx[]>([]);
  const [form, setForm] = useState(blank);
  const [edit, setEdit] = useState<number | null>(null);
  const [adjust, setAdjust] = useState<{ item: Item; mode: "delta" | "set"; value: number } | null>(null);
  const [operator, setOperator] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [inventory, transactions] = await Promise.all([
        fetchApi("/inventory/"),
        fetchApi("/inventory/transactions?limit=200"),
      ]);
      setItems(inventory);
      setHistory(transactions);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => { load(); }, []);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (edit) {
        const { quantity: _quantity, ...details } = form;
        await fetchApi(`/inventory/${edit}`, { method: "PATCH", body: JSON.stringify(details) });
      } else {
        await fetchApi("/inventory/", { method: "POST", body: JSON.stringify(form) });
      }
      setForm(blank);
      setEdit(null);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const openAdjustment = (item: Item, mode: "delta" | "set", value: number) => {
    setAdjust({ item, mode, value });
    setOperator("");
    setReason("");
    setError("");
  };

  const submitAdjustment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjust) return;
    if (!operator.trim() || !reason.trim()) {
      setError("Operator and reason are required for every quantity change.");
      return;
    }
    try {
      const path = adjust.mode === "set"
        ? `/inventory/${adjust.item.id}/set-quantity`
        : `/inventory/${adjust.item.id}/quantity`;
      const body = adjust.mode === "set"
        ? { quantity: Math.max(0, Math.floor(adjust.value)), operator: operator.trim(), reason: reason.trim() }
        : { delta: Math.trunc(adjust.value), operator: operator.trim(), reason: reason.trim() };
      await fetchApi(path, { method: "POST", body: JSON.stringify(body) });
      setAdjust(null);
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const archive = async (item: Item) => {
    if (!confirm(`Archive ${item.name}? Its transaction history will be retained.`)) return;
    try {
      await fetchApi(`/inventory/${item.id}`, { method: "DELETE" });
      await load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Inventory</h1>
        <p className="text-slate-400 text-sm">Editable stand-area stock with operator-wise transaction history.</p>
      </div>

      <form onSubmit={save} className="bg-industrial-card border border-industrial-border rounded-xl p-5 grid md:grid-cols-5 gap-3">
        <input className="bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" placeholder="Material" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
        {!edit ? (
          <input className="bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" type="number" min="0" placeholder="Opening quantity" value={form.quantity} onChange={e => setForm({ ...form, quantity: +e.target.value })} />
        ) : (
          <div className="bg-industrial-dark border border-industrial-border rounded-lg p-2 text-slate-400">Quantity via stock adjustment</div>
        )}
        <input className="bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" type="number" min="0" placeholder="Minimum" value={form.minimum_quantity} onChange={e => setForm({ ...form, minimum_quantity: +e.target.value })} />
        <input className="bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" placeholder="Location" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} required />
        <button className="bg-industrial-accent text-black font-semibold rounded-lg px-4">{edit ? "Update Details" : "Add Inventory"}</button>
        <input className="md:col-span-4 bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" placeholder="Remarks / specification" value={form.remarks} onChange={e => setForm({ ...form, remarks: e.target.value })} />
        {edit && <button type="button" onClick={() => { setEdit(null); setForm(blank); }} className="border border-industrial-border rounded-lg px-4 text-slate-300">Cancel Edit</button>}
      </form>

      {error && <p className="text-red-400">{error}</p>}

      {adjust && (
        <form onSubmit={submitAdjustment} className="bg-industrial-card border border-industrial-accent rounded-xl p-5 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Adjust {adjust.item.name}</h2>
            <p className="text-sm text-slate-400">Current stock: {adjust.item.quantity}</p>
          </div>
          <div className="grid md:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-400">{adjust.mode === "set" ? "New quantity" : "Quantity change"}</label>
              <input className="w-full bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" type="number" min={adjust.mode === "set" ? 0 : undefined} value={adjust.value} onChange={e => setAdjust({ ...adjust, value: Number(e.target.value) })} required />
            </div>
            <div>
              <label className="text-xs text-slate-400">Operator</label>
              <input className="w-full bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" value={operator} onChange={e => setOperator(e.target.value)} placeholder="Name / employee" required />
            </div>
            <div>
              <label className="text-xs text-slate-400">Reason</label>
              <input className="w-full bg-industrial-dark border border-industrial-border rounded-lg p-2 text-white" value={reason} onChange={e => setReason(e.target.value)} placeholder="Issued / received / correction" required />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="bg-industrial-accent text-black font-semibold rounded-lg px-4 py-2">Save Stock Transaction</button>
            <button type="button" onClick={() => setAdjust(null)} className="border border-industrial-border rounded-lg px-4 py-2 text-slate-300">Cancel</button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto bg-industrial-card border border-industrial-border rounded-xl">
        <table className="w-full text-sm">
          <thead><tr className="text-slate-400 border-b border-industrial-border"><th className="p-3 text-left">Material</th><th>Quantity</th><th>Minimum</th><th>Location</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>{items.map(i => (
            <tr key={i.id} className="border-b border-industrial-border text-slate-200">
              <td className="p-3 font-medium">{i.name}{i.remarks && <div className="text-xs text-slate-500 font-normal">{i.remarks}</div>}</td>
              <td className="text-center font-semibold">{i.quantity}</td>
              <td className="text-center">{i.minimum_quantity}</td>
              <td className="text-center">{i.location}</td>
              <td className="text-center">{i.quantity === 0 ? "OUT" : i.quantity <= i.minimum_quantity ? "LOW" : "OK"}</td>
              <td className="p-2"><div className="flex gap-2 justify-center flex-wrap">
                <button onClick={() => openAdjustment(i, "delta", -1)} className="px-2 py-1 border border-industrial-border rounded">−</button>
                <button onClick={() => openAdjustment(i, "delta", 1)} className="px-2 py-1 border border-industrial-border rounded">+</button>
                <button onClick={() => openAdjustment(i, "set", i.quantity)} className="px-2 py-1 border border-industrial-border rounded">Set Qty</button>
                <button onClick={() => { setEdit(i.id); setForm({ name: i.name, quantity: i.quantity, minimum_quantity: i.minimum_quantity, location: i.location, remarks: i.remarks || "" }); }} className="px-2 py-1 border border-industrial-border rounded">Edit</button>
                <button onClick={() => archive(i)} className="px-2 py-1 border border-red-800 text-red-400 rounded">Archive</button>
              </div></td>
            </tr>
          ))}</tbody>
        </table>
      </div>

      <div className="bg-industrial-card border border-industrial-border rounded-xl overflow-hidden">
        <div className="p-4 border-b border-industrial-border">
          <h2 className="text-lg font-semibold text-white">Inventory Transaction History</h2>
          <p className="text-sm text-slate-400">Every stock movement keeps its operator, reason and before/after balance.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 border-b border-industrial-border"><th className="p-3 text-left">Date</th><th>Material</th><th>Before</th><th>Change</th><th>After</th><th>Type</th><th>Operator</th><th className="text-left">Reason</th></tr></thead>
            <tbody>
              {history.map(tx => <tr key={tx.id} className="border-b border-industrial-border text-slate-200">
                <td className="p-3 whitespace-nowrap">{new Date(tx.created_at).toLocaleString()}</td>
                <td className="text-center">{tx.item_name}</td>
                <td className="text-center">{tx.quantity_before}</td>
                <td className={`text-center font-semibold ${tx.quantity_change > 0 ? "text-green-400" : "text-red-400"}`}>{tx.quantity_change > 0 ? "+" : ""}{tx.quantity_change}</td>
                <td className="text-center">{tx.quantity_after}</td>
                <td className="text-center">{tx.transaction_type}</td>
                <td className="text-center">{tx.operator}</td>
                <td className="p-3">{tx.reason}</td>
              </tr>)}
              {!history.length && <tr><td colSpan={8} className="p-5 text-center text-slate-500">No inventory transactions yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
