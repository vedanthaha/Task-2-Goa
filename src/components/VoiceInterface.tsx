"use client";

import { InteractionState } from "../lib/types";
import { AudioWaveform } from "./AudioWaveform";

interface VoiceInterfaceProps {
  state: InteractionState;
  analyserNode: AnalyserNode | null;
  audioLevel?: number;
  hasSpoken?: boolean;
  selectedLanguage: string;
  onLanguageChange: (lang: string) => void;
  onStartListening: () => void;
  onStopListening: () => void;
  errorMessage?: string | null;
}

const LANGUAGES = [
  { code: "unknown", name: "Auto-Detect Language" },
  { code: "en-IN", name: "English (India)" },
  { code: "hi-IN", name: "हिन्दी (Hindi)" },
  { code: "te-IN", name: "తెలుగు (Telugu)" },
  { code: "ta-IN", name: "தமிழ் (Tamil)" },
  { code: "bn-IN", name: "বাংলা (Bengali)" },
  { code: "mr-IN", name: "मराठी (Marathi)" },
  { code: "gu-IN", name: "ગુજરાતી (Gujarati)" },
  { code: "kn-IN", name: "ಕನ್ನಡ (Kannada)" },
];

export function VoiceInterface({
  state,
  analyserNode,
  audioLevel = 0,
  hasSpoken = false,
  selectedLanguage,
  onLanguageChange,
  onStartListening,
  onStopListening,
  errorMessage,
}: VoiceInterfaceProps) {
  const isListening = state === "listening";
  const isBusy =
    state === "transcribing" ||
    state === "retrieving" ||
    state === "generating";

  const getStatusText = () => {
    switch (state) {
      case "listening":
        if (hasSpoken && audioLevel < 0.05) {
          return "Processing speech (pausing to submit)...";
        }
        return audioLevel > 0.05
          ? "Speaking detected... Keep talking"
          : "Listening... Speak your question into microphone";
      case "transcribing":
        return "Transcribing with Sarvam STT...";
      case "retrieving":
        return "Searching MSMARCO-XI knowledge...";
      case "generating":
        return "Synthesizing answer...";
      case "complete":
        return "Response ready";
      case "error":
        return errorMessage || "An error occurred";
      default:
        return "Click microphone to start speaking";
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-10 rounded-3xl bg-slate-900/40 border border-slate-800/80 shadow-2xl relative overflow-hidden backdrop-blur-md">
      {/* Background glow when active */}
      {isListening && (
        <div className="absolute inset-0 bg-emerald-500/5 blur-3xl pointer-events-none transition-opacity duration-700" />
      )}

      {/* Language Selector */}
      <div className="flex items-center gap-2 mb-6 z-10">
        <label
          htmlFor="lang-select"
          className="text-xs font-medium text-slate-400 font-mono"
        >
          Language:
        </label>
        <select
          id="lang-select"
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value)}
          disabled={isListening || isBusy}
          className="bg-slate-950/80 border border-slate-750 text-slate-200 text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all font-sans cursor-pointer disabled:opacity-50"
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.name}
            </option>
          ))}
        </select>
      </div>

      {/* Central Microphone Button with Multi-Ring Animation */}
      <div className="relative flex items-center justify-center my-4 z-10">
        {/* Pulsing ring during listening */}
        {isListening && (
          <>
            <span
              className="absolute rounded-full bg-emerald-500/20 animate-ping"
              style={{
                width: `${Math.max(120, 120 + audioLevel * 100)}px`,
                height: `${Math.max(120, 120 + audioLevel * 100)}px`,
              }}
            />
            <span
              className="absolute rounded-full bg-emerald-500/30 transition-all duration-75"
              style={{
                width: `${Math.max(100, 100 + audioLevel * 60)}px`,
                height: `${Math.max(100, 100 + audioLevel * 60)}px`,
              }}
            />
          </>
        )}

        <button
          onClick={isListening ? onStopListening : onStartListening}
          disabled={isBusy}
          aria-label={isListening ? "Stop listening" : "Start speaking"}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 transform active:scale-95 shadow-xl ${
            isListening
              ? "bg-rose-500 text-white shadow-rose-500/30 ring-4 ring-rose-400/40"
              : isBusy
              ? "bg-slate-800 text-emerald-400 ring-2 ring-emerald-500/30 cursor-wait"
              : "bg-gradient-to-tr from-emerald-500 to-cyan-500 text-slate-950 shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:scale-105"
          }`}
        >
          {isBusy ? (
            <svg
              className="w-10 h-10 animate-spin text-emerald-400"
              viewBox="0 0 24 24"
              fill="none"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : isListening ? (
            <svg className="w-9 h-9 fill-current" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          ) : (
            <svg className="w-10 h-10 fill-current" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          )}
        </button>
      </div>

      {/* Real-Time Waveform Visualizer */}
      <div className="w-full max-w-md my-2 z-10">
        <AudioWaveform
          analyserNode={analyserNode}
          isListening={isListening}
          audioLevel={audioLevel}
        />
      </div>

      {/* State Announcement Text */}
      <div className="text-center mt-2 z-10">
        <p
          className={`text-sm font-medium transition-colors ${
            state === "error"
              ? "text-rose-400"
              : isListening
              ? "text-emerald-400 font-mono animate-pulse"
              : isBusy
              ? "text-cyan-400 font-mono"
              : "text-slate-400"
          }`}
        >
          {getStatusText()}
        </p>
        <p className="text-[11px] text-slate-500 mt-1">
          {isListening
            ? "Auto-detects when you finish speaking • Or click button to stop"
            : "Click mic -> Speak question -> Automatically submits when you pause"}
        </p>
      </div>
    </div>
  );
}
