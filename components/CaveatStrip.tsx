import React from "react";

export function CaveatStrip() {
  return (
    <aside
      aria-label="Dataset Notice"
      className="w-full bg-slate-900 border-b border-border-light text-center py-1.5 px-4 text-xs font-mono text-text-secondary tracking-wide flex items-center justify-center gap-2"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-accent-warning inline-block" aria-hidden="true" />
      <span>Descriptive historical ratings, not predictions.</span>
    </aside>
  );
}
