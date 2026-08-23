"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Wrench, FileText, Layers, Factory, Package, History } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { name: "Home", href: "/dashboard", icon: LayoutDashboard },
    { name: "Stand Status", href: "/stand-area", icon: Factory },
    { name: "Change Stand", href: "/operations", icon: Wrench },
    { name: "Entry Guides", href: "/entry-guides", icon: Layers },
    { name: "Materials", href: "/inventory", icon: Package },
    { name: "History", href: "/activity", icon: History },
    { name: "Reports", href: "/reports", icon: FileText },
  ];

  return (
    <aside className="w-64 bg-industrial-card border-r border-industrial-border min-h-screen p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-2 mb-8">
          <span className="w-3.5 h-3.5 bg-industrial-accent rounded-full"></span>
          <span className="font-bold text-white tracking-wide text-sm">STAND AREA</span>
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition duration-150 ${
                  isActive
                    ? "bg-industrial-dark text-industrial-accent border border-industrial-border"
                    : "text-slate-300 hover:text-white hover:bg-industrial-dark/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="pt-4 border-t border-industrial-border text-xs text-slate-500 text-center">
        Digital Stand Register
      </div>
    </aside>
  );
}
