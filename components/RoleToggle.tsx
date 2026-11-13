import React from "react";
import { PlayerRole } from "@/lib/types";

interface Props {
  role: PlayerRole;
  onChange: (role: PlayerRole) => void;
  batterCount?: number;
  bowlerCount?: number;
}

export function RoleToggle({ role, onChange, batterCount = 118, bowlerCount = 125 }: Props) {
  return (
    <div
      role="tablist"
      aria-label="Filter player role"
      className="inline-flex p-1 bg-surface-subtle border border-border-medium rounded-lg"
    >
      <button
        role="tab"
        aria-selected={role === "batter"}
        onClick={() => onChange("batter")}
        className={`px-4 py-2 text-xs font-mono rounded-md font-bold transition-all ${
          role === "batter"
            ? "bg-accent-batter text-slate-950 shadow-sm"
            : "text-text-secondary hover:text-text-primary hover:bg-surface/50"
        }`}
      >
        Batters ({batterCount})
      </button>

      <button
        role="tab"
        aria-selected={role === "bowler"}
        onClick={() => onChange("bowler")}
        className={`px-4 py-2 text-xs font-mono rounded-md font-bold transition-all ${
          role === "bowler"
            ? "bg-accent-bowler text-slate-950 shadow-sm"
            : "text-text-secondary hover:text-text-primary hover:bg-surface/50"
        }`}
      >
        Bowlers ({bowlerCount})
      </button>
    </div>
  );
}
