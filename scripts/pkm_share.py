"""Public transport share of passenger-km by city and year (BITRE Table 2.3a-h) -> data/car_vs_pt.csv.
Adds each city's COVID-19 low point: the year between 2019-20 and 2022-23 with the lowest public transport share."""
import openpyxl, pandas as pd
RAW = '/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/raw/bitre/2. PASSENGERS.xlsx'
OUT = '/home/claude/dashboard/data/car_vs_pt.csv'
CITIES = ['Sydney', 'Melbourne', 'Brisbane', 'Adelaide', 'Perth', 'Hobart', 'Darwin', 'Canberra']
rows = list(openpyxl.load_workbook(RAW, read_only=True, data_only=True)['Table 2.3a-i'].iter_rows(values_only=True))
out = []
for city in CITIES:
    t = next(i for i, r in enumerate(rows) if r[0] and str(r[0]).startswith('Table 2.3') and str(r[0]).split('\u2014')[-1].strip() == city)
    hdr = rows[t + 1]                    # column names sit one row under the table title
    for r in rows[t + 3:t + 56]:
        if not (r[0] and str(r[0])[:2] in ('19', '20') and '-' in str(r[0])): continue
        d = dict(zip(hdr, r))
        num = lambda v: v if isinstance(v, (int, float)) else 0.0      # blanks and dashes mean no service
        if not isinstance(d['Total'], (int, float)): continue
        pt = sum(num(d[k]) for k in ('Heavy rail', 'Light rail', 'Bus', 'Ferry'))
        out.append({'city': city, 'fy': r[0], 'pt_share': pt / d['Total'] * 100})
d = pd.DataFrame(out)
res = []
for c in CITIES:
    x = d[d.city == c].set_index('fy').pt_share
    covid = x.loc[['2019-20', '2020-21', '2021-22', '2022-23']]
    low = covid.idxmin()
    for period, fy in (('Before', '2018-19'), ('Low point', low), ('After', '2024-25')):
        res.append({'city': c, 'period': period, 'fy': fy, 'pt_share_of_pkm_pct': round(x[fy], 1)})
r = pd.DataFrame(res); r.to_csv(OUT, index=False); print(r.to_string())
