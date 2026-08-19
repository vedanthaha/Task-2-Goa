"use client";

import { AppHeader } from "../../components/AppHeader";
import { ArchitectureDiagram } from "../../components/ArchitectureDiagram";
import { BenchmarkDashboard } from "../../components/BenchmarkDashboard";

export default function BenchmarkPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-emerald-500/30 selection:text-emerald-300">
      <AppHeader />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-10">
        {/* Page Header */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <span>●</span> Performance Engineering & Hackathon Diagnostics
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 font-sans">
            Technical Architecture & Latency SLA Benchmark
          </h1>
          <p className="text-sm text-slate-400 font-sans max-w-3xl leading-relaxed">
            Empirical benchmarking report for HH Goa 2026 Task 2. Offline dataset ingestion is completely decoupled from online inference to guarantee sub-200ms latency across parallel hybrid retrieval, adaptive reranking, and grounded answer synthesis.
          </p>
        </div>

        {/* Live Benchmark & Telemetry Section */}
        <BenchmarkDashboard />

        {/* Pipeline Architecture Flowchart */}
        <ArchitectureDiagram />
      </main>

      {/* Minimal Footer */}
      <footer className="w-full border-t border-slate-800/60 py-6 text-center text-xs font-mono text-slate-400">
        HH Goa 2026 • Task 2 Voice-Enabled RAG • Benchmark & Architecture Telemetry
      </footer>
    </div>
  );
}
