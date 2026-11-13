import React from "react";
import Link from "next/link";
import { Download, FileText, CheckCircle2, XCircle, AlertCircle, Database } from "lucide-react";
import { getValidationSync, getMetaSync } from "@/lib/data";
import { ChartContainer } from "@/components/ChartContainer";
import {
  CalibrationPlot,
  CalibrationTable,
} from "@/components/charts/CalibrationPlot";

export default function MethodPage() {
  const validation = getValidationSync();
  const meta = getMetaSync();

  return (
    <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 py-8 space-y-10">
      {/* Page Header */}
      <div className="space-y-2 border-b border-border-light pb-6">
        <span className="font-mono text-xs text-text-muted uppercase">Scientific Audit Center</span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
          Methodology, Validation & Honest Reliability
        </h1>
        <p className="text-sm text-text-secondary max-w-3xl leading-relaxed">
          Full algorithmic transparency: empirical pipeline, win-probability calibration, out-of-time validation, dropped candidates cemetery, and known structural limitations.
        </p>
      </div>

      {/* a. Pipeline Flow Diagram (6 Stages) */}
      <section aria-labelledby="pipeline-heading" className="space-y-4">
        <h2 id="pipeline-heading" className="text-xl font-bold text-text-primary font-mono">
          1. Six-Stage Methodology Pipeline
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-surface border border-border-light space-y-2">
            <div className="flex items-center justify-between font-mono text-xs text-accent-primary">
              <span className="font-bold">STAGE 01</span>
              <span>Input Ingestion</span>
            </div>
            <h3 className="font-bold text-sm text-text-primary">Clean Non-DLS Extraction</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              195,707 legal balls across 829 matches. 100% of rain-shortened DLS matches (41) and Super Overs (38 balls) strictly excluded to avoid distorting baseline expectations.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface border border-border-light space-y-2">
            <div className="flex items-center justify-between font-mono text-xs text-accent-primary">
              <span className="font-bold">STAGE 02</span>
              <span>State Engine</span>
            </div>
            <h3 className="font-bold text-sm text-text-primary">Win-Probability & Leverage</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Gradient-boosted logistic win probability conditioned on phase, target, balls remaining, and wickets in hand. Standardized within innings into leverage percentiles.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface border border-border-light space-y-2">
            <div className="flex items-center justify-between font-mono text-xs text-accent-primary">
              <span className="font-bold">STAGE 03</span>
              <span>Pressure Corridor</span>
            </div>
            <h3 className="font-bold text-sm text-text-primary">Top Third Standardization</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Pressure = top third of standardized leverage within each innings (LI &ge; 1.258 in Inn 1; LI &ge; 1.246 in Inn 2). Captures 65,229 high-pressure deliveries.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface border border-border-light space-y-2">
            <div className="flex items-center justify-between font-mono text-xs text-accent-primary">
              <span className="font-bold">STAGE 04</span>
              <span>Expected Baselines</span>
            </div>
            <h3 className="font-bold text-sm text-text-primary">LOMO Expectation Baselines</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Leave-One-Match-Out (LOMO) expected runs per ball conditioned on Phase, Wickets in Hand, Batting Order, and Bowler Type, plus shrunk opposition attack adjustment.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface border border-border-light space-y-2">
            <div className="flex items-center justify-between font-mono text-xs text-accent-primary">
              <span className="font-bold">STAGE 05</span>
              <span>Shrinkage Engine</span>
            </div>
            <h3 className="font-bold text-sm text-text-primary">Empirical Bayes Shrinkage</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Observed sample means shrunk toward pool grand mean using player-specific sampling variance. Moderate-volume qualifiers pulled safely toward the baseline.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-surface border border-border-light space-y-2">
            <div className="flex items-center justify-between font-mono text-xs text-accent-primary">
              <span className="font-bold">STAGE 06</span>
              <span>Uncertainty & Audit</span>
            </div>
            <h3 className="font-bold text-sm text-text-primary">Block Bootstrap & Stability</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              500-iteration block bootstrap 80% credible intervals and P(Top-10) estimates. Leave-top-2-matches-out robustness testing to identify volume sensitivity.
            </p>
          </div>
        </div>
      </section>

      {/* b. Win Probability Calibration Curve & Brier Score Table */}
      <section aria-labelledby="calibration-heading" className="space-y-4">
        <h2 id="calibration-heading" className="text-xl font-bold text-text-primary font-mono">
          2. Win Probability Model Calibration
        </h2>

        {/* Error Score KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-surface border border-border-light p-4 rounded-lg">
            <div className="font-mono text-xs text-text-muted">GroupKFold Brier Score</div>
            <div className="text-2xl font-bold font-mono text-accent-success my-1">
              {validation.win_probability_brier.group_kfold_brier.toFixed(4)}
            </div>
            <div className="text-[11px] text-text-secondary">Cross-match evaluated</div>
          </div>
          <div className="bg-surface border border-border-light p-4 rounded-lg">
            <div className="font-mono text-xs text-text-muted">Temporal Holdout Brier</div>
            <div className="text-2xl font-bold font-mono text-accent-primary my-1">
              {validation.win_probability_brier.temporal_holdout_brier.toFixed(4)}
            </div>
            <div className="text-[11px] text-text-secondary">Tested on 2025–2026 matches</div>
          </div>
          <div className="bg-surface border border-border-light p-4 rounded-lg">
            <div className="font-mono text-xs text-text-muted">Naive Constant Baseline</div>
            <div className="text-2xl font-bold font-mono text-text-muted my-1">
              {validation.win_probability_brier.naive_baseline_brier.toFixed(4)}
            </div>
            <div className="text-[11px] text-accent-success">
              +{validation.win_probability_brier.relative_improvement_pct}% improvement
            </div>
          </div>
        </div>

        <ChartContainer
          title="Win Probability Decile Calibration Curve"
          subtitle="Observed match win rates vs predicted probabilities across 10 equal deciles."
          chartView={<CalibrationPlot deciles={validation.calibration_deciles} />}
          tableView={<CalibrationTable deciles={validation.calibration_deciles} />}
        />
      </section>

      {/* c. Out-of-Time Test Table with Intervals and Chance-Level Overlap */}
      <section aria-labelledby="oot-heading" className="space-y-4">
        <div className="space-y-1">
          <h2 id="oot-heading" className="text-xl font-bold text-text-primary font-mono">
            3. Out-of-Time Temporal Repeatability Test
          </h2>
          <p className="text-xs text-text-secondary">
            Strict temporal separation: Models fitted on 2022&ndash;2024 seasons (&ge;150 HP balls), evaluated on raw 2025&ndash;2026 performance (&ge;60 HP balls).
          </p>
        </div>

        <div className="overflow-x-auto border border-border-light rounded-lg bg-surface">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-border-light bg-surface-subtle text-text-secondary uppercase text-[10px]">
                <th className="py-3 px-3">Role</th>
                <th className="py-3 px-3 text-right">Qualifiers (N)</th>
                <th className="py-3 px-3 text-right">Spearman &rho;</th>
                <th className="py-3 px-3 text-center">95% Confidence Interval</th>
                <th className="py-3 px-3 text-right">Pearson r</th>
                <th className="py-3 px-3 text-right">Top-10 Overlap</th>
                <th className="py-3 px-3 text-right">Chance Expected</th>
                <th className="py-3 px-3 text-right">Top-20% Overlap</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-light/40">
              <tr className="hover:bg-surface-subtle/50">
                <td className="py-3 px-3 font-bold text-accent-batter">Batters</td>
                <td className="py-3 px-3 text-right">{validation.out_of_time_repeatability.batters.n_qualifiers}</td>
                <td className="py-3 px-3 text-right font-bold text-text-primary">
                  +{validation.out_of_time_repeatability.batters.spearman_rho.toFixed(4)}
                </td>
                <td className="py-3 px-3 text-center text-text-secondary">
                  [{validation.out_of_time_repeatability.batters.ci95_lower.toFixed(4)},{" "}
                  +{validation.out_of_time_repeatability.batters.ci95_upper.toFixed(4)}]
                </td>
                <td className="py-3 px-3 text-right">+{validation.out_of_time_repeatability.batters.pearson_r.toFixed(4)}</td>
                <td className="py-3 px-3 text-right font-bold text-accent-primary">
                  {validation.out_of_time_repeatability.batters.top10_overlap} of 10
                </td>
                <td className="py-3 px-3 text-right text-text-muted">
                  {validation.out_of_time_repeatability.batters.top10_chance.toFixed(2)} of 10
                </td>
                <td className="py-3 px-3 text-right text-accent-success">
                  {validation.out_of_time_repeatability.batters.top20pct_overlap_pct.toFixed(1)}% (vs 20.0%)
                </td>
              </tr>
              <tr className="hover:bg-surface-subtle/50">
                <td className="py-3 px-3 font-bold text-accent-bowler">Bowlers</td>
                <td className="py-3 px-3 text-right">{validation.out_of_time_repeatability.bowlers.n_qualifiers}</td>
                <td className="py-3 px-3 text-right font-bold text-text-primary">
                  +{validation.out_of_time_repeatability.bowlers.spearman_rho.toFixed(4)}
                </td>
                <td className="py-3 px-3 text-center text-text-secondary">
                  [+{validation.out_of_time_repeatability.bowlers.ci95_lower.toFixed(4)},{" "}
                  +{validation.out_of_time_repeatability.bowlers.ci95_upper.toFixed(4)}]
                </td>
                <td className="py-3 px-3 text-right">+{validation.out_of_time_repeatability.bowlers.pearson_r.toFixed(4)}</td>
                <td className="py-3 px-3 text-right font-bold text-accent-primary">
                  {validation.out_of_time_repeatability.bowlers.top10_overlap} of 10
                </td>
                <td className="py-3 px-3 text-right text-text-muted">
                  {validation.out_of_time_repeatability.bowlers.top10_chance.toFixed(2)} of 10
                </td>
                <td className="py-3 px-3 text-right text-accent-success">
                  {validation.out_of_time_repeatability.bowlers.top20pct_overlap_pct.toFixed(1)}% (vs 20.0%)
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* d. "What We Tried and Dropped" Section */}
      <section aria-labelledby="graveyard-heading" className="space-y-4">
        <h2 id="graveyard-heading" className="text-xl font-bold text-text-primary font-mono">
          4. "What We Tried and Dropped" Cemetery
        </h2>
        <div className="space-y-3">
          {validation.dropped_experiments.map((exp) => (
            <div
              key={exp.candidate}
              className="p-4 rounded-lg bg-surface border border-border-light space-y-1.5"
            >
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-accent-danger shrink-0" />
                <h3 className="font-bold text-sm text-text-primary">{exp.candidate}</h3>
              </div>
              <p className="text-xs text-text-secondary leading-relaxed pl-6">
                <strong>Empirical Result: </strong> {exp.reason}
              </p>
              <p className="text-xs text-accent-warning leading-relaxed pl-6 font-mono">
                &rarr; {exp.disposition}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* e. Data Notes and Limitations List */}
      <section aria-labelledby="limits-heading" className="space-y-4">
        <h2 id="limits-heading" className="text-xl font-bold text-text-primary font-mono">
          5. Structural Limitations
        </h2>
        <ul className="space-y-2 text-xs text-text-secondary leading-relaxed list-disc list-inside bg-surface border border-border-light p-5 rounded-lg">
          <li>
            <strong className="text-text-primary">Signal is Modest:</strong> Rank correlation across disjoint seasons is &rho; ~ 0.25 to 0.29. The ratings describe historical efficiency in high-pressure corridors, NOT deterministic predictive traits.
          </li>
          <li>
            <strong className="text-text-primary">Wickets Reduced Repeatability:</strong> Adding binary dismissal weights (k*WAE) degrades out-of-time stability due to Bernoulli noise. Rankings must be treated as confidence tiers rather than precise ordinal numbers.
          </li>
          <li>
            <strong className="text-text-primary">Middle-Overs Spin Tactical Confounding:</strong> 60% of top-10 bowlers are spinners who operate heavily in middle overs (overs 7&ndash;15). While state baselines control for phase, role-stratified interpretation is recommended.
          </li>
          <li>
            <strong className="text-text-primary">Low-Volume Sensitivity:</strong> For qualifiers near 150&ndash;220 balls, excluding top 2 matches moves Behrendorff, Pathirana, and Motie from top 10 into ranks #28&ndash;#32.
          </li>
          <li>
            <strong className="text-text-primary">No Psychological Attribution:</strong> Models measure delivered outcomes under leverage; they do not quantify mental toughness or psychological states.
          </li>
        </ul>
      </section>

      {/* f. Downloads Block */}
      <section aria-labelledby="downloads-heading" className="space-y-4">
        <h2 id="downloads-heading" className="text-xl font-bold text-text-primary font-mono">
          6. Reproducibility & Research Downloads
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <a
            href="/outputs/final_rankings.csv"
            download
            className="flex items-center justify-between p-4 rounded-lg bg-surface border border-border-light hover:border-border-medium transition-colors group"
          >
            <div className="flex items-center gap-3">
              <Database className="w-5 h-5 text-accent-primary" />
              <div>
                <div className="font-bold text-sm text-text-primary group-hover:text-accent-primary">
                  final_rankings.csv
                </div>
                <div className="text-xs text-text-muted font-mono">243 eligible players with ratings, CIs, and tiers</div>
              </div>
            </div>
            <Download className="w-4 h-4 text-text-muted group-hover:text-text-primary" />
          </a>

          <a
            href="/data/meta.json"
            target="_blank"
            className="flex items-center justify-between p-4 rounded-lg bg-surface border border-border-light hover:border-border-medium transition-colors group"
          >
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-accent-primary" />
              <div>
                <div className="font-bold text-sm text-text-primary group-hover:text-accent-primary">
                  Dataset Audit Metadata (meta.json)
                </div>
                <div className="text-xs text-text-muted font-mono">Match counts, DLS exclusions, data cutoff</div>
              </div>
            </div>
            <Download className="w-4 h-4 text-text-muted group-hover:text-text-primary" />
          </a>
        </div>
      </section>
    </div>
  );
}
