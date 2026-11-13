import React from "react";
import Link from "next/link";
import { RankingItem } from "@/lib/types";
import { UncertaintyBar } from "./UncertaintyBar";
import { TierBadge } from "./TierBadge";

interface Props {
  player: RankingItem;
  rank: number;
}

export function LeaderboardRow({ player, rank }: Props) {
  const isPositive = player.shrunk_rate >= 0;

  return (
    <div className="flex items-center justify-between p-3 rounded-md border border-border-light bg-surface hover:bg-surface-subtle transition-colors group">
      {/* Rank and Player Identity */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div
          className={`w-7 h-7 rounded flex items-center justify-center font-mono text-xs font-bold shrink-0 border ${
            rank === 1
              ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
              : rank <= 3
              ? "bg-slate-700/50 text-slate-200 border-slate-600"
              : "bg-surface-subtle text-text-secondary border-border-light"
          }`}
        >
          {rank}
        </div>

        <div className="min-w-0">
          <Link
            href={`/players/${player.player_id}/`}
            className="font-bold text-sm text-text-primary group-hover:text-accent-primary transition-colors truncate block focus:outline-none focus:underline"
          >
            {player.player_name}
          </Link>
          <div className="text-[11px] font-mono text-text-muted flex items-center gap-2">
            <span>{player.balls} balls</span>
            <span>&bull;</span>
            <span>P(Top10): {(player.prob_top10 * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Stats, Uncertainty Bar, and Tier */}
      <div className="flex items-center gap-4 shrink-0 text-right">
        <div className="hidden sm:block">
          <UncertaintyBar
            lower={player.ci80_lower}
            upper={player.ci80_upper}
            point={player.shrunk_rate}
            width="w-20 lg:w-24"
          />
        </div>

        <div className="font-mono min-w-[70px]">
          <span className={`text-sm font-bold ${isPositive ? "text-accent-success" : "text-accent-danger"}`}>
            {isPositive ? `+${player.shrunk_rate.toFixed(3)}` : player.shrunk_rate.toFixed(3)}
          </span>
          <span className="text-[10px] text-text-muted block">r/b</span>
        </div>

        <div className="hidden md:block">
          <TierBadge tier={player.tier} size="sm" />
        </div>
      </div>
    </div>
  );
}
