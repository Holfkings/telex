import { CyberSkeletonMetric, CyberSkeletonRepo } from "@/components/ui/CyberSkeleton";

export default function DashboardLoading() {
  return (
    <div
      className="flex flex-col gap-6 w-full max-w-7xl mx-auto animate-fade-in"
      role="status"
      aria-label="Loading dashboard"
    >
      {/* Top Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-2">
          <div className="w-48 h-8 rounded-lg bg-white/[0.08] animate-shimmer" />
          <div className="w-80 h-3 rounded bg-white/[0.04] animate-shimmer" />
        </div>
        <div className="flex items-center gap-3">
          <div className="w-32 h-9 rounded-lg bg-white/[0.08] animate-shimmer" />
        </div>
      </div>

      {/* 4-column Metric Strip */}
      <CyberSkeletonMetric />

      {/* Repositories List Skeleton */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="w-32 h-4 rounded bg-white/[0.06] animate-shimmer" />
          <div className="w-20 h-4 rounded bg-white/[0.04] animate-shimmer" />
        </div>
        <CyberSkeletonRepo />
        <CyberSkeletonRepo />
        <CyberSkeletonRepo />
      </div>
    </div>
  );
}
