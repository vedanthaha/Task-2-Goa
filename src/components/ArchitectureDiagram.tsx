"use client";

export function ArchitectureDiagram() {
  const steps = [
    {
      num: "01",
      title: "Voice Input",
      desc: "Browser MediaRecorder / WAV stream",
      badge: "Realtime",
      color: "from-emerald-500 to-teal-500",
    },
    {
      num: "02",
      title: "Sarvam STT",
      desc: "Indic & English speech transcription",
      badge: "Saaras v1",
      color: "from-cyan-500 to-blue-500",
    },
    {
      num: "03",
      title: "Safety Guardrails",
      desc: "Prompt injection & off-topic checks",
      badge: "Security",
      color: "from-indigo-500 to-violet-500",
    },
    {
      num: "04",
      title: "Parallel Hybrid Search",
      desc: "Dense Vector + BM25 Lexical concurrent",
      badge: "MSMARCO-XI",
      color: "from-purple-500 to-pink-500",
    },
    {
      num: "05",
      title: "Reciprocal Rank Fusion",
      desc: "RRF score aggregation: w/(k + rank)",
      badge: "Fusion",
      color: "from-pink-500 to-rose-500",
    },
    {
      num: "06",
      title: "Adaptive Reranker",
      desc: "Confidence bypass to protect <200ms SLA",
      badge: "Low-Latency",
      color: "from-amber-500 to-orange-500",
    },
    {
      num: "07",
      title: "Grounded Generation",
      desc: "Context-bounded LLM response with citations",
      badge: "Gemini",
      color: "from-emerald-500 to-cyan-500",
    },
    {
      num: "08",
      title: "Grounding Verifier",
      desc: "Post-generation hallucination detection",
      badge: "Verification",
      color: "from-teal-500 to-emerald-500",
    },
  ];

  return (
    <div className="w-full p-6 sm:p-8 glass-card shadow-2xl space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2 pb-4 border-b border-white/10">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            End-to-End Pipeline Architecture
          </h2>
          <p className="text-xs text-white/50 mt-0.5">
            Strict separation between Offline Indexing and Online Inference
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Target SLA: &lt;200ms
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((s, idx) => (
          <div
            key={idx}
            className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-white/20 transition-all space-y-2 relative overflow-hidden group"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-white/40 group-hover:text-white/70 transition-colors">
                {s.num}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-black/40 border border-white/10 text-white/50">
                {s.badge}
              </span>
            </div>

            <div className="text-sm font-semibold text-white/90">
              {s.title}
            </div>

            <p className="text-xs text-white/50 leading-relaxed font-sans">
              {s.desc}
            </p>

            <div
              className={`h-1 w-full rounded-full bg-gradient-to-r ${s.color} opacity-40 group-hover:opacity-100 transition-opacity mt-2`}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
