"use client";

import { AppHeader } from "../../components/AppHeader";
import { ArchitectureDiagram } from "../../components/ArchitectureDiagram";
import { BenchmarkDashboard } from "../../components/BenchmarkDashboard";

export default function BenchmarkPage() {
  return (
    <div className="min-h-screen page-bg flex flex-col font-sans">
      <AppHeader />

      <main className="flex-1 flex flex-col items-center px-6 md:px-8 py-10 w-full">
        <div className="w-full max-w-[1120px] space-y-8">
          {/* Hero Section */}
          <div className="space-y-4">
            <div className="text-[11px] font-medium tracking-wide uppercase text-neutral-500">
              Technical Architecture & Latency Benchmark
            </div>
            <h1 className="text-4xl font-semibold text-white tracking-tight leading-[1.1]">
              Voice RAG Performance Telemetry
            </h1>
            <p className="text-[15px] text-neutral-400 leading-relaxed max-w-[720px]">
              Benchmark the system against a measured &lt;200ms latency target.<br/>
              Offline indexing is decoupled from online inference across hybrid retrieval, adaptive reranking, and grounded generation.
            </p>
          </div>

          <div className="flex flex-col space-y-12">
            <BenchmarkDashboard />
            <ArchitectureDiagram />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-[#1A1A1A] py-6 text-center text-xs text-[#64748B]">
        HH Goa 2026 • Task 2 Voice-Enabled RAG • Benchmark & Architecture Telemetry
      </footer>
    </div>
  );
}