"use client";

import React, { useState } from "react";
import { LeverageHeatmapData } from "@/lib/types";

interface Props {
  data: LeverageHeatmapData;
}

export function LeverageHeatmapView({ data }: Props) {
  const [activeInnings, setActiveInnings] = useState<1 | 2>(1);
  const grid = activeInnings === 1 ? data.innings_1 : data.innings_2;

  // Compute color based on leverage value (0.5 to 2.5)
  const getCellBg = (val: number | null | undefined) => {
    if (val === null || val === undefined) return "bg-surface-subtle/20 text-text-muted/30";
    if (val >= 1.8) return "bg-rose-950 text-rose-300 font-bold border-rose-800";
    if (val >= 1.4) return "bg-amber-950 text-amber-300 font-bold border-amber-800";
    if (val >= 1.1) return "bg-sky-950 text-sky-300 border-sky-800";
    if (val >= 0.8) return "bg-slate-800 text-slate-300 border-slate-700";
    return "bg-slate-900 text-slate-500 border-slate-800";
  };

  return (
    <div className="space-y-4">
      {/* Innings Selector Tabs */}
      <div className="flex items-center justify-between">
        <div className="inline-flex p-1 bg-surface-subtle border border-border-medium rounded-lg text-xs font-mono">
          <button
            onClick={() => setActiveInnings(1)}
            className={`px-3 py-1.5 rounded-md font-bold transition-all ${
              activeInnings === 1 ? "bg-accent-batter text-slate-950" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Innings 1 (Setting Target)
          </button>
          <button
            onClick={() => setActiveInnings(2)}
            className={`px-3 py-1.5 rounded-md font-bold transition-all ${
              activeInnings === 2 ? "bg-accent-bowler text-slate-950" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Innings 2 (Chasing Target)
          </button>
        </div>

        <div className="text-[11px] font-mono text-text-muted hidden sm:block">
          Cell value: Mean Leverage Index (LI &ge; 1.25 is High Pressure)
        </div>
      </div>

      {/* 20 Overs x 10 Wickets In Hand Grid */}
      <div className="overflow-x-auto border border-border-light rounded-lg bg-surface p-3">
        <table className="w-full text-center border-collapse text-[10px] font-mono">
          <thead>
            <tr className="text-text-muted">
              <th className="p-1.5 text-left text-text-secondary font-bold">Over</th>
              {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map((wih) => (
                <th key={wih} className="p-1.5 font-bold">
                  {wih} WIH
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {grid.map((row) => (
              <tr key={row.over}>
                <td className="p-1.5 text-left font-bold text-text-secondary">Ov {row.over}</td>
                {[10, 9, 8, 7, 6, 5, 4, 3, 2, 1].map((wih) => {
                  const val = row[`wih_${wih}`] as number | null | undefined;
                  return (
                    <td
                      key={wih}
                      className={`p-1.5 rounded border ${getCellBg(val)} transition-colors`}
                      title={`Over ${row.over}, ${wih} Wickets in Hand: ${val ? `${val} LI` : "No deliveries"}`}
                    >
                      {val ? val.toFixed(2) : "-"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tactical Takeaway Note Panel */}
      <div className="p-4 rounded-lg bg-surface border border-border-light text-xs text-text-secondary leading-relaxed">
        <div className="font-bold text-text-primary font-mono text-xs mb-1">
          Tactical Dynamics & Phase Concentration
        </div>
        <p>{data.summary.tactical_note}</p>
      </div>
    </div>
  );
}
