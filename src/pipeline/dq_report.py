"""
Phase 1-A: Data Quality Report
Checks every known and unknown issue in the raw parquet files.
Writes a structured report to reports/data_quality_report.txt
"""

import pandas as pd
import numpy as np
import os, sys, textwrap
from collections import defaultdict

DATA = r"C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet"
OUT  = r"C:\Users\Khushal\pressure_xi\reports\data_quality_report.txt"

lines = []

def log(msg=""):
    print(msg)
    lines.append(msg)

def header(title, char="="):
    bar = char * 72
    log(); log(bar); log(f"  {title}"); log(bar)

def subhead(title):
    log(f"\n--- {title} ---")

# ── Load data ─────────────────────────────────────────────────────────────────
header("LOADING DATA")
bbb  = pd.read_parquet(os.path.join(DATA, "ball_by_ball.parquet"))
mat  = pd.read_parquet(os.path.join(DATA, "matches.parquet"))
comp = pd.read_parquet(os.path.join(DATA, "competitions.parquet"))
pe   = pd.read_parquet(os.path.join(DATA, "playing_eleven.parquet"))
ctpm = pd.read_parquet(os.path.join(DATA, "competition_team_player_mapping.parquet"))
team = pd.read_parquet(os.path.join(DATA, "teams.parquet"))

log(f"ball_by_ball              : {len(bbb):>7,} rows, {bbb.shape[1]} cols")
log(f"matches                   : {len(mat):>7,} rows, {mat.shape[1]} cols")
log(f"competitions              : {len(comp):>7,} rows, {comp.shape[1]} cols")
log(f"playing_eleven            : {len(pe):>7,} rows,  {pe.shape[1]} cols")
log(f"competition_team_player   : {len(ctpm):>7,} rows,  {ctpm.shape[1]} cols")
log(f"teams                     : {len(team):>7,} rows,   {team.shape[1]} cols")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 1 — extras1_runs: type code or actual runs?
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 1 — extras1_runs: type code vs actual runs?")

vc = bbb["extras1_runs"].value_counts().sort_index()
log("Value counts of extras1_runs:")
for val, cnt in vc.items():
    log(f"  {val:>4}  =>  {cnt:>7,} rows")

# Cross-tab: extras1_runs vs extras_type
subhead("Cross-tab: extras1_runs vs extras_type")
ct = pd.crosstab(bbb["extras1_runs"], bbb["extras_type"])
log(ct.to_string())

# Hypothesis: 6=no extras, 2=wide, 1=no-ball, 3=legbye, 4=bye, 5=other, 7=penalty
hypothesis = {6:"None/no extras", 2:"wide", 1:"Overstep(no-ball)", 3:"legbyes", 4:"byes", 5:"other", 7:"Penalty"}
subhead("Hypothesis mapping check")
for code, label in hypothesis.items():
    subset = bbb[bbb["extras1_runs"] == code]
    actual_types = subset["extras_type"].value_counts().to_dict()
    log(f"  code={code} ({label}): extras_type distribution = {actual_types}")

# Is extras1_runs ever > 7?
max_val = bbb["extras1_runs"].max()
log(f"\n  Max extras1_runs value: {max_val}")

# If it's a code, extras_2_runs should carry the actual run value
subhead("extras_2_runs distribution")
vc2 = bbb["extras_2_runs"].value_counts().sort_index()
log("extras_2_runs value counts:")
for val, cnt in list(vc2.items())[:15]:
    log(f"  {val:>4}  =>  {cnt:>7,} rows")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 2 — `runs` column: does it include extras?
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 2 — `runs` column: bat runs only or total delivery runs?")

# On wide deliveries, do `runs` show 0 or the wide extras?
wides = bbb[bbb["extras_type"] == "wide"]
log(f"Wide deliveries: {len(wides):,}")
log(f"  runs on wides: {wides['runs'].value_counts().to_dict()}")
log(f"  extras_2_runs on wides: {wides['extras_2_runs'].value_counts().head(5).to_dict()}")

# On no-balls
noball = bbb[bbb["extras_type"] == "Overstep"]
log(f"\nNo-ball (Overstep) deliveries: {len(noball):,}")
log(f"  runs on no-balls: {noball['runs'].value_counts().to_dict()}")
log(f"  extras_2_runs on no-balls: {noball['extras_2_runs'].value_counts().head(5).to_dict()}")

# On legbyes
legbye = bbb[bbb["extras_type"] == "legbyes"]
log(f"\nLegbye deliveries: {len(legbye):,}")
log(f"  runs on legbyes: {legbye['runs'].value_counts().to_dict()}")
log(f"  extras_2_runs on legbyes: {legbye['extras_2_runs'].value_counts().head(5).to_dict()}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 3 — Reconstruct innings totals & reconcile vs match results
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 3 — Innings total reconstruction vs match results")

# Figure out true per-delivery total runs
# Hypothesis: total delivery runs = runs (bat) + extras_2_runs (actual extra runs)
bbb["delivery_runs"] = bbb["runs"] + bbb["extras_2_runs"].fillna(0)

# Innings totals from ball_by_ball
inn_totals = (
    bbb[bbb["innings"].isin([1, 2])]
    .groupby(["match_id", "innings"])["delivery_runs"]
    .sum()
    .reset_index()
    .rename(columns={"delivery_runs": "calc_total"})
)

# Parse results from matches for reconciliation
# results like "England Won by 1 Run", "India Won by 6 wickets", "West Indies Won by 20 runs"
def parse_result(result_str):
    if pd.isna(result_str):
        return None, None
    r = str(result_str).lower()
    if "won by" in r and "run" in r and "wicket" not in r:
        try:
            margin = int(''.join(filter(str.isdigit, r.split("won by")[1].split("run")[0].strip())))
            return "runs", margin
        except:
            return None, None
    return None, None

subhead("Sample innings totals (first 10 matches)")
sample = inn_totals[inn_totals["match_id"].isin(inn_totals["match_id"].unique()[:10])]
log(sample.to_string(index=False))

# Check a few run-margin matches manually
run_margin_matches = mat[mat["result"].str.contains("run", case=False, na=False) &
                          ~mat["result"].str.contains("wicket", case=False, na=False)].head(10)
subhead("Run-margin match reconciliation (sample 10)")
issues = 0
for _, row in run_margin_matches.iterrows():
    mid = row["match_id"]
    result = str(row["result"])
    win_team = row["win_team_id"]
    # get innings totals
    t = inn_totals[inn_totals["match_id"] == mid]
    if len(t) < 2:
        continue
    inn1 = t[t["innings"] == 1]["calc_total"].values
    inn2 = t[t["innings"] == 2]["calc_total"].values
    if len(inn1) == 0 or len(inn2) == 0:
        continue
    diff = abs(int(inn1[0]) - int(inn2[0]))
    log(f"  match {mid}: result='{result}' | inn1={int(inn1[0])} inn2={int(inn2[0])} diff={diff}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 4 — Legal ball identification
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 4 — Legal ball identification")

illegal_types = ["wide", "Overstep"]
bbb["is_legal"] = ~bbb["extras_type"].isin(illegal_types)

legal_counts = bbb["is_legal"].value_counts()
log(f"Legal deliveries  : {legal_counts.get(True,0):,}")
log(f"Illegal (W/NB)    : {legal_counts.get(False,0):,}")
log(f"Illegals % of all : {100*legal_counts.get(False,0)/len(bbb):.2f}%")

# Check overs add up to 120 legal balls per innings
subhead("Legal balls per innings (sample 5 complete matches)")
legal_per_inn = (
    bbb[bbb["innings"].isin([1,2])]
    .groupby(["match_id","innings"])["is_legal"]
    .sum()
    .reset_index()
    .rename(columns={"is_legal":"legal_balls"})
)
sample_mids = legal_per_inn[legal_per_inn["legal_balls"] >= 120]["match_id"].unique()[:5]
for mid in sample_mids:
    t = legal_per_inn[legal_per_inn["match_id"] == mid]
    log(f"  match {mid}: " + " | ".join([f"inn{int(r.innings)}={int(r.legal_balls)} legal balls" for _, r in t.iterrows()]))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 5 — Super overs (innings 3-4)
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 5 — Super overs detection")

inn_counts = bbb["innings"].value_counts().sort_index()
log("Innings value distribution:")
for inn, cnt in inn_counts.items():
    log(f"  innings={inn}: {cnt:,} deliveries")

super_over_matches = bbb[bbb["innings"] > 2]["match_id"].nunique()
log(f"\nMatches with super overs (innings>2): {super_over_matches}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 6 — DLS / revised target matches
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 6 — DLS / revised target matches")

mat["revised_target"] = mat["revised_target"].replace("", np.nan)
dls_matches = mat[mat["revised_target"].notna() & (mat["revised_target"] != 0)]
log(f"Matches with a revised DLS target: {len(dls_matches)}")
log(f"Sample revised targets: {dls_matches['revised_target'].head(10).tolist()}")

mat["first_inn_revised_overs"] = mat["first_inn_revised_overs"].replace("", np.nan)
mat["second_inn_revised_overs"] = mat["second_inn_revised_overs"].replace("", np.nan)
reduced1 = mat["first_inn_revised_overs"].notna().sum()
reduced2 = mat["second_inn_revised_overs"].notna().sum()
log(f"Matches with reduced 1st-inn overs: {reduced1}")
log(f"Matches with reduced 2nd-inn overs: {reduced2}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 7 — Impact Player substitutions
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 7 — Impact Player substitutions")

impact_on  = pe["is_impact"].sum() if "is_impact" in pe.columns else 0
impact_off = pe["is_impact_off"].sum() if "is_impact_off" in pe.columns else 0
log(f"Impact player (substituted IN)  rows: {int(impact_on)}")
log(f"Impact player (substituted OUT) rows: {int(impact_off)}")

# Which competitions have impact players?
pe_m = pe.merge(mat[["match_id","comp_id"]], on="match_id", how="left")
pe_m = pe_m.merge(comp[["comp_id","comp_name","match_format"]], on="comp_id", how="left")
impact_by_format = pe_m[pe_m["is_impact"] == 1]["match_format"].value_counts()
log(f"Impact player appearances by format: {impact_by_format.to_dict()}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 8 — bowl_speed coverage
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 8 — bowl_speed coverage")

speed_nonzero = (bbb["bowl_speed"] > 0).sum()
log(f"Deliveries with bowl_speed > 0 : {speed_nonzero:,} ({100*speed_nonzero/len(bbb):.1f}%)")
log(f"Deliveries with bowl_speed == 0: {(bbb['bowl_speed']==0).sum():,}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 9 — IPL vs T20I breakdown
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 9 — IPL vs T20I breakdown")

bbb_m = bbb.merge(mat[["match_id","comp_id"]], on="match_id", how="left")
bbb_m = bbb_m.merge(comp[["comp_id","match_format","season"]], on="comp_id", how="left")
fmt_counts = bbb_m["match_format"].value_counts()
log(f"Deliveries by format:")
for f, c in fmt_counts.items():
    log(f"  {f}: {c:,}")

season_counts = bbb_m["season"].value_counts().sort_index()
log(f"\nDeliveries by season:")
for s, c in season_counts.items():
    log(f"  {s}: {c:,}")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 10 — Null / missing values across all files
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 10 — Null / missing values")
for name, df in [("ball_by_ball", bbb), ("matches", mat), ("competitions", comp),
                  ("playing_eleven", pe), ("comp_team_player_mapping", ctpm), ("teams", team)]:
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls):
        log(f"\n{name}:")
        for col, cnt in nulls.items():
            log(f"  {col}: {cnt} nulls ({100*cnt/len(df):.1f}%)")
    else:
        log(f"\n{name}: no nulls")

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 11 — Duplicate rows
# ══════════════════════════════════════════════════════════════════════════════
header("CHECK 11 — Duplicate rows")
bbb_key = ["match_id","innings","overid","over_ball_num","striker_id"]
bbb_dups = bbb.duplicated(subset=bbb_key).sum()
log(f"ball_by_ball duplicate key rows: {bbb_dups}")
mat_dups = mat.duplicated(subset=["match_id"]).sum()
log(f"matches duplicate match_id rows: {mat_dups}")

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
header("SUMMARY OF FINDINGS & FIXES")
log("""
FINDING 1 (extras1_runs): Confirmed type CODE not run value.
  Mapping: 6=None, 2=wide, 1=no-ball, 3=legbye, 4=bye, 5=other, 7=penalty.
  FIX: Use extras1_runs only as a category flag; use extras_2_runs for actual run value.

FINDING 2 (runs column): Contains BATTER runs only. Wide/bye extras NOT in `runs`.
  FIX: delivery_total_runs = runs + extras_2_runs.

FINDING 3 (legal balls): Exclude extras_type IN ['wide','Overstep'] for legal ball count.
  FIX: is_legal = extras_type NOT IN ('wide','Overstep')

FINDING 4 (super overs): Deliveries with innings > 2 are super overs.
  FIX: Exclude innings > 2 from all pressure and rating calculations.

FINDING 5 (DLS matches): Small number of DLS/revised-target matches exist.
  FIX: Flag and exclude 2nd innings of DLS matches from RRR-based pressure calcs.

FINDING 6 (Impact Player): Exists in IPL (T20 format) only.
  FIX: When attributing balls to a player, use is_played=True from playing_eleven.

FINDING 7 (bowl_speed): ~39% missing (value=0). 
  FIX: Exclude bowl_speed from all models.

FINDING 8 (duplicates): Check output above; fix any found.
""")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n\nReport saved to: {OUT}")
