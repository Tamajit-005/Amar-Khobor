"use client";

import React from "react";
import { Radio } from "lucide-react";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-orange-100 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-2.5 sm:py-0 sm:h-16 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-4">
        {/* Brand row */}
        <div className="flex items-center justify-between w-full sm:w-auto">
          <div
            className="flex items-center space-x-2.5 sm:space-x-3 cursor-pointer min-w-0"
            onClick={() => setActiveTab("digest")}
          >
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-orange-500/20 shrink-0">
              <Radio className="w-4 h-4 sm:w-5 sm:h-5 animate-pulse" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-xl font-bold text-gray-900 tracking-tight truncate flex items-center gap-1.5 sm:gap-2">
                Amar Khobor <span className="text-orange-600 text-xs sm:text-sm font-semibold tracking-normal shrink-0">(আমার খবর)</span>
              </h1>
              <p className="text-[11px] sm:text-xs text-gray-500 hidden sm:block truncate">
                Multilingual Family Morning Audio Briefing
              </p>
            </div>
          </div>

          {/* Mobile model status badge */}
          <div className="sm:hidden flex items-center text-[10px] bg-orange-50 text-orange-800 border border-orange-200 px-2.5 py-1 rounded-full font-medium shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-ping" />
            Sarvam &amp; ElevenLabs
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between sm:justify-end gap-2 w-full sm:w-auto">
          <nav className="grid grid-cols-2 sm:flex sm:items-center gap-1 w-full sm:w-auto bg-stone-100 sm:bg-transparent p-1 sm:p-0 rounded-xl sm:rounded-none">
            <button
              onClick={() => setActiveTab("digest")}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition text-center ${
                activeTab === "digest"
                  ? "bg-white sm:bg-orange-50 text-orange-600 shadow-sm sm:shadow-none font-semibold"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-50/50"
              }`}
            >
              Morning Digest
            </button>
            <button
              onClick={() => setActiveTab("upload")}
              className={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition text-center ${
                activeTab === "upload"
                  ? "bg-white sm:bg-orange-50 text-orange-600 shadow-sm sm:shadow-none font-semibold"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-50/50"
              }`}
            >
              Ingest &amp; Upload
            </button>
          </nav>

          {/* Desktop provider badge */}
          <div className="hidden sm:flex items-center text-xs bg-orange-50 text-orange-800 border border-orange-200 px-3 py-1.5 rounded-full font-medium shrink-0">
            <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-ping" />
            Sarvam Saaras &amp; ElevenLabs
          </div>
        </div>
      </div>
    </header>
  );
};
