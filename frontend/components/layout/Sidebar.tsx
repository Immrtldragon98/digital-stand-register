"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Wrench, ShieldAlert, FileText, Layers, Settings, Database, Factory, Package } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Stand Area", href: "/stand-area", icon: Factory },
    { name: "Operations", href: "/operations", icon: Wrench },
    { name: "Entry Guides", href: "/entry-guides", icon: Layers },
    { name: "Transactions", href: "/transactions", icon: Database },
    { name: "Inventory", href: "/inventory", icon: Package },
    { name: "Activity Logs", href: "/activity", icon: ShieldAlert },
    { name: "Reports", href: "/reports", icon: FileText },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-industrial-card border-r border-industrial-border min-h-screen p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-2 mb-8">
          <span className="w-3.5 h-3.5 bg-industrial-accent rounded-full"></span>
          <span className="font-bold text-white tracking-wider text-sm">DSR PLATFORM</span>
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition duration-150 ${
                  isActive
                    ? "bg-industrial-dark text-industrial-accent border border-industrial-border"
                    : "text-slate-400 hover:text-white hover:bg-industrial-dark/50"
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
        DSR Plant Core v2.4
      </div>
    </aside>
  );
}