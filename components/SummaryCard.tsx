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
      <div className="apple-card p-6 animate-pulse space-y-4">
        <div className="h-3 bg-black/5 dark:bg-white/10 rounded-full w-24" />
        <div className="h-9 bg-black/5 dark:bg-white/10 rounded-full w-36" />
        <div className="h-3 bg-black/5 dark:bg-white/10 rounded-full w-44" />
      </div>
    );
  }

  return (
    <div className="apple-card p-6 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase font-medium text-text-secondary tracking-wider">{label}</span>
        {badge && (
          <span className="text-[11px] font-mono font-medium px-2.5 py-0.5 rounded-full bg-soft-blue text-primary">
            {badge}
          </span>
        )}
      </div>
      <div>
        <div className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          {value}
        </div>
        {subtext && <p className="text-sm text-text-secondary mt-1.5 leading-snug">{subtext}</p>}
      </div>
    </div>
  );
}
