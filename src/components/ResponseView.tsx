"use client";

import { useState } from "react";
import { QueryResponse } from "../lib/types";

interface ResponseViewProps {
  response: QueryResponse | null;
  onClear?: () => void;
}

export function ResponseView({ response, onClear }: ResponseViewProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showLatency, setShowLatency] = useState(false);

  if (!response) return null;

  const { query, answer, citations, guardrails, latency } = response;

  const ragMs = Math.max(0.1, latency.total_pipeline_ms - (latency.stt_ms > 0 ? latency.stt_ms : 0));
  const slaPass = ragMs <= 200;
  const groundingPct = Math.round(guardrails.grounding_score * 100);

  const stages: Array<{ label: string; ms: number; accent?: string }> = [
    { label: "Query Guard", ms: latency.query_processing_ms },
    { label: "Dense Vector", ms: latency.vector_search_ms, accent: "#4ade80" },
    { label: "BM25 Lexical", ms: latency.bm25_search_ms, accent: "#4ade80" },
    { label: "RRF Fusion", ms: latency.hybrid_fusion_ms },
    { label: "Reranking", ms: latency.reranking_ms },
    { label: "LLM Generation", ms: latency.generation_ms, accent: latency.generation_ms > 200 ? "#f87171" : "#4ade80" },
    { label: "Grounding", ms: latency.grounding_ms },
  ];
  const maxMs = Math.max(...stages.map((s) => s.ms), 1);

  return (
    <div className="fade-up" style={{ width: "100%", marginTop: 32, display: "flex", flexDirection: "column", gap: 16 }}>

      {/* Query echo */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "0 4px" }}>
        <div style={{
          width: 24, height: 24, borderRadius: "50%",
          background: "rgba(255,255,255,0.05)", display: "flex", alignItems: "center",
          justifyContent: "center", flexShrink: 0, marginTop: 2
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="#666">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
          </svg>
        </div>
        <p style={{ fontSize: 13, color: "#888", fontStyle: "italic", flex: 1, lineHeight: 1.6 }}>"{query}"</p>
        {onClear && (
          <button onClick={onClear} style={{ fontSize: 12, color: "#555", background: "none", border: "none", cursor: "pointer", flexShrink: 0, transition: "color 0.15s" }}
            onMouseOver={(e) => (e.currentTarget.style.color = "#f0f0f0")}
            onMouseOut={(e) => (e.currentTarget.style.color = "#555")}
          >
            Clear
          </button>
        )}
      </div>

      {/* Answer card */}
      <div className="glass-card" style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Top bar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 24, height: 24, borderRadius: 8, background: "rgba(124,95,247,0.12)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="12" height="12" viewBox="0 0 20 20" fill="#a78bfa">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <span style={{ fontSize: 11, fontFamily: "var(--font-mono), monospace", color: "#666", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Grounded Answer
            </span>
          </div>

          <div style={{ display: "flex", gap: 7, flexWrap: "wrap" }}>
            <span className={`badge ${groundingPct >= 70 ? "badge-green" : "badge-amber"}`}>
              Grounded {groundingPct}%
            </span>
            <button
              onClick={() => setShowLatency(!showLatency)}
              className={`badge ${slaPass ? "badge-green" : "badge-red"}`}
              style={{ cursor: "pointer" }}
            >
              ⚡ {ragMs.toFixed(0)}ms {slaPass ? "✓" : "✗"}
            </button>
          </div>
        </div>

        {/* Answer text */}
        <p style={{ fontSize: 15, lineHeight: 1.75, color: "#e8e8e8" }}>{answer}</p>

        {/* Latency breakdown */}
        {showLatency && (
          <div className="fade-up" style={{ paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.07)", display: "flex", flexDirection: "column", gap: 10 }}>
            <p style={{ fontSize: 10, fontFamily: "var(--font-mono), monospace", color: "#555", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Pipeline Breakdown
            </p>
            {latency.stt_ms > 0 && (
              <LatRow label="Sarvam Cloud STT" ms={latency.stt_ms} maxMs={latency.stt_ms} accent="#fbbf24" note="external" />
            )}
            {stages.map((s) => (
              <LatRow key={s.label} label={s.label} ms={s.ms} maxMs={maxMs} accent={s.accent} />
            ))}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 10, borderTop: "1px solid rgba(255,255,255,0.06)" }}>
              <span style={{ fontSize: 12, fontFamily: "var(--font-mono), monospace", color: "#888" }}>Online RAG Total</span>
              <span style={{ fontSize: 13, fontFamily: "var(--font-mono), monospace", fontWeight: 600, color: slaPass ? "#4ade80" : "#f87171" }}>
                {ragMs.toFixed(1)}ms — {slaPass ? "PASSED ✓" : "FAILED ✗"} &lt;200ms
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Sources */}
      {citations && citations.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0 4px" }}>
            <p style={{ fontSize: 11, fontFamily: "var(--font-mono), monospace", color: "#555", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Sources ({citations.length})
            </p>
            <p style={{ fontSize: 10, color: "#444", fontFamily: "var(--font-mono), monospace" }}>Dense + BM25 RRF</p>
          </div>
          {citations.map((c, idx) => {
            const id = c.id ?? String(idx);
            const open = expandedId === id;
            return (
              <div key={id} className="source-card">
                <button
                  onClick={() => setExpandedId(open ? null : id)}
                  style={{ width: "100%", display: "flex", alignItems: "flex-start", gap: 12, padding: "14px 16px", background: "none", border: "none", cursor: "pointer", textAlign: "left" }}
                >
                  <span style={{ fontSize: 10, fontFamily: "var(--font-mono), monospace", color: "#555", flexShrink: 0, marginTop: 2, minWidth: 18, textAlign: "right" }}>
                    {idx + 1}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 13, color: "#ccc", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.title || `Source ${idx + 1}`}
                    </p>
                    <p style={{ fontSize: 12, color: "#666", marginTop: 3, lineHeight: 1.5, display: "-webkit-box", WebkitLineClamp: open ? "unset" : 2, WebkitBoxOrient: "vertical", overflow: open ? "visible" : "hidden" }}>
                      {c.text}
                    </p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                    {c.score != null && (
                      <span style={{ fontSize: 10, fontFamily: "var(--font-mono), monospace", color: "#555" }}>
                        {c.score.toFixed(3)}
                      </span>
                    )}
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="2"
                      style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function LatRow({ label, ms, maxMs, accent, note }: { label: string; ms: number; maxMs: number; accent?: string; note?: string }) {
  const pct = Math.min(100, (ms / maxMs) * 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ fontSize: 11, color: "#666", width: 120, flexShrink: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</span>
      <div className="lat-bar-track">
        <div className="lat-bar-fill" style={{ width: `${pct}%`, background: accent ?? "rgba(255,255,255,0.18)" }} />
      </div>
      <span style={{ fontSize: 11, fontFamily: "var(--font-mono), monospace", color: accent ?? "#666", width: 60, textAlign: "right", flexShrink: 0 }}>
        {ms.toFixed(1)}ms{note && <span style={{ color: "#555", fontSize: 9 }}> ({note})</span>}
      </span>
    </div>
  );
}
