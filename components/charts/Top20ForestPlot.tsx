"use client";

import React from "react";
import Link from "next/link";
import { RankingItem } from "@/lib/types";

interface Props {
  players: RankingItem[];
}

export function Top20ForestPlot({ players }: Props) {
  const top20 = players.slice(0, 20);
  const minVal = -0.15;
  const maxVal = 0.55;
  const range = maxVal - minVal;

  const toPct = (val: number) => `${((Math.max(minVal, Math.min(maxVal, val)) - minVal) / range) * 100}%`;
  const zeroPct = toPct(0);

  return (
    <div className="space-y-2 py-2">
      {/* Scale header */}
      <div className="relative h-6 border-b border-border-light text-[10px] font-mono text-text-muted flex justify-between px-2">
        <span>-0.10</span>
        <span style={{ position: "absolute", left: zeroPct, transform: "translateX(-50%)" }}>
          0.00 (Baseline)
        </span>
        <span>+0.20</span>
        <span>+0.40</span>
        <span>+0.50 r/b</span>
      </div>

      <div className="space-y-1.5 font-mono">
        {top20.map((player) => {
          const leftPct = toPct(player.ci80_lower);
          const rightPct = toPct(player.ci80_upper);
          const widthPct = `${((player.ci80_upper - player.ci80_lower) / range) * 100}%`;
          const pointPct = toPct(player.shrunk_rate);
          const isPositive = player.shrunk_rate >= 0;

          return (
            <div
              key={player.player_id}
              className="flex items-center gap-3 text-xs p-1.5 rounded hover:bg-surface-subtle transition-colors group"
            >
              {/* Player rank & name */}
              <div className="w-40 sm:w-48 truncate shrink-0 flex items-center gap-2">
                <span className="w-5 text-text-muted font-bold">#{player.rank}</span>
                <Link
                  href={`/players/${player.player_id}/`}
                  className="font-bold text-text-primary group-hover:text-accent-primary truncate focus:underline"
                >
                  {player.player_name}
                </Link>
              </div>

              {/* Graphical Interval Bar Track */}
              <div className="flex-1 relative h-5 bg-surface-subtle/50 rounded flex items-center overflow-hidden">
                {/* Zero line */}
                <div
                  className="absolute top-0 bottom-0 w-[1px] bg-border-strong z-0"
                  style={{ left: zeroPct }}
                  aria-hidden="true"
                />

                {/* 80% CI interval track */}
                <div
                  className="absolute top-1.5 bottom-1.5 bg-border-strong/80 rounded-sm z-10"
                  style={{ left: leftPct, width: widthPct }}
                  aria-hidden="true"
                  title={`80% CI: [${player.ci80_lower >= 0 ? "+" : ""}${player.ci80_lower.toFixed(3)}, ${player.ci80_upper >= 0 ? "+" : ""}${player.ci80_upper.toFixed(3)}]`}
                />

                {/* Point estimate dot */}
                <div
                  className={`absolute top-1 bottom-1 w-2.5 h-2.5 rounded-full z-20 -ml-1 border ${
                    isPositive ? "bg-accent-success border-emerald-300" : "bg-accent-danger border-rose-300"
                  }`}
                  style={{ left: pointPct, top: "50%", transform: "translateY(-50%)" }}
                  aria-hidden="true"
                  title={`Shrunk rating: ${player.shrunk_rate >= 0 ? "+" : ""}${player.shrunk_rate.toFixed(3)}`}
                />
              </div>

              {/* Exact numeric readout */}
              <div className="w-20 text-right shrink-0">
                <span className={`font-bold ${isPositive ? "text-accent-success" : "text-accent-danger"}`}>
                  {isPositive ? `+${player.shrunk_rate.toFixed(3)}` : player.shrunk_rate.toFixed(3)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function Top20ForestTable({ players }: Props) {
  const top20 = players.slice(0, 20);
  return (
    <table className="w-full text-left text-xs font-mono border-collapse">
      <thead>
        <tr className="border-b border-border-light bg-surface-subtle text-text-secondary uppercase text-[10px]">
          <th className="py-2 px-3">Rank</th>
          <th className="py-2 px-3">Player</th>
          <th className="py-2 px-3 text-right">Shrunk Rating</th>
          <th className="py-2 px-3 text-center">80% Credible Interval</th>
          <th className="py-2 px-3 text-right">P(Top-10)</th>
          <th className="py-2 px-3 text-center">Tier</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border-light/40">
        {top20.map((p) => (
          <tr key={p.player_id} className="hover:bg-surface-subtle/50">
            <td className="py-1.5 px-3 font-bold">#{p.rank}</td>
            <td className="py-1.5 px-3 font-sans font-bold text-text-primary">
              <Link href={`/players/${p.player_id}/`} className="hover:underline">
                {p.player_name}
              </Link>
            </td>
            <td className="py-1.5 px-3 text-right font-bold">
              {p.shrunk_rate >= 0 ? `+${p.shrunk_rate.toFixed(3)}` : p.shrunk_rate.toFixed(3)}
            </td>
            <td className="py-1.5 px-3 text-center text-text-secondary">
              [{p.ci80_lower >= 0 ? `+${p.ci80_lower.toFixed(3)}` : p.ci80_lower.toFixed(3)},{" "}
              {p.ci80_upper >= 0 ? `+${p.ci80_upper.toFixed(3)}` : p.ci80_upper.toFixed(3)}]
            </td>
            <td className="py-1.5 px-3 text-right">{(p.prob_top10 * 100).toFixed(0)}%</td>
            <td className="py-1.5 px-3 text-center font-sans text-[11px]">{p.tier}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
