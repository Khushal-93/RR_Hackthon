import pandas as pd
DATA = r'C:\Users\Khushal\Downloads\cricket_ml_parquet\cricket_ml_parquet'
bbb = pd.read_parquet(DATA + r'\ball_by_ball.parquet')

wides = bbb[bbb['extras_type'] == 'wide']
print('Wide deliveries extras_2_runs dist:')
print(wides['extras_2_runs'].value_counts())

nb = bbb[bbb['extras_type'] == 'Overstep']
print('\nNo-ball extras_2_runs dist:')
print(nb['extras_2_runs'].value_counts())

lb = bbb[bbb['extras_type'] == 'legbyes']
print('\nLegbye extras_2_runs dist:')
print(lb['extras_2_runs'].value_counts())

byes = bbb[bbb['extras_type'] == 'byes']
print('\nBye extras_2_runs dist:')
print(byes['extras_2_runs'].value_counts())

ext2 = pd.to_numeric(bbb['extras_2_runs'], errors='coerce').fillna(0)
print('\nTotal extras_2_runs non-zero:', (ext2 > 0).sum())
print('Pct:', round(100*(ext2>0).sum()/len(bbb), 3))
print('\nWide count:', (bbb['extras_type']=='wide').sum())
print('Legbye count:', (bbb['extras_type']=='legbyes').sum())
print('Bye count:', (bbb['extras_type']=='byes').sum())
print('No-ball count:', (bbb['extras_type']=='Overstep').sum())
