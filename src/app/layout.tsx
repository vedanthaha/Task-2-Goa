import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "HH Goa 2026 — Voice-Enabled Multilingual RAG",
  description:
    "Voice-Enabled Retrieval-Augmented Generation with Sarvam Speech-to-Text, MSMARCO-XI Hybrid Retrieval, and Sub-200ms Latency SLA.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans bg-slate-950 text-slate-100 antialiased min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
