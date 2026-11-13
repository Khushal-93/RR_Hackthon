"use client";

import React from "react";
import { SummaryCard } from "@/components/SummaryCard";
import { TierBadge } from "@/components/TierBadge";
import { UncertaintyBar } from "@/components/UncertaintyBar";
import { RoleToggle } from "@/components/RoleToggle";
import { WarningBanner } from "@/components/WarningBanner";
import { CalloutCard } from "@/components/CalloutCard";
import { EmptyState } from "@/components/EmptyState";
import { Skeleton } from "@/components/Skeleton";

export default function DevComponentsPage() {
  const [role, setRole] = React.useState<"batter" | "bowler">("batter");

  return (
    <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 py-10 space-y-12">
      <div className="border-b border-border-medium pb-4">
        <span className="font-mono text-xs text-text-muted uppercase">Development Playground</span>
        <h1 className="text-3xl font-extrabold text-text-primary">Component Inventory & State Matrix</h1>
        <p className="text-sm text-text-secondary mt-1">
          Interactive showcase demonstrating every UI component across Default, Hover, Focus, Active, and Loading states.
        </p>
      </div>

      {/* 1. Summary Cards */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">1. Summary Cards</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard label="Matches Analyzed" value="829" subtext="Non-DLS T20 matches" badge="Clean Sample" />
          <SummaryCard label="Legal Deliveries" value="195,707" subtext="Ball-by-ball states" badge="Parquet" />
          <SummaryCard label="High-Pressure Corridor" value="65,229" subtext="33.3% top leverage" badge="Standardized" />
          <SummaryCard label="Loading State" value="---" subtext="Loading metrics..." isLoading={true} />
        </div>
      </section>

      {/* 2. Tier Badges */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">2. Confidence Tier Badges</h2>
        <div className="flex flex-wrap gap-4 items-center">
          <TierBadge tier="Tier 1: Elite Lock" />
          <TierBadge tier="Tier 2: Quality Under Pressure" />
          <TierBadge tier="Tier 3: Baseline Average" />
          <TierBadge tier="Tier 4: Below Baseline" />
          <TierBadge tier="Tier 1: Elite Lock" size="sm" />
        </div>
      </section>

      {/* 3. Uncertainty Bars */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">3. Uncertainty Bars (80% Credible Interval)</h2>
        <div className="space-y-3 bg-surface p-4 rounded-lg border border-border-light max-w-md">
          <div className="flex items-center justify-between text-xs font-mono">
            <span>High Performer (+0.39 r/b):</span>
            <UncertaintyBar lower={0.29} upper={0.49} point={0.39} width="w-40" showLabels />
          </div>
          <div className="flex items-center justify-between text-xs font-mono">
            <span>Tight Interval (+0.17 r/b):</span>
            <UncertaintyBar lower={0.10} upper={0.25} point={0.17} width="w-40" showLabels />
          </div>
          <div className="flex items-center justify-between text-xs font-mono">
            <span>Negative Rating (-0.12 r/b):</span>
            <UncertaintyBar lower={-0.22} upper={-0.02} point={-0.12} width="w-40" showLabels />
          </div>
        </div>
      </section>

      {/* 4. Role Toggle */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">4. Role Toggle Control</h2>
        <div>
          <RoleToggle role={role} onChange={setRole} />
        </div>
      </section>

      {/* 5. Warning / Limits Banner */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">5. Warning / Limits Banner</h2>
        <WarningBanner />
      </section>

      {/* 6. Callout Cards */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">6. Empirical Callout Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <CalloutCard
            tag="Innings Dynamics"
            title="Early Swing vs Late Chase"
            description="75.5% of Innings 1 pressure occurs in the Powerplay (overs 1-6) as top-order batters face swing volatility. Innings 2 pressure back-loads into middle/death overs."
          />
          <CalloutCard
            tag="Tactical Confounding"
            title="Middle-Overs Spin Dominance"
            description="60% of top-10 bowlers are spinners (vs 35% in pool), with 5 bowling over 63% in middle overs. Tactical role evaluation is essential."
          />
          <CalloutCard
            tag="Repeatability Audit"
            title="Out-of-Time Signal is Modest"
            description="Out-of-time rank correlation across eras is rho ~ 0.25 to 0.29. Dismissals (k*WAE) degraded repeatability and were dropped from the score."
          />
        </div>
      </section>

      {/* 7. Empty State and Skeletons */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold font-mono text-text-primary">7. Skeletons and Empty States</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 bg-surface border border-border-light rounded-lg space-y-3">
            <span className="font-mono text-xs text-text-muted">Skeleton Loader Blocks</span>
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-20 w-full" />
          </div>
          <EmptyState />
        </div>
      </section>
    </div>
  );
}
