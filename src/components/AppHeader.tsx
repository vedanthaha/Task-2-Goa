"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="app-header">
      <div className="app-header-inner">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-[10px] md:gap-[12px] no-underline">
          <img 
            src="/voice-logo.png" 
            alt="Voice RAG Logo" 
            className="w-[26px] h-[26px] md:w-[32px] md:h-[32px] object-contain bg-transparent border-0"
          />
          <span style={{ fontWeight: 600, color: "#f0f0f0", fontSize: 14, letterSpacing: "-0.02em" }}>
            Voice RAG
          </span>
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
      </div>
    </header>
  );
}
