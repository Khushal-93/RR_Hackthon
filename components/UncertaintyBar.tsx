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
      className={`inline-flex flex-col gap-0.5 ${width}`}
      title={`80% Credible Interval: [${lower >= 0 ? "+" : ""}${lower.toFixed(3)}, ${upper >= 0 ? "+" : ""}${upper.toFixed(3)}] | Point: ${point >= 0 ? "+" : ""}${point.toFixed(3)}`}
    >
      <div className="relative h-4 bg-surface-subtle border border-border-light rounded flex items-center overflow-hidden">
        {/* Zero baseline reference line */}
        <div
          className="absolute top-0 bottom-0 w-[1px] bg-border-strong z-0"
          style={{ left: zeroPct }}
          aria-hidden="true"
        />

        {/* 80% Credible Interval Range Bar */}
        <div
          className="absolute top-1 bottom-1 bg-border-strong/70 rounded-sm z-10"
          style={{ left: leftPct, width: widthPct }}
          aria-hidden="true"
        />

        {/* Shrunk Point Estimate Dot */}
        <div
          className={`absolute top-1 bottom-1 w-2 h-2 rounded-full z-20 -ml-1 border ${
            point >= 0 ? "bg-accent-success border-emerald-300" : "bg-accent-danger border-rose-300"
          }`}
          style={{ left: pointPct, top: "50%", transform: "translateY(-50%)" }}
          aria-hidden="true"
        />
      </div>

      {showLabels && (
        <div className="flex justify-between text-[10px] font-mono text-text-muted px-0.5">
          <span>{lower >= 0 ? `+${lower.toFixed(2)}` : lower.toFixed(2)}</span>
          <span className="font-bold text-text-primary">{point >= 0 ? `+${point.toFixed(2)}` : point.toFixed(2)}</span>
          <span>{upper >= 0 ? `+${upper.toFixed(2)}` : upper.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
}
