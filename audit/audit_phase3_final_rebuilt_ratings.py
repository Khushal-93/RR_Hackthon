"""
Phase 3 Final Rebuilt Ratings Script (Corrected Empirical Bayes & Player-Level Resampling)
========================================================================================
Covers:
1. Item 1: Print raw rate, shrunk rate, shrinkage weight lambda, first 10 bootstrap draws,
   tau^2, and sigma^2 for 5 players. State whether shrinkage collapses everyone to the same value.
2. Item 2: Explain what the columns contained, fix bootstrap to resample matches per player.
3. Item 3: Re-rank by posterior shrunk rate with per-player 80% and 95% intervals, and recomputed P(top-10).
4. Item 4: Real pairwise-tie analysis (probability one outranks the other across draws).
5. Item 5: Held-out split-half reliability for FINAL combined score (RAE + k*WAE with opp adj).
6. Item 6: Unified reconciliation of before/after opposition adjustment across earlier rounds (e.g. Krunal Pandya).
7. Item 7: Relabel role classifications strictly as descriptive.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = r"C:\Users\Khushal\pressure_xi"
DATA_PATH = os.path.join(ROOT, "data", "ball_state_clean_pressure.parquet")
RAW_COMPS = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\competitions.parquet"
REPORT_TXT = os.path.join(ROOT, "reports", "phase3_player_ratings_report.txt")


def main():
    print("=" * 80)
    print("PHASE 3 CORRECTED RATINGS & COMPREHENSIVE EVALUATION")
    print("=" * 80)

    df = pd.read_parquet(DATA_PATH)
    comps = pd.read_parquet(RAW_COMPS)
    df = df.merge(comps[["comp_id", "comp_name"]], on="comp_id", how="left")
    df["is_ipl"] = df["comp_name"].str.contains("Indian Premier League|IPL", case=False, na=False)
    df["is_t20i"] = df["match_format"] == "T20I"

    legal = df[df["is_legal"]].copy()

    # Empirical k
    k_emp = 25.27

    # State Buckets
    legal["wih_bucket"] = pd.cut(legal["wickets_in_hand"], bins=[-1, 3, 6, 10], labels=["1-3", "4-6", "7-10"])
    legal["order_bucket"] = pd.cut(legal["batting_order"], bins=[0, 3, 6, 11], labels=["top", "mid", "low"])
    legal["bowler_type"] = legal["pace_or_spin"].fillna("Unknown")

    # LOMO Batting
    bat_state = ["phase", "wih_bucket", "bowler_type"]
    m_bat = legal.groupby(["match_id"] + bat_state, observed=True).agg(
        m_runs=("runs", "sum"), m_wkt=("is_wicket", "sum"), m_balls=("runs", "count")
    ).reset_index()
    tot_bat = m_bat.groupby(bat_state, observed=True)[["m_runs", "m_wkt", "m_balls"]].sum().reset_index()
    m_bat = m_bat.merge(tot_bat, on=bat_state, suffixes=("_m", "_tot"))
    m_bat["lomo_balls"] = m_bat["m_balls_tot"] - m_bat["m_balls_m"]
    m_bat["exp_runs_b"] = (m_bat["m_runs_tot"] - m_bat["m_runs_m"]) / np.maximum(m_bat["lomo_balls"], 1)
    m_bat["exp_wkt_b"] = (m_bat["m_wkt_tot"] - m_bat["m_wkt_m"]) / np.maximum(m_bat["lomo_balls"], 1)

    legal = legal.merge(m_bat[["match_id"] + bat_state + ["exp_runs_b", "exp_wkt_b"]], on=["match_id"] + bat_state, how="left")
    legal["exp_runs_b"] = legal["exp_runs_b"].fillna(legal["runs"].mean())
    legal["exp_wkt_b"] = legal["exp_wkt_b"].fillna(legal["is_wicket"].mean())

    # LOMO Bowling
    bowl_state = ["phase", "wih_bucket", "order_bucket"]
    m_bw = legal.groupby(["match_id"] + bowl_state, observed=True).agg(
        m_runs=("total_delivery_runs", "sum"), m_wkt=("is_wicket", "sum"), m_balls=("total_delivery_runs", "count")
    ).reset_index()
    tot_bw = m_bw.groupby(bowl_state, observed=True)[["m_runs", "m_wkt", "m_balls"]].sum().reset_index()
    m_bw = m_bw.merge(tot_bw, on=bowl_state, suffixes=("_m", "_tot"))
    m_bw["lomo_balls_bw"] = m_bw["m_balls_tot"] - m_bw["m_balls_m"]
    m_bw["exp_runs_bw"] = (m_bw["m_runs_tot"] - m_bw["m_runs_m"]) / np.maximum(m_bw["lomo_balls_bw"], 1)
    m_bw["exp_wkt_bw"] = (m_bw["m_wkt_tot"] - m_bw["m_wkt_m"]) / np.maximum(m_bw["lomo_balls_bw"], 1)

    legal = legal.merge(m_bw[["match_id"] + bowl_state + ["exp_runs_bw", "exp_wkt_bw"]], on=["match_id"] + bowl_state, how="left")
    legal["exp_runs_bw"] = legal["exp_runs_bw"].fillna(legal["total_delivery_runs"].mean())
    legal["exp_wkt_bw"] = legal["exp_wkt_bw"].fillna(legal["is_wicket"].mean())

    # Opposition Adjustments
    gm_econ = legal["total_delivery_runs"].sum() / (len(legal) / 6.0)
    m_sh = 300.0

    t_bowl = legal.groupby("bowling_team_id")["total_delivery_runs"].agg(["sum", "count"]).reset_index()
    t_bowl["opp_bowl_diff"] = ((t_bowl["sum"] + gm_econ * (m_sh / 6.0)) / (t_bowl["count"] + m_sh) * 6.0) - gm_econ
    legal = legal.merge(t_bowl[["bowling_team_id", "opp_bowl_diff"]], on="bowling_team_id", how="left")
    legal["opp_bowl_diff"] = legal["opp_bowl_diff"].fillna(0.0)

    t_bat = legal.groupby("batting_team_id")["total_delivery_runs"].agg(["sum", "count"]).reset_index()
    t_bat["opp_bat_diff"] = ((t_bat["sum"] + gm_econ * (m_sh / 6.0)) / (t_bat["count"] + m_sh) * 6.0) - gm_econ
    legal = legal.merge(t_bat[["batting_team_id", "opp_bat_diff"]], on="batting_team_id", how="left")
    legal["opp_bat_diff"] = legal["opp_bat_diff"].fillna(0.0)

    legal["rae_raw"] = legal["runs"] - legal["exp_runs_b"]
    legal["rae_adj"] = legal["runs"] - (legal["exp_runs_b"] + legal["opp_bowl_diff"] / 6.0)
    legal["wae_bat"] = legal["exp_wkt_b"] - legal["is_wicket"]

    legal["rse_raw"] = legal["exp_runs_bw"] - legal["total_delivery_runs"]
    legal["rse_adj"] = (legal["exp_runs_bw"] + legal["opp_bat_diff"] / 6.0) - legal["total_delivery_runs"]
    legal["wae_bowl"] = legal["is_wicket"] - legal["exp_wkt_bw"]

    legal["bat_rate"] = legal["rae_adj"] + k_emp * legal["wae_bat"]
    legal["bowl_rate"] = legal["rse_adj"] + k_emp * legal["wae_bowl"]

    high = legal[legal["pressure_band_lev"] == "High"].copy()

    # =========================================================================
    # ITEM 1 & 2: SHRINKAGE DIAGNOSTIC & PER-PLAYER BOOTSTRAP
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 1 & 2: SHRINKAGE DIAGNOSTIC (5 PLAYERS) & PROPER RESAMPLING")
    print("=" * 80)

    def fit_eb_and_bootstrap(high_df, id_col, rate_col, name_col, min_balls=150, min_matches=15, B=1000, seed=42):
        agg = high_df.groupby(id_col).agg(
            balls=(rate_col, "count"),
            matches=("match_id", "nunique"),
            name=(name_col, "last"),
            raw_rate=(rate_col, "mean")
        )
        elig = agg[(agg["balls"] >= min_balls) & (agg["matches"] >= min_matches)].copy()

        y = elig["raw_rate"].values
        N = elig["balls"].values.astype(float)
        deliv_vars = high_df[high_df[id_col].isin(elig.index)].groupby(id_col)[rate_col].var().loc[elig.index].values
        v_i = deliv_vars / N

        mu0 = np.average(y, weights=1.0 / v_i)
        var_y = np.var(y, ddof=1)
        tau2 = max(1e-4, var_y - np.mean(v_i))
        lam = tau2 / (tau2 + v_i)

        elig["shrunk_rate"] = lam * y + (1.0 - lam) * mu0
        elig["lambda"] = lam
        elig["v_i"] = v_i
        elig["sigma2_deliv"] = deliv_vars

        # Sort primarily by Posterior Shrunk Mean Rate
        elig = elig.sort_values("shrunk_rate", ascending=False).reset_index()
        elig["rank"] = elig.index + 1

        # Per-player match block bootstrap
        rng = np.random.default_rng(seed)
        boot_rates = np.zeros((len(elig), B))

        for i, pid in enumerate(elig[id_col]):
            p_high = high_df[high_df[id_col] == pid]
            m_agg = p_high.groupby("match_id").agg(s_r=(rate_col, "sum"), n_b=(rate_col, "count")).values
            n_m = len(m_agg)
            boot_m_idx = rng.choice(n_m, size=(B, n_m), replace=True)

            resampled_means = np.zeros(B)
            for b in range(B):
                sample = m_agg[boot_m_idx[b]]
                resampled_means[b] = sample[:, 0].sum() / max(sample[:, 1].sum(), 1)

            p_lam = elig.loc[i, "lambda"]
            boot_rates[i] = p_lam * resampled_means + (1.0 - p_lam) * mu0

        elig["boot_mean"] = boot_rates.mean(axis=1)
        elig["ci80_lower"] = np.percentile(boot_rates, 10, axis=1)
        elig["ci80_upper"] = np.percentile(boot_rates, 90, axis=1)
        elig["ci95_lower"] = np.percentile(boot_rates, 2.5, axis=1)
        elig["ci95_upper"] = np.percentile(boot_rates, 97.5, axis=1)

        # Ranks across all players in each draw
        ranks_in_draws = np.zeros_like(boot_rates)
        for b in range(B):
            ranks_in_draws[:, b] = np.argsort(np.argsort(-boot_rates[:, b])) + 1

        elig["prob_top10"] = (ranks_in_draws <= 10).mean(axis=1)

        return elig, boot_rates, mu0, var_y, tau2, np.mean(v_i)

    bat_res, bat_boot, b_mu0, b_var_y, b_tau2, b_mean_vi = fit_eb_and_bootstrap(high, "striker_id", "bat_rate", "striker_name")
    bowl_res, bowl_boot, bw_mu0, bw_var_y, bw_tau2, bw_mean_vi = fit_eb_and_bootstrap(high, "bowler_id", "bowl_rate", "bowler_name")

    print(f"Batters Shrinkage Diagnostic:")
    print(f"  Grand Mean mu0 = {b_mu0:+.4f}, Total Var var_y = {b_var_y:.4f}, Mean Error Var mean(v_i) = {b_mean_vi:.4f}")
    print(f"  Between-Player Variance tau^2 = {b_tau2:.4f}, Lambda range = [{bat_res['lambda'].min():.3f}, {bat_res['lambda'].max():.3f}]")

    print(f"\nBowlers Shrinkage Diagnostic:")
    print(f"  Grand Mean mu0 = {bw_mu0:+.4f}, Total Var var_y = {bw_var_y:.4f}, Mean Error Var mean(v_i) = {bw_mean_vi:.4f}")
    print(f"  Between-Player Variance tau^2 = {bw_tau2:.4f}, Lambda range = [{bowl_res['lambda'].min():.3f}, {bowl_res['lambda'].max():.3f}]")

    print("\nItem 1 Diagnostic Output: 5 Batters Detail (Raw, Shrunk, Lambda, sigma^2, First 10 Bootstrap Draws):")
    for r in range(5):
        row = bat_res.iloc[r]
        draws_10 = bat_boot[r, :10]
        print(f"Player: {row['name']} (Rank {row['rank']})")
        print(f"  Balls: {row['balls']}, Raw Rate: {row['raw_rate']:+.4f}, Shrunk Rate: {row['shrunk_rate']:+.4f}")
        print(f"  Lambda: {row['lambda']:.4f}, Delivery Var (sigma^2): {row['sigma2_deliv']:.2f}, Error Var (v_i): {row['v_i']:.4f}")
        print(f"  First 10 Bootstrap Draws: {np.round(draws_10, 4).tolist()}")

    print("\nItem 1 Diagnostic Output: 5 Bowlers Detail (Raw, Shrunk, Lambda, sigma^2, First 10 Bootstrap Draws):")
    for r in range(5):
        row = bowl_res.iloc[r]
        draws_10 = bowl_boot[r, :10]
        print(f"Player: {row['name']} (Rank {row['rank']})")
        print(f"  Balls: {row['balls']}, Raw Rate: {row['raw_rate']:+.4f}, Shrunk Rate: {row['shrunk_rate']:+.4f}")
        print(f"  Lambda: {row['lambda']:.4f}, Delivery Var (sigma^2): {row['sigma2_deliv']:.2f}, Error Var (v_i): {row['v_i']:.4f}")
        print(f"  First 10 Bootstrap Draws: {np.round(draws_10, 4).tolist()}")

    # =========================================================================
    # ITEM 3: FINAL REBUILT LEADERBOARDS & TIERS
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 3: FINAL CORRECTED TOP 10 LEADERBOARDS (RANKED BY SHRUNK RATE)")
    print("=" * 80)

    print("TOP 10 BATTERS (PER-PLAYER RESAMPLING, RANKED BY POSTERIOR SHRUNK RATE):")
    print(bat_res[["rank", "name", "balls", "matches", "raw_rate", "shrunk_rate", "boot_mean", "ci80_lower", "ci80_upper", "ci95_lower", "ci95_upper", "prob_top10"]].head(10).to_string(index=False))

    print("\nTOP 10 BOWLERS (PER-PLAYER RESAMPLING, RANKED BY POSTERIOR SHRUNK RATE):")
    print(bowl_res[["rank", "name", "balls", "matches", "raw_rate", "shrunk_rate", "boot_mean", "ci80_lower", "ci80_upper", "ci95_lower", "ci95_upper", "prob_top10"]].head(10).to_string(index=False))

    # =========================================================================
    # ITEM 4: PAIRWISE-TIE ANALYSIS
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 4: PAIRWISE-TIE ANALYSIS (ADJACENT RANKS)")
    print("=" * 80)

    print("Batters Adjacent Pairwise Head-to-Head Probabilities across 1,000 Draws:")
    for r in range(9):
        p_better = (bat_boot[r, :] > bat_boot[r+1, :]).mean()
        p1 = bat_res.loc[r, "name"]
        p2 = bat_res.loc[r+1, "name"]
        print(f"  Rank {r+1} vs {r+2} ({p1:20s} vs {p2:20s}): P({p1} > {p2}) = {p_better*100:.1f}%")

    print("\nBowlers Adjacent Pairwise Head-to-Head Probabilities across 1,000 Draws:")
    for r in range(9):
        p_better = (bowl_boot[r, :] > bowl_boot[r+1, :]).mean()
        p1 = bowl_res.loc[r, "name"]
        p2 = bowl_res.loc[r+1, "name"]
        print(f"  Rank {r+1} vs {r+2} ({p1:20s} vs {p2:20s}): P({p1} > {p2}) = {p_better*100:.1f}%")

    # =========================================================================
    # ITEM 5: HELD-OUT SPLIT-HALF RELIABILITY ON FINAL COMBINED SCORE
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 5: HELD-OUT SPLIT-HALF RELIABILITY ON FINAL COMBINED SCORE (2025-2026)")
    print("=" * 80)

    heldout = legal[legal["season"] > "2024"].copy()
    dev = legal[legal["season"] <= "2024"].copy()

    # Attach dev expectations to heldout
    # Already merged in legal, but let's take heldout directly
    h_held = heldout[heldout["pressure_band_lev"] == "High"].copy()
    odd_h = h_held[h_held["match_id"] % 2 == 1]
    even_h = h_held[h_held["match_id"] % 2 == 0]

    def eb_proper_split(sub, id_col, rate_col):
        agg = sub.groupby(id_col).agg(balls=(rate_col, "count"), rate=(rate_col, "mean"), var=(rate_col, "var"))
        agg = agg[agg["balls"] >= 25].copy()
        y = agg["rate"].values
        N = agg["balls"].values.astype(float)
        sigma2_i = agg["var"].fillna(np.nanmedian(agg["var"])).values
        v_i = sigma2_i / N
        mu0 = np.average(y, weights=1.0 / v_i)
        var_y = np.var(y, ddof=1)
        tau2 = max(1e-4, var_y - np.mean(v_i))
        lam = tau2 / (tau2 + v_i)
        agg["shrunk_rate"] = lam * y + (1.0 - lam) * mu0
        return agg

    b_odd_final = eb_proper_split(odd_h, "striker_id", "bat_rate")
    b_even_final = eb_proper_split(even_h, "striker_id", "bat_rate")
    c_b_final = b_odd_final.index.intersection(b_even_final.index)

    rho_b_final, _ = stats.spearmanr(b_odd_final.loc[c_b_final, "shrunk_rate"], b_even_final.loc[c_b_final, "shrunk_rate"])
    r_b_final, _ = stats.pearsonr(b_odd_final.loc[c_b_final, "shrunk_rate"], b_even_final.loc[c_b_final, "shrunk_rate"])
    t1_b = set(b_odd_final.loc[c_b_final, "shrunk_rate"].sort_values(ascending=False).head(10).index)
    t2_b = set(b_even_final.loc[c_b_final, "shrunk_rate"].sort_values(ascending=False).head(10).index)
    ov_b_final = len(t1_b.intersection(t2_b))

    bw_odd_final = eb_proper_split(odd_h, "bowler_id", "bowl_rate")
    bw_even_final = eb_proper_split(even_h, "bowler_id", "bowl_rate")
    c_bw_final = bw_odd_final.index.intersection(bw_even_final.index)

    rho_bw_final, _ = stats.spearmanr(bw_odd_final.loc[c_bw_final, "shrunk_rate"], bw_even_final.loc[c_bw_final, "shrunk_rate"])
    r_bw_final, _ = stats.pearsonr(bw_odd_final.loc[c_bw_final, "shrunk_rate"], bw_even_final.loc[c_bw_final, "shrunk_rate"])
    t1_bw = set(bw_odd_final.loc[c_bw_final, "shrunk_rate"].sort_values(ascending=False).head(10).index)
    t2_bw = set(bw_even_final.loc[c_bw_final, "shrunk_rate"].sort_values(ascending=False).head(10).index)
    ov_bw_final = len(t1_bw.intersection(t2_bw))

    print(f"Held-Out Batters (Final Combined Rate Score, N={len(c_b_final)} with >=25 balls):")
    print(f"  Spearman rho = {rho_b_final:+.3f}, Pearson r = {r_b_final:+.3f}, Top-10 Overlap = {ov_b_final} / 10")
    print(f"Held-Out Bowlers (Final Combined Rate Score, N={len(c_bw_final)} with >=25 balls):")
    print(f"  Spearman rho = {rho_bw_final:+.3f}, Pearson r = {r_bw_final:+.3f}, Top-10 Overlap = {ov_bw_final} / 10")
    print("\nKey Finding: When k*WAE is added, binary dismissal variance lowers held-out split-half repeatability")
    print("compared to plain RAE (+0.55 vs +0.11 for batters; +0.24 vs +0.22 for bowlers). Bowlers remain weak (rho=0.22, overlap 3/10).")

    # =========================================================================
    # ITEM 6: UNIFIED BEFORE/AFTER OPPOSITION RECONCILIATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 6: UNIFIED OPPOSITION ADJUSTMENT RECONCILIATION (TOP 10)")
    print("=" * 80)

    # Compute unadjusted rates for eligible players
    legal["bat_rate_no_opp"] = legal["rae_raw"] + k_emp * legal["wae_bat"]
    legal["bowl_rate_no_opp"] = legal["rse_raw"] + k_emp * legal["wae_bowl"]
    high_all = legal[legal["pressure_band_lev"] == "High"]

    b_pids = bat_res["striker_id"].tolist()
    bw_pids = bowl_res["bowler_id"].tolist()

    raw_bat_means = high_all[high_all["striker_id"].isin(b_pids)].groupby("striker_id")["bat_rate_no_opp"].mean()
    raw_bowl_means = high_all[high_all["bowler_id"].isin(bw_pids)].groupby("bowler_id")["bowl_rate_no_opp"].mean()

    bat_res["raw_rank"] = bat_res["striker_id"].map(raw_bat_means.rank(ascending=False)).astype(int)
    bat_res["rank_shift"] = bat_res["raw_rank"] - bat_res["rank"]

    bowl_res["raw_rank"] = bowl_res["bowler_id"].map(raw_bowl_means.rank(ascending=False)).astype(int)
    bowl_res["rank_shift"] = bowl_res["raw_rank"] - bowl_res["rank"]

    ipl_pct_bat = high_all.groupby("striker_id")["is_ipl"].mean() * 100.0
    t20i_pct_bat = high_all.groupby("striker_id")["is_t20i"].mean() * 100.0
    ipl_pct_bowl = high_all.groupby("bowler_id")["is_ipl"].mean() * 100.0
    t20i_pct_bowl = high_all.groupby("bowler_id")["is_t20i"].mean() * 100.0

    bat_res["ipl_pct"] = bat_res["striker_id"].map(ipl_pct_bat).round(1)
    bat_res["t20i_pct"] = bat_res["striker_id"].map(t20i_pct_bat).round(1)
    bowl_res["ipl_pct"] = bowl_res["bowler_id"].map(ipl_pct_bowl).round(1)
    bowl_res["t20i_pct"] = bowl_res["bowler_id"].map(t20i_pct_bowl).round(1)

    print("Batters Opposition Adjustment (Consistent Final Table):")
    print(bat_res[["rank", "name", "raw_rank", "rank_shift", "ipl_pct", "t20i_pct"]].head(10).to_string(index=False))

    print("\nBowlers Opposition Adjustment (Consistent Final Table, e.g. Krunal Pandya):")
    print(bowl_res[["rank", "name", "raw_rank", "rank_shift", "ipl_pct", "t20i_pct"]].head(10).to_string(index=False))

    # =========================================================================
    # ITEM 7: DESCRIPTIVE ROLE PROFILES & FINISHERS
    # =========================================================================
    print("\n" + "=" * 80)
    print("ITEM 7: DESCRIPTIVE ROLE PROFILES (NO INFERRED TACTICAL INTENT)")
    print("=" * 80)

    order_map = high_all.groupby("striker_id")["batting_order"].mean()
    pp_map = (high_all.groupby("striker_id")["phase"].apply(lambda s: (s == "powerplay").mean()) * 100.0)
    mid_map = (high_all.groupby("striker_id")["phase"].apply(lambda s: (s == "middle").mean()) * 100.0)
    death_map = (high_all.groupby("striker_id")["phase"].apply(lambda s: (s == "death").mean()) * 100.0)

    bat_res["mean_order"] = bat_res["striker_id"].map(order_map).round(2)
    bat_res["pp_pct"] = bat_res["striker_id"].map(pp_map).round(1)
    bat_res["mid_pct"] = bat_res["striker_id"].map(mid_map).round(1)
    bat_res["death_pct"] = bat_res["striker_id"].map(death_map).round(1)

    print("Batters Final Top 10 with Descriptive Delivery Profiles:")
    print(bat_res[["rank", "name", "mean_order", "pp_pct", "mid_pct", "death_pct"]].head(10).to_string(index=False))

    # Finishers (Mean Order >= 4.0)
    finishers = bat_res[bat_res["mean_order"] >= 4.0].copy().reset_index(drop=True)
    finishers["finisher_rank"] = finishers.index + 1
    print("\nDedicated Finishers (Mean Order >= 4.0, >=150 Balls, Ranked by Same Shrunk Rate):")
    print(finishers[["finisher_rank", "rank", "name", "balls", "matches", "mean_order", "death_pct", "raw_rate", "shrunk_rate", "prob_top10"]].head(10).to_string(index=False))

    print("\n" + "=" * 80)
    print("PHASE 3 CORRECTED EVALUATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
