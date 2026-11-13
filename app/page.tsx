import React from "react";
import Link from "next/link";
import { ArrowRight, Trophy } from "lucide-react";
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
    <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 py-8 space-y-10">
      {/* a. Header Strip */}
      <section className="space-y-2 border-b border-border-light pb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-mono text-xs text-text-muted uppercase tracking-wider">
              Executive Evaluation Dashboard &bull; {meta.build.data_span}
            </div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-text-primary tracking-tight">
              Who Delivers Under Pressure?
            </h1>
          </div>
          <Link
            href="/rankings/"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-mono font-bold rounded-md bg-accent-primary text-slate-950 hover:bg-sky-400 transition-colors shadow-sm"
          >
            <span>Explore All 243 Qualified Players</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        <p className="text-sm sm:text-base text-text-secondary max-w-3xl leading-relaxed">
          An empirical evaluation of batting runs-above-expected and bowling run-suppression across the highest-leverage third of T20 innings, stabilized with Empirical Bayes shrinkage.
        </p>
      </section>

      {/* b. Four Scope Summary Cards */}
      <section aria-labelledby="summary-cards-heading">
        <h2 id="summary-cards-heading" className="sr-only">
          Dataset Scope Summary
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard
            label="Matches Analysed"
            value={meta.dataset.total_matches.toLocaleString()}
            subtext="Clean non-DLS matches (IPL & T20I)"
            badge="0 DLS"
          />
          <SummaryCard
            label="Deliveries Analysed"
            value={meta.dataset.total_legal_deliveries.toLocaleString()}
            subtext="Ball-state tracking records"
            badge="Legal Balls"
          />
          <SummaryCard
            label="High-Pressure Corridor"
            value={meta.dataset.high_pressure_deliveries.toLocaleString()}
            subtext={`${meta.dataset.high_pressure_pct}% standardized leverage`}
            badge="Top Third"
          />
          <SummaryCard
            label="Eligible Players"
            value={`${meta.dataset.eligible_batters} / ${meta.dataset.eligible_bowlers}`}
            subtext="118 Batters &bull; 125 Bowlers qualified"
            badge="&ge;150 balls, &ge;15m"
          />
        </div>
      </section>

      {/* c. Side-by-side Leaderboards (Top 10 Batters & Bowlers) */}
      <section aria-labelledby="leaderboards-heading" className="space-y-4">
        <div className="flex items-center justify-between border-b border-border-light pb-3">
          <div>
            <h2 id="leaderboards-heading" className="text-lg sm:text-xl font-bold text-text-primary flex items-center gap-2">
              <Trophy className="w-5 h-5 text-amber-400" />
              <span>High-Pressure Leaderboards</span>
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Empirical Bayes shrunk rating (runs above expected / runs saved per ball).
            </p>
          </div>
          <Link
            href="/rankings/"
            className="text-xs font-mono text-accent-primary hover:underline hidden sm:inline"
          >
            View full rankings table &rarr;
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top 10 Batters */}
          <div className="space-y-3 bg-surface border border-border-light rounded-lg p-4 sm:p-5">
            <div className="flex items-center justify-between pb-2 border-b border-border-light">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-accent-batter" />
                <h3 className="font-bold text-sm text-text-primary">Top 10 Batters Under Pressure</h3>
              </div>
              <span className="font-mono text-[11px] text-text-muted">RAE Shrunk r/b</span>
            </div>

            <div className="space-y-2">
              {top10Batters.map((player) => (
                <LeaderboardRow key={player.player_id} player={player} rank={player.rank} />
              ))}
            </div>
          </div>

          {/* Top 10 Bowlers */}
          <div className="space-y-3 bg-surface border border-border-light rounded-lg p-4 sm:p-5">
            <div className="flex items-center justify-between pb-2 border-b border-border-light">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-accent-bowler" />
                <h3 className="font-bold text-sm text-text-primary">Top 10 Bowlers Under Pressure</h3>
              </div>
              <span className="font-mono text-[11px] text-text-muted">RSE Shrunk r/b</span>
            </div>

            <div className="space-y-2">
              {top10Bowlers.map((player) => (
                <LeaderboardRow key={player.player_id} player={player} rank={player.rank} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* d. "What We Found": Three Short Callout Cards */}
      <section aria-labelledby="callouts-heading" className="space-y-4">
        <h2 id="callouts-heading" className="text-lg sm:text-xl font-bold text-text-primary">
          Empirical Findings & Insights
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
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

      {/* e. Chart Block: Average Leverage by Over (1 to 20) */}
      <section aria-labelledby="leverage-chart-heading">
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

      {/* f. Honest-Limits Banner Linking to Method Page */}
      <section>
        <WarningBanner
          title="Honest Limits: Descriptive historical ratings, not predictive traits"
          message="Pressure metrics measure historical delivery-level efficiency against baseline expectations. Cross-era rank correlation is modest (rho ~ 0.25 to 0.29) and rankings contain dense statistical ties. View ratings as confidence tiers."
          linkHref="/method/"
          linkLabel="Read Full Methodology & Reliability Audit"
        />
      </section>
    </div>
  );
}
