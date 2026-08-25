"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Home, Wrench, FileText, Factory, Package, History, Layers, Users, LogIn, LogOut } from "lucide-react";
import { AuthUser, clearSession, getUser, isAdmin } from "@/lib/auth";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const sync = () => setUser(getUser());
    sync();
    window.addEventListener("dsr-auth-change", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("dsr-auth-change", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const menuItems = [
    { name: "Home", href: "/dashboard", icon: Home },
    { name: "Stand Area", href: "/stand-area", icon: Factory },
    { name: "Stand Change", href: "/operations", icon: Wrench },
    { name: "Entry Guides", href: "/entry-guides", icon: Layers },
    { name: "Materials", href: "/inventory", icon: Package },
    { name: "History", href: "/activity", icon: History },
    { name: "Reports", href: "/reports", icon: FileText },
    ...(isAdmin(user) ? [{ name: "Users", href: "/users", icon: Users }] : []),
  ];

  const logout = () => {
    clearSession();
    setUser(null);
    router.push("/dashboard");
  };

  return (
    <aside className="w-56 xl:w-60 bg-industrial-card border-r border-industrial-border min-h-screen p-4 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-2 mb-6 px-1">
          <span className="w-3 h-3 bg-blue-500 rounded-sm"></span>
          <span className="font-bold text-white tracking-wide text-sm">Digital Stand Register</span>
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${active ? "bg-blue-600 text-white" : "text-slate-300 hover:text-white hover:bg-slate-800/70"}`}>
                <Icon className="w-4 h-4" />{item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="pt-3 border-t border-industrial-border">
        {user ? (
          <div className="space-y-2">
            <div className="px-2">
              <div className="text-xs font-semibold text-slate-200">{user.username}</div>
              <div className="text-[10px] text-slate-500">{user.role === "ADMIN" ? "Admin" : "Operator"}</div>
            </div>
            <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-slate-800">
              <LogOut className="w-3.5 h-3.5" /> Sign out
            </button>
          </div>
        ) : (
          <Link href="/login" className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-blue-300 border border-blue-900/70 bg-blue-950/20 hover:bg-blue-950/40">
            <LogIn className="w-3.5 h-3.5" /> Sign in to edit
          </Link>
        )}
        <div className="mt-3 text-[10px] text-slate-600 text-center">Anyone with the link can view</div>
      </div>
    </aside>
  );
}
