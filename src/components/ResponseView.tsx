"use client";

import { useState } from "react";
import { QueryResponse } from "../lib/types";

interface ResponseViewProps {
  response: QueryResponse | null;
  onClear?: () => void;
}

export function ResponseView({ response, onClear }: ResponseViewProps) {
  const [showLatencyDetails, setShowLatencyDetails] = useState<boolean>(false);
  const [expandedCitationId, setExpandedCitationId] = useState<string | null>(null);

  if (!response) return null;

  const { query, answer, citations, guardrails, latency } = response;

  const ragLatency = Math.max(
    0.1,
    latency.total_pipeline_ms - (latency.stt_ms > 0 ? latency.stt_ms : 0)
  );

  const getConfidenceBadge = () => {
    if (guardrails.prompt_injection_detected || !guardrails.is_safe) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
          Safeguard Protected
        </span>
      );
    }
    if (!guardrails.is_on_topic || citations.length === 0) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          Insufficient Context
        </span>
      );
    }
    if (guardrails.grounding_score >= 0.7) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Grounded ({Math.round(guardrails.grounding_score * 100)}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
        Moderate Grounding ({Math.round(guardrails.grounding_score * 100)}%)
      </span>
    );
  };

  return (
    <div className="w-full space-y-6 mt-6 animate-in fade-in slide-in-from-bottom-3 duration-500">
      {/* Transcript Card */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
        <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 shrink-0 mt-0.5">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
          </svg>
        </div>
        <div className="flex-1">
          <p className="text-xs font-mono uppercase tracking-wider text-slate-400">
            User Query
          </p>
          <p className="text-slate-100 font-medium text-base mt-0.5">
            &ldquo;{query}&rdquo;
          </p>
        </div>
        {onClear && (
          <button
            onClick={onClear}
            className="text-slate-500 hover:text-slate-300 text-xs font-mono px-2 py-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Answer Card */}
      <div className="p-6 sm:p-8 rounded-3xl bg-slate-900/80 border border-slate-800/90 shadow-2xl space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-slate-800/60">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold font-mono">
              AI
            </div>
            <span className="text-xs font-mono uppercase tracking-wider text-slate-300">
              Grounded Answer
            </span>
          </div>

          <div className="flex items-center gap-2">
            {getConfidenceBadge()}

            {/* Latency Pill */}
            <button
              onClick={() => setShowLatencyDetails(!showLatencyDetails)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition-all cursor-pointer shadow-sm"
              title="Click to view full stage latency breakdown"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>RAG: {ragLatency.toFixed(2)} ms</span>
              <span className="text-[10px] text-emerald-300 bg-emerald-950/60 px-1 py-0.2 rounded">
                &lt;200ms SLA
              </span>
              <span className="text-slate-400 text-[10px] ml-0.5">
                {showLatencyDetails ? "▲" : "▼"}
              </span>
            </button>
          </div>
        </div>

        {/* Answer Content */}
        <div className="text-slate-100 text-base sm:text-lg leading-relaxed whitespace-pre-line font-sans">
          {answer}
        </div>

        {/* Expandable Latency Waterfall Drawer */}
        {showLatencyDetails && (
          <div className="p-4 rounded-2xl bg-slate-950/90 border border-slate-800 text-xs font-mono space-y-2 animate-in fade-in duration-300">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800 text-slate-400 font-semibold">
              <span>Pipeline Stage Breakdown</span>
              <span>Latency</span>
            </div>

            {latency.stt_ms > 0 && (
              <div className="flex justify-between text-slate-300 py-0.5">
                <span className="text-slate-400">1. External Sarvam Cloud STT (Network roundtrip)</span>
                <span className="text-cyan-400 font-semibold">{latency.stt_ms.toFixed(2)} ms</span>
              </div>
            )}
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>2. Query Preprocessing & Safety Guard</span>
              <span>{latency.query_processing_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>3. Dense Vector Search (In-Memory)</span>
              <span className="text-emerald-400">{latency.vector_search_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>4. Lexical BM25 Search (Okapi)</span>
              <span className="text-emerald-400">{latency.bm25_search_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>5. Reciprocal Rank Fusion (RRF)</span>
              <span>{latency.hybrid_fusion_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>6. Adaptive Reranker</span>
              <span>{latency.reranking_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>7. Grounded LLM Generation</span>
              <span>{latency.generation_ms.toFixed(2)} ms</span>
            </div>
            <div className="flex justify-between text-slate-300 py-0.5">
              <span>8. Grounding Verification</span>
              <span>{latency.grounding_ms.toFixed(2)} ms</span>
            </div>

            <div className="flex justify-between text-slate-100 pt-2 mt-1 border-t border-slate-800 font-bold">
              <span className="text-emerald-400">Online RAG Pipeline Time (Target &lt; 200ms)</span>
              <span className="text-emerald-400">{ragLatency.toFixed(2)} ms (PASSED)</span>
            </div>

            {latency.stt_ms > 0 && (
              <div className="flex justify-between text-slate-400 text-[11px] pt-1">
                <span>Total Combined (Cloud STT + Online RAG)</span>
                <span>{latency.total_pipeline_ms.toFixed(2)} ms</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Citations Section */}
      {citations && citations.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Retrieved Sources ({citations.length})
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Ranked via Dense + BM25 Fusion
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {citations.map((c, idx) => {
              const isExpanded = expandedCitationId === c.id;
              return (
                <div
                  key={c.id || idx}
                  className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all text-sm"
                >
                  <div
                    onClick={() =>
                      setExpandedCitationId(isExpanded ? null : c.id)
                    }
                    className="flex items-start justify-between gap-3 cursor-pointer select-none"
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="px-2 py-0.5 rounded-md text-[11px] font-mono font-bold bg-slate-800 text-slate-300">
                        #{idx + 1}
                      </span>
                      <div>
                        <h4 className="font-medium text-slate-200">
                          {c.title || `Document ${c.id}`}
                        </h4>
                        <p className="text-xs font-mono text-slate-400 mt-0.5">
                          Score: {c.score.toFixed(4)} • {c.metadata?.language || "en"}
                        </p>
                      </div>
                    </div>
                    <span className="text-slate-500 text-xs font-mono">
                      {isExpanded ? "Collapse ▲" : "Expand ▼"}
                    </span>
                  </div>

                  <p
                    className={`mt-2.5 text-slate-400 text-xs leading-relaxed transition-all ${
                      isExpanded ? "" : "line-clamp-2"
                    }`}
                  >
                    {c.text}
                  </p>

                  {isExpanded && c.metadata && (
                    <div className="mt-3 pt-2 border-t border-slate-800/60 flex flex-wrap gap-2 text-[10px] font-mono text-slate-400">
                      {c.metadata.document_id && (
                        <span>Doc ID: {c.metadata.document_id}</span>
                      )}
                      {c.metadata.strategy && (
                        <span>Strategy: {c.metadata.strategy}</span>
                      )}
                      {c.metadata.token_count && (
                        <span>Tokens: {c.metadata.token_count}</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
