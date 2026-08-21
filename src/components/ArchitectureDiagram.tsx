"use client";

import { ArrowRight, ArrowDown } from "lucide-react";

export function ArchitectureDiagram() {
  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
        <div>
          <h2 className="text-[20px] font-semibold text-white">System Architecture</h2>
          <p className="text-[13px] text-neutral-500 mt-1">
            Voice RAG data flow and execution graph
          </p>
        </div>
      </div>

      <div className="w-full glass-card bg-[rgba(255,255,255,0.01)] p-8 flex flex-col items-center justify-center min-h-[260px]">
        {/* Desktop/Tablet Pipeline */}
        <div className="hidden lg:flex flex-col items-center w-full relative">
          
          {/* Row 1 */}
          <div className="flex items-center gap-2 z-10 relative">
            <PipelineNode title="Voice Input" subtitle="WAV Stream" />
            <NodeConnector />
            <PipelineNode title="Sarvam STT" subtitle="Saaras v1" />
            <NodeConnector />
            <PipelineNode title="Guardrails" subtitle="Safety Checks" />
          </div>

          {/* Downwards to parallel */}
          <div className="h-6 border-l border-[rgba(255,255,255,0.1)] z-0" />
          
          <div className="w-full max-w-[280px] border-t border-[rgba(255,255,255,0.1)] flex justify-between relative z-0 h-4">
             <div className="w-[1px] h-full bg-[rgba(255,255,255,0.1)] absolute left-0 top-0" />
             <div className="w-[1px] h-full bg-[rgba(255,255,255,0.1)] absolute right-0 top-0" />
          </div>

          {/* Row 2: Parallel Search */}
          <div className="flex items-center justify-between w-full max-w-[320px] z-10 relative -mt-2">
            <PipelineNode title="Dense Vector" subtitle="Semantic" />
            <PipelineNode title="BM25 Lexical" subtitle="Keyword" />
          </div>

          {/* Downwards from parallel to RRF */}
          <div className="w-full max-w-[280px] border-b border-[rgba(255,255,255,0.1)] flex justify-between relative z-0 h-4 mt-0.5">
             <div className="w-[1px] h-full bg-[rgba(255,255,255,0.1)] absolute left-0 bottom-0" />
             <div className="w-[1px] h-full bg-[rgba(255,255,255,0.1)] absolute right-0 bottom-0" />
          </div>
          <div className="h-4 border-l border-[rgba(255,255,255,0.1)] z-0" />
          
          {/* Row 3 & 4 (Combined horizontally for compactness) */}
          <div className="flex items-center gap-2 z-10 relative mt-0.5">
            <PipelineNode title="RRF Fusion" subtitle="Rank Aggregation" highlight />
            <NodeConnector />
            <PipelineNode title="Adaptive Reranker" subtitle="Bypass Logic" />
            <NodeConnector />
            <PipelineNode title="LLM Gen" subtitle="Groq LLaMA 3.3" />
            <NodeConnector />
            <PipelineNode title="Grounding" subtitle="Verifier" />
          </div>
        </div>

        {/* Mobile View */}
        <div className="flex lg:hidden flex-col items-center space-y-2 w-full">
           <PipelineNode title="Voice Input" subtitle="WAV Stream" />
           <ArrowDown size={14} className="text-neutral-600" />
           <PipelineNode title="Sarvam STT" subtitle="Saaras v1" />
           <ArrowDown size={14} className="text-neutral-600" />
           <PipelineNode title="Guardrails" subtitle="Safety Checks" />
           <ArrowDown size={14} className="text-neutral-600" />
           
           <div className="flex gap-2 w-full justify-center my-1">
              <PipelineNode title="Dense Vector" subtitle="Semantic" />
              <PipelineNode title="BM25 Lexical" subtitle="Keyword" />
           </div>
           
           <ArrowDown size={14} className="text-neutral-600" />
           <PipelineNode title="RRF Fusion" subtitle="Rank Aggregation" highlight />
           <ArrowDown size={14} className="text-neutral-600" />
           <PipelineNode title="Adaptive Reranker" subtitle="Bypass Logic" />
           <ArrowDown size={14} className="text-neutral-600" />
           <PipelineNode title="LLM Gen" subtitle="Groq LLaMA 3.3" />
           <ArrowDown size={14} className="text-neutral-600" />
           <PipelineNode title="Grounding" subtitle="Verifier" />
        </div>
      </div>
    </div>
  );
}

function PipelineNode({ title, subtitle, highlight = false }: { title: string, subtitle: string, highlight?: boolean }) {
  return (
    <div className={`flex flex-col items-center justify-center text-center px-4 py-2.5 min-w-[120px] rounded-[10px] border ${highlight ? 'bg-[rgba(124,95,247,0.1)] border-[rgba(124,95,247,0.4)] shadow-[0_0_15px_rgba(124,95,247,0.15)]' : 'bg-[rgba(255,255,255,0.03)] border-[rgba(255,255,255,0.08)]'}`}>
      <span className="text-[13px] font-semibold text-white whitespace-nowrap">{title}</span>
      <span className="text-[11px] text-neutral-400 mt-0.5 font-mono uppercase tracking-wider">{subtitle}</span>
    </div>
  );
}

function NodeConnector() {
  return (
    <div className="text-neutral-700 mx-0.5">
      <ArrowRight size={14} strokeWidth={2} />
    </div>
  );
}
