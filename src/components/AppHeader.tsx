"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchHealth } from "../lib/api";

export function AppHeader() {
  const pathname = usePathname();
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((res) => setIsHealthy(res.status === "ok"))
      .catch(() => setIsHealthy(false));
  }, []);

  return (
    <header className="w-full border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <svg
              className="w-5 h-5 text-slate-950 fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-100 tracking-tight text-base">
                HH Goa RAG
              </span>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Task 2
              </span>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              Multilingual Voice-Enabled RAG
            </p>
          </div>
        </Link>

        {/* Navigation & Status Beacon */}
        <div className="flex items-center gap-4">
          <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-sm">
            <Link
              href="/"
              className={`px-3.5 py-1.5 rounded-lg font-medium transition-all ${
                pathname === "/"
                  ? "bg-slate-800 text-slate-100 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Voice Search
            </Link>
            <Link
              href="/benchmark"
              className={`px-3.5 py-1.5 rounded-lg font-medium transition-all ${
                pathname === "/benchmark"
                  ? "bg-slate-800 text-slate-100 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Benchmark & SLA
            </Link>
          </nav>

          {/* System Status Pill */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy === true
                  ? "bg-emerald-400 shadow-[0_0_8px_#34d399]"
                  : isHealthy === false
                  ? "bg-amber-400 shadow-[0_0_8px_#fbbf24]"
                  : "bg-slate-500 animate-pulse"
              }`}
            />
            <span className="text-slate-300">
              {isHealthy === true
                ? "System Ready"
                : isHealthy === false
                ? "Offline Mode"
                : "Connecting..."}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
