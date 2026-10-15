"""Writes specs/README.md: a plain-English summary of every chart spec (JSON itself cannot hold comments)."""
import json, glob, os
D = '/home/claude/dashboard/specs/'
def enc(e):
    return ', '.join(f"{k}={v.get('field') or v.get('datum') or ('value' if 'value' in v else '?')}" for k, v in e.items() if isinstance(v, dict) and k != 'tooltip')
def layers(sp):
    if 'layer' in sp: return sp['layer']
    if 'hconcat' in sp: return [l for h in sp['hconcat'] for l in layers(h)]
    return [sp]
o = ["# Chart spec guide\n", "Charts are numbered 1-19 in the order they appear on the page; the number is in the file name (`07_pt_share_dumbbell.json` is Chart 7) and shown above each chart.\n",
     "JSON cannot hold comments, so this file explains each spec. Every spec also has a one-line `description` field at the top level.\n",
     "Reading a spec: `data` = which file feeds it, `transform` = calculations done before drawing, `mark` = the shape (line, bar, circle...), `encoding` = which data field drives which visual channel (x, y, colour, size, opacity). A spec with `layer` stacks several of these on top of each other.\n"]
for f in sorted(glob.glob(D + '*.json')):
    sp = json.load(open(f)); n = os.path.basename(f)
    title = sp.get('title') or (sp.get('hconcat', [{}])[0].get('title'))
    if isinstance(title, dict): title = title.get('text')
    o.append(f"\n## Chart {int(n[:2])}: {n}\n**{title}**  \n{sp.get('description', '')}\n")
    for i, l in enumerate(layers(sp), 1):
        d = l.get('data', sp.get('data', {}))
        src = d.get('url') or ('inline values' if 'values' in d else 'sequence' if 'sequence' in d else 'shared data')
        m = l.get('mark'); m = m.get('type') if isinstance(m, dict) else m
        o.append(f"- Layer {i}: `{m}` from `{src}`; {len(l.get('transform', []))} transform(s); encodes {enc(l.get('encoding', {})) or 'nothing (constant)'}")
open(D + 'README.md', 'w').write('\n'.join(o) + '\n')
