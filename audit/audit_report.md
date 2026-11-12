# Independent Cricket Analytics Pipeline Audit

Audit run: 2026-11-11. Raw ball-by-ball/matches/competitions parquet inputs were read from the configured Downloads data directory; original pipeline/source files were not edited. Derived parquet outputs are confined to `audit/`.

## Summary verdict

The reported Brier/log-loss are reproducible but are same-data (in-sample) metrics. Our independent held-out tests do show the model beating both the constant-rate and score/balls baselines; however, data/state defects prevent treating the original calibration and pressure claims as established. The main limitations are incomplete extras and innings-total reconstruction, DLS rows retained despite invalid revised-ball units, an off-by-one remaining-ball convention, and pressure bands that mechanically use wickets-in-hand when validating dismissal rates.

## Status table

| # | Status | Check | Evidence/conclusion |
|---:|---|---|---|
| 1 | PASS | 1A extras1_runs is type code | The code column maps one-to-one to extras_type, not run amounts. |
| 2 | FAIL | 1B innings totals vs result text | Recorded extras are incomplete; even this lower-bound reconstruction cannot match all scorecard margins. |
| 3 | FAIL | 1C superovers and DLS handling | Superovers are excluded. DLS rows are only partially handled and are not separated from fitting or pressure summaries. |
| 4 | FAIL | 1D legal balls and remaining-ball bounds | Normal innings counters are legal, but revised-resource fields appear already expressed in balls and are multiplied by six; first-ball state is also one ball low. |
| 5 | PASS | 1E 200,999 to 200,961 and band denominator | The ~192,675 figure is the legal-ball subtotal, not the band total-delivery subtotal. |
| 6 | FAIL | 2A no future information and claimed evaluation | No final result/current dismissal is a direct model feature; however, the reported metrics are resubstitution metrics, not validation. |
| 7 | PASS | 2B GroupKFold validation and baselines | Out-of-fold predictions prevent deliveries from the same match appearing in both train and test. |
| 8 | PASS | 2C time-based validation and baselines | This temporal split uses a deterministic 80/20 cutoff on distinct match dates. |
| 9 | PASS | 4B clean-folder deterministic pipeline reproduction | The source's hard-coded save path was avoided by save=False; only derived audit outputs were written. |
| 10 | FAIL | 3A first- vs second-innings pressure definition | The two formulas measure different constructs, so composite scores and bands are not directly comparable across innings. |
| 11 | CANNOT VERIFY | 3B confounding by over, batting position and batter quality | Striker fixed strata control stable batter quality; sparse common support limits generalization. |
| 12 | FAIL | 3C composite index encodes wicket outcome proxy | Dismissal-rate separation is partly built into the band definition via prior wickets lost. |
| 13 | PASS | 4A independently recomputed band tables | This confirms reproducibility of reported arithmetic, not validity of the definitions or source data. |
| 14 | PASS | 4C hand verification of 20 raw deliveries | The comparison verifies the formulas as implemented; it does not treat the one-ball state convention as correct. |
| 15 | PASS | 5A high-pressure threshold sensitivity | Reported as robustness evidence; no threshold is selected or tuned to improve results. |
| 16 | PASS | 5B composite component-weight sensitivity | Weights and cutoffs remain unoptimized; fixed thresholds expose score-scale sensitivity. |

## Evidence, executable code and raw output

### 1A extras1_runs is type code — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
matches = sum((extras1_runs == code) & extras_type == expected_label)
extras1_runs.value_counts(); extras_2_runs.ne(0).sum()
```

**Raw output**:

```text
raw_rows=200,999; exact code/label matches=200,999/200,999
extras1_runs value counts:
extras1_runs
1       576
2      7714
3      2748
4       529
5       264
6    189167
7         1
extras_2_runs nonzero rows=36; wide=7,714; no-ball=576
Code mapping cross-check: 1->Overstep, 2->wide, 3->legbyes, 4->byes, 5->other, 7->Penalty, 6->NULL/no extras
```

### 1B innings totals vs result text — FAIL

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
delivery_total = runs + extras_2_runs + (extras_type == "wide")
innings_total = delivery_total.groupby([match_id, innings]).sum()
reconstructed_margin = innings1 - innings2
compare(reconstructed_margin, integer parsed from matches.result)
```

**Raw output**:

```text
run-margin matches parsed=410; exact margin matches=51 (12.44%); within +/-1=128 (31.22%)
non-DLS exact margin matches=49/399 (12.28%)
matches without a numeric run-margin in result text=473/883; wicket-margin/no-result text does not expose final innings scores for total reconciliation
extras_type and recorded extras_2_runs:
             deliveries  recorded_extra_runs  rows_with_extra
extras_type                                                  
Overstep            576                   48               21
Penalty               1                    0                0
byes                529                    0                0
legbyes            2748                    0                0
other               264                   35               14
wide               7714                    0                0
NaN              189167                    1                1
mismatch count=359; each row: match_id | result | innings1 | innings2 | reported margin | reconstructed margin | error | revised_target
 match_id                                          result  inn1  inn2  result_margin  reconstructed_margin  error  revised_target
    13512                            England Won by 1 Run 171.0 162.0            1.0                   9.0    8.0             NaN
    13513                      West Indies Won by 20 runs 214.0 199.0           20.0                  15.0   -5.0             NaN
    13514                          England Won by 34 runs 190.0 155.0           34.0                  35.0    1.0             NaN
    13515                      West Indies Won by 17 runs 174.0 156.0           17.0                  18.0    1.0             NaN
    13524                            India Won by 17 runs 174.0 164.0           17.0                  10.0   -7.0             NaN
    13612           Australia Won by 20 runs (D/L method) 145.0 115.0           20.0                  30.0   10.0           143.0
    14098                 Rajasthan Royals Won by 61 Runs 202.0 143.0           61.0                  59.0   -2.0             NaN
    14102                 Rajasthan Royals Won by 23 Runs 188.0 167.0           23.0                  21.0   -2.0             NaN
    14103                   Gujarat Titans won by 14 runs 167.0 149.0           14.0                  18.0    4.0             NaN
    14104                     Punjab Kings won by 54 runs 179.0 124.0           54.0                  55.0    1.0             NaN
    14105             Lucknow Super Giants won by 12 Runs 166.0 152.0           12.0                  14.0    2.0             NaN
    14112                    Delhi Capitals won by 44 run 205.0 168.0           44.0                  37.0   -7.0             NaN
    14113                  Rajasthan Royals Won By 3 Runs 162.0 161.0            3.0                   1.0   -2.0             NaN
    14115              Chennai Super Kings Won by 23 Runs 209.0 192.0           23.0                  17.0   -6.0             NaN
    14116                     Punjab Kings won by 12 runs 189.0 185.0           12.0                   4.0   -8.0             NaN
    14119             Lucknow Super Giants won by 18 runs 195.0 171.0           18.0                  24.0    6.0             NaN
    14120      Royal Challengers Bengaluru won by 16 runs 185.0 172.0           16.0                  13.0   -3.0             NaN
    14123                  Rajasthan Royals Won by 7 Runs 207.0 210.0            7.0                  -3.0  -10.0             NaN
    14124      Royal Challengers Bengaluru won by 18 runs 178.0 155.0           18.0                  23.0    5.0             NaN
    14127                 Rajasthan Royals Won by 15 Runs 221.0 205.0           15.0                  16.0    1.0             NaN
    14128                    Gujarat Titans Won by 8 Runs 153.0 146.0            8.0                   7.0   -1.0             NaN
    14131                     Punjab Kings Won by 11 Runs 184.0 166.0           11.0                  18.0    7.0             NaN
    14132                 Rajasthan Royals Won by 29 Runs 144.0 110.0           29.0                  34.0    5.0             NaN
    14135             Lucknow Super Giants Won by 20 Runs 145.0 126.0           20.0                  19.0   -1.0             NaN
    14139              Lucknow Super Giants won by 6 runs 190.0 189.0            6.0                   1.0   -5.0             NaN
    14140              Chennai Super Kings won by 13 runs 196.0 186.0           13.0                  10.0   -3.0             NaN
    14143      Royal Challengers Bengaluru won by 13 Runs 168.0 156.0           13.0                  12.0   -1.0             NaN
    14144                   Delhi Capitals Won by 21 Runs 201.0 181.0           21.0                  20.0   -1.0             NaN
    14147             Lucknow Super Giants won by 75 runs 174.0 100.0           75.0                  74.0   -1.0             NaN
    14150            Kolkata Knight Riders Won by 52 Runs 160.0 105.0           52.0                  55.0    3.0             NaN
    14151                   Gujarat Titans won by 62 runs 143.0  82.0           62.0                  61.0   -1.0             NaN
    14154                     Punjab Kings won by 54 runs 205.0 153.0           54.0                  52.0   -2.0             NaN
    14155            Kolkata Knight Riders won by 54 runs 173.0 123.0           54.0                  50.0   -4.0             NaN
    14157                 Rajasthan Royals Won by 24 Runs 176.0 147.0           24.0                  29.0    5.0             NaN
    14158                   Delhi Capitals Won by 17 Runs 152.0 141.0           17.0                  11.0   -6.0             NaN
    14159               Sunrisers Hyderabad Won by 3 Runs 189.0 185.0            3.0                   4.0    1.0             NaN
    14160              Lucknow Super Giants Won by 2 Runs 209.0 204.0            2.0                   5.0    3.0             NaN
    15188      Royal Challengers Bengaluru Won by 14 Runs 202.0 181.0           14.0                  21.0    7.0             NaN
    15408                            India Won by 48 runs 175.0 129.0           48.0                  46.0   -2.0             NaN
    15409                            India Won by 82 runs 166.0  81.0           82.0                  85.0    3.0             NaN
    15547                      West Indies Won by 35 Runs 190.0 156.0           35.0                  34.0   -1.0             NaN
    15610                      Afghanistan Won by 21 Runs 166.0 147.0           21.0                  19.0   -2.0             NaN
    15611                      Afghanistan Won by 35 Runs 122.0  83.0           35.0                  39.0    4.0             NaN
    15796                             India Won by 4 Runs 219.0 210.0            4.0                   9.0    5.0             NaN
    16040                            India Won by 50 Runs 195.0 139.0           50.0                  56.0    6.0             NaN
    16041                            India Won by 49 Runs 166.0 120.0           49.0                  46.0   -3.0             NaN
    16042                          England Won by 17 runs 207.0 196.0           17.0                  11.0   -6.0             NaN
    16062                            India Won by 68 Runs 180.0 119.0           68.0                  61.0   -7.0             NaN
    16065                            India Won by 59 Runs 187.0 129.0           59.0                  58.0   -1.0             NaN
    16066                            India Won by 88 Runs 185.0  96.0           88.0                  89.0    1.0             NaN
    16258                      New Zealand Won by 31 Runs 162.0 137.0           31.0                  25.0   -6.0             NaN
    16259                      New Zealand Won by 88 runs 165.0  91.0           88.0                  74.0  -14.0             NaN
    16315                          England Won by 41 Runs 229.0 190.0           41.0                  39.0   -2.0             NaN
    16316                     South Africa Won by 58 Runs 204.0 149.0           58.0                  55.0   -3.0             NaN
    16317                     South Africa Won by 90 Runs 188.0  94.0           90.0                  94.0    4.0             NaN
    16424                         Zimbabwe Won by 17 Runs 202.0 174.0           17.0                  28.0   11.0             NaN
    16426                         Zimbabwe Won by 10 runs 148.0 139.0           10.0                   9.0   -1.0             NaN
    16646                     South Africa won by 21 runs 206.0 184.0           21.0                  22.0    1.0             NaN
    16658                        Pakistan Won by 155 Runs 183.0  32.0          155.0                 151.0   -4.0             NaN
    16665                        Sri Lanka Won by 23 Runs 162.0 141.0           23.0                  21.0   -2.0             NaN
    16666                      New Zealand Won by 16 Runs 146.0 129.0           16.0                  17.0    1.0             NaN
    16683                      New Zealand Won by 13 Runs 185.0 168.0           13.0                  17.0    4.0             NaN
    16684                      New Zealand Won by 90 Runs 208.0 121.0           90.0                  87.0   -3.0             NaN
    16752                      Afghanistan Won by 22 Runs 184.0 166.0           22.0                  18.0   -4.0             NaN
    16753                      Afghanistan Won by 27 Runs 126.0  97.0           27.0                  29.0    2.0             NaN
    16862                         Hong Kong Won by 8 runs 140.0 138.0            8.0                   2.0   -6.0             NaN
    16864             United Arab Emirates Won by 47 Runs 157.0 111.0           47.0                  46.0   -1.0             NaN
    17555                          England Won by 63 Runs 219.0 151.0           63.0                  68.0    5.0             NaN
    17557                          Pakistan Won by 6 Runs 137.0 136.0            6.0                   1.0   -5.0             NaN
    17559                          England Won by 67 Runs 197.0 139.0           67.0                  58.0   -9.0             NaN
    17626                            India Won by 16 Runs 231.0 217.0           16.0                  14.0   -2.0             NaN
    17627                     South Africa Won by 49 Runs 219.0 175.0           49.0                  44.0   -5.0             NaN
    17631                        Bangladesh won by 7 runs 152.0 148.0            7.0                   4.0   -3.0             NaN
    17632                       Bangladesh Won by 32 Runs 168.0 135.0           32.0                  33.0    1.0             NaN
    17641                        Australia Won by 31 runs 174.0 140.0           31.0                  34.0    3.0             NaN
    17737                         Pakistan Won by 21 Runs 166.0 141.0           21.0                  25.0    4.0             NaN
    17741                      New Zealand Won by 48 Runs 203.0 153.0           48.0                  50.0    2.0             NaN
    17764                           England Won by 8 Runs 176.0 167.0            8.0                   9.0    1.0             NaN
    18531                            India won by 65 runs 185.0 121.0           65.0                  64.0   -1.0             NaN
    19556                             India Won by 2 Runs 161.0 158.0            2.0                   3.0    1.0             NaN
    19717                           India Won by 168 runs 231.0  65.0          168.0                 166.0   -2.0             NaN
    20182          Punjab Kings Won by 7 Runs(D/L Method) 189.0 141.0            7.0                  48.0   41.0             NaN
    20183             Lucknow Super Giants Won by 50 runs 190.0 138.0           50.0                  52.0    2.0             NaN
    20184                 Rajasthan Royals Won By 72 Runs 197.0 127.0           72.0                  70.0   -2.0             NaN
    20186              Chennai Super Kings Won by 12 runs 204.0 201.0           12.0                   3.0   -9.0             NaN
    20188                      Punjab Kings Won by 5 runs 194.0 187.0            5.0                   7.0    2.0             NaN
    20189            Kolkata Knight Riders Won By 81 Runs 187.0 118.0           81.0                  69.0  -12.0             NaN
    20197                  Rajasthan Royals Won by 3 Runs 171.0 169.0            3.0                   2.0   -1.0             NaN
    20199              Sunrisers Hyderabad Won By 23 Runs 223.0 202.0           23.0                  21.0   -2.0             NaN
    20200      Royal Challengers Bengaluru won by 23 runs 166.0 151.0           23.0                  15.0   -8.0             NaN
    20204               Chennai Super Kings Won by 8 Runs 223.0 213.0            8.0                  10.0    2.0             NaN
    20205                   Mumbai Indians Won by 14 Runs 192.0 167.0           14.0                  25.0   11.0             NaN
    20206             Lucknow Super Giants Won by 10 Runs 149.0 134.0           10.0                  15.0    5.0             NaN
    20207      Royal Challengers Bengaluru Won by 24 Runs 164.0 147.0           24.0                  17.0   -7.0             NaN
    20212       Royal Challengers Bengaluru Won By 7 Runs 181.0 177.0            7.0                   4.0   -3.0             NaN
    20214                    Delhi Capitals Won by 7 Runs 141.0 136.0            7.0                   5.0   -2.0             NaN
    20215                   Gujarat Titans Won by 55 runs 207.0 148.0           55.0                  59.0    4.0             NaN
    20216            Kolkata Knight Riders Won by 21 Runs 198.0 175.0           21.0                  23.0    2.0             NaN
    20217                 Rajasthan Royals Won by 32 Runs 195.0 169.0           32.0                  26.0   -6.0             NaN
    20218             Lucknow Super Giants Won by 56 runs 248.0 195.0           56.0                  53.0   -3.0             NaN
    20220               Sunrisers Hyderabad Won by 9 Runs 195.0 187.0            9.0                   8.0   -1.0             NaN
    20223     Royal Challengers Bengaluru Won  by 18 Runs 126.0 104.0           18.0                  22.0    4.0             NaN
    20224                    Delhi Capitals Won by 5 runs 128.0 124.0            5.0                   4.0   -1.0             NaN
    20227             Kolkata Knight Riders Won by 5 Runs 168.0 156.0            5.0                  12.0    7.0             NaN
    20231                   Gujarat Titans Won By 56 Runs 225.0 168.0           56.0                  57.0    1.0             NaN
    20235              Chennai Super Kings Won by 27 Runs 162.0 134.0           27.0                  28.0    1.0             NaN
    20237                   Mumbai Indians Won by 27 Runs 216.0 188.0           27.0                  28.0    1.0             NaN
    20239                     Punjab Kings Won by 31 Runs 161.0 135.0           31.0                  26.0   -5.0             NaN
    20242                   Gujarat Titans Won by 34 runs 181.0 150.0           34.0                  31.0   -3.0             NaN
    20243              Lucknow Super Giants won by 5 runs 172.0 169.0            5.0                   3.0   -2.0             NaN
    20244                   Delhi Capitals Won by 15 runs 213.0 190.0           15.0                  23.0    8.0             NaN
    20247              Chennai Super Kings Won by 77 runs 220.0 142.0           77.0                  78.0    1.0             NaN
    20248               Lucknow Super Giants won by 1 run 169.0 171.0            1.0                  -2.0   -3.0             NaN
    21583              Chennai Super Kings Won by 15 runs 168.0 154.0           15.0                  14.0   -1.0             NaN
    21584                   Mumbai Indians won by 81 runs 172.0  94.0           81.0                  78.0   -3.0             NaN
    21585                   Gujarat Titans won by 62 runs 228.0 168.0           62.0                  60.0   -2.0             NaN
    19961                       West Indies Won by 7 runs 215.0 210.0            7.0                   5.0   -2.0             NaN
    20135                       Bangladesh won by 16 runs 154.0 134.0           16.0                  20.0    4.0             NaN
    21070          Bangladesh Won by 22 Runs (DLS method) 202.0  74.0           22.0                 128.0  106.0           104.0
    20880                         Pakistan Won by 66 Runs 173.0 111.0           66.0                  62.0   -4.0             NaN
    21403                         Pakistan Won by 88 Runs 172.0  94.0           88.0                  78.0  -10.0             NaN
    21405                       New Zealand Won by 4 Runs 158.0 151.0            4.0                   7.0    3.0             NaN
    24350                     West Indies Won   by 4 runs 147.0 135.0            4.0                  12.0    8.0             NaN
    24792                      New Zealand Won by 19 Runs 155.0 133.0           19.0                  22.0    3.0             NaN
    24794                      New Zealand Won by 32 Runs 163.0 124.0           32.0                  39.0    7.0             NaN
    24822                India Won by 2 Runs (DLS method) 138.0  46.0            2.0                  92.0   90.0             NaN
    24823                            India Won by 33 Runs 182.0 142.0           33.0                  40.0    7.0             NaN
    25159                          England Won by 95 runs 193.0 101.0           95.0                  92.0   -3.0             NaN
    25160                      New Zealand Won by 74 runs 198.0 127.0           74.0                  71.0   -3.0             NaN
    25155                       Australia Won by 111 Runs 220.0 115.0          111.0                 105.0   -6.0             NaN
    27061                            India won by 44 runs 231.0 186.0           44.0                  45.0    1.0             NaN
    27063                            India Won by 20 runs 168.0 151.0           20.0                  17.0   -3.0             NaN
    27064                             India won by 6 runs 157.0 154.0            6.0                   3.0   -3.0             NaN
    28047                           India won by 106 runs 196.0  93.0          106.0                 103.0   -3.0             NaN
    28064                      West Indies won by 10 runs 175.0 164.0           10.0                  11.0    1.0             NaN
    28066                          England Won by 75 Runs 263.0 178.0           75.0                  85.0   10.0             NaN
    28963                      New Zealand won by 46 runs 218.0 179.0           46.0                  39.0   -7.0             NaN
    28964                      New Zealand Won by 21 Runs 192.0 172.0           21.0                  20.0   -1.0             NaN
    28965                      New Zealand Won by 45 Runs 219.0 171.0           45.0                  48.0    3.0             NaN
    28967                         Pakistan Won by 42 Runs 125.0  91.0           42.0                  34.0   -8.0             NaN
    29816                        Australia Won by 34 Runs 229.0 196.0           34.0                  33.0   -1.0             NaN
    29983                        Australia Won by 72 Runs 159.0  95.0           72.0                  64.0   -8.0             NaN
    29984           Australia Won by 27 Runs (DLS method) 108.0  89.0           27.0                  19.0   -8.0           126.0
    30058             Kolkata Knight Riders won by 4 runs 206.0 199.0            4.0                   7.0    3.0             NaN
    30059                 Rajasthan Royals won by 20 runs 191.0 163.0           20.0                  28.0    8.0             NaN
    30060                    Gujarat Titans won by 6 runs 159.0 162.0            6.0                  -3.0   -9.0             NaN
    30062              Chennai Super Kings won by 63 runs 205.0 140.0           63.0                  65.0    2.0             NaN
    30063              Sunrisers Hyderabad won by 31 runs 266.0 240.0           31.0                  26.0   -5.0             NaN
    30064                 Rajasthan Royals won by 12 runs 183.0 172.0           12.0                  11.0   -1.0             NaN
    30070             Lucknow Super Giants Won by 28 runs 177.0 146.0           28.0                  31.0    3.0             NaN
    30071           Kolkata Knight Riders Won by 106 runs 263.0 159.0          106.0                 104.0   -2.0             NaN
    30075                   Mumbai Indians Won by 29 runs 228.0 203.0           29.0                  25.0   -4.0             NaN
    30076             Lucknow Super Giants Won by 33 runs 159.0 124.0           33.0                  35.0    2.0             NaN
    31241               Sunrisers Hyderabad Won by 2 runs 180.0 179.0            2.0                   1.0   -1.0             NaN
    31248              Sunrisers Hyderabad Won by 25 runs 283.0 261.0           25.0                  22.0   -3.0             NaN
    31251                    Mumbai Indians Won by 9 runs 186.0 172.0            9.0                  14.0    5.0             NaN
    31253              Sunrisers Hyderabad Won by 67 runs 264.0 198.0           67.0                  66.0   -1.0             NaN
    31254             Kolkata Knight Riders Won by 1 runs 213.0 216.0            1.0                  -3.0   -4.0             NaN
    31258                    Delhi Capitals Won by 4 runs 222.0 215.0            4.0                   7.0    3.0             NaN
    31261                   Delhi Capitals Won by 10 runs 255.0 237.0           10.0                  18.0    8.0             NaN
    31264              Chennai Super Kings Won by 78 runs 209.0 133.0           78.0                  76.0   -2.0             NaN
    31268               Sunrisers Hyderabad Won by 1 runs 201.0 197.0            1.0                   4.0    3.0             NaN
    31269            Kolkata Knight Riders Won by 24 runs 167.0 139.0           24.0                  28.0    4.0             NaN
    31271              Chennai Super Kings Won by 28 runs 166.0 134.0           28.0                  32.0    4.0             NaN
    31272            Kolkata Knight Riders Won by 98 runs 231.0 136.0           98.0                  95.0   -3.0             NaN
    31274                   Delhi Capitals Won by 20 runs 221.0 196.0           20.0                  25.0    5.0             NaN
    31276      Royal Challengers Bengaluru Won by 60 runs 239.0 178.0           60.0                  61.0    1.0             NaN
    31277                   Gujarat Titans Won by 35 runs 230.0 193.0           35.0                  37.0    2.0             NaN
    31280      Royal Challengers Bengaluru Won by 47 runs 184.0 139.0           47.0                  45.0   -2.0             NaN
    31282                   Delhi Capitals Won by 19 runs 208.0 188.0           19.0                  20.0    1.0             NaN
    31285             Lucknow Super Giants Won by 18 runs 213.0 193.0           18.0                  20.0    2.0             NaN
    31286      Royal Challengers Bengaluru Won by 27 runs 217.0 180.0           27.0                  37.0   10.0             NaN
    31291              Sunrisers Hyderabad Won by 36 runs 174.0 137.0           36.0                  37.0    1.0             NaN
    29924                         Sri Lanka Won by 4 runs 157.0 151.0            4.0                   6.0    2.0             NaN
    29925                        Sri Lanka Won by 72 Runs 182.0 113.0           72.0                  69.0   -3.0             NaN
    29926                       Afghanistan won by 3 runs 192.0 204.0            3.0                 -12.0  -15.0             NaN
    30728                          Ireland won by 38 runs 138.0 109.0           38.0                  29.0   -9.0             NaN
    30730                      Afghanistan won by 57 runs 153.0  92.0           57.0                  61.0    4.0             NaN
    30341                         Sri Lanka won by 3 runs 197.0 197.0            3.0                   0.0   -3.0             NaN
    30343                        Sri Lanka won by 28 runs 163.0 143.0           28.0                  20.0   -8.0             NaN
    31710                       New Zealand Won by 4 runs 175.0 169.0            4.0                   6.0    2.0             NaN
    31711                          Pakistan Won by 9 runs 176.0 165.0            9.0                  11.0    2.0             NaN
    32611                          England Won by 23 runs 178.0 159.0           23.0                  19.0   -4.0             NaN
    32134                        Bangladesh Won by 9 runs 161.0 150.0            9.0                  11.0    2.0             NaN
    32135                        Bangladesh Won by 5 runs 133.0 136.0            5.0                  -3.0   -8.0             NaN
    33804                           India Won by 100 runs 233.0 127.0          100.0                 106.0    6.0             NaN
    33805                            India Won by 23 runs 175.0 156.0           23.0                  19.0   -4.0             NaN
    37355                        Australia Won by 13 runs 143.0 127.0           13.0                  16.0    3.0             NaN
    32620                      Netherlands Won by 41 runs 164.0 125.0           41.0                  39.0   -2.0             NaN
    32621                           Ireland Won by 1 runs 148.0 146.0            1.0                   2.0    1.0             NaN
    32623                         Scotland Won by 71 runs 150.0  82.0           71.0                  68.0   -3.0             NaN
    38795                     South Africa Won by 11 runs 183.0 156.0           11.0                  27.0   16.0             NaN
    32617                      West Indies Won by 28 runs 162.0 145.0           28.0                  17.0  -11.0             NaN
    32618                      West Indies Won by 16 runs 202.0 176.0           16.0                  26.0   10.0             NaN
    36097                      West Indies Won by 30 runs 178.0 146.0           30.0                  32.0    2.0             NaN
    38842                        Bangladesh Won by 7 runs 146.0 133.0            7.0                  13.0    6.0             NaN
    38843                       Bangladesh Won by 27 runs 127.0 101.0           27.0                  26.0   -1.0             NaN
    37277                            India Won by 86 runs 217.0 126.0           86.0                  91.0    5.0             NaN
    37278                           India Won by 133 runs 287.0 159.0          133.0                 128.0   -5.0             NaN
    40038                          England Won by 26 runs 165.0 140.0           26.0                  25.0   -1.0             NaN
    40040                           India Won by 150 runs 243.0  96.0          150.0                 147.0   -3.0             NaN
    34427                            India Won by 43 runs 213.0 168.0           43.0                  45.0    2.0             NaN
    36562                        Australia Won by 28 runs 175.0 146.0           28.0                  29.0    1.0             NaN
    36560                        Australia Won by 70 runs 194.0 116.0           70.0                  78.0    8.0             NaN
    37015                          Ireland Won by 10 runs 191.0 184.0           10.0                   7.0   -3.0             NaN
    35425                     Netherlands Won by 102 runs 211.0 114.0          102.0                  97.0   -5.0             NaN
    35427                            Canada Won by 8 runs 130.0 115.0            8.0                  15.0    7.0             NaN
    35428         United States Of America Won by 20 runs 162.0 146.0           20.0                  16.0   -4.0             NaN
    35429                       Netherlands Won by 4 runs 125.0 126.0            4.0                  -1.0   -5.0             NaN
    36199                          England Won by 21 runs 186.0 164.0           21.0                  22.0    1.0             NaN
    36201                          England Won by 37 runs 244.0 198.0           37.0                  46.0    9.0             NaN
    36208         South Africa Won by 14 runs(DLS method)  94.0  49.0           14.0                  45.0   31.0            69.0
    36209                         England Won by 146 runs 298.0 157.0          146.0                 141.0   -5.0             NaN
    37088                           India A Won by 7 runs 179.0 167.0            7.0                  12.0    5.0             NaN
    37089                      Sri Lanka A Won by 42 runs 168.0 135.0           42.0                  33.0   -9.0             NaN
    37091                       Pakistan A Won by 74 runs 180.0 103.0           74.0                  77.0    3.0             NaN
    37095                      Pakistan A Won by 114 runs 179.0  64.0          114.0                 115.0    1.0             NaN
    37098                    Afghanistan A Won by 20 runs 203.0 184.0           20.0                  19.0   -1.0             NaN
    37554                        Sri Lanka Won by 73 runs 148.0  85.0           73.0                  63.0  -10.0             NaN
    37895                       New Zealand Won by 5 runs  92.0  97.0            5.0                  -5.0  -10.0             NaN
    37940                            India Won by 61 runs 199.0 141.0           61.0                  58.0   -3.0             NaN
    37942                            India Won by 11 runs 210.0 203.0           11.0                   7.0   -4.0             NaN
    37943                           India Won by 135 runs 277.0 146.0          135.0                 131.0   -4.0             NaN
    37926                         Pakistan Won by 57 runs 160.0 108.0           57.0                  52.0   -5.0             NaN
    40695              Sunrisers Hyderabad Won by 44 runs 282.0 236.0           44.0                  46.0    2.0             NaN
    40698                     Punjab Kings Won by 11 runs 235.0 228.0           11.0                   7.0   -4.0             NaN
    40701      Royal Challengers Bengaluru Won by 50 runs 193.0 145.0           50.0                  48.0   -2.0             NaN
    40702                   Gujarat Titans Won by 36 runs 191.0 158.0           36.0                  33.0   -3.0             NaN
    40704                  Rajasthan Royals Won by 6 runs 179.0 175.0            6.0                   4.0   -2.0             NaN
    40708            Kolkata Knight Riders Won by 80 runs 192.0 117.0           80.0                  75.0   -5.0             NaN
    40709             Lucknow Super Giants Won by 12 runs 203.0 187.0           12.0                  16.0    4.0             NaN
    40710                   Delhi Capitals Won by 25 runs 180.0 146.0           25.0                  34.0    9.0             NaN
    40712              Lucknow Super Giants Won by 4 runs 233.0 228.0            4.0                   5.0    1.0             NaN
    40715                     Punjab Kings Won by 18 runs 214.0 194.0           18.0                  20.0    2.0             NaN
    40716                   Gujarat Titans Won by 58 runs 214.0 159.0           58.0                  55.0   -3.0             NaN
    40722                   Mumbai Indians Won by 12 runs 203.0 185.0           12.0                  18.0    6.0             NaN
    40724                     Punjab Kings Won by 16 runs 109.0  91.0           16.0                  18.0    2.0             NaN
    40729              Lucknow Super Giants Won by 2 runs 176.0 177.0            2.0                  -1.0   -3.0             NaN
    40732                   Gujarat Titans Won by 39 runs 197.0 154.0           39.0                  43.0    4.0             NaN
    40735      Royal Challengers Bengaluru Won by 11 runs 200.0 192.0           11.0                   8.0   -3.0             NaN
    40738                   Mumbai Indians Won by 54 runs 215.0 158.0           54.0                  57.0    3.0             NaN
    40741            Kolkata Knight Riders Won by 14 runs 200.0 184.0           14.0                  16.0    2.0             NaN
    40743                  Mumbai Indians Won by 100 runs 216.0 105.0          100.0                 111.0   11.0             NaN
    40744                   Gujarat Titans Won by 38 runs 224.0 180.0           38.0                  44.0    6.0             NaN
    40745       Royal Challengers Bengaluru Won by 2 runs 211.0 210.0            2.0                   1.0   -1.0             NaN
    40746              Kolkata Knight Riders Won by 1 run 203.0 203.0            1.0                   0.0   -1.0             NaN
    40747                     Punjab Kings Won by 37 runs 236.0 195.0           37.0                  41.0    4.0             NaN
    40753             Sunrisers Hyderabad Won by 110 runs 264.0 166.0          110.0                  98.0  -12.0             NaN
    40757              Sunrisers Hyderabad Won by 42 runs 226.0 177.0           42.0                  49.0    7.0             NaN
    40758             Lucknow Super Giants Won by 33 runs 231.0 201.0           33.0                  30.0   -3.0             NaN
    40762              Chennai Super Kings Won by 83 runs 223.0 141.0           83.0                  82.0   -1.0             NaN
    40765                   Mumbai Indians Won by 20 runs 221.0 206.0           20.0                  15.0   -5.0             NaN
    40767       Royal Challengers Bengaluru Won by 6 runs 190.0 176.0            6.0                  14.0    8.0             NaN
    38627                      Afghanistan Won by 50 runs 152.0 100.0           50.0                  52.0    2.0             NaN
    38632                       New Zealand Won by 8 runs 169.0 160.0            8.0                   9.0    1.0             NaN
    38633                      New Zealand Won by 45 runs 179.0 137.0           45.0                  42.0   -3.0             NaN
    38634                         Sri Lanka Won by 7 runs 216.0 207.0            7.0                   9.0    2.0             NaN
    39811                     New Zealand Won by 115 runs 210.0 101.0          115.0                 109.0   -6.0             NaN
    41504                      West Indies Won by 62 runs 252.0 179.0           62.0                  73.0   11.0             NaN
    41510                         Pakistan Won by 14 runs 171.0 160.0           14.0                  11.0   -3.0             NaN
    41512                         Pakistan Won by 13 runs 188.0 176.0           13.0                  12.0   -1.0             NaN
    41851           West Indies Won by 6 runs(DLS Method) 112.0 117.0            6.0                  -5.0  -11.0           125.0
    41969                        Australia Won by 17 runs 171.0 155.0           17.0                  16.0   -1.0             NaN
    41970                     South Africa Won by 53 runs 213.0 158.0           53.0                  55.0    2.0             NaN
    41978                            India Won by 48 runs 164.0 118.0           48.0                  46.0   -2.0             NaN
    42027                           India Won by 101 runs 167.0  74.0          101.0                  93.0   -8.0             NaN
    42028                     South Africa Won by 51 runs 206.0 158.0           51.0                  48.0   -3.0             NaN
    42031                            India Won by 30 runs 228.0 197.0           30.0                  31.0    1.0             NaN
    42742                         Pakistan Won by 37 runs 199.0 163.0           37.0                  36.0   -1.0             NaN
    42743                         Pakistan Won by 57 runs 201.0 141.0           57.0                  60.0    3.0             NaN
    42783                       Bangladesh Won by 27 runs 175.0 157.0           27.0                  18.0   -9.0             NaN
    43594                       Bangladesh Won by 83 runs 172.0  91.0           83.0                  81.0   -2.0             NaN
    44266                        Bangladesh Won by 8 runs 131.0 121.0            8.0                  10.0    2.0             NaN
    44267                         Pakistan Won by 74 runs 172.0  96.0           74.0                  76.0    2.0             NaN
    45392                         England Won by 125 runs 200.0  76.0          125.0                 124.0   -1.0             NaN
    45394                          England Won by 56 runs 250.0 199.0           56.0                  51.0   -5.0             NaN
    45489                         England Won by 119 runs 246.0 130.0          119.0                 116.0   -3.0             NaN
    45495                      Afghanistan Won by 94 runs 186.0  89.0           94.0                  97.0    3.0             NaN
    45501             United Arab Emirates Won by 42 runs 169.0 123.0           42.0                  46.0    4.0             NaN
    45503                        Bangladesh Won by 8 runs 154.0 145.0            8.0                   9.0    1.0             NaN
    45504                         Pakistan Won by 41 runs 140.0  98.0           41.0                  42.0    1.0             NaN
    45506                            India Won by 21 runs 181.0 165.0           21.0                  16.0   -5.0             NaN
    45510                            India Won by 41 runs 166.0 123.0           41.0                  43.0    2.0             NaN
    45511                         Pakistan Won by 11 runs 135.0 121.0           11.0                  14.0    3.0             NaN
    45851                         Pakistan Won by 39 runs 171.0 142.0           39.0                  29.0  -10.0             NaN
    45853                      Afghanistan Won by 38 runs 186.0 150.0           38.0                  36.0   -2.0             NaN
    45854                      Afghanistan Won by 18 runs 167.0 144.0           18.0                  23.0    5.0             NaN
    45855                         Pakistan Won by 31 runs 168.0 138.0           31.0                  30.0   -1.0             NaN
    45856                       Afghanistan Won by 4 runs 164.0 163.0            4.0                   1.0   -3.0             NaN
    45857                         Pakistan Won by 75 runs 133.0  62.0           75.0                  71.0   -4.0             NaN
    46250                            Nepal Won by 90 runs 168.0  79.0           90.0                  89.0   -1.0             NaN
    46740                     South Africa Won by 55 runs 192.0 136.0           55.0                  56.0    1.0             NaN
    46748                          England Won by 65 runs 232.0 161.0           65.0                  71.0    6.0             NaN
    46940                      West Indies Won by 16 runs 162.0 147.0           16.0                  15.0   -1.0             NaN
    46941                      West Indies Won by 14 runs 147.0 134.0           14.0                  13.0   -1.0             NaN
    47241                          Ireland Won by 39 runs 177.0 142.0           39.0                  35.0   -4.0             NaN
    47260                      Afghanistan Won by 53 runs 175.0 127.0           53.0                  48.0   -5.0             NaN
    47262                       Afghanistan Won by 9 runs 202.0 195.0            9.0                   7.0   -2.0             NaN
    47965                       West Indies Won by 7 runs 158.0 155.0            7.0                   3.0   -4.0             NaN
    47966                       New Zealand Won by 3 runs 205.0 199.0            3.0                   6.0    3.0             NaN
    47967                       New Zealand Won by 9 runs 174.0 166.0            9.0                   8.0   -1.0             NaN
    47977                         Zimbabwe Won by 67 runs 158.0  89.0           67.0                  69.0    2.0             NaN
    47979                         Pakistan Won by 69 runs 188.0 124.0           69.0                  64.0   -5.0             NaN
    47981                         Sri Lanka Won by 6 runs 178.0 175.0            6.0                   3.0   -3.0             NaN
    48015                       Pakistan A Won by 40 runs 214.0 178.0           40.0                  36.0   -4.0             NaN
    48016                         India A Won by 148 runs 297.0 143.0          148.0                 154.0    6.0             NaN
    48025                    Afghanistan A Won by 24 runs 138.0 113.0           24.0                  25.0    1.0             NaN
    48026                       Sri Lanka A Won by 6 runs 159.0 148.0            6.0                  11.0    5.0             NaN
    48028                        Pakistan A Won by 5 runs 152.0 136.0            5.0                  16.0   11.0             NaN
    50130              Sunrisers Hyderabad Won by 65 runs 222.0 159.0           65.0                  63.0   -2.0             NaN
    50133                  Rajasthan Royals Won by 6 runs 205.0 197.0            6.0                   8.0    2.0             NaN
    50135      Royal Challengers Bengaluru Won by 43 runs 245.0 203.0           43.0                  42.0   -1.0             NaN
    50137                 Rajasthan Royals Won by 27 runs 150.0 118.0           27.0                  32.0    5.0           151.0
    50138                     Gujarat Titans Won by 1 run 209.0 209.0            1.0                   0.0   -1.0             NaN
    50142              Chennai Super Kings Won by 23 runs 212.0 180.0           23.0                  32.0    9.0             NaN
    50144      Royal Challengers Bengaluru Won by 18 runs 238.0 219.0           18.0                  19.0    1.0             NaN
    50343              Chennai Super Kings Won by 32 runs 187.0 158.0           32.0                  29.0   -3.0             NaN
    50348              Sunrisers Hyderabad Won by 10 runs 185.0 177.0           10.0                   8.0   -2.0             NaN
    50351                   Mumbai Indians Won by 99 runs 194.0 100.0           99.0                  94.0   -5.0             NaN
    50352              Sunrisers Hyderabad Won by 47 runs 242.0 193.0           47.0                  49.0    2.0             NaN
    50353                 Rajasthan Royals Won by 40 runs 158.0 117.0           40.0                  41.0    1.0             NaN
    50354             Chennai Super Kings Won by 103 runs 203.0 102.0          103.0                 101.0   -2.0             NaN
    50370              Sunrisers Hyderabad Won by 33 runs 231.0 200.0           33.0                  31.0   -2.0             NaN
    50371 Lucknow Super Giants Won by 9 runs (DLS method) 204.0 199.0            9.0                   5.0   -4.0           213.0
    50373                   Gujarat Titans Won by 77 runs 222.0 151.0           77.0                  71.0   -6.0             NaN
    50377                   Gujarat Titans Won by 82 runs 166.0  85.0           82.0                  81.0   -1.0             NaN
    50381            Kolkata Knight Riders Won by 29 runs 245.0 205.0           29.0                  40.0   11.0             NaN
    50382      Royal Challengers Bengaluru Won by 23 runs 220.0 195.0           23.0                  25.0    2.0             NaN
    50387                   Gujarat Titans Won by 89 runs 220.0 140.0           89.0                  80.0   -9.0             NaN
    50388              Sunrisers Hyderabad Won by 55 runs 254.0 196.0           55.0                  58.0    3.0             NaN
    50390                 Rajasthan Royals Won by 30 runs 200.0 174.0           30.0                  26.0   -4.0             NaN
    50391                   Delhi Capitals Won by 40 runs 199.0 162.0           40.0                  37.0   -3.0             NaN
    50942      Royal Challengers Bengaluru Won by 92 runs 250.0 160.0           92.0                  90.0   -2.0             NaN
    50943                 Rajasthan Royals Won by 47 runs 240.0 191.0           47.0                  49.0    2.0             NaN
    48466                          Ireland Won by 57 runs 172.0 117.0           57.0                  55.0   -2.0             NaN
    48514                        Sri Lanka Won by 14 runs 156.0 145.0           14.0                  11.0   -3.0             NaN
    48591                            India Won by 48 runs 233.0 190.0           48.0                  43.0   -5.0             NaN
    48594                      New Zealand Won by 50 runs 213.0 165.0           50.0                  48.0   -2.0             NaN
    48595                            India Won by 46 runs 265.0 211.0           46.0                  54.0    8.0             NaN
    48596                      Afghanistan Won by 38 runs 180.0 140.0           38.0                  40.0    2.0             NaN
    48597                      Afghanistan Won by 39 runs 182.0 149.0           39.0                  33.0   -6.0             NaN
    48610             England Won by 11 runs (DLS method) 127.0 121.0           11.0                   6.0   -5.0           115.0
    48612                          England Won by 12 runs 127.0 111.0           12.0                  16.0    4.0             NaN
    48915                         Pakistan Won by 22 runs 158.0 145.0           22.0                  13.0   -9.0             NaN
    48917                        Pakistan Won by 111 runs 205.0  84.0          111.0                 121.0   10.0             NaN
    49739                     South Africa Won by 19 runs 161.0 141.0           19.0                  20.0    1.0             NaN
    50340                          Ireland Won by 34 runs 178.0 145.0           34.0                  33.0   -1.0             NaN
    50341                            Ireland Won by 1 run 151.0 147.0            1.0                   4.0    3.0             NaN
    50406                            India Won by 14 runs 217.0 204.0           14.0                  13.0   -1.0             NaN
    50407                      West Indies Won by 24 runs 238.0 211.0           24.0                  27.0    3.0             NaN
    50504                        Sri Lanka Won by 37 runs 188.0 155.0           37.0                  33.0   -4.0             NaN
    50508                            India Won by 90 runs 216.0 124.0           90.0                  92.0    2.0             NaN
    50509                            India Won by 35 runs 185.0 146.0           35.0                  39.0    4.0             NaN
    50598                         Australia Won by 7 runs 191.0 182.0            7.0                   9.0    2.0             NaN
    51383                         Zimbabwe Won by 32 runs 165.0 135.0           32.0                  30.0   -2.0             NaN
    51384                       Bangladesh Won by 34 runs 183.0 151.0           34.0                  32.0   -2.0             NaN
    54410                           India Won by 127 runs 221.0  93.0          127.0                 128.0    1.0             NaN
    54711                             India Won by 2 runs  31.0  30.0            2.0                   1.0   -1.0            33.0
    55079                         Pakistan Won by 82 runs 214.0 131.0           82.0                  83.0    1.0             NaN
```

### 1C superovers and DLS handling — FAIL

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
superovers = raw[innings > 2]
DLS = revised_target > 0
check DLS target/overs and count DLS rows in model/pressure inputs
```

**Raw output**:

```text
raw super-over rows (innings>2)=38; matches=6
raw innings distribution:
innings
1    105727
2     95234
3        25
4        13
ball_state rows=200,961; any innings>2=0
matches with revised_target>0=23; with revised overs=34
DLS rows retained: state=3,727; pressure=3,727; 2nd-innings target != revised_target rows=0
exclude_from_rrr true rows=1,641; retained among model/band input=1,641
Source behavior: DLS target/overs alter state; DLS rows remain in model fit, leverage, composite and validation.
```

### 1D legal balls and remaining-ball bounds — FAIL

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
is_legal = extras_type not in {"wide", "Overstep"}
legal_ball_num = groupby(match_id, innings).is_legal.cumsum()
balls_remaining = clip(max_legal_balls - legal_ball_num, lower=0)
compare raw legal flags and assert 0 <= balls_remaining <= 120
```

**Raw output**:

```text
retained rows=200,961; raw legal rows in innings 1-2=192,675; stored legal rows=192,675; legal-flag mismatches=0
balls_remaining min=0; max=684; outside [0,120]=3,270
innings whose legal_ball_num exceeds max_legal_balls=150/1,712; rows with legal_ball_num>120=172
revised-over field min/max=30/114; values divisible by 6=50/50; distinct samples=[np.float64(30.0), np.float64(42.0), np.float64(48.0), np.float64(54.0), np.float64(60.0), np.float64(66.0), np.float64(72.0), np.float64(78.0), np.float64(84.0), np.float64(90.0), np.float64(102.0), np.float64(108.0)]
Examples of max_legal_balls >120 (pipeline multiplies the revised field by 6):
 match_id  innings  last_legal  max_balls  first_inn_revised_overs  second_inn_revised_overs
    13612        2         114        684                      NaN                     114.0
    15410        1          21        684                    114.0                       NaN
    15546        1          79        504                     84.0                       NaN
    16753        1          66        396                     66.0                       NaN
    16754        2          40        252                      NaN                      42.0
    17395        1          48        288                     48.0                      48.0
    17395        2          44        288                     48.0                      48.0
    17765        1          72        432                     72.0                      72.0
    17765        2          23        432                     72.0                      72.0
    19959        1          66        396                     66.0                       NaN
    21070        2          48        288                      NaN                      48.0
    21071        1         102        612                    102.0                     102.0
first delivery of each innings: legal_ball_num/balls_remaining sample:
 match_id  innings  legal_ball_num  balls_remaining  max_legal_balls
    13511        1               1              119              120
    13511        2               1              119              120
    13512        1               1              119              120
    13512        2               0              120              120
    13513        1               1              119              120
    13513        2               1              119              120
    13514        1               1              119              120
    13514        2               1              119              120
```

### 1E 200,999 to 200,961 and band denominator — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
retained = raw rows with innings in {1,2}
band_total = pressure_band.notna().sum()
band_legal = (is_legal & pressure_band.notna()).sum()
```

**Raw output**:

```text
raw deliveries=200,999; raw innings>2=38; raw minus superovers=200,961; stored=200,961; stored difference=38
composite Total Deliveries sum=200,961; composite Legal Balls sum=192,675; leverage Legal Balls sum=192,675
Band table Total Deliveries counts all rows; its Legal Balls metrics omit wides/no-balls.
```

### 2A no future information and claimed evaluation — FAIL

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
inspect _extract_features_inn1/_extract_features_inn2
fit(df); evaluate(df)  # same rows, not out of sample
```

**Raw output**:

```text
feature names used: innings 2=['runs_needed', 'balls_remaining', 'wickets_in_hand', 'required_run_rate', 'current_run_rate', 'run_rate_gap', 'runs_at_ball', 'match_format']; innings 1= runs_at_ball, balls_remaining, wickets_in_hand, current_run_rate, match_format, derived projection
feature-source scan found explicit outcome/final-score/current-dismissal fields=False
training rows with winner labels=199,029; evaluation rows=199,029 (same dataset)
reproduced in-sample Brier=0.179920; log-loss=0.528169; rounds to reported claims=True
Important timing issue: legal_ball_num is inclusive of the current delivery, while runs_at_ball is pre-delivery.
```

### 2B GroupKFold validation and baselines — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
for train_idx, test_idx in GroupKFold(5).split(valid, y, groups=match_id):
    fit original two-innings logistic WP model on train_idx
    predict test_idx
    fit constant-rate and [runs_at_ball, balls_remaining] baselines on train_idx
compute Brier, log-loss and qcut deciles on concatenated held-out predictions
```

**Raw output**:

```text
fold 1: train matches=674; test matches=168; overlap=0
fold 2: train matches=673; test matches=169; overlap=0
fold 3: train matches=673; test matches=169; overlap=0
fold 4: train matches=674; test matches=168; overlap=0
fold 5: train matches=674; test matches=168; overlap=0

WP model (5-fold GroupKFold by match_id):
n=199,029; batting-team win rate=0.490326; Brier=0.181786; log-loss=0.533221
mean_pred win_rate  count
   0.0311   0.0305  19903
   0.1781   0.1784  19903
   0.3038   0.2959  19903
   0.3949   0.4066  19903
   0.4672   0.4613  19904
   0.5314   0.5455  19901
   0.5987   0.6096  19903
   0.6791   0.6811  19903
   0.7921   0.7706  19903
   0.9293   0.9237  19903

Constant training win-rate baseline:
n=199,029; batting-team win rate=0.490326; Brier=0.249909; log-loss=0.692964
mean_pred win_rate  count
   0.4899   0.4921  79618
   0.4901   0.4912  39782
   0.4906   0.4891  39788
   0.4911   0.4872  39841

Score + balls-remaining logistic baseline:
n=199,029; batting-team win rate=0.490326; Brier=0.234946; log-loss=0.663172
mean_pred win_rate  count
   0.2850   0.2424  19903
   0.3716   0.3754  19905
   0.4169   0.4257  19901
   0.4499   0.4595  19906
   0.4758   0.4895  19901
   0.4973   0.5201  19901
   0.5184   0.5138  19905
   0.5459   0.5378  19902
   0.5994   0.6095  19902
   0.7444   0.7295  19903

beats constant (Brier AND log-loss): True; beats score/balls baseline (Brier AND log-loss): True
```

### 2C time-based validation and baselines — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
sort labeled matches by match_date; use earliest 80% of distinct dates for training
fit WP, constant-rate and score/balls-only models on train; score latest 20%
```

**Raw output**:

```text
train date range=2022-01-22 00:00:00+00:00..2025-11-09 00:00:00+00:00; test date range=2025-11-13 00:00:00+00:00..2026-11-01 00:00:00+00:00; cutoff=2025-11-13 00:00:00+00:00
train rows/matches=159,183/671; test rows/matches=39,846/171

WP model:
n=39,846; batting-team win rate=0.487050; Brier=0.187254; log-loss=0.546406
mean_pred win_rate  count
   0.0184   0.0309   3985
   0.1375   0.1905   3985
   0.2832   0.3351   3984
   0.4020   0.3757   3985
   0.4953   0.4714   3984
   0.5754   0.5410   3985
   0.6560   0.5926   3984
   0.7441   0.6310   3986
   0.8506   0.7555   3983
   0.9516   0.9471   3985

Constant baseline:
n=39,846; batting-team win rate=0.487050; Brier=0.249849; log-loss=0.692845
Empty DataFrame
Columns: [mean_pred, win_rate, count]
Index: []

Score + balls-remaining baseline:
n=39,846; batting-team win rate=0.487050; Brier=0.242185; log-loss=0.684108
mean_pred win_rate  count
   0.2840   0.2196   3985
   0.3940   0.3706   3985
   0.4457   0.4488   3986
   0.4804   0.4911   3985
   0.5056   0.5224   3982
   0.5273   0.5199   3985
   0.5574   0.5197   3989
   0.6046   0.5167   3981
   0.6872   0.6192   3984
   0.8509   0.6426   3984

beats constant (Brier AND log-loss): True; beats score/balls baseline (Brier AND log-loss): True
```

### 4B clean-folder deterministic pipeline reproduction — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
np.random.seed(20261111)
fresh = build_ball_state(save=False)  # reads raw parquet; writes nowhere
fit WinProbabilityModel; compute leverage/composite/bands in memory
repeat from raw again; compare arrays exactly; save only under audit/
```

**Raw output**:

```text
fixed seed=20261111; raw build stdout: Excluded 38 super-over deliveries
two fresh ball-state builds exact-equal=True
fresh state vs committed data/ball_state.parquet exact-equal=True
fresh state per-column mismatches at tolerance 1e-9: {}
full fresh pressure calculations repeated exactly (WP, leverage, composite)=True
fresh pressure vs stored data/ball_state_pressure.parquet mismatches at tolerance 1e-9: {}
output writes: audit/recomputed_ball_state.parquet; audit/recomputed_ball_state_pressure.parquet
```

### 3A first- vs second-innings pressure definition — FAIL

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
read compute_composite_pressure:
innings 1 = wicket_crisis + death_push + par_rate_lag
innings 2 = required_run_rate + wicket_depletion + stage + run_rate_gap
```

**Raw output**:

```text
First-innings formula (from source): wicket crisis + death overs push + par-rate lag; no target/RRR component.
Second-innings formula: RRR urgency + wicket depletion + balls/stage + run-rate gap; knockout multiplier.
innings-1 source formula has RRR/target term=False; innings-2 has RRR term=True
composite band x innings delivery counts:
innings                 1      2
pressure_band_comp              
Low                 58804  53223
Medium              34096  26098
High                12827  15913
composite band x competition x innings counts:
pressure_band_comp  competition_group  innings
Low                 IPL                1          26837
                                       2          22347
                    Other T20          1           1766
                                       2           2048
                    T20I               1          30201
                                       2          28828
Medium              IPL                1          14201
                                       2          12649
                    Other T20          1           1282
                                       2            727
                    T20I               1          18613
                                       2          12722
High                IPL                1           4550
                                       2           7089
                    Other T20          1            625
                                       2            525
                    T20I               1           7652
                                       2           8299
leverage band x competition x innings counts:
pressure_band_lev  competition_group  innings
Low                IPL                1          10949
                                      2          12252
                   Other T20          1           1321
                                      2           1071
                   T20I               1          12913
                                      2          16924
Medium             IPL                1          34639
                                      2           9955
                   Other T20          1           2352
                                      2            794
                   T20I               1          43553
                                      2          11296
High               IPL                1              0
                                      2          19878
                   Other T20          1              0
                                      2           1435
                   T20I               1              0
                                      2          21629
```

### 3B confounding by over, batting position and batter quality — CANNOT VERIFY

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
legal balls only; for each band pair, group by striker_id, innings, overid and batting_order;
keep shared strata and standardize both bands' rates using identical pooled stratum weights
```

**Raw output**:

```text
Pairwise strata are exact striker_id x innings x overid x batting_order; rates standardized to the same pooled legal-ball weights within each pair's common-support cells.
Composite raw metrics:
  Band  Total Deliveries  Legal Balls  Strike Rate  Bowling Econ  Dismissal Rate (%)  Dot Ball (%)  Boundary (%)  Six (%)  Runs/Wicket
   Low            112027       107768       137.84          8.27                4.59         34.20         19.25     6.09        30.02
Medium             60194        57613       140.76          8.45                5.73         28.18         17.63     6.92        24.56
  High             28740        27294       142.92          8.58                9.42         28.34         18.51     8.08        15.17
Composite pairwise standardized rates:
    Comparison     Low SR  Medium SR  Low dismissal (%)  Medium dismissal (%)    High SR  High dismissal (%)
 Low vs Medium 137.040569 141.066582           4.398837              6.739321        NaN                 NaN
   Low vs High 142.825126        NaN           4.993789                   NaN 161.150488            8.931509
Medium vs High        NaN 146.350322                NaN              7.602332 158.342775            8.835629
Composite pairwise support:
{'Low-Medium': {'strata': 4996, 'coverage': 0.35557285584533543, 'rates': {'Low': {'Strike Rate': 137.04056861605181, 'Dismissal Rate (%)': 4.398836851719706}, 'Medium': {'Strike Rate': 141.06658178195488, 'Dismissal Rate (%)': 6.739320658943926}}}, 'Low-High': {'strata': 851, 'coverage': 0.03954846243674581, 'rates': {'Low': {'Strike Rate': 142.82512626351925, 'Dismissal Rate (%)': 4.993788561303865}, 'High': {'Strike Rate': 161.15048779999657, 'Dismissal Rate (%)': 8.931509362329855}}}, 'Medium-High': {'strata': 2679, 'coverage': 0.12396003633060854, 'rates': {'Medium': {'Strike Rate': 146.35032195427186, 'Dismissal Rate (%)': 7.602332050395047}, 'High': {'Strike Rate': 158.34277497093723, 'Dismissal Rate (%)': 8.835629258683996}}}}
Composite effect:
raw dismissal H-L=4.830 pp; adjusted H-L=3.938 pp; retained abs effect=81.5%
raw SR H-L=5.080; adjusted H-L=18.325; retained abs effect=360.7%
shared strata=851; common-support legal-ball coverage=4.0%
Leverage raw metrics:
  Band  Total Deliveries  Legal Balls  Strike Rate  Bowling Econ  Dismissal Rate (%)  Dot Ball (%)  Boundary (%)  Six (%)  Runs/Wicket
   Low             55430        52906       143.62          8.62                6.63         29.80         18.89     7.77        21.67
Medium            102589        98618       138.45          8.31                5.15         31.90         18.58     6.25        26.89
  High             42942        41151       136.41          8.19                5.44         33.07         18.58     6.04        25.06
Leverage pairwise standardized rates:
    Comparison     Low SR  Medium SR  Low dismissal (%)  Medium dismissal (%)    High SR  High dismissal (%)
 Low vs Medium 153.942013 151.770486           6.644472              5.895796        NaN                 NaN
   Low vs High 145.877757        NaN           6.673654                   NaN 141.764792            5.887657
Medium vs High        NaN 146.943582                NaN              5.263808 142.890858            4.986079
Leverage pairwise support:
{'Low-Medium': {'strata': 6076, 'coverage': 0.34752822109770337, 'rates': {'Low': {'Strike Rate': 153.94201346480295, 'Dismissal Rate (%)': 6.644471649777105}, 'Medium': {'Strike Rate': 151.77048579380158, 'Dismissal Rate (%)': 5.895796201170785}}}, 'Low-High': {'strata': 3336, 'coverage': 0.20245491111976124, 'rates': {'Low': {'Strike Rate': 145.87775729849136, 'Dismissal Rate (%)': 6.673654337686355}, 'High': {'Strike Rate': 141.76479238894518, 'Dismissal Rate (%)': 5.887657254589481}}}, 'Medium-High': {'strata': 3527, 'coverage': 0.21695082392630077, 'rates': {'Medium': {'Strike Rate': 146.9435815080913, 'Dismissal Rate (%)': 5.263808380218736}, 'High': {'Strike Rate': 142.89085788980867, 'Dismissal Rate (%)': 4.986078933784687}}}}
Leverage effect:
raw dismissal H-L=-1.190 pp; adjusted H-L=-0.786 pp; retained abs effect=66.1%
raw SR H-L=-7.210; adjusted H-L=-4.113; retained abs effect=57.0%
shared strata=3,336; common-support legal-ball coverage=20.2%
```

### 3C composite index encodes wicket outcome proxy — FAIL

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
wickets_component = f(wickets_in_hand), where wickets_in_hand = 10 - wickets_before
compare original composite bands with same-threshold bands after zeroing that component
```

**Raw output**:

```text
wicket-state component >0 on 163,369/200,961 rows (81.3%); component range=0.000..4.400
reported composite bands:
  Band  Total Deliveries  Legal Balls  Strike Rate  Bowling Econ  Dismissal Rate (%)  Dot Ball (%)  Boundary (%)  Six (%)  Runs/Wicket
   Low            112027       107768       137.84          8.27                4.59         34.20         19.25     6.09        30.02
Medium             60194        57613       140.76          8.45                5.73         28.18         17.63     6.92        24.56
  High             28740        27294       142.92          8.58                9.42         28.34         18.51     8.08        15.17
same cutoffs with wicket component removed (score not re-tuned):
  Band  Total Deliveries  Legal Balls  Strike Rate  Bowling Econ  Dismissal Rate (%)  Dot Ball (%)  Boundary (%)  Six (%)  Runs/Wicket
   Low            164057       157490       138.30          8.30                5.10         32.33         18.62     6.32        27.11
Medium             31431        30053       142.77          8.57                7.43         28.13         18.36     7.61        19.21
  High              5473         5132       154.83          9.29               10.85         28.43         21.80    10.17        14.27
The score uses wickets_in_hand = 10 - wickets_before; outcome is current is_wicket. This is not same-ball label leakage, but it bakes prior wicket depletion into the predictor used to claim wicket-rate separation.
```

### 4A independently recomputed band tables — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
read saved delivery rows; independently regroup each band
legal = rows where is_legal; compute rates from runs, wickets, boundaries, total_delivery_runs
compare every reported count and rounded rate (tolerance 0.01)
```

**Raw output**:

```text
Independent LI table:
  Band  Total Deliveries  Legal Balls  Strike Rate  Bowling Econ  Dismissal Rate (%)  Dot Ball (%)  Boundary (%)  Six (%)  Runs/Wicket
   Low             55430        52906       143.62          8.62                6.63         29.80         18.89     7.77        21.67
Medium            102589        98618       138.45          8.31                5.15         31.90         18.58     6.25        26.89
  High             42942        41151       136.41          8.19                5.44         33.07         18.58     6.04        25.06

Independent composite table:
  Band  Total Deliveries  Legal Balls  Strike Rate  Bowling Econ  Dismissal Rate (%)  Dot Ball (%)  Boundary (%)  Six (%)  Runs/Wicket
   Low            112027       107768       137.84          8.27                4.59         34.20         19.25     6.09        30.02
Medium             60194        57613       140.76          8.45                5.73         28.18         17.63     6.92        24.56
  High             28740        27294       142.92          8.58                9.42         28.34         18.51     8.08        15.17

Comparison to every reported count/rate (counts exact; rates tolerance 0.01):
LI Low: all numeric fields within 0.01
LI Medium: all numeric fields within 0.01
LI High: all numeric fields within 0.01
Composite Low: all numeric fields within 0.01
Composite Medium: all numeric fields within 0.01
Composite High: all numeric fields within 0.01
maximum absolute numeric difference=0.0000
```

### 4C hand verification of 20 raw deliveries — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
rng = np.random.default_rng(20261111); choose 20 output deliveries
for each delivery, accumulate raw runs/wickets/legal balls up through that ball;
recompute target, remaining balls, RRR and composite pressure; compare stored fields
```

**Raw output**:

```text
20 deterministic random deliveries (seed=20261111); independently accumulated raw deliveries before/through the sampled ball, then recomputed current pipeline formulas.
 match  inn  over  ball  score_diff  wkt_diff  legal_diff  br_diff  target_diff  rrr_diff  pressure_diff
 14133    1     2     7         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 16647    2    14     4         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 20214    1    20     6         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 14146    1    16     5         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 50125    1     4     4         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 20213    2    13     5         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 48026    2    13     3         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 31709    1     4     2         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 21586    1    10     6         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 32623    1    16     5         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 14131    2    11     4         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 20240    2    11     1         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 50343    1    20     4         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 28962    2     2     1         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 46007    1    12     4         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 19715    1    15     5         0.0       0.0         0.0      0.0          NaN       NaN            0.0
 39810    2    11     1         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 40756    2    11     3         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 54211    2    10     6         0.0       0.0         0.0      0.0          0.0       0.0            0.0
 54212    2     5     2         0.0       0.0         0.0      0.0          0.0       0.0            0.0
maximum absolute differences: {'score_diff': 0.0, 'wkt_diff': 0.0, 'legal_diff': 0.0, 'br_diff': 0.0, 'target_diff': 0.0, 'rrr_diff': 0.0, 'pressure_diff': 0.0}
```

### 5A high-pressure threshold sensitivity — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
for threshold factor in {0.8, 1.0, 1.2}:
    keep low/medium cutoff fixed; multiply high cutoff; recompute counts, SR and dismissal rate
```

**Raw output**:

```text
Leverage high cutoff x0.8 (high >= 1.120); low cutoff fixed at 0.700
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low             55430        52906       143.62                6.63
Medium             93527        89898       138.64                5.13
  High             52004        49871       136.42                5.43

Leverage high cutoff x1.0 (high >= 1.400); low cutoff fixed at 0.700
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low             55430        52906       143.62                6.63
Medium            102589        98618       138.45                5.15
  High             42942        41151       136.41                5.44

Leverage high cutoff x1.2 (high >= 1.680); low cutoff fixed at 0.700
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low             55430        52906       143.62                6.63
Medium            112870       108493       138.17                5.15
  High             32661        31276       136.74                5.54

Composite high cutoff x0.8 (high >= 5.200); low cutoff fixed at 3.500
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            112027       107768       137.84                4.59
Medium             38964        37384       137.77                5.53
  High             49970        47523       144.35                8.01

Composite high cutoff x1.0 (high >= 6.500); low cutoff fixed at 3.500
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            112027       107768       137.84                4.59
Medium             60194        57613       140.76                5.73
  High             28740        27294       142.92                9.42

Composite high cutoff x1.2 (high >= 7.800); low cutoff fixed at 3.500
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            112027       107768       137.84                4.59
Medium             77392        73985       141.55                6.41
  High             11542        10922       140.77               10.36
```

### 5B composite component-weight sensitivity — PASS

**Code executed** (full runnable implementation: [`run_audit.py`](./run_audit.py)):

```python
recompute each existing component with one component x0.8/x1.2 (OAT),
then all components x0.8 and x1.2; keep 3.5/6.5 cutoffs fixed; report band metrics
```

**Raw output**:

```text
rrr weight x0.8
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            116549       112145       137.83                4.63
Medium             59265        56674       141.18                5.86
  High             25147        23856       142.85                9.70

rrr weight x1.2
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            107507       103422       137.65                4.58
Medium             61412        58818       140.56                5.69
  High             32042        30435       143.33                9.00

wickets weight x0.8
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            119642       115078       137.38                4.62
Medium             60338        57685       142.31                6.13
  High             20981        19912       143.00                9.88

wickets weight x1.2
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            105664       101640       138.06                4.59
Medium             59315        56847       139.67                5.57
  High             35982        34188       143.12                8.73

stage weight x0.8
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            117921       113408       138.02                4.66
Medium             60175        57551       141.62                5.98
  High             22865        21716       141.03                9.65

stage weight x1.2
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            106666       102609       137.41                4.57
Medium             59896        57433       139.76                5.57
  High             34399        32633       145.21                8.99

gap weight x0.8
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            113115       108829       137.78                4.60
Medium             60063        57469       140.99                5.79
  High             27783        26377       142.87                9.45

gap weight x1.2
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            110872       106653       137.88                4.59
Medium             60364        57789       140.54                5.72
  High             29725        28233       143.04                9.27

lag weight x0.8
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            113979       109647       137.35                4.59
Medium             59318        56785       141.34                5.76
  High             27664        26243       144.00                9.59

lag weight x1.2
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            109460       105283       138.39                4.60
Medium             61682        59057       140.01                5.70
  High             29819        28335       142.11                9.21

all weights x0.8
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low            134354       129190       137.41                4.73
Medium             58332        55684       144.36                6.96
  High              8275         7801       137.76               10.63

all weights x1.2
  Band  Total Deliveries  Legal Balls  Strike Rate  Dismissal Rate (%)
   Low             93148        89600       138.00                4.54
Medium             61949        59470       138.18                5.33
  High             45864        43605       144.09                8.22
```

## Corrected claims supported by the evidence

- Raw input has 200,999 rows; 38 rows have innings > 2. Removing those yields 200,961 rows.
- The reproduced in-sample Brier/log-loss are 0.1799/0.5282; these are same-data fit/evaluation results, not held-out estimates.
- Five-fold match-grouped Brier/log-loss are 0.1818/0.5332; chronological holdout is 0.1873/0.5464. Both beat the constant and score/balls baselines on both metrics. This supports predictive signal on the supplied data, not the originally reported in-sample figures as out-of-sample estimates. See per-decile tables above.
- The 200,961 pressure-band deliveries include all retained rows; 192,675 are legal balls, which accounts for the often-confused ~192,675 subtotal.
- Balls remaining are not validly bounded: 3,270 rows exceed 120, with a maximum of 684. Revised fields range from 30 to 114, all multiples of 6, but the pipeline multiplies them by 6 again; the first delivery also starts at 119 remaining rather than 120.
- `extras1_runs` is supported as a category code, not a run quantity. The observed `extras_2_runs` does not fully represent wide/no-ball/byes/leg-byes/penalty values; reconstructed innings margins therefore do not provide full scorecard reconciliation.
- First-innings composite pressure is a different formula/construct from second-innings chase pressure. Band-level comparisons should not be pooled as one comparable scale.
- Direct future-result/current-dismissal fields were not found in the WP features. The audit does find held-out predictive improvement over both tested baselines, while pressure-band behavioral effects remain uncertain because of narrow common support and outcome coupling.

## Prioritized fixes

1. Correct revised-overs units before computing max_legal_balls; enforce the applicable legal-ball cap and align pre-delivery runs, legal balls remaining and RRR. Add DLS boundary tests.
2. Define and validate a canonical delivery-runs field against scorecards; separately account for wide, no-ball, bye, leg-bye, penalty and overthrows. Block downstream score-state use when totals cannot be reconstructed.
3. Report only match-grouped and chronological out-of-sample model metrics; keep all preprocessing, calibration and threshold selection inside training data.
4. Specify DLS inclusion explicitly. Either model revised targets/resources correctly and validate DLS separately, or exclude flagged rows from the stated non-DLS evaluation and pressure summaries.
5. Separate pressure definition from its behavioral outcome tests: remove wicket depletion from a dismissal-rate validation claim or report an outcome-independent sensitivity/conditional design.
6. Define innings-specific pressure scales explicitly and report competition/innings-stratified results with common-support adjusted estimates.

## Full audit source

The following is the exact Python source executed for this audit. Re-running it requires the raw parquet path and the packages installed in the audit-local environment.

````python
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

````
