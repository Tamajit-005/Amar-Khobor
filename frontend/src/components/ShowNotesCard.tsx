"use client";

import React from "react";
import { HeartPulse, Plane, Wallet, Calendar, AlertCircle, Clock, User } from "lucide-react";

export interface ShowNoteItem {
  claim: string;
  sender: string;
  timestamp: string;
  category: "health" | "money" | "travel" | "event" | "other";
  urgent?: boolean;
}

const CATEGORY_STYLES = {
  health: {
    bg: "bg-rose-50 text-rose-700 border-rose-200",
    icon: HeartPulse,
    label: "Health / Medical",
  },
  travel: {
    bg: "bg-sky-50 text-sky-700 border-sky-200",
    icon: Plane,
    label: "Travel / Transit",
  },
  money: {
    bg: "bg-emerald-50 text-emerald-700 border-emerald-200",
    icon: Wallet,
    label: "Money / Bank",
  },
  event: {
    bg: "bg-purple-50 text-purple-700 border-purple-200",
    icon: Calendar,
    label: "Event / Meal",
  },
  other: {
    bg: "bg-amber-50 text-amber-700 border-amber-200",
    icon: AlertCircle,
    label: "General Update",
  },
};

export const ShowNotesCard: React.FC<{ item: ShowNoteItem; index: number }> = ({ item, index }) => {
  const cat = CATEGORY_STYLES[item.category] || CATEGORY_STYLES.other;
  const IconComponent = cat.icon;

  return (
    <div
      className={`p-4 rounded-xl border bg-white shadow-sm hover:shadow-md transition duration-200 ${
        item.urgent ? "border-red-300 ring-1 ring-red-200" : "border-gray-200"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
        <div className="flex flex-wrap items-center gap-1.5">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cat.bg}`}
          >
            <IconComponent className="w-3.5 h-3.5" />
            {cat.label}
          </span>
          {item.urgent && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-600 text-white animate-pulse">
              URGENT
            </span>
          )}
        </div>
        <span className="text-xs font-medium text-gray-400 flex items-center gap-1 shrink-0">
          <Clock className="w-3 h-3" />
          {item.timestamp}
        </span>
      </div>

      <p className="text-sm font-semibold text-gray-900 leading-snug mb-3">
        "{item.claim}"
      </p>

      <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <span className="flex items-center gap-1 font-medium text-gray-700">
          <User className="w-3.5 h-3.5 text-orange-600" />
          Speaker: {item.sender}
        </span>
        <span className="text-[11px] text-gray-400 font-mono">Receipt #{index + 1}</span>
      </div>
    </div>
  );
};
