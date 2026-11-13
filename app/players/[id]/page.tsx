import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, GitCompare, AlertTriangle, ShieldCheck, Calendar, Activity } from "lucide-react";
import { getAllPlayerIdsSync, getPlayerSync } from "@/lib/data";
import { UncertaintyBar } from "@/components/UncertaintyBar";
import { TierBadge } from "@/components/TierBadge";

interface Props {
  params: {
    id: string;
  };
}

export function generateStaticParams() {
  const ids = getAllPlayerIdsSync();
  return ids.map((id) => ({ id }));
}

export default function PlayerProfilePage({ params }: Props) {
  const player = getPlayerSync(params.id);
  if (!player) {
    notFound();
  }

  const isPositive = player.stats.shrunk_rate >= 0;

  return (
    <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 py-8 space-y-8">
      {/* g. Navigation breadcrumbs */}
      <div className="flex items-center justify-between">
        <Link
          href="/rankings/"
          className="inline-flex items-center gap-1.5 font-mono text-xs text-text-muted hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Rankings</span>
        </Link>

        <Link
          href={`/compare/?player1=${player.player_id}`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 font-mono text-xs font-bold rounded border border-border-medium bg-surface hover:bg-surface-subtle text-accent-primary transition-colors"
        >
          <GitCompare className="w-3.5 h-3.5" />
          <span>Compare This Player</span>
        </Link>
      </div>

      {/* a. Identity Block */}
      <div className="bg-surface border border-border-light rounded-lg p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-surface-subtle border border-border-medium text-accent-primary">
              #{player.rank} in {player.role === "batter" ? "Batters" : "Bowlers"}
            </span>
            <TierBadge tier={player.tier} />
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
            {player.player_name}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-text-secondary pt-1">
            <span className="capitalize">{player.role}</span>
            <span>&bull;</span>
            <span>{player.profile.batting_type || player.profile.bowling_type || player.profile.pace_or_spin}</span>
            <span>&bull;</span>
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-text-muted" />
              <span>{player.profile.active_years[0]} &ndash; {player.profile.active_years[1]}</span>
            </span>
            <span>&bull;</span>
            <span>{player.stats.balls} HP balls across {player.stats.matches} matches</span>
          </div>
        </div>

        {/* Rating summary highlight */}
        <div className="bg-surface-subtle/80 border border-border-light p-4 rounded-lg min-w-[220px] text-right font-mono">
          <div className="text-[11px] text-text-muted uppercase">Shrunk Pressure Rating</div>
          <div className={`text-3xl font-extrabold my-1 ${isPositive ? "text-accent-success" : "text-accent-danger"}`}>
            {isPositive ? `+${player.stats.shrunk_rate.toFixed(3)}` : player.stats.shrunk_rate.toFixed(3)}
            <span className="text-xs text-text-muted ml-1">r/b</span>
          </div>
          <div className="text-[11px] text-text-secondary">
            Lambda: {player.stats.lambda.toFixed(3)} (Shrinkage weight)
          </div>
        </div>
      </div>

      {/* b. Plain-Language Reading Card */}
      <div className="p-4 rounded-lg bg-surface border border-border-light font-mono text-xs text-text-secondary leading-relaxed flex items-start gap-3">
        <Activity className="w-4 h-4 text-accent-primary shrink-0 mt-0.5" />
        <p className="text-text-primary">{player.plain_language_reading}</p>
      </div>

      {/* c. Component Breakdown: Actual vs Expected Rate & Dismissal vs Expected */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface border border-border-light rounded-lg p-5 space-y-4">
          <h2 className="font-bold text-base text-text-primary">Performance Components</h2>
          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between py-2 border-b border-border-light">
              <span className="text-text-secondary">Raw Observed Rate:</span>
              <span className="font-bold text-text-primary">
                {player.stats.raw_rate >= 0 ? `+${player.stats.raw_rate.toFixed(3)}` : player.stats.raw_rate.toFixed(3)} r/b
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-border-light">
              <span className="text-text-secondary">Shrunk Rating (RAE/RSE):</span>
              <span className={`font-bold ${isPositive ? "text-accent-success" : "text-accent-danger"}`}>
                {isPositive ? `+${player.stats.shrunk_rate.toFixed(3)}` : player.stats.shrunk_rate.toFixed(3)} r/b
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-border-light">
              <span className="text-text-secondary">80% Credible Interval:</span>
              <span className="text-text-primary">
                [{player.stats.ci80_lower >= 0 ? `+${player.stats.ci80_lower.toFixed(3)}` : player.stats.ci80_lower.toFixed(3)},{" "}
                {player.stats.ci80_upper >= 0 ? `+${player.stats.ci80_upper.toFixed(3)}` : player.stats.ci80_upper.toFixed(3)}]
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-border-light">
              <span className="text-text-secondary">Dismissal Rate vs Expected:</span>
              <span className="font-bold text-text-primary">
                {player.stats.dismissal_rate_vs_exp >= 0
                  ? `+${(player.stats.dismissal_rate_vs_exp * 100).toFixed(2)}%`
                  : `${(player.stats.dismissal_rate_vs_exp * 100).toFixed(2)}%`}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-text-secondary">Bootstrap P(Top-10):</span>
              <span className="font-bold text-accent-primary">
                {(player.stats.prob_top10 * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* d. Pressure-Ball Mix: Phase, Innings, Competition */}
        <div className="bg-surface border border-border-light rounded-lg p-5 space-y-4">
          <h2 className="font-bold text-base text-text-primary">Corridor Delivery Distribution</h2>
          <div className="space-y-4 text-xs font-mono">
            {/* Phase share */}
            <div>
              <div className="flex justify-between text-text-secondary mb-1">
                <span>Phase Mix</span>
                <span>PP {player.phase_split.powerplay_pct}% &bull; Mid {player.phase_split.middle_pct}% &bull; Dth {player.phase_split.death_pct}%</span>
              </div>
              <div className="h-3 w-full bg-surface-subtle rounded flex overflow-hidden">
                <div style={{ width: `${player.phase_split.powerplay_pct}%` }} className="bg-amber-400" title="Powerplay" />
                <div style={{ width: `${player.phase_split.middle_pct}%` }} className="bg-sky-400" title="Middle" />
                <div style={{ width: `${player.phase_split.death_pct}%` }} className="bg-rose-400" title="Death" />
              </div>
            </div>

            {/* Innings share */}
            <div>
              <div className="flex justify-between text-text-secondary mb-1">
                <span>Innings Mix</span>
                <span>Inn 1: {player.innings_split.innings_1_pct}% &bull; Inn 2: {player.innings_split.innings_2_pct}%</span>
              </div>
              <div className="h-3 w-full bg-surface-subtle rounded flex overflow-hidden">
                <div style={{ width: `${player.innings_split.innings_1_pct}%` }} className="bg-amber-500" title="Innings 1" />
                <div style={{ width: `${player.innings_split.innings_2_pct}%` }} className="bg-sky-500" title="Innings 2" />
              </div>
            </div>

            {/* Competition share */}
            <div>
              <div className="flex justify-between text-text-secondary mb-1">
                <span>Competition Mix</span>
                <span>IPL: {player.stats.ipl_share_pct}% &bull; T20I: {player.stats.t20i_share_pct}%</span>
              </div>
              <div className="h-3 w-full bg-surface-subtle rounded flex overflow-hidden">
                <div style={{ width: `${player.stats.ipl_share_pct}%` }} className="bg-blue-600" title="IPL" />
                <div style={{ width: `${player.stats.t20i_share_pct}%` }} className="bg-emerald-600" title="T20I" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* e. Stability Check: Rating with and without Two Best Matches */}
      <section aria-labelledby="stability-check-heading">
        <div
          className={`p-5 rounded-lg border ${
            player.stability_check.is_sensitive
              ? "bg-amber-950/20 border-amber-500/50"
              : "bg-surface border-border-light"
          }`}
        >
          <div className="flex items-start gap-3">
            {player.stability_check.is_sensitive ? (
              <AlertTriangle className="w-5 h-5 text-accent-warning shrink-0 mt-0.5" />
            ) : (
              <ShieldCheck className="w-5 h-5 text-accent-success shrink-0 mt-0.5" />
            )}
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center justify-between">
                <h2 id="stability-check-heading" className="font-bold text-sm text-text-primary">
                  Leave-Top-2-Matches-Out Robustness Audit
                </h2>
                <span className="font-mono text-xs font-bold text-text-muted">
                  Sensitivity Check
                </span>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed">
                {player.stability_check.audit_note}
              </p>
              <div className="flex flex-wrap gap-4 pt-2 font-mono text-xs">
                <div>
                  <span className="text-text-muted">Full Rating: </span>
                  <span className="font-bold text-text-primary">
                    {player.stats.shrunk_rate >= 0 ? `+${player.stats.shrunk_rate.toFixed(3)}` : player.stats.shrunk_rate.toFixed(3)} (#{player.rank})
                  </span>
                </div>
                <div>
                  <span className="text-text-muted">Excluding Top 2: </span>
                  <span className="font-bold text-accent-warning">
                    {player.stability_check.leave_2_matches_shrunk_rate >= 0
                      ? `+${player.stability_check.leave_2_matches_shrunk_rate.toFixed(3)}`
                      : player.stability_check.leave_2_matches_shrunk_rate.toFixed(3)}{" "}
                    (#{player.stability_check.leave_2_matches_rank})
                  </span>
                </div>
                <div>
                  <span className="text-text-muted">Rank Shift: </span>
                  <span className="font-bold text-text-secondary">
                    {player.stability_check.rank_delta > 0
                      ? `-${player.stability_check.rank_delta} spots`
                      : "0 spots"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* f. Match-by-match Contribution Strip */}
      <section aria-labelledby="match-strip-heading" className="space-y-3">
        <h2 id="match-strip-heading" className="font-bold text-base text-text-primary">
          Match-by-Match High-Pressure Performances (Recent Appearances)
        </h2>
        {player.match_strip.length > 0 ? (
          <div className="overflow-x-auto border border-border-light rounded-lg bg-surface">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-border-light bg-surface-subtle text-text-secondary uppercase text-[10px]">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Season</th>
                  <th className="py-2.5 px-3 text-right">HP Balls</th>
                  <th className="py-2.5 px-3 text-right">{player.role === "batter" ? "Runs Scored" : "Runs Conceded"}</th>
                  <th className="py-2.5 px-3 text-right">Wickets</th>
                  <th className="py-2.5 px-3 text-right">Performance Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-light/40">
                {player.match_strip.map((m) => (
                  <tr key={m.match_id} className="hover:bg-surface-subtle/50">
                    <td className="py-2 px-3 font-sans text-text-primary">{m.match_date}</td>
                    <td className="py-2 px-3 text-text-muted">{m.season}</td>
                    <td className="py-2 px-3 text-right">{m.balls}</td>
                    <td className="py-2 px-3 text-right font-bold">{m.runs}</td>
                    <td className="py-2 px-3 text-right">{m.wickets}</td>
                    <td className="py-2 px-3 text-right font-bold">
                      <span className={m.contribution_rate >= 0 ? "text-accent-success" : "text-accent-danger"}>
                        {m.contribution_rate >= 0 ? `+${m.contribution_rate.toFixed(2)}` : m.contribution_rate.toFixed(2)} r/b
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6 text-center text-xs font-mono text-text-muted bg-surface border border-border-light rounded-lg">
            No delivery records found for this player.
          </div>
        )}
      </section>
    </div>
  );
}
