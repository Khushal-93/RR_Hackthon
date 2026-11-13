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
    <div className="flex items-center justify-between p-3.5 rounded-2xl border border-border-light bg-surface hover:bg-black/[0.02] dark:hover:bg-white/[0.04] transition-all duration-300 hover:translate-y-[-1px] group">
      {/* Rank and Player Identity */}
      <div className="flex items-center gap-3.5 min-w-0 flex-1">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center font-mono text-xs font-bold shrink-0 ${
            rank === 1
              ? "bg-gradient-to-tr from-[#2B4ACB] to-[#FF5C93] text-white shadow-sm"
              : rank <= 3
              ? "bg-soft-blue text-primary font-bold"
              : "bg-black/5 dark:bg-white/10 text-text-secondary"
          }`}
        >
          {rank}
        </div>

        <div className="min-w-0">
          <Link
            href={`/players/${player.player_id}/`}
            className="font-semibold text-[15px] text-text-primary group-hover:text-primary transition-colors truncate block focus:outline-none focus:underline"
          >
            {player.player_name}
          </Link>
          <div className="text-xs text-text-secondary flex items-center gap-2">
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
            width="w-24 lg:w-28"
          />
        </div>

        <div className="font-mono min-w-[74px]">
          <span className={`text-[15px] font-bold ${isPositive ? "text-primary" : "text-secondary"}`}>
            {isPositive ? `+${player.shrunk_rate.toFixed(3)}` : player.shrunk_rate.toFixed(3)}
          </span>
          <span className="text-[11px] text-text-muted block">r/b</span>
        </div>

        <div className="hidden md:block">
          <TierBadge tier={player.tier} size="sm" />
        </div>
      </div>
    </div>
  );
}
