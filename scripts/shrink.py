"""Data reduction: raw open-data files -> the small CSVs in data/. Sections are numbered; each says what it makes.
Raw files are not in the repository (too big); see the data sources in the page footer."""
import json, re, sys, math, zipfile, subprocess
import numpy as np, pandas as pd
RAW='/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/raw/Data/'
OUT='/home/claude/dashboard/data/'
O='/mnt/user-data/outputs/'

# ---- 1. BITRE sets (already small) -------------------------------------
# BITRE national tables are already small: just copy the needed columns.
t=pd.read_csv(O+'upt_national_mode_share.csv'); t['trips_million']=t.trips_million.round(1); t.to_csv(OUT+'national_mode_share.csv',index=False)
t=pd.read_csv(O+'upt_city_mode_long.csv'); t['trips_million']=t.trips_million.round(1); t.to_csv(OUT+'city_mode_long.csv',index=False)
pd.read_csv(O+'upt_city_totals_recovery.csv').round(1).to_csv(OUT+'city_totals_recovery.csv',index=False)
pd.read_csv(O+'upt_city_mode_recovery_2024_25.csv').to_csv(OUT+'city_mode_recovery.csv',index=False)
pd.read_csv(O+'upt_city_latest_for_map.csv').to_csv(OUT+'city_map.csv',index=False)
pd.read_csv(O+'city_car_vs_pt_pkm_2018_19_and_2024_25.csv').to_csv(OUT+'car_vs_pt.csv',index=False)
pd.read_csv(O+'city_per_capita_2024_25.csv').to_csv(OUT+'per_capita.csv',index=False)

# ---- 2. Population over time (ABS) joined to BITRE trips ----------------
# Population (ABS) is joined to trips so we can compute trips PER RESIDENT.
x=pd.read_excel(RAW+'Population/32180DS0003_2001-25.xlsx','Table 1',header=5)
x.columns=[str(c).strip() for c in x.columns]
gcol=[c for c in x.columns if c.startswith('GCCSA name')][0]
ycols=list(x.columns[10:35]); x=x.rename(columns=dict(zip(ycols,[str(2001+i) for i in range(25)]))); years=[str(2001+i) for i in range(25)]
for c in years: x[c]=pd.to_numeric(x[c],errors='coerce')
print('pop years',years[0],years[-1], x[gcol].dropna().unique()[:30])
m={'Greater Sydney':'Sydney','Greater Melbourne':'Melbourne','Greater Brisbane':'Brisbane','Greater Adelaide':'Adelaide','Greater Perth':'Perth','Greater Hobart':'Hobart','Greater Darwin':'Darwin','Australian Capital Territory':'Canberra'}
p=x[x[gcol].isin(m)].copy(); p['city']=p[gcol].map(m)
p=p.groupby('city')[years].sum().reset_index().melt('city',var_name='year_end',value_name='population'); p['year_end']=p.year_end.astype(int)
tot=pd.read_csv(O+'upt_city_totals_recovery.csv')[['city','year_end','total_trips_million']]
pt=p.merge(tot,on=['city','year_end'],how='left')
pt['trips_per_person']=(pt.total_trips_million*1e6/pt.population).round(1)
base=pt[pt.year_end==2001].set_index('city')
pt['pop_index']=(pt.population/pt.city.map(base.population)*100).round(1)
pt['trips_index']=(pt.total_trips_million/pt.city.map(base.total_trips_million)*100).round(1)
pt[['city','year_end','population','total_trips_million','trips_per_person','pop_index','trips_index']].to_csv(OUT+'city_pop_trips.csv',index=False)
chk=pt[pt.year_end==2025].set_index('city').population; print('ERP 2025',chk.to_dict(), chk.sum())

# ---- 3. Monthly: Melbourne (DTP) and Sydney (TfNSW) ---------------------
# Monthly trips by mode for Melbourne (Victoria DTP) and Sydney (TfNSW), used for the 2019 = 100 index.
v=pd.read_csv(RAW+'Victoria/monthly_public_transport_patronage_by_mode.csv')
v.columns=[c.strip() for c in v.columns]
for c in v.columns[3:]:
    v[c]=pd.to_numeric(v[c].astype(str).str.extract(r'^(\d+)')[0],errors='coerce')
v['month']=pd.to_datetime(dict(year=v.Year,month=v.Month,day=1))
mv=v.melt('month',value_vars=['Metropolitan train','Metropolitan tram','Metropolitan bus'],var_name='m',value_name='trips')
mv['city']='Melbourne'; mv['mode']=mv.m.map({'Metropolitan train':'Train','Metropolitan tram':'Tram','Metropolitan bus':'Bus'})
n=pd.read_csv(RAW+'New South Wales/all_modes.csv'); n['mode']=n.Travel_Mode.str.lower().map({'bus':'Bus','ferry':'Ferry','light rail':'Tram','train':'Train','metro':'Train'})
n=n.dropna(subset=['mode']); n['month']=pd.to_datetime(n.Year_Month,format='%b-%Y')
mn=n.groupby(['month','mode'],as_index=False).Trip.sum().rename(columns={'Trip':'trips'}); mn['city']='Sydney'
mm=pd.concat([mv[['city','month','mode','trips']],mn])
b19=mm[mm.month.dt.year==2019].groupby(['city','mode']).trips.mean().rename('b19')
mm=mm.join(b19,on=['city','mode']); mm['index_2019']=(mm.trips/mm.b19*100).round(1)
mm['trips_million']=(mm.trips/1e6).round(3); mm['month']=mm.month.dt.strftime('%Y-%m-%d')
mm.loc[(mm.city=='Sydney')&(mm['mode']=='Tram'),'index_2019']=np.nan  # CBD light rail opened Dec 2019: 2019 baseline not comparable
mm=mm.dropna(subset=['index_2019'])
mm[['city','month','mode','trips_million','index_2019']].sort_values(['city','mode','month']).to_csv(OUT+'monthly_city_mode.csv',index=False)
print('monthly',mm.groupby('city').month.agg(['min','max']))

# ---- 4. Victoria day types ----------------------------------------------
d=pd.read_csv(RAW+'Victoria/monthly_average_patronage_by_day_type_and_by_mode.csv')
print(d.Day_type.unique(), d.Mode.unique())
d['grp']=np.where(d.Day_type=='Weekend','Weekend','Weekday')
dd=d[d.Mode.isin(['MetroTrain','Tram','MetroBus'])].groupby(['Year','Mode','grp'],as_index=False).Pax_daily.mean()
dd['Mode']=dd.Mode.map({'MetroTrain':'Train','Tram':'Tram','MetroBus':'Bus'}); dd['Pax_daily']=dd.Pax_daily.round(0).astype(int)
dd.rename(columns={'Year':'year','Mode':'mode','grp':'day','Pax_daily':'avg_daily_trips'}).to_csv(OUT+'melb_daytype.csv',index=False)

# ---- 5. Stations --------------------------------------------------------
# Station entries (Sydney, Melbourne) with coordinates for the station maps.
s=pd.read_csv(RAW+'Victoria/annual_metropolitan_train_station_entries_fy_2024_2025.csv')
s=s.rename(columns={'Stop_name':'station','Stop_lat':'lat','Stop_long':'lon','Pax_annual':'entries'})[['station','lat','lon','entries']]
s['lat']=s.lat.round(4); s['lon']=s.lon.round(4); s.to_csv(OUT+'melb_stations.csv',index=False)

e=pd.read_csv(RAW+'New South Wales/entry_exit.csv'); e=e[e.Entry_Exit=='Entry'].copy()
e['Trip']=pd.to_numeric(e.Trip,errors='coerce').fillna(0)
e['date']=pd.to_datetime(e.MonthYear); last=e.date.max(); first=last-pd.DateOffset(months=11)
e=e[(e.date>=first)&(e.date<=last)]
e['key']=e.Station.str.replace(r'\s+',' ',regex=True).str.strip().str.lower().str.replace(r' (station|light rail|metro)$','',regex=True)
g=e.groupby(['key','Station_Type'],as_index=False).Trip.sum()
l=pd.read_csv(RAW+'New South Wales/locationfacilitydata.csv',usecols=['LOCATION_NAME','LATITUDE','LONGITUDE'])
l['key']=l.LOCATION_NAME.str.replace(r'\s+',' ',regex=True).str.strip().str.lower().str.replace(r' (station|light rail stop|light rail|metro station|metro)$','',regex=True)
l=l.drop_duplicates('key')
alias={'central chalmers street':'central','central grand concourse':'central','domestic':'domestic airport','international':'international airport'}
g['key']=g.key.replace(alias); g['Station_Type']=g.Station_Type.replace({'Metro Shared':'Train'}); g=g.groupby(['key','Station_Type'],as_index=False).Trip.sum()
j=g.merge(l,on='key',how='left'); print('sydney unmatched',j.LATITUDE.isna().sum(),'of',len(j), j[j.LATITUDE.isna()].sort_values('Trip',ascending=False).head(8)[['key','Station_Type','Trip']].values.tolist())
j=j.dropna(subset=['LATITUDE'])
j['Station_Type']=j.Station_Type.replace({'Metro Shared':'Metro'})
j['key']=j.key.str.title().str.replace("'S","'s")
j.rename(columns={'key':'station','Station_Type':'mode','LATITUDE':'lat','LONGITUDE':'lon','Trip':'entries'})[['station','mode','lat','lon','entries']].assign(lat=lambda f:f.lat.round(4),lon=lambda f:f.lon.round(4),entries=lambda f:f.entries.astype(int)).to_csv(OUT+'syd_stations.csv',index=False)
print('syd window',first.date(),last.date())

# ---- 6. Adelaide daily validations -------------------------------------
# Adelaide Metrocard validations: daily totals for the calendar heatmap (counts come in bands of ten, so they understate use).
a=pd.read_csv(RAW+'South Australia/banded-adelaide-metrocard-validations-2026-q2.csv',encoding='utf-8-sig',usecols=['VALIDATION_DATE','BAND_BOARDINGS_FLOOR'])
a['date']=pd.to_datetime(a.VALIDATION_DATE,format='%d/%m/%Y')
ad=a.groupby('date',as_index=False).BAND_BOARDINGS_FLOOR.sum().rename(columns={'BAND_BOARDINGS_FLOOR':'validations_min'})
ad['date']=ad.date.dt.strftime('%Y-%m-%d'); ad['weekday']=pd.to_datetime(ad.date).dt.day_name()
dt=pd.to_datetime(ad.date)
ad['week_start']=(dt-pd.to_timedelta(dt.dt.dayofweek,unit='D')).dt.strftime('%Y-%m-%d')
hol={'2026-04-03':'Good Friday','2026-04-06':'Easter Monday','2026-04-25':'Anzac Day','2026-06-08':"King's Birthday"}
ad['holiday']=ad.date.map(hol).fillna('')
ad.to_csv(OUT+'adelaide_daily.csv',index=False); print(ad.describe())

# ---- 7. Melbourne stops (topojson -> csv) ------------------------------
# Melbourne stops: topojson decoded to a tiny lon/lat/mode CSV.
tp=json.load(open(RAW+'Victoria/public_transport_stops.topojson'))
sc,tr=tp['transform']['scale'],tp['transform']['translate']
rows=[]
for g in tp['objects']['features']['geometries']:
    c=g['coordinates']; rows.append((g['properties']['MODE'],c[0]*sc[0]+tr[0],c[1]*sc[1]+tr[1]))
f=pd.DataFrame(rows,columns=['m','lon','lat'])
print('vic raw coord sample',f.head(2).values.tolist())
f=f[f.m.isin(['METRO BUS','METRO TRAM','METRO TRAIN'])]
f=f[f.lon.between(144.4,145.6)&f.lat.between(-38.5,-37.4)]
f['mode']=f.m.map({'METRO BUS':'Bus','METRO TRAM':'Tram','METRO TRAIN':'Train'})
f['lat']=f.lat.round(4); f['lon']=f.lon.round(4)
f[['mode','lat','lon']].drop_duplicates().sort_values(['mode','lat','lon']).to_csv(OUT+'melb_stops.csv',index=False)
print(f['mode'].value_counts().to_dict())

# ---- 8. Brisbane stops via GTFS ----------------------------------------
# South East Queensland stops: built from GTFS (superseded by seq_boardings.py, which also adds July 2026 boardings).
import os
if not os.path.exists(OUT+'bris_stops.csv'): subprocess.run([sys.executable,'-I','/mnt/user-data/outputs/prepare_data.py','stops',RAW+'Queensland/SEQ_GTFS.zip','--out',OUT+'bris_stops.csv','--bbox','152.8','-28.2','153.6','-27.0','--collapse-parents'],check=True)

# ---- 9. Brisbane rail lines: decode, filter, simplify -------------------
# Brisbane rail lines: decode the topojson, keep the SEQ area, simplify the geometry to keep the file small.
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=pts[0],pts[-1]; ab=b-a; L=np.hypot(*ab)
    q=pts-a; d=np.abs(ab[0]*q[:,1]-ab[1]*q[:,0])/L if L>0 else np.hypot(*(pts-a).T)
    i=int(np.argmax(d))
    if d[i]>eps: return np.vstack([rdp(pts[:i+1],eps)[:-1],rdp(pts[i:],eps)])
    return np.vstack([a,b])
tp=json.load(open(RAW+'Queensland/railway-line-locations.topojson'))
sc,tr=tp['transform']['scale'],tp['transform']['translate']
arcs=[]
for arc in tp['arcs']:
    a_=np.array(arc,dtype=float).cumsum(axis=0); a_[:,0]=a_[:,0]*sc[0]+tr[0]; a_[:,1]=a_[:,1]*sc[1]+tr[1]; arcs.append(a_)
def geom_arcs(idx):
    pts=[]
    for i in idx:
        a_=arcs[i] if i>=0 else arcs[~i][::-1]
        pts.append(a_ if not pts else a_[1:])
    return np.vstack(pts)
lines=[]
for g in tp['objects']['features']['geometries']:
    if g['properties'].get('status')!='Operational': continue
    segs=[g['arcs']] if g['type']=='LineString' else g['arcs']
    for s_ in segs:
        c=geom_arcs(s_)
        if c[:,0].max()<152.8 or c[:,0].min()>153.6 or c[:,1].max()<-28.2 or c[:,1].min()>-27.0: continue
        c=rdp(c,0.0004); lines.append([[round(float(x),4),round(float(y),4)] for x,y in c])
json.dump({'type':'Feature','properties':{},'geometry':{'type':'MultiLineString','coordinates':lines}},open(OUT+'bris_rail.geojson','w'),separators=(',',':'))
print('rail segs',len(lines))

# ---- 10. Melbourne lines: split each station's 2024-25 entries across the lines that serve it
# Melbourne lines: a station's entries are shared across the lines serving it, in proportion to each line's loads.
tb = pd.read_csv(RAW+'Victoria/Train_Boardings.csv', sep=';')
tb['Boardings'] = pd.to_numeric(tb.Boardings, errors='coerce')
share = tb.groupby(['Station_Name', 'Line_Name'], as_index=False).Boardings.mean()
share['w'] = share.Boardings / share.groupby('Station_Name').Boardings.transform('sum')
nl = share.groupby('Station_Name').Line_Name.transform('nunique')
share['kind'] = np.where(nl == 1, 'Only this line', 'Shared with other lines')
ent = pd.read_csv(RAW+'Victoria/annual_metropolitan_train_station_entries_fy_2024_2025.csv')[['Stop_name', 'Pax_annual']]
j = share.merge(ent, left_on='Station_Name', right_on='Stop_name')
j['est'] = j.w * j.Pax_annual / 1e6
ml = j.groupby(['Line_Name', 'kind'], as_index=False).est.sum().round(2).rename(columns={'Line_Name': 'line', 'est': 'entries_million'})
ml.to_csv(OUT+'melb_lines.csv', index=False)
print('lines total', ml.entries_million.sum(), ent.Pax_annual.sum()/1e6)

# ---- 11. Time of day: Canberra boardings by hour (pre-COVID months) and Melbourne train time bands
# Canberra boardings by hour (2019-20 and 2020-21, July-Feb) and Melbourne train time bands.
import re
# Both files are summed over stops themselves (cells use "." as a thousands separator, e.g. "1.267").
MONTHS = ['July', 'August', 'September', 'October', 'November', 'December', 'January', 'February']
def ca_hours(path, label):
    d = pd.read_csv(path, low_memory=False, dtype=str)
    d = d[d['Stop ID'] != 'Total']
    def num(x):
        if pd.isna(x): return 0.0
        x = x.strip().replace(',', '')
        return float(x.replace('.', '')) if re.fullmatch(r'\d{1,3}(\.\d{3})+', x) else float(x)
    acc = {}
    for c in d.columns:
        # headers read "July 2019 12:00:00 AM" (2019-20) or "2020 July 12:00:00 AM" (2020-21); some years are mislabelled, so match on month name only
        m = re.match(r'^(?:20\d\d )?([A-Za-z]+)(?: 20\d\d)? (\d\d):\d\d:\d\d ([AP]M)$', c)
        if not m or m.group(1) not in MONTHS: continue
        h = int(m.group(2)) % 12 + (12 if m.group(3) == 'PM' else 0)
        acc[h] = acc.get(h, 0) + d[c].map(num).sum()
    hr = pd.Series(acc).reindex(range(24), fill_value=0)
    hr = hr[hr.index > 0]   # the midnight bucket looks like a placeholder for records with no time
    return pd.DataFrame({'period': label, 'hour': hr.index, 'share_pct': (hr / hr.sum() * 100).round(2).values, 'boardings': hr.values})
P = RAW + 'Australia Capital Territory/'
hr = pd.concat([ca_hours(P + 'Boardings_by_Stop_by_Hour_2019_-_2020_20261014.csv', 'July-Feb 2019-20'),
                ca_hours(P + 'Boardings_by_Stop_by_Hour_2020_-_2021_20261015.csv', 'July-Feb 2020-21')])
hr[['period', 'hour', 'share_pct']].to_csv(OUT+'canberra_hourly.csv', index=False)
print(hr.groupby('period').boardings.sum())
print(hr.pivot(index='hour', columns='period', values='share_pct').to_string())
st = pd.read_csv(RAW+'Victoria/annual_metropolitan_train_station_entries_fy_2024_2025.csv')
bands = [('Before AM peak', 'Pax_pre_AM_peak'), ('AM peak', 'Pax_AM_peak'), ('Inter-peak', 'Pax_interpeak'), ('PM peak', 'Pax_PM_peak'), ('Late evening', 'Pax_PM_late')]
mb = pd.DataFrame({'band': [b for b, _ in bands], 'order': range(5), 'entries': [st[c].sum() for _, c in bands]})
mb['share_pct'] = (mb.entries / mb.entries.sum() * 100).round(1)
mb.to_csv(OUT+'melb_timebands.csv', index=False); print(mb)
print('weekday', st.Pax_norm_weekday.sum(), 'bands', mb.entries.sum(), 'sat', st.Pax_Saturday.sum(), 'sun', st.Pax_Sunday.sum())
