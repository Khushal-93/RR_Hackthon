"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { Download, ArrowUpDown, ChevronDown, ChevronUp } from "lucide-react";
import { RankingItem } from "@/lib/types";
import { TierBadge } from "./TierBadge";
import { UncertaintyBar } from "./UncertaintyBar";

interface Props {
  data: RankingItem[];
}

type SortField =
  | "rank"
  | "player_name"
  | "balls"
  | "matches"
  | "raw_rate"
  | "shrunk_rate"
  | "prob_top10"
  | "dismissal_rate_vs_exp"
  | "ipl_share_pct";

export function DataTable({ data }: Props) {
  const [sortField, setSortField] = useState<SortField>("rank");
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === "rank" || field === "player_name");
    }
    setPage(1);
  };

  const sortedData = useMemo(() => {
    const list = [...data];
    list.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (typeof aVal === "string") {
        return sortAsc
          ? (aVal as string).localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal as string);
      }
      return sortAsc
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
    return list;
  }, [data, sortField, sortAsc]);

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const pagedData = sortedData.slice((page - 1) * pageSize, page * pageSize);

  const downloadCSV = () => {
    const headers = [
      "rank",
      "role",
      "player_name",
      "balls",
      "matches",
      "raw_rate",
      "shrunk_rate",
      "lambda",
      "ci80_lower",
      "ci80_upper",
      "prob_top10",
      "dismissal_rate_vs_exp",
      "ipl_share_pct",
      "t20i_share_pct",
      "tier",
    ];
    const rows = sortedData.map((p) =>
      [
        p.rank,
        p.role,
        `"${p.player_name}"`,
        p.balls,
        p.matches,
        p.raw_rate,
        p.shrunk_rate,
        p.lambda,
        p.ci80_lower,
        p.ci80_upper,
        p.prob_top10,
        p.dismissal_rate_vs_exp,
        p.ipl_share_pct,
        p.t20i_share_pct,
        `"${p.tier}"`,
      ].join(",")
    );
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `pressure_xi_rankings_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-text-muted/60" />;
    }
    return sortAsc ? (
      <ChevronUp className="w-3.5 h-3.5 text-accent-primary" />
    ) : (
      <ChevronDown className="w-3.5 h-3.5 text-accent-primary" />
    );
  };

  return (
    <div className="space-y-4">
      {/* Table toolbar */}
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-text-secondary">
          Showing {(page - 1) * pageSize + 1} &ndash; {Math.min(page * pageSize, sortedData.length)} of {sortedData.length} players
        </span>
        <button
          onClick={downloadCSV}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-border-medium bg-surface hover:bg-surface-subtle text-text-primary transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Desktop & Tablet Table Container */}
      <div className="overflow-x-auto border border-border-light rounded-lg bg-surface">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-border-light bg-surface-subtle/80 font-mono text-[11px] text-text-secondary uppercase">
              <th className="py-3 px-3 cursor-pointer" onClick={() => handleSort("rank")}>
                <div className="flex items-center gap-1">
                  <span>#</span>
                  {renderSortIcon("rank")}
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer" onClick={() => handleSort("player_name")}>
                <div className="flex items-center gap-1">
                  <span>Player</span>
                  {renderSortIcon("player_name")}
                </div>
              </th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("balls")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Balls</span>
                  {renderSortIcon("balls")}
                </div>
              </th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("matches")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Mat</span>
                  {renderSortIcon("matches")}
                </div>
              </th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("raw_rate")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Raw r/b</span>
                  {renderSortIcon("raw_rate")}
                </div>
              </th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("shrunk_rate")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Shrunk Rating</span>
                  {renderSortIcon("shrunk_rate")}
                </div>
              </th>
              <th className="py-3 px-4 text-center">80% Interval</th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("prob_top10")}>
                <div className="flex items-center justify-end gap-1">
                  <span>P(Top-10)</span>
                  {renderSortIcon("prob_top10")}
                </div>
              </th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("dismissal_rate_vs_exp")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Out vs Exp</span>
                  {renderSortIcon("dismissal_rate_vs_exp")}
                </div>
              </th>
              <th className="py-3 px-3 text-right cursor-pointer" onClick={() => handleSort("ipl_share_pct")}>
                <div className="flex items-center justify-end gap-1">
                  <span>IPL%</span>
                  {renderSortIcon("ipl_share_pct")}
                </div>
              </th>
              <th className="py-3 px-4 text-center">Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-light/50 font-mono">
            {pagedData.map((player) => {
              const isPositive = player.shrunk_rate >= 0;
              return (
                <tr key={player.player_id} className="hover:bg-surface-subtle transition-colors group">
                  <td className="py-2.5 px-3 font-bold text-text-secondary group-hover:text-text-primary">
                    {player.rank}
                  </td>
                  <td className="py-2.5 px-4 font-sans font-bold text-text-primary group-hover:text-accent-primary">
                    <Link href={`/players/${player.player_id}/`} className="hover:underline">
                      {player.player_name}
                    </Link>
                  </td>
                  <td className="py-2.5 px-3 text-right text-text-secondary">{player.balls}</td>
                  <td className="py-2.5 px-3 text-right text-text-secondary">{player.matches}</td>
                  <td className="py-2.5 px-3 text-right text-text-secondary">
                    {player.raw_rate >= 0 ? `+${player.raw_rate.toFixed(3)}` : player.raw_rate.toFixed(3)}
                  </td>
                  <td className="py-2.5 px-3 text-right font-bold">
                    <span className={isPositive ? "text-accent-success" : "text-accent-danger"}>
                      {isPositive ? `+${player.shrunk_rate.toFixed(3)}` : player.shrunk_rate.toFixed(3)}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    <UncertaintyBar
                      lower={player.ci80_lower}
                      upper={player.ci80_upper}
                      point={player.shrunk_rate}
                      width="w-24"
                    />
                  </td>
                  <td className="py-2.5 px-3 text-right text-text-secondary">
                    {(player.prob_top10 * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-3 text-right text-text-secondary">
                    {player.dismissal_rate_vs_exp >= 0
                      ? `+${(player.dismissal_rate_vs_exp * 100).toFixed(1)}%`
                      : `${(player.dismissal_rate_vs_exp * 100).toFixed(1)}%`}
                  </td>
                  <td className="py-2.5 px-3 text-right text-text-secondary">
                    {player.ipl_share_pct.toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-4 text-center font-sans">
                    <TierBadge tier={player.tier} size="sm" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs font-mono pt-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded border border-border-medium bg-surface hover:bg-surface-subtle disabled:opacity-40 transition-colors"
          >
            &larr; Previous
          </button>
          <span className="text-text-muted">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 rounded border border-border-medium bg-surface hover:bg-surface-subtle disabled:opacity-40 transition-colors"
          >
            Next &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
