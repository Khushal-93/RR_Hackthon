import React from "react";
import Link from "next/link";
import { ArrowRight, Trophy, Sparkles, Shield, BarChart3, ChevronRight } from "lucide-react";
import {
  getMetaSync,
  getRankingsSync,
  getLeverageByOverSync,
} from "@/lib/data";
import { SummaryCard } from "@/components/SummaryCard";
import { LeaderboardRow } from "@/components/LeaderboardRow";
import { WarningBanner } from "@/components/WarningBanner";
import { CalloutCard } from "@/components/CalloutCard";
import { ChartContainer } from "@/components/ChartContainer";
import {
  LeverageByOverChart,
  LeverageByOverTable,
} from "@/components/charts/LeverageByOverChart";

export default function OverviewPage() {
  const meta = getMetaSync();
  const top10Batters = getRankingsSync("batter").slice(0, 10);
  const top10Bowlers = getRankingsSync("bowler").slice(0, 10);
  const leverageByOver = getLeverageByOverSync();

  return (
    <div className="space-y-16 py-8 sm:py-12">
      {/* 1. HERO SECTION (Apple-Style Minimal & Cinematic) */}
      <section className="max-w-[1200px] mx-auto px-6 text-center space-y-6 pt-4 sm:pt-8">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-soft-blue border border-primary/20 text-primary text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-secondary" />
          <span>Competition Research &bull; IPL & T20I, 2022 to 2026</span>
        </div>

        <h1 className="apple-hero-title max-w-4xl mx-auto text-text-primary tracking-tight">
          Who Delivers When the Match Is on the Line?
        </h1>

        <p className="apple-subheading max-w-2xl mx-auto text-text-secondary leading-relaxed">
          An audited empirical evaluation across 829 non-DLS matches. Shrunk with Empirical Bayes to separate genuine signal from small-sample noise.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link href="/rankings/" className="apple-btn-gradient">
            <span>Explore 243 Qualified Players</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/method/" className="apple-btn-secondary">
            <span>Methodology & Audit</span>
          </Link>
        </div>

        <div className="text-xs font-mono text-text-muted pt-2">
          Descriptive historical ratings &bull; Not predictive traits
        </div>
      </section>

      {/* 2. FOUR SCOPE SUMMARY CARDS */}
      <section aria-labelledby="summary-cards-heading" className="max-w-[1200px] mx-auto px-6">
        <h2 id="summary-cards-heading" className="sr-only">
          Dataset Scope Summary
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <SummaryCard
            label="Matches Analysed"
            value={meta.dataset.total_matches.toLocaleString()}
            subtext="Clean non-DLS matches (IPL & T20I)"
            badge="0 DLS"
          />
          <SummaryCard
            label="Legal Deliveries"
            value={meta.dataset.total_legal_deliveries.toLocaleString()}
            subtext="Ball-state tracking records"
            badge="Audited"
          />
          <SummaryCard
            label="High-Pressure Corridor"
            value={meta.dataset.high_pressure_deliveries.toLocaleString()}
            subtext={`${meta.dataset.high_pressure_pct}% standardized leverage`}
            badge="Top Third"
          />
          <SummaryCard
            label="Eligible Roster"
            value={`${meta.dataset.eligible_batters} / ${meta.dataset.eligible_bowlers}`}
            subtext="118 Batters &bull; 125 Bowlers qualified"
            badge="&ge;150 balls, &ge;15m"
          />
        </div>
      </section>

      {/* 3. SIDE-BY-SIDE LEADERBOARDS (Top 10 Batters & Bowlers) */}
      <section aria-labelledby="leaderboards-heading" className="max-w-[1200px] mx-auto px-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-border-light pb-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-primary mb-1">
              Top Performers
            </div>
            <h2 id="leaderboards-heading" className="apple-section-title text-text-primary">
              High-Pressure Corridors
            </h2>
          </div>
          <Link
            href="/rankings/"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary-dark transition-colors"
          >
            <span>View all 243 players</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Top 10 Batters */}
          <div className="apple-card p-6 sm:p-7 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border-light">
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-secondary" />
                <h3 className="text-lg font-semibold text-text-primary">Top 10 Batters Under Pressure</h3>
              </div>
              <span className="text-xs font-mono text-text-muted">RAE Shrunk r/b</span>
            </div>

            <div className="space-y-2.5">
              {top10Batters.map((player) => (
                <LeaderboardRow key={player.player_id} player={player} rank={player.rank} />
              ))}
            </div>
          </div>

          {/* Top 10 Bowlers */}
          <div className="apple-card p-6 sm:p-7 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border-light">
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <h3 className="text-lg font-semibold text-text-primary">Top 10 Bowlers Under Pressure</h3>
              </div>
              <span className="text-xs font-mono text-text-muted">RSE Shrunk r/b</span>
            </div>

            <div className="space-y-2.5">
              {top10Bowlers.map((player) => (
                <LeaderboardRow key={player.player_id} player={player} rank={player.rank} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 4. THREE CORE EMPIRICAL CALLOUT CARDS */}
      <section aria-labelledby="callouts-heading" className="max-w-[1200px] mx-auto px-6 space-y-6">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-secondary mb-1">
            Empirical Findings
          </div>
          <h2 id="callouts-heading" className="apple-section-title text-text-primary">
            Key Insights From 195,707 Deliveries
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <CalloutCard
            tag="Innings Architecture"
            title="Innings 1 vs Innings 2 Asymmetry"
            description="75.5% of Innings 1 pressure concentrates in Overs 1-6 (Powerplay) as top-order batters face early swing while setting target. Innings 2 pressure back-loads into middle and death overs under escalating required run rates."
            linkHref="/pressure/"
            linkLabel="Explore leverage distribution"
          />
          <CalloutCard
            tag="Tactical Confounding"
            title="Middle-Overs Spin Dominance"
            description="60% of top-10 bowlers are spinners (vs 35.1% in pool). Five bowlers deliver 63% to 92% of their pressure balls in middle overs. Tactical role and phase context must accompany rank interpretations."
            linkHref="/method/"
            linkLabel="Inspect phase confounding notes"
          />
          <CalloutCard
            tag="Signal Repeatability"
            title="Modest Signal Across Eras"
            description="Fitted on 2022-2024 and tested on 2025-2026, rank repeatability is modest (rho = +0.25 batters, +0.29 bowlers). Binary dismissals (k*WAE) degraded stability due to noise and were removed from the score."
            linkHref="/method/"
            linkLabel="Audit out-of-time results"
          />
        </div>
      </section>

      {/* 5. LEVERAGE BY OVER CHART */}
      <section aria-labelledby="leverage-chart-heading" className="max-w-[1200px] mx-auto px-6">
        <h2 id="leverage-chart-heading" className="sr-only">
          Average Leverage Index by Over
        </h2>
        <ChartContainer
          title="Average Leverage Index by Over (Overs 1 to 20)"
          subtitle="Comparison of match swing leverage: Innings 1 (Powerplay foundation) vs Innings 2 (Chasing escalation)."
          chartView={<LeverageByOverChart data={leverageByOver} />}
          tableView={<LeverageByOverTable data={leverageByOver} />}
        />
      </section>

      {/* 6. HONEST-LIMITS WARNING BANNER */}
      <section className="max-w-[1200px] mx-auto px-6">
        <WarningBanner
          title="Honest Limits: Descriptive historical ratings, not predictive traits"
          message="Pressure metrics measure historical delivery-level efficiency against baseline expectations. Cross-era rank correlation is modest (rho ~ 0.25 to 0.29) and rankings contain dense statistical ties. View ratings as confidence tiers."
          linkHref="/method/"
          linkLabel="Read Full Methodology & Reliability Audit"
        />
      </section>

      {/* 7. AUDIT CITATIONS & TESTIMONIALS STRIP */}
      <section className="max-w-[1200px] mx-auto px-6 py-6 border-t border-border-light">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-text-secondary leading-relaxed">
          <div className="space-y-1.5">
            <div className="font-semibold text-text-primary text-xs uppercase tracking-wider font-mono">
              01 &bull; 0 DLS Deliveries
            </div>
            <p>100% of rain-shortened DLS matches (41) and Super Overs (38 balls) strictly excluded to protect baseline validity.</p>
          </div>
          <div className="space-y-1.5">
            <div className="font-semibold text-text-primary text-xs uppercase tracking-wider font-mono">
              02 &bull; Empirical Bayes Equalizer
            </div>
            <p>True per-player delivery variance prevents low-volume qualifiers from spiking ahead of veteran samples.</p>
          </div>
          <div className="space-y-1.5">
            <div className="font-semibold text-text-primary text-xs uppercase tracking-wider font-mono">
              03 &bull; Dropped Wicket Weighting
            </div>
            <p>Out-of-time tests proved adding binary wickets degrades repeatability. Pure run efficiency maximizes signal-to-noise.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
