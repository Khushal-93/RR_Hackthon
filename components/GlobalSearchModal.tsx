"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Search, X, User } from "lucide-react";
import { RankingItem } from "@/lib/types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalSearchModal({ isOpen, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [players, setPlayers] = useState<RankingItem[]>([]);
  const [filtered, setFiltered] = useState<RankingItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      fetch("/data/rankings.json")
        .then((res) => res.json())
        .then((data: RankingItem[]) => {
          setPlayers(data);
          setFiltered(data.slice(0, 8));
        })
        .catch(() => {});
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
    }
  }, [isOpen]);

  useEffect(() => {
    if (!query.trim()) {
      setFiltered(players.slice(0, 8));
      return;
    }
    const q = query.toLowerCase().trim();
    const matches = players.filter(
      (p) =>
        p.player_name.toLowerCase().includes(q) ||
        p.tier.toLowerCase().includes(q) ||
        p.role.toLowerCase().startsWith(q)
    );
    setFiltered(matches.slice(0, 10));
  }, [query, players]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="global-search-title"
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-surface border border-border-medium rounded-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-border-light bg-surface-subtle">
          <Search className="w-4 h-4 text-text-muted mr-3" />
          <input
            ref={inputRef}
            id="global-search-title"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search eligible players (e.g. Bumrah, Sooryavanshi, Narine)..."
            className="w-full bg-transparent text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="p-1 text-text-muted hover:text-text-primary mr-2"
              aria-label="Clear search input"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <kbd className="hidden sm:inline-block bg-surface px-2 py-0.5 text-[10px] font-mono rounded border border-border-light text-text-muted">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-border-light/40">
          {filtered.length > 0 ? (
            filtered.map((player) => (
              <Link
                key={player.player_id}
                href={`/players/${player.player_id}/`}
                onClick={onClose}
                className="flex items-center justify-between p-3 rounded hover:bg-surface-subtle transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-surface-subtle border border-border-medium flex items-center justify-center font-mono text-xs font-bold text-text-secondary group-hover:text-accent-primary">
                    #{player.rank}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-text-primary group-hover:text-accent-primary">
                      {player.player_name}
                    </div>
                    <div className="text-xs text-text-secondary font-mono flex items-center gap-2">
                      <span className="capitalize">{player.role}</span>
                      <span>&bull;</span>
                      <span>{player.balls} HP balls</span>
                      <span>&bull;</span>
                      <span>{player.tier}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right font-mono">
                  <div className={`text-sm font-bold ${player.shrunk_rate >= 0 ? "text-accent-success" : "text-accent-danger"}`}>
                    {player.shrunk_rate >= 0 ? `+${player.shrunk_rate.toFixed(3)}` : player.shrunk_rate.toFixed(3)}
                  </div>
                  <div className="text-[10px] text-text-muted">shrunk r/b</div>
                </div>
              </Link>
            ))
          ) : (
            <div className="py-12 text-center text-text-secondary font-mono text-xs">
              No eligible players found matching &ldquo;{query}&rdquo;.
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 border-t border-border-light bg-surface-subtle text-[11px] font-mono text-text-muted flex justify-between">
          <span>243 eligible players (118 batters, 125 bowlers)</span>
          <span>Press ESC to close</span>
        </div>
      </div>
    </div>
  );
}
