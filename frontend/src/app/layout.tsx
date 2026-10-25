import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Amar Khobor (আমার খবর) — Multilingual Family Audio Briefing",
  description: "AI-powered morning audio digest and Dual-STT bake-off for WhatsApp voice notes (Bengali, Hindi, English, Benglish, Hinglish)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-orange-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
