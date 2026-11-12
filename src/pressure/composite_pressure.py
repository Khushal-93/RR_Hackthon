"""
Phase 2: Composite Pressure Index (Remediated)
Implements an explainable 0-10 score combining:
- Required run rate vs current (run-rate gap)
- Balls remaining (death overs urgency)
- Innings stage & match closeness
- Knockout match importance multiplier

Audit Fix Applied:
Removed wickets-in-hand from the pressure score used to validate dismissal rates
to prevent circular validation / outcome proxy leakage.
Provides an `include_wickets` toggle for before/after comparison.
"""

import numpy as np
import pandas as pd


def compute_composite_pressure(df: pd.DataFrame, include_wickets: bool = False) -> pd.Series:
    """
    Computes an explainable Pressure Score [0.0 - 10.0] for every delivery.
    
    Parameters:
        df: DataFrame with ball-by-ball features.
        include_wickets: If False (default, recommended), excludes wickets-in-hand
                         to avoid mechanical coupling with dismissal rate validation.
    """
    p_score = pd.Series(index=df.index, dtype=float)

    # ─────────────────────────────────────────────────────────────────────────
    # INNINGS 2: Chasing Pressure
    # ─────────────────────────────────────────────────────────────────────────
    mask2 = df["innings"] == 2
    if mask2.any():
        sub2 = df[mask2]
        rrr = np.clip(sub2["required_run_rate"].fillna(8.0), 0.0, 36.0)
        gap = np.clip(sub2["run_rate_gap"].fillna(0.0), -6.0, 18.0)
        br  = np.clip(sub2["balls_remaining"], 0.0, 120.0)
        ko  = sub2["knock_out"].fillna(0).astype(float)

        # 1. RRR Urgency [0 - 3.5]
        rrr_factor = np.clip((rrr - 6.0) / 8.0, 0.0, 1.0) * 3.5

        # 2. Balls Remaining / Stage Crunch [0 - 2.5]
        stage_factor = np.clip((120.0 - br) / 120.0, 0.0, 1.0)**1.5 * 2.5

        # 3. Gap Component [0 - 1.0]
        gap_factor = np.clip(gap / 6.0, 0.0, 1.0) * 1.0

        if include_wickets:
            wkt = np.clip(sub2["wickets_in_hand"], 0.0, 10.0)
            wkt_factor = np.where(
                wkt <= 3,
                2.0 + (3.0 - wkt) / 3.0,
                (10.0 - wkt) / 7.0 * 2.0
            )
            wkt_factor = np.clip(wkt_factor, 0.0, 3.0)
            raw_p2 = rrr_factor + wkt_factor + stage_factor + gap_factor
            raw_p2 = raw_p2 * np.where(ko == 1, 1.1, 1.0)
            p_score.loc[mask2] = np.clip(raw_p2, 0.0, 10.0)
        else:
            raw_p2 = rrr_factor + stage_factor + gap_factor
            raw_p2 = raw_p2 * np.where(ko == 1, 1.1, 1.0)
            # Rescale base of 7.0 to 10.0
            p_score.loc[mask2] = np.clip((raw_p2 / 7.0) * 10.0, 0.0, 10.0)

    # ─────────────────────────────────────────────────────────────────────────
    # INNINGS 1: Setting a Target Pressure
    # ─────────────────────────────────────────────────────────────────────────
    mask1 = df["innings"] == 1
    if mask1.any():
        sub1 = df[mask1]
        br  = np.clip(sub1["balls_remaining"], 0.0, 120.0)
        crr = np.clip(sub1["current_run_rate"].fillna(7.5), 0.0, 36.0)
        ko  = sub1["knock_out"].fillna(0).astype(float)

        # 1. Death Overs Push [0 - 3.5] (overs 16-20 acceleration urgency)
        death_push = np.clip((120.0 - br) / 120.0, 0.0, 1.0)**2 * 3.5

        # 2. Par Rate Lag [0 - 2.5] (if team scoring below 7.5 rpo)
        lag_factor = np.clip((8.0 - crr) / 4.0, 0.0, 1.0) * 2.5

        if include_wickets:
            wkt = np.clip(sub1["wickets_in_hand"], 0.0, 10.0)
            early_loss = np.clip((10.0 - wkt) / 6.0, 0.0, 1.0) * 4.0
            raw_p1 = early_loss + death_push + lag_factor
            raw_p1 = raw_p1 * np.where(ko == 1, 1.1, 1.0)
            p_score.loc[mask1] = np.clip(raw_p1, 0.0, 10.0)
        else:
            raw_p1 = death_push + lag_factor
            raw_p1 = raw_p1 * np.where(ko == 1, 1.1, 1.0)
            # Rescale base of 6.0 to 10.0
            p_score.loc[mask1] = np.clip((raw_p1 / 6.0) * 10.0, 0.0, 10.0)

    return p_score
