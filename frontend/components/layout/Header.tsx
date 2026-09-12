"use client";

import Image from "next/image";

export default function Header({ title }: { title: string }) {
  return (
    <header className="hidden md:flex h-14 items-center justify-between gap-4 border-b border-[#26354a] bg-[#0d1422]/95 px-5">
      <div className="min-w-0">
        <div className="text-[11px] font-medium text-slate-400">Finishing Mill</div>
        <h1 className="text-base font-semibold text-white truncate">{title}</h1>
      </div>
      <div className="flex h-9 items-center gap-2 rounded-lg border border-slate-700/60 bg-white px-2.5 shadow-sm">
        <Image src="/vaaman.webp" alt="Vaaman Engineers" width={104} height={28} className="h-6 w-auto object-contain" priority />
        <span className="h-5 w-px bg-slate-300" />
        <Image src="/vedanta.webp" alt="Vedanta" width={112} height={28} className="h-6 w-auto object-contain" priority />
      </div>
    </header>
  );
}
