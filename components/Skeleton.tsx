import React from "react";

interface Props {
  className?: string;
}

export function Skeleton({ className = "h-4 w-full" }: Props) {
  return (
    <div
      className={`bg-surface-subtle animate-pulse rounded ${className}`}
      aria-hidden="true"
    />
  );
}
