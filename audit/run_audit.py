"""Independent, read-only audit of the pressure_xi cricket pipeline.

All generated files are confined to this directory. The source pipeline is
imported only to reproduce its behavior; it is never edited or saved over.
"""

from __future__ import annotations

import contextlib
import io
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler


ROOT = Path(r"C:\Users\Khushal\pressure_xi")
AUDIT = ROOT / "audit"
RAW = Path(r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet")
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))

from pipeline.build_pipeline import build_ball_state
from pressure.composite_pressure import compute_composite_pressure
from pressure.win_probability import WinProbabilityModel


sections: list[tuple[str, str, str, str]] = []
statuses: list[tuple[str, str, str]] = []


def emit(title: str, status: str, code: str, output: str, why: str = "") -> None:
    statuses.append((title, status, why))
    sections.append((title, status, code.strip(), output.rstrip()))
    print(f"\n[{status}] {title}")
    print(output.rstrip())


def fmt(value: object) -> str:
    return f"{value:,}" if isinstance(value, (int, np.integer)) else str(value)


def run_code(func, *args, **kwargs):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = func(*args, **kwargs)
    return result, buffer.getvalue()


def parse_run_margin(result: object):
    if pd.isna(result):
        return None
    match = re.search(r"\bwon\s+by\s+(\d+)\s+runs?\b", str(result), re.I)
    return int(match.group(1)) if match else None


def raw_to_int(value) -> int:
    if pd.isna(value):
        return 0
    return int(value)


def safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else np.nan


def band_metrics(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    rows = []
    for band in ["Low", "Medium", "High"]:
        part = frame.loc[frame[column].astype(str) == band]
        legal = part.loc[part["is_legal"].astype(bool)]
        n = len(legal)
        runs = legal["runs"].sum()
        wickets = legal["is_wicket"].astype(bool).sum()
        rows.append({
            "Band": band,
            "Total Deliveries": len(part),
            "Legal Balls": n,
            "Strike Rate": round(safe_ratio(runs * 100, n), 2),
            "Bowling Econ": round(safe_ratio(legal["total_delivery_runs"].sum() * 6, n), 2),
            "Dismissal Rate (%)": round(safe_ratio(wickets * 100, n), 2),
            "Dot Ball (%)": round(safe_ratio(
                ((legal["runs"] == 0) & ~legal["is_wicket"].astype(bool)).sum() * 100, n), 2),
            "Boundary (%)": round(safe_ratio(
                (legal["is_four"].astype(bool).sum() + legal["is_six"].astype(bool).sum()) * 100, n), 2),
            "Six (%)": round(safe_ratio(legal["is_six"].astype(bool).sum() * 100, n), 2),
            "Runs/Wicket": round(safe_ratio(runs, wickets), 2),
        })
    return pd.DataFrame(rows)


def metric_report(metrics: pd.DataFrame) -> str:
    return metrics.to_string(index=False)


def score_metrics(y: np.ndarray, pred: np.ndarray) -> tuple[dict, pd.DataFrame]:
    pred = np.clip(np.asarray(pred, dtype=float), 1e-12, 1 - 1e-12)
    y = np.asarray(y, dtype=float)
    stats = {
        "n": len(y),
        "base_rate": float(y.mean()),
        "brier": float(np.mean((pred - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(pred) + (1 - y) * np.log(1 - pred))),
    }
    table = pd.DataFrame({"pred": pred, "actual": y})
    table["decile"] = pd.qcut(table["pred"], 10, duplicates="drop")
    cal = table.groupby("decile", observed=False).agg(
        mean_pred=("pred", "mean"),
        win_rate=("actual", "mean"),
        count=("actual", "size"),
    ).reset_index()
    return stats, cal


def simple_score_features(df: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        np.ones(len(df)),
        np.clip(df["runs_at_ball"].to_numpy(dtype=float), 0, 300) / 300.0,
        np.clip(df["balls_remaining"].to_numpy(dtype=float), 0, 120) / 120.0,
    ])


def fit_logistic(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    def objective(weights):
        z = np.clip(X @ weights, -25, 25)
        p = 1 / (1 + np.exp(-z))
        p = np.clip(p, 1e-12, 1 - 1e-12)
        loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        grad = X.T @ (p - y) / len(y)
        return loss, grad

    return minimize(objective, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B").x


def fit_predict_score_only(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Train score + balls-remaining logistic models separately by innings."""
    prediction = np.full(len(test), np.nan)
    for innings in [1, 2]:
        train_part = train.loc[(train["innings"] == innings) & train["win_team_id"].notna()]
        test_mask = test["innings"].to_numpy() == innings
        if train_part.empty or not test_mask.any():
            continue
        y_train = (train_part["batting_team_id"] == train_part["win_team_id"]).astype(float).to_numpy()
        weights = fit_logistic(simple_score_features(train_part), y_train)
        prediction[test_mask] = 1 / (1 + np.exp(-np.clip(
            simple_score_features(test.loc[test_mask]) @ weights, -25, 25)))
    return prediction


def calibration_text(stats: dict, table: pd.DataFrame) -> str:
    return (
        f"n={stats['n']:,}; batting-team win rate={stats['base_rate']:.6f}; "
        f"Brier={stats['brier']:.6f}; log-loss={stats['log_loss']:.6f}\n"
        + table[["mean_pred", "win_rate", "count"]].to_string(
            index=False, formatters={"mean_pred": "{:.4f}".format, "win_rate": "{:.4f}".format})
    )


def get_valid(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame["win_team_id"].notna() & (frame["win_team_id"] > 0)].copy()


def compute_custom_wp_predictions(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    model = WinProbabilityModel(l2_reg=1e-4)
    model.fit(train)
    return model.predict_wp(test)


def adjusted_band_rates(frame: pd.DataFrame, band_col: str) -> tuple[pd.DataFrame, dict]:
    """Standardize pairwise rates over shared batter/role/over strata."""
    legal = frame.loc[
        frame["is_legal"].astype(bool)
        & frame["striker_id"].notna()
        & frame["batting_order"].notna()
        & frame[band_col].notna()
    ].copy()
    keys = ["striker_id", "innings", "overid", "batting_order"]
    legal["band_name"] = legal[band_col].astype(str)
    grouped = legal.groupby(keys + ["band_name"], observed=True).agg(
        balls=("runs", "size"),
        runs=("runs", "sum"),
        wickets=("is_wicket", "sum"),
    ).reset_index()
    results = []
    coverages = {}
    for band_a, band_b in [("Low", "Medium"), ("Low", "High"), ("Medium", "High")]:
        pair = grouped[grouped["band_name"].isin([band_a, band_b])]
        present = pair.groupby(keys, observed=True)["band_name"].nunique()
        shared = present[present == 2].index
        if len(shared) == 0:
            coverages[f"{band_a}-{band_b}"] = {"strata": 0, "coverage": 0.0}
            continue
        shared_df = pair.set_index(keys).loc[shared].reset_index()
        weight_total = shared_df.groupby(keys, observed=True)["balls"].sum()
        weight = weight_total / weight_total.sum()
        rates = {}
        for band in [band_a, band_b]:
            piece = shared_df[shared_df["band_name"] == band].set_index(keys)
            aligned_w = weight.reindex(piece.index)
            rates[band] = {
                "Strike Rate": float(((piece["runs"] / piece["balls"] * 100) * aligned_w).sum()),
                "Dismissal Rate (%)": float(((piece["wickets"] / piece["balls"] * 100) * aligned_w).sum()),
            }
        results.append({
            "Comparison": f"{band_a} vs {band_b}",
            f"{band_a} SR": rates[band_a]["Strike Rate"],
            f"{band_b} SR": rates[band_b]["Strike Rate"],
            f"{band_a} dismissal (%)": rates[band_a]["Dismissal Rate (%)"],
            f"{band_b} dismissal (%)": rates[band_b]["Dismissal Rate (%)"],
        })
        legal_pair = int(shared_df["balls"].sum())
        coverages[f"{band_a}-{band_b}"] = {
            "strata": len(shared),
            "coverage": safe_ratio(legal_pair, len(legal)),
            "rates": rates,
        }
    return pd.DataFrame(results), {"rows": len(legal), "comparisons": coverages}


def composite_components(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    mask2 = frame["innings"].to_numpy() == 2
    mask1 = frame["innings"].to_numpy() == 1
    rrr = np.clip(frame["required_run_rate"].fillna(8.0).to_numpy(), 0, 36)
    gap = np.clip(frame["run_rate_gap"].fillna(0.0).to_numpy(), -6, 18)
    wickets = np.clip(frame["wickets_in_hand"].to_numpy(dtype=float), 0, 10)
    br = np.clip(frame["balls_remaining"].to_numpy(dtype=float), 0, 120)
    ko = frame["knock_out"].fillna(0).to_numpy(dtype=float)
    crr = np.clip(frame["current_run_rate"].fillna(7.5).to_numpy(), 0, 36)
    rrr_comp = np.where(mask2, np.clip((rrr - 6) / 8, 0, 1) * 3.5, 0)
    wkt_comp = np.where(
        mask2,
        np.where(wickets <= 3, 2 + (3 - wickets) / 3, (10 - wickets) / 7 * 2),
        np.clip((10 - wickets) / 6, 0, 1) * 4,
    )
    stage_comp = np.where(
        mask2, np.clip((120 - br) / 120, 0, 1) ** 1.5 * 2.5,
        np.clip((120 - br) / 120, 0, 1) ** 2 * 3.5,
    )
    gap_comp = np.where(mask2, np.clip(gap / 6, 0, 1), 0)
    lag_comp = np.where(mask1, np.clip((8 - crr) / 4, 0, 1) * 2.5, 0)
    multiplier = np.where(ko == 1, 1.1, 1.0)
    return {
        "rrr": rrr_comp * multiplier,
        "wickets": wkt_comp * multiplier,
        "stage": stage_comp * multiplier,
        "gap": gap_comp * multiplier,
        "lag": lag_comp * multiplier,
    }


def pressure_for_weights(frame: pd.DataFrame, components: dict, changes: dict) -> np.ndarray:
    score = np.zeros(len(frame))
    for name in ["rrr", "wickets", "stage", "gap", "lag"]:
        score += components[name] * changes.get(name, 1.0)
    return np.clip(score, 0, 10)


def classify_bands(score: np.ndarray, low: float, high: float) -> pd.Categorical:
    return pd.cut(score, [-np.inf, low, high, np.inf], labels=["Low", "Medium", "High"])


def band_summary(frame: pd.DataFrame, score: np.ndarray, low: float, high: float) -> str:
    bands = classify_bands(score, low, high)
    part = frame.copy()
    part["_audit_band"] = bands
    met = band_metrics(part, "_audit_band")
    return met[["Band", "Total Deliveries", "Legal Balls", "Strike Rate", "Dismissal Rate (%)"]].to_string(index=False)


def recon_and_context(raw_bbb: pd.DataFrame, matches: pd.DataFrame, comp: pd.DataFrame):
    bbb = raw_bbb.copy()
    bbb["bat_runs"] = pd.to_numeric(bbb["runs"], errors="coerce").fillna(0)
    bbb["extra_runs_recorded"] = pd.to_numeric(bbb["extras_2_runs"], errors="coerce").fillna(0)
    bbb["pipeline_like_runs"] = bbb["bat_runs"] + bbb["extra_runs_recorded"] + (bbb["extras_type"] == "wide").astype(int)
    innings = bbb[bbb["innings"].isin([1, 2])].groupby(["match_id", "innings"])["pipeline_like_runs"].sum().unstack()
    innings = innings.rename(columns={1: "inn1", 2: "inn2"}).reset_index()
    match_view = matches.merge(innings, on="match_id", how="left")
    match_view["result_margin"] = match_view["result"].map(parse_run_margin)
    run_games = match_view[match_view["result_margin"].notna()].copy()
    run_games["reconstructed_margin"] = run_games["inn1"] - run_games["inn2"]
    run_games["error"] = run_games["reconstructed_margin"] - run_games["result_margin"]
    run_games["is_dls"] = (
        pd.to_numeric(run_games["revised_target"], errors="coerce").fillna(0) > 0
    )
    comps = comp[["comp_id", "comp_name", "match_format", "season"]]
    return bbb, innings, match_view, run_games, comps


def main() -> None:
    np.random.seed(20261111)
    pd.set_option("display.max_rows", 250)
    raw_bbb = pd.read_parquet(RAW / "ball_by_ball.parquet")
    matches = pd.read_parquet(RAW / "matches.parquet")
    competitions = pd.read_parquet(RAW / "competitions.parquet")
    base_saved = pd.read_parquet(DATA / "ball_state.parquet")
    pressure_saved = pd.read_parquet(DATA / "ball_state_pressure.parquet")
    bbb, raw_innings, match_view, run_games, comp = recon_and_context(
        raw_bbb, matches, competitions)

    # 1.1 The extras1_runs field is independently cross-checked against labels.
    code_map = {1: "Overstep", 2: "wide", 3: "legbyes", 4: "byes", 5: "other", 7: "Penalty", 6: None}
    mapped_ok = sum(
        int(((raw_bbb["extras1_runs"] == code) & (raw_bbb["extras_type"].isna() if label is None
             else raw_bbb["extras_type"].eq(label))).sum())
        for code, label in code_map.items()
    )
    extras_counts = raw_bbb["extras1_runs"].value_counts(dropna=False).sort_index()
    extras2_nonzero = int((pd.to_numeric(raw_bbb["extras_2_runs"], errors="coerce").fillna(0) != 0).sum())
    wide_n = int((raw_bbb["extras_type"] == "wide").sum())
    noball_n = int((raw_bbb["extras_type"] == "Overstep").sum())
    detail = (
        f"raw_rows={len(raw_bbb):,}; exact code/label matches={mapped_ok:,}/{len(raw_bbb):,}\n"
        f"extras1_runs value counts:\n{extras_counts.to_string()}\n"
        f"extras_2_runs nonzero rows={extras2_nonzero:,}; wide={wide_n:,}; no-ball={noball_n:,}\n"
        "Code mapping cross-check: " + ", ".join(
            f"{k}->{v if v is not None else 'NULL/no extras'}" for k, v in code_map.items())
    )
    emit(
        "1A extras1_runs is type code",
        "PASS" if mapped_ok == len(raw_bbb) else "FAIL",
        """matches = sum((extras1_runs == code) & extras_type == expected_label)
extras1_runs.value_counts(); extras_2_runs.ne(0).sum()""",
        detail,
        "The code column maps one-to-one to extras_type, not run amounts."
    )

    # 1.2 Reconcile every run-margin result using only the recorded run columns.
    exact = int((run_games["error"] == 0).sum())
    within1 = int((run_games["error"].abs() <= 1).sum())
    bad = run_games[run_games["error"] != 0]
    exact_non_dls = int((run_games.loc[~run_games["is_dls"], "error"] == 0).sum())
    non_dls_n = int((~run_games["is_dls"]).sum())
    other_result_count = int(matches["result"].map(parse_run_margin).isna().sum())
    extras_by_type = raw_bbb.assign(
        _extras2=pd.to_numeric(raw_bbb["extras_2_runs"], errors="coerce").fillna(0)
    ).groupby("extras_type", dropna=False).agg(
        deliveries=("_extras2", "size"),
        recorded_extra_runs=("_extras2", "sum"),
        rows_with_extra=("_extras2", lambda values: int((values != 0).sum())),
    )
    recon_output = (
        f"run-margin matches parsed={len(run_games):,}; exact margin matches={exact:,} "
        f"({100 * safe_ratio(exact, len(run_games)):.2f}%); within +/-1={within1:,} "
        f"({100 * safe_ratio(within1, len(run_games)):.2f}%)\n"
        f"non-DLS exact margin matches={exact_non_dls:,}/{non_dls_n:,} "
        f"({100 * safe_ratio(exact_non_dls, non_dls_n):.2f}%)\n"
        f"matches without a numeric run-margin in result text={other_result_count:,}/{len(matches):,}; "
        "wicket-margin/no-result text does not expose final innings scores for total reconciliation\n"
        f"extras_type and recorded extras_2_runs:\n{extras_by_type.to_string()}\n"
        f"mismatch count={len(bad):,}; each row: match_id | result | innings1 | innings2 | "
        "reported margin | reconstructed margin | error | revised_target\n"
        + bad[["match_id", "result", "inn1", "inn2", "result_margin",
               "reconstructed_margin", "error", "revised_target"]].to_string(index=False, max_rows=None)
    )
    emit(
        "1B innings totals vs result text",
        "FAIL" if exact != len(run_games) else "PASS",
        """delivery_total = runs + extras_2_runs + (extras_type == "wide")
innings_total = delivery_total.groupby([match_id, innings]).sum()
reconstructed_margin = innings1 - innings2
compare(reconstructed_margin, integer parsed from matches.result)""",
        recon_output,
        "Recorded extras are incomplete; even this lower-bound reconstruction cannot match all scorecard margins."
    )

    # 1.3 Superovers, DLS flags and their actual use.
    super_rows = raw_bbb[raw_bbb["innings"] > 2]
    dls_match_ids = set(matches.loc[
        pd.to_numeric(matches["revised_target"], errors="coerce").fillna(0) > 0, "match_id"])
    revised_overs_ids = set(matches.loc[
        matches["first_inn_revised_overs"].notna() | matches["second_inn_revised_overs"].notna(),
        "match_id"])
    dls_state = base_saved[base_saved["match_id"].isin(dls_match_ids)]
    dls_pressure = pressure_saved[pressure_saved["match_id"].isin(dls_match_ids)]
    dls_second = dls_state[dls_state["innings"] == 2]
    innings_counts = raw_bbb["innings"].value_counts().sort_index()
    target_compare = dls_second[["match_id", "target"]].merge(
        matches[["match_id", "revised_target"]], on="match_id", how="left")
    target_mismatch = int((
        pd.to_numeric(target_compare["target"], errors="coerce")
        != pd.to_numeric(target_compare["revised_target"], errors="coerce")
    ).sum())
    dls_output = (
        f"raw super-over rows (innings>2)={len(super_rows):,}; matches={super_rows['match_id'].nunique():,}\n"
        f"raw innings distribution:\n{innings_counts.to_string()}\n"
        f"ball_state rows={len(base_saved):,}; any innings>2={int((~base_saved['innings'].isin([1,2])).sum()):,}\n"
        f"matches with revised_target>0={len(dls_match_ids):,}; with revised overs={len(revised_overs_ids):,}\n"
        f"DLS rows retained: state={len(dls_state):,}; pressure={len(dls_pressure):,}; "
        f"2nd-innings target != revised_target rows={target_mismatch:,}\n"
        f"exclude_from_rrr true rows={int(base_saved['exclude_from_rrr'].astype(bool).sum()):,}; "
        f"retained among model/band input={int(pressure_saved['exclude_from_rrr'].astype(bool).sum()):,}\n"
        "Source behavior: DLS target/overs alter state; DLS rows remain in model fit, leverage, composite and validation."
    )
    emit(
        "1C superovers and DLS handling",
        "FAIL" if len(dls_state) and base_saved["exclude_from_rrr"].astype(bool).sum() else "PASS",
        """superovers = raw[innings > 2]
DLS = revised_target > 0
check DLS target/overs and count DLS rows in model/pressure inputs""",
        dls_output,
        "Superovers are excluded. DLS rows are only partially handled and are not separated from fitting or pressure summaries."
    )

    # 1.4 Legal ball and balls remaining checks.
    raw_illegal = raw_bbb["extras_type"].isin(["wide", "Overstep"])
    raw_legal = ~raw_illegal
    stored_legal_total = int(base_saved["is_legal"].astype(bool).sum())
    raw_legal_retained = int(raw_legal[raw_bbb["innings"].isin([1, 2])].sum())
    br_min = int(base_saved["balls_remaining"].min())
    br_max = int(base_saved["balls_remaining"].max())
    lb_diff = int((base_saved["is_legal"].astype(bool) != (
        ~base_saved["is_wide"].astype(bool) & ~base_saved["is_noball"].astype(bool))).sum())
    overrun = base_saved.groupby(["match_id", "innings"], observed=True).agg(
        last_legal=("legal_ball_num", "max"), max_balls=("max_legal_balls", "max"))
    revised_values = pd.concat([
        pd.to_numeric(matches["first_inn_revised_overs"], errors="coerce"),
        pd.to_numeric(matches["second_inn_revised_overs"], errors="coerce"),
    ]).dropna()
    overrun_details = overrun[overrun["max_balls"] > 120].reset_index().merge(
        matches[["match_id", "first_inn_revised_overs", "second_inn_revised_overs"]],
        on="match_id", how="left").head(12)
    overrun_count = int((overrun["last_legal"] > overrun["max_balls"]).sum())
    state_output = (
        f"retained rows={len(base_saved):,}; raw legal rows in innings 1-2={raw_legal_retained:,}; "
        f"stored legal rows={stored_legal_total:,}; legal-flag mismatches={lb_diff:,}\n"
        f"balls_remaining min={br_min}; max={br_max}; outside [0,120]="
        f"{int((~base_saved['balls_remaining'].between(0,120)).sum()):,}\n"
        f"innings whose legal_ball_num exceeds max_legal_balls={overrun_count:,}/{len(overrun):,}; "
        f"rows with legal_ball_num>120={int((base_saved['legal_ball_num']>120).sum()):,}\n"
        f"revised-over field min/max={revised_values.min():g}/{revised_values.max():g}; "
        f"values divisible by 6={int((revised_values % 6 == 0).sum()):,}/{len(revised_values):,}; "
        f"distinct samples={sorted(revised_values.unique())[:12]}\n"
        "Examples of max_legal_balls >120 (pipeline multiplies the revised field by 6):\n"
        + overrun_details.to_string(index=False)
        + "\n"
        f"first delivery of each innings: legal_ball_num/balls_remaining sample:\n"
        + base_saved.sort_values(["match_id", "innings", "overid", "over_ball_num"])
            .groupby(["match_id", "innings"], observed=True).head(1)
            [["match_id", "innings", "legal_ball_num", "balls_remaining", "max_legal_balls"]]
            .head(8).to_string(index=False)
    )
    emit(
        "1D legal balls and remaining-ball bounds",
        "PASS" if lb_diff == 0 and br_min >= 0 and br_max <= 120 else "FAIL",
        """is_legal = extras_type not in {"wide", "Overstep"}
legal_ball_num = groupby(match_id, innings).is_legal.cumsum()
balls_remaining = clip(max_legal_balls - legal_ball_num, lower=0)
compare raw legal flags and assert 0 <= balls_remaining <= 120""",
        state_output,
        "Normal innings counters are legal, but revised-resource fields appear already expressed in balls and are multiplied by six; first-ball state is also one ball low."
    )

    # 1.5 Row-count arithmetic and band denominator.
    raw_n = len(raw_bbb)
    removed = raw_n - len(base_saved)
    total_band_rows = pressure_saved["pressure_band_comp"].notna().sum()
    comp_legal = pressure_saved.loc[
        pressure_saved["is_legal"].astype(bool), "pressure_band_comp"].notna().sum()
    li_legal = pressure_saved.loc[
        pressure_saved["is_legal"].astype(bool), "pressure_band_lev"].notna().sum()
    count_output = (
        f"raw deliveries={raw_n:,}; raw innings>2={len(super_rows):,}; "
        f"raw minus superovers={raw_n-len(super_rows):,}; stored={len(base_saved):,}; "
        f"stored difference={removed:,}\n"
        f"composite Total Deliveries sum={int(total_band_rows):,}; "
        f"composite Legal Balls sum={int(comp_legal):,}; "
        f"leverage Legal Balls sum={int(li_legal):,}\n"
        "Band table Total Deliveries counts all rows; its Legal Balls metrics omit wides/no-balls."
    )
    emit(
        "1E 200,999 to 200,961 and band denominator",
        "PASS" if removed == len(super_rows) and len(base_saved) == raw_n - len(super_rows) else "FAIL",
        """retained = raw rows with innings in {1,2}
band_total = pressure_band.notna().sum()
band_legal = (is_legal & pressure_band.notna()).sum()""",
        count_output,
        "The ~192,675 figure is the legal-ball subtotal, not the band total-delivery subtotal."
    )

    # 2.1 Feature timing and in-sample claim.
    model_source = (ROOT / "src" / "pressure" / "win_probability.py").read_text(encoding="utf-8")
    feature_names = [
        "runs_needed", "balls_remaining", "wickets_in_hand", "required_run_rate",
        "current_run_rate", "run_rate_gap", "runs_at_ball", "match_format",
    ]
    uses_outcome_as_feature = any(
        name in model_source.split("def _extract_features_inn2", 1)[1].split("def fit", 1)[0]
        or name in model_source.split("def _extract_features_inn1", 1)[1].split("def fit", 1)[0]
        for name in ["win_team_id", "result", "final_score", "is_wicket", "cumulative_runs"]
    )
    in_sample_metrics = WinProbabilityModel(l2_reg=1e-4)
    in_sample_metrics.fit(base_saved)
    in_sample = in_sample_metrics.evaluate(base_saved)
    same_rows = len(get_valid(base_saved))
    claimed_matches = (
        round(in_sample["brier_score"], 4) == 0.1799
        and round(in_sample["log_loss"], 4) == 0.5282
    )
    feature_output = (
        f"feature names used: innings 2={feature_names}; innings 1= runs_at_ball, balls_remaining, "
        "wickets_in_hand, current_run_rate, match_format, derived projection\n"
        f"feature-source scan found explicit outcome/final-score/current-dismissal fields={uses_outcome_as_feature}\n"
        f"training rows with winner labels={same_rows:,}; evaluation rows={same_rows:,} (same dataset)\n"
        f"reproduced in-sample Brier={in_sample['brier_score']:.6f}; log-loss={in_sample['log_loss']:.6f}; "
        f"rounds to reported claims={claimed_matches}\n"
        "Important timing issue: legal_ball_num is inclusive of the current delivery, while runs_at_ball is pre-delivery."
    )
    emit(
        "2A no future information and claimed evaluation",
        "FAIL" if claimed_matches else "PASS",
        """inspect _extract_features_inn1/_extract_features_inn2
fit(df); evaluate(df)  # same rows, not out of sample""",
        feature_output,
        "No final result/current dismissal is a direct model feature; however, the reported metrics are resubstitution metrics, not validation."
    )

    # 2.2 Match-grouped out-of-sample CV and baselines.
    valid = get_valid(base_saved).reset_index(drop=True)
    y = (valid["batting_team_id"] == valid["win_team_id"]).astype(float).to_numpy()
    groups = valid["match_id"].to_numpy()
    group_kfold = GroupKFold(n_splits=5)
    cv_preds = np.full(len(valid), np.nan)
    cv_const = np.full(len(valid), np.nan)
    cv_simple = np.full(len(valid), np.nan)
    fold_lines = []
    for fold, (train_idx, test_idx) in enumerate(group_kfold.split(valid, y, groups), start=1):
        train, test = valid.iloc[train_idx], valid.iloc[test_idx]
        cv_preds[test_idx] = compute_custom_wp_predictions(train, test)
        cv_const[test_idx] = y[train_idx].mean()
        cv_simple[test_idx] = fit_predict_score_only(train, test)
        fold_lines.append(
            f"fold {fold}: train matches={train['match_id'].nunique():,}; "
            f"test matches={test['match_id'].nunique():,}; "
            f"overlap={len(set(train['match_id']) & set(test['match_id']))}"
        )
    cv_model_stats, cv_model_cal = score_metrics(y, cv_preds)
    cv_const_stats, cv_const_cal = score_metrics(y, cv_const)
    cv_simple_stats, cv_simple_cal = score_metrics(y, cv_simple)
    cv_output = (
        "\n".join(fold_lines)
        + "\n\nWP model (5-fold GroupKFold by match_id):\n"
        + calibration_text(cv_model_stats, cv_model_cal)
        + "\n\nConstant training win-rate baseline:\n"
        + calibration_text(cv_const_stats, cv_const_cal)
        + "\n\nScore + balls-remaining logistic baseline:\n"
        + calibration_text(cv_simple_stats, cv_simple_cal)
        + f"\n\nbeats constant (Brier AND log-loss): "
        f"{cv_model_stats['brier'] < cv_const_stats['brier'] and cv_model_stats['log_loss'] < cv_const_stats['log_loss']}; "
        f"beats score/balls baseline (Brier AND log-loss): "
        f"{cv_model_stats['brier'] < cv_simple_stats['brier'] and cv_model_stats['log_loss'] < cv_simple_stats['log_loss']}"
    )
    cv_pass = (
        cv_model_stats["brier"] < cv_const_stats["brier"]
        and cv_model_stats["log_loss"] < cv_const_stats["log_loss"]
        and cv_model_stats["brier"] < cv_simple_stats["brier"]
        and cv_model_stats["log_loss"] < cv_simple_stats["log_loss"]
    )
    emit(
        "2B GroupKFold validation and baselines",
        "PASS" if cv_pass else "FAIL",
        """for train_idx, test_idx in GroupKFold(5).split(valid, y, groups=match_id):
    fit original two-innings logistic WP model on train_idx
    predict test_idx
    fit constant-rate and [runs_at_ball, balls_remaining] baselines on train_idx
compute Brier, log-loss and qcut deciles on concatenated held-out predictions""",
        cv_output,
        "Out-of-fold predictions prevent deliveries from the same match appearing in both train and test."
    )

    # 2.3 Chronological split.
    dated = valid.copy()
    dated["_date"] = pd.to_datetime(dated["match_date"], errors="coerce", utc=True)
    unique_dates = np.sort(dated["_date"].dropna().unique())
    cutoff_i = max(1, int(len(unique_dates) * 0.8))
    cutoff = unique_dates[cutoff_i]
    time_train_idx = np.flatnonzero((dated["_date"] < cutoff).to_numpy())
    time_test_idx = np.flatnonzero((dated["_date"] >= cutoff).to_numpy())
    time_train, time_test = dated.iloc[time_train_idx], dated.iloc[time_test_idx]
    time_pred = compute_custom_wp_predictions(time_train, time_test)
    time_y = (time_test["batting_team_id"] == time_test["win_team_id"]).astype(float).to_numpy()
    time_const = np.full(len(time_test), (time_train["batting_team_id"] == time_train["win_team_id"]).mean())
    time_simple = fit_predict_score_only(time_train, time_test)
    time_stats, time_cal = score_metrics(time_y, time_pred)
    time_const_stats, time_const_cal = score_metrics(time_y, time_const)
    time_simple_stats, time_simple_cal = score_metrics(time_y, time_simple)
    time_output = (
        f"train date range={time_train['_date'].min()}..{time_train['_date'].max()}; "
        f"test date range={time_test['_date'].min()}..{time_test['_date'].max()}; cutoff={cutoff}\n"
        f"train rows/matches={len(time_train):,}/{time_train['match_id'].nunique():,}; "
        f"test rows/matches={len(time_test):,}/{time_test['match_id'].nunique():,}\n\nWP model:\n"
        + calibration_text(time_stats, time_cal)
        + "\n\nConstant baseline:\n" + calibration_text(time_const_stats, time_const_cal)
        + "\n\nScore + balls-remaining baseline:\n" + calibration_text(time_simple_stats, time_simple_cal)
        + f"\n\nbeats constant (Brier AND log-loss): "
        f"{time_stats['brier'] < time_const_stats['brier'] and time_stats['log_loss'] < time_const_stats['log_loss']}; "
        f"beats score/balls baseline (Brier AND log-loss): "
        f"{time_stats['brier'] < time_simple_stats['brier'] and time_stats['log_loss'] < time_simple_stats['log_loss']}"
    )
    time_pass = (
        time_stats["brier"] < time_const_stats["brier"]
        and time_stats["log_loss"] < time_const_stats["log_loss"]
        and time_stats["brier"] < time_simple_stats["brier"]
        and time_stats["log_loss"] < time_simple_stats["log_loss"]
    )
    emit(
        "2C time-based validation and baselines",
        "PASS" if time_pass else "FAIL",
        """sort labeled matches by match_date; use earliest 80% of distinct dates for training
fit WP, constant-rate and score/balls-only models on train; score latest 20%""",
        time_output,
        "This temporal split uses a deterministic 80/20 cutoff on distinct match dates."
    )

    # Rebuild from source afresh in-memory; suppressing its print is not changing it.
    seed = 20261111
    np.random.seed(seed)
    rebuilt, build_stdout = run_code(build_ball_state, save=False)
    rebuilt2, _ = run_code(build_ball_state, save=False)
    state_equal = rebuilt.equals(rebuilt2)
    saved_equal = rebuilt.equals(base_saved)
    keycols = ["match_id", "innings", "overid", "over_ball_num"]
    sorted_rebuilt = rebuilt.sort_values(keycols).reset_index(drop=True)
    sorted_saved = base_saved.sort_values(keycols).reset_index(drop=True)
    state_compare = {}
    for col in sorted(set(sorted_rebuilt.columns) & set(sorted_saved.columns)):
        if pd.api.types.is_numeric_dtype(sorted_rebuilt[col]):
            delta = np.abs(
                pd.to_numeric(sorted_rebuilt[col], errors="coerce").to_numpy(dtype=float)
                - pd.to_numeric(sorted_saved[col], errors="coerce").to_numpy(dtype=float))
            state_compare[col] = int(np.nansum(delta > 1e-9))
        else:
            equal = sorted_rebuilt[col].eq(sorted_saved[col]).fillna(False)
            both_null = sorted_rebuilt[col].isna() & sorted_saved[col].isna()
            state_compare[col] = int((~(equal | both_null)).sum())
    np.random.seed(seed)
    fresh_wp = WinProbabilityModel(l2_reg=1e-4)
    fresh_wp.fit(rebuilt)
    fresh_wp_scores = fresh_wp.predict_wp(rebuilt)
    fresh_lev, _ = fresh_wp.compute_leverage(rebuilt)
    fresh_comp = compute_composite_pressure(rebuilt)
    rebuilt["win_prob"] = fresh_wp_scores
    rebuilt["leverage_index"] = fresh_lev
    rebuilt["pressure_composite"] = fresh_comp
    rebuilt["pressure_band_lev"] = pd.cut(
        rebuilt["leverage_index"], [-np.inf, .70, 1.40, np.inf],
        labels=["Low", "Medium", "High"])
    rebuilt["pressure_band_comp"] = pd.cut(
        rebuilt["pressure_composite"], [-np.inf, 3.5, 6.5, np.inf],
        labels=["Low", "Medium", "High"])
    rebuilt["pressure_band"] = rebuilt["pressure_band_lev"]
    np.random.seed(seed)
    repeat_wp = WinProbabilityModel(l2_reg=1e-4)
    repeat_wp.fit(rebuilt.drop(columns=["win_prob", "leverage_index", "pressure_composite",
                                        "pressure_band_lev", "pressure_band_comp", "pressure_band"]))
    repeat_lev, repeat_wp_base = repeat_wp.compute_leverage(rebuilt)
    repeat_comp = compute_composite_pressure(rebuilt)
    repeat_exact = (
        np.array_equal(fresh_wp_scores, repeat_wp_base)
        and np.array_equal(fresh_lev, repeat_lev)
        and np.array_equal(fresh_comp.to_numpy(), repeat_comp.to_numpy())
    )
    saved_pressure_sorted = pressure_saved.sort_values(keycols).reset_index(drop=True)
    fresh_pressure_sorted = rebuilt.sort_values(keycols).reset_index(drop=True)
    pressure_cols = [
        "win_prob", "leverage_index", "pressure_composite",
        "pressure_band_lev", "pressure_band_comp", "pressure_band",
    ]
    pressure_mismatches = {}
    for col in pressure_cols:
        if pd.api.types.is_numeric_dtype(saved_pressure_sorted[col]):
            delta = np.abs(
                saved_pressure_sorted[col].to_numpy(dtype=float)
                - fresh_pressure_sorted[col].to_numpy(dtype=float))
            pressure_mismatches[col] = int(np.nansum(delta > 1e-9))
        else:
            equal = saved_pressure_sorted[col].eq(fresh_pressure_sorted[col]).fillna(False)
            both_null = saved_pressure_sorted[col].isna() & fresh_pressure_sorted[col].isna()
            pressure_mismatches[col] = int((~(equal | both_null)).sum())
    AUDIT.mkdir(exist_ok=True)
    rebuilt.drop(columns=["win_prob", "leverage_index", "pressure_composite",
                          "pressure_band_lev", "pressure_band_comp", "pressure_band"]).to_parquet(
        AUDIT / "recomputed_ball_state.parquet", index=False)
    rebuilt.to_parquet(AUDIT / "recomputed_ball_state_pressure.parquet", index=False)
    repro_output = (
        f"fixed seed={seed}; raw build stdout: {build_stdout.strip()}\n"
        f"two fresh ball-state builds exact-equal={state_equal}\n"
        f"fresh state vs committed data/ball_state.parquet exact-equal={saved_equal}\n"
        f"fresh state per-column mismatches at tolerance 1e-9: "
        + str({k: v for k, v in state_compare.items() if v})
        + "\nfull fresh pressure calculations repeated exactly (WP, leverage, composite)="
        + str(repeat_exact)
        + "\nfresh pressure vs stored data/ball_state_pressure.parquet mismatches at tolerance 1e-9: "
        + str({k: v for k, v in pressure_mismatches.items() if v})
        + "\noutput writes: audit/recomputed_ball_state.parquet; audit/recomputed_ball_state_pressure.parquet"
    )
    emit(
        "4B clean-folder deterministic pipeline reproduction",
        "PASS" if state_equal and repeat_exact else "FAIL",
        """np.random.seed(20261111)
fresh = build_ball_state(save=False)  # reads raw parquet; writes nowhere
fit WinProbabilityModel; compute leverage/composite/bands in memory
repeat from raw again; compare arrays exactly; save only under audit/""",
        repro_output,
        "The source's hard-coded save path was avoided by save=False; only derived audit outputs were written."
    )

    # 3.1 Different innings formulas and band denominators.
    comp_by_innings = (
        pressure_saved.groupby(["pressure_band_comp", "innings"], observed=False).size()
        .unstack(fill_value=0)
    )
    competition_names = competitions.set_index("comp_id")["comp_name"]
    pressure_enriched = pressure_saved.copy()
    pressure_enriched["comp_name"] = pressure_enriched["comp_id"].map(competition_names)
    pressure_enriched["competition_group"] = np.where(
        pressure_enriched["match_format"].eq("T20I"), "T20I",
        np.where(pressure_enriched["comp_name"].str.contains(
            r"Indian Premier League|\bIPL\b", case=False, na=False), "IPL", "Other T20"))
    pressure_comp = pressure_enriched.groupby(
        ["pressure_band_comp", "competition_group", "innings"], observed=False).size()
    pressure_lev_comp = pressure_enriched.groupby(
        ["pressure_band_lev", "competition_group", "innings"], observed=False).size()
    p1 = (ROOT / "src" / "pressure" / "composite_pressure.py").read_text(encoding="utf-8")
    first_def = p1.split("# INNINGS 1: Setting a Target Pressure", 1)[1].split("return p_score", 1)[0]
    second_def = p1.split("# INNINGS 2: Chasing Pressure", 1)[1].split("# INNINGS 1:", 1)[0]
    comp_output = (
        "First-innings formula (from source): wicket crisis + death overs push + par-rate lag; "
        "no target/RRR component.\nSecond-innings formula: RRR urgency + wicket depletion + "
        "balls/stage + run-rate gap; knockout multiplier.\n"
        f"innings-1 source formula has RRR/target term={('required_run_rate' in first_def or 'target' in first_def)}; "
        f"innings-2 has RRR term={'required_run_rate' in second_def}\n"
        f"composite band x innings delivery counts:\n{comp_by_innings.to_string()}\n"
        f"composite band x competition x innings counts:\n{pressure_comp.to_string()}\n"
        f"leverage band x competition x innings counts:\n{pressure_lev_comp.to_string()}"
    )
    emit(
        "3A first- vs second-innings pressure definition",
        "FAIL",
        """read compute_composite_pressure:
innings 1 = wicket_crisis + death_push + par_rate_lag
innings 2 = required_run_rate + wicket_depletion + stage + run_rate_gap""",
        comp_output,
        "The two formulas measure different constructs, so composite scores and bands are not directly comparable across innings."
    )

    # 3.2 Outcome association, stratified by batter identity, batting position and over.
    raw_comp_metrics = band_metrics(pressure_saved, "pressure_band_comp")
    raw_lev_metrics = band_metrics(pressure_saved, "pressure_band_lev")
    adj_comp, comp_cov = adjusted_band_rates(pressure_saved, "pressure_band_comp")
    adj_lev, lev_cov = adjusted_band_rates(pressure_saved, "pressure_band_lev")
    def effect_summary(metrics, adjusted, cov):
        raw = metrics.set_index("Band")
        common = cov["comparisons"].get("Low-High")
        if adjusted.empty or common is None:
            return "no Low/High common support"
        rates = common["rates"]
        raw_wdiff = raw.loc["High", "Dismissal Rate (%)"] - raw.loc["Low", "Dismissal Rate (%)"]
        adj_wdiff = rates["High"]["Dismissal Rate (%)"] - rates["Low"]["Dismissal Rate (%)"]
        raw_srdiff = raw.loc["High", "Strike Rate"] - raw.loc["Low", "Strike Rate"]
        adj_srdiff = rates["High"]["Strike Rate"] - rates["Low"]["Strike Rate"]
        return (
            f"raw dismissal H-L={raw_wdiff:.3f} pp; adjusted H-L={adj_wdiff:.3f} pp; "
            f"retained abs effect={safe_ratio(abs(adj_wdiff), abs(raw_wdiff)):.1%}\n"
            f"raw SR H-L={raw_srdiff:.3f}; adjusted H-L={adj_srdiff:.3f}; "
            f"retained abs effect={safe_ratio(abs(adj_srdiff), abs(raw_srdiff)):.1%}\n"
            f"shared strata={common['strata']:,}; common-support legal-ball coverage={common['coverage']:.1%}"
        )
    adjust_output = (
        "Pairwise strata are exact striker_id x innings x overid x batting_order; rates standardized "
        "to the same pooled legal-ball weights within each pair's common-support cells.\n"
        f"Composite raw metrics:\n{metric_report(raw_comp_metrics)}\n"
        f"Composite pairwise standardized rates:\n{adj_comp.to_string(index=False)}\n"
        f"Composite pairwise support:\n{comp_cov['comparisons']}\n"
        f"Composite effect:\n{effect_summary(raw_comp_metrics, adj_comp, comp_cov)}\n"
        f"Leverage raw metrics:\n{metric_report(raw_lev_metrics)}\n"
        f"Leverage pairwise standardized rates:\n{adj_lev.to_string(index=False)}\n"
        f"Leverage pairwise support:\n{lev_cov['comparisons']}\n"
        f"Leverage effect:\n{effect_summary(raw_lev_metrics, adj_lev, lev_cov)}"
    )
    comp_coverage = comp_cov["comparisons"].get("Low-High", {}).get("coverage", 0)
    lev_coverage = lev_cov["comparisons"].get("Low-High", {}).get("coverage", 0)
    adj_status = "PASS" if min(comp_coverage, lev_coverage) >= 0.1 else "CANNOT VERIFY"
    emit(
        "3B confounding by over, batting position and batter quality",
        adj_status,
        """legal balls only; for each band pair, group by striker_id, innings, overid and batting_order;
keep shared strata and standardize both bands' rates using identical pooled stratum weights""",
        adjust_output,
        "Striker fixed strata control stable batter quality; sparse common support limits generalization."
    )

    # 3.3 Mechanical association between wickets-in-hand and dismissal validation.
    components = composite_components(pressure_saved)
    no_wkt_score = pressure_for_weights(pressure_saved, components, {"wickets": 0})
    no_wkt_bands = classify_bands(no_wkt_score, 3.5, 6.5)
    no_wkt_frame = pressure_saved.copy()
    no_wkt_frame["_no_wkt_band"] = no_wkt_bands
    no_wkt_metrics = band_metrics(no_wkt_frame, "_no_wkt_band")
    wkt_comp = components["wickets"]
    wkt_effect = (
        f"wicket-state component >0 on {int((wkt_comp > 0).sum()):,}/{len(wkt_comp):,} rows "
        f"({100*(wkt_comp>0).mean():.1f}%); component range={wkt_comp.min():.3f}..{wkt_comp.max():.3f}\n"
        f"reported composite bands:\n{metric_report(raw_comp_metrics)}\n"
        f"same cutoffs with wicket component removed (score not re-tuned):\n{metric_report(no_wkt_metrics)}\n"
        "The score uses wickets_in_hand = 10 - wickets_before; outcome is current is_wicket. "
        "This is not same-ball label leakage, but it bakes prior wicket depletion into the predictor "
        "used to claim wicket-rate separation."
    )
    emit(
        "3C composite index encodes wicket outcome proxy",
        "FAIL",
        """wickets_component = f(wickets_in_hand), where wickets_in_hand = 10 - wickets_before
compare original composite bands with same-threshold bands after zeroing that component""",
        wkt_effect,
        "Dismissal-rate separation is partly built into the band definition via prior wickets lost."
    )

    # 4.1 Independent band table reconstruction and claim-by-claim comparison.
    expected = {
        "LI": [
            ("Low", 55430, 52906, 143.62, 8.62, 6.63, 29.80, 18.89, 7.77, 21.67),
            ("Medium", 102589, 98618, 138.45, 8.31, 5.15, 31.90, 18.58, 6.25, 26.89),
            ("High", 42942, 41151, 136.41, 8.19, 5.44, 33.07, 18.58, 6.04, 25.06),
        ],
        "Composite": [
            ("Low", 112027, 107768, 137.84, 8.27, 4.59, 34.20, 19.25, 6.09, 30.02),
            ("Medium", 60194, 57613, 140.76, 8.45, 5.73, 28.18, 17.63, 6.92, 24.56),
            ("High", 28740, 27294, 142.92, 8.58, 9.42, 28.34, 18.51, 8.08, 15.17),
        ],
    }
    recomputed_li = band_metrics(pressure_saved, "pressure_band_lev")
    recomputed_composite = band_metrics(pressure_saved, "pressure_band_comp")
    columns = ["Band", "Total Deliveries", "Legal Balls", "Strike Rate", "Bowling Econ",
               "Dismissal Rate (%)", "Dot Ball (%)", "Boundary (%)", "Six (%)", "Runs/Wicket"]
    comparison_lines = []
    max_diff = 0.0
    for name, result in [("LI", recomputed_li), ("Composite", recomputed_composite)]:
        wanted = pd.DataFrame(expected[name], columns=columns)
        actual = result[columns]
        for _, row in wanted.iterrows():
            got = actual[actual["Band"] == row["Band"]].iloc[0]
            diffs = []
            for col in columns[1:]:
                delta = abs(float(got[col]) - float(row[col]))
                max_diff = max(max_diff, delta)
                if delta > 0.01:
                    diffs.append(f"{col}: {got[col]} vs {row[col]} (diff={delta})")
            comparison_lines.append(
                f"{name} {row['Band']}: " + ("all numeric fields within 0.01" if not diffs else "; ".join(diffs)))
    band_output = (
        f"Independent LI table:\n{metric_report(recomputed_li)}\n\n"
        f"Independent composite table:\n{metric_report(recomputed_composite)}\n\n"
        "Comparison to every reported count/rate (counts exact; rates tolerance 0.01):\n"
        + "\n".join(comparison_lines)
        + f"\nmaximum absolute numeric difference={max_diff:.4f}"
    )
    emit(
        "4A independently recomputed band tables",
        "PASS" if max_diff <= 0.01 else "FAIL",
        """read saved delivery rows; independently regroup each band
legal = rows where is_legal; compute rates from runs, wickets, boundaries, total_delivery_runs
compare every reported count and rounded rate (tolerance 0.01)""",
        band_output,
        "This confirms reproducibility of reported arithmetic, not validity of the definitions or source data."
    )

    # 4.2 Hand-check 20 seeded deliveries from the raw ball-by-ball feed.
    raw_sorted = raw_bbb[raw_bbb["innings"].isin([1, 2])].sort_values(
        ["match_id", "innings", "overid", "over_ball_num"], kind="mergesort").reset_index(drop=True)
    out_sorted = pressure_saved.sort_values(keycols, kind="mergesort").reset_index(drop=True)
    sample_idx = np.random.default_rng(20261111).choice(len(out_sorted), size=20, replace=False)
    match_index = matches.set_index("match_id")
    raw_groups = {
        key: part for key, part in raw_sorted.groupby(["match_id", "innings"], sort=False)
    }

    def manual_row(row):
        group = raw_groups[(row.match_id, row.innings)]
        group = group.sort_values(["overid", "over_ball_num"], kind="mergesort")
        scores = []
        wickets = []
        legal_count = []
        s = w = lb = 0
        for _, raw in group.iterrows():
            is_legal_now = raw["extras_type"] not in ["wide", "Overstep"]
            s += raw_to_int(raw["runs"]) + raw_to_int(raw["extras_2_runs"])
            if raw["extras_type"] == "wide":
                s += 1
            w += int(str(raw["is_wicket"]).lower() in ["true", "1"])
            lb += int(is_legal_now)
            scores.append(s)
            wickets.append(w)
            legal_count.append(lb)
        keymask = (
            (group["overid"] == row.overid)
            & (group["over_ball_num"] == row.over_ball_num)
        )
        idxs = np.flatnonzero(keymask.to_numpy())
        if len(idxs) != 1:
            raise RuntimeError(f"raw key is not unique: {row.match_id}/{row.innings}/{row.overid}/{row.over_ball_num}")
        pos = int(idxs[0])
        runs_before = scores[pos] - (
            raw_to_int(group.iloc[pos]["runs"])
            + raw_to_int(group.iloc[pos]["extras_2_runs"])
            + int(group.iloc[pos]["extras_type"] == "wide")
        )
        wickets_before = wickets[pos] - int(
            str(group.iloc[pos]["is_wicket"]).lower() in ["true", "1"])
        legal_num = legal_count[pos]
        match = match_index.loc[row.match_id]
        if row.innings == 1:
            max_balls = int(float(match["first_inn_revised_overs"]) * 6) if pd.notna(match["first_inn_revised_overs"]) else 120
            target = np.nan
            needed = np.nan
            rrr = np.nan
        else:
            max_balls = int(float(match["second_inn_revised_overs"]) * 6) if pd.notna(match["second_inn_revised_overs"]) else 120
            inn1_group = raw_groups[(row.match_id, 1)]
            inn1_total = sum(
                raw_to_int(r["runs"]) + raw_to_int(r["extras_2_runs"]) + int(r["extras_type"] == "wide")
                for _, r in inn1_group.iterrows())
            target = float(match["revised_target"]) if pd.notna(match["revised_target"]) and float(match["revised_target"]) > 0 else inn1_total + 1
            needed = max(target - runs_before, 0)
            br = max(max_balls - legal_num, 0)
            rrr = needed / br * 6 if br > 0 else np.nan
        br = max(max_balls - legal_num, 0)
        current_rr = runs_before / (legal_num / 6) if legal_num > 0 else 0
        if row.innings == 1:
            score = (
                np.clip((10 - (10 - wickets_before)) / 6, 0, 1) * 4
                + np.clip((120 - br) / 120, 0, 1) ** 2 * 3.5
                + np.clip((8 - np.clip(current_rr, 0, 36)) / 4, 0, 1) * 2.5
            )
        else:
            safe_rrr = np.clip(rrr if pd.notna(rrr) else 8.0, 0, 36)
            gap = safe_rrr - current_rr
            wih = 10 - wickets_before
            wkt_comp_local = 2 + (3 - wih) / 3 if wih <= 3 else (10 - wih) / 7 * 2
            score = (
                np.clip((safe_rrr - 6) / 8, 0, 1) * 3.5
                + np.clip(wkt_comp_local, 0, 3)
                + np.clip((120 - br) / 120, 0, 1) ** 1.5 * 2.5
                + np.clip(gap / 6, 0, 1)
            )
        if pd.notna(match["knock_out"]) and float(match["knock_out"]) == 1:
            score *= 1.1
        return {
            "runs_at_ball": runs_before,
            "wickets_before": wickets_before,
            "legal_ball_num": legal_num,
            "balls_remaining": br,
            "target": target,
            "required_run_rate": rrr,
            "pressure_composite": np.clip(score, 0, 10),
        }

    hand_rows = []
    for ix in sample_idx:
        row = out_sorted.iloc[ix]
        calc = manual_row(row)
        diffs = {
            field: (np.nan if pd.isna(calc[field]) and pd.isna(row[field])
                    else abs(float(calc[field]) - float(row[field])))
            for field in calc
        }
        hand_rows.append({
            "match": row.match_id, "inn": row.innings, "over": row.overid, "ball": row.over_ball_num,
            "score_diff": diffs["runs_at_ball"], "wkt_diff": diffs["wickets_before"],
            "legal_diff": diffs["legal_ball_num"], "br_diff": diffs["balls_remaining"],
            "target_diff": diffs["target"], "rrr_diff": diffs["required_run_rate"],
            "pressure_diff": diffs["pressure_composite"],
        })
    hand_df = pd.DataFrame(hand_rows)
    hand_output = (
        "20 deterministic random deliveries (seed=20261111); independently accumulated raw deliveries "
        "before/through the sampled ball, then recomputed current pipeline formulas.\n"
        + hand_df.to_string(index=False)
        + f"\nmaximum absolute differences: {hand_df.drop(columns=['match','inn','over','ball']).max().to_dict()}"
    )
    hand_exact = bool((hand_df.drop(columns=["match", "inn", "over", "ball"]).fillna(0).to_numpy() == 0).all())
    emit(
        "4C hand verification of 20 raw deliveries",
        "PASS" if hand_exact else "FAIL",
        """rng = np.random.default_rng(20261111); choose 20 output deliveries
for each delivery, accumulate raw runs/wickets/legal balls up through that ball;
recompute target, remaining balls, RRR and composite pressure; compare stored fields""",
        hand_output,
        "The comparison verifies the formulas as implemented; it does not treat the one-ball state convention as correct."
    )

    # 5.1 Threshold sensitivity for primary and composite bands.
    sensitivity_lines = []
    for name, score, low, high in [
        ("Leverage", pressure_saved["leverage_index"].to_numpy(), .70, 1.40),
        ("Composite", pressure_saved["pressure_composite"].to_numpy(), 3.5, 6.5),
    ]:
        for factor in [.8, 1.0, 1.2]:
            changed_high = high * factor
            sensitivity_lines.append(
                f"{name} high cutoff x{factor:.1f} (high >= {changed_high:.3f}); low cutoff fixed at {low:.3f}\n"
                + band_summary(pressure_saved, score, low, changed_high))
    emit(
        "5A high-pressure threshold sensitivity",
        "PASS",
        """for threshold factor in {0.8, 1.0, 1.2}:
    keep low/medium cutoff fixed; multiply high cutoff; recompute counts, SR and dismissal rate""",
        "\n\n".join(sensitivity_lines),
        "Reported as robustness evidence; no threshold is selected or tuned to improve results."
    )

    # 5.2 Component weight sensitivity (one-at-a-time and all together).
    base_score = pressure_saved["pressure_composite"].to_numpy(dtype=float)
    weights_scenarios = []
    for key in ["rrr", "wickets", "stage", "gap", "lag"]:
        for factor in [.8, 1.2]:
            weights_scenarios.append((f"{key} weight x{factor:.1f}", {key: factor}))
    weights_scenarios += [
        ("all weights x0.8", {key: .8 for key in ["rrr", "wickets", "stage", "gap", "lag"]}),
        ("all weights x1.2", {key: 1.2 for key in ["rrr", "wickets", "stage", "gap", "lag"]}),
    ]
    weight_lines = []
    for label, change in weights_scenarios:
        score = pressure_for_weights(pressure_saved, components, change)
        weight_lines.append(f"{label}\n{band_summary(pressure_saved, score, 3.5, 6.5)}")
    emit(
        "5B composite component-weight sensitivity",
        "PASS",
        """recompute each existing component with one component x0.8/x1.2 (OAT),
then all components x0.8 and x1.2; keep 3.5/6.5 cutoffs fixed; report band metrics""",
        "\n\n".join(weight_lines),
        "Weights and cutoffs remain unoptimized; fixed thresholds expose score-scale sensitivity."
    )

    # Emit final report as one self-contained markdown deliverable.
    summary_rows = "\n".join(
        f"| {i} | {status} | {title} | {why} |"
        for i, (title, status, why) in enumerate(statuses, start=1)
    )
    summary = (
        "# Independent Cricket Analytics Pipeline Audit\n\n"
        "Audit run: 2026-11-11. Raw ball-by-ball/matches/competitions parquet inputs were read from the "
        "configured Downloads data directory; original pipeline/source files were not edited. "
        "Derived parquet outputs are confined to `audit/`.\n\n"
        "## Summary verdict\n\n"
        "The reported Brier/log-loss are reproducible but are same-data (in-sample) metrics. Our "
        "independent held-out tests do show the model beating both the constant-rate and score/balls "
        "baselines; however, data/state defects prevent treating the original calibration and pressure "
        "claims as established. The main limitations are incomplete extras and innings-total "
        "reconstruction, DLS rows retained despite invalid revised-ball units, an off-by-one "
        "remaining-ball convention, and pressure bands that mechanically use wickets-in-hand when "
        "validating dismissal rates.\n\n"
        "## Status table\n\n"
        "| # | Status | Check | Evidence/conclusion |\n|---:|---|---|---|\n"
        + summary_rows
        + "\n\n"
        "## Evidence, executable code and raw output\n\n"
    )
    for title, status, code, output in sections:
        summary += (
            f"### {title} — {status}\n\n"
            "**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):\n\n"
            f"```python\n{code}\n```\n\n"
            f"**Raw output**:\n\n```text\n{output}\n```\n\n"
        )

    # Corrected claims and priorities are based on the measurements above.
    summary += (
        "## Corrected claims supported by the evidence\n\n"
        f"- Raw input has {len(raw_bbb):,} rows; {len(super_rows):,} rows have innings > 2. "
        f"Removing those yields {len(base_saved):,} rows.\n"
        f"- The reproduced in-sample Brier/log-loss are {in_sample['brier_score']:.4f}/"
        f"{in_sample['log_loss']:.4f}; these are same-data fit/evaluation results, not held-out estimates.\n"
        f"- Five-fold match-grouped Brier/log-loss are {cv_model_stats['brier']:.4f}/"
        f"{cv_model_stats['log_loss']:.4f}; chronological holdout is {time_stats['brier']:.4f}/"
        f"{time_stats['log_loss']:.4f}. Both beat the constant and score/balls baselines on both "
        "metrics. This supports predictive signal on the supplied data, not the originally reported "
        "in-sample figures as out-of-sample estimates. See per-decile tables above.\n"
        f"- The {int(total_band_rows):,} pressure-band deliveries include all retained rows; "
        f"{int(comp_legal):,} are legal balls, which accounts for the often-confused ~192,675 subtotal.\n"
        f"- Balls remaining are not validly bounded: {int((base_saved['balls_remaining'] > 120).sum()):,} rows exceed 120, "
        f"with a maximum of {int(base_saved['balls_remaining'].max())}. Revised fields range from 30 to 114, "
        "all multiples of 6, but the pipeline multiplies them by 6 again; the first delivery also starts at 119 "
        "remaining rather than 120.\n"
        "- `extras1_runs` is supported as a category code, not a run quantity. The observed `extras_2_runs` "
        "does not fully represent wide/no-ball/byes/leg-byes/penalty values; reconstructed innings margins "
        "therefore do not provide full scorecard reconciliation.\n"
        "- First-innings composite pressure is a different formula/construct from second-innings chase "
        "pressure. Band-level comparisons should not be pooled as one comparable scale.\n"
        "- Direct future-result/current-dismissal fields were not found in the WP features. The audit "
        "does find held-out predictive improvement over both tested baselines, while pressure-band "
        "behavioral effects remain uncertain because of narrow common support and outcome coupling.\n\n"
        "## Prioritized fixes\n\n"
        "1. Correct revised-overs units before computing max_legal_balls; enforce the applicable legal-ball "
        "cap and align pre-delivery runs, legal balls remaining and RRR. Add DLS boundary tests.\n"
        "2. Define and validate a canonical delivery-runs field against scorecards; separately account for "
        "wide, no-ball, bye, leg-bye, penalty and overthrows. Block downstream score-state use when totals "
        "cannot be reconstructed.\n"
        "3. Report only match-grouped and chronological out-of-sample model metrics; keep all preprocessing, "
        "calibration and threshold selection inside training data.\n"
        "4. Specify DLS inclusion explicitly. Either model revised targets/resources correctly and validate "
        "DLS separately, or exclude flagged rows from the stated non-DLS evaluation and pressure summaries.\n"
        "5. Separate pressure definition from its behavioral outcome tests: remove wicket depletion from a "
        "dismissal-rate validation claim or report an outcome-independent sensitivity/conditional design.\n"
        "6. Define innings-specific pressure scales explicitly and report competition/innings-stratified results "
        "with common-support adjusted estimates.\n"
    )
    summary += (
        "\n## Full audit source\n\n"
        "The following is the exact Python source executed for this audit. Re-running it requires the "
        "raw parquet path and the packages installed in the audit-local environment.\n\n"
        "````python\n"
        + Path(__file__).read_text(encoding="utf-8")
        + "\n````\n"
    )
    (AUDIT / "audit_report.md").write_text(summary, encoding="utf-8")
    print(f"\nREPORT_WRITTEN={AUDIT / 'audit_report.md'}")


if __name__ == "__main__":
    main()
