import React from "react";
import Link from "next/link";
import { Sparkles, Info, Compass, Flame, ShieldAlert } from "lucide-react";
import { getHeatmapSync, getMetaSync } from "@/lib/data";
import { LeverageHeatmapView } from "@/components/charts/LeverageHeatmapView";

export default function PressureExplorerPage() {
  const heatmap = getHeatmapSync();
  const meta = getMetaSync();

  return (
    <div className="max-w-[1200px] mx-auto px-6 py-8 sm:py-12 space-y-12">
      {/* Header */}
      <div className="space-y-2 border-b border-border-light pb-6">
        <span className="text-xs uppercase font-semibold text-secondary tracking-wider">Concept & Architecture</span>
        <h1 className="apple-section-title text-text-primary tracking-tight">
          Pressure Definition & State Explorer
        </h1>
        <p className="text-sm sm:text-base text-text-secondary max-w-2xl leading-relaxed">
          How leverage index quantifies match-outcome volatility, and why standardized top-third pressure creates balanced evaluation corridors across both innings.
        </p>
      </div>

      {/* a. Plain-English Definition Panel */}
      <section aria-labelledby="definition-heading" className="apple-card p-8 space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-soft-blue flex items-center justify-center text-primary">
            <Compass className="w-5 h-5" />
          </div>
          <h2 id="definition-heading" className="text-2xl font-bold text-text-primary">
            What Exactly Is Leverage Index?
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm leading-relaxed text-text-secondary">
          <div className="space-y-3">
            <h3 className="font-semibold text-base text-text-primary">Standard Swing Volatility</h3>
            <p>
              Leverage Index (LI) measures how much the <strong>win probability of the match</strong> can swing on a single delivery compared to an average ball.
            </p>
            <ul className="space-y-1.5 list-disc list-inside font-mono text-xs text-text-primary">
              <li><strong>LI = 1.0:</strong> An average delivery (standard outcome volatility).</li>
              <li><strong>LI &gt; 1.25:</strong> High-leverage corridor (our pressure definition).</li>
              <li><strong>LI &gt; 2.50:</strong> Extreme leverage (super-critical death or swing overs).</li>
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold text-base text-text-primary">Within-Innings Normalization</h3>
            <p>
              Unstandardized leverage is heavily biased toward Innings 2 because chasing teams experience rapid win-probability swings near the death overs.
            </p>
            <p>
              To ensure fairness, we standardise leverage <strong>within each innings separately</strong>. High pressure is defined strictly as the <strong>top third (66.7th percentile)</strong> within Innings 1 (LI &ge; {meta.dataset.leverage_inn1_cutoff}) and Innings 2 (LI &ge; {meta.dataset.leverage_inn2_cutoff}).
            </p>
          </div>
        </div>
      </section>

      {/* b. Match Trajectory Sample: High-Pressure Corridor in Action */}
      <section aria-labelledby="match-trajectory-heading" className="apple-card p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-soft-pink flex items-center justify-center text-secondary">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <h2 id="match-trajectory-heading" className="text-xl font-bold text-text-primary">
                Match Timeline & Win Probability Anatomy
              </h2>
              <p className="text-xs text-text-secondary">
                How individual balls enter the high-pressure corridor during a 190-run chase.
              </p>
            </div>
          </div>
          <span className="font-mono text-xs text-primary px-3 py-1 rounded-full bg-soft-blue">
            Representative Match Sample
          </span>
        </div>

        {/* Visualized Timeline Strip */}
        <div className="space-y-3 font-mono text-xs">
          <div className="relative h-12 bg-black/[0.03] dark:bg-white/[0.05] rounded-xl overflow-hidden border border-border-light flex items-center px-4 justify-between">
            {/* High pressure corridor highlights */}
            <div className="absolute top-0 bottom-0 left-[0%] width-[25%] bg-amber-500/10 border-r border-amber-500/30 flex items-center px-2 text-[10px] text-amber-600 dark:text-amber-400">
              Overs 1&ndash;5 (Swing Volatility)
            </div>
            <div className="absolute top-0 bottom-0 left-[65%] right-0 bg-primary/10 border-l border-primary/30 flex items-center px-2 text-[10px] text-primary">
              Overs 14&ndash;20 (Chase Escalation)
            </div>
            <span className="relative z-10 text-text-muted">Ov 1</span>
            <span className="relative z-10 text-text-muted">Ov 6 (PP)</span>
            <span className="relative z-10 text-text-muted">Ov 12</span>
            <span className="relative z-10 text-text-muted">Ov 16</span>
            <span className="relative z-10 text-text-muted">Ov 20</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-text-secondary leading-relaxed pt-2">
            <div className="p-4 rounded-xl bg-surface border border-border-light">
              <span className="font-bold text-text-primary block mb-1">Innings 1 High-Pressure Zone</span>
              75.54% of Innings 1 pressure occurs in the Powerplay (overs 1&ndash;6), faced 86.99% by batting orders 1&ndash;3. This captures <strong>Early Foundation Volatility</strong>.
            </div>
            <div className="p-4 rounded-xl bg-surface border border-border-light">
              <span className="font-bold text-text-primary block mb-1">Innings 2 High-Pressure Zone</span>
              Concentrated in middle and death overs under escalating required run rates. This captures <strong>Target-Chasing Execution</strong> under match-outcome volatility.
            </div>
          </div>
        </div>
      </section>

      {/* c. Two Over x Wickets Heatmaps (Innings 1 & 2) */}
      <section aria-labelledby="heatmaps-heading" className="space-y-6">
        <div>
          <span className="text-xs uppercase font-semibold text-primary tracking-wider">Leverage State Space</span>
          <h2 id="heatmaps-heading" className="apple-section-title text-text-primary">
            Over &times; Wickets in Hand Heatmaps
          </h2>
          <p className="text-sm text-text-secondary mt-1">
            20 Overs &times; 10 Wickets-in-Hand state matrix showing mean empirical leverage index across 195,707 deliveries.
          </p>
        </div>

        <LeverageHeatmapView data={heatmap} />
      </section>
    </div>
  );
}
