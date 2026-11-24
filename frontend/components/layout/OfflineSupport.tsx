"use client";
import { useEffect } from "react";
export default function OfflineSupport() {
  useEffect(() => {
    if (process.env.NEXT_PUBLIC_OFFLINE_SHELL !== "1" || !("serviceWorker" in navigator)) return;
    // Failure to cache must never block the application.
    navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" }).catch(() => {});
  }, []);
  return null;
}
