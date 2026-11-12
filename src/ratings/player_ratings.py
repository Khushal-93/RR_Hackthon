"""
Phase 3: Player Pressure Performance Ratings
===========================================
Computes evidence-backed player pressure ratings on clean (non-DLS) data:
1. Pressure defined as within-innings standardized Leverage Index (High = top 33.3%).
2. Leave-One-Match-Out (LOMO) expected state baselines (wickets in hand, phase, balls remaining, opponent type).
3. Win Probability Added (WPA) normalized by expected swing (Leverage) + runs/wickets vs expected.
4. Stratified differential rating (High Pressure minus Low Pressure, stratified by WIH x Phase to eliminate Simpson's paradox).
5. Empirical Bayes shrinkage and match-level block bootstrap confidence intervals.
6. Separate breakdowns for Innings 1 and Innings 2.
7. Comprehensive rank stability checks: split-half, season-to-season, percentile vs absolute, exact vs approximate.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def validate_ratings_input(df: pd.DataFrame) -> None:
    """Enforces that zero DLS rows reach ratings code."""
    if "is_dls" in df.columns and df["is_dls"].any():
        n_dls = int(df["is_dls"].sum())
        raise AssertionError(f"CRITICAL AUDIT ERROR: {n_dls} DLS rows detected in ratings input! Phase 3 permits clean non-DLS data only.")


def prepare_ratings_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validates input, sorts deliveries, computes post-ball WP, WPA, NWPA, and state features."""
    validate_ratings_input(df)

    data = df.sort_values(["match_id", "innings", "overid", "over_ball_num"]).copy().reset_index(drop=True)

    # State Buckets
    data["wih_bucket"] = pd.cut(
        data["wickets_in_hand"],
        bins=[-1, 3, 6, 10],
        labels=["1-3 (Low)", "4-6 (Med)", "7-10 (High)"]
    )
    data["order_bucket"] = pd.cut(
        data["batting_order"],
        bins=[0, 3, 6, 11],
        labels=["Top (1-3)", "Middle (4-6)", "Lower (7-11)"]
    )
    # Opponent pace/spin clean
    data["bowler_type"] = data["pace_or_spin"].fillna("Unknown")

    # Pressure bands: High = top 33.3%, Medium = middle 33.3%, Low = bottom 33.3%
    data["pressure_band_lev"] = pd.cut(
        data["leverage_percentile"],
        bins=[-np.inf, 1.0 / 3.0, 2.0 / 3.0, np.inf],
        labels=["Low", "Medium", "High"]
    )

    # Post-delivery win probability
    data["next_match"] = data["match_id"].shift(-1)
    data["next_inn"] = data["innings"].shift(-1)
    data["next_wp"] = data["win_prob"].shift(-1)

    is_same_inn = (data["match_id"] == data["next_match"]) & (data["innings"] == data["next_inn"])
    inn2_last = (~is_same_inn) & (data["innings"] == 2)
    final_wp_inn2 = np.where(data["win_team_id"] == data["batting_team_id"], 1.0, 0.0)

    post_wp = np.where(is_same_inn, data["next_wp"], np.where(inn2_last, final_wp_inn2, data["win_prob"]))
    data["post_wp"] = post_wp

    # Win Probability Added
    data["wpa_bat"] = data["post_wp"] - data["win_prob"]
    data["wpa_bowl"] = -data["wpa_bat"]

    # Normalized WPA by Expected Swing (Leverage + 0.05)
    data["nwpa_bat"] = data["wpa_bat"] / (data["leverage_index"] + 0.05)
    data["nwpa_bowl"] = data["wpa_bowl"] / (data["leverage_index"] + 0.05)

    # Compute Leave-One-Match-Out (LOMO) expected state baselines
    data = compute_lomo_state_expectations(data)

    return data


def compute_lomo_state_expectations(df: pd.DataFrame) -> pd.DataFrame:
    """Computes exact Leave-One-Match-Out expectations for runs, dismissals, and NWPA in each state."""
    # Batting state: (phase, wih_bucket, bowler_type)
    bat_state_cols = ["phase", "wih_bucket", "bowler_type"]
    match_bat = df.groupby(["match_id"] + bat_state_cols, observed=True).agg(
        m_runs=("runs", "sum"),
        m_wkt=("is_wicket", "sum"),
        m_nwpa=("nwpa_bat", "sum"),
        m_balls=("runs", "count")
    ).reset_index()

    tot_bat = match_bat.groupby(bat_state_cols, observed=True).agg(
        tot_runs=("m_runs", "sum"),
        tot_wkt=("m_wkt", "sum"),
        tot_nwpa=("m_nwpa", "sum"),
        tot_balls=("m_balls", "sum")
    ).reset_index()

    m_merged_bat = match_bat.merge(tot_bat, on=bat_state_cols, how="left")
    m_merged_bat["lomo_balls"] = m_merged_bat["tot_balls"] - m_merged_bat["m_balls"]
    m_merged_bat["exp_runs_bat"] = (m_merged_bat["tot_runs"] - m_merged_bat["m_runs"]) / np.maximum(m_merged_bat["lomo_balls"], 1)
    m_merged_bat["exp_wkt_bat"] = (m_merged_bat["tot_wkt"] - m_merged_bat["m_wkt"]) / np.maximum(m_merged_bat["lomo_balls"], 1)
    m_merged_bat["exp_nwpa_bat"] = (m_merged_bat["tot_nwpa"] - m_merged_bat["m_nwpa"]) / np.maximum(m_merged_bat["lomo_balls"], 1)

    df = df.merge(
        m_merged_bat[["match_id"] + bat_state_cols + ["exp_runs_bat", "exp_wkt_bat", "exp_nwpa_bat"]],
        on=["match_id"] + bat_state_cols,
        how="left"
    )

    # Bowling state: (phase, wih_bucket, order_bucket)
    bowl_state_cols = ["phase", "wih_bucket", "order_bucket"]
    match_bowl = df.groupby(["match_id"] + bowl_state_cols, observed=True).agg(
        m_runs_conceded=("total_delivery_runs", "sum"),
        m_wkt_taken=("is_wicket", "sum"),
        m_nwpa_bowl=("nwpa_bowl", "sum"),
        m_balls_bowled=("total_delivery_runs", "count")
    ).reset_index()

    tot_bowl = match_bowl.groupby(bowl_state_cols, observed=True).agg(
        tot_runs_conceded=("m_runs_conceded", "sum"),
        tot_wkt_taken=("m_wkt_taken", "sum"),
        tot_nwpa_bowl=("m_nwpa_bowl", "sum"),
        tot_balls_bowled=("m_balls_bowled", "sum")
    ).reset_index()

    m_merged_bowl = match_bowl.merge(tot_bowl, on=bowl_state_cols, how="left")
    m_merged_bowl["lomo_balls_bowl"] = m_merged_bowl["tot_balls_bowled"] - m_merged_bowl["m_balls_bowled"]
    m_merged_bowl["exp_runs_bowl"] = (m_merged_bowl["tot_runs_conceded"] - m_merged_bowl["m_runs_conceded"]) / np.maximum(m_merged_bowl["lomo_balls_bowl"], 1)
    m_merged_bowl["exp_wkt_bowl"] = (m_merged_bowl["tot_wkt_taken"] - m_merged_bowl["m_wkt_taken"]) / np.maximum(m_merged_bowl["lomo_balls_bowl"], 1)
    m_merged_bowl["exp_nwpa_bowl"] = (m_merged_bowl["tot_nwpa_bowl"] - m_merged_bowl["m_nwpa_bowl"]) / np.maximum(m_merged_bowl["lomo_balls_bowl"], 1)

    df = df.merge(
        m_merged_bowl[["match_id"] + bowl_state_cols + ["exp_runs_bowl", "exp_wkt_bowl", "exp_nwpa_bowl"]],
        on=["match_id"] + bowl_state_cols,
        how="left"
    )

    # Deviations from state expectations
    # Batter:
    df["rae_bat"] = df["runs"] - df["exp_runs_bat"].fillna(df["runs"].mean())
    df["wae_bat"] = df["exp_wkt_bat"].fillna(df["is_wicket"].mean()) - df["is_wicket"]  # positive = preserved wicket
    df["nwpa_ae_bat"] = df["nwpa_bat"] - df["exp_nwpa_bat"].fillna(0.0)

    # Bowler:
    df["rse_bowl"] = df["exp_runs_bowl"].fillna(df["total_delivery_runs"].mean()) - df["total_delivery_runs"]  # positive = runs saved
    df["wae_bowl"] = df["is_wicket"] - df["exp_wkt_bowl"].fillna(df["is_wicket"].mean())  # positive = extra wicket taken
    df["nwpa_ae_bowl"] = df["nwpa_bowl"] - df["exp_nwpa_bowl"].fillna(0.0)

    return df


def compute_stratified_ratings(
    df: pd.DataFrame,
    role: str = "batter",
    min_high_balls: int = 60,
    innings: int = None
) -> pd.DataFrame:
    """
    Computes player ratings stratified by (wih_bucket x phase) to eliminate Simpson's paradox:
    Rating = Sum_k [ w_k * (High_Perf_k - Low_Perf_k) ]
    Also computes Absolute High Pressure Performance and applies Empirical Bayes shrinkage.
    """
    validate_ratings_input(df)

    sub_df = df.copy()
    if innings is not None:
        sub_df = sub_df[sub_df["innings"] == innings].copy()

    # Filter to legal balls for delivery counting and rates
    legal_df = sub_df[sub_df["is_legal"]].copy()

    id_col = "striker_id" if role == "batter" else "bowler_id"
    name_col = "striker_name" if role == "batter" else "bowler_name"
    nwpa_col = "nwpa_bat" if role == "batter" else "nwpa_bowl"
    runs_diff_col = "rae_bat" if role == "batter" else "rse_bowl"
    wkt_diff_col = "wae_bat" if role == "batter" else "wae_bowl"
    raw_runs_col = "runs" if role == "batter" else "total_delivery_runs"

    strata_cols = ["wih_bucket", "phase"]

    # Filter eligible players based on High Pressure legal balls
    high_balls = legal_df[legal_df["pressure_band_lev"] == "High"].groupby(id_col).size()
    eligible_ids = set(high_balls[high_balls >= min_high_balls].index)

    if not eligible_ids:
        return pd.DataFrame()

    eligible_df = legal_df[legal_df[id_col].isin(eligible_ids)].copy()

    # Stratified means by player, stratum, and pressure band
    strat_means = eligible_df.groupby([id_col, "pressure_band_lev"] + strata_cols, observed=True).agg(
        n_balls=(nwpa_col, "count"),
        mean_nwpa=(nwpa_col, "mean"),
        mean_runs_diff=(runs_diff_col, "mean"),
        mean_wkt_diff=(wkt_diff_col, "mean"),
        raw_runs=(raw_runs_col, "sum"),
        raw_wkts=("is_wicket", "sum")
    ).reset_index()

    # Population stratum means for low pressure as baseline prior
    pop_low = eligible_df[eligible_df["pressure_band_lev"] == "Low"].groupby(strata_cols, observed=True).agg(
        pop_low_nwpa=(nwpa_col, "mean"),
        pop_low_runs=(runs_diff_col, "mean"),
        pop_low_wkt=(wkt_diff_col, "mean")
    ).reset_index()

    player_results = []
    names_map = eligible_df.groupby(id_col)[name_col].last().to_dict()

    for pid in eligible_ids:
        p_strat = strat_means[strat_means[id_col] == pid]
        p_high = p_strat[p_strat["pressure_band_lev"] == "High"]
        p_low = p_strat[p_strat["pressure_band_lev"] == "Low"]

        tot_high_balls = p_high["n_balls"].sum()
        if tot_high_balls == 0:
            continue

        tot_low_balls = p_low["n_balls"].sum()
        raw_high_runs = p_high["raw_runs"].sum()
        raw_high_wkts = p_high["raw_wkts"].sum()

        # Merge High with Low in each stratum
        merged = p_high.merge(p_low, on=strata_cols, how="left", suffixes=("_h", "_l"))
        merged = merged.merge(pop_low, on=strata_cols, how="left")

        # If player has no low-pressure balls in that stratum, fallback to population low baseline
        baseline_nwpa = np.where(merged["mean_nwpa_l"].notna(), merged["mean_nwpa_l"], merged["pop_low_nwpa"])
        baseline_runs = np.where(merged["mean_runs_diff_l"].notna(), merged["mean_runs_diff_l"], merged["pop_low_runs"])
        baseline_wkt = np.where(merged["mean_wkt_diff_l"].notna(), merged["mean_wkt_diff_l"], merged["pop_low_wkt"])

        # Differences in stratum
        diff_nwpa = merged["mean_nwpa_h"] - baseline_nwpa
        diff_runs = merged["mean_runs_diff_h"] - baseline_runs
        diff_wkt = merged["mean_wkt_diff_h"] - baseline_wkt

        # Weights proportional to player's high pressure deliveries in each stratum
        weights = merged["n_balls_h"] / tot_high_balls

        stratified_nwpa_diff = (diff_nwpa * weights).sum()
        stratified_runs_diff_100 = (diff_runs * weights).sum() * 100.0
        stratified_wkt_diff_100 = (diff_wkt * weights).sum() * 100.0

        # Absolute high pressure metrics
        abs_nwpa = (merged["mean_nwpa_h"] * weights).sum()
        abs_rae_100 = (merged["mean_runs_diff_h"] * weights).sum() * 100.0
        abs_wae_100 = (merged["mean_wkt_diff_h"] * weights).sum() * 100.0

        # Raw rates in high pressure
        sr_high = (raw_high_runs / tot_high_balls) * 100.0
        econ_high = (raw_high_runs / (tot_high_balls / 6.0)) if role == "bowler" else np.nan
        dis_pct_high = (raw_high_wkts / tot_high_balls) * 100.0

        player_results.append({
            "player_id": pid,
            "player_name": names_map.get(pid, f"ID_{pid}"),
            "high_pressure_balls": tot_high_balls,
            "low_pressure_balls": tot_low_balls,
            "differential_rating_raw": stratified_nwpa_diff,
            "stratified_runs_diff_100": stratified_runs_diff_100,
            "stratified_wkt_diff_100": stratified_wkt_diff_100,
            "abs_pressure_nwpa": abs_nwpa,
            "abs_rae_100": abs_rae_100,
            "abs_wae_100": abs_wae_100,
            "sr_high": sr_high,
            "econ_high": econ_high,
            "dis_pct_high": dis_pct_high
        })

    res_df = pd.DataFrame(player_results)
    if res_df.empty:
        return res_df

    # Empirical Bayes Shrinkage on differential rating
    res_df = apply_empirical_bayes_shrinkage(res_df, target_col="differential_rating_raw", shrunk_col="differential_rating_eb")
    # Empirical Bayes Shrinkage on absolute pressure NWPA
    res_df = apply_empirical_bayes_shrinkage(res_df, target_col="abs_pressure_nwpa", shrunk_col="abs_pressure_nwpa_eb")

    # Primary composite rating: scaled to 0-100 or standardized index
    # We sort primarily by Empirical Bayes Differential Rating
    res_df = res_df.sort_values("differential_rating_eb", ascending=False).reset_index(drop=True)
    res_df["rank"] = res_df.index + 1

    return res_df


def apply_empirical_bayes_shrinkage(df: pd.DataFrame, target_col: str, shrunk_col: str) -> pd.DataFrame:
    """Applies Empirical Bayes shrinkage toward population grand mean based on ball count variance."""
    k = len(df)
    if k <= 2:
        df[shrunk_col] = df[target_col]
        return df

    y = df[target_col].to_numpy()
    n = df["high_pressure_balls"].to_numpy().astype(float)

    mu_0 = np.mean(y)
    # Estimate within-unit variance from pooled residuals
    sigma2_within = np.var(y) * np.median(n)
    v_i = sigma2_within / np.maximum(n, 1.0)

    # Between-unit variance tau^2
    var_y = np.var(y, ddof=1)
    mean_vi = np.mean(v_i)
    tau2 = max(1e-6, var_y - mean_vi)

    # Shrinkage weights
    lambda_i = tau2 / (tau2 + v_i)
    df[shrunk_col] = lambda_i * y + (1.0 - lambda_i) * mu_0

    return df


def compute_match_bootstrap_ci(
    df: pd.DataFrame,
    role: str = "batter",
    top_pids: list = None,
    min_high_balls: int = 60,
    n_boot: int = 500,
    seed: int = 42
) -> dict:
    """Computes match-level block bootstrap 95% confidence intervals for selected top players."""
    validate_ratings_input(df)

    rng = np.random.default_rng(seed)
    unique_matches = df["match_id"].unique()
    n_matches = len(unique_matches)

    boot_ratings = {pid: [] for pid in top_pids}

    print(f"  Running {n_boot} match-level bootstrap iterations for {role}s...")

    for b in range(n_boot):
        boot_matches = rng.choice(unique_matches, size=n_matches, replace=True)
        # Create bootstrap dataframe by sampling matches
        # Frequency of sampled matches
        m_counts = pd.Series(boot_matches).value_counts()
        boot_sub = df[df["match_id"].isin(m_counts.index)].copy()
        boot_sub["weight"] = boot_sub["match_id"].map(m_counts)

        # Recompute ratings on resampled subset
        # To make bootstrap fast, recompute weighted means
        id_col = "striker_id" if role == "batter" else "bowler_id"
        nwpa_col = "nwpa_bat" if role == "batter" else "nwpa_bowl"

        sub_high = boot_sub[(boot_sub["pressure_band_lev"] == "High") & boot_sub["is_legal"]]
        sub_low = boot_sub[(boot_sub["pressure_band_lev"] == "Low") & boot_sub["is_legal"]]

        h_agg = sub_high.groupby([id_col, "wih_bucket", "phase"], observed=True).apply(
            lambda g: pd.Series({"wm_nwpa": np.average(g[nwpa_col], weights=g["weight"]), "w_cnt": g["weight"].sum()})
        ).reset_index()

        l_agg = sub_low.groupby([id_col, "wih_bucket", "phase"], observed=True).apply(
            lambda g: pd.Series({"wm_nwpa_l": np.average(g[nwpa_col], weights=g["weight"])})
        ).reset_index()

        for pid in top_pids:
            ph = h_agg[h_agg[id_col] == pid]
            if ph.empty or ph["w_cnt"].sum() < 30:
                continue
            pl = l_agg[l_agg[id_col] == pid]
            mrg = ph.merge(pl, on=["wih_bucket", "phase"], how="left")
            base_l = mrg["wm_nwpa_l"].fillna(0.0)
            diff = mrg["wm_nwpa"] - base_l
            w = mrg["w_cnt"] / mrg["w_cnt"].sum()
            boot_ratings[pid].append(float((diff * w).sum()))

    ci_results = {}
    for pid in top_pids:
        vals = boot_ratings[pid]
        if len(vals) >= 50:
            ci_results[pid] = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))
        else:
            ci_results[pid] = (np.nan, np.nan)

    return ci_results


def run_rank_stability_suite(df: pd.DataFrame, role: str = "batter", min_high_balls: int = 60) -> dict:
    """
    Executes four comprehensive stability evaluations:
    1. Split-Half Reliability (Odd vs Even Match IDs)
    2. Season-to-Season Stability (2022-2023 vs 2024-2025)
    3. Metric Specification Sensitivity (Percentile Rank vs Absolute Leverage threshold)
    4. Data Filtering Sensitivity (With vs Without Approximate-Score Matches)
    """
    validate_ratings_input(df)

    id_col = "striker_id" if role == "batter" else "bowler_id"
    results = {}

    # 1. Split-Half (Odd vs Even Match ID)
    df_odd = df[df["match_id"] % 2 == 1].copy()
    df_even = df[df["match_id"] % 2 == 0].copy()

    r_odd = compute_stratified_ratings(df_odd, role=role, min_high_balls=min_high_balls // 2)
    r_even = compute_stratified_ratings(df_even, role=role, min_high_balls=min_high_balls // 2)

    merged_half = r_odd.merge(r_even, on="player_id", suffixes=("_odd", "_even"))
    if len(merged_half) >= 10:
        sp_r, sp_p = stats.spearmanr(merged_half["differential_rating_eb_odd"], merged_half["differential_rating_eb_even"])
        pe_r, pe_p = stats.pearsonr(merged_half["differential_rating_eb_odd"], merged_half["differential_rating_eb_even"])
        results["split_half"] = {
            "n_players": len(merged_half),
            "spearman_rho": float(sp_r),
            "spearman_p": float(sp_p),
            "pearson_r": float(pe_r)
        }
    else:
        results["split_half"] = {"n_players": len(merged_half), "spearman_rho": np.nan, "pearson_r": np.nan}

    # 2. Season-to-Season (Early vs Late)
    # Check seasons in data
    seasons = sorted(df["season"].dropna().unique())
    mid_idx = len(seasons) // 2
    early_seasons = seasons[:mid_idx]
    late_seasons = seasons[mid_idx:]

    df_early = df[df["season"].isin(early_seasons)].copy()
    df_late = df[df["season"].isin(late_seasons)].copy()

    r_early = compute_stratified_ratings(df_early, role=role, min_high_balls=min_high_balls // 2)
    r_late = compute_stratified_ratings(df_late, role=role, min_high_balls=min_high_balls // 2)

    merged_season = r_early.merge(r_late, on="player_id", suffixes=("_early", "_late"))
    if len(merged_season) >= 10:
        sp_s, _ = stats.spearmanr(merged_season["differential_rating_eb_early"], merged_season["differential_rating_eb_late"])
        pe_s, _ = stats.pearsonr(merged_season["differential_rating_eb_early"], merged_season["differential_rating_eb_late"])
        results["season_to_season"] = {
            "n_players": len(merged_season),
            "spearman_rho": float(sp_s),
            "pearson_r": float(pe_s),
            "early_seasons": [str(s) for s in early_seasons],
            "late_seasons": [str(s) for s in late_seasons]
        }
    else:
        results["season_to_season"] = {"n_players": len(merged_season), "spearman_rho": np.nan, "pearson_r": np.nan}

    # 3. Percentile Rank vs Absolute Leverage (> 1.5)
    df_abs = df.copy()
    df_abs["pressure_band_lev"] = pd.cut(
        df_abs["leverage_index"],
        bins=[-np.inf, 0.75, 1.5, np.inf],
        labels=["Low", "Medium", "High"]
    )
    r_pct = compute_stratified_ratings(df, role=role, min_high_balls=min_high_balls)
    r_abs = compute_stratified_ratings(df_abs, role=role, min_high_balls=min_high_balls)

    merged_spec = r_pct.merge(r_abs, on="player_id", suffixes=("_pct", "_abs"))
    if len(merged_spec) >= 10:
        sp_spec, _ = stats.spearmanr(merged_spec["differential_rating_eb_pct"], merged_spec["differential_rating_eb_abs"])
        results["percentile_vs_absolute"] = {
            "n_players": len(merged_spec),
            "spearman_rho": float(sp_spec)
        }
    else:
        results["percentile_vs_absolute"] = {"n_players": len(merged_spec), "spearman_rho": np.nan}

    # 4. With vs Without Approximate Score Matches
    # Reconciled exact only: (margin_reconciled == True and approximate_score == False)
    df_exact = df[(~df["approximate_score"]) | (df["innings"] == 1)].copy()
    r_all = compute_stratified_ratings(df, role=role, min_high_balls=min_high_balls)
    r_exact = compute_stratified_ratings(df_exact, role=role, min_high_balls=min_high_balls)

    merged_approx = r_all.merge(r_exact, on="player_id", suffixes=("_all", "_exact"))
    if len(merged_approx) >= 10:
        sp_app, _ = stats.spearmanr(merged_approx["differential_rating_eb_all"], merged_approx["differential_rating_eb_exact"])
        results["with_vs_without_approximate"] = {
            "n_players": len(merged_approx),
            "spearman_rho": float(sp_app)
        }
    else:
        results["with_vs_without_approximate"] = {"n_players": len(merged_approx), "spearman_rho": np.nan}

    return results
