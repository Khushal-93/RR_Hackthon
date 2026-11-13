"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { LeverageByOverItem } from "@/lib/types";

interface Props {
  data: LeverageByOverItem[];
}

export function LeverageByOverChart({ data }: Props) {
  return (
    <div className="w-full h-[320px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="over"
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            tickFormatter={(val) => `Ov ${val}`}
          />
          <YAxis
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            domain={[0.5, 2.0]}
            tickFormatter={(val) => val.toFixed(1)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              borderColor: "#475569",
              borderRadius: "6px",
              fontSize: "12px",
              fontFamily: "monospace",
              color: "#f8fafc",
            }}
            formatter={(value: any, name: any) => [
              `${Number(value).toFixed(3)} LI`,
              name === "innings_1_mean" ? "Innings 1 (Setting)" : "Innings 2 (Chasing)",
            ]}
            labelFormatter={(label) => `Over ${label}`}
          />
          <Legend
            verticalAlign="top"
            height={36}
            formatter={(value) => (
              <span className="text-xs font-mono text-text-secondary">
                {value === "innings_1_mean" ? "Innings 1 (Powerplay spike)" : "Innings 2 (Escalating death)"}
              </span>
            )}
          />
          <ReferenceLine y={1.0} stroke="#64748b" strokeDasharray="3 3" label={{ value: "Baseline LI = 1.0", fill: "#94a3b8", fontSize: 10 }} />
          <Line
            type="monotone"
            dataKey="innings_1_mean"
            stroke="#fbbf24"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#fbbf24" }}
            activeDot={{ r: 5 }}
            name="innings_1_mean"
          />
          <Line
            type="monotone"
            dataKey="innings_2_mean"
            stroke="#38bdf8"
            strokeWidth={2.5}
            dot={{ r: 3, fill: "#38bdf8" }}
            activeDot={{ r: 5 }}
            name="innings_2_mean"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LeverageByOverTable({ data }: Props) {
  return (
    <table className="w-full text-left text-xs font-mono border-collapse">
      <thead>
        <tr className="border-b border-border-light bg-surface-subtle text-text-secondary uppercase text-[10px]">
          <th className="py-2 px-3">Over</th>
          <th className="py-2 px-3 text-right">Innings 1 (Mean LI)</th>
          <th className="py-2 px-3 text-right">Innings 1 (StdErr)</th>
          <th className="py-2 px-3 text-right">Innings 2 (Mean LI)</th>
          <th className="py-2 px-3 text-right">Innings 2 (StdErr)</th>
          <th className="py-2 px-3 text-right">Overall Mean</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border-light/40">
        {data.map((row) => (
          <tr key={row.over} className="hover:bg-surface-subtle/50">
            <td className="py-1.5 px-3 font-bold">Over {row.over}</td>
            <td className="py-1.5 px-3 text-right text-accent-batter">{row.innings_1_mean.toFixed(3)}</td>
            <td className="py-1.5 px-3 text-right text-text-muted">&plusmn;{row.innings_1_stderr.toFixed(3)}</td>
            <td className="py-1.5 px-3 text-right text-accent-bowler">{row.innings_2_mean.toFixed(3)}</td>
            <td className="py-1.5 px-3 text-right text-text-muted">&plusmn;{row.innings_2_stderr.toFixed(3)}</td>
            <td className="py-1.5 px-3 text-right font-bold">{row.overall_mean.toFixed(3)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
