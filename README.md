# Buses, trains, trams and ferries: who came back?

FIT3179 Data Visualisation 2 (Monash, Semester 2 2026), topic 20: Urban Public Transport.
Author: Hilman Wiraatmaja (34141685).

A single-page Vega-Lite dashboard comparing public transport in Australia's eight capital cities.

## Files
- `index.html`: the page (text, layout, and the script that loads each chart).
- `specs/`: one readable Vega-Lite JSON spec per chart (each has a one-line `description`).
- `data/`: reduced CSV and GeoJSON files the charts read (about 1.7 MB in total).
- `scripts/`: Python used to reduce the raw data and generate the specs and page. Not needed to run the site. (legacy, many modifications were performed afterwards, kept as a trace)

## How to read the code (start here)
1. `index.html`: open it in a text editor. The CSS is at the top (comments explain the layout), then the page text, then a short script at the bottom. The script has one list, `CHARTS`, that pairs each chart box with a spec file, then `fetch`es the spec and draws it with vega-embed. `themed()` only recolours a copy of the spec for dark mode.
2. `specs/README.md`: a plain-English guide to every chart spec (JSON cannot hold comments). Each spec also has a one-line `description`.
3. `scripts/build_dashboard.py`: the code that writes the specs. Every chart section starts with a WHAT / WHY / HOW comment.
4. `scripts/shrink.py`: how the raw data was cut down to the small files in `data/`. `seq_boardings.py` builds the Queensland stop file.

## Chart numbers
Charts are numbered 1-19 in page order. The number appears above each chart on the page, in the spec file name (`07_pt_share_dumbbell.json` is Chart 7) and in the `# N ---` comment above each chart in `scripts/build_dashboard.py`. Quote the number when you want a change.

## View it
Enable GitHub Pages (Settings > Pages > deploy from the main branch, root folder). Charts load specs with `fetch`, so open the page through Pages or a local server (`python3 -m http.server`), not by double-clicking the file.

## Data sources
BITRE Yearbook 2025; ABS population and boundaries (ASGS Edition 4, CC BY 4.0); Transport for NSW Open Data; Victoria Department of Transport and Planning; Queensland Government and TransLink; Government of South Australia; ACT Government Open Data. Full list in the page footer.

## AI acknowledgement
Claude (Anthropic) helped reduce the data files, check numbers and write the chart specifications. See the page footer.
