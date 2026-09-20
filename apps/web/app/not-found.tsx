import Link from "next/link";
import CyberGridBackground from "@/components/ui/CyberGridBackground";
import SpotlightCard from "@/components/ui/SpotlightCard";

export default function NotFound() {
  return (
    <div className="flex min-h-screen bg-black text-[#F2F1ED] items-center justify-center p-6 relative overflow-hidden font-sans">
      <CyberGridBackground />
      <div className="animate-terminal-scan" />

      <SpotlightCard
        spotlightColor="rgba(255, 255, 255, 0.08)"
        className="relative z-10 max-w-md w-full p-8 rounded-2xl border border-white/10 bg-black/85 backdrop-blur-2xl shadow-2xl text-center flex flex-col items-center gap-6"
        enableTilt={false}
      >
        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/15 flex items-center justify-center text-white">
          <svg
            className="w-8 h-8 stroke-current"
            viewBox="0 0 24 24"
            fill="none"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 9l-6 6M9 9l6 6" />
          </svg>
        </div>

        <div className="flex flex-col items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#A1A1AA] px-3 py-1 rounded-full border border-white/10 bg-white/[0.04]">
            Telemetry Code 404 // Target Lost
          </span>
          <h1 className="font-mono text-2xl font-bold text-white tracking-tight">
            Sector Not Found
          </h1>
          <p className="font-sans text-xs text-[#8E8E93] leading-relaxed max-w-sm">
            The requested telemetry endpoint, repository, or command deck route does not exist in the active fleet registry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="px-5 py-2.5 rounded-lg bg-white text-black font-mono font-bold text-xs hover:bg-white/90 transition-all shadow-md active:scale-[0.98]"
          >
            Return to Fleet Overview
          </Link>
          <Link
            href="/"
            className="px-4 py-2.5 rounded-lg border border-white/20 bg-white/5 text-white font-mono text-xs hover:bg-white/10 transition-colors"
          >
            Main Console
          </Link>
        </div>
      </SpotlightCard>
    </div>
  );
}
