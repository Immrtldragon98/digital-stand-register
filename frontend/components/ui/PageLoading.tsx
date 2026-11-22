"use client";

import { useEffect, useState } from "react";

export default function PageLoading({ label }: { label: string }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = window.setTimeout(() => setSlow(true), 8000);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div role="status" aria-live="polite" aria-busy="true" className="space-y-3 p-4">
      <p className="text-sm text-slate-300">{label}</p>
      {slow && <p className="text-xs text-slate-400">The connection is taking longer than usual. Please wait; a retry option will appear if it fails.</p>}
      <div aria-hidden="true" className="grid grid-cols-1 gap-4 motion-safe:animate-pulse sm:grid-cols-2">
        {[0, 1, 2, 3].map(i => <div key={i} className="space-y-2"><div className="h-3 w-24 rounded bg-slate-700/60"/><div className="h-11 rounded-lg bg-slate-800"/></div>)}
      </div>
    </div>
  );
}
