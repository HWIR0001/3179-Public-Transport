"""SEQ stops with July 2026 boardings (TransLink origin-destination trips), for chart 19.
Output: data/bris_stops.csv  (mode, lat, lon, boardings). Rail platforms are merged into their station."""
import sys, zipfile, pandas as pd
R = '/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/raw/'
OUT = '/home/claude/dashboard/data/bris_stops.csv'
zf = zipfile.ZipFile(R + 'Data/Queensland/SEQ_GTFS.zip')

def mode_of(rt):                       # GTFS route_type -> dashboard mode
    rt = int(rt)
    if rt in (0, 5) or 900 <= rt <= 999: return 'Light rail'
    if rt in (1, 2, 12) or 100 <= rt <= 199 or 400 <= rt <= 499: return 'Heavy rail'
    if rt in (3, 11) or 200 <= rt <= 299 or 700 <= rt <= 899: return 'Bus'
    if rt == 4 or 1000 <= rt <= 1099: return 'Ferry'
    return 'Other'

routes = pd.read_csv(zf.open('routes.txt'), dtype=str, usecols=['route_id', 'route_type'])
routes['mode'] = routes.route_type.map(mode_of)
trips = pd.read_csv(zf.open('trips.txt'), dtype=str, usecols=['trip_id', 'route_id'])
tmode = trips.merge(routes[['route_id', 'mode']], on='route_id').set_index('trip_id')['mode']
pairs = []
for ch in pd.read_csv(zf.open('stop_times.txt'), dtype=str, usecols=['trip_id', 'stop_id'], chunksize=2_000_000):
    ch['mode'] = ch.trip_id.map(tmode)
    pairs.append(ch[['stop_id', 'mode']].dropna().drop_duplicates())
    pairs = [pd.concat(pairs).drop_duplicates()]
pairs = pairs[0]

stops = pd.read_csv(zf.open('stops.txt'), dtype=str, usecols=['stop_id', 'stop_lat', 'stop_lon', 'parent_station'])
stops[['stop_lat', 'stop_lon']] = stops[['stop_lat', 'stop_lon']].apply(pd.to_numeric)
xy = stops.set_index('stop_id')[['stop_lat', 'stop_lon']]
par = stops.parent_station.where(stops.parent_station.isin(xy.index))
stops['key'] = par.fillna(stops.stop_id)                       # station id (parent) or the stop itself
stops['lat'] = xy.loc[stops.key, 'stop_lat'].values
stops['lon'] = xy.loc[stops.key, 'stop_lon'].values

# July 2026 boardings = trips by origin stop
od = pd.read_csv(R + 'qld_od/202607 (Jul) TL Org-Dest Trips.csv', dtype=str, usecols=['ORIGIN_STOP', 'QUANTITY'])
od['q'] = od.QUANTITY.astype(int)
board = od.groupby('ORIGIN_STOP').q.sum().rename('boardings')

m = pairs.merge(stops[['stop_id', 'key', 'lat', 'lon']], on='stop_id').merge(board, left_on='stop_id', right_index=True, how='left')
m['boardings'] = m.boardings.fillna(0)
m = m[m.lon.between(152.6, 153.7) & m.lat.between(-28.3, -26.7)]
g = m.groupby(['key', 'mode'], as_index=False).agg(lat=('lat', 'first'), lon=('lon', 'first'), boardings=('boardings', 'sum'))
g['lat'] = g.lat.round(4); g['lon'] = g.lon.round(4); g['boardings'] = g.boardings.astype(int)
g[['mode', 'lat', 'lon', 'boardings']].sort_values('boardings').to_csv(OUT, index=False)
print(len(g), g.boardings.sum(), 'of', board.sum()); print(g.groupby('mode').agg(n=('lat', 'size'), b=('boardings', 'sum')))
print(g.sort_values('boardings').tail(5))
