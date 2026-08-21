"use client";

import { InteractionState } from "../lib/types";
import { VoicePoweredOrb } from "./ui/voice-powered-orb";
import { ShimmerButton } from "./ui/shimmer-button";

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
  { code: "unknown", name: "Auto-Detect" },
  { code: "en-IN",  name: "English (India)" },
  { code: "hi-IN",  name: "हिन्दी" },
  { code: "te-IN",  name: "తెలుగు" },
  { code: "ta-IN",  name: "தமிழ்" },
  { code: "bn-IN",  name: "বাংলা" },
  { code: "mr-IN",  name: "मराठी" },
  { code: "gu-IN",  name: "ગુજરાતી" },
  { code: "kn-IN",  name: "ಕನ್ನಡ" },
];

export function VoiceInterface({
  state,
  audioLevel = 0,
  hasSpoken = false,
  selectedLanguage,
  onLanguageChange,
  onStartListening,
  onStopListening,
  errorMessage,
}: VoiceInterfaceProps) {
  const isListening = state === "listening";
  const isBusy = state === "transcribing" || state === "retrieving" || state === "generating";
  const isError = state === "error";

  const statusText = () => {
    if (isError) return errorMessage || "Something went wrong";
    if (isListening && hasSpoken && audioLevel < 0.05) return "Almost done — processing…";
    if (isListening) return audioLevel > 0.05 ? "Listening — keep speaking" : "Listening — say something";
    if (state === "transcribing") return "Transcribing with Sarvam STT…";
    if (state === "retrieving") return "Searching knowledge base…";
    if (state === "generating") return "Generating answer…";
    if (state === "complete") return "Done ✓";
    return "";
  };

  const statusColor = isError ? "#f87171" : isListening ? "#60a5fa" : isBusy ? "#888" : "#555";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, paddingTop: 16, paddingBottom: 16, width: "100%" }}>
      {/* Orb Container */}
      <div style={{ position: "relative", width: 220, height: 220, display: "flex", alignItems: "center", justifyContent: "center" }}>
        
        <VoicePoweredOrb
          enableVoiceControl={isListening}
          className="rounded-full shadow-[0_0_80px_rgba(37,99,235,0.15)]"
          hue={220} // Blueish hue
        />
        
        {/* Center Mic Icon (Optional: inside the orb) */}
        <div style={{ position: "absolute", zIndex: 10, pointerEvents: "none" }}>
          {isBusy ? (
            <div className="spin-ring" style={{ width: 40, height: 40, borderColor: "rgba(255,255,255,0.3)", borderTopColor: "white" }} />
          ) : (
            <svg width="32" height="32" viewBox="0 0 24 24" fill="white" style={{ opacity: isListening ? 1 : 0.8, filter: isListening ? 'drop-shadow(0 0 8px rgba(255,255,255,0.8))' : 'none', transition: 'all 0.3s' }}>
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
        {/* Action Button */}
        <ShimmerButton
          onClick={isListening ? onStopListening : onStartListening}
          disabled={isBusy}
          shimmerColor="#fbbf24"
          background="#09090b"
          borderRadius="9999px"
          className="shadow-2xl dark:text-white"
        >
          <span className="flex items-center gap-3 px-6 font-medium text-white z-10 relative">
            <span>{isBusy ? "Processing..." : isListening ? "Stop" : "Speak"}</span>
            {!isBusy && !isListening && (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            )}
          </span>
        </ShimmerButton>

        {/* Status */}
        <p style={{ fontSize: 13, color: statusColor, textAlign: "center", transition: "color 0.3s", minHeight: 20 }}>
          {statusText()}
        </p>

        {/* Language selector */}
        <select
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value)}
          disabled={isListening || isBusy}
          className="lang-select"
          style={{ 
            marginTop: 8, 
            background: "rgba(255,255,255,0.03)", 
            border: "1px solid rgba(255,255,255,0.1)", 
            color: "#aaa",
            borderRadius: 100,
            padding: "6px 12px",
            fontSize: 12
          }}
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>{l.name}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
