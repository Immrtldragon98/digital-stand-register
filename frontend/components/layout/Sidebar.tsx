"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Wrench, FileText, Factory, Package, History } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const menuItems = [
    { name: "Home", href: "/dashboard", icon: Home },
    { name: "Stand Area", href: "/stand-area", icon: Factory },
    { name: "Stand Change", href: "/operations", icon: Wrench },
    { name: "Materials", href: "/inventory", icon: Package },
    { name: "History", href: "/activity", icon: History },
    { name: "Reports", href: "/reports", icon: FileText },
  ];

  return (
    <aside className="w-64 bg-industrial-card border-r border-industrial-border min-h-screen p-5 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-2 mb-7">
          <span className="w-3 h-3 bg-blue-500 rounded-sm"></span>
          <span className="font-bold text-white tracking-wide text-sm">Digital Stand Register</span>
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}
                className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium ${isActive ? "bg-blue-600 text-white" : "text-slate-300 hover:text-white hover:bg-slate-800/70"}`}>
                <Icon className="w-4 h-4" />{item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="pt-4 border-t border-industrial-border text-xs text-slate-500 text-center">© 2026 Digital Stand Register</div>
    </aside>
  );
}
