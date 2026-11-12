"""
Phase 3 Unit Tests: Data Integrity and Clean Data Enforcement
Asserts:
1. Ratings input dataset contains 0 DLS deliveries.
2. Ratings functions strictly fail with AssertionError/ValueError if any is_dls=True row reaches ratings code.
3. Kept 2nd-innings matches for RRR have reconstruction error strictly bounded within [-10, +10] runs.
4. Approximate matches are cleanly flagged.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_CLEAN = os.path.join(ROOT, "data", "ball_state_clean.parquet")


def test_no_dls_in_clean_data():
    """Verify that ball_state_clean contains exactly 0 DLS rows."""
    df = pd.read_parquet(DATA_CLEAN)
    assert not df["is_dls"].any(), f"FAILED: Clean dataset contains {df['is_dls'].sum()} DLS rows!"
    assert len(df) == 195707, f"FAILED: Expected 195,707 clean rows, got {len(df):,}"


def test_ratings_rejects_dls():
    """Verify that ratings input validator immediately raises AssertionError if DLS rows are present."""
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from ratings.player_ratings import validate_ratings_input

    clean_df = pd.read_parquet(DATA_CLEAN).head(100).copy()
    # Should pass on clean data
    validate_ratings_input(clean_df)

    # Must fail when DLS is injected
    dirty_df = clean_df.copy()
    dirty_df.loc[dirty_df.index[0], "is_dls"] = True

    with pytest.raises(AssertionError, match="DLS rows detected in ratings input"):
        validate_ratings_input(dirty_df)


def test_rrr_reconstruction_error_bounds():
    """Verify that matches kept for RRR (exclude_from_rrr == False) have reconstruction error within [-10, +10]."""
    df = pd.read_parquet(DATA_CLEAN)
    inn2_kept = df[(df["innings"] == 2) & (~df["exclude_from_rrr"])]

    # Reconstruction error must be within [-10, 10]
    errors = inn2_kept["reconstruction_error"].dropna()
    assert (errors >= -10.0).all(), f"Error below -10 found: {errors.min()}"
    assert (errors <= 10.0).all(), f"Error above +10 found: {errors.max()}"


def test_approximate_matches_flagged():
    """Verify that matches with 0 < |error| <= 10 are flagged approximate_score=True."""
    df = pd.read_parquet(DATA_CLEAN)
    approx_rows = df[df["approximate_score"]]
    assert (approx_rows["reconstruction_error"].abs() > 0).all()
    assert (approx_rows["reconstruction_error"].abs() <= 10.0).all()
    assert not approx_rows["is_dls"].any()
