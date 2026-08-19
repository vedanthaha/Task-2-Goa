"use client";

import { useState } from "react";

interface TextInputFallbackProps {
  onSubmit: (text: string) => void;
  disabled: boolean;
}

const SAMPLE_QUERIES = [
  "What is machine learning?",
  "How does hybrid retrieval with RRF work?",
  "How do bifacial solar panels work?",
  "भारत में सौर ऊर्जा और फोटोवोल्टिक सेल",
  "Explain speech recognition architecture",
];

export function TextInputFallback({
  onSubmit,
  disabled,
}: TextInputFallbackProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || disabled) return;
    onSubmit(query.trim());
    setQuery("");
  };

  return (
    <div className="w-full space-y-3 mt-6">
      {/* Search Input Bar */}
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={disabled}
          placeholder="Or type a question (fallback text input)..."
          className="w-full pl-5 pr-28 py-3.5 rounded-2xl bg-slate-900/60 border border-slate-800 text-slate-100 placeholder:text-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all font-sans disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!query.trim() || disabled}
          className="absolute right-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 text-xs font-semibold font-mono transition-all disabled:cursor-not-allowed cursor-pointer"
        >
          Ask RAG
        </button>
      </form>

      {/* Suggested Quick Prompt Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar text-xs">
        <span className="text-slate-400 font-mono shrink-0">Try asking:</span>
        {SAMPLE_QUERIES.map((sq, i) => (
          <button
            key={i}
            onClick={() => onSubmit(sq)}
            disabled={disabled}
            className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800/80 transition-colors shrink-0 cursor-pointer disabled:opacity-50"
          >
            {sq}
          </button>
        ))}
      </div>
    </div>
  );
}
