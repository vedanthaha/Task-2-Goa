"use client";

import { AppHeader } from "../../components/AppHeader";
import { ArchitectureDiagram } from "../../components/ArchitectureDiagram";
import { BenchmarkDashboard } from "../../components/BenchmarkDashboard";

export default function BenchmarkPage() {
  return (
    <div className="min-h-screen bg-[#0A0A0A] flex flex-col">
      <AppHeader />

      <main className="flex-1 flex flex-col items-center px-4 py-8 sm:py-12 w-full">
        <div className="w-full max-w-5xl space-y-8">
          {/* Page Header */}
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#1A1A1A] border border-[#2A2A2A] rounded-full text-xs font-medium text-[#94A3B8]">
              <span className="text-yellow-400">●</span>
              Performance Engineering & Hackathon Diagnostics
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Technical Architecture & Latency SLA Benchmark
            </h1>
            <p className="text-sm sm:text-base text-[#64748B] leading-relaxed max-w-3xl">
              Empirical benchmarking report for HH Goa 2026 Task 2. Offline dataset ingestion is completely decoupled from online inference to guarantee sub-200ms latency across parallel hybrid retrieval, adaptive reranking, and grounded answer synthesis.
            </p>
          </div>

          {/* Live Benchmark Dashboard */}
          <BenchmarkDashboard />

          {/* Pipeline Architecture Diagram */}
          <ArchitectureDiagram />
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-[#1A1A1A] py-4 text-center text-xs text-[#64748B]">
        HH Goa 2026 • Task 2 Voice-Enabled RAG • Benchmark & Architecture Telemetry
      </footer>
    </div>
  );
}