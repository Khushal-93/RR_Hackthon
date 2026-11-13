import React from "react";

interface Props {
  lower: number;
  upper: number;
  point: number;
  minScale?: number;
  maxScale?: number;
  width?: string;
  showLabels?: boolean;
}

export function UncertaintyBar({
  lower,
  upper,
  point,
  minScale = -0.4,
  maxScale = 0.6,
  width = "w-28",
  showLabels = false,
}: Props) {
  const clamp = (val: number) => Math.max(minScale, Math.min(maxScale, val));
  const range = maxScale - minScale;
  const toPct = (val: number) => `${((clamp(val) - minScale) / range) * 100}%`;

  const leftPct = toPct(lower);
  const rightPct = toPct(upper);
  const widthPct = `${((clamp(upper) - clamp(lower)) / range) * 100}%`;
  const pointPct = toPct(point);
  const zeroPct = toPct(0);

  return (
    <div
      className={`inline-flex flex-col gap-1 ${width}`}
      title={`80% Credible Interval: [${lower >= 0 ? "+" : ""}${lower.toFixed(3)}, ${upper >= 0 ? "+" : ""}${upper.toFixed(3)}] | Point: ${point >= 0 ? "+" : ""}${point.toFixed(3)}`}
    >
      <div className="relative h-3.5 bg-black/5 dark:bg-white/10 rounded-full flex items-center overflow-hidden border border-border-light">
        {/* Zero baseline reference line */}
        <div
          className="absolute top-0 bottom-0 w-[1.5px] bg-border-strong z-0"
          style={{ left: zeroPct }}
          aria-hidden="true"
        />

        {/* 80% Credible Interval Range Bar */}
        <div
          className="absolute top-1 bottom-1 bg-primary/25 dark:bg-primary/40 rounded-full z-10"
          style={{ left: leftPct, width: widthPct }}
          aria-hidden="true"
        />

        {/* Shrunk Point Estimate Dot */}
        <div
          className={`absolute top-0.5 bottom-0.5 w-2.5 h-2.5 rounded-full z-20 -ml-1.5 shadow-sm border border-white dark:border-slate-900 ${
            point >= 0 ? "bg-primary" : "bg-secondary"
          }`}
          style={{ left: pointPct, top: "50%", transform: "translateY(-50%)" }}
          aria-hidden="true"
        />
      </div>

      {showLabels && (
        <div className="flex justify-between text-[11px] font-mono text-text-muted px-1">
          <span>{lower >= 0 ? `+${lower.toFixed(2)}` : lower.toFixed(2)}</span>
          <span className="font-semibold text-text-primary">{point >= 0 ? `+${point.toFixed(2)}` : point.toFixed(2)}</span>
          <span>{upper >= 0 ? `+${upper.toFixed(2)}` : upper.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
}
