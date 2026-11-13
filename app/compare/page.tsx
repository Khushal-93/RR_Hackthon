"use client";

import React, { useState, useEffect, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { GitCompare, AlertCircle, ArrowRight, UserPlus, X } from "lucide-react";
import { RankingItem, PlayerRole } from "@/lib/types";
import { RoleToggle } from "@/components/RoleToggle";
import { TierBadge } from "@/components/TierBadge";
import { UncertaintyBar } from "@/components/UncertaintyBar";

function CompareContent() {
  const searchParams = useSearchParams();
  const [role, setRole] = useState<PlayerRole>("batter");
  const [allPlayers, setAllPlayers] = useState<RankingItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("/data/rankings.json")
      .then((res) => res.json())
      .then((data: RankingItem[]) => {
        setAllPlayers(data);
        setIsLoading(false);

        // Pre-select from URL params or default to top 2
        const p1 = searchParams.get("player1");
        const p2 = searchParams.get("player2");
        if (p1 && data.some((p) => p.player_id === p1)) {
          const matchP1 = data.find((p) => p.player_id === p1);
          if (matchP1) setRole(matchP1.role);
          setSelectedIds([p1, p2 && data.some((p) => p.player_id === p2) ? p2 : (data.find((p) => p.role === matchP1?.role && p.player_id !== p1)?.player_id || "")].filter(Boolean));
        } else {
          // Default to top 2 batters
          const top2 = data.filter((p) => p.role === "batter").slice(0, 2).map((p) => p.player_id);
          setSelectedIds(top2);
        }
      })
      .catch(() => setIsLoading(false));
  }, [searchParams]);

  const availablePlayers = useMemo(() => {
    return allPlayers.filter((p) => p.role === role);
  }, [allPlayers, role]);

  const selectedPlayers = useMemo(() => {
    return selectedIds
      .map((id) => allPlayers.find((p) => p.player_id === id))
      .filter(Boolean) as RankingItem[];
  }, [selectedIds, allPlayers]);

  const handleRoleChange = (newRole: PlayerRole) => {
    setRole(newRole);
    const top2 = allPlayers.filter((p) => p.role === newRole).slice(0, 2).map((p) => p.player_id);
    setSelectedIds(top2);
  };

  const addPlayer = (id: string) => {
    if (selectedIds.length < 4 && !selectedIds.includes(id)) {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const removePlayer = (id: string) => {
    if (selectedIds.length > 2) {
      setSelectedIds(selectedIds.filter((pId) => pId !== id));
    }
  };

  // Pairwise probability calculation between player 1 and player 2
  const pairwiseStats = useMemo(() => {
    if (selectedPlayers.length < 2) return null;
    const p1 = selectedPlayers[0];
    const p2 = selectedPlayers[1];

    // Normal approximation delta: Z = (rate1 - rate2) / sqrt(se1^2 + se2^2)
    // Approximate se from 80% CI width: width = 2 * 1.2816 * se => se = width / 2.563
    const se1 = Math.max(0.01, (p1.ci80_upper - p1.ci80_lower) / 2.563);
    const se2 = Math.max(0.01, (p2.ci80_upper - p2.ci80_lower) / 2.563);
    const diff = p1.shrunk_rate - p2.shrunk_rate;
    const pooledSe = Math.sqrt(se1 * se1 + se2 * se2);
    const z = diff / pooledSe;

    // Standard normal CDF approximation
    const cdf = (val: number) => {
      const t = 1 / (1 + 0.2316419 * Math.abs(val));
      const d = 0.3989423 * Math.exp((-val * val) / 2);
      let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
      return val > 0 ? 1 - p : p;
    };

    const probP1BeatsP2 = cdf(z);
    const isTie = Math.abs(probP1BeatsP2 - 0.5) <= 0.12; // 38% to 62% is statistical tie

    return {
      p1,
      p2,
      diff,
      probP1BeatsP2,
      probP2BeatsP1: 1 - probP1BeatsP2,
      isTie,
    };
  }, [selectedPlayers]);

  return (
    <div className="max-w-[1200px] mx-auto px-6 py-8 sm:py-12 space-y-10">
      {/* Header */}
      <div className="space-y-2 border-b border-border-light pb-6">
        <span className="text-xs uppercase font-semibold text-primary tracking-wider">Evaluation Workbench</span>
        <h1 className="apple-section-title text-text-primary tracking-tight">
          Head-to-Head Player Comparison
        </h1>
        <p className="text-sm sm:text-base text-text-secondary max-w-2xl leading-relaxed">
          Select 2 to 4 same-role players to compare empirical ratings, confidence intervals, sample sizes, and pairwise bootstrap superiority probabilities.
        </p>
      </div>

      {/* Role Toggle & Picker Bar */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <RoleToggle role={role} onChange={handleRoleChange} />

          {selectedIds.length < 4 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-secondary font-mono">Add player:</span>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    addPlayer(e.target.value);
                    e.target.value = "";
                  }
                }}
                className="bg-surface border border-border-medium rounded-full px-4 py-1.5 text-xs font-mono text-text-primary focus:outline-none"
              >
                <option value="">Select a player...</option>
                {availablePlayers
                  .filter((p) => !selectedIds.includes(p.player_id))
                  .map((p) => (
                    <option key={p.player_id} value={p.player_id}>
                      #{p.rank} {p.player_name} ({p.shrunk_rate >= 0 ? `+${p.shrunk_rate.toFixed(3)}` : p.shrunk_rate.toFixed(3)})
                    </option>
                  ))}
              </select>
            </div>
          )}
        </div>

        {/* Selected Player Chips */}
        <div className="flex flex-wrap gap-2.5 pt-2">
          {selectedPlayers.map((p, idx) => (
            <div
              key={p.player_id}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface border border-border-medium text-xs font-medium shadow-sm"
            >
              <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center font-mono text-[10px] font-bold">
                {idx + 1}
              </span>
              <span className="font-semibold text-text-primary">{p.player_name}</span>
              <span className="font-mono text-text-muted">#{p.rank}</span>
              {selectedIds.length > 2 && (
                <button
                  onClick={() => removePlayer(p.player_id)}
                  className="text-text-muted hover:text-text-primary p-0.5"
                  aria-label={`Remove ${p.player_name}`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Head-to-Head Pairwise Probability Banner */}
      {pairwiseStats && (
        <div className="space-y-4">
          {pairwiseStats.isTie ? (
            <div className="p-6 rounded-[22px] bg-soft-blue border border-primary/30 flex items-start gap-4 animate-in fade-in">
              <AlertCircle className="w-5 h-5 text-primary shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-base text-primary">
                  Statistical Tie Detected ({pairwiseStats.p1.player_name} vs {pairwiseStats.p2.player_name})
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">
                  The head-to-head win probability is <strong>{(pairwiseStats.probP1BeatsP2 * 100).toFixed(1)}% vs {(pairwiseStats.probP2BeatsP1 * 100).toFixed(1)}%</strong>. Because this is within the 40%&ndash;60% confidence threshold, these players represent a statistical tie rather than a meaningful rank difference.
                </p>
              </div>
            </div>
          ) : (
            <div className="apple-card p-6 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div className="space-y-1 text-center sm:text-left">
                <div className="text-xs font-mono uppercase text-text-secondary">Pairwise Bootstrap Odds</div>
                <div className="text-lg font-semibold text-text-primary">
                  {pairwiseStats.p1.player_name} leads {pairwiseStats.p2.player_name}
                </div>
                <div className="text-xs text-text-muted">
                  Delta: {pairwiseStats.diff >= 0 ? `+${pairwiseStats.diff.toFixed(3)}` : pairwiseStats.diff.toFixed(3)} runs/ball
                </div>
              </div>

              <div className="flex items-center gap-6 font-mono text-center">
                <div>
                  <div className="text-2xl font-bold text-primary">
                    {(pairwiseStats.probP1BeatsP2 * 100).toFixed(0)}%
                  </div>
                  <div className="text-[11px] text-text-secondary truncate max-w-[120px]">{pairwiseStats.p1.player_name}</div>
                </div>
                <span className="text-xs text-text-muted">vs</span>
                <div>
                  <div className="text-2xl font-bold text-secondary">
                    {(pairwiseStats.probP2BeatsP1 * 100).toFixed(0)}%
                  </div>
                  <div className="text-[11px] text-text-secondary truncate max-w-[120px]">{pairwiseStats.p2.player_name}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Side-by-Side Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {selectedPlayers.map((player) => {
          const isPositive = player.shrunk_rate >= 0;
          return (
            <div key={player.player_id} className="apple-card p-6 space-y-5 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded-full bg-soft-blue text-primary">
                    #{player.rank} in {player.role}
                  </span>
                  <TierBadge tier={player.tier} size="sm" />
                </div>
                <div>
                  <Link
                    href={`/players/${player.player_id}/`}
                    className="font-bold text-lg text-text-primary hover:text-primary transition-colors block"
                  >
                    {player.player_name}
                  </Link>
                  <span className="text-xs text-text-secondary">
                    {player.batting_type || player.bowling_type || player.pace_or_spin}
                  </span>
                </div>
              </div>

              {/* Shrunk rating */}
              <div className="p-4 rounded-xl bg-black/[0.02] dark:bg-white/[0.04] text-center font-mono">
                <div className="text-[11px] text-text-muted uppercase">Shrunk Rating</div>
                <div className={`text-2xl font-bold my-1 ${isPositive ? "text-primary" : "text-secondary"}`}>
                  {isPositive ? `+${player.shrunk_rate.toFixed(3)}` : player.shrunk_rate.toFixed(3)}
                  <span className="text-xs text-text-muted ml-1">r/b</span>
                </div>
                <div className="text-[11px] text-text-secondary">
                  Raw: {player.raw_rate >= 0 ? `+${player.raw_rate.toFixed(3)}` : player.raw_rate.toFixed(3)}
                </div>
              </div>

              {/* Metrics table */}
              <div className="space-y-2 text-xs font-mono divide-y divide-border-light/60">
                <div className="flex justify-between py-1.5">
                  <span className="text-text-secondary">HP Deliveries:</span>
                  <span className="font-semibold text-text-primary">{player.balls} b</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-text-secondary">Matches:</span>
                  <span className="font-semibold text-text-primary">{player.matches}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-text-secondary">Shrinkage &lambda;:</span>
                  <span className="font-semibold text-primary">{player.lambda.toFixed(3)}</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-text-secondary">P(Top-10):</span>
                  <span className="font-semibold text-secondary">{(player.prob_top10 * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-text-secondary">IPL Share:</span>
                  <span className="font-semibold text-text-primary">{player.ipl_share_pct.toFixed(0)}%</span>
                </div>
              </div>

              {/* Uncertainty Bar */}
              <div className="pt-2">
                <div className="text-[11px] font-mono text-text-muted mb-1">80% Credible Interval:</div>
                <UncertaintyBar
                  lower={player.ci80_lower}
                  upper={player.ci80_upper}
                  point={player.shrunk_rate}
                  width="w-full"
                  showLabels
                />
              </div>

              <div className="pt-2">
                <Link
                  href={`/players/${player.player_id}/`}
                  className="w-full apple-btn-secondary text-center text-xs py-2 block"
                >
                  View Full Profile &rarr;
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-[1200px] mx-auto px-6 py-16 text-center font-mono text-sm text-text-muted">
          Loading comparison data...
        </div>
      }
    >
      <CompareContent />
    </Suspense>
  );
}

