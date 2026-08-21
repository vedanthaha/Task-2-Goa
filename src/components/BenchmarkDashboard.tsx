"use client";

import { useState } from "react";
import { BenchmarkResponse } from "../lib/types";
import { runBenchmark } from "../lib/api";

const PRESET_QUERIES = [
  "What is machine learning?",
  "How does hybrid retrieval with RRF work?",
  "What are the benefits of solar photovoltaic systems?",
  "What is MSMARCO dataset?",
  "Tell me about speech recognition architecture.",
  "भारत में सौर ऊर्जा तकनीक और फोटोवोल्टिक सेल",
  "Explain deep neural network acoustic modeling",
  "How do container microservices communicate via gRPC?",
];

export function BenchmarkDashboard() {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);
  const [lastRunTime, setLastRunTime] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunBenchmark = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const data = await runBenchmark(PRESET_QUERIES, 5);
      setBenchmarkData(data);
      setLastRunTime(new Date());
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to execute benchmark."
      );
    } finally {
      setIsRunning(false);
    }
  };

  const getDistribution = () => {
    if (!benchmarkData || !benchmarkData.results || benchmarkData.results.length === 0) {
      return { p1_2: 0, p2_5: 0, p5_10: 0, p10_plus: 0 };
    }

    let p1_2 = 0, p2_5 = 0, p5_10 = 0, p10_plus = 0;
    const total = benchmarkData.results.length;

    benchmarkData.results.forEach(r => {
      const val = r.latency_ms || 0;
      if (val <= 2) p1_2++;
      else if (val <= 5) p2_5++;
      else if (val <= 10) p5_10++;
      else p10_plus++;
    });

    return {
      p1_2: Math.round((p1_2 / total) * 100),
      p2_5: Math.round((p2_5 / total) * 100),
      p5_10: Math.round((p5_10 / total) * 100),
      p10_plus: Math.round((p10_plus / total) * 100)
    };
  };

  const dist = getDistribution();

  return (
    <div className="w-full glass-card overflow-hidden">
      {/* Header Area */}
      <div className="p-6 md:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[rgba(255,255,255,0.05)]">
        <div>
          <h2 className="text-[22px] font-medium text-white tracking-tight flex items-center gap-3">
            Performance Telemetry
            {lastRunTime && (
              <span className="badge badge-purple text-[10px]">Updated</span>
            )}
          </h2>
          <p className="text-[13px] text-neutral-400 mt-1.5">
            {lastRunTime ? `Last run: ${lastRunTime.toLocaleTimeString()}` : "Not run yet"}
          </p>
        </div>
        <button
          onClick={handleRunBenchmark}
          disabled={isRunning}
          className="glass-button px-5 py-2.5 rounded-xl text-[13px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed h-[38px] gap-2"
        >
          {isRunning ? (
            <>
              <span className="inline-block w-3.5 h-3.5 border-2 border-[rgba(255,255,255,0.3)] border-t-white rounded-full animate-spin" />
              Running...
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12l5 5l10 -10"></path>
              </svg>
              Run Benchmark
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="m-6 p-4 bg-red-950/20 border border-red-900/30 rounded-[10px] text-red-400 text-sm flex items-center gap-3">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          {error}
        </div>
      )}

      {/* Main Dashboard Surface */}
      <div className="w-full bg-[rgba(255,255,255,0.01)] relative">
        
        {!benchmarkData && !isRunning && (
          <div className="flex flex-col items-center justify-center py-16 px-6">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-600 mb-4"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
            <p className="text-[15px] font-medium text-neutral-300">No benchmark run yet</p>
            <p className="text-[13px] text-neutral-500 mt-1 max-w-[280px] text-center leading-relaxed">Run the benchmark to generate measured telemetry across the entire retrieval pipeline.</p>
          </div>
        )}

        {isRunning && !benchmarkData && (
          <div className="flex flex-col items-center justify-center py-16 px-6">
            <span className="inline-block w-8 h-8 border-2 border-[rgba(255,255,255,0.1)] border-t-[#a78bfa] rounded-full animate-spin mb-4" />
            <p className="text-[14px] font-medium text-neutral-300">Executing Queries</p>
            <p className="text-[13px] text-neutral-500 mt-1 text-center">Capturing end-to-end latency and distributions...</p>
          </div>
        )}

        {benchmarkData && (
          <div className="animate-in fade-in duration-500 flex flex-col">
            
            {/* KPI Row (Single Cohesive Surface) */}
            <div className="grid grid-cols-2 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-[rgba(255,255,255,0.05)] border-b border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)]">
              <div className="p-5 flex flex-col justify-center">
                <span className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider mb-2">SLA</span>
                <div className={`text-[28px] font-bold ${benchmarkData.target_met ? 'text-emerald-400' : 'text-red-400'} leading-none`}>
                  {benchmarkData.target_met ? 'PASS' : 'FAIL'}
                </div>
              </div>
              <div className="p-5 flex flex-col justify-center">
                <span className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider mb-2">P50</span>
                <div className="text-[28px] font-bold text-white leading-none flex items-baseline gap-1.5">
                  {benchmarkData.p50_ms.toFixed(2)}
                  <span className="text-[12px] font-mono font-normal text-neutral-500">ms</span>
                </div>
              </div>
              <div className="p-5 flex flex-col justify-center">
                <span className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider mb-2">P95</span>
                <div className="text-[28px] font-bold text-white leading-none flex items-baseline gap-1.5">
                  {benchmarkData.p95_ms.toFixed(2)}
                  <span className="text-[12px] font-mono font-normal text-neutral-500">ms</span>
                </div>
              </div>
              <div className="p-5 flex flex-col justify-center">
                <span className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider mb-2">P100</span>
                <div className="text-[28px] font-bold text-white leading-none flex items-baseline gap-1.5">
                  {benchmarkData.p100_ms.toFixed(2)}
                  <span className="text-[12px] font-mono font-normal text-neutral-500">ms</span>
                </div>
              </div>
              <div className="p-5 flex flex-col justify-center">
                <span className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider mb-2">Mean</span>
                <div className="text-[28px] font-bold text-white leading-none flex items-baseline gap-1.5">
                  {benchmarkData.mean_ms.toFixed(2)}
                  <span className="text-[12px] font-mono font-normal text-neutral-500">ms</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[rgba(255,255,255,0.05)]">
              {/* Latency Distribution */}
              <div className="p-6 md:p-8">
                <h3 className="text-[14px] font-medium text-white mb-6 tracking-wide">Latency Distribution</h3>
                <div className="space-y-4">
                  {[
                    { label: "1–2 ms", value: dist.p1_2 },
                    { label: "2–5 ms", value: dist.p2_5 },
                    { label: "5–10 ms", value: dist.p5_10 },
                    { label: ">10 ms", value: dist.p10_plus },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center h-[28px]">
                      <span className="w-16 text-[12px] text-neutral-400 shrink-0 font-mono">
                        {item.label}
                      </span>
                      <div className="flex-1 mx-4 h-[4px] rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-[#7c5ff7] to-[#5f5ce8] rounded-full transition-all duration-700"
                          style={{ width: `${Math.max(item.value, 0)}%` }}
                        />
                      </div>
                      <span className="w-8 text-[12px] font-mono text-neutral-300 text-right shrink-0">
                        {item.value}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Mock Stage Latency (Since API doesn't return it yet, we show a clean compact list) */}
              <div className="p-6 md:p-8">
                <h3 className="text-[14px] font-medium text-white mb-6 tracking-wide">Stage Latency (Estimated)</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.05)]">
                    <span className="text-[13px] text-neutral-300">Sarvam STT</span>
                    <span className="text-[12px] font-mono text-neutral-400">~600 ms</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.05)]">
                    <span className="text-[13px] text-neutral-300">Dense Retrieval</span>
                    <span className="text-[12px] font-mono text-neutral-400">~45 ms</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.05)]">
                    <span className="text-[13px] text-neutral-300">BM25</span>
                    <span className="text-[12px] font-mono text-neutral-400">~25 ms</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.05)]">
                    <span className="text-[13px] text-neutral-300">RRF Fusion</span>
                    <span className="text-[12px] font-mono text-neutral-400">~5 ms</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-[rgba(255,255,255,0.05)]">
                    <span className="text-[13px] text-neutral-300">Grounded Generation</span>
                    <span className="text-[12px] font-mono text-neutral-400">~800 ms</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}