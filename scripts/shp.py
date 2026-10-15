"""Tiny shapefile reader (no GIS libraries): read_shp/read_dbf, plus rdp() to simplify lines so map files stay small."""
import struct, json, sys, numpy as np

def read_dbf(path):
    b = open(path, 'rb').read()
    n, hl, rl = struct.unpack('<xxxxIHH', b[:12])
    fields = []; o = 32
    while b[o] != 0x0D:
        name = b[o:o+11].split(b'\0')[0].decode(); ln = b[o+16]; fields.append((name, ln)); o += 32
    rows = []
    for i in range(n):
        r = b[hl+i*rl:hl+(i+1)*rl]; p = 1; d = {}
        for name, ln in fields:
            d[name] = r[p:p+ln].decode('utf-8', 'replace').strip(); p += ln
        rows.append(d)
    return rows

def rdp(pts, eps):
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts)-1)]
    while stack:
        a, b = stack.pop()
        if b <= a+1: continue
        p0, p1 = pts[a], pts[b]; v = p1-p0; L = np.hypot(*v)
        q = pts[a+1:b]-p0
        d = np.abs(v[0]*q[:, 1]-v[1]*q[:, 0])/L if L > 0 else np.hypot(q[:, 0], q[:, 1])
        i = int(np.argmax(d))
        if d[i] > eps:
            k = a+1+i; keep[k] = True; stack += [(a, k), (k, b)]
    return pts[keep]

def read_shp(path, window=None, eps=0.01, pre=1, dec=3, minarea=0.0):
    """yield (index, [rings]) simplified; window=(minx,miny,maxx,maxy) filters on record bbox."""
    f = open(path, 'rb'); f.seek(100); idx = 0; out = []
    data = f.read(); o = 0
    while o < len(data):
        rn, cl = struct.unpack('>ii', data[o:o+8]); o += 8
        rec = data[o:o+cl*2]; o += cl*2
        st = struct.unpack('<i', rec[:4])[0]
        if st == 5:
            bb = struct.unpack('<4d', rec[4:36])
            if window and (bb[2] < window[0] or bb[0] > window[2] or bb[3] < window[1] or bb[1] > window[3]):
                idx += 1; continue
            npart, npts = struct.unpack('<ii', rec[36:44])
            parts = list(struct.unpack(f'<{npart}i', rec[44:44+4*npart])) + [npts]
            pts = np.frombuffer(rec, '<f8', npts*2, 44+4*npart).reshape(-1, 2)
            rings = []
            for a, b in zip(parts[:-1], parts[1:]):
                r = pts[a:b]
                if pre > 1 and len(r) > 200:
                    r = np.vstack([r[:-1:pre], r[-1:]])
                r = rdp(r, eps)
                if len(r) < 4: continue
                area = abs(np.sum(r[:-1, 0]*r[1:, 1]-r[1:, 0]*r[:-1, 1]))/2
                if area < minarea: continue
                rings.append(np.round(r, dec).tolist())
            out.append((idx, rings))
        idx += 1
    return out

def to_geojson(items, rows, keep):
    """Shapefile exterior rings run clockwise and holes counter-clockwise, which is also what d3-geo (Vega) expects."""
    feats = []
    for i, rings in items:
        polys = []
        for r in rings:
            a = np.array(r)
            area = np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1]) / 2
            if area <= 0 or not polys:      # clockwise (or first ring): new polygon
                polys.append([r])
            else:                           # counter-clockwise: hole in the last polygon
                polys[-1].append(r)
        if polys:
            feats.append({'type': 'Feature', 'properties': {k: rows[i][k] for k in keep},
                          'geometry': {'type': 'MultiPolygon', 'coordinates': polys}})
    return {'type': 'FeatureCollection', 'features': feats}
