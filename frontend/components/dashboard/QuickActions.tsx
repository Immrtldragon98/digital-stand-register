"use client";

import Link from "next/link";
import { PlusCircle, Layers, Wrench, Compass } from "lucide-react";

export default function QuickActions() {
  const actions = [
    { name: "New Entry Guide", href: "/entry-guides", icon: PlusCircle, color: "text-industrial-accent" },
    { name: "Record Operation", href: "/operations", icon: Wrench, color: "text-blue-400" },
    { name: "Configure Stand", href: "/stands", icon: Layers, color: "text-green-400" },
    { name: "Position Map", href: "/positions", icon: Compass, color: "text-amber-400" },
  ];

  return (
    <div className="bg-industrial-card border border-industrial-border rounded-xl p-6 shadow-xl">
      <h2 className="text-lg font-semibold text-white mb-4">Quick Operational Actions</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {actions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <Link
              key={idx}
              href={action.href}
              className="flex items-center gap-3 p-4 bg-industrial-dark border border-industrial-border rounded-lg hover:border-industrial-accent transition duration-150 group"
            >
              <Icon className={`w-5 h-5 ${action.color}`} />
              <span className="text-sm font-medium text-slate-200 group-hover:text-white">{action.name}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}