"use client";

import { useState } from "react";

interface TextInputFallbackProps {
  onSubmit: (text: string) => void;
  disabled: boolean;
}

const SAMPLE_QUERIES = [
  "What is machine learning?",
  "How does RRF retrieval work?",
  "How do bifacial solar panels work?",
  "Explain speech recognition",
  "भारत में सौर ऊर्जा",
];

export function TextInputFallback({ onSubmit, disabled }: TextInputFallbackProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || disabled) return;
    onSubmit(query.trim());
    setQuery("");
  };

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 12 }}>
      <form onSubmit={handleSubmit} style={{ position: "relative", display: "flex", alignItems: "center" }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled}
          placeholder="Or type a question…"
          className="text-input"
        />
        <button
          type="submit"
          disabled={!query.trim() || disabled}
          style={{
            position: "absolute", right: 8,
            padding: "7px 16px", borderRadius: 10,
            border: "none", cursor: query.trim() && !disabled ? "pointer" : "not-allowed",
            fontSize: 12, fontWeight: 600, fontFamily: "var(--font-mono), monospace",
            background: query.trim() && !disabled ? "linear-gradient(135deg, #7c5ff7, #5f5ce8)" : "rgba(255,255,255,0.05)",
            color: query.trim() && !disabled ? "white" : "#555",
            transition: "background 0.15s, color 0.15s",
          }}
        >
          Ask
        </button>
      </form>

      <div style={{ display: "flex", gap: 8, overflowX: "auto" }} className="no-scrollbar">
        {SAMPLE_QUERIES.map((sq, i) => (
          <button key={i} onClick={() => onSubmit(sq)} disabled={disabled} className="pill-btn">
            {sq}
          </button>
        ))}
      </div>
    </div>
  );
}
