"use client";

import Image from "next/image";
import { Bell, Search } from "lucide-react";

export default function Header({ title }: { title: string }) {
  return (
    <header className="bg-industrial-card border-b border-industrial-border px-4 md:px-6 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4 min-w-0">
        <div className="hidden sm:flex items-center rounded-md bg-white px-2 py-1 h-10 shrink-0">
          <Image src="/vaaman.webp" alt="Vaaman Engineers" width={126} height={38} className="h-8 w-auto object-contain" priority />
        </div>
        <div className="min-w-0">
          <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Finishing Mill</div>
          <h1 className="text-lg md:text-xl font-bold text-white tracking-wide truncate">{title}</h1>
        </div>
      </div>
      <div className="flex items-center gap-3 md:gap-4 shrink-0">
        <div className="relative hidden lg:block">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search assets..."
            className="pl-9 pr-4 py-1.5 bg-industrial-dark border border-industrial-border rounded-lg text-sm text-slate-200 focus:outline-none focus:border-industrial-accent"
          />
        </div>
        <button className="hidden md:block p-2 bg-industrial-dark border border-industrial-border rounded-lg text-slate-400 hover:text-white transition">
          <Bell className="w-4 h-4" />
        </button>
        <div className="flex items-center rounded-md bg-white px-2 py-1 h-10 shrink-0">
          <Image src="/vedanta.webp" alt="Vedanta" width={150} height={34} className="h-8 w-auto object-contain" priority />
        </div>
      </div>
    </header>
  );
}