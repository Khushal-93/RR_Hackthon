"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { ValidationData } from "@/lib/types";

interface Props {
  deciles: ValidationData["calibration_deciles"];
}

export function CalibrationPlot({ deciles }: Props) {
  const chartData = deciles.map((d) => ({
    pred: d.pred_wp,
    obs: d.obs_win_rate,
    ideal: d.pred_wp,
    count: d.count,
  }));

  return (
    <div className="w-full h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="pred"
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
            label={{ value: "Predicted Win Probability", position: "insideBottom", offset: -5, fill: "#94a3b8", fontSize: 10 }}
          />
          <YAxis
            stroke="#94a3b8"
            fontSize={11}
            tickLine={false}
            domain={[0, 1]}
            tickFormatter={(val) => `${(val * 100).toFixed(0)}%`}
            label={{ value: "Observed Win Rate", angle: -90, position: "insideLeft", offset: 15, fill: "#94a3b8", fontSize: 10 }}
          />
          <ReferenceLine stroke="#64748b" strokeDasharray="3 3" />
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
              `${(Number(value) * 100).toFixed(1)}%`,
              name === "obs" ? "Observed Match Win Rate" : "Ideal Calibration",
            ]}
            labelFormatter={(label) => `Predicted WP: ${(Number(label) * 100).toFixed(0)}%`}
          />
          <Line
            type="monotone"
            dataKey="ideal"
            stroke="#64748b"
            strokeDasharray="4 4"
            strokeWidth={1.5}
            dot={false}
            name="ideal"
          />
          <Line
            type="monotone"
            dataKey="obs"
            stroke="#38bdf8"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "#38bdf8" }}
            name="obs"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CalibrationTable({ deciles }: Props) {
  return (
    <table className="w-full text-left text-xs font-mono border-collapse">
      <thead>
        <tr className="border-b border-border-light bg-surface-subtle text-text-secondary uppercase text-[10px]">
          <th className="py-2 px-3">Decile Bin</th>
          <th className="py-2 px-3 text-right">Predicted WP</th>
          <th className="py-2 px-3 text-right">Observed Win Rate</th>
          <th className="py-2 px-3 text-right">Absolute Error</th>
          <th className="py-2 px-3 text-right">Deliveries Count</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border-light/40">
        {deciles.map((d) => (
          <tr key={d.decile} className="hover:bg-surface-subtle/50">
            <td className="py-1.5 px-3 font-bold">Decile {d.decile}</td>
            <td className="py-1.5 px-3 text-right text-text-secondary">{(d.pred_wp * 100).toFixed(0)}%</td>
            <td className="py-1.5 px-3 text-right font-bold text-accent-primary">
              {(d.obs_win_rate * 100).toFixed(1)}%
            </td>
            <td className="py-1.5 px-3 text-right text-text-muted">
              {Math.abs(d.obs_win_rate - d.pred_wp).toFixed(3)}
            </td>
            <td className="py-1.5 px-3 text-right text-text-secondary">{d.count.toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
