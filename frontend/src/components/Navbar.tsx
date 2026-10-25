"use client";

import React from "react";
import { Mic, Radio, Award, History, Settings as SettingsIcon } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  sttProvider: string;
  ttsEngine: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  sttProvider,
  ttsEngine,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-orange-100 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("digest")}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-orange-500/20">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
              আমার খবর <span className="text-orange-600 text-sm font-semibold tracking-normal">(Amar Khobor)</span>
            </h1>
            <p className="text-xs text-gray-500">Multilingual Family Morning Audio Briefing</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center space-x-1">
          <button
            onClick={() => setActiveTab("digest")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              activeTab === "digest"
                ? "bg-orange-50 text-orange-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            Morning Digest
          </button>
          <button
            onClick={() => setActiveTab("upload")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              activeTab === "upload"
                ? "bg-orange-50 text-orange-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            Ingest & Upload
          </button>
          <button
            onClick={() => setActiveTab("compare")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              activeTab === "compare"
                ? "bg-orange-50 text-orange-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            Compare STT
          </button>
          <button
            onClick={() => setActiveTab("leaderboard")}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              activeTab === "leaderboard"
                ? "bg-orange-50 text-orange-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            Bake-Off Leaderboard
          </button>
        </nav>

        <div className="flex items-center space-x-2">
          <div className="hidden sm:flex items-center text-xs bg-orange-50 text-orange-800 border border-orange-200 px-2.5 py-1 rounded-full font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 mr-1.5 animate-ping" />
            STT: {sttProvider.toUpperCase()} | TTS: {ttsEngine}
          </div>
          <button
            onClick={() => setActiveTab("settings")}
            className="p-2 rounded-lg text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition"
            title="Settings & Provider Toggle"
          >
            <SettingsIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
};
