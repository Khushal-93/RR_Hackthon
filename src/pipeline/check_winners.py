import pandas as pd
DATA = r'C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet'
mat = pd.read_parquet(DATA + r'\matches.parquet')
for mid in [14123, 20248, 30060, 31254, 29926]:
    row = mat[mat['match_id']==mid]
    if len(row):
        res = row.iloc[0]["result"]
        rt = row.iloc[0]["revised_target"]
        print(f"match {mid}: result='{res}' revised_target={rt}")
