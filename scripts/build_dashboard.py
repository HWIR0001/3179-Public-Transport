"""Build script: reads the reduced CSV/GeoJSON in data/ and writes one Vega-Lite JSON spec per chart into specs/.
Each spec carries a one-line "description" (JSON has no comments). build_page.py then writes index.html."""
import json, os
import pandas as pd

ROOT = '/home/claude/dashboard/'
SPECS = ROOT + 'specs/'
os.makedirs(SPECS, exist_ok=True)

SCHEMA = 'https://vega.github.io/schema/vega-lite/v5.json'
CITIES = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Canberra', 'Hobart', 'Darwin']
MODES = ['Bus', 'Train', 'Tram / light rail', 'Ferry']
MODE_COL = ['#d9730d', '#1d4e89', '#17a398', '#8e5bc4']
GREY = '#8a8f98'
INK = '#1f2933'
ACCENT = '#d6452f'

# BITRE labels -> plain-English labels used in every chart (Heavy rail -> Train, Light rail -> Tram / light rail)
MODE_CALC = ("datum.mode == 'Heavy rail' || datum.mode == 'Train' || datum.mode == 'Metro' ? 'Train' : "
             "datum.mode == 'Light rail' || datum.mode == 'Tram' ? 'Tram / light rail' : datum.mode")
MODE_SCALE = {'domain': MODES, 'range': MODE_COL}
CONFIG = {
    'font': "'Public Sans', 'Segoe UI', system-ui, sans-serif",   # same family as the page body text (loaded in index.html)
    'axis': {'labelFontSize': 12, 'titleFontSize': 12, 'titleColor': '#52606d', 'labelColor': '#52606d',
             'gridColor': '#e4e7eb', 'domainColor': '#9aa5b1', 'tickColor': '#9aa5b1'},
    'legend': {'labelFontSize': 12, 'titleFontSize': 12, 'orient': 'top', 'direction': 'horizontal'},
    'view': {'stroke': None},
    'title': {'fontSize': 13, 'anchor': 'start', 'color': INK},
}


def mode_color(title='Mode', legend=True):
    return {'field': 'mode', 'type': 'nominal', 'scale': MODE_SCALE, 'title': title,
            **({} if legend else {'legend': None})}


DESC = {'01_national_trips': 'Streamgraph of yearly trips by mode, all eight capitals. Bus sits under train so the share shift is visible; labels give 1977-2025 shares.', '05_city_recovery_multiples': "Lines: each city's yearly trips indexed to 2018-19 = 100. End labels are kept in value order with leader lines.", '04_change_by_mode': 'Diverging stacked bars: change in trips per resident since 2018-19, by city and mode. Diamond = net; right-hand note = net change in total trips.', '02_trips_per_person': 'Bubble scatter where each bubble is a donut of the city mode mix. x = trips per person, y = car km per person vs the average. Brisbane and Perth are offset and linked by leader lines.', '07_pt_share_dumbbell': 'Dumbbell: public transport share of passenger-km by city before COVID-19 (2018-19), at its COVID-19 low point (year printed on the dot) and after (2024-25).', '06_trips_per_person_trend': 'Lines: public transport trips per resident since 2001, with spaced end labels.', '08_monthly_sydney_melbourne': 'Two line panels: monthly trips by mode vs the 2019 average (2019 = 100) for Sydney and Melbourne.', '09_adelaide_daily': 'Calendar heatmap of Adelaide Metrocard touch-ons per day (thousands); red outline = public holiday.', '15_sydney_stations': 'Proportional-symbol map of Sydney station entries: size, yellow shade and opacity all show usage. Rail lines and postcodes as base layers.', '16_melbourne_stations': 'Same encoding as chart 13 for Melbourne train stations, using the same scales.', '18_melbourne_stops': 'Dot map of every Melbourne stop, coloured by mode, over postcode outlines.', '19_brisbane_stops': 'Map of every South East Queensland stop, station and wharf: colour = mode, opacity = boardings in July 2026 (TransLink origin-destination trips), with rail lines.', '03_national_map': "Choropleth: each state is coloured by its capital city's 2024-25 trips as % of 2018-19. Number of dots = total trips (1 dot = 20 million).", '17_melbourne_lines': 'Bars: estimated Melbourne station entries by train line; station entries are split across the lines serving them.', '11_canberra_hourly': 'Lines: share of Canberra bus boardings by hour, July to February of 2019-20 and 2020-21; peak windows shaded.', '10_train_hours_by_day': "Lines: share of a day's Melbourne train loads by hour for each day type. Hours above 23 are after midnight.", '14_train_line_hour_heatmap': "Binless bivariate heatmap by line and hour: blue = share of the line's weekday travel, orange = passengers on board. Colour is computed in the spec; the key is generated from a sequence.", '12_train_tidal_flow': 'Diverging bars: weekday train loads towards the city (above zero) and away from it (below) by hour.', '13_train_line_peaks': "Lollipop/bubble: share of each line's weekday travel in the two peaks; bubble size = line's share of all train travel."}


def save(name, spec):
    """Write specs/<name>.json with the shared config and a one-line description."""
    spec = {'$schema': SCHEMA, 'description': DESC[name], 'config': CONFIG, **spec}
    with open(SPECS + name + '.json', 'w') as f:
        json.dump(spec, f, indent=1)


def note(x, y, text, **kw):
    """One annotation label (a layer with inline data)."""
    return {'data': {'values': [{'x': x, 'y': y, 't': text}]},
            'mark': {'type': 'text', 'align': kw.get('align', 'left'), 'baseline': kw.get('baseline', 'middle'),
                     'fontSize': 11, 'color': INK, 'fontStyle': 'italic', 'dx': kw.get('dx', 4), 'dy': kw.get('dy', 0),
                     'lineBreak': '\n'},
            'encoding': {'x': {'field': 'x', **kw.get('xtype', {'type': 'quantitative'})},
                         'y': {'field': 'y', 'type': 'quantitative'}, 'text': {'field': 't'}}}


def spread(values, gap):
    """Label heights for end-of-line labels: keep them in value order, as near the real value as the gap allows."""
    order = sorted(values, key=values.get, reverse=True)
    out, prev = {}, None
    for c in order:
        y = values[c] if prev is None else min(values[c], prev - gap)
        out[c] = y
        prev = y
    return order, out


def end_labels(rows, xdom, x_end, x_lab, ydef, color, label_fmt):
    """Leader line + label for each row {'city','v','y','lab'}; one inline dataset keeps the order explicit."""
    enc = {'x': {'field': 'x0', 'type': 'quantitative', 'scale': {'domain': xdom, 'zero': False, 'nice': False}},
           'color': color}
    return [
        {'data': {'values': rows}, 'mark': {'type': 'rule', 'strokeWidth': 1},
         'encoding': {**enc, 'x2': {'field': 'x1'}, 'y': {'field': 'v', 'type': 'quantitative'}, 'y2': {'field': 'y'}}},
        {'data': {'values': rows}, 'mark': {'type': 'text', 'align': 'left', 'dx': 4, 'fontSize': 11, 'fontWeight': 'bold'},
         'encoding': {'x': {'field': 'x1', 'type': 'quantitative', 'scale': {'domain': xdom, 'zero': False, 'nice': False}},
                      'y': {'field': 'y', 'type': 'quantitative'}, 'text': {'field': 'lab'}, 'color': color}}]


RECOVER_ORDER = ['Perth', 'Brisbane', 'Canberra', 'Adelaide', 'Sydney', 'Hobart', 'Darwin', 'Melbourne']


def XS(dom):
    return {'type': 'quantitative', 'scale': {'domain': dom, 'zero': False, 'nice': False}}


# 1 ---------------------------------------------------------------- national trips by mode (streamgraph)
# WHAT: streamgraph of yearly trips by mode for all eight capitals (BITRE).
# WHY:  shows bus share being eaten by train over time. Bus is stacked underneath train so the shift is easy to see.
# HOW:  stacked area with an explicit stack order; text labels at the right edge give the 1977 and 2025 shares.
# Vega centres each stack inside [0, largest total], so annotation heights are worked out from the totals.
TOT = {2022: 861.7, 1977: 1048.8, 2019: 1779.7, 2025: 1600.6}
MAXT = 1779.7
top = lambda year: (MAXT + TOT[year]) / 2
Y1 = {'type': 'quantitative', 'scale': {'domain': [0, 1900], 'nice': False}}
_n = pd.read_csv(ROOT + 'data/national_mode_share.csv')
_n['m'] = _n['mode'].replace({'Heavy rail': 'Train', 'Light rail': 'Tram / light rail'})
SHARE_LABELS = []
for _y, _al, _dx in [(1977, 'left', 5), (1995, 'center', 0), (2013, 'center', 0), (2025, 'right', -5)]:
    _d = _n[_n.year_end == _y].groupby('m').agg(t=('trips_million', 'sum'), sh=('share_pct', 'sum'))
    _off = (MAXT - _d.t.sum()) / 2
    for _m in ('Bus', 'Train'):
        _below = 0 if _m == 'Bus' else _d.t['Bus']
        SHARE_LABELS.append({'x': _y, 'y': _off + _below + _d.t[_m] / 2, 't': f"{_m}\n{_d.sh[_m]:.0f}%", 'al': _al, 'dx': _dx})
save('01_national_trips', {
    'title': {'text': 'Trips on city public transport, all eight capitals',
              'subtitle': 'Bus share fell from 54% to 42% of trips while train rose from 35% to 43% (1977 to 2025)'},
    'data': {'url': 'data/national_mode_share.csv'},
    'width': 'container', 'height': 300,
    'transform': [{'calculate': MODE_CALC, 'as': 'mode'},
                  {'calculate': "datum.mode == 'Bus' ? 0 : datum.mode == 'Train' ? 1 : datum.mode == 'Tram / light rail' ? 2 : 3", 'as': 'ord'}],
    'layer': [
        {'data': {'values': [{'a': 2019.5, 'b': 2022.5}]}, 'mark': {'type': 'rect', 'color': GREY, 'opacity': 0.15},
         'encoding': {'x': {'field': 'a', **XS([1977, 2025])}, 'x2': {'field': 'b'}}},
        {'mark': {'type': 'area', 'interpolate': 'monotone', 'opacity': 0.92},
         'encoding': {'x': {'field': 'year_end', **XS([1977, 2025]), 'title': 'Year ending 30 June',
                            'axis': {'format': 'd', 'tickMinStep': 5}},
                      'y': {'field': 'trips_million', 'stack': 'center', 'axis': None, **Y1},
                      'color': mode_color(), 'order': {'field': 'ord', 'type': 'quantitative'},
                      'tooltip': [{'field': 'fy', 'title': 'Year'}, {'field': 'mode'},
                                  {'field': 'trips_million', 'title': 'Trips (millions)'},
                                  {'field': 'share_pct', 'title': 'Share of trips (%)'}]}},
        *[{'data': {'values': SHARE_LABELS}, 'transform': [{'filter': f"datum.al == '{a}'"}],
           'mark': {'type': 'text', 'fontSize': 11, 'fontWeight': 'bold', 'color': '#ffffff', 'lineBreak': '\n', 'align': a,
                    'dx': {'left': 5, 'center': 0, 'right': -5}[a]},
           'encoding': {'x': {'field': 'x', **XS([1977, 2025])}, 'y': {'field': 'y', **Y1}, 'text': {'field': 't'}}}
          for a in ('left', 'center', 'right')],
        {'data': {'values': [
              {'x': 1977, 'y': top(1977) + 70, 't': '1.05 billion trips in 1976-77', 'al': 'left'},
              {'x': 2019, 'y': top(2019) + 70, 't': '1.78 billion in 2018-19', 'al': 'right'},
              {'x': 2025, 'y': top(2025) + 70, 't': '1.60 billion in 2024-25', 'al': 'right'},
              {'x': 2021, 'y': top(2022) + 110, 't': 'COVID-19 years', 'al': 'center'}]},
         'mark': {'type': 'text', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'align': 'left'},
         'encoding': {'x': {'field': 'x', **XS([1977, 2025])}, 'y': {'field': 'y', **Y1}, 'text': {'field': 't'}}}]})


# 5 ---------------------------------------------------------------- recovery: all cities on one index chart
# WHAT: one line per city, trips indexed to 2018-19 = 100 (so 100 means 'back to pre-COVID').
# WHY:  compares recovery on one scale. Perth and Brisbane are above 100, Melbourne is below.
# HOW:  lines + end-of-line labels. The labels are pre-spaced in Python (spread()) so they never overlap, and a thin leader line joins each label to its line.
CITY_COL = {'field': 'city', 'type': 'nominal', 'scale': {'domain': CITIES, 'scheme': 'tableau10'}, 'legend': None}  # colours fixed per city
_e4 = pd.read_csv(ROOT + 'data/city_totals_recovery.csv').query('year_end == 2025').set_index('city').index_2018_19.to_dict()
_o4, _y4 = spread(_e4, 3.8)
END4 = [{'city': c, 'v': _e4[c], 'y': round(_y4[c], 1), 'x0': 2025, 'x1': 2026.3, 'lab': f'{c} {_e4[c]:.0f}'} for c in _o4]
_rc = pd.read_csv(ROOT + 'data/city_totals_recovery.csv')
LOWS4 = []
for _c, _g in _rc[_rc.year_end.between(2020, 2023)].groupby('city'):          # 2019-20 to 2022-23
    _r = _g.loc[_g.index_2018_19.idxmin()]
    LOWS4.append({'city': _c, 'year_end': int(_r.year_end), 'fy': _r.fy, 'index': float(_r.index_2018_19)})
_deep = min(LOWS4, key=lambda d: d['index'])
LOW_ALL = {'x0': 2020.5, 'x1': _deep['year_end'], 'index': _deep['index'],
           'lab': f"Lowest point of all:\n{_deep['city']}, {_deep['fy']}, {_deep['index']:.0f}"}
save('05_city_recovery_multiples', {
    'title': 'Trips each year compared with 2018-19 (2018-19 = 100), all eight cities',
    'data': {'url': 'data/city_totals_recovery.csv'},
    'width': 'container', 'height': 340,
    'transform': [{'filter': 'datum.year_end >= 2012'}],
    'layer': [
        {'data': {'values': [{'a': 2019.5, 'b': 2022.5}]}, 'mark': {'type': 'rect', 'color': GREY, 'opacity': 0.15},
         'encoding': {'x': {'field': 'a', **XS([2012, 2029])}, 'x2': {'field': 'b'}}},
        {'mark': {'type': 'rule', 'strokeDash': [4, 3], 'color': GREY}, 'encoding': {'y': {'datum': 100}}},
        {'mark': {'type': 'line', 'interpolate': 'monotone'},
         'encoding': {'x': {'field': 'year_end', **XS([2012, 2029]), 'title': 'Year ending 30 June', 'axis': {'format': 'd', 'values': [2012, 2015, 2018, 2021, 2024]}},
                      'y': {'field': 'index_2018_19', 'type': 'quantitative', 'title': 'Trips (2018-19 = 100)', 'scale': {'domain': [20, 120]}},
                      'color': CITY_COL,
                      'strokeWidth': {'condition': {'test': "datum.city == 'Melbourne' || datum.city == 'Perth'", 'value': 3.2}, 'value': 1.6},
                      'tooltip': [{'field': 'city'}, {'field': 'fy', 'title': 'Year'},
                                  {'field': 'index_2018_19', 'title': 'Index (2018-19 = 100)'}]}},
        *end_labels(END4, [2012, 2029], 2025, 2026.3, None, CITY_COL, None),
        {'data': {'values': [{'x': 2021, 'y': 24, 't': 'COVID-19 years'}]},
         'mark': {'type': 'text', 'align': 'center', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933'},
         'encoding': {'x': {'field': 'x', **XS([2012, 2029])}, 'y': {'field': 'y', 'type': 'quantitative'}, 'text': {'field': 't'}}},
        # each city's own COVID-19 low point (lowest year from 2019-20 to 2022-23), drawn as a dot in the city's colour
        {'data': {'values': LOWS4}, 'mark': {'type': 'point', 'filled': True, 'size': 55, 'stroke': '#ffffff', 'strokeWidth': 1.2, 'opacity': 1},
         'encoding': {'x': {'field': 'year_end', **XS([2012, 2029])}, 'y': {'field': 'index', 'type': 'quantitative'}, 'color': CITY_COL,
                      'tooltip': [{'field': 'city'}, {'field': 'fy', 'title': 'Lowest year'}, {'field': 'index', 'title': 'Index (2018-19 = 100)'}]}},
        # callout for the deepest low point of all eight cities
        {'data': {'values': [LOW_ALL]}, 'mark': {'type': 'rule', 'color': '#1f2933', 'strokeWidth': 0.8},
         'encoding': {'x': {'field': 'x0', **XS([2012, 2029])}, 'x2': {'field': 'x1'}, 'y': {'field': 'index', 'type': 'quantitative'}}},
        {'data': {'values': [LOW_ALL]}, 'mark': {'type': 'text', 'align': 'right', 'baseline': 'middle', 'dx': -2, 'fontSize': 11, 'fontWeight': 'bold', 'color': '#1f2933', 'lineBreak': '\n'},
         'encoding': {'x': {'field': 'x0', **XS([2012, 2029])}, 'y': {'field': 'index', 'type': 'quantitative'}, 'text': {'field': 'lab'}}}]})

# 4 ---------------------------------------------------------------- change per resident, with absolute net noted
# WHAT: change in trips PER RESIDENT since 2018-19, split by mode, one bar per city.
# WHY:  cities grow, so raw totals hide that each person rides less. Per-resident numbers are fairer.
# HOW:  diverging stacked bars (negative goes left). The diamond is the net change; the text at the right is the net change in total trips.
save('04_change_by_mode', {
    'title': {'text': 'Change in yearly trips per resident since 2018-19, by city and mode',
              'subtitle': 'Per resident, so cities of different sizes can be compared. The note on the right gives each city\'s total net change.'},
    'data': {'url': 'data/city_mode_recovery.csv'},
    'width': 'container', 'height': 300,
    'transform': [{'calculate': MODE_CALC, 'as': 'mode'},
                  {'calculate': 'datum.trips_2024_25 * 1000000 / datum.pop_2024_25 - datum.trips_2018_19 * 1000000 / datum.pop_2018_19', 'as': 'change_pc'},
                  {'calculate': 'datum.trips_2024_25 - datum.trips_2018_19', 'as': 'change_abs'},
                  {'joinaggregate': [{'op': 'sum', 'field': 'change_pc', 'as': 'net_pc'}, {'op': 'sum', 'field': 'change_abs', 'as': 'net_abs'}],
                   'groupby': ['city']},
                  {'calculate': "(datum.net_abs > 0 ? '+' : '\u2212') + format(abs(datum.net_abs), '.0f') + 'M trips'", 'as': 'net_lab'}],
    'encoding': {'y': {'field': 'city', 'type': 'nominal', 'title': None,
                       'sort': {'field': 'net_pc', 'op': 'min', 'order': 'ascending'}}},
    'layer': [
        {'mark': {'type': 'rule', 'color': GREY}, 'encoding': {'x': {'datum': 0, 'type': 'quantitative'}}},
        {'mark': {'type': 'bar', 'size': 16},
         'encoding': {'x': {'field': 'change_pc', 'type': 'quantitative', 'title': 'Trips per resident per year, 2024-25 minus 2018-19',
                            'scale': {'domain': [-36, 14], 'nice': False}},
                      'color': mode_color(),
                      'order': {'field': 'mode', 'type': 'nominal'},
                      'tooltip': [{'field': 'city'}, {'field': 'mode'},
                                  {'field': 'change_pc', 'title': 'Change per resident', 'format': '+.1f'},
                                  {'field': 'change_abs', 'title': 'Change in total trips (millions)', 'format': '+.1f'}]}},
        {'mark': {'type': 'point', 'shape': 'diamond', 'filled': True, 'size': 90, 'color': '#1f2933', 'stroke': 'white'},
         'encoding': {'x': {'field': 'net_pc', 'type': 'quantitative'},
                      'tooltip': [{'field': 'city'}, {'field': 'net_pc', 'title': 'Net change per resident', 'format': '+.1f'},
                                  {'field': 'net_abs', 'title': 'Net change in total trips (millions)', 'format': '+.1f'}]}},
        {'transform': [{'window': [{'op': 'row_number', 'as': 'rn'}], 'groupby': ['city']}, {'filter': 'datum.rn == 1'}],
         'mark': {'type': 'text', 'align': 'right', 'fontSize': 11, 'fontWeight': 'bold', 'color': '#1f2933'},
         'encoding': {'x': {'datum': 14, 'type': 'quantitative'}, 'text': {'field': 'net_lab'}}},
        {'data': {'values': [{'x': 14, 'y': 'Melbourne', 't': 'Net change, all trips'}]},
         'mark': {'type': 'text', 'align': 'right', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'dy': -16},
         'encoding': {'x': {'field': 'x', 'type': 'quantitative'}, 'y': {'field': 'y', 'type': 'nominal'}, 'text': {'field': 't'}}},
        {'data': {'values': [{'x': -4, 'y': 'Perth', 't': '\u25c6 net per resident'}]},
         'mark': {'type': 'text', 'align': 'right', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'dy': -14},
         'encoding': {'x': {'field': 'x', 'type': 'quantitative'}, 'y': {'field': 'y', 'type': 'nominal'}, 'text': {'field': 't'}}}]})

# 2 ---------------------------------------------------------------- bubble scatter whose bubbles are mode donuts
# WHAT: each city is a bubble. x = public transport trips per person, y = car km per person compared with the national average.
# WHY:  one picture for 'who relies on cars vs transit'. Each bubble is also a donut showing the city's mode mix (bus / train / tram / ferry).
# HOW:  donuts are arc marks placed by x/y. Their angles come from a stack transform that normalises each city's modes to 100%.
#       Brisbane and Perth are nudged (MOVE) so they do not overlap, with a leader line back to their true position.
_pc = pd.read_csv(ROOT + 'data/per_capita.csv').set_index('city')
_avg = (_pc.car_km_per_person * _pc.erp_30_jun_2025).sum() / _pc.erp_30_jun_2025.sum()
_avg_pt = _pc.pt_trips_million.sum() * 1e6 / _pc.erp_30_jun_2025.sum()
X7, Y7 = [0, 140], [-3.3, 3.3]
# Brisbane and Perth sit almost on top of each other, so their rings are moved and joined to the true position
MOVE = {'Brisbane': (52, 2.3), 'Perth': (68, -1.6)}
RPX = lambda pop: 8 + (36 - 8) * (pop / _pc.erp_30_jun_2025.max()) ** 0.5
BUB = []
for c in CITIES:
    x0, y0 = float(_pc.pt_trips_per_person[c]), float(_pc.car_km_per_person[c] - _avg) / 1000
    xd, yd = MOVE.get(c, (x0, y0))
    BUB.append({'city': c, 'x0': x0, 'y0': round(y0, 2), 'xd': xd, 'yd': yd, 'moved': c in MOVE,
                'ly': round(yd + RPX(_pc.erp_30_jun_2025[c]) / 55 + 0.25, 2),
                'pop': int(_pc.erp_30_jun_2025[c]), 'ppp': float(_pc.pt_trips_per_person[c]),
                'car': int(_pc.car_km_per_person[c])})
XS7 = lambda **k: {'type': 'quantitative', 'scale': {'domain': X7, 'zero': True, 'nice': False}, **k}
YS7 = lambda **k: {'type': 'quantitative', 'scale': {'domain': Y7, 'zero': False, 'nice': False}, **k}
save('02_trips_per_person', {
    'title': {'text': 'Riding versus driving, 2024-25',
              'subtitle': 'Each ring is a city: ring size is population and slices are the mix of modes. Hover a ring to highlight it.'},
    'width': 'container', 'height': 380,
    'layer': [
        {'data': {'values': [{'y': 0}]}, 'mark': {'type': 'rule', 'strokeDash': [6, 4], 'strokeWidth': 1.5, 'color': '#9aa5b1'},
         'encoding': {'y': {'field': 'y', **YS7()}}},
        {'data': {'values': [{'x': round(_avg_pt, 1)}]}, 'mark': {'type': 'rule', 'strokeDash': [6, 4], 'strokeWidth': 1.5, 'color': '#9aa5b1'},
         'encoding': {'x': {'field': 'x', **XS7()}}},
        {'data': {'values': [{'x': round(_avg_pt, 1), 'y': -3.2, 't': f'Average: {_avg_pt:.0f} trips'}]},
         'mark': {'type': 'text', 'align': 'left', 'dx': 4, 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'baseline': 'bottom'},
         'encoding': {'x': {'field': 'x', **XS7()}, 'y': {'field': 'y', **YS7()}, 'text': {'field': 't'}}},
        {'data': {'values': [{'x': 1, 'y': 0, 't': f'Average: {_avg / 1000:.1f} thousand km'}]},
         'mark': {'type': 'text', 'align': 'left', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'dy': -7},
         'encoding': {'x': {'field': 'x', **XS7()}, 'y': {'field': 'y', **YS7()}, 'text': {'field': 't'}}},
        {'data': {'values': [b for b in BUB if b['moved']]}, 'mark': {'type': 'rule', 'strokeWidth': 1.8, 'stroke': '#b07032'},   # brown = midpoint of the blue (train) and orange (bus) hues, brightened

         'encoding': {'x': {'field': 'x0', **XS7()}, 'x2': {'field': 'xd'}, 'y': {'field': 'y0', **YS7()}, 'y2': {'field': 'yd'}}},
        {'data': {'values': [b for b in BUB if b['moved']]}, 'mark': {'type': 'circle', 'size': 75, 'color': '#b07032', 'stroke': 'white', 'strokeWidth': 1.2},
         'encoding': {'x': {'field': 'x0', **XS7()}, 'y': {'field': 'y0', **YS7()}}},
        {'data': {'values': BUB}, 'mark': {'type': 'text', 'fontSize': 11, 'fontWeight': 'bold', 'color': '#1f2933'},
         'encoding': {'x': {'field': 'xd', **XS7(title='Public transport trips per person per year')},
                      'y': {'field': 'ly', **YS7(title="Car travel per person, compared with the average ('000 km a year)",
                                                  axis={'labelExpr': "datum.value > 0 ? '+' + datum.value : datum.value", 'tickMinStep': 1})},
                      'text': {'field': 'city'}}},
        {'data': {'url': 'data/city_mode_long.csv'},
         'params': [{'name': 'pick', 'select': {'type': 'point', 'fields': ['city'], 'on': 'mouseover', 'clear': 'mouseout'}}],
         'transform': [{'filter': "datum.fy == '2024-25'"}, {'calculate': MODE_CALC, 'as': 'mode'},
                       {'calculate': "datum.mode == 'Bus' ? 0 : datum.mode == 'Train' ? 1 : datum.mode == 'Tram / light rail' ? 2 : 3", 'as': 'ord'},
                       {'stack': 'trips_million', 'groupby': ['city'], 'offset': 'normalize', 'as': ['a0', 'a1'],
                        'sort': [{'field': 'ord', 'order': 'ascending'}]},
                       {'lookup': 'city', 'from': {'data': {'values': BUB}, 'key': 'city', 'fields': ['xd', 'yd', 'pop', 'ppp', 'car']}},
                       {'calculate': '(datum.a1 - datum.a0) * 100', 'as': 'share'}],
         'mark': {'type': 'arc', 'innerRadius': 4, 'stroke': 'white', 'strokeWidth': 0.8},
         'encoding': {'x': {'field': 'xd', **XS7()}, 'y': {'field': 'yd', **YS7()},
                      'theta': {'field': 'a0', 'type': 'quantitative', 'scale': {'domain': [0, 1]}, 'stack': None},
                      'theta2': {'field': 'a1'},
                      'radius': {'field': 'pop', 'type': 'quantitative', 'scale': {'type': 'sqrt', 'zero': True, 'range': [8, 36]}, 'legend': None},
                      'color': mode_color(),
                      'opacity': {'condition': {'param': 'pick', 'value': 1}, 'value': 0.4},
                      'tooltip': [{'field': 'city'}, {'field': 'mode'}, {'field': 'share', 'title': 'Share of city trips (%)', 'format': '.0f'},
                                  {'field': 'ppp', 'title': 'Trips per person'}, {'field': 'car', 'title': 'Car km per person', 'format': ','},
                                  {'field': 'pop', 'title': 'Population', 'format': ','}]}}]})

# 7 ---------------------------------------------------------------- dumbbell
# WHAT: dumbbell: public transport's share of passenger-km per city at three moments: before COVID-19 (2018-19), its COVID-19 low point (red, year printed above the dot), and after (2024-25).
# WHY:  separates the COVID dip from the lasting change. A red dot far left of the dark-blue one = big dip; dark blue left of light blue = share never came back.
# DATA: data/car_vs_pt.csv is built by pkm_share.py from BITRE Table 2.3.
PT_PER = ['Before', 'Low point', 'After']   # before = 2018-19, low point = each city's lowest COVID-19 year (printed on the dot), after = 2024-25
PT_COL = ['#9db7d5', '#d6452f', '#1d4e89']
save('07_pt_share_dumbbell', {
    'title': ['COVID-19 effect on public transport', 'share of distance travelled'],
    'data': {'url': 'data/car_vs_pt.csv'},
    'width': 'container', 'height': 300,
    'encoding': {'y': {'field': 'city', 'type': 'nominal', 'sort': CITIES, 'title': None},
                 'x': {'field': 'pt_share_of_pkm_pct', 'type': 'quantitative', 'title': 'Share of distance travelled (%)',
                       'scale': {'domain': [0, 18]}}},
    'layer': [
        {'mark': {'type': 'line', 'color': GREY, 'strokeWidth': 2}, 'encoding': {'detail': {'field': 'city'}}},
        {'mark': {'type': 'circle', 'size': 120, 'opacity': 1},
         'encoding': {'color': {'field': 'period', 'type': 'nominal', 'title': None,
                                'scale': {'domain': PT_PER, 'range': PT_COL}},
                      'tooltip': [{'field': 'city'}, {'field': 'period', 'title': 'Point'}, {'field': 'fy', 'title': 'Year'},
                                  {'field': 'pt_share_of_pkm_pct', 'title': 'Public transport share (%)'}]}},
        # the financial year of each city's COVID-19 low point, printed above its dot
        {'transform': [{'filter': "datum.period == 'Low point'"}],
         'mark': {'type': 'text', 'dy': -12, 'fontSize': 10, 'color': '#d6452f'},
         'encoding': {'text': {'field': 'fy'}}}]})

# 6 ---------------------------------------------------------------- trips per person over time
# WHAT: public transport trips per resident since 2001, one line per city.
# WHY:  shows the long-run decline/rise, not only the COVID dip. End labels are spaced so city names stay readable.
_e9 = pd.read_csv(ROOT + 'data/city_pop_trips.csv').query('year_end == 2025').set_index('city').trips_per_person.to_dict()
_o9, _y9 = spread(_e9, 8)
END9 = [{'city': c, 'v': _e9[c], 'y': round(_y9[c], 1), 'x0': 2025, 'x1': 2027, 'lab': f'{c} {_e9[c]:.0f}'} for c in _o9]
save('06_trips_per_person_trend', {
    'title': 'Public transport trips per resident since 2001',
    'data': {'url': 'data/city_pop_trips.csv'},
    'width': 'container', 'height': 320,
    'layer': [
        {'mark': {'type': 'line', 'strokeWidth': 2.2},
         'encoding': {'x': {'field': 'year_end', 'type': 'quantitative', 'title': 'Year ending 30 June',
                            'axis': {'format': 'd', 'tickMinStep': 4}, 'scale': {'domain': [2001, 2033], 'zero': False, 'nice': False}},
                      'y': {'field': 'trips_per_person', 'type': 'quantitative', 'title': 'Trips per person per year'},
                      'color': {'field': 'city', 'type': 'nominal', 'scale': {'domain': CITIES, 'scheme': 'tableau10'}, 'legend': None},
                      'tooltip': [{'field': 'city'}, {'field': 'year_end', 'title': 'Year ending', 'format': 'd'},
                                  {'field': 'trips_per_person', 'title': 'Trips per person'},
                                  {'field': 'population', 'title': 'Population', 'format': ','}]}},
        *end_labels(END9, [2001, 2033], 2025, 2027, None, {'field': 'city', 'type': 'nominal', 'scale': {'domain': CITIES, 'scheme': 'tableau10'}, 'legend': None}, None)]})

# 8 --------------------------------------------------------------- monthly index, Sydney and Melbourne
# WHAT: two small line charts (Sydney, Melbourne): monthly trips by mode, 2019 average = 100.
# WHY:  shows which modes recovered and how fast.
# HOW:  hconcat of two panels sharing a legend.
def monthly(city, notes):
    return {
        'title': city, 'width': 300, 'height': 240,
        'data': {'url': 'data/monthly_city_mode.csv', 'format': {'parse': {'month': "date:'%Y-%m-%d'"}}},
        'transform': [{'filter': f"datum.city == '{city}' && year(datum.month) >= 2018"},
                      {'calculate': MODE_CALC, 'as': 'mode'}],
        'layer': [
            {'mark': {'type': 'rule', 'strokeDash': [4, 3], 'color': GREY}, 'encoding': {'y': {'datum': 100}}},
            {'mark': {'type': 'line', 'strokeWidth': 1.8},
             'encoding': {'x': {'field': 'month', 'type': 'temporal', 'title': None, 'axis': {'format': '%Y', 'tickCount': 5}},
                          'y': {'field': 'index_2019', 'type': 'quantitative', 'title': 'Trips vs the same mode in 2019 (2019 average = 100)',
                                'scale': {'domain': [0, 140]}},
                          'color': mode_color(),
                          'tooltip': [{'field': 'month', 'type': 'temporal', 'format': '%b %Y', 'title': 'Month'}, {'field': 'mode'},
                                      {'field': 'trips_million', 'title': 'Trips (millions)'},
                                      {'field': 'index_2019', 'title': 'Index (2019 = 100)'}]}},
            *notes]}


def tnote(date, y, text, align='left', dx=4):
    return {'data': {'values': [{'d': date, 'y': y, 't': text}]},
            'mark': {'type': 'text', 'align': align, 'fontSize': 10.5, 'fontStyle': 'italic', 'color': INK, 'dx': dx, 'lineBreak': '\n'},
            'encoding': {'x': {'field': 'd', 'type': 'temporal'}, 'y': {'field': 'y', 'type': 'quantitative'}, 'text': {'field': 't'}}}


save('08_monthly_sydney_melbourne', {
    'resolve': {'scale': {'y': 'shared'}},
    'hconcat': [
        monthly('Sydney', [tnote('2020-04-01T00:00:00', 12, 'First COVID-19\nlockdowns'),
                           tnote('2024-06-01T00:00:00', 128, 'Ferries above\n2019 levels', align='right', dx=-2)]),
        monthly('Melbourne', [tnote('2020-04-01T00:00:00', 12, 'Lockdowns'),
                              tnote('2026-01-01T00:00:00', 116, 'Tram counting\nmethod changed', align='right', dx=-2)])]})

# 9 --------------------------------------------------------------- Adelaide calendar heatmap
# WHAT: calendar heatmap of Adelaide Metrocard touch-ons per day (thousands).
# WHY:  weekday/weekend rhythm and public holidays jump out. Red outline = public holiday.
# HOW:  rect marks, week on the x axis, weekday on the y axis, colour = touch-ons.
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
CAL_X = {'field': 'week_start', 'type': 'ordinal', 'title': 'Week starting', 'axis': {'labelAngle': 0, 'labelOverlap': True,
         'labelExpr': "utcFormat(toDate(datum.value), '%-d %b')"}}
CAL_Y = {'field': 'weekday', 'type': 'ordinal', 'sort': DAYS, 'title': None, 'axis': {'labelExpr': "slice(datum.value, 0, 3)"}}
save('09_adelaide_daily', {
    'title': 'Adelaide: Metrocard touch-ons per day (thousands), April to June 2026 (at least)',
    'data': {'url': 'data/adelaide_daily.csv'},
    'width': 'container', 'height': 190,
    'transform': [{'calculate': 'datum.validations_min / 1000', 'as': 'touch_k'}],
    'layer': [
        {'mark': {'type': 'rect', 'stroke': 'white', 'strokeWidth': 1.5},
         'encoding': {'x': CAL_X, 'y': CAL_Y,
                      'color': {'field': 'touch_k', 'type': 'quantitative', 'title': "'000 touch-ons",
                                'scale': {'scheme': 'blues'}, 'legend': {'format': '.0f', 'gradientLength': 160}},
                      'tooltip': [{'field': 'date', 'title': 'Date'}, {'field': 'weekday', 'title': 'Day'},
                                  {'field': 'touch_k', 'title': "'000 touch-ons (at least)", 'format': '.1f'},
                                  {'field': 'holiday', 'title': 'Public holiday'}]}},
        {'transform': [{'filter': "datum.holiday != ''"}],
         'mark': {'type': 'rect', 'fill': None, 'strokeWidth': 2.5},
         # the stroke is driven by a constant label so that it gets its own legend entry
         'encoding': {'x': CAL_X, 'y': CAL_Y,
                      'stroke': {'datum': 'Public holiday', 'type': 'nominal', 'title': None,
                                 'scale': {'domain': ['Public holiday'], 'range': ['#d6452f']},
                                 'legend': {'symbolType': 'square', 'symbolFillColor': 'transparent', 'symbolStrokeWidth': 2.5}}}},
        {'transform': [{'filter': "datum.holiday != ''"}],
         'mark': {'type': 'text', 'fontSize': 9, 'fontWeight': 'bold', 'color': '#d6452f', 'text': '\u25cf', 'dy': 0},
         'encoding': {'x': CAL_X, 'y': CAL_Y}}]})

# 15 / 16 ---------------------------------------------------------------- station maps (same size scale)
LEG = {'type': 'symbol', 'orient': 'bottom', 'values': [1e6, 5e6, 20e6], 'format': '.2s', 'title': 'Station entries per year'}
STROKE = {'datum': None, 'type': 'nominal', 'title': None,
          'scale': {'domain': ['Rail line', 'Postcode boundary'], 'range': ['#4f7cac', '#b8c2cc']},
          'legend': {'orient': 'bottom', 'symbolType': 'stroke', 'symbolStrokeWidth': 2.5}}
USE_COL = {'field': 'entries', 'type': 'quantitative', 'title': 'Station entries per year',
           'scale': {'type': 'sqrt', 'domain': [0, 27e6], 'range': ['#ffe9a0', '#f2a900']}, 'legend': LEG}
USE_OPA = {'field': 'entries', 'type': 'quantitative', 'scale': {'type': 'sqrt', 'domain': [0, 27e6], 'range': [0.35, 0.95]}, 'legend': None}
SIZE = {'type': 'quantitative', 'scale': {'domain': [0, 27e6], 'range': [0, 1500], 'type': 'sqrt'}, 'title': 'Station entries per year', 'legend': LEG}


def stroke_enc(name):
    return {'stroke': {**STROKE, 'datum': name}}


def base(url):
    return {'data': {'url': url, 'format': {'type': 'json', 'property': 'features'}},
            'mark': {'type': 'geoshape', 'filled': False, 'stroke': '#b8c2cc', 'strokeWidth': 0.5, 'opacity': 0.8, 'clip': True},
            'encoding': stroke_enc('Postcode boundary')}


def station_map(name, title, url, proj, w, h, color_encoding, extra_transform, callouts=(), extra_tooltip=(), basemap=None, rail=None):
    save(name, {
        'title': title, 'width': w, 'height': h,
        'data': {'url': url},
        'projection': proj,
        'transform': extra_transform,
        'layer': [
            base(basemap),
            {'data': {'url': rail, 'format': {'type': 'json'}},
             'mark': {'type': 'geoshape', 'filled': False, 'stroke': '#4f7cac', 'strokeWidth': 1.6, 'opacity': 0.95, 'clip': True},
             'encoding': stroke_enc('Rail line')},
            {'mark': {'type': 'circle', 'stroke': '#7a5400', 'strokeWidth': 0.6, 'clip': True},
             'encoding': {'longitude': {'field': 'lon', 'type': 'quantitative'},
                          'latitude': {'field': 'lat', 'type': 'quantitative'},
                          'size': SIZE, 'color': USE_COL, 'opacity': USE_OPA, 'order': {'field': 'entries', 'sort': 'descending'},
                          'tooltip': [{'field': 'station', 'title': 'Station'}, *extra_tooltip,
                                      {'field': 'entries', 'title': 'Entries per year', 'format': ','}]}},
            *callout_layers(callouts)]})


def callout_layers(callouts):
    """Ring, leader line and label for the busiest stations, drawn in a contrasting colour."""
    ring = {'data': {'values': callouts},
            'mark': {'type': 'circle', 'fill': None, 'stroke': ACCENT, 'strokeWidth': 2.2},
            'encoding': {'longitude': {'field': 'lon', 'type': 'quantitative'}, 'latitude': {'field': 'lat', 'type': 'quantitative'},
                         'size': {'field': 'entries', 'type': 'quantitative', 'scale': SIZE['scale'], 'legend': None}}}
    line = {'data': {'values': callouts}, 'mark': {'type': 'rule', 'stroke': '#1f2933', 'strokeWidth': 0.8},
            'encoding': {'longitude': {'field': 'lon', 'type': 'quantitative'}, 'latitude': {'field': 'lat', 'type': 'quantitative'},
                         'longitude2': {'field': 'lon2'}, 'latitude2': {'field': 'lat2'}}}
    out = [line]
    for halo in (True, False):
        for align in ('left', 'right', 'center'):
            m = {'type': 'text', 'align': align, 'fontSize': 11, 'fontWeight': 'bold', 'lineBreak': '\n', 'lineHeight': 13,
                 'dx': 4 if align == 'left' else -4 if align == 'right' else 0, 'dy': -8 if align == 'center' else 0,
                 'color': '#ffffff' if halo else '#1f2933'}
            if halo:
                m.update({'stroke': '#ffffff', 'strokeWidth': 3.5})
            out.append({'data': {'values': callouts}, 'transform': [{'filter': f"datum.align == '{align}'"}], 'mark': m,
                        'encoding': {'longitude': {'field': 'lon2', 'type': 'quantitative'}, 'latitude': {'field': 'lat2', 'type': 'quantitative'},
                                     'text': {'field': 'label'}}})
    return out


def make_callouts(csv, spots, mode=None):
    d = pd.read_csv(ROOT + csv)
    if mode:
        d = d[d['mode'] == mode]
    rows = []
    for name, (lon2, lat2, align) in spots.items():
        r = d[d.station == name].sort_values('entries', ascending=False).iloc[0]
        rows.append({'station': name, 'lon': float(r.lon), 'lat': float(r.lat), 'entries': int(r.entries),
                     'lon2': lon2, 'lat2': lat2, 'align': align, 'label': name})
    return rows


# 15 / 16 ---- station maps. WHAT: one circle per rail station; size, yellow shade and opacity all grow with yearly entries (same scales in both cities so they compare).
#               Blue lines = rail network, grey outlines = postcodes. Red rings + labels mark the busiest stations.
station_map('15_sydney_stations', 'Sydney: busiest stations, last 12 months of data',
            'data/syd_stations.csv', {'type': 'mercator', 'scale': 27500, 'center': [151.08, -33.85]}, 390, 400,
            {'field': 'mode', 'type': 'nominal', 'title': 'Mode',
             'scale': {'domain': ['Train', 'Metro', 'Light rail'], 'range': ['#1d4e89', '#c0392b', '#17a398']}},
            [{'filter': 'datum.lon > 150.6 && datum.lon < 151.4 && datum.lat > -34.2 && datum.lat < -33.5'}],
            callouts=make_callouts('data/syd_stations.csv', {
                'Town Hall': (151.262, -33.845, 'left'), 'Central': (151.262, -33.905, 'left'),
                'Parramatta': (151.0055, -33.775, 'center')}, mode='Train'),
            extra_tooltip=[{'field': 'mode', 'title': 'Mode'}], basemap='data/syd_poa.json', rail='data/syd_rail.json')
station_map('16_melbourne_stations', 'Melbourne: busiest train stations, 2024-25',
            'data/melb_stations.csv', {'type': 'mercator', 'scale': 25700, 'center': [145.05, -37.85]}, 390, 400,
            {'value': '#f2a900'}, [{'filter': 'datum.lon > 144.5 && datum.lon < 145.6'}],
            callouts=make_callouts('data/melb_stations.csv', {
                'Southern Cross': (144.885, -37.835, 'right'), 'Flinders Street': (145.025, -37.857, 'left'),
                'Melbourne Central': (144.90, -37.775, 'right')}),
            basemap='data/melb_poa.json', rail='data/melb_rail.json')


# Mode legend for the stop maps. Dot size comes from a calculated numeric field ('sz', scale: null) so it cannot
# merge with or suppress the colour legend; symbols are drawn large and fully opaque so the hues are easy to read.
MODE_LEG = mode_color('Mode')
MODE_LEG['legend'] = {'orient': 'top', 'direction': 'horizontal', 'symbolType': 'circle', 'symbolSize': 110, 'symbolOpacity': 1,
                      'labelFontSize': 11, 'titleFontSize': 11}
SZ = lambda: {'field': 'sz', 'type': 'quantitative', 'scale': None, 'legend': None}

# 18 --------------------------------------------------------------- Melbourne stops
# WHAT: dot map of every Melbourne public transport stop, coloured by mode (legend at the top).
# WHY:  shows where each mode serves: trams in the inner city, trains in lines, buses filling the suburbs.
# HOW:  circles at lon/lat on a Mercator projection over postcode outlines. Buses are drawn first (underneath) and are the smallest dots.
#       Dot size comes from a calculated field (sz) so it cannot hide the colour legend.
ORDER_CALC = "datum.mode == 'Bus' ? 0 : datum.mode == 'Tram' ? 1 : 2"
save('18_melbourne_stops', {
    'title': 'Melbourne: every stop and station', 'width': 390, 'height': 440,
    'projection': {'type': 'mercator', 'scale': 31900, 'center': [145.0, -37.9]},
    'layer': [
        base('data/melb_poa.json'),
        {'data': {'url': 'data/melb_stops.csv'},
         'transform': [{'calculate': MODE_CALC, 'as': 'mode'}, {'calculate': ORDER_CALC.replace('Tram', 'Tram / light rail'), 'as': 'z'},
                       {'calculate': "datum.mode == 'Bus' ? 3 : datum.mode == 'Train' ? 9 : datum.mode == 'Tram / light rail' ? 6 : 3", 'as': 'sz'}],
         'mark': {'type': 'circle', 'opacity': 0.55, 'clip': True},
         'encoding': {'longitude': {'field': 'lon', 'type': 'quantitative'}, 'latitude': {'field': 'lat', 'type': 'quantitative'},
                      'order': {'field': 'z', 'type': 'quantitative'},
                      'size': SZ(),
                      'color': MODE_LEG,
                      'tooltip': [{'field': 'mode'}]}}]})

# 19 --------------------------------------------------------------- Brisbane stops + rail
# WHAT: map of every South East Queensland stop, station and wharf.
# WHY:  hue = mode, opacity = how busy the stop was in July 2026 (TransLink origin-destination trips). Quiet stops are nearly clear, busy ones solid.
# HOW:  a symlog opacity scale spreads the very skewed counts (87% of stops have under 1,000 boardings). Buses are small and drawn underneath;
#       blue lines are the rail network. The data is built by seq_boardings.py.
save('19_brisbane_stops', {
    'title': 'South East Queensland: boardings at every stop, July 2026', 'width': 390, 'height': 540,
    'projection': {'type': 'mercator', 'scale': 27800, 'center': [153.2, -27.6]},
    'layer': [
        base('data/seq_poa.json'),
        {'data': {'url': 'data/bris_rail.geojson', 'format': {'type': 'json'}},
         'mark': {'type': 'geoshape', 'filled': False, 'stroke': '#1d4e89', 'strokeWidth': 1.1, 'opacity': 0.6, 'clip': True},
         'encoding': stroke_enc('Rail line')},
        {'data': {'url': 'data/bris_stops.csv'},
         'transform': [{'calculate': MODE_CALC, 'as': 'mode'},
                       {'calculate': "(datum.mode == 'Bus' ? 0 : 1e7) + datum.boardings", 'as': 'z'},
                       {'calculate': "datum.mode == 'Bus' ? 7 : 34", 'as': 'sz'}],
         'mark': {'type': 'circle', 'clip': True},
         'encoding': {'longitude': {'field': 'lon', 'type': 'quantitative'}, 'latitude': {'field': 'lat', 'type': 'quantitative'},
                      'order': {'field': 'z', 'type': 'quantitative'},            # buses underneath, then busiest stops on top
                      'size': SZ(),   # small bus dots show more detail
                      # both legends are stacked in the empty sea at top-right (orient 'none' + legendX/Y): mode first, boardings underneath.
                      # This keeps them inside the map's width, so the chart is not stretched wider than its card.
                      'color': {**MODE_LEG, 'legend': {**MODE_LEG['legend'], 'orient': 'none', 'direction': 'vertical', 'legendX': 262, 'legendY': 6}},
                      # transparency = usage: nearly clear for quiet stops, solid for busy ones (symlog spreads the skewed counts)
                      'opacity': {'field': 'boardings', 'type': 'quantitative', 'title': 'Boardings, July 2026',
                                  'scale': {'type': 'symlog', 'domain': [0, 500000], 'range': [0.05, 1], 'clamp': True},
                                  'legend': {'format': ',.0f', 'values': [0, 1000, 10000, 100000, 500000], 'symbolFillColor': '#52606d', 'symbolStrokeWidth': 0,
                                             'orient': 'none', 'direction': 'vertical', 'legendX': 262, 'legendY': 104}},
                      'tooltip': [{'field': 'mode', 'title': 'Mode'}, {'field': 'boardings', 'title': 'Boardings in July 2026', 'format': ',.0f'}]}}]})

# 3 --------------------------------------------------------------- national choropleth
# WHAT: map of Australia: each state is shaded by its capital city's 2024-25 trips as % of 2018-19. The NUMBER OF DOTS at each capital shows total trips (1 dot = 20 million).
# WHY:  a national overview of who has recovered. Labels sit beside the circles.
STATE_CITY = [{'s': 'New South Wales', 'city': 'Sydney'}, {'s': 'Victoria', 'city': 'Melbourne'},
              {'s': 'Queensland', 'city': 'Brisbane'}, {'s': 'South Australia', 'city': 'Adelaide'},
              {'s': 'Western Australia', 'city': 'Perth'}, {'s': 'Tasmania', 'city': 'Hobart'},
              {'s': 'Northern Territory', 'city': 'Darwin'}, {'s': 'Australian Capital Territory', 'city': 'Canberra'}]
LAT = {'field': 'lat', 'type': 'quantitative'}
LON = {'field': 'lon', 'type': 'quantitative'}
LABEL = [{'calculate': "datum.city + ' ' + format(datum.index_2018_19, '.0f') + '%'", 'as': 'lab'}]
DOT_M = 20          # one dot = 20 million trips in 2024-25 (every capital gets at least one dot)
GOLD = 2.39996      # golden angle: spreads dots evenly in a round cluster (sunflower layout)
# Each cluster is centred on the city itself and keeps only the dots that fall on the capital's own land, so a coastal city
# gives a half-disc that fans out inland. (city lon, city lat, label lon, label lat, label alignment). Names only; the % is in the
# state colour and the tooltip. Single-dot cities are nudged a little inland so the dot is inside the border.
SPOTS = {'Sydney':    (151.21, -33.87, 148.4, -33.5, 'right'),
         'Melbourne': (144.96, -37.81, 142.9, -37.5, 'right'),
         'Brisbane':  (153.03, -27.47, 150.5, -27.0, 'right'),
         'Perth':     (115.86, -31.95, 117.5, -31.9, 'left'),
         'Adelaide':  (138.60, -34.93, 137.9, -34.0, 'right'),
         'Canberra':  (149.13, -35.28, 148.8, -35.1, 'right'),
         'Hobart':    (147.20, -42.80, 146.6, -42.05, 'center'),
         'Darwin':    (130.95, -12.55, 131.4, -12.9, 'left')}
STATE_OF = {c['city']: c['s'] for c in STATE_CITY}
SPACING = 0.31      # degrees between neighbouring dots (about 6 px on the map), so dots touch as little as possible


def inside(pt, rings):
    """Ray-casting point-in-polygon test (rings = outer rings of a MultiPolygon)."""
    x, y = pt
    hit = False
    for poly in rings:
        ring = poly[0]
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i]; xj, yj = ring[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                hit = not hit
            j = i
    return hit


def label_box(l):
    """Approximate rectangle (degrees) covered by a label, so dots can steer around it."""
    w = len(l['lab']) * 6.3 / 10.3 + 0.5
    x0 = l['lon'] - (w if l['align'] == 'right' else w / 2 if l['align'] == 'center' else 0)
    return x0, x0 + w, l['lat'] - 0.7, l['lat'] + 0.7


def dot_clusters():
    """One row per dot: a cluster centred on each city, kept on the capital's own land and clear of every label; plus the labels."""
    import math
    cm = pd.read_csv(ROOT + 'data/city_map.csv').set_index('city')
    states = {f['properties']['STE_NAME26']: f['geometry']['coordinates']
              for f in json.load(open(ROOT + 'data/australia_states.json'))['features']}
    labels = [{'city': c, 'lon': v[2], 'lat': v[3], 'lab': c, 'align': v[4]} for c, v in SPOTS.items()]
    boxes = [label_box(l) for l in labels]
    dots = []
    for city, (ax, ay, *_rest) in SPOTS.items():
        r = cm.loc[city]
        n = max(1, round(r.total_trips_2024_25_million / DOT_M))
        land = states[STATE_OF[city]]
        others = [(v[0], v[1]) for c, v in SPOTS.items() if c != city]
        got, k = 0, 0
        while got < n and k < 6000:
            rr, th = (0.0 if n == 1 else SPACING * math.sqrt(k + 0.5)), k * GOLD
            k += 1
            lon = ax + rr * math.cos(th)
            lat = ay + rr * math.sin(th) * math.cos(math.radians(ay))   # Mercator stretches north-south, so squash lat to keep it round
            if n > 1:
                if not inside((lon, lat), land): continue                                 # in the sea or another state
                if any(x0 <= lon <= x1 and y0 <= lat <= y1 for x0, x1, y0, y1 in boxes): continue   # under a label
                if any(math.hypot(lon - ox, (lat - oy) / math.cos(math.radians(oy))) < 0.9 for ox, oy in others): continue  # on another city
            dots.append({'city': city, 'lon': round(lon, 3), 'lat': round(lat, 3), 'trips_m': r.total_trips_2024_25_million, 'dots': n})
            got += 1
    return dots, labels


DOTS, LABELS = dot_clusters()
pd.DataFrame(DOTS).to_csv(ROOT + 'data/city_dots.csv', index=False)   # written at build time, read by the chart


def label_layer(align, halo):
    m = {'type': 'text', 'align': align, 'dx': {'left': 2, 'right': -2, 'center': 0}[align], 'fontSize': 11, 'fontWeight': 'bold',
         'color': '#ffffff' if halo else '#1f2933'}
    if halo:
        m.update({'stroke': '#ffffff', 'strokeWidth': 3.5})
    return {'data': {'values': [l for l in LABELS if l['align'] == align]}, 'mark': m,
            'encoding': {'longitude': LON, 'latitude': LAT, 'text': {'field': 'lab'}}}


save('03_national_map', {
    'title': 'Trips in 2024-25 as % of 2018-19. Each state is coloured by its capital city.',
    'width': 500, 'height': 420,
    'view': {'fill': '#cfd8e2', 'stroke': None},
    'projection': {'type': 'mercator', 'scale': 590, 'center': [133.7, -27.5]},
    'layer': [
        {'data': {'sphere': True}, 'mark': {'type': 'geoshape', 'fill': '#cfd8e2', 'stroke': None}},
        {'data': {'url': 'data/australia_states.json', 'format': {'type': 'json', 'property': 'features'}},
         'transform': [{'lookup': 'properties.STE_NAME26', 'from': {'data': {'values': STATE_CITY}, 'key': 's', 'fields': ['city']}},
                       {'lookup': 'city', 'from': {'data': {'url': 'data/city_map.csv'}, 'key': 'city',
                                                   'fields': ['index_2018_19', 'total_trips_2024_25_million']}}],
         'mark': {'type': 'geoshape', 'stroke': '#ffffff', 'strokeWidth': 1},
         'encoding': {'color': {'field': 'index_2018_19', 'type': 'quantitative', 'title': '% of 2018-19',
                                'scale': {'domain': [80, 90, 100, 106], 'range': ['#b2182b', '#ef8a62', '#f7f7f7', '#2166ac'], 'clamp': True},
                                'legend': {'orient': 'bottom', 'direction': 'horizontal', 'gradientLength': 220, 'gradientThickness': 12}},
                      'tooltip': [{'field': 'city', 'title': 'Capital city'},
                                  {'field': 'total_trips_2024_25_million', 'title': 'Trips 2024-25 (millions)'},
                                  {'field': 'index_2018_19', 'title': '% of 2018-19'}]}},
        # dots: the number of dots at each capital shows its trips (1 dot = 20 million)
        {'data': {'url': 'data/city_dots.csv'},
         'mark': {'type': 'circle', 'size': 20, 'fill': '#0b2545', 'opacity': 0.95, 'stroke': '#ffffff', 'strokeWidth': 0.4},
         'encoding': {'longitude': LON, 'latitude': LAT,
                      'tooltip': [{'field': 'city', 'title': 'Capital city'}, {'field': 'trips_m', 'title': 'Trips 2024-25 (millions)'}]}},
        # key for the dots, placed in the sea below the continent
        {'data': {'values': [{'lon': 114.6, 'lat': -40.6, 't': f'= {DOT_M} million trips in 2024-25'}]},
         'mark': {'type': 'circle', 'size': 20, 'fill': '#0b2545', 'stroke': '#ffffff', 'strokeWidth': 0.4},
         'encoding': {'longitude': LON, 'latitude': LAT}},
        *[{'data': {'values': [{'lon': 114.6, 'lat': -40.6, 't': f'= {DOT_M} million trips in 2024-25'}]},
           'mark': {'type': 'text', 'align': 'left', 'dx': 8, 'fontSize': 11, 'fontWeight': 'bold',
                    'color': '#ffffff' if halo else '#1f2933', **({'stroke': '#ffffff', 'strokeWidth': 3.5} if halo else {})},
           'encoding': {'longitude': LON, 'latitude': LAT, 'text': {'field': 't'}}} for halo in (True, False)],
        *[label_layer(al, halo) for halo in (True, False) for al in ('left', 'right', 'center')]]})

# 17 --------------------------------------------------------------- Melbourne train lines
# WHAT: bars of estimated Melbourne station entries by train line.
# WHY:  stations on several lines are split across those lines using each line's share of loads, so lines can be compared.
# ORDER: lines are grouped by corridor (see LINE_ORDER), so related lines such as Cranbourne and Pakenham sit next to each other.
# Lines are listed by corridor, going round the network from the north-west, so related lines sit together
# (Cranbourne next to Pakenham, Lilydale next to Belgrave, and so on). Not alphabetical, not by size.
LINE_ORDER = ['Sunbury', 'Craigieburn', 'Upfield',                    # north-west and north
              'Mernda', 'Hurstbridge',                                # north-east
              'Lilydale', 'Belgrave', 'Alamein', 'Glen Waverley',     # east (Burnley and Camberwell group)
              'Pakenham', 'Cranbourne',                               # south-east (Dandenong corridor)
              'Frankston', 'Stony Point', 'Sandringham',              # south and bayside
              'Williamstown', 'Werribee',                             # west
              'Richmond and City Loop', 'Flemington Racecourse']      # city-only services
LINE_Y = {'field': 'line', 'type': 'nominal', 'title': None, 'sort': LINE_ORDER}
save('17_melbourne_lines', {
    'title': 'Melbourne: estimated train station entries by line, 2024-25 (millions)',
    'data': {'url': 'data/melb_lines.csv'},
    'width': 'container', 'height': 420,
    'layer': [
        {'mark': 'bar',
         'encoding': {'y': LINE_Y,
                      'x': {'field': 'entries_million', 'type': 'quantitative', 'title': 'Entries per year (millions)'},
                      'color': {'field': 'kind', 'type': 'nominal', 'title': None,
                                'scale': {'domain': ['Only this line', 'Shared with other lines'], 'range': ['#1d4e89', '#9db7d5']}},
                      'order': {'field': 'kind', 'type': 'nominal', 'sort': 'descending'},
                      'tooltip': [{'field': 'line', 'title': 'Line'}, {'field': 'kind', 'title': 'Stations'},
                                  {'field': 'entries_million', 'title': 'Entries (millions)', 'format': '.1f'}]}},
        {'transform': [{'joinaggregate': [{'op': 'sum', 'field': 'entries_million', 'as': 'total'}], 'groupby': ['line']},
                       {'window': [{'op': 'row_number', 'as': 'rn'}], 'groupby': ['line']}, {'filter': 'datum.rn == 1'}],
         'mark': {'type': 'text', 'align': 'left', 'dx': 4, 'fontSize': 11},
         'encoding': {'y': LINE_Y, 'x': {'field': 'total', 'type': 'quantitative'},
                      'text': {'field': 'total', 'type': 'quantitative', 'format': '.1f'}}}]})

# 11 --------------------------------------------------------------- Canberra by hour
# WHAT: Canberra bus boardings by hour of day, July-February, 2019-20 (orange) vs 2020-21 (blue).
# WHY:  both years show two sharp peaks (morning and 3 pm school time). Each line is a share of its own period, so the shape compares even though 2020-21 had ~36% fewer boardings.
# HOW:  grey bands mark the peak windows; the midnight bucket is excluded because it looks like a placeholder.
HRS = [{'x': 7, 'x2': 9, 't': 'Morning peak'}, {'x': 15, 'x2': 18, 't': 'Afternoon peak'}]
CA_DOM = ['July-Feb 2019-20', 'July-Feb 2020-21']
CA_COL = ['#d9730d', '#1d4e89']   # orange = before COVID-19, blue = during
CA_X = {'type': 'quantitative', 'scale': {'domain': [1, 23], 'nice': False}}
save('11_canberra_hourly', {
    'title': 'Canberra: share of daily boardings by hour, July to February, before and during COVID-19',
    'data': {'url': 'data/canberra_hourly.csv'},
    'width': 'container', 'height': 300,
    'layer': [
        {'data': {'values': HRS}, 'mark': {'type': 'rect', 'color': GREY, 'opacity': 0.18},
         'encoding': {'x': {'field': 'x', **CA_X}, 'x2': {'field': 'x2'}}},
        {'data': {'values': HRS}, 'mark': {'type': 'text', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'align': 'center', 'dy': 8, 'baseline': 'top'},
         'encoding': {'x': {'field': 'x', **CA_X}, 'y': {'datum': 17}, 'text': {'field': 't'}}},
        {'mark': {'type': 'line', 'interpolate': 'monotone', 'strokeWidth': 2.4, 'point': {'filled': True, 'size': 36}},
         'encoding': {
            'x': {'field': 'hour', **CA_X, 'title': 'Hour of day (24-hour clock, hour starting)', 'axis': {'values': [1, 4, 7, 10, 13, 16, 19, 22]}},
            'y': {'field': 'share_pct', 'type': 'quantitative', 'title': 'Share of the period\'s boardings (%)', 'scale': {'domain': [0, 18], 'nice': False}},
            'color': {'field': 'period', 'type': 'nominal', 'title': None, 'scale': {'domain': CA_DOM, 'range': CA_COL}},
            'tooltip': [{'field': 'period', 'title': 'Period'}, {'field': 'hour', 'title': 'Hour starting'}, {'field': 'share_pct', 'title': 'Share of boardings (%)'}]}}]})


# ======================================================================= Melbourne train loads (new data, sample)
TRH = [{'calculate': 'toNumber(datum.hour)', 'as': 'h'}]
HR = lambda ordinal=False: {'field': 'h' if ordinal else 'hour', 'type': 'ordinal' if ordinal else 'quantitative', 'title': 'Hour of day (hour starting)',
                            **({'scale': {'domain': list(range(4, 28))}} if ordinal else {}),
                            'axis': {'labelExpr': 'datum.value % 24', 'values': list(range(4, 28, 2)), 'labelAngle': 0}}
DAY_DOM = ['Weekday', 'Weekday in school holidays', 'Saturday', 'Sunday', 'Public holiday']
DAY_COL = ['#1d4e89', '#6aa6e8', '#d9730d', '#8e5bc4', '#8a8f98']

# 10 ---------------------------------------------------------------- hourly profile by day type
# WHAT: Melbourne trains: share of a day's travel by hour, one line per day type (weekday, school holidays, Saturday, Sunday, public holiday).
# WHY:  weekdays have sharp peaks, weekends a broad plateau. Hours above 23 mean after midnight (24 = midnight hour).
# NOTE: the train-load file is a SAMPLE of trips, so shares and shapes are reliable, absolute totals are not.
save('10_train_hours_by_day', {
    'title': 'Melbourne trains: share of a day\'s travel by hour, for each type of day',
    'data': {'url': 'data/train_hourly_daytype.csv'},
    'width': 'container', 'height': 320,
    'layer': [
        {'data': {'values': [{'a': 7, 'b': 9}, {'a': 16, 'b': 18}]}, 'mark': {'type': 'rect', 'color': GREY, 'opacity': 0.14},
         'encoding': {'x': {'field': 'a', 'type': 'quantitative', 'scale': {'domain': [4, 27], 'nice': False}}, 'x2': {'field': 'b'}}},
        {'data': {'values': [{'x': 8, 't': 'Morning rush\n7 to 9 am'}, {'x': 17, 't': 'Evening rush\n4 to 6 pm'}]},
         'mark': {'type': 'text', 'fontSize': 11, 'fontStyle': 'italic', 'color': '#1f2933', 'lineBreak': '\n', 'baseline': 'bottom'},
         'encoding': {'x': {'field': 'x', 'type': 'quantitative', 'scale': {'domain': [4, 27], 'nice': False}},
                      'y': {'datum': 17.5, 'type': 'quantitative'}, 'text': {'field': 't'}}},
        {'mark': {'type': 'line', 'interpolate': 'monotone', 'strokeWidth': 2.2},
         'encoding': {'x': {**HR(), 'scale': {'domain': [4, 27], 'nice': False}},
                      'y': {'field': 'share_pct', 'type': 'quantitative', 'title': 'Share of the day\'s train loads (%)', 'scale': {'domain': [0, 18], 'nice': False}},
                      'color': {'field': 'day', 'type': 'nominal', 'title': None, 'scale': {'domain': DAY_DOM, 'range': DAY_COL}},
                      'strokeDash': {'condition': {'test': "datum.day == 'Public holiday'", 'value': [5, 3]}, 'value': [1, 0]},
                      'tooltip': [{'field': 'day', 'title': 'Day type'}, {'field': 'hour', 'title': 'Hour starting'},
                                  {'field': 'share_pct', 'title': 'Share of the day (%)'}]}}]})

# 12 ---------------------------------------------------------------- tidal flow
# WHAT: Melbourne weekday train loads by hour, towards the city (above zero) vs away from it (below zero).
# WHY:  the 'tide': inbound peaks in the morning, outbound in the afternoon.
# NOTE: hours are converted with toNumber() because CSV text would otherwise be treated as labels, not numbers.
save('12_train_tidal_flow', {
    'title': {'text': 'Melbourne trains: weekday travel towards and away from the city',
              'subtitle': 'Morning rush is 7 to 9 am and evening rush is 4 to 6 pm'},
    'data': {'url': 'data/train_tidal.csv'},
    'width': 'container', 'height': 320,
    'transform': TRH,
    'layer': [
        {'mark': {'type': 'bar'},
         'encoding': {'x': HR(True),
                      'y': {'field': 'share_signed', 'type': 'quantitative', 'title': 'Share of weekday train loads (%), away from city below zero',
                            'axis': {'format': '~s'}},
                      'color': {'field': 'direction', 'type': 'nominal', 'title': None,
                                'scale': {'domain': ['Towards the city', 'Away from the city'], 'range': ['#1d4e89', '#d9730d']}},
                      'tooltip': [{'field': 'direction', 'title': 'Direction'}, {'field': 'hour', 'title': 'Hour starting'},
                                  {'field': 'share_signed', 'title': 'Share (%, sign shows direction)'}]}},
        {'mark': {'type': 'rule', 'color': GREY}, 'encoding': {'y': {'datum': 0}}}]})

# 13 ---------------------------------------------------------------- how peaky is each line
# WHAT: for each Melbourne train line, the share of weekday travel in the morning and evening peaks. Bubble size = the line's share of all train travel.
# WHY:  ranks lines by how 'peaky' they are.
save('13_train_line_peaks', {
    'title': 'Melbourne trains: how much of each line\'s weekday travel falls in the two peaks',
    'data': {'url': 'data/train_line_share.csv'},
    'width': 'container', 'height': 400,
    'transform': [{'calculate': '0', 'as': 'x0'}],
    'encoding': {'y': {'field': 'line', 'type': 'nominal', 'title': None, 'sort': {'field': 'peak_share', 'op': 'max', 'order': 'descending'}}},
    'layer': [
        {'mark': {'type': 'rule', 'color': GREY, 'strokeWidth': 1.5},
         'encoding': {'x': {'field': 'x0', 'type': 'quantitative', 'scale': {'domain': [0, 100], 'nice': False}}, 'x2': {'field': 'peak_share'}}},
        {'mark': {'type': 'circle', 'color': '#1d4e89', 'opacity': 0.85, 'stroke': 'white', 'strokeWidth': 1},
         'encoding': {'x': {'field': 'peak_share', 'type': 'quantitative', 'title': 'Share of weekday travel in the two peaks (%)',
                            'scale': {'domain': [0, 100], 'nice': False}},
                      'size': {'field': 'share_pct', 'type': 'quantitative', 'title': 'Share of all weekday train travel (%)',
                               'scale': {'range': [60, 900], 'zero': True},
                               'legend': {'orient': 'bottom', 'values': [2, 6, 10], 'symbolFillColor': '#1d4e89'}},
                      'tooltip': [{'field': 'line', 'title': 'Line'}, {'field': 'peak_share', 'title': 'In the two peaks (%)'},
                                  {'field': 'share_pct', 'title': 'Share of weekday train travel (%)'}]}}]})

# 14 ---------------------------------------------------------------- bivariate heatmap: busy hours x crowding, by line
# WHAT: bivariate heatmap by line (rows) and hour (columns). Blue = how much of the line's weekday travel happens then; orange = how crowded the train is.
# WHY:  one chart answers 'when is it busy' and 'when is it crowded'. Diagonal cells (both high) are the real peak hours.
# HOW:  'binless' - each cell's colour is computed in the spec by chained calculate transforms into an rgb() string (scale: null);
#       the 5x5 colour key beside it is generated from a sequence so it uses exactly the same maths.
_a = pd.read_csv(ROOT + 'data/train_line_hour.csv')
_b = pd.read_csv(ROOT + 'data/train_line_load.csv')[['line', 'hour', 'load', 'n']]
_a.merge(_b, on=['line', 'hour'], how='inner').to_csv(ROOT + 'data/train_line_bivariate.csv', index=False)
# Binless bivariate colour: blue = how big a share of the line's weekday travel falls in the hour,
# orange = how crowded the trains are. Both go through a square-root curve (the data are skewed) and the two ramps
# the hue slides from blue to orange, and the cell darkens where both are high. Blue and orange stay distinct for every
# common type of colour blindness, and the light-to-dark axis carries the amount.
S_CAP, L_CAP, GRID = 12, 330, 24
PAPER = (247, 244, 239)                                  # colour of a quiet, uncrowded cell
BLUE, MID, ORANGE = (33, 102, 172), (52, 64, 88), (230, 100, 10)   # full-strength blue, slate where both are high, orange


def colour_calcs(ts, tl):
    """calculate transforms turning two 0-1 values (given as expressions) into one CSS colour called 'col'.
    Hue: blue when the 'busy' value dominates, orange when the 'crowded' value dominates, slate in between.
    The balance is sharpened with a smoothstep so only evenly balanced cells are grey. Strength follows the larger value."""
    out = [{'calculate': ts, 'as': 'tS'}, {'calculate': tl, 'as': 'tL'},
           {'calculate': '(datum.tS + datum.tL) == 0 ? 0.5 : datum.tL / (datum.tS + datum.tL)', 'as': 'w0'},
           {'calculate': 'max(0, min(1, (datum.w0 - 0.3) / 0.4))', 'as': 'u'},
           {'calculate': 'datum.u * datum.u * (3 - 2 * datum.u)', 'as': 'w'},
           {'calculate': 'pow(max(datum.tS, datum.tL), 0.8)', 'as': 'a'}, {'calculate': 'min(datum.tS, datum.tL)', 'as': 'm'}]
    for k, name in enumerate('rgb'):
        base = (f'(datum.w < 0.5 ? {BLUE[k]} * (1 - 2 * datum.w) + {MID[k]} * 2 * datum.w'
                f' : {MID[k]} * (2 - 2 * datum.w) + {ORANGE[k]} * (2 * datum.w - 1))')
        out.append({'calculate': f'({PAPER[k]} + ({base} - {PAPER[k]}) * datum.a) * (1 - 0.5 * datum.m)', 'as': name})
    out.append({'calculate': "'rgb(' + round(datum.r) + ',' + round(datum.g) + ',' + round(datum.b) + ')'", 'as': 'col'})
    return out


BIV_COLOR = {'field': 'col', 'type': 'nominal', 'scale': None, 'legend': None}
_a = pd.read_csv(ROOT + 'data/train_line_hour.csv')
_b = pd.read_csv(ROOT + 'data/train_line_load.csv')[['line', 'hour', 'load', 'n']]
_a.merge(_b, on=['line', 'hour'], how='inner').to_csv(ROOT + 'data/train_line_bivariate.csv', index=False)
save('14_train_line_hour_heatmap', {
    'title': {'text': 'Melbourne trains by line and hour: how busy the hour is and how crowded the trains are (weekdays)',
              'subtitle': 'Blue shows a bigger share of the line\'s weekday travel, orange shows more crowded trains, and dark slate grey means both. Blank cells have too few sampled trips.'},
    'hconcat': [
        {'width': 480, 'height': 380,
         'data': {'url': 'data/train_line_bivariate.csv'},
         'transform': TRH + colour_calcs(f'sqrt(min(datum.share_pct, {S_CAP}) / {S_CAP})', f'sqrt(min(datum.load, {L_CAP}) / {L_CAP})'),
         'mark': {'type': 'rect', 'stroke': 'white', 'strokeWidth': 1},
         'encoding': {'x': HR(True),
                      'y': {'field': 'line', 'type': 'nominal', 'title': None, 'sort': {'field': 'peak_share', 'op': 'max', 'order': 'descending'}},
                      'color': BIV_COLOR,
                      'tooltip': [{'field': 'line', 'title': 'Line'}, {'field': 'hour', 'title': 'Hour starting'},
                                  {'field': 'share_pct', 'title': 'Share of the line\'s weekday travel (%)'},
                                  {'field': 'load', 'title': 'Average passengers on board'},
                                  {'field': 'n', 'title': 'Sample trips'}]}},
        {'title': {'text': 'Colour key', 'fontSize': 11}, 'width': 130, 'height': 130,
         'data': {'sequence': {'start': 0, 'stop': GRID * GRID, 'as': 'i'}},
         'transform': [{'calculate': f'datum.i % {GRID}', 'as': 'ix'}, {'calculate': f'floor(datum.i / {GRID})', 'as': 'iy'},
                       *colour_calcs(f'(datum.iy + 0.5) / {GRID}', f'(datum.ix + 0.5) / {GRID}'),
                       {'calculate': f'{L_CAP} * pow(datum.ix / {GRID}, 2)', 'as': 'x0'},
                       {'calculate': f'{L_CAP} * pow((datum.ix + 1) / {GRID}, 2)', 'as': 'x1'},
                       {'calculate': f'{S_CAP} * pow(datum.iy / {GRID}, 2)', 'as': 'y0'},
                       {'calculate': f'{S_CAP} * pow((datum.iy + 1) / {GRID}, 2)', 'as': 'y1'}],
         'mark': {'type': 'rect'},
         'encoding': {'x': {'field': 'x0', 'type': 'quantitative', 'title': ['Passengers on board'],
                            'scale': {'type': 'sqrt', 'domain': [0, L_CAP], 'nice': False},
                            'axis': {'values': [0, 50, 100, 200, L_CAP], 'labelExpr': f"datum.value == {L_CAP} ? '{L_CAP}+' : datum.value", 'labelAngle': 0}},
                      'x2': {'field': 'x1'},
                      'y': {'field': 'y0', 'type': 'quantitative', 'title': ['Share of line\'s', 'weekday travel (%)'],
                            'scale': {'type': 'sqrt', 'domain': [0, S_CAP], 'nice': False},
                            'axis': {'values': [0, 1, 3, 6, S_CAP], 'labelExpr': f"datum.value == {S_CAP} ? '{S_CAP}+' : datum.value"}},
                      'y2': {'field': 'y1'},
                      'color': BIV_COLOR}}]})

print('wrote', sorted(os.listdir(SPECS)))
