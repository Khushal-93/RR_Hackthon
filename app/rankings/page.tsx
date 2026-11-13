"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Filter, Search, RotateCcw } from "lucide-react";
import { RankingItem, PlayerRole } from "@/lib/types";
import { RoleToggle } from "@/components/RoleToggle";
import { DataTable } from "@/components/DataTable";
import { ChartContainer } from "@/components/ChartContainer";
import {
  Top20ForestPlot,
  Top20ForestTable,
} from "@/components/charts/Top20ForestPlot";
import { ScatterPlot, ScatterTable } from "@/components/charts/ScatterPlot";

export default function RankingsPage() {
  const [role, setRole] = useState<PlayerRole>("batter");
  const [allPlayers, setAllPlayers] = useState<RankingItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters state
  const [minBalls, setMinBalls] = useState<number>(150);
  const [competition, setCompetition] = useState<"all" | "ipl" | "t20i">("all");
  const [paceOrSpin, setPaceOrSpin] = useState<"all" | "Pace" | "Spin">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);

  useEffect(() => {
    fetch("/data/rankings.json")
      .then((res) => res.json())
      .then((data: RankingItem[]) => {
        setAllPlayers(data);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  const resetFilters = () => {
    setMinBalls(150);
    setCompetition("all");
    setPaceOrSpin("all");
    setSearchQuery("");
  };

  const filteredPlayers = useMemo(() => {
    return allPlayers.filter((p) => {
      if (p.role !== role) return false;
      if (p.balls < minBalls) return false;

      if (competition === "ipl" && p.ipl_share_pct < 50) return false;
      if (competition === "t20i" && p.t20i_share_pct < 50) return false;

      if (role === "bowler" && paceOrSpin !== "all") {
        if (p.pace_or_spin !== paceOrSpin) return false;
      }

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        if (!p.player_name.toLowerCase().includes(q) && !p.tier.toLowerCase().includes(q)) {
          return false;
        }
      }

      return true;
    });
  }, [allPlayers, role, minBalls, competition, paceOrSpin, searchQuery]);

  const activeFiltersCount =
    (minBalls > 150 ? 1 : 0) +
    (competition !== "all" ? 1 : 0) +
    (paceOrSpin !== "all" && role === "bowler" ? 1 : 0) +
    (searchQuery.trim() ? 1 : 0);

  return (
    <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="space-y-2 border-b border-border-light pb-6">
        <span className="font-mono text-xs text-text-muted uppercase">Player Roster Explorer</span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
          Pressure Performance Rankings
        </h1>
        <p className="text-sm text-text-secondary max-w-3xl leading-relaxed">
          Comprehensive rankings of all 243 eligible players (118 batters, 125 bowlers) meeting the &ge;150 high-pressure legal balls threshold.
        </p>
      </div>

      {/* Role Toggle & Filter Controls */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <RoleToggle role={role} onChange={setRole} />

          <div className="flex items-center gap-2">
            {/* Search Input */}
            <div className="relative flex-1 sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search player or tier..."
                className="w-full pl-9 pr-3 py-1.5 text-xs font-mono bg-surface border border-border-medium rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none"
              />
            </div>

            {/* Mobile Filter Drawer Button */}
            <button
              onClick={() => setFilterDrawerOpen(!filterDrawerOpen)}
              className="lg:hidden inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono border border-border-medium rounded-lg bg-surface hover:bg-surface-subtle"
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Filters {activeFiltersCount > 0 ? `(${activeFiltersCount})` : ""}</span>
            </button>
          </div>
        </div>

        {/* Filter Toolbar (Desktop / Tablet / Mobile Drawer) */}
        <div
          className={`${
            filterDrawerOpen ? "block" : "hidden"
          } lg:flex flex-wrap items-center gap-4 p-4 rounded-lg bg-surface border border-border-light text-xs font-mono`}
        >
          {/* Min Balls Slider */}
          <div className="flex items-center gap-2">
            <span className="text-text-secondary">Min Balls:</span>
            <input
              type="range"
              min="150"
              max="600"
              step="25"
              value={minBalls}
              onChange={(e) => setMinBalls(Number(e.target.value))}
              className="w-24 accent-accent-primary"
            />
            <span className="font-bold text-text-primary w-12">{minBalls} b</span>
          </div>

          <div className="hidden lg:block w-[1px] h-4 bg-border-light" />

          {/* Competition Selector */}
          <div className="flex items-center gap-2">
            <span className="text-text-secondary">Competition:</span>
            <select
              value={competition}
              onChange={(e) => setCompetition(e.target.value as any)}
              className="bg-surface-subtle border border-border-medium rounded px-2 py-1 text-text-primary"
            >
              <option value="all">All (IPL & T20I)</option>
              <option value="ipl">IPL Heavy (&ge;50%)</option>
              <option value="t20i">T20I Heavy (&ge;50%)</option>
            </select>
          </div>

          {/* Pace / Spin (Bowlers Only) */}
          {role === "bowler" && (
            <>
              <div className="hidden lg:block w-[1px] h-4 bg-border-light" />
              <div className="flex items-center gap-2">
                <span className="text-text-secondary">Type:</span>
                <select
                  value={paceOrSpin}
                  onChange={(e) => setPaceOrSpin(e.target.value as any)}
                  className="bg-surface-subtle border border-border-medium rounded px-2 py-1 text-text-primary"
                >
                  <option value="all">All Bowlers</option>
                  <option value="Pace">Pace Bowlers</option>
                  <option value="Spin">Spin Bowlers</option>
                </select>
              </div>
            </>
          )}

          {activeFiltersCount > 0 && (
            <button
              onClick={resetFilters}
              className="inline-flex items-center gap-1 text-text-muted hover:text-text-primary ml-auto"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* c. Top-20 Forest Plot */}
      <section aria-labelledby="forest-plot-heading">
        <ChartContainer
          title={`Top 20 ${role === "batter" ? "Batters" : "Bowlers"}: Forest Plot (80% Credible Interval)`}
          subtitle="Point estimates with 80% credible bounds shrunk toward the pool mean using Empirical Bayes."
          chartView={<Top20ForestPlot players={filteredPlayers} />}
          tableView={<Top20ForestTable players={filteredPlayers} />}
        />
      </section>

      {/* d. 13-Column Sortable Data Table */}
      <section aria-labelledby="rankings-table-heading" className="space-y-3">
        <h2 id="rankings-table-heading" className="text-lg font-bold text-text-primary font-mono">
          Eligible Player Roster ({filteredPlayers.length} players)
        </h2>
        {isLoading ? (
          <div className="py-16 text-center font-mono text-xs text-text-muted">Loading roster data...</div>
        ) : (
          <DataTable data={filteredPlayers} />
        )}
      </section>

      {/* e. Rating vs Sample Size Scatter Plot */}
      <section aria-labelledby="scatter-plot-heading">
        <ChartContainer
          title={`Rating vs Sample Size: ${role === "batter" ? "Batters" : "Bowlers"}`}
          subtitle="Evaluation of volume effects. Shrinkage factor lambda pulls lower-sample qualifiers safely toward the pool mean."
          chartView={<ScatterPlot players={filteredPlayers} />}
          tableView={<ScatterTable players={filteredPlayers} />}
        />
      </section>
    </div>
  );
}
