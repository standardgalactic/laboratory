#!/usr/bin/env python3
"""content_mtimes.py - last time each .tex file's CONTENT changed, following exact
renames and exact copies back to the edit that produced the content.
Usage: python3 content_mtimes.py gaps.json BARE_REPO_DIR... > tex_mtimes.json  (dir names owner_repo)
Dates the paths listed in gaps.json, so files renamed since a snapshot are still found."""
import subprocess, sys, json, os
res = {}
need = {}
for r in json.load(open(sys.argv[1], encoding='utf-8')):
    full = r['repo'] if '/' in r['repo'] else 'standardgalactic/' + r['repo']
    need.setdefault(full, set()).add(r['path'])
for d in sys.argv[2:]:
    repo = os.path.basename(d.rstrip('/')).replace('_', '/', 1)
    waiting = {p: {p} for p in need.get(repo, ())}
    times = {}
    log = subprocess.run(['git', '-c', 'core.quotePath=false', '-C', d, 'log', '--format=@%ct', '--name-status', '-M100%', '-C100%', '--find-copies-harder', 'HEAD'],
                         capture_output=True, text=True).stdout
    t = None
    for line in log.split('\n'):
        if not line: continue
        if line[0] == '@': t = int(line[1:]); continue
        f = line.split('\t'); st = f[0]
        if st[0] in 'RC' and st[1:] == '100':
            old, new = f[1], f[2]
            if new in waiting:
                ws = waiting.pop(new)
                waiting.setdefault(old, set()).update(ws)
        elif st[0] == 'D':
            continue
        else:
            p = f[-1]
            if p in waiting:
                for h in waiting.pop(p): times.setdefault(h, t)
        if not waiting: break
    res[repo] = times
    print(f'{repo:40s} {len(times)}/{len(need.get(repo, ()))} dated', file=sys.stderr)
json.dump(res, sys.stdout)
