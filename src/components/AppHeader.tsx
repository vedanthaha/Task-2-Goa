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
      .then((r) => setIsHealthy(r.status === "ok"))
      .catch(() => setIsHealthy(false));
  }, []);

  return (
    <header className="app-header">
      <div className="app-header-inner">
        {/* Logo */}
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "linear-gradient(135deg, #7c5ff7, #5f5ce8)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 12px rgba(124,95,247,0.3)"
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          </div>
          <span style={{ fontWeight: 600, color: "#f0f0f0", fontSize: 14, letterSpacing: "-0.02em" }}>
            Voice RAG
          </span>
          <span className="badge badge-purple">HH Goa 2026</span>
        </Link>

        {/* Nav */}
        <nav style={{ display: "flex", gap: 2 }}>
          <Link href="/" className={`nav-link ${pathname === "/" ? "active" : ""}`}>
            Search
          </Link>
          <Link href="/benchmark" className={`nav-link ${pathname === "/benchmark" ? "active" : ""}`}>
            Benchmark
          </Link>
        </nav>

        {/* Status */}
        <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, color: "#666" }}>
          <span style={{
            width: 7, height: 7, borderRadius: "50%", display: "inline-block",
            background: isHealthy === true ? "#4ade80" : isHealthy === false ? "#f87171" : "#555",
            boxShadow: isHealthy === true ? "0 0 6px #4ade80" : isHealthy === false ? "0 0 6px #f87171" : "none",
          }} />
          {isHealthy === true ? "API Ready" : isHealthy === false ? "Offline" : "Connecting…"}
        </div>
      </div>
    </header>
  );
}
