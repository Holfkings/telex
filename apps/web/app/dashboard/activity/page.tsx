"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "motion/react";
import SpotlightCard from "@/components/ui/SpotlightCard";
import CyberGridBackground from "@/components/ui/CyberGridBackground";
import type { ActivityItem } from "@/lib/api";

export default function ActivityPage() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadActivity() {
      try {
        const { getActivity } = await import("@/lib/api");
        const data = await getActivity();
        if (isMounted && data?.activities) {
          setActivities(data.activities);
        }
      } catch {
        // Keep current state
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadActivity();
    const timer = setInterval(loadActivity, 10000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="flex flex-col gap-6 relative z-10 max-w-7xl mx-auto w-full">
      <CyberGridBackground />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <Link href="/dashboard" className="font-mono text-[10px] text-[#71717A] hover:text-white uppercase transition-colors">
              Fleet Overview
            </Link>
            <span className="text-[#3F3F46]">/</span>
            <span className="font-mono text-[10px] text-white">Event Log</span>
          </div>
          <h1 className="font-mono font-bold text-xl sm:text-2xl text-white tracking-tight">
            Activity Feed
          </h1>
          <p className="font-sans text-xs text-[#71717A]">
            Reverse-chronological log of breaking changes detected, synthesized patches, and pull requests opened.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/10 self-start sm:self-center">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-white shadow-[0_0_6px_#FFFFFF]" />
          </span>
          <span className="font-mono text-[11px] text-white font-medium">
            Live Stream Active
          </span>
        </div>
      </div>

      {/* State 1: Loading */}
      {isLoading ? (
        <div className="flex flex-col gap-3 animate-pulse">
          <div className="h-20 rounded-xl border border-white/10 bg-black/40" />
          <div className="h-20 rounded-xl border border-white/10 bg-black/40" />
          <div className="h-20 rounded-xl border border-white/10 bg-black/40" />
          <div className="h-20 rounded-xl border border-white/10 bg-black/40" />
        </div>
      ) : activities.length === 0 ? (
        /* State 2: Empty State */
        <SpotlightCard
          spotlightColor="rgba(255, 255, 255, 0.08)"
          className="p-8 sm:p-12 bg-black/70 backdrop-blur-xl border border-white/15 rounded-2xl flex flex-col items-center text-center gap-5 shadow-2xl"
          enableTilt={false}
        >
          <div className="w-14 h-14 rounded-xl bg-white/5 border border-white/15 flex items-center justify-center text-white">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <div className="flex flex-col gap-1.5 max-w-md">
            <h2 className="font-mono font-bold text-lg text-white">
              No activity recorded yet
            </h2>
            <p className="font-sans text-xs text-[#A1A1AA] leading-relaxed">
              Autonomous self-healing events will stream here in real time as breaking changes are detected, patches are generated, and pull requests are opened.
            </p>
          </div>

          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-black font-mono font-semibold text-xs hover:bg-white/90 transition-all shadow-md"
          >
            <span>← Back to Fleet Overview</span>
          </Link>
        </SpotlightCard>
      ) : (
        /* State 3: Populated Feed */
        <div className="flex flex-col gap-2.5">
          <AnimatePresence mode="popLayout">
            {activities.map((item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
              >
                <div className="p-4 rounded-xl border border-white/[0.08] bg-black/60 backdrop-blur-xl hover:border-white/20 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start sm:items-center gap-3 min-w-0">
                    {/* Type icon badge */}
                    <div className="w-8 h-8 rounded-lg bg-white/10 border border-white/15 flex items-center justify-center font-mono text-[10px] font-bold text-white flex-shrink-0 mt-0.5 sm:mt-0">
                      {item.type === "pull_request" ? "PR" : item.type === "patch" ? "FIX" : "EV"}
                    </div>

                    <div className="flex flex-col min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-bold text-white truncate">
                          {item.title}
                        </span>
                        <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-white/5 text-[#A1A1AA] border border-white/10">
                          {item.repo_name}
                        </span>
                        {item.merged && (
                          <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-white text-black font-bold">
                            MERGED
                          </span>
                        )}
                        {item.verification_mode && (
                          <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-white/10 text-white border border-white/15">
                            {item.verification_mode === "full" ? "Sandbox Verified" : "Structural AST"}
                          </span>
                        )}
                      </div>

                      <span className="font-sans text-xs text-[#71717A] truncate mt-0.5">
                        {item.description}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end sm:self-auto font-mono text-xs text-[#71717A] flex-shrink-0">
                    {item.timestamp && (
                      <span className="text-[11px] text-[#A1A1AA]">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    )}

                    {item.url && (
                      <Link
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2.5 py-1 rounded border border-white/15 text-white hover:bg-white hover:text-black transition-all flex items-center gap-1 text-xs"
                      >
                        <span>View</span>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </Link>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
