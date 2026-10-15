"""One chunked pass over the 558 MB Melbourne train-load file -> small summary tables."""
import pandas as pd, numpy as np, sys
SRC = sys.argv[1]; OUT = '/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/work/'
use = ['Business_Date', 'Day_Type', 'Mode', 'Train_Number', 'Line_Name', 'Direction', 'Departure_Time_Scheduled',
       'Passenger_Boardings', 'Passenger_Alightings', 'Passenger_Departure_Load']
agg, trips = [], []
for ch in pd.read_csv(SRC, usecols=use, chunksize=500000, encoding='utf-8-sig',
                      dtype={'Train_Number': str, 'Departure_Time_Scheduled': str}):
    ch = ch[(ch.Mode == 'Metro Trains') & ch.Departure_Time_Scheduled.notna()].copy()
    ch['hour'] = ch.Departure_Time_Scheduled.str.slice(0, 2).astype(int) % 24
    agg.append(ch.groupby(['Business_Date', 'Day_Type', 'Line_Name', 'Direction', 'hour'], as_index=False)
               .agg(boardings=('Passenger_Boardings', 'sum'), alightings=('Passenger_Alightings', 'sum')))
    i = ch.groupby(['Business_Date', 'Train_Number', 'Line_Name', 'Direction']).Passenger_Departure_Load.idxmax()
    t = ch.loc[i, ['Business_Date', 'Day_Type', 'Train_Number', 'Line_Name', 'Direction', 'hour', 'Passenger_Departure_Load']]
    trips.append(t)
a = pd.concat(agg).groupby(['Business_Date', 'Day_Type', 'Line_Name', 'Direction', 'hour'], as_index=False).sum()
a.to_pickle(OUT + 'train_agg.pkl')
t = pd.concat(trips)
t = t.loc[t.groupby(['Business_Date', 'Train_Number', 'Line_Name', 'Direction']).Passenger_Departure_Load.idxmax()] if t.index.is_unique else \
    t.sort_values('Passenger_Departure_Load').drop_duplicates(['Business_Date', 'Train_Number', 'Line_Name', 'Direction'], keep='last')
t.to_pickle(OUT + 'train_trips.pkl')
print(a.shape, t.shape, a.Business_Date.min(), a.Business_Date.max(), a.Business_Date.nunique())
print(a.groupby('Day_Type').Business_Date.nunique())
