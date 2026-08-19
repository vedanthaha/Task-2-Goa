"use client";

import { useState } from "react";
import { AppHeader } from "../components/AppHeader";
import { VoiceInterface } from "../components/VoiceInterface";
import { ResponseView } from "../components/ResponseView";
import { TextInputFallback } from "../components/TextInputFallback";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import { sendTextQuery, sendVoiceQuery } from "../lib/api";
import { InteractionState, QueryResponse } from "../lib/types";

export default function VoiceRAGPage() {
  const [state, setState] = useState<InteractionState>("idle");
  const [selectedLanguage, setSelectedLanguage] = useState<string>("en-IN");
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    isRecording,
    analyserNode,
    audioLevel,
    hasSpoken,
    startRecording,
    stopRecording,
    resetRecording,
    error: recorderError,
  } = useVoiceRecorder();

  // Process voice audio blob
  const processAudioBlob = async (blob: Blob) => {
    setState("transcribing");
    try {
      setState("retrieving");
      const resp = await sendVoiceQuery(blob, selectedLanguage, 5);
      setQueryResponse(resp);
      setState("complete");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Voice query failed. Please check microphone or use text fallback.";
      setErrorMessage(msg);
      setState("error");
    }
  };

  // Voice Interaction Handlers
  const handleStartListening = async () => {
    setErrorMessage(null);
    setState("listening");
    // Pass auto-stop callback: triggers automatically when speech finishes and silence is detected
    await startRecording(async (autoBlob: Blob) => {
      await processAudioBlob(autoBlob);
    });
  };

  const handleStopListening = async () => {
    setState("transcribing");
    try {
      const audioBlob = await stopRecording();
      if (!audioBlob || audioBlob.size === 0) {
        setState("idle");
        return;
      }
      await processAudioBlob(audioBlob);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Voice query failed. Please check microphone or use text fallback.";
      setErrorMessage(msg);
      setState("error");
    }
  };

  // Text Fallback Handler
  const handleTextSubmit = async (text: string) => {
    setErrorMessage(null);
    setState("retrieving");
    try {
      const resp = await sendTextQuery(text, 5);
      setQueryResponse(resp);
      setState("complete");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Text query failed. Please check backend connection.";
      setErrorMessage(msg);
      setState("error");
    }
  };

  const handleClear = () => {
    setQueryResponse(null);
    setState("idle");
    setErrorMessage(null);
    resetRecording();
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-emerald-500/30 selection:text-emerald-300">
      <AppHeader />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 flex flex-col items-center">
        {/* Hero title */}
        <div className="text-center space-y-2 mb-8 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-1">
            <span>●</span> MSMARCO-XI Multilingual Knowledge Base
          </div>
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-slate-100 font-sans">
            Fast Voice-Enabled RAG Search
          </h1>
          <p className="text-sm text-slate-400 font-sans leading-relaxed">
            Speak in Indian languages or English. Powered by Sarvam Speech-to-Text, parallel hybrid retrieval (Dense + BM25), and sub-200ms grounded generation.
          </p>
        </div>

        {/* Voice Interface Card */}
        <div className="w-full max-w-2xl">
          <VoiceInterface
            state={state}
            analyserNode={analyserNode}
            audioLevel={audioLevel}
            hasSpoken={hasSpoken}
            selectedLanguage={selectedLanguage}
            onLanguageChange={setSelectedLanguage}
            onStartListening={handleStartListening}
            onStopListening={handleStopListening}
            errorMessage={errorMessage || recorderError}
          />
        </div>

        {/* Text Input Fallback */}
        <div className="w-full max-w-2xl">
          <TextInputFallback
            onSubmit={handleTextSubmit}
            disabled={state === "listening" || state === "transcribing" || state === "retrieving" || state === "generating"}
          />
        </div>

        {/* Response View */}
        <div className="w-full max-w-3xl">
          <ResponseView response={queryResponse} onClear={handleClear} />
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="w-full border-t border-slate-800/60 py-6 text-center text-xs font-mono text-slate-400">
        HH Goa 2026 • Task 2 Voice-Enabled RAG • Sarvam STT • MSMARCO-XI • Sub-200ms Latency SLA
      </footer>
    </div>
  );
}
