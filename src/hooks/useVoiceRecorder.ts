"use client";

import { useCallback, useRef, useState } from "react";

export interface VoiceRecorderState {
  isRecording: boolean;
  audioBlob: Blob | null;
  error: string | null;
  analyserNode: AnalyserNode | null;
  audioLevel: number;
  hasSpoken: boolean;
  startRecording: (onAutoStop?: (blob: Blob) => void) => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  resetRecording: () => void;
}

export function useVoiceRecorder(): VoiceRecorderState {
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [hasSpoken, setHasSpoken] = useState<boolean>(false);

  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const speechDetectedRef = useRef<boolean>(false);
  const silenceStartRef = useRef<number | null>(null);
  const startTimeRef = useRef<number>(0);
  const autoStopCallbackRef = useRef<((blob: Blob) => void) | null>(null);
  const isStoppingRef = useRef<boolean>(false);

  const stopRecordingInternal = useCallback(async (): Promise<Blob | null> => {
    if (isStoppingRef.current) return null;
    isStoppingRef.current = true;

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setIsRecording(false);
    setAudioLevel(0);
    setHasSpoken(false);

    return new Promise<Blob | null>((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        isStoppingRef.current = false;
        resolve(null);
        return;
      }

      recorder.onstop = () => {
        const mimeType = recorder.mimeType || "audio/webm";
        const finalBlob = new Blob(audioChunksRef.current, { type: mimeType });
        setAudioBlob(finalBlob);

        // Stop stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }

        // Close AudioContext
        if (audioContextRef.current) {
          audioContextRef.current.close().catch(() => {});
          audioContextRef.current = null;
        }
        setAnalyserNode(null);

        isStoppingRef.current = false;
        resolve(finalBlob);
      };

      recorder.stop();
    });
  }, []);

  const startRecording = useCallback(
    async (onAutoStop?: (blob: Blob) => void) => {
      setError(null);
      setAudioBlob(null);
      setHasSpoken(false);
      audioChunksRef.current = [];
      speechDetectedRef.current = false;
      silenceStartRef.current = null;
      startTimeRef.current = Date.now();
      autoStopCallbackRef.current = onAutoStop || null;
      isStoppingRef.current = false;

      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error(
            "Microphone access is not supported in this browser. Please use the text input."
          );
        }

        // Request clean microphone stream
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        streamRef.current = stream;

        // Initialize AudioContext & Analyser for real-time waveform
        const audioCtx = new (window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();

        if (audioCtx.state === "suspended") {
          await audioCtx.resume();
        }
        audioContextRef.current = audioCtx;

        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.25;
        source.connect(analyser);
        setAnalyserNode(analyser);

        // Determine best supported recording format
        const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : MediaRecorder.isTypeSupported("audio/mp4")
          ? "audio/mp4"
          : "";

        const options = mimeType ? { mimeType } : undefined;
        const recorder = new MediaRecorder(stream, options);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        recorder.start(100); // 100ms time slice
        setIsRecording(true);

        // Continuous volume & VAD monitor loop via AnalyserNode
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const SILENCE_THRESHOLD_MS = 1800; // 1.8s pause after speech
        const MIN_RECORDING_MS = 1200; // Minimum 1.2 seconds of audio before auto-stopping
        const SPEECH_ENERGY_THRESHOLD = 15; // Volume threshold

        const checkAudioLoop = () => {
          if (isStoppingRef.current) return;

          analyser.getByteFrequencyData(dataArray);

          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const avg = sum / bufferLength;
          const normalizedLevel = Math.min(1, avg / 70);
          setAudioLevel(normalizedLevel);

          const elapsedMs = Date.now() - startTimeRef.current;

          if (avg >= SPEECH_ENERGY_THRESHOLD) {
            speechDetectedRef.current = true;
            setHasSpoken(true);
            silenceStartRef.current = null;
          } else if (speechDetectedRef.current && elapsedMs >= MIN_RECORDING_MS) {
            const now = Date.now();
            if (silenceStartRef.current === null) {
              silenceStartRef.current = now;
            } else if (now - silenceStartRef.current >= SILENCE_THRESHOLD_MS) {
              // Silence detected after user spoke full question -> auto-stop!
              silenceStartRef.current = null;
              const cb = autoStopCallbackRef.current;
              autoStopCallbackRef.current = null; // clear immediately to prevent double-fire
              stopRecordingInternal().then((blob) => {
                if (blob && cb) {
                  cb(blob);
                }
              }).catch(() => {});
              return;
            }
          }

          animationFrameRef.current = requestAnimationFrame(checkAudioLoop);
        };

        animationFrameRef.current = requestAnimationFrame(checkAudioLoop);
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : "Failed to access microphone. Please allow microphone permissions in browser.";
        setError(msg);
        setIsRecording(false);
      }
    },
    [stopRecordingInternal]
  );

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    autoStopCallbackRef.current = null; // prevent auto-stop callback from also firing
    return stopRecordingInternal();
  }, [stopRecordingInternal]);

  const resetRecording = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    setIsRecording(false);
    setAudioBlob(null);
    setError(null);
    setAudioLevel(0);
    setHasSpoken(false);
    audioChunksRef.current = [];
    speechDetectedRef.current = false;
    silenceStartRef.current = null;
    isStoppingRef.current = false;

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAnalyserNode(null);
  }, []);

  return {
    isRecording,
    audioBlob,
    error,
    analyserNode,
    audioLevel,
    hasSpoken,
    startRecording,
    stopRecording,
    resetRecording,
  };
}
