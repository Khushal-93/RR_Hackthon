import React from "react";
import Link from "next/link";
import { AlertCircle, ArrowRight } from "lucide-react";

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
      className="p-6 rounded-[22px] border border-secondary/30 bg-soft-pink/40 dark:bg-secondary/10 text-text-primary flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 transition-colors"
    >
      <div className="flex items-start gap-4">
        <div className="w-9 h-9 rounded-full bg-secondary/15 flex items-center justify-center shrink-0 mt-0.5">
          <AlertCircle className="w-5 h-5 text-secondary" aria-hidden="true" />
        </div>
        <div className="space-y-1">
          <div className="font-semibold text-base text-text-primary">{title}</div>
          <p className="apple-caption leading-relaxed max-w-3xl">{message}</p>
        </div>
      </div>

      {linkHref && (
        <Link
          href={linkHref}
          className="inline-flex items-center gap-1.5 font-medium text-sm text-secondary hover:text-secondary-dark transition-colors shrink-0"
        >
          <span>{linkLabel}</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}
