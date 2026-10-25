"use client";

import React, { useRef, useState, useEffect } from "react";
import { Play, Pause, Volume2, RotateCcw, FastForward, Download } from "lucide-react";

interface AudioPlayerProps {
  audioUrl: string;
  ttsEngine: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl, ttsEngine }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration || 0);
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("loadedmetadata", updateDuration);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("loadedmetadata", updateDuration);
      audio.removeEventListener("ended", onEnded);
    };
  }, [audioUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const cyclePlaybackRate = () => {
    const rates = [1, 1.25, 1.5];
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const nextRate = rates[nextIdx];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="bg-gradient-to-r from-orange-50 via-white to-amber-50 border border-orange-200 rounded-2xl p-6 shadow-sm">
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <span className="text-xs uppercase font-bold tracking-wider text-orange-600 bg-orange-100 px-2.5 py-0.5 rounded-full">
            Morning Voice Briefing
          </span>
          <h3 className="text-lg font-bold text-gray-900 mt-1">আজকের পারিবারিক খবর (Today's Digest)</h3>
        </div>

        {/* ElevenLabs Attribution Requirement */}
        <div className="flex items-center space-x-2 text-xs font-semibold text-gray-500 bg-white border border-gray-200 px-3 py-1.5 rounded-full shadow-sm">
          <span>Engine: <span className="text-gray-800">{ttsEngine}</span></span>
          <span className="text-gray-300">|</span>
          <span className="text-orange-700 font-bold">Powered by ElevenLabs</span>
        </div>
      </div>

      {/* Progress slider */}
      <div className="mb-4">
        <input
          type="range"
          min="0"
          max={duration || 100}
          value={currentTime}
          onChange={handleSeek}
          className="w-full h-2 bg-orange-200 rounded-lg appearance-none cursor-pointer accent-orange-600"
        />
        <div className="flex justify-between text-xs font-medium text-gray-500 mt-1">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Player Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={togglePlay}
            className="w-12 h-12 rounded-full bg-orange-600 hover:bg-orange-700 active:scale-95 text-white flex items-center justify-center shadow-lg shadow-orange-600/30 transition"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          <button
            onClick={() => {
              if (audioRef.current) {
                audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
              }
            }}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-full transition"
            title="Rewind 10 seconds"
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          <button
            onClick={cyclePlaybackRate}
            className="px-2.5 py-1 text-xs font-bold bg-white border border-gray-200 text-gray-700 rounded-md hover:bg-gray-50 shadow-sm"
          >
            {playbackRate}x
          </button>
        </div>

        <a
          href={audioUrl}
          download="amar_khobor_digest.mp3"
          className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 hover:text-orange-600 bg-white border border-gray-200 px-3 py-1.5 rounded-lg shadow-sm transition"
        >
          <Download className="w-4 h-4" />
          Download Audio
        </a>
      </div>
    </div>
  );
};
