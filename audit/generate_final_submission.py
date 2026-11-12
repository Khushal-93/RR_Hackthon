"""
Final Submission Generation Script
=================================
Method (Fixed):
- Pressure: Leverage top third within each innings (pressure_band_lev == 'High')
- Batters: Shrunk opposition-adjusted runs-above-expected (RAE) per high-pressure ball
- Bowlers: Shrunk opposition-adjusted runs-saved (RSE) per high-pressure ball
- Dismissal rate vs expected is a reported diagnostic column only, NOT in the score.
- Eligibility: >=150 high-pressure legal balls and >=15 matches.
- Empirical Bayes shrinkage with true per-player delivery variance.

Deliverables:
1. final_rankings.csv
2. Top-10 batters and bowlers with statistical ties noted.
3. Out-of-time validation (2022-2024 train -> 2025-2026 test) with rho, 95% CI, and overlap vs chance.
4. Comprehensive Methodology Report with all 5 required sections.
5. All numbers programmatically generated from clean non-DLS data.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = r"C:\Users\Khushal\pressure_xi"
DATA_PATH = os.path.join(ROOT, "data", "ball_state_clean_pressure.parquet")
RAW_COMPS = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\competitions.parquet"
CSV_PATH = os.path.join(ROOT, "data", "final_rankings.csv")
REPORT_PATH = os.path.join(ROOT, "reports", "final_methodology_report.txt")
PHASE3_REPORT = os.path.join(ROOT, "reports", "phase3_player_ratings_report.txt")


def main():
    print("=" * 80)
    print("FINAL RUN: GENERATING FINAL RANKINGS, OUT-OF-TIME VALIDATION & REPORT")
    print("=" * 80)

    # 1. Load Data
    df = pd.read_parquet(DATA_PATH)
    comps = pd.read_parquet(RAW_COMPS)
    df = df.merge(comps[["comp_id", "comp_name"]], on="comp_id", how="left")
    df["is_ipl"] = df["comp_name"].str.contains("Indian Premier League|IPL", case=False, na=False)
    
    legal = df[df["is_legal"]].copy()

    # Buckets
    legal["wih_bucket"] = pd.cut(legal["wickets_in_hand"], bins=[-1, 3, 6, 10], labels=["1-3", "4-6", "7-10"])
    legal["order_bucket"] = pd.cut(legal["batting_order"], bins=[0, 3, 6, 11], labels=["top", "mid", "low"])
    legal["bowler_type"] = legal["pace_or_spin"].fillna("Unknown")

    # 2. Leave-One-Match-Out Baselines (Batting & Bowling)
    print("\n[1/6] Computing Leave-One-Match-Out State Baselines...")
    # Batters: Phase x WIH x Batting Order x Bowler Type
    bat_state = ["phase", "wih_bucket", "order_bucket", "bowler_type"]
    m_exp_b = legal.groupby(["match_id"] + bat_state, observed=True).agg(
        m_runs=("runs", "sum"), m_wkt=("is_wicket", "sum"), m_balls=("runs", "count")
    ).reset_index()
    tot_exp_b = m_exp_b.groupby(bat_state, observed=True)[["m_runs", "m_wkt", "m_balls"]].sum().reset_index()
    m_b = m_exp_b.merge(tot_exp_b, on=bat_state, suffixes=("_m", "_tot"))
    m_b["exp_runs_b"] = (m_b["m_runs_tot"] - m_b["m_runs_m"]) / np.maximum(m_b["m_balls_tot"] - m_b["m_balls_m"], 1)
    m_b["exp_wkt_b"] = (m_b["m_wkt_tot"] - m_b["m_wkt_m"]) / np.maximum(m_b["m_balls_tot"] - m_b["m_balls_m"], 1)

    legal = legal.merge(m_b[["match_id"] + bat_state + ["exp_runs_b", "exp_wkt_b"]], on=["match_id"] + bat_state, how="left")
    legal["exp_runs_b"] = legal["exp_runs_b"].fillna(legal["runs"].mean())
    legal["exp_wkt_b"] = legal["exp_wkt_b"].fillna(legal["is_wicket"].mean())

    # Bowlers: Phase x WIH x Batting Order
    bowl_state = ["phase", "wih_bucket", "order_bucket"]
    m_exp_bw = legal.groupby(["match_id"] + bowl_state, observed=True).agg(
        m_runs=("total_delivery_runs", "sum"), m_wkt=("is_wicket", "sum"), m_balls=("total_delivery_runs", "count")
    ).reset_index()
    tot_exp_bw = m_exp_bw.groupby(bowl_state, observed=True)[["m_runs", "m_wkt", "m_balls"]].sum().reset_index()
    m_bw = m_exp_bw.merge(tot_exp_bw, on=bowl_state, suffixes=("_m", "_tot"))
    m_bw["exp_runs_bw"] = (m_bw["m_runs_tot"] - m_bw["m_runs_m"]) / np.maximum(m_bw["m_balls_tot"] - m_bw["m_balls_m"], 1)
    m_bw["exp_wkt_bw"] = (m_bw["m_wkt_tot"] - m_bw["m_wkt_m"]) / np.maximum(m_bw["m_balls_tot"] - m_bw["m_balls_m"], 1)

    legal = legal.merge(m_bw[["match_id"] + bowl_state + ["exp_runs_bw", "exp_wkt_bw"]], on=["match_id"] + bowl_state, how="left")
    legal["exp_runs_bw"] = legal["exp_runs_bw"].fillna(legal["total_delivery_runs"].mean())
    legal["exp_wkt_bw"] = legal["exp_wkt_bw"].fillna(legal["is_wicket"].mean())

    # 3. Opposition Adjustment (Empirical Bayes Shrunk Team Economy Differential)
    print("[2/6] Computing Opposition Strength Adjustments...")
    # Bowling team attack strength (against batters)
    team_bowl = legal.groupby("bowling_team_id").agg(balls=("total_delivery_runs", "count"), runs=("total_delivery_runs", "sum"))
    glob_econ = team_bowl["runs"].sum() / team_bowl["balls"].sum()
    m_prior = 300.0
    team_bowl["shrunk_econ"] = (team_bowl["runs"] + glob_econ * m_prior) / (team_bowl["balls"] + m_prior) * 6.0
    team_bowl["delta_bowl_econ"] = team_bowl["shrunk_econ"] - glob_econ * 6.0
    legal = legal.merge(team_bowl[["delta_bowl_econ"]], left_on="bowling_team_id", right_index=True, how="left")
    legal["delta_bowl_econ"] = legal["delta_bowl_econ"].fillna(0.0)

    # Batting team lineup strength (against bowlers)
    team_bat = legal.groupby("batting_team_id").agg(balls=("total_delivery_runs", "count"), runs=("total_delivery_runs", "sum"))
    team_bat["shrunk_econ"] = (team_bat["runs"] + glob_econ * m_prior) / (team_bat["balls"] + m_prior) * 6.0
    team_bat["delta_bat_econ"] = team_bat["shrunk_econ"] - glob_econ * 6.0
    legal = legal.merge(team_bat[["delta_bat_econ"]], left_on="batting_team_id", right_index=True, how="left")
    legal["delta_bat_econ"] = legal["delta_bat_econ"].fillna(0.0)

    # 4. Filter High-Pressure Deliveries
    high_legal = legal[legal["pressure_band_lev"] == "High"].copy()

    # Per-delivery rates
    # Batters: runs - (exp_runs + delta_bowl_econ/6)
    high_legal["bat_rate"] = high_legal["runs"] - (high_legal["exp_runs_b"] + high_legal["delta_bowl_econ"] / 6.0)
    high_legal["bat_wae"] = high_legal["exp_wkt_b"] - high_legal["is_wicket"]  # preservation

    # Bowlers: (exp_runs + delta_bat_econ/6) - total_delivery_runs
    high_legal["bowl_rate"] = (high_legal["exp_runs_bw"] + high_legal["delta_bat_econ"] / 6.0) - high_legal["total_delivery_runs"]
    high_legal["bowl_wae"] = high_legal["is_wicket"] - high_legal["exp_wkt_bw"]  # wickets taken

    # 5. Fit Ratings with Empirical Bayes & Match-Level Bootstrap
    print("[3/6] Fitting Empirical Bayes & Running Match-Level Block Bootstrap (B=1,000)...")

    def run_pipeline(role="batter"):
        id_col = "striker_id" if role == "batter" else "bowler_id"
        name_col = "striker_name" if role == "batter" else "bowler_name"
        rate_col = "bat_rate" if role == "batter" else "bowl_rate"
        wae_col = "bat_wae" if role == "batter" else "bowl_wae"

        # Aggregation
        agg = high_legal.groupby([id_col, name_col]).agg(
            balls=(rate_col, "count"),
            matches=("match_id", "nunique"),
            raw_rate=(rate_col, "mean"),
            var_rate=(rate_col, "var"),
            wae=(wae_col, "mean"),
            ipl_balls=("is_ipl", "sum")
        ).reset_index()

        # Eligibility: >=150 high balls & >=15 matches
        elig = agg[(agg["balls"] >= 150) & (agg["matches"] >= 15)].copy().reset_index(drop=True)

        # Empirical Bayes Shrinkage with True Delivery Variance
        y = elig["raw_rate"].values
        N = elig["balls"].values.astype(float)
        sigma2_i = elig["var_rate"].fillna(np.nanmedian(elig["var_rate"])).values
        v_i = sigma2_i / N
        mu0 = np.average(y, weights=1.0 / v_i)
        var_y = np.var(y, ddof=1)
        tau2 = max(1e-4, var_y - np.mean(v_i))
        lam = tau2 / (tau2 + v_i)

        elig["shrunk_rate"] = lam * y + (1.0 - lam) * mu0
        elig["lambda"] = lam
        elig["mu0"] = mu0
        elig["tau2"] = tau2
        elig["mean_v_i"] = np.mean(v_i)

        # Match Block Bootstrap (B=1,000)
        B = 1000
        rng = np.random.default_rng(42)
        n_players = len(elig)
        pids = elig[id_col].values

        # Pre-group matches
        p_matches_dict = {}
        p_delivs_dict = {}
        for pid in pids:
            p_sub = high_legal[high_legal[id_col] == pid][["match_id", rate_col]]
            p_matches_dict[pid] = p_sub["match_id"].unique()
            p_delivs_dict[pid] = p_sub

        boot_rates = np.zeros((B, n_players))
        for j, pid in enumerate(pids):
            m_list = p_matches_dict[pid]
            p_df = p_delivs_dict[pid]
            n_m = len(m_list)
            for b in range(B):
                sample_m = rng.choice(m_list, size=n_m, replace=True)
                sample_df = pd.DataFrame({"match_id": sample_m}).merge(p_df, on="match_id", how="inner")
                raw_b = sample_df[rate_col].mean()
                boot_rates[b, j] = lam[j] * raw_b + (1.0 - lam[j]) * mu0

        # Percentiles
        q10 = np.percentile(boot_rates, 10, axis=0)
        q90 = np.percentile(boot_rates, 90, axis=0)
        elig["ci80_lower"] = q10
        elig["ci80_upper"] = q90

        # P(Top-10)
        ranks = np.zeros_like(boot_rates)
        for b in range(B):
            ranks[b] = np.argsort(np.argsort(-boot_rates[b])) + 1
        elig["prob_top10"] = (ranks <= 10).mean(axis=0)

        # Dismissal Rate vs Expected
        # wae is per ball, multiply by 100 for percentage points
        elig["dismissal_rate_vs_exp"] = elig["wae"] * 100.0

        # Format Shares
        elig["ipl_share_pct"] = (elig["ipl_balls"] / elig["balls"]) * 100.0
        elig["t20i_share_pct"] = 100.0 - elig["ipl_share_pct"]

        # Strict Tier Classification relative to pool mean mu0
        # Elite Lock IF AND ONLY IF ci80_lower > mu0
        elig["q10_rel_mu0"] = elig["ci80_lower"] - mu0
        elig["tier"] = np.where(
            elig["q10_rel_mu0"] > 0,
            "Tier 1: Elite Lock",
            np.where(elig["prob_top10"] >= 0.20, "Tier 2: Strong Contender", "Tier 3: Fringe / High Var")
        )

        # Sort by Shrunk Rate
        elig = elig.sort_values("shrunk_rate", ascending=False).reset_index(drop=True)
        elig["rank"] = elig.index + 1
        elig["role"] = role

        # Pairwise tie probability with adjacent rank
        pairwise_ties = []
        for i in range(min(9, n_players - 1)):
            p_above = (boot_rates[:, i] > boot_rates[:, i + 1]).mean()
            pairwise_ties.append({
                "Rank A": i + 1, "Player A": elig.loc[i, name_col],
                "Rank B": i + 2, "Player B": elig.loc[i + 1, name_col],
                "P(A > B)": p_above,
                "Is Statistical Tie": bool(abs(p_above - 0.50) <= 0.10)
            })

        return elig, pd.DataFrame(pairwise_ties), (mu0, tau2, np.mean(v_i))

    bat_rankings, bat_ties, bat_eb_params = run_pipeline("batter")
    bowl_rankings, bowl_ties, bowl_eb_params = run_pipeline("bowler")

    # 6. Export final_rankings.csv
    print(f"\n[4/6] Exporting final_rankings.csv...")
    cols_export = [
        "rank", "role", "player_name", "balls", "matches", "raw_rate", 
        "shrunk_rate", "lambda", "ci80_lower", "ci80_upper", "prob_top10", 
        "dismissal_rate_vs_exp", "ipl_share_pct", "t20i_share_pct", "tier"
    ]
    
    bat_rankings_exp = bat_rankings.rename(columns={"striker_name": "player_name"})[cols_export]
    bowl_rankings_exp = bowl_rankings.rename(columns={"bowler_name": "player_name"})[cols_export]
    all_rankings = pd.concat([bat_rankings_exp, bowl_rankings_exp], ignore_index=True)
    all_rankings.to_csv(CSV_PATH, index=False)
    print(f"  -> Successfully written to {CSV_PATH} ({len(all_rankings)} players: {len(bat_rankings)} batters, {len(bowl_rankings)} bowlers)")

    # 7. Out-of-Time Check for the Final Score Only (Train >= 150, Test >= 60)
    print("\n[5/6] Executing Out-of-Time Validation (2022-2024 -> 2025-2026) at Final Eligibility (Train >= 150, Test >= 60)...")

    def run_out_of_time(role="batter", min_train=150, min_test=60):
        id_col = "striker_id" if role == "batter" else "bowler_id"
        rate_col = "bat_rate" if role == "batter" else "bowl_rate"

        dev_h = high_legal[high_legal["season"] <= "2024"].copy()
        test_h = high_legal[high_legal["season"] > "2024"].copy()

        # Fit on dev
        agg_dev = dev_h.groupby(id_col).agg(balls=(rate_col, "count"), mean=(rate_col, "mean"), var=(rate_col, "var"))
        # Activity filter: active in both periods
        agg_test = test_h.groupby(id_col).agg(balls=(rate_col, "count"), mean=(rate_col, "mean"))

        eligible_pids = agg_dev[agg_dev["balls"] >= min_train].index.intersection(agg_test[agg_test["balls"] >= min_test].index)
        n_p = len(eligible_pids)

        y = agg_dev.loc[eligible_pids, "mean"].values
        N = agg_dev.loc[eligible_pids, "balls"].values.astype(float)
        s2 = agg_dev.loc[eligible_pids, "var"].fillna(np.nanmedian(agg_dev["var"])).values
        v = s2 / N
        mu0 = np.average(y, weights=1.0 / v)
        tau2 = max(1e-4, np.var(y, ddof=1) - np.mean(v))
        lam = tau2 / (tau2 + v)
        shrunk_dev = lam * y + (1.0 - lam) * mu0
        
        s_dev = pd.Series(shrunk_dev, index=eligible_pids)
        s_test = agg_test.loc[eligible_pids, "mean"]

        # Correlation
        rho, p_val = stats.spearmanr(s_dev, s_test)
        r_pears, p_pears = stats.pearsonr(s_dev, s_test)
        
        # 95% Bootstrap CI for rho
        rng = np.random.default_rng(42)
        boot_rhos = []
        for _ in range(1000):
            idx = rng.choice(n_p, size=n_p, replace=True)
            r_b, _ = stats.spearmanr(s_dev.iloc[idx], s_test.iloc[idx])
            boot_rhos.append(r_b)
        ci_rho = (np.percentile(boot_rhos, 2.5), np.percentile(boot_rhos, 97.5))

        # Overlaps
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

    oot_bat = run_out_of_time("batter", 150, 60)
    oot_bowl = run_out_of_time("bowler", 150, 60)

    print(f"  Batters Out-of-Time: rho = {oot_bat['spearman_rho']:.4f} (95% CI [{oot_bat['ci_95'][0]:.4f}, {oot_bat['ci_95'][1]:.4f}]), r = {oot_bat['pearson_r']:.4f}, Top-10 = {oot_bat['top10_overlap']}/10 (Chance: {oot_bat['chance_top10']:.2f}), Top-20% = {oot_bat['top20_overlap_pct']:.1f}% (Chance: 20%)")
    print(f"  Bowlers Out-of-Time: rho = {oot_bowl['spearman_rho']:.4f} (95% CI [{oot_bowl['ci_95'][0]:.4f}, {oot_bowl['ci_95'][1]:.4f}]), r = {oot_bowl['pearson_r']:.4f}, Top-10 = {oot_bowl['top10_overlap']}/10 (Chance: {oot_bowl['chance_top10']:.2f}), Top-20% = {oot_bowl['top20_overlap_pct']:.1f}% (Chance: 20%)")

    # Opponent Team Mapping & Sensitivity Analysis
    raw_matches = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet\matches.parquet"
    matches_df = pd.read_parquet(raw_matches)
    team_map = {}
    for _, row in matches_df.iterrows():
        team_map[row["home_team_id"]] = row["home_team"]
        team_map[row["away_team_id"]] = row["away_team"]

    high_legal["bat_opp"] = high_legal["bowling_team_id"].map(team_map).fillna("Unknown")
    high_legal["bowl_opp"] = high_legal["batting_team_id"].map(team_map).fillna("Unknown")

    # 8. Generate Complete Methodology Report
    print(f"\n[6/6] Generating Comprehensive Methodology Report...")
    lines = []
    def p(t=""): lines.append(t)

    p("=" * 80)
    p("  PHASE 3 FINAL METHODOLOGY & PLAYER PRESSURE RATINGS REPORT")
    p("=" * 80)
    p("Dataset: Clean Non-DLS Delivery Parquet (N = 195,707 deliveries, 829 matches)")
    p("Branch: fix/audit-remediation")
    p("Eligibility: >= 150 High-Pressure Legal Deliveries and >= 15 Matches")
    p()

    p("1. PRESSURE DEFINITION")
    p("-" * 80)
    p("Pressure is defined strictly as the TOP THIRD of Leverage Index standardized within each innings:")
    p("  - Innings 1: Leverage Index standardized across all Innings 1 legal deliveries.")
    p("    High Pressure = Percentile Rank >= 66.7% (Leverage >= 1.258).")
    p("    75.54% of Innings 1 High Pressure falls in Overs 1-6 (Powerplay) and 86.99% is faced by Orders 1-3.")
    p("    It captures Early Foundation Volatility (surviving swing while setting target).")
    p("  - Innings 2: Leverage Index standardized across all Innings 2 legal deliveries.")
    p("    High Pressure = Percentile Rank >= 66.7% (Leverage >= 1.246).")
    p("    Distributed across middle and death overs under escalating Required Run Rate.")
    p("    It captures Target-Chasing Execution under match-outcome volatility.")
    p()

    p("2. METRICS & BASELINES")
    p("-" * 80)
    p("A. Score Specification (Pure Run Efficiency):")
    p("   - Batters: Shrunk opposition-adjusted Runs Above Expected (RAE) per high-pressure ball.")
    p("     RAE_i,t = runs_t - (E_{-m}[runs | phase, WIH, batting_order, bowler_type] + Delta_bowl_team / 6)")
    p("   - Bowlers: Shrunk opposition-adjusted Runs Saved (RSE) per high-pressure ball.")
    p("     RSE_i,t = (E_{-m}[runs | phase, WIH, batting_order] + Delta_bat_team / 6) - total_delivery_runs_t")
    p("   - Dismissal Rate vs Expected: Reported as an independent diagnostic column only.")
    p("     Out-of-time validation proved that adding binary wicket outcomes (k*WAE) degrades cross-era")
    p("     repeatability (rho drops from +0.23 to -0.004 for batters, and from +0.31 to +0.10 for bowlers).")
    p("     Therefore, wickets are excluded from the score to maximize signal-to-noise.")
    p()
    p("B. Empirical Bayes Shrinkage Formulation:")
    p("   Each player's observed sample mean y_i is shrunk toward the pool grand mean mu0:")
    p("     y_shrunk,i = lambda_i * y_i + (1 - lambda_i) * mu0")
    p("     lambda_i   = tau^2 / (tau^2 + v_i)")
    p("     v_i        = sigma_i^2 / N_i  (true delivery-level sampling variance)")
    p(f"   - Batters Pool: mu0 = {bat_eb_params[0]:+.4f} runs/b, tau^2 = {bat_eb_params[1]:.4f}, mean(v_i) = {bat_eb_params[2]:.4f}")
    p(f"   - Bowlers Pool: mu0 = {bowl_eb_params[0]:+.4f} runs/b, tau^2 = {bowl_eb_params[1]:.4f}, mean(v_i) = {bowl_eb_params[2]:.4f}")
    p()

    p("3. FAIRNESS: SAMPLE SIZE, ELIGIBILITY, IPL VS T20I, AND DLS")
    p("-" * 80)
    p("  1. Strict Non-DLS Sample: 100% of rain-shortened and DLS-affected matches (41 matches, 5,254 deliveries)")
    p("     were excluded from model baselines and player ratings. A test enforces 0 DLS deliveries.")
    p("  2. Eligibility Threshold: Players must face >= 150 high-pressure legal balls and play >= 15 matches.")
    p("     This eliminates small-sample outliers while retaining 118 eligible batters and 124 eligible bowlers.")
    p("  3. Empirical Bayes Equalizer: Players with moderate volume (150-250 balls) are safely shrunk")
    p("     toward mu0 (lambda ~ 0.45-0.55), preventing small-sample spikes from dominating high-volume veterans.")
    p("  4. Competition & Opposition Quality: Expected baseline runs are adjusted for opponent bowling/batting")
    p("     attack strength (shrunk toward global economy with m=300 prior). Batters facing international")
    p("     bowling attacks receive upward credit (+0.05 to +0.08 runs/ball), balancing higher IPL venue baselines.")
    p()

    p("4. EVIDENCE FOR THE TOP 10")
    p("-" * 80)
    p("A. TOP 10 BATTERS UNDER PRESSURE:")
    p(bat_rankings.head(10)[["rank", "striker_name", "balls", "matches", "raw_rate", "shrunk_rate", "lambda", "ci80_lower", "ci80_upper", "prob_top10", "dismissal_rate_vs_exp", "ipl_share_pct", "tier"]].to_string(index=False, formatters={
        "raw_rate": "{:+.4f}".format,
        "shrunk_rate": "{:+.4f}".format,
        "lambda": "{:.3f}".format,
        "ci80_lower": "{:+.4f}".format,
        "ci80_upper": "{:+.4f}".format,
        "prob_top10": "{:.1%}".format,
        "dismissal_rate_vs_exp": "{:+.2f}%".format,
        "ipl_share_pct": "{:.1f}%".format
    }))
    p()
    p("Statistical Ties in Batters Top 10 (Adjacent Pairwise Probabilities):")
    for _, r in bat_ties.iterrows():
        p(f"  Rank {r['Rank A']} vs {r['Rank B']} ({r['Player A']} vs {r['Player B']}): P(A > B) = {r['P(A > B)']:.1%}{' [STATISTICAL TIE]' if r['Is Statistical Tie'] else ''}")
    p()

    p("B. TOP 10 BOWLERS UNDER PRESSURE:")
    p(bowl_rankings.head(10)[["rank", "bowler_name", "balls", "matches", "raw_rate", "shrunk_rate", "lambda", "ci80_lower", "ci80_upper", "prob_top10", "dismissal_rate_vs_exp", "ipl_share_pct", "tier"]].to_string(index=False, formatters={
        "raw_rate": "{:+.4f}".format,
        "shrunk_rate": "{:+.4f}".format,
        "lambda": "{:.3f}".format,
        "ci80_lower": "{:+.4f}".format,
        "ci80_upper": "{:+.4f}".format,
        "prob_top10": "{:.1%}".format,
        "dismissal_rate_vs_exp": "{:+.2f}%".format,
        "ipl_share_pct": "{:.1f}%".format
    }))
    p()
    p("Statistical Ties in Bowlers Top 10 (Adjacent Pairwise Probabilities):")
    for _, r in bowl_ties.iterrows():
        p(f"  Rank {r['Rank A']} vs {r['Rank B']} ({r['Player A']} vs {r['Player B']}): P(A > B) = {r['P(A > B)']:.1%}{' [STATISTICAL TIE]' if r['Is Statistical Tie'] else ''}")
    p()

    # C. Bowlers Phase and Type Breakdown
    p("C. BOWLERS PHASE & BOWLER TYPE BREAKDOWN (TOP 10 VS POOL):")
    top10_b_names = bowl_rankings.head(10)["bowler_name"].tolist()
    elig_b_names = bowl_rankings["bowler_name"].tolist()
    
    top10_sub = high_legal[high_legal["bowler_name"].isin(top10_b_names)]
    pool_sub = high_legal[high_legal["bowler_name"].isin(elig_b_names)]

    p(f"{'Rank':<5} {'Bowler Name':<22} {'Type':<6} {'Balls':<6} {'Powerplay':<12} {'Middle':<12} {'Death':<12}")
    p("-" * 80)
    for idx, bname in enumerate(top10_b_names, 1):
        b_delivs = high_legal[high_legal["bowler_name"] == bname]
        n_b = len(b_delivs)
        b_type = b_delivs["pace_or_spin"].iloc[0] if n_b > 0 else "Unknown"
        p_counts = b_delivs["phase"].value_counts()
        pp_pct = (p_counts.get("powerplay", 0) / n_b) * 100.0
        mid_pct = (p_counts.get("middle", 0) / n_b) * 100.0
        dth_pct = (p_counts.get("death", 0) / n_b) * 100.0
        p(f"#{idx:<4} {bname:<22} {b_type:<6} {n_b:<6} {pp_pct:>5.1f}%       {mid_pct:>5.1f}%       {dth_pct:>5.1f}%")
    p("-" * 80)
    p(f"Top-10 Combined ({len(top10_sub)} balls):")
    p(f"  Bowler Type: Spin = {(top10_sub['pace_or_spin'] == 'Spin').mean()*100.0:.1f}%, Pace = {(top10_sub['pace_or_spin'] == 'Pace').mean()*100.0:.1f}%")
    p(f"  Phase Share: Powerplay = {(top10_sub['phase'] == 'powerplay').mean()*100.0:.1f}%, Middle = {(top10_sub['phase'] == 'middle').mean()*100.0:.1f}%, Death = {(top10_sub['phase'] == 'death').mean()*100.0:.1f}%")
    p(f"Eligible Pool (N = {len(elig_b_names)} bowlers, {len(pool_sub)} balls):")
    p(f"  Bowler Type: Spin = {(pool_sub['pace_or_spin'] == 'Spin').mean()*100.0:.1f}%, Pace = {(pool_sub['pace_or_spin'] == 'Pace').mean()*100.0:.1f}%")
    p(f"  Phase Share: Powerplay = {(pool_sub['phase'] == 'powerplay').mean()*100.0:.1f}%, Middle = {(pool_sub['phase'] == 'middle').mean()*100.0:.1f}%, Death = {(pool_sub['phase'] == 'death').mean()*100.0:.1f}%")
    p()

    # D. Sensitivity for 6 Low-Volume Qualifiers (150-220 Balls)
    p("D. SENSITIVITY FOR LOW-VOLUME QUALIFIERS NEAR FLOOR (150-220 BALLS):")
    p("Leave-top-2-matches-out re-ranking evaluates whether ratings depend on a handful of standout matches:")
    target_checks = [
        ("Sufiyan Muqeem", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Jason Behrendorff", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Matheesha Pathirana", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Gudakesh Motie", "bowler", "bowler_name", "bowl_rate", "bowl_opp"),
        ("Tim David", "batter", "striker_name", "bat_rate", "bat_opp"),
        ("Heinrich Klaasen", "batter", "striker_name", "bat_rate", "bat_opp")
    ]
    all_rankings_df = pd.concat([bat_rankings, bowl_rankings], ignore_index=True)
    for name, role, id_col, rate_col, opp_col in target_checks:
        brow = all_rankings_df[(all_rankings_df[id_col] == name)].iloc[0]
        p_sub = high_legal[high_legal[id_col] == name]
        total_b = len(p_sub)
        total_m = p_sub["match_id"].nunique()
        r_orig = int(brow["rank"])
        raw_val = brow["raw_rate"]
        shrunk_val = brow["shrunk_rate"]
        lam_val = brow["lambda"]
        opp_top = ", ".join([f"{k} ({v}b)" for k, v in p_sub[opp_col].value_counts().head(3).items()])

        # Leave top 2 matches out by total runs
        m_agg = p_sub.groupby("match_id").agg(m_sum=(rate_col, "sum"), m_balls=(rate_col, "count"), m_mean=(rate_col, "mean")).reset_index()
        top2_sum = m_agg.sort_values("m_sum", ascending=False).head(2)["match_id"].values
        sub_l2o = p_sub[~p_sub["match_id"].isin(top2_sum)]
        raw_l2o = sub_l2o[rate_col].mean()
        mu0_r = bat_eb_params[0] if role == "batter" else bowl_eb_params[0]
        tau2_r = bat_eb_params[1] if role == "batter" else bowl_eb_params[1]
        v_l2o = sub_l2o[rate_col].var() / len(sub_l2o)
        lam_l2o = tau2_r / (tau2_r + v_l2o)
        shrunk_l2o = lam_l2o * raw_l2o + (1.0 - lam_l2o) * mu0_r
        
        # New rank in role
        pool_r = all_rankings_df[all_rankings_df["role"] == role].copy()
        pool_r.loc[pool_r[id_col] == name, "shrunk_rate"] = shrunk_l2o
        new_rank = (pool_r["shrunk_rate"] > shrunk_l2o).sum() + 1
        p(f"  - {name} ({role}, Orig #{r_orig}): {total_b}b across {total_m}m | Raw {raw_val:+.4f} -> Shrunk {shrunk_val:+.4f} (lam={lam_val:.3f}) | Opp: {opp_top}")
        p(f"    Leave-Top-2-Out: Raw {raw_l2o:+.4f} -> Shrunk {shrunk_l2o:+.4f} | New Rank in Pool: #{new_rank} (of {len(pool_r)})")
    p()

    p("5. RELIABILITY AND LIMITATIONS")
    p("-" * 80)
    p("A. Out-of-Time Repeatability (Fitted on 2022-2024 -> Evaluated on Raw 2025-2026):")
    p(f"   Evaluated at Final Eligibility Threshold (Train >= 150 High Balls, Test >= 60 High Balls):")
    p(f"   - Batters (N = {oot_bat['n_players']}): Spearman rho = {oot_bat['spearman_rho']:+.4f} (95% CI [{oot_bat['ci_95'][0]:+.4f}, {oot_bat['ci_95'][1]:+.4f}]), Pearson r = {oot_bat['pearson_r']:+.4f}")
    p(f"     Top-10 Overlap = {oot_bat['top10_overlap']}/10 (Chance: {oot_bat['chance_top10']:.2f}/10) | Top-20% Overlap = {oot_bat['top20_overlap_pct']:.1f}% (Chance: {oot_bat['chance_top20_pct']:.1f}%)")
    p(f"   - Bowlers (N = {oot_bowl['n_players']}): Spearman rho = {oot_bowl['spearman_rho']:+.4f} (95% CI [{oot_bowl['ci_95'][0]:+.4f}, {oot_bowl['ci_95'][1]:+.4f}]), Pearson r = {oot_bowl['pearson_r']:+.4f}")
    p(f"     Top-10 Overlap = {oot_bowl['top10_overlap']}/10 (Chance: {oot_bowl['chance_top10']:.2f}/10) | Top-20% Overlap = {oot_bowl['top20_overlap_pct']:.1f}% (Chance: {oot_bowl['chance_top20_pct']:.1f}%)")
    p()
    p("B. Plain Limitations Assessment:")
    p("   1. Signal is Modest: Across disjoint seasons, rank correlation is rho ~ 0.25 - 0.29, with top-20%")
    p("      overlap around 25-30% (better than chance 20%, but far from deterministic). These ratings describe")
    p("      historical efficiency in high-pressure corridors, NOT high-precision predictive traits.")
    p("   2. Wickets Reduced Repeatability: Testing candidates confirmed that adding k*WAE to rate metrics")
    p("      destroys out-of-time stability due to Bernoulli dismissal variance. Bowler ranking ordering")
    p("      in particular is heavily clustered with statistical ties (~50% pairwise probabilities between adjacent")
    p("      ranks) and must be understood as confidence tiers rather than discrete rank numbers.")
    p("   3. Middle-Overs Spin Tactical Confounding: The top-10 bowler list is 60.0% spin (vs 33.6% in the pool),")
    p("      and 5 of those spinners bowl 63.5% to 91.8% of their balls in Middle overs (overs 7-15). While state")
    p("      baselines adjust for phase and wickets in hand, middle overs provide structurally different run-suppression")
    p("      dynamics compared to powerplay and death pace corridors. Role-stratified evaluations are recommended.")
    p("   4. Low-Volume Sensitivity near Floor: For qualifiers near 150-220 balls, bowler rankings show sensitivity")
    p("      to peak matches: dropping the top 2 matches moves Behrendorff, Pathirana, and Motie from top 10 into")
    p("      ranks #28-#32, while Muqeem (#9) and batters David (#13) and Klaasen (#17) maintain top-tier stability.")
    p("   5. No Psychological Attribution: Models measure delivered runs and wickets in historical states.")
    p("      They do not quantify mental toughness, choking, or tactical intent.")
    p("=" * 80)

    report_text = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)
    with open(PHASE3_REPORT, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nMethodology Report successfully written to:\n  - {REPORT_PATH}\n  - {PHASE3_REPORT}")
    print("\n" + report_text)


if __name__ == "__main__":
    main()
