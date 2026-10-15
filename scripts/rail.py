"""Decodes the Brisbane rail-line topojson, keeps South East Queensland and simplifies it -> data/bris_rail.geojson."""
import json, io, zipfile, math, sys
import numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/scripts')
from shp import rdp
RAW = '/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/raw/Data/'
OUT = '/home/claude/dashboard/data/'

def runs(pts, win):
    """split a polyline into runs that stay inside the window"""
    inside = ((pts[:, 0] >= win[0]) & (pts[:, 0] <= win[2]) & (pts[:, 1] >= win[1]) & (pts[:, 1] <= win[3]))
    out, cur = [], []
    for p, ok in zip(pts, inside):
        if ok: cur.append(p)
        elif cur:
            out.append(np.array(cur)); cur = []
    if cur: out.append(np.array(cur))
    return [r for r in out if len(r) > 1]

def finish(lines, name, eps, dec=4):
    seen, res = set(), []
    for l in lines:
        s = rdp(l, eps).round(dec)
        key = tuple(map(tuple, s.tolist()))
        rkey = key[::-1]
        if key in seen or rkey in seen or len(s) < 2: continue
        seen.add(key); res.append(s.tolist())
    json.dump({'type': 'Feature', 'properties': {}, 'geometry': {'type': 'MultiLineString', 'coordinates': res}},
              open(OUT + name, 'w'), separators=(',', ':'))
    print(name, len(res), 'lines')

# ---- Sydney (EPSG:3857 -> lon/lat)
R = 6378137.0
win = (150.55, -34.25, 151.45, -33.45)
d = json.load(open(RAW + 'New South Wales/sydneytrains.json'))
lines = []
for r in d:
    g = r['json_geometry']; g = json.loads(g) if isinstance(g, str) else g
    segs = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
    for seg in segs:
        a = np.array(seg, float)[:, :2]
        lon = np.degrees(a[:, 0] / R); lat = np.degrees(np.arctan(np.sinh(a[:, 1] / R)))
        lines += runs(np.column_stack([lon, lat]), win)
finish(lines, 'syd_rail.json', 0.0004)

# ---- Melbourne metro trains from the GTFS shapes
outer = zipfile.ZipFile(RAW + 'Victoria/gtfs.zip')
inner = zipfile.ZipFile(io.BytesIO(outer.read('2/google_transit.zip')))
routes = pd.read_csv(inner.open('routes.txt'), dtype=str, encoding='utf-8-sig')
rail = routes[routes.route_type.isin(['400', '2', '1']) & ~routes.route_long_name.fillna('').str.contains('Replacement|Bus', case=False)
              & ~routes.route_short_name.fillna('').str.contains('Replacement|Bus', case=False)]
print('rail routes', len(rail))
trips = pd.read_csv(inner.open('trips.txt'), dtype=str, usecols=['route_id', 'shape_id', 'direction_id'], encoding='utf-8-sig')
rt = trips[trips.route_id.isin(rail.route_id)].dropna(subset=['shape_id'])
ids = set(rt.shape_id)
shape_key = rt.drop_duplicates('shape_id').set_index('shape_id')[['route_id', 'direction_id']]
print('shape ids', len(ids))
sh = []
for ch in pd.read_csv(inner.open('shapes.txt'), dtype={'shape_id': str}, usecols=['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'],
                      encoding='utf-8-sig', chunksize=500000):
    sh.append(ch[ch.shape_id.isin(ids)])
sh = pd.concat(sh)
win = (144.3, -38.4, 145.8, -37.3)
cand = {}
for sid, g in sh.groupby('shape_id'):
    g = g.sort_values('shape_pt_sequence')
    pts = np.column_stack([g.shape_pt_lon.astype(float), g.shape_pt_lat.astype(float)])
    k = tuple(shape_key.loc[sid])
    if k not in cand or len(pts) > len(cand[k]): cand[k] = pts
cells = lambda ps: {(round(x, 3), round(y, 3)) for p in ps for x, y in p}
allpts = [np.column_stack([g.shape_pt_lon.astype(float), g.shape_pt_lat.astype(float)]) for _, g in sh.groupby('shape_id')]
full = cells(allpts); lines = []
for pts in cand.values(): lines += runs(pts, win)
print('kept', len(cand), 'coverage', len(cells(cand.values())) / len(full))
finish(lines, 'melb_rail.json', 0.0004)
