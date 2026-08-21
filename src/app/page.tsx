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
    analyserNode,
    audioLevel,
    hasSpoken,
    startRecording,
    stopRecording,
    resetRecording,
    error: recorderError,
  } = useVoiceRecorder();

  const processAudioBlob = async (blob: Blob) => {
    setState("transcribing");
    try {
      setState("retrieving");
      const resp = await sendVoiceQuery(blob, selectedLanguage, 5);
      setQueryResponse(resp);
      setState("complete");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Voice query failed.");
      setState("error");
    }
  };

  const handleStartListening = async () => {
    setErrorMessage(null);
    setState("listening");
    await startRecording(async (blob: Blob) => { await processAudioBlob(blob); });
  };

  const handleStopListening = async () => {
    setState("transcribing");
    try {
      const blob = await stopRecording();
      if (!blob || blob.size === 0) { setState("idle"); return; }
      await processAudioBlob(blob);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Voice query failed.");
      setState("error");
    }
  };

  const handleTextSubmit = async (text: string) => {
    setErrorMessage(null);
    setState("retrieving");
    try {
      const resp = await sendTextQuery(text, 5);
      setQueryResponse(resp);
      setState("complete");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Query failed.");
      setState("error");
    }
  };

  const handleClear = () => {
    setQueryResponse(null);
    setState("idle");
    setErrorMessage(null);
    resetRecording();
  };

  const isBusy = ["listening","transcribing","retrieving","generating"].includes(state);
  const showHero = state === "idle" && !queryResponse;

  return (
    <div className="page-bg" style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <AppHeader />

      <main style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",     /* centres children horizontally */
        justifyContent: "flex-start",
        padding: "24px 24px 40px",
        width: "100%",
      }}>
        {/* Inner container — fixed width, centred */}
        <div style={{ width: "100%", maxWidth: 620 }}>

          {/* Hero — only when idle */}
          {showHero && (
            <div className="fade-up" style={{ textAlign: "center", marginBottom: 40 }}>
              <h1 style={{ fontSize: "clamp(32px, 6vw, 48px)", fontWeight: 500, letterSpacing: "-0.02em", lineHeight: 1.2, color: "#e2e8f0", marginBottom: 12 }}>
                Talk to HH Goa AI –<br />
                <span style={{ color: "#94a3b8" }}>Smarter, Faster, Better</span>
              </h1>
            </div>
          )}

          {/* Voice interface */}
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

          {/* Or type divider */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "8px 0 16px" }}>
            <hr className="divider" />
            <span style={{ fontSize: 11, color: "#555", fontFamily: "var(--font-mono), monospace", flexShrink: 0 }}>or type</span>
            <hr className="divider" />
          </div>

          {/* Text input */}
          <TextInputFallback onSubmit={handleTextSubmit} disabled={isBusy} />

          {/* Response */}
          <ResponseView response={queryResponse} onClear={handleClear} />
        </div>
      </main>

      <footer style={{ textAlign: "center", padding: "24px 0", fontSize: 10, fontFamily: "var(--font-mono), monospace", color: "#333", letterSpacing: "0.1em" }}>
        HH GOA 2026 · TASK 2 · VOICE-ENABLED RAG
      </footer>
    </div>
  );
}
