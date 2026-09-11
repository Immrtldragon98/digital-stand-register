"use client";

import Image from "next/image";

export default function Header({ title }: { title: string }) {
  return (
    <header className="hidden md:flex items-center justify-between gap-4 border-b border-slate-800 bg-[#0e1115] px-5 py-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex items-center rounded-md bg-white px-2 py-1 h-9 shrink-0">
          <Image src="/vaaman.webp" alt="Vaaman Engineers" width={120} height={34} className="h-7 w-auto object-contain" priority />
        </div>
        <div className="min-w-0">
          <div className="text-xs font-medium text-slate-400">Finishing Mill</div>
          <h1 className="text-lg font-semibold text-white truncate">{title}</h1>
        </div>
      </div>
      <div className="flex items-center rounded-md bg-white px-2 py-1 h-9 shrink-0">
        <Image src="/vedanta.webp" alt="Vedanta" width={142} height={32} className="h-7 w-auto object-contain" priority />
      </div>
    </header>
  );
}
