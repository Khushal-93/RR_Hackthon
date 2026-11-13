import React from "react";
import { ShieldCheck, Award, MinusCircle, AlertCircle } from "lucide-react";

interface Props {
  tier: string;
  size?: "sm" | "md";
}

export function TierBadge({ tier, size = "md" }: Props) {
  let icon = <MinusCircle className="w-3 h-3" />;
  let colorClasses = "bg-slate-800 text-slate-300 border-slate-600";
  let label = tier;

  if (tier.includes("Tier 1") || tier.includes("Elite")) {
    icon = <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
    colorClasses = "bg-emerald-950/60 text-emerald-300 border-emerald-500/40";
  } else if (tier.includes("Tier 2") || tier.includes("Quality") || tier.includes("Above")) {
    icon = <Award className="w-3.5 h-3.5 text-sky-400" />;
    colorClasses = "bg-sky-950/60 text-sky-300 border-sky-500/40";
  } else if (tier.includes("Tier 3") || tier.includes("Average") || tier.includes("Baseline")) {
    icon = <MinusCircle className="w-3 h-3 text-slate-400" />;
    colorClasses = "bg-slate-800/80 text-slate-300 border-slate-600/50";
  } else if (tier.includes("Tier 4") || tier.includes("Below")) {
    icon = <AlertCircle className="w-3.5 h-3.5 text-rose-400" />;
    colorClasses = "bg-rose-950/60 text-rose-300 border-rose-500/40";
  }

  const padding = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-medium rounded border ${colorClasses} ${padding} transition-colors`}
      title={`Confidence Tier: ${tier}`}
    >
      <span aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </span>
  );
}
