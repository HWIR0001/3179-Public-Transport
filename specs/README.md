# Chart spec guide

Charts are numbered 1-19 in the order they appear on the page; the number is in the file name (`07_pt_share_dumbbell.json` is Chart 7) and shown above each chart.

JSON cannot hold comments, so this file explains each spec. Every spec also has a one-line `description` field at the top level.

Reading a spec: `data` = which file feeds it, `transform` = calculations done before drawing, `mark` = the shape (line, bar, circle...), `encoding` = which data field drives which visual channel (x, y, colour, size, opacity). A spec with `layer` stacks several of these on top of each other.


## Chart 1: 01_national_trips.json
**Trips on city public transport, all eight capitals**  
Streamgraph of yearly trips by mode, all eight capitals. Bus sits under train so the share shift is visible; labels give 1977-2025 shares.

- Layer 1: `rect` from `inline values`; 0 transform(s); encodes x=a, x2=b
- Layer 2: `area` from `data/national_mode_share.csv`; 0 transform(s); encodes x=year_end, y=trips_million, color=mode, order=ord
- Layer 3: `text` from `inline values`; 1 transform(s); encodes x=x, y=y, text=t
- Layer 4: `text` from `inline values`; 1 transform(s); encodes x=x, y=y, text=t
- Layer 5: `text` from `inline values`; 1 transform(s); encodes x=x, y=y, text=t
- Layer 6: `text` from `inline values`; 0 transform(s); encodes x=x, y=y, text=t

## Chart 2: 02_trips_per_person.json
**Riding versus driving, 2024-25**  
Bubble scatter where each bubble is a donut of the city mode mix. x = trips per person, y = car km per person vs the average. Brisbane and Perth are offset and linked by leader lines.

- Layer 1: `rule` from `inline values`; 0 transform(s); encodes y=y
- Layer 2: `rule` from `inline values`; 0 transform(s); encodes x=x
- Layer 3: `text` from `inline values`; 0 transform(s); encodes x=x, y=y, text=t
- Layer 4: `text` from `inline values`; 0 transform(s); encodes x=x, y=y, text=t
- Layer 5: `rule` from `inline values`; 0 transform(s); encodes x=x0, x2=xd, y=y0, y2=yd
- Layer 6: `circle` from `inline values`; 0 transform(s); encodes x=x0, y=y0
- Layer 7: `circle` from `inline values`; 0 transform(s); encodes x=x, y=cy, size=sz
- Layer 8: `text` from `inline values`; 0 transform(s); encodes x=x, y=top, text=lab
- Layer 9: `text` from `inline values`; 0 transform(s); encodes x=x, y=cy, text=t
- Layer 10: `text` from `inline values`; 0 transform(s); encodes x=xd, y=ly, text=city
- Layer 11: `arc` from `data/city_mode_long.csv`; 6 transform(s); encodes x=xd, y=yd, theta=a0, theta2=a1, radius=pop, color=mode, opacity=value

## Chart 3: 03_national_map.json
**Trips in 2024-25 as % of 2018-19. Each state is coloured by its capital city.**  
Choropleth: each state is coloured by its capital city's 2024-25 trips as % of 2018-19. Number of dots = total trips (1 dot = 20 million).

- Layer 1: `geoshape` from `shared data`; 0 transform(s); encodes nothing (constant)
- Layer 2: `geoshape` from `data/australia_states.json`; 2 transform(s); encodes color=index_2018_19
- Layer 3: `circle` from `data/city_dots.csv`; 0 transform(s); encodes longitude=lon, latitude=lat
- Layer 4: `circle` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat
- Layer 5: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=t
- Layer 6: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=t
- Layer 7: `rule` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, longitude2=lon2, latitude2=lat2
- Layer 8: `text` from `inline values`; 0 transform(s); encodes longitude=lon2, latitude=lat2, text=lab
- Layer 9: `text` from `inline values`; 0 transform(s); encodes longitude=lon2, latitude=lat2, text=lab
- Layer 10: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=lab
- Layer 11: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=lab
- Layer 12: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=lab
- Layer 13: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=lab
- Layer 14: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=lab
- Layer 15: `text` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, text=lab

## Chart 4: 04_change_by_mode.json
**Change in yearly trips per resident since 2018-19, by city and mode**  
Diverging stacked bars: change in trips per resident since 2018-19, by city and mode. Diamond = net; right-hand note = net change in total trips.

- Layer 1: `rule` from `data/city_mode_recovery.csv`; 0 transform(s); encodes x=?
- Layer 2: `bar` from `data/city_mode_recovery.csv`; 0 transform(s); encodes x=change_pc, color=mode, order=mode
- Layer 3: `point` from `data/city_mode_recovery.csv`; 0 transform(s); encodes x=net_pc
- Layer 4: `text` from `data/city_mode_recovery.csv`; 2 transform(s); encodes x=14, text=net_lab
- Layer 5: `text` from `inline values`; 0 transform(s); encodes x=x, y=y, text=t
- Layer 6: `text` from `inline values`; 0 transform(s); encodes x=x, y=y, text=t

## Chart 5: 05_city_recovery_multiples.json
**Trips each year compared with 2018-19 (2018-19 = 100), all eight cities**  
Lines: each city's yearly trips indexed to 2018-19 = 100. End labels are kept in value order with leader lines.

- Layer 1: `rect` from `inline values`; 0 transform(s); encodes x=a, x2=b
- Layer 2: `rule` from `data/city_totals_recovery.csv`; 0 transform(s); encodes y=100
- Layer 3: `line` from `data/city_totals_recovery.csv`; 0 transform(s); encodes x=year_end, y=index_2018_19, color=city, strokeWidth=value
- Layer 4: `rule` from `inline values`; 0 transform(s); encodes x=x0, color=city, x2=x1, y=v, y2=y
- Layer 5: `text` from `inline values`; 0 transform(s); encodes x=x1, y=y, text=lab, color=city
- Layer 6: `text` from `inline values`; 0 transform(s); encodes x=x, y=y, text=t
- Layer 7: `point` from `inline values`; 0 transform(s); encodes x=year_end, y=index, color=city
- Layer 8: `rule` from `inline values`; 0 transform(s); encodes x=x0, x2=x1, y=index
- Layer 9: `text` from `inline values`; 0 transform(s); encodes x=x0, y=index, text=lab

## Chart 6: 06_trips_per_person_trend.json
**Public transport trips per resident since 2001**  
Lines: public transport trips per resident since 2001, with spaced end labels.

- Layer 1: `line` from `data/city_pop_trips.csv`; 0 transform(s); encodes x=year_end, y=trips_per_person, color=city
- Layer 2: `rule` from `inline values`; 0 transform(s); encodes x=x0, color=city, x2=x1, y=v, y2=y
- Layer 3: `text` from `inline values`; 0 transform(s); encodes x=x1, y=y, text=lab, color=city

## Chart 7: 07_pt_share_dumbbell.json
**['COVID-19 effect on public transport', 'share of distance travelled']**  
Dumbbell: public transport share of passenger-km by city before COVID-19 (2018-19), at its COVID-19 low point (year printed on the dot) and after (2024-25).

- Layer 1: `line` from `data/car_vs_pt.csv`; 0 transform(s); encodes detail=city
- Layer 2: `circle` from `data/car_vs_pt.csv`; 0 transform(s); encodes color=period
- Layer 3: `text` from `data/car_vs_pt.csv`; 1 transform(s); encodes text=fy

## Chart 8: 08_monthly_sydney_melbourne.json
**Sydney**  
Two line panels: monthly trips by mode vs the 2019 average (2019 = 100) for Sydney and Melbourne.

- Layer 1: `rule` from `shared data`; 0 transform(s); encodes y=100
- Layer 2: `line` from `shared data`; 0 transform(s); encodes x=month, y=index_2019, color=mode
- Layer 3: `text` from `inline values`; 0 transform(s); encodes x=d, y=y, text=t
- Layer 4: `text` from `inline values`; 0 transform(s); encodes x=d, y=y, text=t
- Layer 5: `rule` from `shared data`; 0 transform(s); encodes y=100
- Layer 6: `line` from `shared data`; 0 transform(s); encodes x=month, y=index_2019, color=mode
- Layer 7: `text` from `inline values`; 0 transform(s); encodes x=d, y=y, text=t
- Layer 8: `text` from `inline values`; 0 transform(s); encodes x=d, y=y, text=t

## Chart 9: 09_adelaide_daily.json
**Adelaide: Metrocard touch-ons per day (thousands), April to June 2026 (at least)**  
Calendar heatmap of Adelaide Metrocard touch-ons per day (thousands); red outline = public holiday.

- Layer 1: `rect` from `data/adelaide_daily.csv`; 0 transform(s); encodes x=week_start, y=weekday, color=touch_k
- Layer 2: `rect` from `data/adelaide_daily.csv`; 1 transform(s); encodes x=week_start, y=weekday, stroke=Public holiday
- Layer 3: `text` from `data/adelaide_daily.csv`; 1 transform(s); encodes x=week_start, y=weekday

## Chart 10: 10_train_hours_by_day.json
**Melbourne trains: share of a day's travel by hour, for each type of day**  
Lines: share of a day's Melbourne train loads by hour for each day type. Hours above 23 are after midnight.

- Layer 1: `rect` from `inline values`; 0 transform(s); encodes x=a, x2=b
- Layer 2: `text` from `inline values`; 0 transform(s); encodes x=x, y=17.5, text=t
- Layer 3: `line` from `data/train_hourly_daytype.csv`; 0 transform(s); encodes x=hour, y=share_pct, color=day, strokeDash=day

## Chart 11: 11_canberra_hourly.json
**Canberra: share of daily boardings by hour, July to February, before and during COVID-19**  
Lines: share of Canberra bus boardings by hour, July to February of 2019-20 and 2020-21; peak windows shaded.

- Layer 1: `rect` from `inline values`; 0 transform(s); encodes x=x, x2=x2
- Layer 2: `text` from `inline values`; 0 transform(s); encodes x=x, y=17, text=t
- Layer 3: `line` from `data/canberra_hourly.csv`; 0 transform(s); encodes x=hour, y=share_pct, color=period

## Chart 12: 12_train_tidal_flow.json
**Melbourne trains: weekday travel towards and away from the city**  
Diverging bars: weekday train loads towards the city (above zero) and away from it (below) by hour.

- Layer 1: `bar` from `data/train_tidal.csv`; 0 transform(s); encodes x=h, y=share_signed, color=direction
- Layer 2: `rule` from `data/train_tidal.csv`; 0 transform(s); encodes y=?

## Chart 13: 13_train_line_peaks.json
**Melbourne trains: how much of each line's weekday travel falls in the two peaks**  
Lollipop/bubble: share of each line's weekday travel in the two peaks; bubble size = line's share of all train travel.

- Layer 1: `rule` from `data/train_line_share.csv`; 0 transform(s); encodes x=x0, x2=peak_share
- Layer 2: `circle` from `data/train_line_share.csv`; 0 transform(s); encodes x=peak_share, size=share_pct

## Chart 14: 14_train_line_hour_heatmap.json
**Melbourne trains by line and hour: how busy the hour is and how crowded the trains are (weekdays)**  
Binless bivariate heatmap by line and hour: blue = share of the line's weekday travel, orange = passengers on board. Colour is computed in the spec; the key is generated from a sequence.

- Layer 1: `rect` from `data/train_line_bivariate.csv`; 12 transform(s); encodes x=h, y=line, color=col
- Layer 2: `rect` from `sequence`; 17 transform(s); encodes x=x0, x2=x1, y=y0, y2=y1, color=col

## Chart 15: 15_sydney_stations.json
**Sydney: busiest stations, last 12 months of data**  
Proportional-symbol map of Sydney station entries: size, yellow shade and opacity all show usage. Rail lines and postcodes as base layers.

- Layer 1: `geoshape` from `data/syd_poa.json`; 0 transform(s); encodes stroke=Postcode boundary
- Layer 2: `geoshape` from `data/syd_rail.json`; 0 transform(s); encodes stroke=Rail line
- Layer 3: `circle` from `data/syd_stations.csv`; 0 transform(s); encodes longitude=lon, latitude=lat, size=?, color=entries, opacity=entries, order=entries
- Layer 4: `rule` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, longitude2=lon2, latitude2=lat2
- Layer 5: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 6: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 7: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 8: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 9: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 10: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label

## Chart 16: 16_melbourne_stations.json
**Melbourne: busiest train stations, 2024-25**  
Same encoding as chart 13 for Melbourne train stations, using the same scales.

- Layer 1: `geoshape` from `data/melb_poa.json`; 0 transform(s); encodes stroke=Postcode boundary
- Layer 2: `geoshape` from `data/melb_rail.json`; 0 transform(s); encodes stroke=Rail line
- Layer 3: `circle` from `data/melb_stations.csv`; 0 transform(s); encodes longitude=lon, latitude=lat, size=?, color=entries, opacity=entries, order=entries
- Layer 4: `rule` from `inline values`; 0 transform(s); encodes longitude=lon, latitude=lat, longitude2=lon2, latitude2=lat2
- Layer 5: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 6: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 7: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 8: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 9: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label
- Layer 10: `text` from `inline values`; 1 transform(s); encodes longitude=lon2, latitude=lat2, text=label

## Chart 17: 17_melbourne_lines.json
**Melbourne: estimated train station entries by line, 2024-25 (millions)**  
Bars: estimated Melbourne station entries by train line; station entries are split across the lines serving them.

- Layer 1: `bar` from `data/melb_lines.csv`; 0 transform(s); encodes y=line, x=entries_million, color=kind, order=kind
- Layer 2: `text` from `data/melb_lines.csv`; 3 transform(s); encodes y=line, x=total, text=total

## Chart 18: 18_melbourne_stops.json
**Melbourne: every stop and station**  
Dot map of every Melbourne stop, coloured by mode, over postcode outlines.

- Layer 1: `geoshape` from `data/melb_poa.json`; 0 transform(s); encodes stroke=Postcode boundary
- Layer 2: `circle` from `data/melb_stops.csv`; 3 transform(s); encodes longitude=lon, latitude=lat, order=z, size=sz, color=mode

## Chart 19: 19_brisbane_stops.json
**South East Queensland: boardings at every stop, July 2026**  
Map of every South East Queensland stop, station and wharf: colour = mode, opacity = boardings in July 2026 (TransLink origin-destination trips), with rail lines.

- Layer 1: `geoshape` from `data/seq_poa.json`; 0 transform(s); encodes stroke=Postcode boundary
- Layer 2: `geoshape` from `data/bris_rail.geojson`; 0 transform(s); encodes stroke=Rail line
- Layer 3: `circle` from `data/bris_stops.csv`; 3 transform(s); encodes longitude=lon, latitude=lat, order=z, size=sz, color=mode, opacity=boardings
