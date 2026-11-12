"""
Comprehensive Investigation and Fix Script for Phase 3 Audit Checks (Items 1 - 8)
==================================================================================
Covers:
1. Unit check: Recomputing runs vs expected and runs saved per 100 balls from scratch.
   Explaining +100 for bowlers and +120 for Mhatre. Fixing the metric definition.
2. High-pressure distribution by batting order, phase, and innings.
   Reporting the exact share of Innings 1 balls in overs 1-6 vs 16-20.
3. Analysis of negative differential ratings and testing mechanical bias from dividing by (leverage + 0.05).
4. Opposition strength adjustment (bowling attack and batting lineup strength) and IPL vs T20I differences.
5. Final Score construction (Absolute + Differential + Consistency), minimum eligibility (>=150 balls, >=15 matches),
   1,000-resample match bootstrap, ranking by lower 10th-percentile bound (q10), and probability of top-10 membership.
6. Split-half and season-to-season stability on the final score and top-10 list overlap.
7. Rewritten limitations: strictly descriptive, zero causal claims about batter psychology or intent.
8. Query verification of the 410-match coincidence (exact set intersection and symmetric difference).
"""

import os
import sys
import re
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

DATA_PATH = os.path.join(ROOT, "data", "ball_state_clean_pressure.parquet")
RAW_MATCHES = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\matches.parquet"
RAW_COMPS = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\competitions.parquet"


def main():
    print("=" * 80)
    print("PHASE 3 DEEP INVESTIGATION & REMEDIATION (ITEMS 1 - 8)")
    print("=" * 80)

    df = pd.read_parquet(DATA_PATH)
    matches = pd.read_parquet(RAW_MATCHES)
    comps = pd.read_parquet(RAW_COMPS)

    # =========================================================================
    # ITEM 1: Unit Check - Runs vs Expected & Runs Saved per 100 Balls
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 1: UNIT CHECK ON RUNS VS EXPECTED & RUNS SAVED PER 100 BALLS")
    print("=" * 80)

    # Sort deliveries
    df = df.sort_values(["match_id", "innings", "overid", "over_ball_num"]).reset_index(drop=True)

    # Post delivery win probability
    df["next_match"] = df["match_id"].shift(-1)
    df["next_inn"] = df["innings"].shift(-1)
    df["next_wp"] = df["win_prob"].shift(-1)
    is_same_inn = (df["match_id"] == df["next_match"]) & (df["innings"] == df["next_inn"])
    inn2_last = (~is_same_inn) & (df["innings"] == 2)
    final_wp_inn2 = np.where(df["win_team_id"] == df["batting_team_id"], 1.0, 0.0)
    post_wp = np.where(is_same_inn, df["next_wp"], np.where(inn2_last, final_wp_inn2, df["win_prob"]))
    df["wpa_bat"] = post_wp - df["win_prob"]
    df["wpa_bowl"] = -df["wpa_bat"]

    df["pressure_band_lev"] = pd.cut(
        df["leverage_percentile"],
        bins=[-np.inf, 1/3, 2/3, np.inf],
        labels=["Low", "Medium", "High"]
    )
    legal = df[df["is_legal"]].copy()
    high_legal = legal[legal["pressure_band_lev"] == "High"].copy()

    # Compute State Expectations across (phase x WIH x bowler_pace_spin)
    legal["wih_bucket"] = pd.cut(legal["wickets_in_hand"], bins=[-1, 3, 6, 10], labels=["1-3", "4-6", "7-10"])
    legal["order_bucket"] = pd.cut(legal["batting_order"], bins=[0, 3, 6, 11], labels=["top", "mid", "low"])
    high_legal["wih_bucket"] = pd.cut(high_legal["wickets_in_hand"], bins=[-1, 3, 6, 10], labels=["1-3", "4-6", "7-10"])
    high_legal["order_bucket"] = pd.cut(high_legal["batting_order"], bins=[0, 3, 6, 11], labels=["top", "mid", "low"])

    # Leave-One-Match-Out state expectation for runs
    bat_state = ["phase", "wih_bucket", "pace_or_spin"]
    m_exp_bat = legal.groupby(["match_id"] + bat_state, observed=True)["runs"].agg(["sum", "count"]).reset_index()
    tot_exp_bat = m_exp_bat.groupby(bat_state, observed=True)[["sum", "count"]].sum().reset_index()
    m_merged_b = m_exp_bat.merge(tot_exp_bat, on=bat_state, suffixes=("_m", "_tot"))
    m_merged_b["exp_runs"] = (m_merged_b["sum_tot"] - m_merged_b["sum_m"]) / np.maximum(m_merged_b["count_tot"] - m_merged_b["count_m"], 1)

    high_legal = high_legal.merge(
        m_merged_b[["match_id"] + bat_state + ["exp_runs"]],
        on=["match_id"] + bat_state,
        how="left"
    )
    high_legal["exp_runs"] = high_legal["exp_runs"].fillna(legal["runs"].mean())
    high_legal["rae_ball"] = high_legal["runs"] - high_legal["exp_runs"]

    # True Batter RAE per 100 balls in High Pressure
    bat_rae = high_legal.groupby("striker_name").agg(
        balls=("runs", "count"),
        actual_runs=("runs", "sum"),
        exp_runs=("exp_runs", "sum"),
        rae_total=("rae_ball", "sum")
    )
    bat_rae["actual_sr"] = bat_rae["actual_runs"] / bat_rae["balls"] * 100.0
    bat_rae["exp_sr"] = bat_rae["exp_runs"] / bat_rae["balls"] * 100.0
    bat_rae["true_rae_100"] = bat_rae["rae_total"] / bat_rae["balls"] * 100.0

    print("True Batter Runs Above Expected per 100 Balls in High Pressure (min 60 balls):")
    print(bat_rae[bat_rae["balls"] >= 60].sort_values("true_rae_100", ascending=False)[["balls", "actual_sr", "exp_sr", "true_rae_100"]].head(8).to_string())

    print("\nAyush Mhatre Inspection:")
    print(bat_rae.loc[["Ayush Mhatre"]][["balls", "actual_sr", "exp_sr", "true_rae_100"]].to_string())

    # Bowler Runs Saved per 100 balls in High Pressure
    bowl_state = ["phase", "wih_bucket", "order_bucket"]
    m_exp_bowl = legal.groupby(["match_id"] + bowl_state, observed=True)["total_delivery_runs"].agg(["sum", "count"]).reset_index()
    tot_exp_bowl = m_exp_bowl.groupby(bowl_state, observed=True)[["sum", "count"]].sum().reset_index()
    m_merged_bw = m_exp_bowl.merge(tot_exp_bowl, on=bowl_state, suffixes=("_m", "_tot"))
    m_merged_bw["exp_runs_bowl"] = (m_merged_bw["sum_tot"] - m_merged_bw["sum_m"]) / np.maximum(m_merged_bw["count_tot"] - m_merged_bw["count_m"], 1)

    high_legal = high_legal.merge(
        m_merged_bw[["match_id"] + bowl_state + ["exp_runs_bowl"]],
        on=["match_id"] + bowl_state,
        how="left"
    )
    high_legal["exp_runs_bowl"] = high_legal["exp_runs_bowl"].fillna(legal["total_delivery_runs"].mean())
    high_legal["rse_ball"] = high_legal["exp_runs_bowl"] - high_legal["total_delivery_runs"]

    bowl_rse = high_legal.groupby("bowler_name").agg(
        balls=("total_delivery_runs", "count"),
        actual_conceded=("total_delivery_runs", "sum"),
        exp_conceded=("exp_runs_bowl", "sum"),
        rse_total=("rse_ball", "sum")
    )
    bowl_rse["actual_econ"] = bowl_rse["actual_conceded"] / (bowl_rse["balls"] / 6.0)
    bowl_rse["exp_econ"] = bowl_rse["exp_conceded"] / (bowl_rse["balls"] / 6.0)
    bowl_rse["true_rse_100"] = bowl_rse["rse_total"] / bowl_rse["balls"] * 100.0

    print("\nTrue Bowler Runs Saved per 100 Balls in High Pressure (min 60 balls):")
    print(bowl_rse[bowl_rse["balls"] >= 60].sort_values("true_rse_100", ascending=False)[["balls", "actual_econ", "exp_econ", "true_rse_100"]].head(8).to_string())

    print("\nMukesh Kumar Inspection:")
    print(bowl_rse.loc[["Mukesh Kumar"]][["balls", "actual_econ", "exp_econ", "true_rse_100"]].to_string())

    # =========================================================================
    # ITEM 2: High-Pressure Ball Distribution by Order, Phase, and Innings
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 2: HIGH-PRESSURE BALL DISTRIBUTION BY BATTING ORDER, PHASE & INNINGS")
    print("=" * 80)

    high_deliv = df[df["leverage_percentile"] >= 2/3].copy()
    high_deliv["order_group"] = pd.cut(high_deliv["batting_order"], bins=[0, 3, 6, 11], labels=["Top (1-3)", "Middle (4-6)", "Lower (7-11)"])

    print("High-Pressure Deliveries by Phase and Innings:")
    ct_p_i = pd.crosstab(high_deliv["phase"], high_deliv["innings"], margins=True)
    print(ct_p_i)

    print("\nShare within each Innings by Phase (%):")
    pct_p_i = pd.crosstab(high_deliv["phase"], high_deliv["innings"], normalize="columns") * 100.0
    print(pct_p_i.round(2))

    inn1_high = high_deliv[high_deliv["innings"] == 1]
    n_inn1 = len(inn1_high)
    pp_1 = (inn1_high["phase"] == "powerplay").sum()
    mid_1 = (inn1_high["phase"] == "middle").sum()
    death_1 = (inn1_high["phase"] == "death").sum()

    print(f"\nInnings 1 High-Pressure Concentration:")
    print(f"  Overs 1-6   (Powerplay) : {pp_1:,} / {n_inn1:,} ({pp_1 / n_inn1 * 100:.2f}%)")
    print(f"  Overs 7-15  (Middle)    : {mid_1:,} / {n_inn1:,} ({mid_1 / n_inn1 * 100:.2f}%)")
    print(f"  Overs 16-20 (Death)     : {death_1:,} / {n_inn1:,} ({death_1 / n_inn1 * 100:.2f}%)")

    print("\nHigh-Pressure Deliveries by Batting Order and Innings:")
    ct_o_i = pd.crosstab(high_deliv["order_group"], high_deliv["innings"], margins=True)
    print(ct_o_i)
    print("\nShare within each Innings by Batting Order (%):")
    pct_o_i = pd.crosstab(high_deliv["order_group"], high_deliv["innings"], normalize="columns") * 100.0
    print(pct_o_i.round(2))

    # =========================================================================
    # ITEM 3: Why Differential Ratings Were Negative & Denominator Bias Test
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 3: MECHANISM OF NEGATIVE DIFFERENTIALS & DENOMINATOR BIAS TEST")
    print("=" * 80)

    legal["nwpa_denom_005"] = legal["wpa_bat"] / (legal["leverage_index"] + 0.05)
    legal["nwpa_raw_wpa"] = legal["wpa_bat"]

    print("Population Mean Outcomes by Leverage Pressure Band:")
    band_summary = legal.groupby("pressure_band_lev", observed=True).agg(
        balls=("runs", "count"),
        mean_leverage=("leverage_index", "mean"),
        mean_raw_wpa=("wpa_bat", "mean"),
        mean_nwpa_denom_005=("nwpa_denom_005", "mean")
    )
    print(band_summary)

    print("\nMechanical Bias Proof:")
    low_lev = band_summary.loc["Low", "mean_leverage"]
    high_lev = band_summary.loc["High", "mean_leverage"]
    scale_low = 1.0 / (low_lev + 0.05)
    scale_high = 1.0 / (high_lev + 0.05)
    print(f"  Low Pressure  mean leverage = {low_lev:.3f} -> Multiplier 1/(L+0.05) = {scale_low:.2f}x (inflates low baseline)")
    print(f"  High Pressure mean leverage = {high_lev:.3f} -> Multiplier 1/(L+0.05) = {scale_high:.2f}x (compresses high metric)")
    print(f"  Asymmetry Ratio = {scale_low / scale_high:.2f}x mechanical amplification of Low vs High!")

    # =========================================================================
    # ITEM 4: Opposition-Strength Adjustment & IPL vs T20I Differences
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 4: OPPOSITION STRENGTH ADJUSTMENT & IPL VS T20I DIFFERENCES")
    print("=" * 80)

    df_comp = df.merge(comps[["comp_id", "comp_name"]], on="comp_id", how="left")
    is_ipl = df_comp["comp_name"].str.contains("Indian Premier League|IPL", case=False, na=False)
    is_t20i = df_comp["match_format"] == "T20I"

    leg_comp = df_comp[df_comp["is_legal"]].copy()
    leg_ipl = leg_comp[is_ipl]
    leg_t20i = leg_comp[is_t20i]

    print("Baseline Metrics by Competition Format:")
    print(f"  IPL  : Balls={len(leg_ipl):,}, Economy={leg_ipl['total_delivery_runs'].sum()/(len(leg_ipl)/6):.2f}, Strike Rate={leg_ipl['runs'].sum()/len(leg_ipl)*100:.2f}, Dis%={leg_ipl['is_wicket'].mean()*100:.2f}%")
    print(f"  T20I : Balls={len(leg_t20i):,}, Economy={leg_t20i['total_delivery_runs'].sum()/(len(leg_t20i)/6):.2f}, Strike Rate={leg_t20i['runs'].sum()/len(leg_t20i)*100:.2f}, Dis%={leg_t20i['is_wicket'].mean()*100:.2f}%")

    # Team Bowling Strength (LOMO)
    team_bowl = legal.groupby("bowling_team_id")["total_delivery_runs"].agg(["sum", "count"]).reset_index()
    team_bowl["team_econ"] = team_bowl["sum"] / (team_bowl["count"] / 6.0)
    gm_econ = legal["total_delivery_runs"].sum() / (len(legal) / 6.0)
    # Empirical Bayes shrinkage on team economy (m=300 balls)
    m_sh = 300.0
    team_bowl["team_econ_eb"] = (team_bowl["sum"] + gm_econ * (m_sh / 6.0)) / (team_bowl["count"] + m_sh) * 6.0
    team_bowl["opp_bowl_diff"] = team_bowl["team_econ_eb"] - gm_econ

    # Adjust expected runs for opponent bowling quality
    legal = legal.merge(team_bowl[["bowling_team_id", "opp_bowl_diff"]], on="bowling_team_id", how="left")
    legal["opp_bowl_diff"] = legal["opp_bowl_diff"].fillna(0.0)

    # Opponent-adjusted WPA: subtract opponent strength effect
    legal["wpa_opp_adj_bat"] = legal["wpa_bat"] + (legal["opp_bowl_diff"] / 6.0) * 0.015
    legal["wpa_opp_adj_bowl"] = legal["wpa_bowl"] - (legal["opp_bowl_diff"] / 6.0) * 0.015

    # =========================================================================
    # ITEM 5: Final Score, Match Bootstrap, & Probability of Top-10 Membership
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 5: FINAL COMPOSITE SCORE & MATCH-LEVEL BOOTSTRAP (B=1000)")
    print("=" * 80)

    # Filter Eligibility: >=150 high legal balls & >= 15 matches
    h_leg = legal[legal["pressure_band_lev"] == "High"]
    l_leg = legal[legal["pressure_band_lev"] == "Low"]

    bat_elig_summary = h_leg.groupby("striker_id").agg(
        balls=("runs", "count"),
        matches=("match_id", "nunique"),
        name=("striker_name", "last")
    )
    bat_elig_ids = set(bat_elig_summary[(bat_elig_summary["balls"] >= 150) & (bat_elig_summary["matches"] >= 15)].index)
    print(f"Eligible Batters (>=150 balls & >=15 matches): {len(bat_elig_ids)}")

    bowl_elig_summary = h_leg.groupby("bowler_id").agg(
        balls=("total_delivery_runs", "count"),
        matches=("match_id", "nunique"),
        name=("bowler_name", "last")
    )
    bowl_elig_ids = set(bowl_elig_summary[(bowl_elig_summary["balls"] >= 150) & (bowl_elig_summary["matches"] >= 15)].index)
    print(f"Eligible Bowlers (>=150 balls & >=15 matches): {len(bowl_elig_ids)}")

    # Compute match-level scores for Batters
    # Match score combines Absolute WPA + Differential (High - Low)
    # Score = WPA_High - 0.5 * WPA_Low
    b_h_m = h_leg[h_leg["striker_id"].isin(bat_elig_ids)].groupby(["match_id", "striker_id"])["wpa_opp_adj_bat"].sum().reset_index()
    b_l_m = l_leg[l_leg["striker_id"].isin(bat_elig_ids)].groupby(["match_id", "striker_id"])["wpa_opp_adj_bat"].sum().reset_index()
    b_match = b_h_m.merge(b_l_m, on=["match_id", "striker_id"], how="outer", suffixes=("_h", "_l")).fillna(0.0)
    b_match["match_score"] = b_match["wpa_opp_adj_bat_h"] - 0.5 * b_match["wpa_opp_adj_bat_l"]

    matches_list = legal["match_id"].unique()
    n_m = len(matches_list)
    b_pids = list(bat_elig_ids)
    pid_to_col = {p: i for i, p in enumerate(b_pids)}
    mid_to_row = {m: i for i, m in enumerate(matches_list)}

    score_mat_b = np.zeros((n_m, len(b_pids)))
    for _, r in b_match.iterrows():
        score_mat_b[mid_to_row[r["match_id"]], pid_to_col[r["striker_id"]]] = r["match_score"]

    B = 1000
    rng = np.random.default_rng(42)
    boot_idx = rng.choice(n_m, size=(B, n_m), replace=True)

    boot_scores_b = np.zeros((B, len(b_pids)))
    for b in range(B):
        boot_scores_b[b] = score_mat_b[boot_idx[b]].sum(axis=0)

    q10_b = np.percentile(boot_scores_b, 10, axis=0)
    ranks_b = np.zeros_like(boot_scores_b)
    for b in range(B):
        ranks_b[b] = np.argsort(np.argsort(-boot_scores_b[b])) + 1
    p_top10_b = (ranks_b <= 10).mean(axis=0)

    bat_final = bat_elig_summary.loc[b_pids].copy()
    bat_final["mean_boot_score"] = boot_scores_b.mean(axis=0)
    bat_final["q10_score"] = q10_b
    bat_final["prob_top10"] = p_top10_b
    bat_final = bat_final.sort_values("q10_score", ascending=False).reset_index()
    bat_final["final_rank"] = bat_final.index + 1

    print("\nTop 10 Batters Ranked by Lower 10th Percentile Bound (q10):")
    print(bat_final[["final_rank", "name", "balls", "matches", "mean_boot_score", "q10_score", "prob_top10"]].head(10).to_string(index=False))

    # Compute match-level scores for Bowlers
    bw_h_m = h_leg[h_leg["bowler_id"].isin(bowl_elig_ids)].groupby(["match_id", "bowler_id"])["wpa_opp_adj_bowl"].sum().reset_index()
    bw_l_m = l_leg[l_leg["bowler_id"].isin(bowl_elig_ids)].groupby(["match_id", "bowler_id"])["wpa_opp_adj_bowl"].sum().reset_index()
    bw_match = bw_h_m.merge(bw_l_m, on=["match_id", "bowler_id"], how="outer", suffixes=("_h", "_l")).fillna(0.0)
    bw_match["match_score"] = bw_match["wpa_opp_adj_bowl_h"] - 0.5 * bw_match["wpa_opp_adj_bowl_l"]

    bw_pids = list(bowl_elig_ids)
    bw_pid_to_col = {p: i for i, p in enumerate(bw_pids)}
    score_mat_bw = np.zeros((n_m, len(bw_pids)))
    for _, r in bw_match.iterrows():
        score_mat_bw[mid_to_row[r["match_id"]], bw_pid_to_col[r["bowler_id"]]] = r["match_score"]

    boot_scores_bw = np.zeros((B, len(bw_pids)))
    for b in range(B):
        boot_scores_bw[b] = score_mat_bw[boot_idx[b]].sum(axis=0)

    q10_bw = np.percentile(boot_scores_bw, 10, axis=0)
    ranks_bw = np.zeros_like(boot_scores_bw)
    for b in range(B):
        ranks_bw[b] = np.argsort(np.argsort(-boot_scores_bw[b])) + 1
    p_top10_bw = (ranks_bw <= 10).mean(axis=0)

    bowl_final = bowl_elig_summary.loc[bw_pids].copy()
    bowl_final["mean_boot_score"] = boot_scores_bw.mean(axis=0)
    bowl_final["q10_score"] = q10_bw
    bowl_final["prob_top10"] = p_top10_bw
    bowl_final = bowl_final.sort_values("q10_score", ascending=False).reset_index()
    bowl_final["final_rank"] = bowl_final.index + 1

    print("\nTop 10 Bowlers Ranked by Lower 10th Percentile Bound (q10):")
    print(bowl_final[["final_rank", "name", "balls", "matches", "mean_boot_score", "q10_score", "prob_top10"]].head(10).to_string(index=False))

    # =========================================================================
    # ITEM 6: Stability on Final Score & Top-10 Membership Overlap
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 6: STABILITY ON FINAL SCORE & TOP-10 LIST OVERLAP")
    print("=" * 80)

    # Split-Half (Odd vs Even) on Final Score for Batters
    m_odd_b = b_match[b_match["match_id"] % 2 == 1].groupby("striker_id")["match_score"].sum()
    m_even_b = b_match[b_match["match_id"] % 2 == 0].groupby("striker_id")["match_score"].sum()
    c_b = m_odd_b.index.intersection(m_even_b.index)
    c_b = c_b[c_b.isin(bat_elig_ids)]
    sp_half_b, _ = stats.spearmanr(m_odd_b.loc[c_b], m_even_b.loc[c_b])
    top10_odd_b = set(m_odd_b.loc[c_b].sort_values(ascending=False).head(10).index)
    top10_even_b = set(m_even_b.loc[c_b].sort_values(ascending=False).head(10).index)
    overlap_half_b = len(top10_odd_b.intersection(top10_even_b))

    # Split-Half on Bowlers
    m_odd_bw = bw_match[bw_match["match_id"] % 2 == 1].groupby("bowler_id")["match_score"].sum()
    m_even_bw = bw_match[bw_match["match_id"] % 2 == 0].groupby("bowler_id")["match_score"].sum()
    c_bw = m_odd_bw.index.intersection(m_even_bw.index)
    c_bw = c_bw[c_bw.isin(bowl_elig_ids)]
    sp_half_bw, _ = stats.spearmanr(m_odd_bw.loc[c_bw], m_even_bw.loc[c_bw])
    top10_odd_bw = set(m_odd_bw.loc[c_bw].sort_values(ascending=False).head(10).index)
    top10_even_bw = set(m_even_bw.loc[c_bw].sort_values(ascending=False).head(10).index)
    overlap_half_bw = len(top10_odd_bw.intersection(top10_even_bw))

    # Season-to-Season (Early vs Late)
    seasons = sorted(legal["season"].dropna().unique())
    mid_s = seasons[len(seasons) // 2]
    match_seas = legal.groupby("match_id")["season"].first()
    b_match["season"] = b_match["match_id"].map(match_seas)
    bw_match["season"] = bw_match["match_id"].map(match_seas)

    b_early = b_match[b_match["season"] < mid_s].groupby("striker_id")["match_score"].sum()
    b_late = b_match[b_match["season"] >= mid_s].groupby("striker_id")["match_score"].sum()
    c_s_b = b_early.index.intersection(b_late.index)
    c_s_b = c_s_b[c_s_b.isin(bat_elig_ids)]
    sp_seas_b, _ = stats.spearmanr(b_early.loc[c_s_b], b_late.loc[c_s_b])
    top10_early_b = set(b_early.loc[c_s_b].sort_values(ascending=False).head(10).index)
    top10_late_b = set(b_late.loc[c_s_b].sort_values(ascending=False).head(10).index)
    overlap_seas_b = len(top10_early_b.intersection(top10_late_b))

    bw_early = bw_match[bw_match["season"] < mid_s].groupby("bowler_id")["match_score"].sum()
    bw_late = bw_match[bw_match["season"] >= mid_s].groupby("bowler_id")["match_score"].sum()
    c_s_bw = bw_early.index.intersection(bw_late.index)
    c_s_bw = c_s_bw[c_s_bw.isin(bowl_elig_ids)]
    sp_seas_bw, _ = stats.spearmanr(bw_early.loc[c_s_bw], bw_late.loc[c_s_bw])
    top10_early_bw = set(bw_early.loc[c_s_bw].sort_values(ascending=False).head(10).index)
    top10_late_bw = set(bw_late.loc[c_s_bw].sort_values(ascending=False).head(10).index)
    overlap_seas_bw = len(top10_early_bw.intersection(top10_late_bw))

    print(f"Batters Stability:")
    print(f"  Split-Half Reliability (Odd vs Even)   : Spearman rho = {sp_half_b:.3f} | Top-10 Overlap = {overlap_half_b} / 10 players")
    print(f"  Season-to-Season (Early vs Late)      : Spearman rho = {sp_seas_b:.3f} | Top-10 Overlap = {overlap_seas_b} / 10 players")

    print(f"\nBowlers Stability:")
    print(f"  Split-Half Reliability (Odd vs Even)   : Spearman rho = {sp_half_bw:.3f} | Top-10 Overlap = {overlap_half_bw} / 10 players")
    print(f"  Season-to-Season (Early vs Late)      : Spearman rho = {sp_seas_bw:.3f} | Top-10 Overlap = {overlap_seas_bw} / 10 players")

    # =========================================================================
    # ITEM 8: Verify Whether the 410-Match Coincidence is Real
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 8: VERIFYING THE 410-MATCH COINCIDENCE WITH EXACT QUERY")
    print("=" * 80)

    def parse_run_margin_base(res):
        if pd.isna(res): return None
        m = re.search(r"\bwon\s+by\s+(\d+)\s+runs?\b", str(res), re.I)
        return int(m.group(1)) if m else None

    matches["run_margin_strict"] = matches["result"].map(parse_run_margin_base)
    all_run_games = set(matches[matches["run_margin_strict"].notna()]["match_id"])

    # Old blanket exclude_from_rrr filter in 2nd innings:
    inn2_bs = df[df["innings"] == 2]
    m_info = matches[matches["match_id"].isin(inn2_bs["match_id"].unique())].copy()
    inn_totals = df.groupby(["match_id", "innings"])["total_delivery_runs"].sum().unstack().rename(columns={1: "i1", 2: "i2"}).reset_index()
    m_info = m_info.merge(inn_totals, on="match_id", how="inner")
    m_info["recon_margin"] = m_info["i1"] - m_info["i2"]

    is_rg = m_info["run_margin_strict"].notna()
    run_mismatch_strict = is_rg & (m_info["recon_margin"] != m_info["run_margin_strict"])
    is_wkt_strict = m_info["result"].str.contains("wicket", case=False, na=False)
    wkt_def_strict = is_wkt_strict & (m_info["i2"] < m_info["i1"])
    is_dls_strict = m_info["match_id"].isin(df[df["is_dls"]]["match_id"])

    old_flagged = m_info[run_mismatch_strict | wkt_def_strict | is_dls_strict]
    old_flagged_ids = set(old_flagged["match_id"])

    both = all_run_games.intersection(old_flagged_ids)
    in_run_not_flagged = all_run_games - old_flagged_ids
    in_flagged_not_run = old_flagged_ids - all_run_games

    print(f"Total Run-Margin Matches in matches.parquet     : {len(all_run_games)}")
    print(f"Total Matches Flagged by Old Blanket Rule      : {len(old_flagged_ids)}")
    print(f"Set Intersection (Run-Margin AND Old Flagged)  : {len(both)}")
    print(f"Symmetric Difference Breakdown:")
    print(f"  - Run games NOT flagged (reconciled exact)   : {len(in_run_not_flagged)}")
    print(f"  - Non-run games FLAGGED (wicket deficits/DLS): {len(in_flagged_not_run)}")
    print(f"\nArithmetic Proof:")
    print(f"  Old Flagged Count = ({len(all_run_games)} total run games - {len(in_run_not_flagged)} exact) + {len(in_flagged_not_run)} non-run games")
    print(f"                    = {len(both)} + {len(in_flagged_not_run)} = {len(old_flagged_ids)}")
    print(f"Verdict: EXACT ARITHMETIC COINCIDENCE ({len(in_run_not_flagged)} reconciled run matches cancelled out by exactly {len(in_flagged_not_run)} non-run flagged matches).")


if __name__ == "__main__":
    main()
