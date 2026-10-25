"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileArchive,
  RotateCw,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Volume2,
  Radio,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { AudioPlayer } from "@/components/AudioPlayer";
import { ShowNotesCard, ShowNoteItem } from "@/components/ShowNotesCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState("digest");

  // Digest state - empty initially until a briefing is uploaded and processed
  const [digestId, setDigestId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [spokenScript, setSpokenScript] = useState<string>("");
  const [showNotes, setShowNotes] = useState<ShowNoteItem[]>([]);
  const [audioUrl, setAudioUrl] = useState<string>("");

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Poll digest status if processing
  useEffect(() => {
    if (!digestId || status !== "processing") return;

    const interval = setInterval(() => {
      fetch(`${API_BASE}/digests/${digestId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.status === "ready") {
            setStatus("ready");
            if (data.spoken_script) setSpokenScript(data.spoken_script);
            if (data.show_notes) setShowNotes(data.show_notes);
            setAudioUrl(`${API_BASE}/audio/${digestId}`);
            setActiveTab("digest");
            clearInterval(interval);
          } else if (data.status === "failed") {
            setStatus("failed");
            setUploadError(data.error || "Digest processing failed");
            clearInterval(interval);
          }
        })
        .catch((err) => console.error("Polling error:", err));
    }, 2000);

    return () => clearInterval(interval);
  }, [digestId, status]);

  // Shared async start: POST returns 202 Accepted, then we poll GET /digests/{id}.
  const startDigest = async (request: () => Promise<Response>) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await request();
      if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
      const data = await res.json();
      setDigestId(data.digest_id);
      setStatus("processing");
      setActiveTab("digest");
    } catch (e: any) {
      setUploadError(e.message || "Failed to start ingest");
    } finally {
      setIsUploading(false);
    }
  };

  // Handler for uploading a real WhatsApp export zip.
  const handleStartIngest = () => {
    if (!selectedFile) {
      setUploadError("Select a WhatsApp .zip export first.");
      return;
    }
    startDigest(() => {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("language_mode", "bn-IN");
      return fetch(`${API_BASE}/digests/run`, {
        method: "POST",
        body: formData,
      });
    });
  };

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        {/* Top Hero Banner */}
        <div className="mb-8 p-5 sm:p-6 rounded-2xl sm:rounded-3xl bg-gradient-to-r from-orange-600 via-amber-600 to-orange-700 text-white shadow-xl shadow-orange-900/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white/20 backdrop-blur border border-white/30 text-white mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              Overnight Intelligence for Indian Families
            </span>
            <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold tracking-tight">
              You slept. It listened. Here's what you missed.
            </h1>
            <p className="mt-2 text-xs sm:text-sm text-orange-100 leading-relaxed">
              Amar Khobor turns chaotic overnight voice notes from multilingual family WhatsApp groups
              (Bengali, Hindi, English, Benglish, Hinglish) into a warm, 2-minute morning audio briefing
              with verifiable citation receipts.
            </p>
          </div>

          <div className="flex flex-col gap-2 w-full md:w-auto">
            <button
              onClick={() => setActiveTab("upload")}
              className="px-6 py-3.5 rounded-xl bg-white hover:bg-orange-50 text-orange-700 font-bold text-sm shadow-lg active:scale-95 transition flex items-center justify-center gap-2"
            >
              <UploadCloud className="w-4 h-4" /> Upload WhatsApp Export
            </button>
          </div>
        </div>

        {/* Status Notification if Processing */}
        {status === "processing" && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm animate-pulse">
            <div className="flex items-center space-x-3">
              <RotateCw className="w-5 h-5 text-amber-600 animate-spin shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-amber-900">
                  Synthesizing Morning Briefing
                </h4>
                <p className="text-xs text-amber-700">
                  Normalizing audio to 16kHz mono • Running VAD pre-filter • Transcribing with Sarvam Saaras • Polling status
                </p>
              </div>
            </div>
            <span className="text-xs font-mono bg-white px-2.5 py-1 rounded-md text-amber-800 border border-amber-200 shrink-0 self-start sm:self-auto">
              ID: {digestId}
            </span>
          </div>
        )}

        {/* TAB 1: MORNING DIGEST VIEW */}
        {activeTab === "digest" && (
          spokenScript && audioUrl ? (
            <div className="space-y-6">
              {/* Audio Player Component */}
              <AudioPlayer audioUrl={audioUrl} />

              {/* Decoupled Spoken Script Card */}
              <div className="bg-white rounded-2xl border border-gray-200 p-4 sm:p-6 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 sm:gap-2 mb-4">
                  <div className="flex items-center space-x-2">
                    <Volume2 className="w-5 h-5 text-orange-600 shrink-0" />
                    <h3 className="text-base font-bold text-gray-900">
                      Spoken Script (Familial Voice)
                    </h3>
                  </div>
                  <span className="text-xs text-gray-400 font-medium">
                    Strictly No Timestamps or In-Line Brackets
                  </span>
                </div>
                <div className="p-4 rounded-xl bg-orange-50/40 border border-orange-100 text-gray-800 text-sm leading-relaxed font-serif italic">
                  "{spokenScript}"
                </div>
              </div>

              {/* Interactive Receipts Panel (Show Notes) */}
              <div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                      Receipts & Citation Cards (Show Notes)
                    </h3>
                    <p className="text-xs text-gray-500">
                      Verifiable claim cards mapped to speakers and chat timestamps
                    </p>
                  </div>
                  <span className="text-xs font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-full self-start sm:self-auto shrink-0">
                    {showNotes.length} Verified Claims
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {showNotes.map((item, idx) => (
                    <ShowNotesCard key={idx} item={item} index={idx} />
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-6 sm:p-12 text-center shadow-sm">
              <div className="w-16 h-16 bg-orange-50 text-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Radio className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-1">No Morning Briefing Generated Yet</h3>
              <p className="text-sm text-gray-500 max-w-md mx-auto mb-6">
                Upload your family WhatsApp group export (.zip) to generate your personalized morning audio briefing and citation receipts.
              </p>
              <button
                onClick={() => setActiveTab("upload")}
                className="px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-semibold text-sm shadow-md transition inline-flex items-center gap-2"
              >
                <UploadCloud className="w-4 h-4" /> Go to Ingest &amp; Upload
              </button>
            </div>
          )
        )}

        {/* TAB 2: UPLOAD & INGEST */}
        {activeTab === "upload" && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-gray-200 p-5 sm:p-8 shadow-sm">
            <div className="text-center mb-6">
              <div className="w-14 h-14 bg-orange-100 text-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <FileArchive className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Ingest WhatsApp Export</h2>
              <p className="text-xs text-gray-500 mt-1">
                Drop your exported family WhatsApp group zip file containing <code className="bg-gray-100 px-1 py-0.5 rounded">_chat.txt</code> and voice notes
              </p>
            </div>

            <div className="border-2 border-dashed border-gray-300 hover:border-orange-500 rounded-2xl p-8 text-center cursor-pointer transition bg-gray-50/50">
              <input
                type="file"
                accept=".zip"
                id="file-upload"
                className="hidden"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <UploadCloud className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                <span className="text-sm font-semibold text-gray-700 block">
                  {selectedFile ? selectedFile.name : "Click to select WhatsApp export .zip"}
                </span>
                <span className="text-xs text-gray-400 mt-1 block">
                  Supports Android & iOS chat logs across all regional date formats
                </span>
              </label>
            </div>

            {uploadError && (
              <div className="mt-4 p-3 rounded-lg bg-red-50 text-red-700 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <div className="mt-6 flex flex-col gap-3">
              <button
                disabled={isUploading}
                onClick={handleStartIngest}
                className="w-full py-3 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-bold text-sm shadow-md transition disabled:opacity-50"
              >
                {isUploading ? "Starting Async Pipeline..." : "Process WhatsApp Archive"}
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-gray-200 bg-white py-6">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-500">
          <div>
            <span className="font-bold text-gray-700">Amar Khobor (আমার খবর)</span> — Multilingual Family Audio Digest
          </div>
          <div className="flex items-center space-x-3">
            <span>Powered by <strong className="text-gray-700">ElevenLabs</strong> & <strong className="text-gray-700">Sarvam AI</strong></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
