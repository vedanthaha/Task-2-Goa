"use client";

import { useEffect, useRef } from "react";

interface AudioWaveformProps {
  analyserNode: AnalyserNode | null;
  isListening: boolean;
  audioLevel?: number;
}

export function AudioWaveform({
  analyserNode,
  isListening,
  audioLevel = 0,
}: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let phase = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      if (isListening && analyserNode) {
        // Read frequency data for real dynamic equalizer bars
        const bufferLength = analyserNode.frequencyBinCount;
        const freqArray = new Uint8Array(bufferLength);
        analyserNode.getByteFrequencyData(freqArray);

        const barCount = 32;
        const barWidth = width / barCount - 2;
        const centerY = height / 2;

        ctx.shadowBlur = 12;
        ctx.shadowColor = audioLevel > 0.05 ? "#10b981" : "#06b6d4";

        for (let i = 0; i < barCount; i++) {
          // Average frequency bins for this bar
          const binIndex = Math.floor((i / barCount) * (bufferLength / 2));
          const val = freqArray[binIndex] / 255.0;
          const barHeight = Math.max(4, val * height * 0.9 + audioLevel * 15);

          const x = i * (barWidth + 2);
          const y = centerY - barHeight / 2;

          // Gradient for equalizer bar
          const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
          grad.addColorStop(0, "#34d399"); // Emerald bright
          grad.addColorStop(1, "#06b6d4"); // Cyan

          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.roundRect(x, y, barWidth, barHeight, 3);
          ctx.fill();
        }
      } else if (isListening) {
        // Fallback animated wave
        phase += 0.1;
        ctx.lineWidth = 3;
        ctx.strokeStyle = "#10b981";
        ctx.shadowColor = "#10b981";
        ctx.shadowBlur = 10;

        ctx.beginPath();
        for (let x = 0; x < width; x += 4) {
          const y =
            height / 2 +
            Math.sin(x * 0.05 + phase) * (12 + audioLevel * 20);
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      } else {
        // Resting subtle wave
        phase += 0.03;
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "rgba(71, 85, 105, 0.4)";
        ctx.shadowBlur = 0;

        ctx.beginPath();
        for (let x = 0; x < width; x += 4) {
          const y = height / 2 + Math.sin(x * 0.03 + phase) * 3;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [analyserNode, isListening, audioLevel]);

  return (
    <div className="w-full flex justify-center py-2">
      <canvas
        ref={canvasRef}
        width={380}
        height={56}
        className="w-full max-w-sm rounded-lg"
      />
    </div>
  );
}
