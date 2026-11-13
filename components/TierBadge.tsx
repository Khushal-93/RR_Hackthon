import React from "react";
import { ShieldCheck, Award, MinusCircle, AlertCircle } from "lucide-react";

interface Props {
  tier: string;
  size?: "sm" | "md";
}

export function TierBadge({ tier, size = "md" }: Props) {
  let icon = <MinusCircle className="w-3 h-3" />;
  let colorClasses = "bg-black/5 dark:bg-white/10 text-text-secondary border-transparent";
  let label = tier;

  if (tier.includes("Tier 1") || tier.includes("Elite")) {
    icon = <ShieldCheck className="w-3.5 h-3.5 text-secondary" />;
    colorClasses = "bg-soft-pink text-secondary dark:bg-secondary/20 dark:text-secondary border-secondary/30";
  } else if (tier.includes("Tier 2") || tier.includes("Quality") || tier.includes("Above")) {
    icon = <Award className="w-3.5 h-3.5 text-primary" />;
    colorClasses = "bg-soft-blue text-primary dark:bg-primary/20 dark:text-primary border-primary/30";
  } else if (tier.includes("Tier 3") || tier.includes("Average") || tier.includes("Baseline")) {
    icon = <MinusCircle className="w-3 h-3 text-text-muted" />;
    colorClasses = "bg-black/5 dark:bg-white/10 text-text-secondary border-border-light";
  } else if (tier.includes("Tier 4") || tier.includes("Below")) {
    icon = <AlertCircle className="w-3.5 h-3.5 text-red-500" />;
    colorClasses = "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400 border-red-200 dark:border-red-900";
  }

  const padding = size === "sm" ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${colorClasses} ${padding} transition-colors`}
      title={`Confidence Tier: ${tier}`}
    >
      <span aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </span>
  );
}
