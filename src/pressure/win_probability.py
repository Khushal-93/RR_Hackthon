"""
Phase 2: Win Probability & Ball-Level Leverage Index (Remediated)
Implements:
1. In-game Win Probability (WP) model for T20 cricket (Innings 1 & 2).
   Excludes DLS/revised matches from training to prevent corrupted resource inputs.
2. GroupKFold (by match_id) and Chronological out-of-sample evaluation.
3. Ball-level Leverage Index standardized within each innings (percentile & z-score)
   so both innings have balanced representation of High, Medium, and Low pressure.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.model_selection import GroupKFold


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -25.0, 25.0)))


class WinProbabilityModel:
    def __init__(self, l2_reg: float = 1e-4):
        self.l2_reg = l2_reg
        self.w1 = None  # weights for innings 1
        self.w2 = None  # weights for innings 2

    def _extract_features_inn2(self, df: pd.DataFrame) -> np.ndarray:
        rn  = np.clip(df["runs_needed"].fillna(100.0).values, 0.0, 250.0)
        br  = np.clip(df["balls_remaining"].values, 0.0, 120.0)
        w   = np.clip(df["wickets_in_hand"].values, 0.0, 10.0)
        rrr = np.clip(df["required_run_rate"].fillna(8.0).values, 0.0, 36.0)
        crr = np.clip(df["current_run_rate"].fillna(7.0).values, 0.0, 36.0)
        gap = rrr - crr
        rn_per_w = rn / (w + 0.5)
        balls_ratio = (br + 1.0) / 121.0
        is_t20i = (df["match_format"] == "T20I").astype(float).values

        return np.column_stack([
            np.ones(len(df)),
            rn / 100.0,
            br / 100.0,
            w / 10.0,
            rrr / 10.0,
            gap / 10.0,
            rn_per_w / 20.0,
            balls_ratio * (w / 10.0),
            is_t20i
        ])

    def _extract_features_inn1(self, df: pd.DataFrame) -> np.ndarray:
        runs = np.clip(df["runs_at_ball"].values, 0.0, 300.0)
        br   = np.clip(df["balls_remaining"].values, 0.0, 120.0)
        w    = np.clip(df["wickets_in_hand"].values, 0.0, 10.0)
        crr  = np.clip(df["current_run_rate"].fillna(7.5).values, 0.0, 36.0)
        is_t20i = (df["match_format"] == "T20I").astype(float).values
        proj = runs + (br / 6.0) * (6.0 + 0.35 * w)

        return np.column_stack([
            np.ones(len(df)),
            (proj - 165.0) / 30.0,
            runs / 100.0,
            br / 100.0,
            w / 10.0,
            (crr - 8.0) / 4.0,
            is_t20i
        ])

    def fit(self, df: pd.DataFrame):
        # Audit fix: Exclude DLS matches from model training
        valid = df[
            (~df["is_dls"].fillna(False)) &
            df["win_team_id"].notna() &
            (df["win_team_id"] > 0)
        ].copy()
        valid["bat_won"] = (valid["batting_team_id"] == valid["win_team_id"]).astype(float)

        # Fit Innings 2
        df2 = valid[valid["innings"] == 2]
        X2 = self._extract_features_inn2(df2)
        y2 = df2["bat_won"].values
        self.w2 = self._fit_logistic(X2, y2)

        # Fit Innings 1
        df1 = valid[valid["innings"] == 1]
        X1 = self._extract_features_inn1(df1)
        y1 = df1["bat_won"].values
        self.w1 = self._fit_logistic(X1, y1)

    def _fit_logistic(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        def loss_and_grad(w):
            p = sigmoid(X @ w)
            eps = 1e-12
            p = np.clip(p, eps, 1.0 - eps)
            loss = -np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)) + 0.5 * self.l2_reg * np.sum(w[1:]**2)
            grad = (X.T @ (p - y)) / len(y)
            grad[1:] += self.l2_reg * w[1:]
            return loss, grad

        w0 = np.zeros(X.shape[1])
        res = minimize(loss_and_grad, w0, jac=True, method="L-BFGS-B")
        return res.x

    def predict_wp(self, df: pd.DataFrame) -> np.ndarray:
        """Predict Win Probability for batting team at each delivery."""
        wp = np.full(len(df), 0.5)

        # Innings 2
        mask2 = df["innings"] == 2
        if mask2.any():
            X2 = self._extract_features_inn2(df[mask2])
            wp[mask2] = sigmoid(X2 @ self.w2)

        # Innings 1
        mask1 = df["innings"] == 1
        if mask1.any():
            X1 = self._extract_features_inn1(df[mask1])
            wp[mask1] = sigmoid(X1 @ self.w1)

        return wp

    def compute_leverage(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute Ball-level Leverage Index:
        Swing = |WP(after 6 runs, 1 ball) - WP(after wicket, 0 runs, 1 ball)|
        
        Audit Fix Applied:
        Standardize Leverage within each innings so both Innings 1 and Innings 2
        have proportional distribution of High, Medium, and Low pressure balls.
        Returns:
            (leverage_ratio, wp_base, leverage_percentile, leverage_zscore)
        """
        # Base WP
        wp_base = self.predict_wp(df)

        # State after 6 (boundary)
        df_six = df.copy()
        df_six["balls_remaining"] = np.maximum(0, df["balls_remaining"] - 1)
        df_six["legal_ball_num"] = df["legal_ball_num"] + 1
        df_six["runs_at_ball"] = df["runs_at_ball"] + 6
        df_six["runs_needed"] = np.maximum(0, df["runs_needed"] - 6)
        df_six["required_run_rate"] = np.where(
            df_six["balls_remaining"] > 0,
            (df_six["runs_needed"] / df_six["balls_remaining"]) * 6.0,
            0.0
        )
        wp_six = self.predict_wp(df_six)

        # State after Wicket (0 runs)
        df_wkt = df.copy()
        df_wkt["balls_remaining"] = np.maximum(0, df["balls_remaining"] - 1)
        df_wkt["legal_ball_num"] = df["legal_ball_num"] + 1
        df_wkt["wickets_in_hand"] = np.maximum(0, df["wickets_in_hand"] - 1)
        df_wkt["required_run_rate"] = np.where(
            df_wkt["balls_remaining"] > 0,
            (df_wkt["runs_needed"] / df_wkt["balls_remaining"]) * 6.0,
            36.0
        )
        wp_wkt = self.predict_wp(df_wkt)

        # Delivery swing in win probability
        swing = np.abs(wp_six - wp_wkt)

        # Innings-specific standardization
        leverage_ratio = np.zeros(len(df))
        lev_pct = np.zeros(len(df))
        lev_z = np.zeros(len(df))

        for inn in [1, 2]:
            mask = df["innings"].to_numpy() == inn
            if mask.any():
                inn_swing = swing[mask]
                mean_s = np.mean(inn_swing) if np.mean(inn_swing) > 0 else 1.0
                std_s = np.std(inn_swing) if np.std(inn_swing) > 0 else 1.0
                leverage_ratio[mask] = inn_swing / mean_s
                lev_pct[mask] = pd.Series(inn_swing).rank(pct=True).to_numpy()
                lev_z[mask] = (inn_swing - mean_s) / (std_s if std_s > 0 else 1.0)

        return leverage_ratio, wp_base, lev_pct, lev_z

    def evaluate_group_kfold(self, df: pd.DataFrame, n_splits: int = 5) -> Dict:
        """
        Evaluate strictly out-of-sample using GroupKFold grouped by match_id.
        No deliveries from the same match ever appear in both train and test.
        """
        valid = df[
            (~df["is_dls"].fillna(False)) &
            df["win_team_id"].notna() &
            (df["win_team_id"] > 0)
        ].copy().reset_index(drop=True)

        y = (valid["batting_team_id"] == valid["win_team_id"]).astype(float).values
        groups = valid["match_id"].values
        gkf = GroupKFold(n_splits=n_splits)

        cv_preds = np.full(len(valid), np.nan)
        cv_const = np.full(len(valid), np.nan)
        cv_simple = np.full(len(valid), np.nan)

        for train_idx, test_idx in gkf.split(valid, y, groups):
            train_df, test_df = valid.iloc[train_idx], valid.iloc[test_idx]

            # Fit model on training fold
            fold_model = WinProbabilityModel(l2_reg=self.l2_reg)
            fold_model.fit(train_df)
            cv_preds[test_idx] = fold_model.predict_wp(test_df)

            # Baselines
            cv_const[test_idx] = y[train_idx].mean()

            # Score + balls baseline (innings specific)
            cv_simple[test_idx] = self._fit_predict_score_baseline(train_df, test_df)

        return {
            "model": self._compute_metrics(y, cv_preds),
            "constant_baseline": self._compute_metrics(y, cv_const),
            "score_baseline": self._compute_metrics(y, cv_simple),
        }

    def evaluate_chronological(self, df: pd.DataFrame, split_ratio: float = 0.8) -> Dict:
        """
        Evaluate strictly out-of-sample using a temporal 80/20 train/test cutoff on match dates.
        """
        valid = df[
            (~df["is_dls"].fillna(False)) &
            df["win_team_id"].notna() &
            (df["win_team_id"] > 0) &
            df["match_date"].notna()
        ].copy().reset_index(drop=True)

        valid["_date"] = pd.to_datetime(valid["match_date"], errors="coerce", utc=True)
        unique_dates = np.sort(valid["_date"].dropna().unique())
        cutoff_idx = max(1, int(len(unique_dates) * split_ratio))
        cutoff_date = unique_dates[cutoff_idx]

        train_mask = valid["_date"] < cutoff_date
        test_mask = valid["_date"] >= cutoff_date

        train_df, test_df = valid[train_mask], valid[test_mask]
        y_test = (test_df["batting_team_id"] == test_df["win_team_id"]).astype(float).values
        y_train = (train_df["batting_team_id"] == train_df["win_team_id"]).astype(float).values

        # Model
        model = WinProbabilityModel(l2_reg=self.l2_reg)
        model.fit(train_df)
        preds = model.predict_wp(test_df)

        # Baselines
        const_preds = np.full(len(test_df), y_train.mean())
        score_preds = self._fit_predict_score_baseline(train_df, test_df)

        return {
            "cutoff_date": str(cutoff_date),
            "train_matches": train_df["match_id"].nunique(),
            "test_matches": test_df["match_id"].nunique(),
            "model": self._compute_metrics(y_test, preds),
            "constant_baseline": self._compute_metrics(y_test, const_preds),
            "score_baseline": self._compute_metrics(y_test, score_preds),
        }

    def _fit_predict_score_baseline(self, train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        preds = np.full(len(test), np.nan)
        for inn in [1, 2]:
            tr_part = train[train["innings"] == inn]
            te_mask = test["innings"].to_numpy() == inn
            if tr_part.empty or not te_mask.any():
                continue
            y_tr = (tr_part["batting_team_id"] == tr_part["win_team_id"]).astype(float).values
            X_tr = np.column_stack([
                np.ones(len(tr_part)),
                np.clip(tr_part["runs_at_ball"].values, 0, 300) / 300.0,
                np.clip(tr_part["balls_remaining"].values, 0, 120) / 120.0
            ])
            X_te = np.column_stack([
                np.ones(int(te_mask.sum())),
                np.clip(test.loc[te_mask, "runs_at_ball"].values, 0, 300) / 300.0,
                np.clip(test.loc[te_mask, "balls_remaining"].values, 0, 120) / 120.0
            ])

            def obj(w):
                p = sigmoid(X_tr @ w)
                eps = 1e-12
                p = np.clip(p, eps, 1.0 - eps)
                loss = -np.mean(y_tr * np.log(p) + (1.0 - y_tr) * np.log(1.0 - p))
                grad = (X_tr.T @ (p - y_tr)) / len(y_tr)
                return loss, grad

            res = minimize(obj, np.zeros(X_tr.shape[1]), jac=True, method="L-BFGS-B")
            preds[te_mask] = sigmoid(X_te @ res.x)
        return preds

    def _compute_metrics(self, y: np.ndarray, preds: np.ndarray) -> Dict:
        eps = 1e-12
        p_clip = np.clip(preds, eps, 1.0 - eps)
        brier = float(np.mean((preds - y)**2))
        logloss = float(-np.mean(y * np.log(p_clip) + (1.0 - y) * np.log(1.0 - p_clip)))

        df_cal = pd.DataFrame({"pred": preds, "actual": y})
        df_cal["decile"] = pd.qcut(df_cal["pred"], q=10, duplicates="drop")
        cal_table = df_cal.groupby("decile", observed=False).agg(
            mean_pred=("pred", "mean"),
            win_rate=("actual", "mean"),
            count=("actual", "count")
        ).reset_index()

        return {
            "brier_score": brier,
            "log_loss": logloss,
            "calibration_table": cal_table
        }
