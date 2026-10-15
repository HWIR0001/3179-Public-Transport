"""Turns ABS state boundary shapefiles into small simplified GeoJSON for the maps (uses shp.py)."""
import sys, json, os
sys.path.insert(0, "/tmp/claude-0/-home-claude/b963723c-c8bf-54d5-a5f0-629084236edb/scratchpad/scripts")
import shp
D = "/home/claude/dashboard/data/"
rows = shp.read_dbf("/tmp/s/ste/STE_2026_AUST_GDA2020.dbf")
items = shp.read_shp("/tmp/s/ste/STE_2026_AUST_GDA2020.shp", eps=0.02, pre=8, dec=2, minarea=0.02)
items = [(i, r) for i, r in items if rows[i]["STE_CODE26"] in list("12345678")]
json.dump(shp.to_geojson(items, rows, ["STE_CODE26", "STE_NAME26"]), open(D + "australia_states.json", "w"), separators=(",", ":"))
p = shp.read_dbf("/tmp/s/poa/POA_2026_AUST_GDA2020.dbf")
W = {"melb_poa": (144.4, -38.5, 145.7, -37.3), "syd_poa": (150.5, -34.3, 151.5, -33.4), "seq_poa": (152.7, -28.3, 153.7, -26.9)}
for k, w in W.items():
    it = shp.read_shp("/tmp/s/poa/POA_2026_AUST_GDA2020.shp", window=w, eps=0.0012, pre=3, dec=3)
    json.dump(shp.to_geojson(it, p, ["POA_CODE26"]), open(D + k + ".json", "w"), separators=(",", ":"))
