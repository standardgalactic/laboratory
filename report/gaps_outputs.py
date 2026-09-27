#!/usr/bin/env python3
"""gaps_outputs.py - write gaps.md and gaps.csv from a (deduplicated) gaps JSON.

Usage: python3 gaps_outputs.py gaps_latest.json gaps.md gaps.csv

gaps.md keeps the format split_queues.py parses; each essay also gets a line
naming the earlier drafts that were set aside (ignored by split_queues.py).
"""
import csv, json, sys, time

src, md, cs = sys.argv[1:4]
R = json.load(open(src, encoding='utf-8'))
counts = ['uncited_claims', 'uncited_works', 'stub_sections', 'unproved', 'markers']
with open(md, 'w', encoding='utf-8') as f:
    f.write('{% raw %}\n')
    for r in R:
        repo = r['repo'].replace('/', ':')   # owner:repo, so split_queues.py's first-slash split stays correct
        f.write(f"## {r['title']}\n`{repo}/{r['path']}` · {r['words']} words · "
                f"{r['cites']} cites ({r['cites_per_1k']}/1k) · {r['bib_entries']} bib entries\n\n")
        if r.get('superseded'):
            day = time.strftime('%Y-%m-%d', time.gmtime(r['mtime'])) if r.get('mtime') else '?'
            f.write(f"Latest draft (edited {day}, chosen by {r.get('kept_by', '')}); earlier drafts set aside: "
                    + ', '.join(f"`{s['repo']}/{s['path']}`" for s in r['superseded']) + "\n\n")
        for c in counts:
            for fp, ln, s in r['flags'].get(c, []):
                f.write(f"- [ ] **{c}** `{fp}:{ln}` {s}\n")
        if r['missing_keys']:
            f.write(f"- [ ] **missing bib keys**: {', '.join(r['missing_keys'])}\n")
        f.write('\n')
    f.write('{% endraw %}\n')
with open(cs, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['repo', 'path', 'title', 'words', 'cites', 'cites_per_1k', 'bib_entries', 'score'] + counts
               + ['missing_keys', 'unused_bib', 'last_edit', 'earlier_drafts', 'kept_by'])
    for r in R:
        w.writerow([r['repo'], r['path'], r['title'], r['words'], r['cites'], r['cites_per_1k'], r['bib_entries'], r['score']]
                   + [len(r['flags'].get(c, [])) for c in counts]
                   + [len(r['missing_keys']), len(r['unused_bib']),
                      time.strftime('%Y-%m-%d', time.gmtime(r['mtime'])) if r.get('mtime') else '',
                      len(r.get('superseded', [])), r.get('kept_by', '')])
print(f'wrote {md} and {cs} ({len(R)} essays)')
