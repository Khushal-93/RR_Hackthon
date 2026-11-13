import React from "react";
import { SearchX } from "lucide-react";

interface Props {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

export function EmptyState({
  title = "No results found",
  description = "No players match the selected filters. Try broadening your criteria.",
  actionText = "Reset Filters",
  onAction,
}: Props) {
  return (
    <div className="py-16 px-4 text-center border border-dashed border-border-medium rounded-lg bg-surface flex flex-col items-center justify-center space-y-3">
      <div className="w-10 h-10 rounded-full bg-surface-subtle flex items-center justify-center text-text-muted">
        <SearchX className="w-5 h-5" />
      </div>
      <h4 className="font-bold text-sm text-text-primary">{title}</h4>
      <p className="text-xs text-text-secondary max-w-sm">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-2 px-3 py-1.5 text-xs font-mono font-medium rounded border border-border-strong bg-surface hover:bg-surface-subtle text-text-primary transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
