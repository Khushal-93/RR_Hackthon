"""
Phase 2: Statistical Validation, Regression & Chart Generation (Remediated)
Implements:
1. Behavioral metrics per pressure band.
2. Multiple regression controlling for batter quality, innings phase, and batting order,
   reporting effect sizes with confidence intervals and p-values.
3. Publication-quality charts saved to reports/charts/.
"""

import os
from typing import Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf


def compute_band_metrics(df: pd.DataFrame, band_col: str) -> pd.DataFrame:
    """Computes comprehensive batting & bowling metrics per pressure band."""
    results = []
    bands = ["Low", "Medium", "High"]

    for b in bands:
        sub = df[df[band_col] == b]
        legal = sub[sub["is_legal"]]
        n_legal = len(legal)
        if n_legal == 0:
            continue

        runs = legal["runs"].sum()
        tot_runs = legal["total_delivery_runs"].sum()
        wkts = legal["is_wicket"].sum()
        fours = legal["is_four"].sum()
        sixes = legal["is_six"].sum()
        dots = ((legal["runs"] == 0) & (~legal["is_wicket"])).sum()

        sr = (runs / n_legal) * 100.0
        econ = (tot_runs / n_legal) * 6.0
        wkt_pct = (wkts / n_legal) * 100.0
        dot_pct = (dots / n_legal) * 100.0
        bound_pct = ((fours + sixes) / n_legal) * 100.0
        six_pct = (sixes / n_legal) * 100.0
        runs_per_wkt = runs / wkts if wkts > 0 else np.nan

        results.append({
            "Band": b,
            "Total Deliveries": len(sub),
            "Legal Balls": n_legal,
            "Strike Rate": round(sr, 2),
            "Bowling Econ": round(econ, 2),
            "Dismissal Rate (%)": round(wkt_pct, 2),
            "Dot Ball (%)": round(dot_pct, 2),
            "Boundary (%)": round(bound_pct, 2),
            "Six (%)": round(six_pct, 2),
            "Runs/Wicket": round(runs_per_wkt, 2)
        })

    return pd.DataFrame(results)


def run_dismissal_regression(df: pd.DataFrame) -> Dict:
    """
    Rigorous test of whether pressure genuinely increases dismissals after controlling
    for batter baseline skill (empirical Bayes shrinkage), match phase, and batting order.
    Uses cluster-robust standard errors grouped by match_id.
    """
    legal = df[df["is_legal"] & df["batting_order"].notna() & df["striker_id"].notna()].copy()
    legal["is_wicket"] = legal["is_wicket"].astype(float)

    # Compute batter career baseline dismissal rate with empirical Bayes shrinkage
    batter_stats = legal.groupby("striker_id")["is_wicket"].agg(["mean", "count"])
    global_mean = legal["is_wicket"].mean()
    m = 50.0  # shrinkage pseudo-count
    batter_stats["batter_wkt_rate"] = (batter_stats["mean"] * batter_stats["count"] + global_mean * m) / (batter_stats["count"] + m)
    legal["batter_wkt_rate"] = legal["striker_id"].map(batter_stats["batter_wkt_rate"])

    # Regression 1: Composite Pressure (without wickets in hand)
    model_comp = smf.ols(
        "is_wicket ~ pressure_composite_no_wkt + batting_order + C(phase) + batter_wkt_rate",
        data=legal
    ).fit(cov_type="cluster", cov_kwds={"groups": legal["match_id"]})

    # Regression 2: Standardized Leverage Percentile
    model_lev = smf.ols(
        "is_wicket ~ leverage_percentile + batting_order + C(phase) + batter_wkt_rate",
        data=legal
    ).fit(cov_type="cluster", cov_kwds={"groups": legal["match_id"]})

    return {
        "model_comp": model_comp,
        "model_lev": model_lev,
        "n_deliveries": len(legal),
        "n_matches": legal["match_id"].nunique(),
    }


def plot_calibration(cal_table: pd.DataFrame, brier: float, logloss: float, out_path: str):
    """Generates Out-of-Sample Win Probability Calibration Plot."""
    fig, ax = plt.subplots(figsize=(7, 6))

    pred = cal_table["mean_pred"]
    actual = cal_table["win_rate"]

    ax.plot([0, 1], [0, 1], linestyle="--", color="#78909c", label="Perfect Calibration")
    ax.plot(pred, actual, marker="o", linewidth=2.5, markersize=8, color="#1565c0", label="Out-of-Sample (GroupKFold)")

    ax.set_title("Out-of-Sample Win Probability Calibration Curve", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Mean Predicted Win Probability", fontsize=11)
    ax.set_ylabel("Observed Win Rate", fontsize=11)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle=":", alpha=0.6)

    text_str = f"Out-of-Sample CV\nBrier Score: {brier:.4f}\nLog-Loss: {logloss:.4f}\nFolds: 5 (by match_id)"
    ax.text(0.05, 0.85, text_str, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", bbox=dict(boxstyle="round,pad=0.5", facecolor="#e3f2fd", edgecolor="#1565c0", alpha=0.85))

    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()


def plot_leverage_distribution(df: pd.DataFrame, out_path: str):
    """Generates Leverage Index Distribution across Match Overs and Innings."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # 1. Histogram of Within-Innings Standardized Leverage Index
    lev = df["leverage_index"].clip(0, 4)
    ax1.hist(lev[df["innings"] == 1], bins=35, color="#00838f", alpha=0.6, density=True, label="1st Innings")
    ax1.hist(lev[df["innings"] == 2], bins=35, color="#e65100", alpha=0.6, density=True, label="2nd Innings")
    ax1.axvline(1.0, color="#2e7d32", linestyle="--", linewidth=1.8, label="Mean Swing (1.0)")
    ax1.set_title("Standardized Leverage Index Distribution", fontsize=13, fontweight="bold")
    ax1.set_xlabel("Leverage Index (Innings Mean = 1.0)", fontsize=11)
    ax1.set_ylabel("Density", fontsize=11)
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.legend(loc="upper right")

    # 2. Leverage progression across overs 1-20
    over_lev = df.groupby(["overid", "innings"])["leverage_index"].mean().unstack("innings")
    if 1 in over_lev.columns:
        ax2.plot(over_lev.index, over_lev[1], marker="o", color="#00838f", linewidth=2.2, label="1st Innings")
    if 2 in over_lev.columns:
        ax2.plot(over_lev.index, over_lev[2], marker="s", color="#e65100", linewidth=2.5, label="2nd Innings (Chase)")

    ax2.set_title("Standardized Mean Leverage Index by Over", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Over Number (1 - 20)", fontsize=11)
    ax2.set_ylabel("Mean Leverage Index", fontsize=11)
    ax2.set_xticks(range(1, 21))
    ax2.axvspan(16, 20, color="#ffebee", alpha=0.5, label="Death Overs (16-20)")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(loc="upper left")

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()


def plot_pressure_bands_validation(metrics_lev: pd.DataFrame, metrics_comp: pd.DataFrame, out_path: str):
    """Generates comparison bar charts validating behavioral differences across bands."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    x = np.arange(len(metrics_lev["Band"]))
    width = 0.35

    # 1. Strike Rate Comparison
    axes[0, 0].bar(x - width/2, metrics_lev["Strike Rate"], width, label="Leverage Index (Percentile)", color="#1565c0")
    axes[0, 0].bar(x + width/2, metrics_comp["Strike Rate"], width, label="Composite (No Wickets)", color="#00897b")
    axes[0, 0].set_title("Batter Strike Rate across Pressure Bands", fontsize=12, fontweight="bold")
    axes[0, 0].set_ylabel("Strike Rate (Runs / 100 Balls)", fontsize=10)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(metrics_lev["Band"])
    axes[0, 0].legend()
    axes[0, 0].grid(True, linestyle=":", alpha=0.5)

    # 2. Dismissal Rate Comparison
    axes[0, 1].bar(x - width/2, metrics_lev["Dismissal Rate (%)"], width, label="Leverage Index (Percentile)", color="#c62828")
    axes[0, 1].bar(x + width/2, metrics_comp["Dismissal Rate (%)"], width, label="Composite (No Wickets)", color="#ef6c00")
    axes[0, 1].set_title("Dismissal Rate (%) across Pressure Bands", fontsize=12, fontweight="bold")
    axes[0, 1].set_ylabel("Dismissal Rate (%)", fontsize=10)
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(metrics_lev["Band"])
    axes[0, 1].legend()
    axes[0, 1].grid(True, linestyle=":", alpha=0.5)

    # 3. Dot Ball % Comparison
    axes[1, 0].bar(x - width/2, metrics_lev["Dot Ball (%)"], width, label="Leverage Index", color="#5c6bc0")
    axes[1, 0].bar(x + width/2, metrics_comp["Dot Ball (%)"], width, label="Composite Index", color="#26a69a")
    axes[1, 0].set_title("Dot Ball % across Pressure Bands", fontsize=12, fontweight="bold")
    axes[1, 0].set_ylabel("Dot Ball (%)", fontsize=10)
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(metrics_lev["Band"])
    axes[1, 0].legend()
    axes[1, 0].grid(True, linestyle=":", alpha=0.5)

    # 4. Bowler Economy Comparison
    axes[1, 1].bar(x - width/2, metrics_lev["Bowling Econ"], width, label="Leverage Index", color="#7e57c2")
    axes[1, 1].bar(x + width/2, metrics_comp["Bowling Econ"], width, label="Composite Index", color="#ffa726")
    axes[1, 1].set_title("Bowling Economy across Pressure Bands", fontsize=12, fontweight="bold")
    axes[1, 1].set_ylabel("Economy (Runs / Over)", fontsize=10)
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(metrics_lev["Band"])
    axes[1, 1].legend()
    axes[1, 1].grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
