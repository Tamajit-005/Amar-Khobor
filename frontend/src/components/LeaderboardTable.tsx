"use client";

import React from "react";
import { Award, Zap, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

interface LeaderboardProps {
  data?: any;
}

export const LeaderboardTable: React.FC<LeaderboardProps> = ({ data }) => {
  const saarasData = data?.saaras || {
    avg_wer_monolingual: 0.1481,
    avg_llm_judge_codemixed: 4.8,
    avg_latency_ms: 103,
    noise_hallucinations: 0,
  };

  const whisperData = data?.whisper || {
    avg_wer_monolingual: 0.1481,
    avg_llm_judge_codemixed: 4.8,
    avg_latency_ms: 82,
    noise_hallucinations: 0,
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Award className="w-6 h-6 text-amber-500" />
            Dual-STT Bake-Off Leaderboard
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Empirical benchmark comparing Sarvam Saaras vs Groq Whisper-large-v3 across 5 language modes
          </p>
        </div>
        <span className="inline-flex items-center text-xs font-semibold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Fixture Data — Live Run Pending
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/80 text-xs font-bold text-gray-600 uppercase tracking-wider">
              <th className="py-3 px-4 rounded-l-lg">STT Model</th>
              <th className="py-3 px-4">Monolingual WER (bn, hi, en) ↓</th>
              <th className="py-3 px-4">Code-Mixed LLM-Judge ↑</th>
              <th className="py-3 px-4">Avg Latency ↓</th>
              <th className="py-3 px-4 rounded-r-lg">Noise Hallucinations</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {/* Sarvam Saaras */}
            <tr className="hover:bg-orange-50/40 transition">
              <td className="py-4 px-4 font-bold text-gray-900">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-orange-600" />
                  <div>
                    <span>Sarvam Saaras</span>
                    <span className="block text-[11px] font-normal text-gray-500">model: saaras:v4 (Indic Specialist)</span>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4">
                <span className="font-mono font-bold text-gray-900">
                  {(saarasData.avg_wer_monolingual * 100).toFixed(2)}%
                </span>
                <span className="block text-[10px] text-gray-400">Unicode NFC + ZWJ stripped</span>
              </td>
              <td className="py-4 px-4">
                <span className="inline-flex items-center gap-1 font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                  <Sparkles className="w-3 h-3" />
                  {saarasData.avg_llm_judge_codemixed.toFixed(1)} / 5.0
                </span>
                <span className="block text-[10px] text-gray-400">Gemma Semantic Fidelity</span>
              </td>
              <td className="py-4 px-4 font-mono font-medium text-gray-700">
                <span className="flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  {saarasData.avg_latency_ms} ms
                </span>
              </td>
              <td className="py-4 px-4">
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                  {saarasData.noise_hallucinations} errors
                </span>
              </td>
            </tr>

            {/* Groq Whisper */}
            <tr className="hover:bg-orange-50/40 transition">
              <td className="py-4 px-4 font-bold text-gray-900">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-600" />
                  <div>
                    <span>Groq Whisper</span>
                    <span className="block text-[11px] font-normal text-gray-500">model: whisper-large-v3 (Open-source)</span>
                  </div>
                </div>
              </td>
              <td className="py-4 px-4">
                <span className="font-mono font-bold text-gray-900">
                  {(whisperData.avg_wer_monolingual * 100).toFixed(2)}%
                </span>
                <span className="block text-[10px] text-gray-400">Unicode NFC + ZWJ stripped</span>
              </td>
              <td className="py-4 px-4">
                <span className="inline-flex items-center gap-1 font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                  <Sparkles className="w-3 h-3" />
                  {whisperData.avg_llm_judge_codemixed.toFixed(1)} / 5.0
                </span>
                <span className="block text-[10px] text-gray-400">Gemma Semantic Fidelity</span>
              </td>
              <td className="py-4 px-4 font-mono font-medium text-gray-700">
                <span className="flex items-center gap-1">
                  <Zap className="w-3.5 h-3.5 text-amber-500" />
                  {whisperData.avg_latency_ms} ms
                </span>
              </td>
              <td className="py-4 px-4">
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                  {whisperData.noise_hallucinations} errors
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Methodological Annotation Box */}
      <div className="mt-5 p-4 rounded-xl bg-orange-50/60 border border-orange-100 text-xs text-gray-700">
        <h4 className="font-bold text-orange-900 mb-1 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-orange-600" />
          Methodological Invariant: Script-Aware Split
        </h4>
        <p className="leading-relaxed">
          <strong>Pure Monolingual Speech (Bengali, Hindi, English):</strong> Evaluated via normalized Levenshtein Word Error Rate after NFC canonical composition, zero-width joiner (<code className="bg-white px-1 py-0.5 rounded">‌, ‍</code>) stripping, and case-folding.
          <br />
          <strong>Code-Mixed Speech (Benglish, Hinglish):</strong> Evaluated <em>exclusively via LLM-Judge</em> (1–5 semantic fidelity score) because Whisper outputs native Indic script whereas Saaras produces Romanized text. Computing character or word WER across scripts is methodologically invalid.
        </p>
      </div>
    </div>
  );
};
