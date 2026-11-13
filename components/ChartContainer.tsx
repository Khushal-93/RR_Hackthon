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
    <div className="apple-card overflow-hidden flex flex-col">
      {/* Header with Title and Accessible Data-Table Toggle */}
      <div className="p-6 sm:p-7 border-b border-border-light flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold text-text-primary tracking-tight">{title}</h3>
          {subtitle && <p className="text-sm text-text-secondary mt-1">{subtitle}</p>}
        </div>

        <button
          onClick={() => setShowTable(!showTable)}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full border border-border-medium bg-surface hover:bg-black/5 dark:hover:bg-white/10 text-text-primary transition-colors shrink-0 self-start sm:self-auto"
          aria-label={showTable ? "Switch to chart view" : "Switch to accessible data table"}
        >
          {showTable ? (
            <>
              <BarChart2 className="w-3.5 h-3.5 text-primary" />
              <span>Show Chart View</span>
            </>
          ) : (
            <>
              <Table className="w-3.5 h-3.5 text-text-muted" />
              <span>Show Accessible Table</span>
            </>
          )}
        </button>
      </div>

      {/* Main Body */}
      <div className="p-6 sm:p-7 flex-1 min-h-[320px] flex items-center justify-center">
        {showTable ? (
          <div className="w-full overflow-x-auto" tabIndex={0} aria-label={`${title} data table`}>
            {tableView}
          </div>
        ) : (
          <div className="w-full h-full min-h-[300px]">{chartView}</div>
        )}
      </div>

      {/* Footnote Source */}
      <div className="px-7 py-3 border-t border-border-light bg-black/[0.01] dark:bg-white/[0.02] text-xs font-mono text-text-muted flex justify-between items-center">
        <span>Source: {sourceText}</span>
        <span className="hidden sm:inline">Descriptive Historical Analysis</span>
      </div>
    </div>
  );
}
