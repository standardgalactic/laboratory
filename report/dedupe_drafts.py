#!/usr/bin/env python3
"""dedupe_drafts.py - keep only the most recent draft of each essay.

Usage: python3 dedupe_drafts.py gaps.json tex_mtimes.json out.json [--groups draft-groups.csv] [--roots DIR] [--keep keep.txt]

keep.txt: one repo/path per line (as shown in draft-groups.csv) to force a draft to be the kept one.

Drafts are grouped when they share a normalized path within a repository
(draft-01/, draft 03, -v2, _v02, version3 ... removed) or a normalized title
anywhere in the corpus (draft/version words and punctuation removed; only
titles of 4+ words or 25+ characters, so generic titles like "Essay" never merge).
The kept draft is the one whose content was edited most recently (moves and exact
copies inherit the date of the edit they came from; identical copies are one version); ties go to the
highest draft/version number, then to the one with more citations, then more words.
"""
import json, re, sys, os
from collections import defaultdict

VER = r'(?:\b|_|(?<=\d))(?:draft|drafts|version|ver|rev|revision|v)[\s_\-\.]*0*(\d+)|\(\s*(\d+)\s*\)|[\s_\-]+0*(\d{1,2})(?=\.tex$|$)'
GENERIC = {'main', 'essay', 'monograph', 'paper', 'document', 'book', 'draft', 'index', 'article', 'report', 'thesis', 'notes'}


def draft_no(s):
    nums = [int(x) for m in re.findall(VER, s, re.I) for x in m if x]
    return max(nums) if nums else -1


def draft_key(s):
    """(scheme, number): explicit draft/version words rank above bare or (N) copy numbers,
    which rank above no number at all (treated as draft 0), which ranks above a bare "draft"."""
    found = re.findall(VER, s, re.I)
    if not found and re.search(r'(^|[/_\-\s])drafts?($|[/_\-\s.])', s, re.I):
        return (-1, 0)   # an unnumbered "draft" sits below the unmarked final
    best = (0, 0)
    for a, b, c in found:
        best = max(best, (2, int(a)) if a else (1, int(b or c)))
    return best


def norm_path(p):
    p = p.lower()
    p = re.sub(r'\.tex$', '', p)
    p = re.sub(VER, '', p, flags=re.I)
    p = re.sub(r'(^|/)(drafts?|final|old|new|latest|current)(?=/|$)', r'\1', p)
    p = re.sub(r'[\s_\-\.]+', '-', p)
    p = re.sub(r'-+(?=/|$)|(?<=/)-+', '', p)
    p = re.sub(r'/+', '/', p).strip('/-')
    return p


def norm_title(t):
    t = t.lower()
    t = re.sub(VER, ' ', t, flags=re.I)
    t = re.sub(r'\b(draft|revised|final|preprint|working paper)\b', ' ', t)
    t = re.sub(r'[^a-z0-9]+', ' ', t).strip()
    return t


def locate(repo, path, roots):
    owner, name = (repo.split('/', 1) if '/' in repo else ('standardgalactic', repo))
    for base in roots:
        for p in (os.path.join(base, name, path), os.path.join(base, 'flyxion-corpus', 'sources', owner, name, path)):
            if os.path.isfile(p):
                return p
    return None


def text_hash(p):
    import hashlib
    try:
        t = open(p, encoding='utf-8', errors='replace').read()
    except (OSError, TypeError):
        return None
    t = re.sub(r'(?<!\\)%.*', '', t)
    return hashlib.sha1(re.sub(r'\s+', '', t).encode()).hexdigest()


def main():
    src, mt, dst = sys.argv[1:4]
    roots = [sys.argv[sys.argv.index('--roots') + 1]] if '--roots' in sys.argv else ['.']
    keep_over = set()
    if '--keep' in sys.argv and os.path.isfile(sys.argv[sys.argv.index('--keep') + 1]):
        keep_over = {l.strip() for l in open(sys.argv[sys.argv.index('--keep') + 1]) if l.strip() and not l.startswith('#')}
    R = json.load(open(src, encoding='utf-8'))
    M = json.load(open(mt))
    parent = list(range(len(R)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        parent[find(a)] = find(b)

    by_path, by_title = {}, {}
    for i, r in enumerate(R):
        k = (r['repo'], norm_path(r['path']))
        if k in by_path: union(i, by_path[k])
        else: by_path[k] = i
        t = norm_title(r['title'])
        base = os.path.splitext(os.path.basename(r['path']))[0].lower()
        if t and t not in GENERIC and t != base and (len(t.split()) >= 4 or len(t) >= 25):
            if t in by_title: union(i, by_title[t])
            else: by_title[t] = i

    for r in R:
        full = r['repo'] if '/' in r['repo'] else 'standardgalactic/' + r['repo']
        r['mtime'] = M.get(full, {}).get(r['path'], 0) or 0
        r['draft_no'] = max(draft_no(r['path']), draft_no(r['title']))
        r['dkey'] = max(draft_key(r['path']), draft_key(r['title']))
        r['hash'] = text_hash(locate(r['repo'], r['path'], roots))

    groups = defaultdict(list)
    for i in range(len(R)):
        groups[find(i)].append(i)

    kept, rows = [], []
    for members in groups.values():
        # identical copies count as one version dated by the earliest copy (the original edit)
        first = {}
        for i in members:
            h = R[i]['hash'] or i
            if R[i]['mtime'] and (h not in first or R[i]['mtime'] < first[h]):
                first[h] = R[i]['mtime']
        # an identical copy is ranked as the original: the lowest-ranked twin
        twin = {}
        for i in members:
            h = R[i]['hash'] or i
            twin[h] = min(twin.get(h, (9, 10 ** 6)), R[i]['dkey'])
        for i in members:
            R[i]['eff'] = first.get(R[i]['hash'] or i, R[i]['mtime'])
            R[i]['rank'] = twin[R[i]['hash'] or i]
        key = lambda i: (f"{R[i]['repo']}/{R[i]['path']}" in keep_over, R[i]['eff'], R[i]['rank'], R[i]['cites'], R[i]['words'])
        ms = sorted(members, key=key, reverse=True)
        size = lambda i: 40 * R[i]['cites'] + R[i]['words']   # a citation counts like 40 words of development
        dev = lambda a, b: size(a) > 1.5 * size(b) + 500
        developed = False
        if not key(ms[0])[0]:
            tied = [i for i in ms if R[i]['eff'] == R[ms[0]]['eff']]
            better = [i for i in tied[1:] if R[i]['hash'] != R[ms[0]]['hash'] and dev(i, ms[0])]
            if better:
                # same commit, so the name is the only order signal; references go into the last version,
                # so a clearly more developed draft is taken to be the later one
                best = max(better, key=size)
                ms.remove(best); ms.insert(0, best); developed = True
        k = R[ms[0]]
        how = 'override' if key(ms[0])[0] else 'development' if developed else ('date' if len(ms) == 1 or R[ms[0]]['eff'] != R[ms[1]]['eff'] else
               ('draft number' if R[ms[0]]['rank'] != R[ms[1]]['rank'] else 'citations/length'))
        k['kept_by'] = how
        # flag for review when an older draft looks clearly more developed than the kept one
        k['review'] = developed or any(R[j]['hash'] != k['hash'] and dev(j, ms[0]) for j in ms[1:])
        if k['review']:
            how += ', CHECK'
        k['superseded'] = [{'repo': R[j]['repo'], 'path': R[j]['path'], 'mtime': R[j]['eff'], 'words': R[j]['words'], 'cites': R[j]['cites']} for j in ms[1:]]
        kept.append(k)
        if len(ms) > 1:
            for n, j in enumerate(ms):
                rows.append((k['title'][:80], ('KEEP by ' + how) if n == 0 else 'drop', R[j]['eff'], R[j]['draft_no'], R[j]['cites'], R[j]['words'], f"{R[j]['repo']}/{R[j]['path']}"))

    for k in kept:
        for f in ('hash', 'dkey', 'rank', 'eff'):
            k.pop(f, None)
    kept.sort(key=lambda r: -r['score'])
    json.dump(kept, open(dst, 'w', encoding='utf-8'), indent=1)
    if '--groups' in sys.argv:
        import time
        with open(sys.argv[sys.argv.index('--groups') + 1], 'w', encoding='utf-8', newline='') as f:
            # CSV rather than TSV: the laboratory repository's .gitignore excludes *.tsv
            import csv
            out = csv.writer(f)
            out.writerow(['title', 'decision', 'last_edit', 'draft_no', 'cites', 'words', 'file'])
            for t, d, m, dn, c, w, p in rows:
                out.writerow([t, d, time.strftime('%Y-%m-%d %H:%M', time.gmtime(m)) if m else '?', dn if dn >= 0 else '', c, w, p])
    print(f'{len(R)} documents -> {len(kept)} essays ({len(R) - len(kept)} earlier drafts removed, '
          f'{sum(1 for k in kept if k["superseded"])} essays had drafts, {sum(1 for k in kept if k.get("review"))} flagged CHECK)', file=sys.stderr)


if __name__ == '__main__':
    main()
