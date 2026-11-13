import React from "react";

interface Props {
  label: string;
  value: string | number;
  subtext?: string;
  badge?: string;
  isLoading?: boolean;
}

export function SummaryCard({ label, value, subtext, badge, isLoading = false }: Props) {
  if (isLoading) {
    return (
      <div className="bg-surface border border-border-light rounded-lg p-5 animate-pulse space-y-3">
        <div className="h-3 bg-surface-subtle rounded w-24" />
        <div className="h-8 bg-surface-subtle rounded w-32" />
        <div className="h-3 bg-surface-subtle rounded w-40" />
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border-light rounded-lg p-5 hover:border-border-medium transition-colors flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs uppercase text-text-secondary tracking-wider">{label}</span>
        {badge && (
          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface-subtle border border-border-light text-text-muted">
            {badge}
          </span>
        )}
      </div>
      <div>
        <div className="text-2xl sm:text-3xl font-extrabold font-mono tracking-tight text-text-primary">
          {value}
        </div>
        {subtext && <p className="text-xs text-text-secondary mt-1">{subtext}</p>}
      </div>
    </div>
  );
}
