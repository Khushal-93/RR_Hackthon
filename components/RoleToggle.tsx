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
      className="inline-flex p-1 bg-black/5 dark:bg-white/10 rounded-full border border-border-light"
    >
      <button
        role="tab"
        aria-selected={role === "batter"}
        onClick={() => onChange("batter")}
        className={`px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 ${
          role === "batter"
            ? "bg-secondary text-white shadow-sm"
            : "text-text-secondary hover:text-text-primary"
        }`}
      >
        Batters ({batterCount})
      </button>

      <button
        role="tab"
        aria-selected={role === "bowler"}
        onClick={() => onChange("bowler")}
        className={`px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 ${
          role === "bowler"
            ? "bg-primary text-white shadow-sm"
            : "text-text-secondary hover:text-text-primary"
        }`}
      >
        Bowlers ({bowlerCount})
      </button>
    </div>
  );
}
