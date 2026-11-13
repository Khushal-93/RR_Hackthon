import React from "react";
import Link from "next/link";
import { AlertTriangle, ArrowRight } from "lucide-react";

interface Props {
  title?: string;
  message?: string;
  linkHref?: string;
  linkLabel?: string;
}

export function WarningBanner({
  title = "Honest Limitations & Signal Reliability",
  message = "Out-of-time rank correlation across disjoint seasons is modest (rho = +0.25 for batters, +0.29 for bowlers). Ratings describe historical efficiency in high-pressure corridors, not deterministic traits.",
  linkHref = "/method/",
  linkLabel = "Read full methodology & repeatability audit",
}: Props) {
  return (
    <div
      role="region"
      aria-label="Scientific Limitations Warning"
      className="p-4 sm:p-5 rounded-lg border border-amber-500/40 bg-amber-950/20 text-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-accent-warning shrink-0 mt-0.5" aria-hidden="true" />
        <div className="space-y-1">
          <div className="font-bold text-sm text-text-primary">{title}</div>
          <p className="text-xs text-text-secondary leading-relaxed max-w-3xl">{message}</p>
        </div>
      </div>

      {linkHref && (
        <Link
          href={linkHref}
          className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-accent-warning hover:text-amber-300 underline shrink-0"
        >
          <span>{linkLabel}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      )}
    </div>
  );
}
