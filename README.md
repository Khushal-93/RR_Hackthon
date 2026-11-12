# Pressure XI: T20 Player Performance Ratings Under Pressure

## Problem Statement
Evaluating player performance in Twenty20 (T20) cricket often conflates raw aggregate scoring and economy rates with tactical match context. This project builds an audited, mathematically grounded framework to quantify individual player performance under high match leverage. Using historical ball-by-ball delivery data from T20 leagues and international fixtures, we construct in-game win probability baselines, standardize leverage across innings to identify high-pressure game states, and estimate shrinkage-regularized player run efficiency ratings relative to matched game situations.

## Pressure Definition
Pressure is defined strictly as the **top third** of ball-by-ball Leverage Index standardized within each innings:
- **Innings 1**: Leverage Index standardized across all Innings 1 legal deliveries. High Pressure corresponds to percentile rank $\ge 66.7\%$ ($\text{Leverage} \ge 1.258$). Early foundation volatility dominates: 75.54% of Innings 1 high-pressure balls fall in Overs 1–6 (Powerplay) and 86.99% are faced by batting orders 1–3.
- **Innings 2**: Leverage Index standardized across all Innings 2 legal deliveries. High Pressure corresponds to percentile rank $\ge 66.7\%$ ($\text{Leverage} \ge 1.246$), capturing chasing execution across middle and death overs under escalating Required Run Rate (RRR).

## Scoring Method
Player ratings measure net per-delivery run efficiency relative to matched game states, adjusted for opponent quality and regularized via Empirical Bayes:
- **Batters**: Shrunk opposition-adjusted Runs Above Expected (RAE) per high-pressure ball:
  $$\text{RAE}_{i,t} = \text{runs}_t - \left( E_{-m}[\text{runs} \mid \text{phase}, \text{WIH}, \text{batting\_order}, \text{bowler\_type}] + \frac{\Delta_{\text{bowl\_team}}}{6} \right)$$
- **Bowlers**: Shrunk opposition-adjusted Runs Saved (RSE) per high-pressure ball:
  $$\text{RSE}_{i,t} = \left( E_{-m}[\text{runs} \mid \text{phase}, \text{WIH}, \text{batting\_order}] + \frac{\Delta_{\text{bat\_team}}}{6} \right) - \text{total\_runs}_t$$
State baselines use leave-one-match-out expectations $E_{-m}[\cdot]$ across phase, wickets in hand (WIH), batting order, and bowler style. Opponent attack quality ($\Delta_{\text{team}}$) is shrunk toward the global economy with an $m = 300$ balls prior. Dismissal rate vs. expected is reported as an independent diagnostic column only, as adding binary dismissal outcomes ($k \cdot \text{WAE}$) degrades cross-era repeatability. Empirical Bayes shrinkage scales each player's rate using their true delivery-level sampling variance ($v_i = \sigma_i^2 / N_i$). Eligibility requires $\ge 150$ high-pressure legal balls and $\ge 15$ matches in clean non-DLS data ($N = 118$ eligible batters, $N = 125$ eligible bowlers).

## Data Setup
Raw competition data is not included in this repository. To run the pipeline from scratch:
1. Place raw Parquet files (`matches.parquet`, `competitions.parquet`, `innings.parquet`, etc.) in a local directory (e.g., `data/raw/` or set `RAW_DATA_PATH`).
2. Run data compilation to generate intermediate clean non-DLS state files.

## Running the Pipeline and Tests
To install dependencies and execute the test suite:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the test suite (14 unit and regression tests)
pytest src/tests -v

# Run the final submission and ratings generation
python audit/generate_final_submission.py
```

## Results
The complete player ratings table and confidence intervals are saved in:
- [`outputs/final_rankings.csv`](outputs/final_rankings.csv) (also mirrored at `data/final_rankings.csv`)
- Full methodology report: [`outputs/final_methodology_report.txt`](outputs/final_methodology_report.txt)

### Top-10 Batters Under Pressure
1. **Vaibhav Sooryavanshi**: 331b, Shrunk Rate **+0.3921** runs/b (80% CI: [+0.295, +0.488], $\lambda = 0.520$)
2. **Priyansh Arya**: 316b, Shrunk Rate **+0.2531** runs/b (80% CI: [+0.162, +0.339], $\lambda = 0.576$)
3. **Abhishek Sharma**: 1084b, Shrunk Rate **+0.2420** runs/b (80% CI: [+0.168, +0.304], $\lambda = 0.831$)
4. **Tim David**: 279b, Shrunk Rate **+0.1898** runs/b (80% CI: [+0.072, +0.303], $\lambda = 0.542$)
5. **Phil Salt**: 716b, Shrunk Rate **+0.1731** runs/b (80% CI: [+0.098, +0.247], $\lambda = 0.781$)
6. **Travis Head**: 586b, Shrunk Rate **+0.1650** runs/b (80% CI: [+0.069, +0.261], $\lambda = 0.728$)
7. **Josh Inglis**: 342b, Shrunk Rate **+0.1539** runs/b (80% CI: [+0.053, +0.250], $\lambda = 0.611$)
8. **Finn Allen**: 364b, Shrunk Rate **+0.1490** runs/b (80% CI: [+0.070, +0.234], $\lambda = 0.605$)
9. **Heinrich Klaasen**: 229b, Shrunk Rate **+0.1454** runs/b (80% CI: [+0.061, +0.222], $\lambda = 0.524$)
10. **Harry Brook**: 239b, Shrunk Rate **+0.1407** runs/b (80% CI: [+0.065, +0.225], $\lambda = 0.576$)

### Top-10 Bowlers Under Pressure
1. **Krunal Pandya**: 468b, Shrunk Rate **+0.2707** runs saved/b (80% CI: [+0.193, +0.342], $\lambda = 0.723$)
2. **Sunil Narine**: 472b, Shrunk Rate **+0.2365** runs saved/b (80% CI: [+0.163, +0.304], $\lambda = 0.690$)
3. **Rashid Khan**: 680b, Shrunk Rate **+0.2354** runs saved/b (80% CI: [+0.172, +0.294], $\lambda = 0.794$)
4. **Sufiyan Muqeem**: 171b, Shrunk Rate **+0.2236** runs saved/b (80% CI: [+0.152, +0.287], $\lambda = 0.503$)
5. **Adil Rashid**: 264b, Shrunk Rate **+0.2029** runs saved/b (80% CI: [+0.111, +0.293], $\lambda = 0.611$)
6. **Jason Behrendorff**: 182b, Shrunk Rate **+0.1916** runs saved/b (80% CI: [+0.126, +0.255], $\lambda = 0.453$)
7. **Mohammed Shami**: 507b, Shrunk Rate **+0.1859** runs saved/b (80% CI: [+0.120, +0.245], $\lambda = 0.665$)
8. **Gudakesh Motie**: 219b, Shrunk Rate **+0.1772** runs saved/b (80% CI: [+0.112, +0.244], $\lambda = 0.512$)
9. **Bhuvneshwar Kumar**: 910b, Shrunk Rate **+0.1716** runs saved/b (80% CI: [+0.106, +0.232], $\lambda = 0.777$)
10. **Matheesha Pathirana**: 191b, Shrunk Rate **+0.1659** runs saved/b (80% CI: [+0.108, +0.219], $\lambda = 0.504$)

## Limitations
1. **Weak Out-of-Time Repeatability**: When fitted strictly on 2022–2024 and evaluated out-of-time on raw 2025–2026 data ($\ge 150$ train balls, $\ge 60$ test balls), cross-era rank correlation is modest:
   - Batters ($N = 51$): Spearman $\rho = +0.2501$ ($95\%$ CI $[-0.0711, +0.4985]$), which spans zero and is not statistically distinguishable from random variation.
   - Bowlers ($N = 63$): Spearman $\rho = +0.2861$ ($95\%$ CI $[+0.0105, +0.5017]$).
2. **Bowler List Leans Toward Middle-Over Spin**: 6 of the top 10 bowlers are spinners (60.0% vs. 33.6% in the eligible pool), and 5 of them bowl 63.5% to 91.8% of their high-pressure deliveries in Middle overs (overs 7–15). Middle overs provide structurally different run-suppression dynamics against consolidating batters compared to powerplay and death pace corridors.
3. **Scorecard Reconstruction & DLS Exclusions**: Matches with RRR reconstruction errors within $\pm 10$ runs were retained and flagged approximate. 100% of rain-shortened and DLS-affected matches (41 matches, 5,254 deliveries) and super-overs were strictly excluded from baselines and ratings to prevent distorted resource tables.
4. **Fragility Near Eligibility Floor (150–220 Balls)**: In leave-top-2-matches-out robustness tests, bowler ranks near the floor drop substantially (Behrendorff drops to #28, Pathirana to #32, Motie to #30), while Muqeem (#9) and batters Tim David (#10–#13) and Heinrich Klaasen (#14–#17) remain stable.
5. **Descriptive, Not Predictive**: All results represent descriptive historical rate efficiency within specific situational corridors. They do not quantify individual psychology, "clutch" temperament, or causal bravery under pressure.
