# Remediated Pipeline Audit Summary

| Check | Title | Status | Findings |
|:---:|---|:---:|---|
| 1A | extras1_runs is type code, not runs | **PASS** | Verified: 200,999 / 200,999 rows match categorical mapping exactly. Value counts: |
| 1B | Innings totals rebuilt with known extras & unreconciled matches flagged | **PASS** | Run-margin games parsed: 410 |
| 1C | Super overs excluded; DLS matches excluded from model fitting & stored separately | **PASS** | Super-over deliveries in raw data: 38 across 6 matches; in pipeline: 0 |
| 1D | Legal-ball counting & balls remaining bounded in [0, 120] | **PASS** | balls_remaining min=0; max=120; outside [0, 120]=0 |
| 1E | Row count reconciliation: 200,961 total and 192,675 legal balls | **PASS** | Raw deliveries: 200,999 |
| 2A | No future information; in-sample resubstitution metrics removed from reports | **PASS** | No match outcome or future deliveries used in feature extraction. |
| 2B | Out-of-sample GroupKFold by match_id vs. baselines | **PASS** | 5-Fold GroupKFold (Matches = 829): |
| 2C | Chronological 80/20 train/test holdout vs. baselines | **PASS** | Temporal Cutoff: 2025-11-09 (Train Matches: 649, Test Matches: 165) |
| 3A | Within-innings standardized Leverage Index (both innings have high-pressure balls) | **PASS** | Leverage bands distribution across innings: |
| 3B & 3C | Dismissal regression controlling for batter quality, phase & batting order (uncoupled pressure) | **PASS** | Evaluated on 192,675 legal balls across 867 matches (clustered SE by match_id). |
| 3D | Deliveries per band by competition (IPL vs. T20I) and innings | **PASS** | Leverage band x Competition x Innings distribution: |
| 4A | Independent band table recomputation | **PASS** | Independent Leverage Table: |
| 4B | Clean deterministic pipeline rerun | **PASS** | Rebuilt two independent instances from raw data in memory: exact parity = True |
| 4C | Hand verification of 20 deterministic random deliveries | **PASS** | Verified state bounds and formula conformity across 20 deliveries (sample seed=20261111): |
| 5 | Sensitivity analysis (cutoffs varied +/-20%) | **PASS** | Leverage High Percentile Cutoff x0.8 (>= 0.5334): Deliveries=93,777, Legal=90,137, SR=135.28, Dismissal%=4.92% |