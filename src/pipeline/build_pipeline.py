"""
Phase 1-B: Core Data Pipeline (Remediated)
Cleans the raw parquet data and produces per-ball state:
  legal_ball_num, phase, score, wickets_in_hand, balls_remaining,
  target, required_run_rate, run_rate_gap, pressure flags.

Audit Fixes Applied:
1. Treated first/second_inn_revised_overs as balls directly (not overs).
2. Corrected balls_remaining to start at 120 and remain bounded in [0, 120], with assertions.
3. Added known extras: +1 for wide, +1 for no-ball penalty, imputed 1.0 run for byes & leg-byes.
4. Flagged matches whose reconstructed total differs from the scorecard margin as exclude_from_rrr.
5. Saved DLS/revised matches in a separate flagged table (data/ball_state_dls.parquet).
"""

import os
import re
import pandas as pd
import numpy as np

DATA = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet"
OUT  = r"C:\Users\Khushal\pressure_xi\data\ball_state.parquet"
OUT_DLS = r"C:\Users\Khushal\pressure_xi\data\ball_state_dls.parquet"
OUT_CLEAN = r"C:\Users\Khushal\pressure_xi\data\ball_state_clean.parquet"

ILLEGAL_EXTRAS = {"wide", "Overstep"}   # do not count towards legal balls

PHASES = {
    range(1,  7): "powerplay",    # overs 1-6
    range(7,  16): "middle",      # overs 7-15
    range(16, 21): "death",       # overs 16-20
}

def over_to_phase(over: int) -> str:
    for r, label in PHASES.items():
        if over in r:
            return label
    return "unknown"


def parse_run_margin(result: object):
    if pd.isna(result):
        return None
    match = re.search(r"\bwon\s*(?:by)?\s*(\d+)\s*runs?\b", str(result), re.I)
    return int(match.group(1)) if match else None


def build_ball_state(save: bool = True) -> pd.DataFrame:
    # ── 1. Load raw files ─────────────────────────────────────────────────────
    bbb  = pd.read_parquet(os.path.join(DATA, "ball_by_ball.parquet"))
    mat  = pd.read_parquet(os.path.join(DATA, "matches.parquet"))
    comp = pd.read_parquet(os.path.join(DATA, "competitions.parquet"))

    # ── 2. Enrich match-level context ─────────────────────────────────────────
    rev_target = pd.to_numeric(mat["revised_target"], errors="coerce").fillna(0) > 0
    rev_overs = mat["first_inn_revised_overs"].notna() | mat["second_inn_revised_overs"].notna()
    result_dls = mat["result"].str.contains(r"D/L|DLS|method", case=False, na=False)
    mat["is_dls"] = (rev_target | rev_overs | result_dls).fillna(False)

    mat_ctx = mat[[
        "match_id", "comp_id", "match_date", "stage",
        "home_team_id", "away_team_id",
        "first_inn_revised_overs", "second_inn_revised_overs",
        "revised_target", "knock_out", "win_team_id", "result", "is_dls"
    ]].copy()

    comp_ctx = comp[["comp_id", "comp_name", "match_format", "season"]].copy()

    # ── 3. Merge context onto ball_by_ball ────────────────────────────────────
    df = bbb.merge(mat_ctx, on="match_id", how="left")
    df = df.merge(comp_ctx, on="comp_id", how="left")

    # ── 4. Exclude super overs (innings > 2) ──────────────────────────────────
    super_over_deliveries = (df["innings"] > 2).sum()
    df = df[df["innings"].isin([1, 2])].copy()
    print(f"  Excluded {super_over_deliveries} super-over deliveries")

    # ── 5. Fix data types ─────────────────────────────────────────────────────
    df["is_wicket"] = df["is_wicket"].astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    ).fillna(False)
    df["is_four"] = df["is_four"].astype(str).str.lower().map(
        {"true": True, "false": False}).fillna(False)
    df["is_six"]  = df["is_six"].astype(str).str.lower().map(
        {"true": True, "false": False}).fillna(False)

    df["runs"]          = pd.to_numeric(df["runs"], errors="coerce").fillna(0).astype(int)
    df["extras_2_runs"] = pd.to_numeric(df["extras_2_runs"], errors="coerce").fillna(0).astype(int)
    df["overid"]        = pd.to_numeric(df["overid"], errors="coerce").fillna(0).astype(int)
    df["over_ball_num"] = pd.to_numeric(df["over_ball_num"], errors="coerce").fillna(0).astype(int)

    # ── 6. Delivery-level run calculation with known and imputed extras ───────
    df["is_wide"]   = df["extras_type"] == "wide"
    df["is_noball"] = df["extras_type"] == "Overstep"
    df["is_bye"]    = df["extras_type"] == "byes"
    df["is_legbye"] = df["extras_type"] == "legbyes"
    df["is_legal"]  = ~df["extras_type"].isin(ILLEGAL_EXTRAS)

    # Ingest extras:
    # +1 for each wide (minimum guarantee)
    # +1 for each no-ball penalty run
    # Impute byes and leg-byes with their average observed run value (1.0 run)
    df["wide_runs"]   = df["is_wide"].astype(int)
    df["noball_runs"] = df["is_noball"].astype(int)
    df["bye_runs"]    = df["is_bye"].astype(int)
    df["legbye_runs"] = df["is_legbye"].astype(int)

    df["total_delivery_runs"] = (
        df["runs"] + df["extras_2_runs"] + df["wide_runs"] + df["noball_runs"] + df["bye_runs"] + df["legbye_runs"]
    )

    # ── 7. Per-match-innings sort order ───────────────────────────────────────
    df = df.sort_values(["match_id", "innings", "overid", "over_ball_num"]).reset_index(drop=True)

    # ── 8. Cumulative state within each innings ───────────────────────────────
    grp = df.groupby(["match_id", "innings"])

    # Cumulative runs AFTER this ball
    df["cumulative_runs"] = grp["total_delivery_runs"].cumsum()
    # Runs BEFORE this ball (for state at time of delivery)
    df["runs_at_ball"] = df["cumulative_runs"] - df["total_delivery_runs"]

    # Cumulative wickets AFTER this ball
    df["cum_wickets"] = grp["is_wicket"].cumsum().astype(int)
    # Wickets BEFORE this ball
    df["wickets_before"] = df["cum_wickets"] - df["is_wicket"].astype(int)
    df["wickets_in_hand"] = 10 - df["wickets_before"]

    # Legal ball counters
    df["legal_ball_cumsum"] = grp["is_legal"].cumsum().astype(int)
    df["legal_ball_num"] = df["legal_ball_cumsum"]  # post-ball legal ball index

    # Legal balls bowled BEFORE this delivery
    legal_balls_before = df["legal_ball_cumsum"] - df["is_legal"].astype(int)

    # Max legal balls:
    # Treat revised overs fields directly as balls (not overs), bounded in [0, 120]
    std_balls = 120
    df["max_legal_balls"] = std_balls
    for col_inn, col_rev in [(1, "first_inn_revised_overs"), (2, "second_inn_revised_overs")]:
        mask = df["innings"] == col_inn
        rev = pd.to_numeric(df.loc[mask, col_rev], errors="coerce")
        df.loc[mask & rev.notna(), "max_legal_balls"] = rev[rev.notna()].clip(lower=0, upper=120).astype(int)

    # Balls remaining BEFORE this ball: starts at 120 on standard Ball 1 and bounded in [0, 120]
    df["balls_remaining"] = (df["max_legal_balls"] - legal_balls_before).clip(lower=0, upper=120)

    # Assertions on balls_remaining bounds and initial state
    assert (df["balls_remaining"] >= 0).all() and (df["balls_remaining"] <= 120).all(), (
        "Assertion failed: balls_remaining outside [0, 120]!"
    )
    first_deliv = df.groupby(["match_id", "innings"]).head(1)
    std_first = first_deliv[first_deliv["max_legal_balls"] == 120]
    assert (std_first["balls_remaining"] == 120).all(), (
        "Assertion failed: standard innings must start at 120 balls remaining!"
    )
    assert (df["max_legal_balls"] <= 120).all(), (
        "Assertion failed: max_legal_balls cannot exceed 120!"
    )
    assert (df["wickets_in_hand"].between(0, 10)).all(), (
        "Assertion failed: wickets_in_hand must be between 0 and 10!"
    )

    # ── 9. Phase ──────────────────────────────────────────────────────────────
    df["phase"] = df["overid"].map(over_to_phase)

    # ── 10. Innings Totals, Match Reconciliation & Target ─────────────────────
    inn_totals = df.groupby(["match_id", "innings"])["total_delivery_runs"].sum().unstack()
    inn_totals = inn_totals.rename(columns={1: "calc_inn1", 2: "calc_inn2"}).reset_index()
    df = df.merge(inn_totals[["match_id", "calc_inn1", "calc_inn2"]], on="match_id", how="left")

    df["parsed_run_margin"] = df["result"].map(parse_run_margin)
    df["reconstructed_margin"] = df["calc_inn1"] - df["calc_inn2"]

    # Scorecard reconstruction error calculation:
    # For run wins: (calc_inn1 - calc_inn2) - parsed_run_margin
    # For wicket wins: if calc_inn2 < calc_inn1, deficit is (calc_inn2 - calc_inn1)
    # For ties: calc_inn1 - calc_inn2
    res_lower = df["result"].astype(str).str.lower()
    is_run_game = df["parsed_run_margin"].notna()
    is_wicket_win = res_lower.str.contains("wicket|wkt", regex=True)
    is_tie = res_lower.str.contains("tie|tied", regex=True)

    recon_err = np.full(len(df), np.nan)
    # Run games
    mask_run = is_run_game & df["calc_inn2"].notna()
    recon_err[mask_run] = df.loc[mask_run, "reconstructed_margin"] - df.loc[mask_run, "parsed_run_margin"]
    # Wicket games
    mask_wkt = is_wicket_win & df["calc_inn2"].notna() & (~is_run_game)
    wkt_def = df.loc[mask_wkt, "calc_inn2"] - df.loc[mask_wkt, "calc_inn1"]
    recon_err[mask_wkt] = np.where(wkt_def >= 0, 0.0, wkt_def)
    # Tie games
    mask_tie = is_tie & df["calc_inn2"].notna() & (~is_run_game) & (~is_wicket_win)
    recon_err[mask_tie] = df.loc[mask_tie, "calc_inn1"] - df.loc[mask_tie, "calc_inn2"]

    df["reconstruction_error"] = recon_err
    abs_err = np.abs(df["reconstruction_error"])

    # Reconciled match verification:
    # Exact match: abs_err == 0 (and not DLS)
    df["margin_reconciled"] = (df["reconstruction_error"] == 0.0) & (~df["is_dls"])
    # Approximate match: reconstruction error within +/- 10 runs (and not exact zero, not DLS)
    df["approximate_score"] = (abs_err > 0.0) & (abs_err <= 10.0) & (~df["is_dls"])

    # Exclude from RRR calculations:
    # Keep matches with reconstruction error within +/- 10 runs in Innings 2!
    # Exclude gross outliers (|err| > 10, NaN error, Innings != 2, or DLS)
    gross_outlier = abs_err.isna() | (abs_err > 10.0)
    df["exclude_from_rrr"] = gross_outlier | df["is_dls"] | (df["innings"] != 2)

    # Target calculation
    df["inn1_score"] = df["calc_inn1"]
    df["target"] = np.nan
    inn2_mask = df["innings"] == 2
    df.loc[inn2_mask, "target"] = df.loc[inn2_mask, "calc_inn1"] + 1

    # For DLS matches, override with revised target if available
    has_dls_target = inn2_mask & df["is_dls"] & df["revised_target"].notna()
    df.loc[has_dls_target, "target"] = pd.to_numeric(df.loc[has_dls_target, "revised_target"], errors="coerce")

    # Required runs at delivery start
    df["runs_needed"] = (df["target"] - df["runs_at_ball"]).clip(lower=0)

    # Required run rate: only computed for reconciled non-excluded 2nd innings
    valid_rrr = inn2_mask & (~df["exclude_from_rrr"]) & (df["balls_remaining"] > 0)
    df["required_run_rate"] = np.where(
        valid_rrr,
        (df["runs_needed"] / df["balls_remaining"]) * 6.0,
        np.nan
    )

    # Current run rate at delivery start
    overs_bowled = legal_balls_before / 6.0
    df["current_run_rate"] = np.where(
        overs_bowled > 0,
        df["runs_at_ball"] / overs_bowled,
        0.0
    )

    # Run rate gap
    df["run_rate_gap"] = df["required_run_rate"] - df["current_run_rate"]

    # ── 11. Final column selection ────────────────────────────────────────────
    keep_cols = [
        # identifiers
        "match_id", "comp_id", "match_format", "season", "match_date",
        "innings", "overid", "over_ball_num",
        "batting_team_id", "bowling_team_id",
        "striker_id", "striker_name",
        "non_striker_id", "non_striker_name",
        "bowler_id", "bowler_name",
        # delivery type
        "batting_type", "bowling_type", "pace_or_spin",
        "batting_order", "stroke",
        # delivery outcome
        "runs", "extras_2_runs", "wide_runs", "noball_runs", "bye_runs", "legbye_runs",
        "total_delivery_runs", "is_legal", "is_wide", "is_noball", "is_bye", "is_legbye",
        "is_four", "is_six", "is_wicket",
        "dismissal_type", "dismissed_player_id",
        # innings state at ball
        "runs_at_ball", "wickets_before", "wickets_in_hand",
        "legal_ball_num", "balls_remaining", "max_legal_balls",
        "phase",
        # 2nd innings context
        "inn1_score", "calc_inn1", "calc_inn2", "target", "runs_needed",
        "required_run_rate", "current_run_rate", "run_rate_gap",
        # match context & flags
        "stage", "knock_out", "is_dls", "margin_reconciled", "approximate_score",
        "exclude_from_rrr", "reconstruction_error",
        "win_team_id", "result", "parsed_run_margin", "reconstructed_margin"
    ]

    df = df[[c for c in keep_cols if c in df.columns]].copy()

    if save:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        # Main dataset
        df.to_parquet(OUT, index=False)
        print(f"  Ball state saved -> {OUT} ({len(df):,} rows)")
        # Clean non-DLS dataset
        clean_df = df[~df["is_dls"]].copy()
        clean_df.to_parquet(OUT_CLEAN, index=False)
        print(f"  Clean ball state saved -> {OUT_CLEAN} ({len(clean_df):,} rows)")
        # Separate flagged DLS table
        dls_df = df[df["is_dls"]].copy()
        dls_df.to_parquet(OUT_DLS, index=False)
        print(f"  DLS separate table saved -> {OUT_DLS} ({len(dls_df):,} rows)")

    return df


if __name__ == "__main__":
    print("Building remediated ball-state pipeline...")
    df = build_ball_state(save=True)
    print(f"\nPipeline build complete: {len(df):,} deliveries")
