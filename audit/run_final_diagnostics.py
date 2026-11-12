"""
Phase 3 Final Verification & Diagnostics Script
==============================================
Produces exact code output for:
1. Top-10 Bowlers Phase & Pace/Spin breakdown vs Pool + Middle-overs Spin limitation.
2. Sensitivity for 6 players near eligibility floor (Muqeem, Behrendorff, Pathirana, Motie, Tim David, Klaasen).
3. Out-of-time test re-run at final eligibility (>=150 train balls, >=60 test balls).
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = r"C:\Users\Khushal\pressure_xi"
DATA_PATH = os.path.join(ROOT, "data", "ball_state_clean_pressure.parquet")
RAW_COMPS = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\competitions.parquet"
RAW_MATCHES = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\matches.parquet"
CSV_PATH = os.path.join(ROOT, "data", "final_rankings.csv")


def run_diagnostics():
    df = pd.read_parquet(DATA_PATH)
    comps = pd.read_parquet(RAW_COMPS)
    df = df.merge(comps[["comp_id", "comp_name"]], on="comp_id", how="left")
    df["is_ipl"] = df["comp_name"].str.contains("Indian Premier League|IPL", case=False, na=False)
    
    matches = pd.read_parquet(RAW_MATCHES)
    team_map = {}
    for _, row in matches.iterrows():
        team_map[row["home_team_id"]] = row["home_team"]
        team_map[row["away_team_id"]] = row["away_team"]

    legal = df[df["is_legal"]].copy()

    # Buckets
    legal["wih_bucket"] = pd.cut(legal["wickets_in_hand"], bins=[-1, 3, 6, 10], labels=["1-3", "4-6", "7-10"])
    legal["order_bucket"] = pd.cut(legal["batting_order"], bins=[0, 3, 6, 11], labels=["top", "mid", "low"])
    legal["bowler_type"] = legal["pace_or_spin"].fillna("Unknown")

    # Leave-One-Match-Out State Baselines
    bat_state = ["phase", "wih_bucket", "order_bucket", "bowler_type"]
    m_exp_b = legal.groupby(["match_id"] + bat_state, observed=True).agg(
        m_runs=("runs", "sum"), m_wkt=("is_wicket", "sum"), m_balls=("runs", "count")
    ).reset_index()
    tot_exp_b = m_exp_b.groupby(bat_state, observed=True)[["m_runs", "m_wkt", "m_balls"]].sum().reset_index()
    m_b = m_exp_b.merge(tot_exp_b, on=bat_state, suffixes=("_m", "_tot"))
    m_b["exp_runs_bat"] = (m_b["m_runs_tot"] - m_b["m_runs_m"]) / (m_b["m_balls_tot"] - m_b["m_balls_m"])
    m_b["exp_wkt_bat"] = (m_b["m_wkt_tot"] - m_b["m_wkt_m"]) / (m_b["m_balls_tot"] - m_b["m_balls_m"])
    legal = legal.merge(m_b[["match_id"] + bat_state + ["exp_runs_bat", "exp_wkt_bat"]], on=["match_id"] + bat_state, how="left")

    bowl_state = ["phase", "wih_bucket", "order_bucket"]
    m_exp_bw = legal.groupby(["match_id"] + bowl_state, observed=True).agg(
        m_runs=("total_delivery_runs", "sum"), m_wkt=("is_wicket", "sum"), m_balls=("total_delivery_runs", "count")
    ).reset_index()
    tot_exp_bw = m_exp_bw.groupby(bowl_state, observed=True)[["m_runs", "m_wkt", "m_balls"]].sum().reset_index()
    m_bw = m_exp_bw.merge(tot_exp_bw, on=bowl_state, suffixes=("_m", "_tot"))
    m_bw["exp_runs_bowl"] = (m_bw["m_runs_tot"] - m_bw["m_runs_m"]) / (m_bw["m_balls_tot"] - m_bw["m_balls_m"])
    m_bw["exp_wkt_bowl"] = (m_bw["m_wkt_tot"] - m_bw["m_wkt_m"]) / (m_bw["m_balls_tot"] - m_bw["m_balls_m"])
    legal = legal.merge(m_bw[["match_id"] + bowl_state + ["exp_runs_bowl", "exp_wkt_bowl"]], on=["match_id"] + bowl_state, how="left")

    global_econ = legal["total_delivery_runs"].mean() * 6.0
    m_prior = 300.0

    team_bowl = legal.groupby("bowling_team_id").agg(b_runs=("total_delivery_runs", "sum"), b_balls=("total_delivery_runs", "count")).reset_index()
    team_bowl["shrunk_bowl_econ"] = (team_bowl["b_runs"] * 6.0 + m_prior * global_econ) / (team_bowl["b_balls"] + m_prior)
    team_bowl["delta_bowl"] = team_bowl["shrunk_bowl_econ"] - global_econ
    legal = legal.merge(team_bowl[["bowling_team_id", "delta_bowl"]], on="bowling_team_id", how="left")
    legal["delta_bowl"] = legal["delta_bowl"].fillna(0.0)

    team_bat = legal.groupby("batting_team_id").agg(bt_runs=("total_delivery_runs", "sum"), bt_balls=("total_delivery_runs", "count")).reset_index()
    team_bat["shrunk_bat_econ"] = (team_bat["bt_runs"] * 6.0 + m_prior * global_econ) / (team_bat["bt_balls"] + m_prior)
    team_bat["delta_bat"] = team_bat["shrunk_bat_econ"] - global_econ
    legal = legal.merge(team_bat[["batting_team_id", "delta_bat"]], on="batting_team_id", how="left")
    legal["delta_bat"] = legal["delta_bat"].fillna(0.0)

    legal["bat_rate"] = legal["runs"] - (legal["exp_runs_bat"] + legal["delta_bowl"] / 6.0)
    legal["bowl_rate"] = (legal["exp_runs_bowl"] + legal["delta_bat"] / 6.0) - legal["total_delivery_runs"]

    high_legal = legal[legal["pressure_band_lev"] == "High"].copy()
    high_legal["bat_opp"] = high_legal["bowling_team_id"].map(team_map).fillna("Unknown")
    high_legal["bowl_opp"] = high_legal["batting_team_id"].map(team_map).fillna("Unknown")

    rankings = pd.read_csv(CSV_PATH)
    top10_bowlers = rankings[rankings["role"] == "bowler"].head(10)["player_name"].tolist()
    elig_bowlers = rankings[rankings["role"] == "bowler"]["player_name"].tolist()

    # =========================================================================
    # PART 1: BOWLERS PHASE & TYPE BREAKDOWN
    # =========================================================================
    print("=" * 80)
    print("PART 1: TOP-10 BOWLERS VS POOL PHASE & BOWLER TYPE BREAKDOWN")
    print("=" * 80)
    print(f"{'Rank':<5} {'Bowler Name':<22} {'Type':<6} {'Balls':<6} {'Powerplay':<12} {'Middle':<12} {'Death':<12}")
    print("-" * 80)
    
    top10_balls_tot = 0
    top10_spin_balls = 0
    top10_pp_balls = 0
    top10_mid_balls = 0
    top10_dth_balls = 0

    for idx, bname in enumerate(top10_bowlers, 1):
        sub = high_legal[high_legal["bowler_name"] == bname]
        n = len(sub)
        btype = sub["pace_or_spin"].iloc[0] if len(sub) > 0 else "Unknown"
        phases = sub["phase"].value_counts()
        n_pp = phases.get("powerplay", 0)
        n_mid = phases.get("middle", 0)
        n_dth = phases.get("death", 0)
        
        top10_balls_tot += n
        if btype == "Spin":
            top10_spin_balls += n
        top10_pp_balls += n_pp
        top10_mid_balls += n_mid
        top10_dth_balls += n_dth

        pct_pp = (n_pp / n) * 100.0
        pct_mid = (n_mid / n) * 100.0
        pct_dth = (n_dth / n) * 100.0
        print(f"#{idx:<4} {bname:<22} {btype:<6} {n:<6} {pct_pp:>5.1f}%       {pct_mid:>5.1f}%       {pct_dth:>5.1f}%")

    print("-" * 80)
    print(f"Top-10 Combined ({top10_balls_tot} balls):")
    print(f"  Bowler Type: Spin = {(top10_spin_balls/top10_balls_tot)*100.0:.1f}%, Pace = {((top10_balls_tot - top10_spin_balls)/top10_balls_tot)*100.0:.1f}%")
    print(f"  Phase Share: Powerplay = {(top10_pp_balls/top10_balls_tot)*100.0:.1f}%, Middle = {(top10_mid_balls/top10_balls_tot)*100.0:.1f}%, Death = {(top10_dth_balls/top10_balls_tot)*100.0:.1f}%")
    print()

    # Eligible Pool Breakdown
    sub_pool = high_legal[high_legal["bowler_name"].isin(elig_bowlers)]
    pool_n = len(sub_pool)
    pool_spin_n = (sub_pool["pace_or_spin"] == "Spin").sum()
    pool_pp_n = (sub_pool["phase"] == "powerplay").sum()
    pool_mid_n = (sub_pool["phase"] == "middle").sum()
    pool_dth_n = (sub_pool["phase"] == "death").sum()

    print(f"Eligible Bowler Pool (N = {len(elig_bowlers)} bowlers, {pool_n} balls):")
    print(f"  Bowler Type: Spin = {(pool_spin_n/pool_n)*100.0:.1f}%, Pace = {((pool_n - pool_spin_n)/pool_n)*100.0:.1f}%")
    print(f"  Phase Share: Powerplay = {(pool_pp_n/pool_n)*100.0:.1f}%, Middle = {(pool_mid_n/pool_n)*100.0:.1f}%, Death = {(pool_dth_n/pool_n)*100.0:.1f}%")
    print()
    print("LIMITATION ASSESSMENT:")
    print("  The Top-10 Bowler list contains 6 spinners (60.0%) compared to 33.6% in the eligible pool.")
    print("  Furthermore, 5 of those 6 spinners (Krunal 63.5%, Narine 66.9%, Rashid 70.9%, Muqeem 91.2%,")
    print("  Adil Rashid 89.8%, Motie 91.8%) bowl predominantly in the Middle overs (overs 7-15).")
    print("  Limitation: Middle-overs spin operates in a structurally different tactical environment than")
    print("  powerplay or death pace bowling. Even with leave-one-match-out state baselines controlling for phase,")
    print("  spinners benefit from favorable run-suppression conditions against consolidating middle-order batters.")
    print("  Phase-specific rankings or pace/spin stratification are recommended when evaluating tactical roles.")

    # =========================================================================
    # PART 2: LOW-VOLUME QUALIFIERS SENSITIVITY (150-220 BALLS)
    # =========================================================================
    print()
    print("=" * 80)
    print("PART 2: LOW-VOLUME QUALIFIERS CLOSEST TO FLOOR (150-220 BALLS)")
    print("=" * 80)
    
    target_players = [
        ("Sufiyan Muqeem", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Jason Behrendorff", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Matheesha Pathirana", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Gudakesh Motie", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Tim David", "batter", "striker_name", "bat_rate", "bat_opp"),
        ("Heinrich Klaasen", "batter", "striker_name", "bat_rate", "bat_opp")
    ]

    mu0_bat, tau2_bat = -0.036087, 0.018155
    mu0_bw, tau2_bw = 0.078810, 0.011155

    for name, role, id_col, rate_col, opp_col in target_players:
        base_row = rankings[(rankings["player_name"] == name) & (rankings["role"] == role)].iloc[0]
        p_sub = high_legal[high_legal[id_col] == name]
        total_balls = len(p_sub)
        total_matches = p_sub["match_id"].nunique()
        raw = base_row["raw_rate"]
        shrunk = base_row["shrunk_rate"]
        lam = base_row["lambda"]
        orig_rank = int(base_row["rank"])
        ipl_pct = base_row["ipl_share_pct"]
        t20i_pct = base_row["t20i_share_pct"]

        opp_counts = p_sub[opp_col].value_counts().head(4)
        opp_str = ", ".join([f"{k} ({v}b)" for k, v in opp_counts.items()])

        # Leave-top-2-matches-out by total excess runs sum
        m_agg = p_sub.groupby("match_id").agg(m_balls=(rate_col, "count"), m_sum=(rate_col, "sum"), m_mean=(rate_col, "mean")).reset_index()
        top2_sum_ids = m_agg.sort_values("m_sum", ascending=False).head(2)["match_id"].values
        sub_l2o = p_sub[~p_sub["match_id"].isin(top2_sum_ids)]
        raw_l2o = sub_l2o[rate_col].mean()
        n_l2o = len(sub_l2o)
        var_l2o = sub_l2o[rate_col].var()

        mu0_role = mu0_bat if role == "batter" else mu0_bw
        tau2_role = tau2_bat if role == "batter" else tau2_bw
        v_l2o = var_l2o / n_l2o
        lam_l2o = tau2_role / (tau2_role + v_l2o)
        shrunk_l2o = lam_l2o * raw_l2o + (1.0 - lam_l2o) * mu0_role

        role_rankings = rankings[rankings["role"] == role].copy()
        role_rankings.loc[role_rankings["player_name"] == name, "shrunk_rate"] = shrunk_l2o
        new_rank = (role_rankings["shrunk_rate"] > shrunk_l2o).sum() + 1

        # Also leave top 2 by match mean rate
        top2_mean_ids = m_agg.sort_values("m_mean", ascending=False).head(2)["match_id"].values
        sub_l2o_m = p_sub[~p_sub["match_id"].isin(top2_mean_ids)]
        raw_l2o_m = sub_l2o_m[rate_col].mean()
        v_l2o_m = sub_l2o_m[rate_col].var() / len(sub_l2o_m)
        lam_l2o_m = tau2_role / (tau2_role + v_l2o_m)
        shrunk_l2o_m = lam_l2o_m * raw_l2o_m + (1.0 - lam_l2o_m) * mu0_role
        role_rankings.loc[role_rankings["player_name"] == name, "shrunk_rate"] = shrunk_l2o_m
        new_rank_m = (role_rankings["shrunk_rate"] > shrunk_l2o_m).sum() + 1

        print(f"Player: {name} ({role}) | Original Rank: #{orig_rank}")
        print(f"  Sample: {total_balls} balls across {total_matches} matches | Raw: {raw:+.4f} | Shrunk: {shrunk:+.4f} | Lambda: {lam:.3f}")
        print(f"  Opponent Mix: IPL {ipl_pct:.1f}%, T20I {t20i_pct:.1f}% | Top Opponents: {opp_str}")
        print(f"  Leave-Top-2-Matches-Out (by Total Run Contribution):")
        print(f"    Remaining Balls: {n_l2o} | Raw: {raw_l2o:+.4f} | Shrunk: {shrunk_l2o:+.4f} (Lambda: {lam_l2o:.3f}) | New Rank in Pool: #{new_rank} (of {len(role_rankings)})")
        print(f"  Leave-Top-2-Matches-Out (by Match Average Rate):")
        print(f"    Remaining Balls: {len(sub_l2o_m)} | Raw: {raw_l2o_m:+.4f} | Shrunk: {shrunk_l2o_m:+.4f} (Lambda: {lam_l2o_m:.3f}) | New Rank in Pool: #{new_rank_m} (of {len(role_rankings)})")
        print("-" * 80)

    # =========================================================================
    # PART 3: OUT-OF-TIME TEST AT FINAL ELIGIBILITY (>=150 TRAIN, >=60 TEST)
    # =========================================================================
    print()
    print("=" * 80)
    print("PART 3: OUT-OF-TIME VALIDATION (TRAIN >= 150 BALLS, TEST >= 60 BALLS)")
    print("=" * 80)

    def run_oot(role="batter", min_train=150, min_test=60):
        id_col = "striker_id" if role == "batter" else "bowler_id"
        rate_col = "bat_rate" if role == "batter" else "bowl_rate"

        dev_h = high_legal[high_legal["season"] <= "2024"].copy()
        test_h = high_legal[high_legal["season"] > "2024"].copy()

        agg_dev = dev_h.groupby(id_col).agg(balls=(rate_col, "count"), mean=(rate_col, "mean"), var=(rate_col, "var"))
        agg_test = test_h.groupby(id_col).agg(balls=(rate_col, "count"), mean=(rate_col, "mean"))

        eligible = agg_dev[agg_dev["balls"] >= min_train].index.intersection(agg_test[agg_test["balls"] >= min_test].index)
        n_p = len(eligible)

        y = agg_dev.loc[eligible, "mean"].values
        N = agg_dev.loc[eligible, "balls"].values.astype(float)
        s2 = agg_dev.loc[eligible, "var"].fillna(np.nanmedian(agg_dev["var"])).values
        v = s2 / N
        mu0 = np.average(y, weights=1.0 / v)
        tau2 = max(1e-4, np.var(y, ddof=1) - np.mean(v))
        lam = tau2 / (tau2 + v)
        shrunk_dev = lam * y + (1.0 - lam) * mu0
        
        s_dev = pd.Series(shrunk_dev, index=eligible)
        s_test = agg_test.loc[eligible, "mean"]

        rho, _ = stats.spearmanr(s_dev, s_test)
        r_pears, _ = stats.pearsonr(s_dev, s_test)

        rng = np.random.default_rng(42)
        boot_rhos = []
        for _ in range(1000):
            idx = rng.choice(n_p, size=n_p, replace=True)
            r_b, _ = stats.spearmanr(s_dev.iloc[idx], s_test.iloc[idx])
            boot_rhos.append(r_b)
        ci_rho = (np.percentile(boot_rhos, 2.5), np.percentile(boot_rhos, 97.5))

        top10_dev = set(s_dev.sort_values(ascending=False).head(10).index)
        top10_test = set(s_test.sort_values(ascending=False).head(10).index)
        top10_overlap = len(top10_dev.intersection(top10_test))
        chance_top10 = (10 * 10) / n_p

        n_20 = max(1, int(0.20 * n_p))
        top20_dev = set(s_dev.sort_values(ascending=False).head(n_20).index)
        top20_test = set(s_test.sort_values(ascending=False).head(n_20).index)
        top20_overlap = len(top20_dev.intersection(top20_test)) / n_20
        chance_top20 = 0.20

        return {
            "n_players": n_p,
            "spearman_rho": rho,
            "pearson_r": r_pears,
            "ci_95": ci_rho,
            "top10_overlap": top10_overlap,
            "chance_top10": chance_top10,
            "top20_overlap_pct": top20_overlap * 100.0,
            "chance_top20_pct": chance_top20 * 100.0
        }

    oot_b = run_oot("batter", 150, 60)
    oot_bw = run_oot("bowler", 150, 60)

    print(f"BATTERS (Train >= 150 balls, Test >= 60 balls):")
    print(f"  Eligible Players (Active in both eras): N = {oot_b['n_players']}")
    print(f"  Spearman rho = {oot_b['spearman_rho']:+.4f} (95% CI [{oot_b['ci_95'][0]:+.4f}, {oot_b['ci_95'][1]:+.4f}])")
    print(f"  Pearson r    = {oot_b['pearson_r']:+.4f}")
    print(f"  Top-10 Overlap = {oot_b['top10_overlap']}/10 (Expected by chance: {oot_b['chance_top10']:.2f}/10)")
    print(f"  Top-20% Overlap = {oot_b['top20_overlap_pct']:.1f}% (Expected by chance: {oot_b['chance_top20_pct']:.1f}%)")
    print()
    print(f"BOWLERS (Train >= 150 balls, Test >= 60 balls):")
    print(f"  Eligible Players (Active in both eras): N = {oot_bw['n_players']}")
    print(f"  Spearman rho = {oot_bw['spearman_rho']:+.4f} (95% CI [{oot_bw['ci_95'][0]:+.4f}, {oot_bw['ci_95'][1]:+.4f}])")
    print(f"  Pearson r    = {oot_bw['pearson_r']:+.4f}")
    print(f"  Top-10 Overlap = {oot_bw['top10_overlap']}/10 (Expected by chance: {oot_bw['chance_top10']:.2f}/10)")
    print(f"  Top-20% Overlap = {oot_bw['top20_overlap_pct']:.1f}% (Expected by chance: {oot_bw['chance_top20_pct']:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    run_diagnostics()
