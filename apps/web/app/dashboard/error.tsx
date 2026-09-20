"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import SpotlightCard from "@/components/ui/SpotlightCard";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard caught route error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 text-center">
      <SpotlightCard
        spotlightColor="rgba(255, 255, 255, 0.08)"
        className="p-8 sm:p-12 bg-black/80 backdrop-blur-2xl border border-white/15 rounded-2xl flex flex-col items-center text-center gap-5 max-w-lg w-full shadow-2xl"
        enableTilt={false}
      >
        <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/15 flex items-center justify-center text-rose-400">
          <svg
            className="w-7 h-7 stroke-current"
            viewBox="0 0 24 24"
            fill="none"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <div className="flex flex-col gap-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#A1A1AA]">
            Telemetry Error // Exception Caught
          </span>
          <h2 className="font-mono font-bold text-xl text-white">
            Operator Console Interrupted
          </h2>
          <p className="font-sans text-xs text-[#A1A1AA] leading-relaxed">
            {error.message ||
              "An unexpected runtime error occurred while streaming repository telemetry."}
          </p>
          {error.digest && (
            <div className="mt-1 p-2 rounded bg-white/[0.03] border border-white/[0.08] font-mono text-[10px] text-[#71717A] break-all">
              DIAGNOSTIC HASH: {error.digest}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <button
            onClick={() => reset()}
            className="px-5 py-2.5 rounded-lg bg-white text-black font-mono font-bold text-xs hover:bg-white/90 transition-all shadow-md active:scale-[0.98] cursor-pointer"
          >
            Re-synchronize Session
          </button>
          <Link
            href="/dashboard"
            className="px-4 py-2.5 rounded-lg border border-white/20 bg-white/5 text-white font-mono text-xs hover:bg-white/10 transition-colors"
          >
            Fleet Overview
          </Link>
        </div>
      </SpotlightCard>
    </div>
  );
}
