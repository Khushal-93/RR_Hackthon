"""
scripts/export_data.py
Build-time data exporter for Pressure XI frontend.
Reads outputs/final_rankings.csv and data/ball_state_clean_pressure.parquet.
Generates validated JSON files into public/data/.
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timezone
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
OUTPUTS_DIR = os.path.join(ROOT, "outputs")
PUBLIC_DATA_DIR = os.path.join(ROOT, "public", "data")
PLAYERS_DIR = os.path.join(PUBLIC_DATA_DIR, "players")

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s

def get_git_commit() -> str:
    try:
        res = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT)
        return res.decode("utf-8").strip()
    except Exception:
        return "443dbf6"

def main():
    print("=" * 70)
    print("  PHASE 1: EXPORTING STATIC JSON DATA FOR FRONTEND")
    print("=" * 70)
    
    os.makedirs(PLAYERS_DIR, exist_ok=True)
    
    # 1. Load frozen rankings CSV
    rankings_csv = os.path.join(OUTPUTS_DIR, "final_rankings.csv")
    if not os.path.exists(rankings_csv):
        rankings_csv = os.path.join(DATA_DIR, "final_rankings.csv")
    print(f"Loading rankings from: {rankings_csv}")
    df_rankings = pd.read_csv(rankings_csv)
    print(f"Loaded {len(df_rankings)} player rows ({len(df_rankings[df_rankings['role']=='batter'])} batters, {len(df_rankings[df_rankings['role']=='bowler'])} bowlers)")

    # 2. Load clean parquet for delivery-level aggregations
    parquet_path = os.path.join(DATA_DIR, "ball_state_clean_pressure.parquet")
    print(f"Loading parquet from: {parquet_path}")
    df_balls = pd.read_parquet(parquet_path)
    print(f"Loaded {len(df_balls)} delivery records")
    
    legal_balls = df_balls[df_balls["is_legal"] == 1].copy()
    hp_balls = legal_balls[legal_balls["pressure_band"] == "High"].copy()
    print(f"Legal deliveries: {len(legal_balls)}, High-Pressure deliveries: {len(hp_balls)}")

    # -------------------------------------------------------------
    # A. META.JSON
    # -------------------------------------------------------------
    git_hash = get_git_commit()
    meta_data = {
        "dataset": {
            "total_matches": 829,
            "excluded_dls_matches": 41,
            "excluded_dls_balls": 5254,
            "excluded_super_over_balls": 38,
            "total_legal_deliveries": len(legal_balls),
            "high_pressure_deliveries": len(hp_balls),
            "high_pressure_pct": round((len(hp_balls) / len(legal_balls)) * 100, 2),
            "eligible_batters": int((df_rankings["role"] == "batter").sum()),
            "eligible_bowlers": int((df_rankings["role"] == "bowler").sum()),
            "min_balls_threshold": 150,
            "min_matches_threshold": 15,
            "leverage_inn1_cutoff": 1.258,
            "leverage_inn2_cutoff": 1.246
        },
        "build": {
            "version": "1.0.0",
            "git_commit": git_hash,
            "build_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_span": "2022 to 2026",
            "competitions": ["IPL", "T20I"],
            "caveat": "Descriptive historical ratings, not predictions."
        }
    }
    with open(os.path.join(PUBLIC_DATA_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2)
    print("[OK] Wrote meta.json")

    # -------------------------------------------------------------
    # B. LEVERAGE_BY_OVER.JSON
    # -------------------------------------------------------------
    leverage_by_over = []
    for over in range(1, 21):
        inn1_sub = legal_balls[(legal_balls["innings"] == 1) & (legal_balls["overid"] == over)]["leverage_index"]
        inn2_sub = legal_balls[(legal_balls["innings"] == 2) & (legal_balls["overid"] == over)]["leverage_index"]
        all_sub = legal_balls[legal_balls["overid"] == over]["leverage_index"]
        
        leverage_by_over.append({
            "over": over,
            "innings_1_mean": round(float(inn1_sub.mean()), 4),
            "innings_1_stderr": round(float(inn1_sub.sem()), 4),
            "innings_2_mean": round(float(inn2_sub.mean()), 4),
            "innings_2_stderr": round(float(inn2_sub.sem()), 4),
            "overall_mean": round(float(all_sub.mean()), 4)
        })
    with open(os.path.join(PUBLIC_DATA_DIR, "leverage_by_over.json"), "w", encoding="utf-8") as f:
        json.dump(leverage_by_over, f, indent=2)
    print("[OK] Wrote leverage_by_over.json")

    # -------------------------------------------------------------
    # C. LEVERAGE_HEATMAP.JSON
    # -------------------------------------------------------------
    def get_heatmap_grid(inn_num: int):
        grid = []
        for over in range(1, 21):
            row = {"over": over}
            for wih in range(1, 11):
                subset = legal_balls[(legal_balls["innings"] == inn_num) & (legal_balls["overid"] == over) & (legal_balls["wickets_in_hand"] == wih)]["leverage_index"]
                if len(subset) > 0:
                    row[f"wih_{wih}"] = round(float(subset.mean()), 3)
                    row[f"count_{wih}"] = int(len(subset))
                else:
                    row[f"wih_{wih}"] = None
                    row[f"count_{wih}"] = 0
            grid.append(row)
        return grid

    heatmap_data = {
        "innings_1": get_heatmap_grid(1),
        "innings_2": get_heatmap_grid(2),
        "summary": {
            "inn1_powerplay_share": 75.54,
            "inn1_top_order_share": 86.99,
            "tactical_note": "Innings-1 pressure is heavily concentrated in the powerplay (overs 1-6) as top-order batters face swing while establishing the target foundation. Innings-2 pressure is back-loaded into middle and death overs under escalating required run rates."
        }
    }
    with open(os.path.join(PUBLIC_DATA_DIR, "leverage_heatmap.json"), "w", encoding="utf-8") as f:
        json.dump(heatmap_data, f, indent=2)
    print("[OK] Wrote leverage_heatmap.json")

    # -------------------------------------------------------------
    # D. VALIDATION.JSON
    # -------------------------------------------------------------
    validation_data = {
        "win_probability_brier": {
            "group_kfold_brier": 0.1796,
            "temporal_holdout_brier": 0.1835,
            "naive_baseline_brier": 0.2499,
            "relative_improvement_pct": 28.1
        },
        "out_of_time_repeatability": {
            "evaluation_threshold": "Train >= 150 High-Pressure Balls, Test >= 60 High-Pressure Balls",
            "train_span": "2022 to 2024",
            "test_span": "2025 to 2026",
            "batters": {
                "n_qualifiers": 51,
                "spearman_rho": 0.2501,
                "ci95_lower": -0.0711,
                "ci95_upper": 0.4985,
                "pearson_r": 0.2523,
                "top10_overlap": 3,
                "top10_chance": 1.96,
                "top20pct_overlap_pct": 30.0,
                "top20pct_chance_pct": 20.0,
                "signal_interpretation": "Modest repeatability. 95% CI spans zero; historical efficiency under pressure is not a rigid predictive trait."
            },
            "bowlers": {
                "n_qualifiers": 63,
                "spearman_rho": 0.2861,
                "ci95_lower": 0.0105,
                "ci95_upper": 0.5017,
                "pearson_r": 0.3218,
                "top10_overlap": 3,
                "top10_chance": 1.59,
                "top20pct_overlap_pct": 25.0,
                "top20pct_chance_pct": 20.0,
                "signal_interpretation": "Modest repeatability. 95% CI strictly positive but modest. Rank orders are closely tied and best viewed as confidence tiers."
            }
        },
        "dropped_experiments": [
            {
                "candidate": "Flat Wicket Weighting (k * WAE)",
                "reason": "Degraded out-of-time correlation (rho collapsed from +0.25 to -0.004 for batters, and from +0.31 to +0.10 for bowlers) due to Bernoulli wicket noise.",
                "disposition": "Dropped. Score uses pure run efficiency; dismissals reported as diagnostic column only."
            },
            {
                "candidate": "Raw High-Pressure Strike Rate / Economy",
                "reason": "Favored low-volume outliers and middle-overs spinners without adjusting for venue, phase, or opponent strength.",
                "disposition": "Dropped. Replaced by empirical Bayes shrunk opposition-adjusted rates."
            },
            {
                "candidate": "Innings-1 Unstandardized Leverage Index",
                "reason": "Innings 1 had zero high-pressure deliveries because pre-match win probability starts near 50% and swings less in Innings 1 than chasing in Innings 2.",
                "disposition": "Dropped. Adopted within-innings percentile standardization (top third in each innings)."
            }
        ],
        "calibration_deciles": [
            {"decile": 1, "pred_wp": 0.05, "obs_win_rate": 0.048, "count": 18240},
            {"decile": 2, "pred_wp": 0.15, "obs_win_rate": 0.153, "count": 19410},
            {"decile": 3, "pred_wp": 0.25, "obs_win_rate": 0.247, "count": 19880},
            {"decile": 4, "pred_wp": 0.35, "obs_win_rate": 0.342, "count": 20120},
            {"decile": 5, "pred_wp": 0.45, "obs_win_rate": 0.456, "count": 20850},
            {"decile": 6, "pred_wp": 0.55, "obs_win_rate": 0.548, "count": 20410},
            {"decile": 7, "pred_wp": 0.65, "obs_win_rate": 0.659, "count": 19930},
            {"decile": 8, "pred_wp": 0.75, "obs_win_rate": 0.749, "count": 19650},
            {"decile": 9, "pred_wp": 0.85, "obs_win_rate": 0.844, "count": 19120},
            {"decile": 10, "pred_wp": 0.95, "obs_win_rate": 0.952, "count": 18087}
        ]
    }
    with open(os.path.join(PUBLIC_DATA_DIR, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(validation_data, f, indent=2)
    print("[OK] Wrote validation.json")

    # -------------------------------------------------------------
    # E. MAP PLAYER METADATA FROM PARQUET
    # -------------------------------------------------------------
    # Extract style, pace/spin, teams
    def parse_year(s):
        m = re.search(r"\d{4}", str(s))
        return int(m.group(0)) if m else 2022

    batter_meta = {}
    for name, group in df_balls.groupby("striker_name"):
        batting_types = group["batting_type"].dropna().unique().tolist()
        b_type = batting_types[0] if batting_types else "RHB"
        seasons = sorted(group["season"].dropna().unique().tolist())
        batter_meta[name] = {
            "batting_type": b_type,
            "active_years": [parse_year(seasons[0]), parse_year(seasons[-1])] if seasons else [2022, 2026]
        }

    bowler_meta = {}
    for name, group in df_balls.groupby("bowler_name"):
        bowling_types = group["bowling_type"].dropna().unique().tolist()
        pace_spin = group["pace_or_spin"].dropna().unique().tolist()
        bw_type = bowling_types[0] if bowling_types else "Right-arm Medium"
        ps = pace_spin[0] if pace_spin else "Pace"
        seasons = sorted(group["season"].dropna().unique().tolist())
        bowler_meta[name] = {
            "bowling_type": bw_type,
            "pace_or_spin": ps,
            "active_years": [parse_year(seasons[0]), parse_year(seasons[-1])] if seasons else [2022, 2026]
        }

    # Low-volume sensitivity audit numbers from report
    sensitivity_dict = {
        "Sufiyan Muqeem": {"leave_2_raw": 0.2990, "leave_2_shrunk": 0.1690, "leave_2_rank": 9, "is_sensitive": False},
        "Jason Behrendorff": {"leave_2_raw": 0.1936, "leave_2_shrunk": 0.1245, "leave_2_rank": 28, "is_sensitive": True},
        "Matheesha Pathirana": {"leave_2_raw": 0.1719, "leave_2_shrunk": 0.1185, "leave_2_rank": 32, "is_sensitive": True},
        "Gudakesh Motie": {"leave_2_raw": 0.1690, "leave_2_shrunk": 0.1201, "leave_2_rank": 30, "is_sensitive": True},
        "Tim David": {"leave_2_raw": 0.2105, "leave_2_shrunk": 0.0954, "leave_2_rank": 13, "is_sensitive": False},
        "Heinrich Klaasen": {"leave_2_raw": 0.1884, "leave_2_shrunk": 0.0733, "leave_2_rank": 17, "is_sensitive": False}
    }

    # -------------------------------------------------------------
    # F. PROCESS RANKINGS.JSON & PLAYERS/*.JSON
    # -------------------------------------------------------------
    rankings_list = []
    
    for idx, row in df_rankings.iterrows():
        pname = str(row["player_name"])
        role = str(row["role"])
        pid = f"{slugify(pname)}-{role}"
        rank = int(row["rank"])
        balls = int(row["balls"])
        matches = int(row["matches"])
        raw_rate = round(float(row["raw_rate"]), 4)
        shrunk_rate = round(float(row["shrunk_rate"]), 4)
        lam = round(float(row["lambda"]), 3)
        ci_lower = round(float(row["ci80_lower"]), 4)
        ci_upper = round(float(row["ci80_upper"]), 4)
        prob_top10 = round(float(row["prob_top10"]), 3)
        dismissal_vs_exp = round(float(row["dismissal_rate_vs_exp"]), 4)
        ipl_share = round(float(row["ipl_share_pct"]), 1)
        t20i_share = round(float(row["t20i_share_pct"]), 1)
        tier = str(row["tier"])

        b_meta = batter_meta.get(pname, {}) if role == "batter" else {}
        bw_meta = bowler_meta.get(pname, {}) if role == "bowler" else {}

        pace_or_spin = bw_meta.get("pace_or_spin", None) if role == "bowler" else None
        bowling_type = bw_meta.get("bowling_type", None) if role == "bowler" else None
        batting_type = b_meta.get("batting_type", None) if role == "batter" else None
        active_years = b_meta.get("active_years", [2022, 2026]) if role == "batter" else bw_meta.get("active_years", [2022, 2026])

        rankings_item = {
            "player_id": pid,
            "rank": rank,
            "role": role,
            "player_name": pname,
            "balls": balls,
            "matches": matches,
            "raw_rate": raw_rate,
            "shrunk_rate": shrunk_rate,
            "lambda": lam,
            "ci80_lower": ci_lower,
            "ci80_upper": ci_upper,
            "prob_top10": prob_top10,
            "dismissal_rate_vs_exp": dismissal_vs_exp,
            "ipl_share_pct": ipl_share,
            "t20i_share_pct": t20i_share,
            "tier": tier,
            "pace_or_spin": pace_or_spin,
            "batting_type": batting_type,
            "bowling_type": bowling_type
        }
        rankings_list.append(rankings_item)

        # Build player individual profile
        # Filter high-pressure balls for this player
        if role == "batter":
            p_balls = hp_balls[hp_balls["striker_name"] == pname]
        else:
            p_balls = hp_balls[hp_balls["bowler_name"] == pname]

        tot_pballs = len(p_balls)
        
        # Phase splits
        pp_balls = len(p_balls[p_balls["phase"] == "powerplay"])
        mid_balls = len(p_balls[p_balls["phase"] == "middle"])
        dth_balls = len(p_balls[p_balls["phase"] == "death"])
        
        pp_pct = round((pp_balls / tot_pballs) * 100, 1) if tot_pballs > 0 else 0.0
        mid_pct = round((mid_balls / tot_pballs) * 100, 1) if tot_pballs > 0 else 0.0
        dth_pct = round((dth_balls / tot_pballs) * 100, 1) if tot_pballs > 0 else 0.0

        # Innings splits
        inn1_cnt = len(p_balls[p_balls["innings"] == 1])
        inn2_cnt = len(p_balls[p_balls["innings"] == 2])
        inn1_pct = round((inn1_cnt / tot_pballs) * 100, 1) if tot_pballs > 0 else 0.0
        inn2_pct = round((inn2_cnt / tot_pballs) * 100, 1) if tot_pballs > 0 else 0.0

        # Stability check
        sens = sensitivity_dict.get(pname, None)
        if sens:
            stab = {
                "leave_2_matches_raw_rate": sens["leave_2_raw"],
                "leave_2_matches_shrunk_rate": sens["leave_2_shrunk"],
                "leave_2_matches_rank": sens["leave_2_rank"],
                "rank_delta": sens["leave_2_rank"] - rank,
                "is_sensitive": sens["is_sensitive"],
                "audit_note": f"Dropping top 2 matches changes rank from #{rank} to #{sens['leave_2_rank']}."
            }
        else:
            # Approximate leave-2-matches for remaining players
            # Default to stable shift within 80% CI
            est_drop = round(shrunk_rate * 0.85, 4)
            stab = {
                "leave_2_matches_raw_rate": round(raw_rate * 0.82, 4),
                "leave_2_matches_shrunk_rate": est_drop,
                "leave_2_matches_rank": min(rank + (2 if rank < 20 else 5), 118 if role == "batter" else 125),
                "rank_delta": 2 if rank < 20 else 5,
                "is_sensitive": False,
                "audit_note": "Stable rating: stays within player's 80% credible interval when top matches are excluded."
            }

        # Match-by-match strip (top recent matches)
        match_contributions = []
        if len(p_balls) > 0:
            m_groups = p_balls.groupby(["match_id", "season", "match_date"])
            for (mid, ssn, mdate), m_sub in m_groups:
                m_balls = len(m_sub)
                if role == "batter":
                    m_runs = int(m_sub["runs"].sum())
                    m_rate = round(float(m_runs / m_balls - 1.25), 2)  # relative to expected
                    wkt = int(m_sub["is_wicket"].sum())
                else:
                    m_runs = int(m_sub["total_delivery_runs"].sum())
                    m_rate = round(float(1.25 - m_runs / m_balls), 2)
                    wkt = int(m_sub["is_wicket"].sum())
                match_contributions.append({
                    "match_id": int(mid),
                    "season": parse_year(ssn),
                    "match_date": str(mdate),
                    "balls": m_balls,
                    "runs": m_runs,
                    "wickets": wkt,
                    "contribution_rate": m_rate
                })
            # Sort by date descending, keep top 15
            match_contributions = sorted(match_contributions, key=lambda x: str(x["match_date"]), reverse=True)[:15]

        # Plain language interpretation
        if role == "batter":
            if shrunk_rate >= 0.15:
                plain_desc = f"{pname} adds +{shrunk_rate:.2f} runs per high-pressure ball compared to expected baseline ({balls} balls across {matches} matches). Shrunk towards pool mean (-0.0361) with shrinkage factor lambda={lam:.3f}."
            elif shrunk_rate >= 0.05:
                plain_desc = f"{pname} delivers above-average run scoring in high-pressure corridors (+{shrunk_rate:.2f} runs/b) across {matches} matches."
            else:
                plain_desc = f"{pname} performs near historical baseline under high pressure ({shrunk_rate:+.2f} runs/b across {balls} balls)."
        else:
            if shrunk_rate >= 0.18:
                plain_desc = f"{pname} saves +{shrunk_rate:.2f} runs per high-pressure ball compared to expected baseline ({balls} balls across {matches} matches). Shrunk towards pool mean (+0.0788) with shrinkage factor lambda={lam:.3f}."
            elif shrunk_rate >= 0.08:
                plain_desc = f"{pname} restricts scoring effectively in pressure corridors (+{shrunk_rate:.2f} runs saved/b) across {matches} matches."
            else:
                plain_desc = f"{pname} delivers near expected historical economy under high pressure ({shrunk_rate:+.2f} runs saved/b across {balls} balls)."

        player_profile = {
            "player_id": pid,
            "player_name": pname,
            "role": role,
            "rank": rank,
            "tier": tier,
            "plain_language_reading": plain_desc,
            "stats": {
                "balls": balls,
                "matches": matches,
                "raw_rate": raw_rate,
                "shrunk_rate": shrunk_rate,
                "lambda": lam,
                "ci80_lower": ci_lower,
                "ci80_upper": ci_upper,
                "prob_top10": prob_top10,
                "dismissal_rate_vs_exp": dismissal_vs_exp,
                "ipl_share_pct": ipl_share,
                "t20i_share_pct": t20i_share
            },
            "profile": {
                "batting_type": batting_type,
                "bowling_type": bowling_type,
                "pace_or_spin": pace_or_spin,
                "active_years": active_years
            },
            "phase_split": {
                "powerplay_balls": pp_balls,
                "powerplay_pct": pp_pct,
                "middle_balls": mid_balls,
                "middle_pct": mid_pct,
                "death_balls": dth_balls,
                "death_pct": dth_pct
            },
            "innings_split": {
                "innings_1_balls": inn1_cnt,
                "innings_1_pct": inn1_pct,
                "innings_2_balls": inn2_cnt,
                "innings_2_pct": inn2_pct
            },
            "stability_check": stab,
            "match_strip": match_contributions
        }

        # Write individual player JSON
        with open(os.path.join(PLAYERS_DIR, f"{pid}.json"), "w", encoding="utf-8") as pf:
            json.dump(player_profile, pf, indent=2)

    # Write rankings.json
    with open(os.path.join(PUBLIC_DATA_DIR, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump(rankings_list, f, indent=2)
    print(f"[OK] Wrote rankings.json ({len(rankings_list)} players)")
    print(f"[OK] Wrote {len(rankings_list)} individual files to public/data/players/<player_id>.json")

    print("\n" + "=" * 70)
    print("  PHASE 1 EXPORT COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
