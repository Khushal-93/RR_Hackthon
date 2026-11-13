"use client";

import React from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { RankingItem } from "@/lib/types";

interface Props {
  players: RankingItem[];
}

export function ScatterPlot({ players }: Props) {
  const chartData = players.map((p) => ({
    name: p.player_name,
    balls: p.balls,
    shrunk_rate: p.shrunk_rate,
    matches: p.matches,
    tier: p.tier,
    rank: p.rank,
    fill: p.tier.includes("Tier 1") ? "#34d399" : p.tier.includes("Tier 2") ? "#38bdf8" : "#94a3b8",
  }));

  return (
    <div className="w-full h-[320px]">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            type="number"
            dataKey="balls"
            name="High-Pressure Balls"
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            unit=" b"
            domain={[140, "auto"]}
          />
          <YAxis
            type="number"
            dataKey="shrunk_rate"
            name="Shrunk Rating"
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            unit=" r/b"
            domain={[-0.2, 0.45]}
            tickFormatter={(val) => (val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2))}
          />
          <ZAxis type="number" dataKey="matches" range={[20, 140]} name="Matches" />
          <ReferenceLine y={0} stroke="#64748b" strokeDasharray="3 3" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-slate-900 border border-border-medium p-2.5 rounded shadow-lg text-xs font-mono space-y-1 text-slate-100">
                    <div className="font-bold text-accent-primary">
                      #{data.rank} {data.name}
                    </div>
                    <div>Rating: {data.shrunk_rate >= 0 ? `+${data.shrunk_rate.toFixed(3)}` : data.shrunk_rate.toFixed(3)} r/b</div>
                    <div className="text-text-muted">{data.balls} HP balls &bull; {data.matches} matches</div>
                    <div className="text-[10px] text-text-secondary">{data.tier}</div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter data={chartData} fill="#38bdf8" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ScatterTable({ players }: Props) {
  // Quartile summary of balls vs shrunk rate
  const sortedByBalls = [...players].sort((a, b) => a.balls - b.balls);
  const q1 = sortedByBalls.slice(0, Math.floor(players.length * 0.25));
  const q2 = sortedByBalls.slice(Math.floor(players.length * 0.25), Math.floor(players.length * 0.5));
  const q3 = sortedByBalls.slice(Math.floor(players.length * 0.5), Math.floor(players.length * 0.75));
  const q4 = sortedByBalls.slice(Math.floor(players.length * 0.75));

  const quartiles = [
    { label: "Q1: 150 - 220 balls (Floor Qualifiers)", group: q1 },
    { label: "Q2: 221 - 340 balls (Moderate Sample)", group: q2 },
    { label: "Q3: 341 - 520 balls (High Sample)", group: q3 },
    { label: "Q4: 521+ balls (Veterans)", group: q4 },
  ];

  return (
    <table className="w-full text-left text-xs font-mono border-collapse">
      <thead>
        <tr className="border-b border-border-light bg-surface-subtle text-text-secondary uppercase text-[10px]">
          <th className="py-2 px-3">Sample Volume Band</th>
          <th className="py-2 px-3 text-right">Players</th>
          <th className="py-2 px-3 text-right">Mean Lambda</th>
          <th className="py-2 px-3 text-right">Mean Raw Rate</th>
          <th className="py-2 px-3 text-right">Mean Shrunk Rating</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border-light/40">
        {quartiles.map((q) => {
          const meanLam = q.group.reduce((acc, p) => acc + p.lambda, 0) / (q.group.length || 1);
          const meanRaw = q.group.reduce((acc, p) => acc + p.raw_rate, 0) / (q.group.length || 1);
          const meanShrunk = q.group.reduce((acc, p) => acc + p.shrunk_rate, 0) / (q.group.length || 1);
          return (
            <tr key={q.label} className="hover:bg-surface-subtle/50">
              <td className="py-2 px-3 font-bold text-text-primary">{q.label}</td>
              <td className="py-2 px-3 text-right">{q.group.length}</td>
              <td className="py-2 px-3 text-right text-accent-primary">{meanLam.toFixed(3)}</td>
              <td className="py-2 px-3 text-right">{meanRaw >= 0 ? `+${meanRaw.toFixed(3)}` : meanRaw.toFixed(3)}</td>
              <td className="py-2 px-3 text-right font-bold text-accent-success">
                {meanShrunk >= 0 ? `+${meanShrunk.toFixed(3)}` : meanShrunk.toFixed(3)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
