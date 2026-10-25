"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileArchive,
  Play,
  RotateCw,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Volume2,
  Clock,
  Layers,
  Settings as SettingsIcon,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { AudioPlayer } from "@/components/AudioPlayer";
import { ShowNotesCard, ShowNoteItem } from "@/components/ShowNotesCard";
import { LeaderboardTable } from "@/components/LeaderboardTable";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState("digest");
  const [sttProvider, setSttProvider] = useState("saaras");
  const [ttsEngine, setTtsEngine] = useState("edge-tts");
  const [mockMode, setMockMode] = useState(true);
  const [sarvamModel, setSarvamModel] = useState("saaras:v4");
  const [whisperModel, setWhisperModel] = useState("whisper-large-v3");
  const [gemmaModel, setGemmaModel] = useState("gemma-4");
  const [elevenlabsModel, setElevenlabsModel] = useState("eleven_v4_turbo");

  // Digest state
  const [digestId, setDigestId] = useState<string | null>("sample_demo");
  const [status, setStatus] = useState<string>("ready");
  const [spokenScript, setSpokenScript] = useState<string>(
    "Good morning family! Here is your quick morning briefing. Dadu reminded everyone that his blood pressure medicine needs to be brought home today. Also, Rahul will be arriving at Kolkata airport this evening, so please make sure a cab is arranged. Wishing everyone a calm and productive day ahead!"
  );
  const [showNotes, setShowNotes] = useState<ShowNoteItem[]>([
    {
      claim: "Dadu requested blood pressure medicines to be picked up by noon",
      sender: "Dadu",
      timestamp: "Yesterday 8:14 PM",
      category: "health",
      urgent: true,
    },
    {
      claim: "Rahul is arriving at Kolkata Airport (T2) and needs a cab",
      sender: "Rahul",
      timestamp: "Yesterday 8:30 PM",
      category: "travel",
      urgent: true,
    },
  ]);
  const [audioUrl, setAudioUrl] = useState<string>(`${API_BASE}/audio/sample_demo`);
  const [leaderboardData, setLeaderboardData] = useState<any>(null);

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch initial settings and leaderboard
  useEffect(() => {
    fetch(`${API_BASE}/settings`)
      .then((res) => res.json())
      .then((data) => {
        if (data.stt_provider) setSttProvider(data.stt_provider);
        if (data.tts_engine) setTtsEngine(data.tts_engine);
        if (data.sarvam_model) setSarvamModel(data.sarvam_model);
        if (data.whisper_model) setWhisperModel(data.whisper_model);
        if (data.gemma_model) setGemmaModel(data.gemma_model);
        if (data.elevenlabs_model) setElevenlabsModel(data.elevenlabs_model);
        if (data.mock_mode !== undefined) setMockMode(data.mock_mode);
      })
      .catch(() => console.log("Backend offline; using local mock mode defaults."));

    fetch(`${API_BASE}/leaderboard`)
      .then((res) => res.json())
      .then((data) => setLeaderboardData(data))
      .catch(() => {});
  }, []);

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

  // Server-side fixture run: uses data/nightly/ or test_data/sample_chat.zip.
  const handleRunDemo = () =>
    startDigest(() => {
      const formData = new FormData();
      formData.append("language_mode", "bn-IN");
      return fetch(`${API_BASE}/digests/run-nightly`, {
        method: "POST",
        body: formData,
      });
    });

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

  // Handler for settings update
  const handleToggleSettings = async (newProvider: string, newTTS: string) => {
    setSttProvider(newProvider);
    setTtsEngine(newTTS);
    try {
      await fetch(`${API_BASE}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stt_provider: newProvider, tts_engine: newTTS }),
      });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        sttProvider={sttProvider}
        ttsEngine={ttsEngine}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        {/* Top Hero Banner */}
        <div className="mb-8 p-6 rounded-3xl bg-gradient-to-r from-orange-600 via-amber-600 to-orange-700 text-white shadow-xl shadow-orange-900/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white/20 backdrop-blur border border-white/30 text-white mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              Overnight Intelligence for Indian Families
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              You slept. It listened. Here's what you missed.
            </h1>
            <p className="mt-2 text-sm text-orange-100 leading-relaxed">
              Amar Khobor turns chaotic overnight voice notes from multilingual family WhatsApp groups
              (Bengali, Hindi, English, Benglish, Hinglish) into a warm, 2-minute morning audio briefing
              with verifiable citation receipts.
            </p>
          </div>

          <div className="flex flex-col gap-2 w-full md:w-auto">
            <button
              onClick={handleRunDemo}
              className="px-5 py-3 rounded-xl bg-white text-orange-700 font-bold text-sm shadow-lg hover:bg-orange-50 active:scale-95 transition flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4 fill-current" /> Run Demo Briefing
            </button>
            <button
              onClick={() => setActiveTab("upload")}
              className="px-5 py-2.5 rounded-xl bg-orange-800/40 hover:bg-orange-800/60 text-white font-semibold text-xs border border-white/20 transition flex items-center justify-center gap-2"
            >
              <UploadCloud className="w-4 h-4" /> Upload Custom Export
            </button>
          </div>
        </div>

        {/* Status Notification if Processing */}
        {status === "processing" && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-between shadow-sm animate-pulse">
            <div className="flex items-center space-x-3">
              <RotateCw className="w-5 h-5 text-amber-600 animate-spin" />
              <div>
                <h4 className="text-sm font-bold text-amber-900">
                  Synthesizing Morning Briefing (Async HTTP 202)...
                </h4>
                <p className="text-xs text-amber-700">
                  Normalizing audio to 16kHz mono • Running VAD pre-filter • Transcribing with {sttProvider.toUpperCase()} • Polling status
                </p>
              </div>
            </div>
            <span className="text-xs font-mono bg-white px-2.5 py-1 rounded-md text-amber-800 border border-amber-200">
              ID: {digestId}
            </span>
          </div>
        )}

        {/* TAB 1: MORNING DIGEST VIEW */}
        {activeTab === "digest" && (
          <div className="space-y-6">
            {/* Audio Player Component */}
            <AudioPlayer audioUrl={audioUrl} ttsEngine={ttsEngine} />

            {/* Decoupled Spoken Script Card */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Volume2 className="w-5 h-5 text-orange-600" />
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
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                    Receipts & Citation Cards (Show Notes)
                  </h3>
                  <p className="text-xs text-gray-500">
                    Verifiable claim cards mapped to speakers and chat timestamps
                  </p>
                </div>
                <span className="text-xs font-bold text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
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
        )}

        {/* TAB 2: UPLOAD & INGEST */}
        {activeTab === "upload" && (
          <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
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

              <button
                onClick={handleRunDemo}
                className="w-full py-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold text-xs transition"
              >
                Use Preloaded Test Fixture (sample_chat.zip)
              </button>
            </div>
          </div>
        )}

        {/* TAB 3: COMPARE STT */}
        {activeTab === "compare" && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900 mb-1 flex items-center gap-2">
                <Layers className="w-5 h-5 text-orange-600" />
                Side-by-Side Dual-STT Comparison
              </h2>
              <p className="text-xs text-gray-500 mb-6">
                Direct transcription comparison between Sarvam Saaras and Groq Whisper-large-v3 on multilingual Indian family speech.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Saaras column */}
                <div className="p-5 rounded-xl border border-orange-200 bg-orange-50/30">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-bold text-orange-900 text-sm">Sarvam Saaras (saaras:v4)</span>
                    <span className="text-[11px] font-semibold bg-orange-200 text-orange-800 px-2 py-0.5 rounded">
                      Indic Specialist
                    </span>
                  </div>
                  <div className="space-y-3 text-xs">
                    <div className="p-3 bg-white rounded-lg border border-orange-100">
                      <span className="font-bold text-gray-500 block mb-1">Bengali Pure (bn-IN):</span>
                      <p className="text-gray-900">"দাদু বললেন ওনার প্রেসারের ওষুধটা যেন আজকে নিয়ে আসা হয়।"</p>
                    </div>
                    <div className="p-3 bg-white rounded-lg border border-orange-100">
                      <span className="font-bold text-gray-500 block mb-1">Benglish Code-Mixed:</span>
                      <p className="text-gray-900 font-mono">"Kalke bikele flight ache, ar medicine ta collect kore niyo."</p>
                    </div>
                  </div>
                </div>

                {/* Whisper column */}
                <div className="p-5 rounded-xl border border-sky-200 bg-sky-50/30">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-bold text-sky-900 text-sm">Groq Whisper (whisper-large-v3)</span>
                    <span className="text-[11px] font-semibold bg-sky-200 text-sky-800 px-2 py-0.5 rounded">
                      Open-Source Baseline
                    </span>
                  </div>
                  <div className="space-y-3 text-xs">
                    <div className="p-3 bg-white rounded-lg border border-sky-100">
                      <span className="font-bold text-gray-500 block mb-1">Bengali Pure (bn-IN):</span>
                      <p className="text-gray-900">"দাদু বললেন প্রেসারের ওষুধ আজকে নিয়ে আসতে।"</p>
                    </div>
                    <div className="p-3 bg-white rounded-lg border border-sky-100">
                      <span className="font-bold text-gray-500 block mb-1">Benglish Code-Mixed (Native Script):</span>
                      <p className="text-gray-900 font-mono">"কালকে বিকেলে ফ্লাইট আছে আর মেডিসিনটা কালেক্ট করে নিও।"</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: BAKE-OFF LEADERBOARD */}
        {activeTab === "leaderboard" && (
          <div className="space-y-6">
            <LeaderboardTable data={leaderboardData} />
          </div>
        )}

        {/* TAB 5: SETTINGS */}
        {activeTab === "settings" && (
          <div className="max-w-xl mx-auto bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-orange-600" />
              Pipeline Configuration & Provider Toggles
            </h2>

            <div className="space-y-4 text-sm">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">STT Provider</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => handleToggleSettings("saaras", ttsEngine)}
                    className={`p-3 rounded-xl border font-bold text-center transition ${
                      sttProvider === "saaras"
                        ? "border-orange-500 bg-orange-50 text-orange-700"
                        : "border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Sarvam Saaras
                    <span className="block text-[11px] font-normal text-gray-500">{sarvamModel}</span>
                  </button>
                  <button
                    onClick={() => handleToggleSettings("whisper", ttsEngine)}
                    className={`p-3 rounded-xl border font-bold text-center transition ${
                      sttProvider === "whisper"
                        ? "border-orange-500 bg-orange-50 text-orange-700"
                        : "border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Groq Whisper
                    <span className="block text-[11px] font-normal text-gray-500">{whisperModel}</span>
                  </button>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">TTS Voice Tier</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => handleToggleSettings(sttProvider, "edge-tts")}
                    className={`p-3 rounded-xl border font-bold text-center transition ${
                      ttsEngine === "edge-tts"
                        ? "border-orange-500 bg-orange-50 text-orange-700"
                        : "border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Edge-TTS
                    <span className="block text-[11px] font-normal text-gray-500">Dev & Testing (Free)</span>
                  </button>
                  <button
                    onClick={() => handleToggleSettings(sttProvider, "elevenlabs")}
                    className={`p-3 rounded-xl border font-bold text-center transition ${
                      ttsEngine === "elevenlabs"
                        ? "border-orange-500 bg-orange-50 text-orange-700"
                        : "border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    ElevenLabs
                    <span className="block text-[11px] font-normal text-gray-500">Demo Showcase ({elevenlabsModel})</span>
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                <span>LLM Summarizer / Judge Model:</span>
                <span className="font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                  {gemmaModel}
                </span>
              </div>

              <div className="pt-2 flex items-center justify-between text-xs text-gray-500">
                <span>MOCK_MODE Status:</span>
                <span className="font-mono font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                  {mockMode ? "Enabled (Zero Credit Mode)" : "Live Network API Mode"}
                </span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-gray-200 bg-white py-6">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-500">
          <div>
            <span className="font-bold text-gray-700">আমার খবর (Amar Khobor)</span> — Multilingual Family Audio Digest & Bake-Off
          </div>
          <div className="flex items-center space-x-3">
            <span>Powered by <strong className="text-gray-700">ElevenLabs</strong> & <strong className="text-gray-700">Sarvam AI</strong></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
