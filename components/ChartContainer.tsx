"use client";

import React, { useState } from "react";
import { Table, BarChart2 } from "lucide-react";

interface Props {
  title: string;
  subtitle?: string;
  sourceText?: string;
  chartView: React.ReactNode;
  tableView: React.ReactNode;
  defaultToTable?: boolean;
}

export function ChartContainer({
  title,
  subtitle,
  sourceText = "829 clean non-DLS matches (IPL & T20I, 2022 to 2026)",
  chartView,
  tableView,
  defaultToTable = false,
}: Props) {
  const [showTable, setShowTable] = useState(defaultToTable);

  return (
    <div className="bg-surface border border-border-light rounded-lg overflow-hidden flex flex-col">
      {/* Header with Title and Accessible Data-Table Toggle */}
      <div className="p-4 sm:p-5 border-b border-border-light flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface-subtle/50">
        <div>
          <h3 className="font-bold text-base text-text-primary">{title}</h3>
          {subtitle && <p className="text-xs text-text-secondary mt-0.5">{subtitle}</p>}
        </div>

        <button
          onClick={() => setShowTable(!showTable)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded border border-border-medium bg-surface hover:bg-surface-subtle text-text-primary transition-colors shrink-0 self-start sm:self-auto"
          aria-label={showTable ? "Switch to chart view" : "Switch to accessible data table"}
        >
          {showTable ? (
            <>
              <BarChart2 className="w-3.5 h-3.5 text-accent-primary" />
              <span>Show Chart View</span>
            </>
          ) : (
            <>
              <Table className="w-3.5 h-3.5 text-text-muted" />
              <span>Show Data Table</span>
            </>
          )}
        </button>
      </div>

      {/* Main Body */}
      <div className="p-4 sm:p-5 flex-1 min-h-[300px] flex items-center justify-center">
        {showTable ? (
          <div className="w-full overflow-x-auto" tabIndex={0} aria-label={`${title} data table`}>
            {tableView}
          </div>
        ) : (
          <div className="w-full h-full min-h-[280px]">{chartView}</div>
        )}
      </div>

      {/* Footnote Source */}
      <div className="px-4 py-2.5 border-t border-border-light bg-surface-subtle/30 text-[11px] font-mono text-text-muted flex justify-between items-center">
        <span>Source: {sourceText}</span>
        <span className="hidden sm:inline">Descriptive ratings</span>
      </div>
    </div>
  );
}
