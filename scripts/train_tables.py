"""Summary tables for the dashboard from train_agg.pkl / train_trips.pkl (made by train_agg.py)."""
import pandas as pd, numpy as np
W = '/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/work/'
OUT = '/home/claude/dashboard/data/'
a = pd.read_pickle(W + 'train_agg.pkl'); t = pd.read_pickle(W + 'train_trips.pkl')
lab = {'Normal Weekday': 'Weekday', 'School Holiday': 'Weekday in school holidays', 'Saturday': 'Saturday', 'Sunday': 'Sunday', 'Public Holiday': 'Public holiday'}
for d in (a, t): d['day'] = d.Day_Type.map(lab); d['h'] = np.where(d.hour < 4, d.hour + 24, d.hour)   # after-midnight trains sit at the end of the day

# 1. share of the day's boardings by hour and day type
x = a.groupby(['Business_Date', 'day', 'h'], as_index=False).boardings.sum()
m = x.groupby(['day', 'h']).boardings.sum().reset_index()
days = x.groupby('day').Business_Date.nunique()
m['avg'] = m.boardings / m.day.map(days)
m['share_pct'] = (m.avg / m.groupby('day').avg.transform('sum') * 100).round(2)
full = pd.MultiIndex.from_product([lab.values(), range(4, 28)], names=['day', 'h']).to_frame(index=False)
m = full.merge(m, how='left').fillna(0)
m.rename(columns={'h': 'hour'})[['day', 'hour', 'share_pct']].to_csv(OUT + 'train_hourly_daytype.csv', index=False)

# 2. weekday: line x hour share of the line's own boardings, ordered by how peaky the line is
w = a[a.day == 'Weekday']
lh = w.groupby(['Line_Name', 'h'], as_index=False).boardings.sum()
lh['share_pct'] = (lh.boardings / lh.groupby('Line_Name').boardings.transform('sum') * 100).round(2)
peak = lh[lh.h.isin([7, 8, 15, 16, 17])].groupby('Line_Name').share_pct.sum().rename('peak_share')
lh = lh.merge(peak, on='Line_Name')
lh = lh[lh.Line_Name != 'Stony Point']
lh.rename(columns={'Line_Name': 'line', 'h': 'hour'})[['line', 'hour', 'share_pct', 'peak_share']].round(1).to_csv(OUT + 'train_line_hour.csv', index=False)

# 3. tidal flow: weekday boardings towards the city (Up) and away from it (Down), as % of the weekday total
dd = w.groupby(['Direction', 'h'], as_index=False).boardings.sum()
dd['share_pct'] = dd.boardings / dd.boardings.sum() * 100
dd['share_signed'] = np.where(dd.Direction == 'D', -dd.share_pct, dd.share_pct).round(2)
dd['direction'] = dd.Direction.map({'U': 'Towards the city', 'D': 'Away from the city'})
dd.rename(columns={'h': 'hour'})[['direction', 'hour', 'share_signed']].to_csv(OUT + 'train_tidal.csv', index=False)

# 4. each line's share of weekday boardings
ls = w.groupby('Line_Name', as_index=False).boardings.sum()
ls['share_pct'] = (ls.boardings / ls.boardings.sum() * 100).round(2)
ls.merge(peak.reset_index(), on='Line_Name').rename(columns={'Line_Name': 'line'})[['line', 'share_pct', 'peak_share']].round(1).sort_values('share_pct', ascending=False).to_csv(OUT + 'train_line_share.csv', index=False)

# 5. crowding: busiest point on each weekday train, averaged by line and hour the train passes it
tw = t[(t.day == 'Weekday') & (t.Line_Name != 'Stony Point')]
cl = tw.groupby(['Line_Name', 'h'], as_index=False).agg(load=('Passenger_Departure_Load', 'mean'), n=('Passenger_Departure_Load', 'size'))
cl = cl[cl.n >= 20]
cl['load'] = cl.load.round(0)
cl = cl.merge(peak.reset_index(), on='Line_Name')
cl.rename(columns={'Line_Name': 'line', 'h': 'hour'})[['line', 'hour', 'load', 'n', 'peak_share']].to_csv(OUT + 'train_line_load.csv', index=False)
print(m.groupby('day').share_pct.sum().round(1).to_dict())
print(ls.sort_values('share_pct', ascending=False).head(5)); print(peak.sort_values().round(1).to_dict())
print('AM+PM peak share weekday', m[(m.day == 'Weekday') & m.hour.isin([7, 8, 15, 16, 17])].share_pct.sum().round(1))
print('school hol', m[(m.day == 'Weekday in school holidays') & m.hour.isin([7, 8, 15, 16, 17])].share_pct.sum().round(1))
print(dd[dd.h.isin([7, 8, 17])][['direction', 'h', 'share_signed']] if 'h' in dd else dd.head())
print(cl.sort_values('load', ascending=False).head(5))
