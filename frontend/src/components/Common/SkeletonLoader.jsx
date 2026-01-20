/**
 * Skeleton Loader Components - Modern Glassmorphism Design
 * ✨ Animated loading placeholders for better UX
 */
import React from "react";

// Base Skeleton Component
export const Skeleton = ({ className = "", animate = true }) => (
  <div
    className={`bg-white/5 rounded ${animate ? "animate-pulse" : ""} ${className}`}
  />
);

// Text Line Skeleton
export const SkeletonText = ({ lines = 1, className = "" }) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        className={`h-4 ${i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"}`}
      />
    ))}
  </div>
);

// Circle Skeleton (Avatar, Icons)
export const SkeletonCircle = ({ size = "md", className = "" }) => {
  const sizes = {
    sm: "w-8 h-8",
    md: "w-12 h-12",
    lg: "w-16 h-16",
    xl: "w-24 h-24",
  };
  return <Skeleton className={`rounded-full ${sizes[size]} ${className}`} />;
};

// Card Skeleton
export const SkeletonCard = ({ className = "" }) => (
  <div
    className={`glass-card p-6 rounded-2xl border border-white/10 ${className}`}
  >
    <div className="flex items-center gap-4 mb-4">
      <SkeletonCircle size="md" />
      <div className="flex-1">
        <Skeleton className="h-4 w-1/2 mb-2" />
        <Skeleton className="h-3 w-1/3" />
      </div>
    </div>
    <SkeletonText lines={3} />
  </div>
);

// Stats Card Skeleton
export const SkeletonStatsCard = ({ className = "" }) => (
  <div
    className={`glass-card p-6 rounded-2xl border border-white/10 ${className}`}
  >
    <div className="flex items-start justify-between mb-4">
      <Skeleton className="h-4 w-24" />
      <SkeletonCircle size="sm" />
    </div>
    <Skeleton className="h-8 w-32 mb-2" />
    <Skeleton className="h-3 w-20" />
  </div>
);

// Chart Skeleton
export const SkeletonChart = ({ className = "" }) => (
  <div
    className={`glass-card p-6 rounded-2xl border border-white/10 ${className}`}
  >
    <div className="flex justify-between items-center mb-6">
      <Skeleton className="h-6 w-32" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-16 rounded-lg" />
        <Skeleton className="h-8 w-16 rounded-lg" />
        <Skeleton className="h-8 w-16 rounded-lg" />
      </div>
    </div>
    <div className="relative h-64">
      {/* Chart Bars Simulation */}
      <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between gap-1 h-full px-4">
        {Array.from({ length: 20 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1"
            style={{ height: `${Math.random() * 60 + 20}%` }}
          />
        ))}
      </div>
    </div>
  </div>
);

// Table Row Skeleton
export const SkeletonTableRow = ({ columns = 5, className = "" }) => (
  <div
    className={`flex items-center gap-4 py-4 border-b border-white/5 ${className}`}
  >
    {Array.from({ length: columns }).map((_, i) => (
      <Skeleton key={i} className={`h-4 ${i === 0 ? "w-32" : "flex-1"}`} />
    ))}
  </div>
);

// Table Skeleton
export const SkeletonTable = ({ rows = 5, columns = 5, className = "" }) => (
  <div
    className={`glass-card p-6 rounded-2xl border border-white/10 ${className}`}
  >
    {/* Header */}
    <div className="flex items-center gap-4 pb-4 border-b border-white/10 mb-4">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === 0 ? "w-32" : "flex-1"}`} />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, i) => (
      <SkeletonTableRow key={i} columns={columns} />
    ))}
  </div>
);

// Dashboard Skeleton (Full Page)
export const SkeletonDashboard = () => (
  <div className="space-y-6 animate-fade-in">
    {/* Stats Row */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <SkeletonStatsCard />
      <SkeletonStatsCard />
      <SkeletonStatsCard />
      <SkeletonStatsCard />
    </div>

    {/* Main Content */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <SkeletonChart />
      </div>
      <div className="space-y-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>
    </div>

    {/* Table */}
    <SkeletonTable rows={5} columns={6} />
  </div>
);

// Signal Card Skeleton
export const SkeletonSignalCard = ({ className = "" }) => (
  <div
    className={`glass-card p-6 rounded-2xl border border-white/10 ${className}`}
  >
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <Skeleton className="w-16 h-8 rounded-lg" />
        <Skeleton className="w-20 h-4" />
      </div>
      <Skeleton className="w-24 h-6 rounded-full" />
    </div>
    <div className="grid grid-cols-3 gap-4">
      <div>
        <Skeleton className="h-3 w-16 mb-1" />
        <Skeleton className="h-5 w-20" />
      </div>
      <div>
        <Skeleton className="h-3 w-16 mb-1" />
        <Skeleton className="h-5 w-20" />
      </div>
      <div>
        <Skeleton className="h-3 w-16 mb-1" />
        <Skeleton className="h-5 w-20" />
      </div>
    </div>
  </div>
);

// News Card Skeleton
export const SkeletonNewsCard = ({ className = "" }) => (
  <div
    className={`glass-card p-4 rounded-xl border border-white/10 flex gap-4 ${className}`}
  >
    <Skeleton className="w-24 h-20 rounded-lg flex-shrink-0" />
    <div className="flex-1">
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-3/4 mb-3" />
      <div className="flex items-center gap-2">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  </div>
);

// List Skeleton
export const SkeletonList = ({ items = 5, className = "" }) => (
  <div className={`space-y-3 ${className}`}>
    {Array.from({ length: items }).map((_, i) => (
      <div
        key={i}
        className="flex items-center gap-3 p-3 rounded-xl bg-white/5"
      >
        <SkeletonCircle size="sm" />
        <div className="flex-1">
          <Skeleton className="h-4 w-1/2 mb-1" />
          <Skeleton className="h-3 w-1/3" />
        </div>
        <Skeleton className="h-6 w-16 rounded-lg" />
      </div>
    ))}
  </div>
);

export default {
  Skeleton,
  SkeletonText,
  SkeletonCircle,
  SkeletonCard,
  SkeletonStatsCard,
  SkeletonChart,
  SkeletonTableRow,
  SkeletonTable,
  SkeletonDashboard,
  SkeletonSignalCard,
  SkeletonNewsCard,
  SkeletonList,
};
