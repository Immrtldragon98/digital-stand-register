"use client";

export default function Footer() {
  return (
    <footer className="bg-industrial-card border-t border-industrial-border py-4 px-6 text-center text-xs text-slate-500">
      &copy; {new Date().getFullYear()} Digital Stand Register Platform. All industrial rights reserved.
    </footer>
  );
}