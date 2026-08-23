"use client";

import { Bell, Search } from "lucide-react";

export default function Header({ title }: { title: string }) {
  return (
    <header className="bg-industrial-card border-b border-industrial-border px-6 py-4 flex items-center justify-between">
      <h1 className="text-xl font-bold text-white tracking-wide">{title}</h1>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search assets..."
            className="pl-9 pr-4 py-1.5 bg-industrial-dark border border-industrial-border rounded-lg text-sm text-slate-200 focus:outline-none focus:border-industrial-accent"
          />
        </div>
        <button className="p-2 bg-industrial-dark border border-industrial-border rounded-lg text-slate-400 hover:text-white transition">
          <Bell className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}