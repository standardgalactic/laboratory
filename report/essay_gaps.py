#!/usr/bin/env python3
"""
essay_gaps.py - flag places in LaTeX essays that need references or more detail.

Usage:
    python3 essay_gaps.py ROOT [ROOT ...] [--csv out.csv] [--json out.json] [--md out.md]

A "document" is any .tex file containing \\documentclass; its \\input / \\include
files are pulled in recursively. .tex files that nothing includes and that have
no \\documentclass are reported as fragments.

Per document it reports:
  words, cites, cites_per_1k   citation density
  bib_entries, unused_bib      bibliography size / entries never cited
  missing_keys                 \\cite keys with no matching bib entry
  uncited_claims               sentences with empirical-claim wording and no \\cite
  uncited_works                "Author et al." / "(1999)" mentions with no \\cite
  stub_sections                sections whose own body is under STUB_WORDS words
  unproved                     theorem/proposition/lemma blocks with no proof after
  markers                      TODO, FIXME, TBD, [citation needed], ?? etc.
and a gap score used for ranking. Each flag carries a file:line so it can be
turned into an issue or an "open threads" list.
"""
import argparse, csv, hashlib, json, os, re, sys
from collections import defaultdict

STUB_WORDS = 60
CITE_RE = re.compile(r'\\(?:no)?(?:cite[a-zA-Z]*|[pP]arencite|[tT]extcite|autocite|footcite|citeauthor|citeyear)\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}')
BIBITEM_RE = re.compile(r'\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}')
BIBFILE_RE = re.compile(r'\\(?:bibliography|addbibresource)\{([^}]*)\}')
BIBENTRY_RE = re.compile(r'@(?!comment|string|preamble)\w+\s*\{\s*([^,\s]+)\s*,', re.I)
INPUT_RE = re.compile(r'\\(?:input|include|subfile)\{([^}]*)\}')
SECTION_RE = re.compile(r'\\(part|chapter|section|subsection)\*?(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}')
THM_RE = re.compile(r'\\begin\{(theorem|proposition|lemma|corollary|conjecture|claim)\}')
MARKER_RE = re.compile(r'\b(TODO|FIXME|TBD|XXX)\b|\[citation needed\]|\bcitation needed\b|\\cite\{\?+\}|\?\?\?|\bto be (?:written|added|expanded|completed)\b|(?:^|[\[(:])\s*placeholder\b|lorem ipsum|\bexpand (?:this|here)\b', re.I)
CLAIM_RE = re.compile(
    r"\b(studies (?:show|have shown|suggest|find|found)|research (?:shows|has shown|suggests|indicates)|"
    r"(?:it is|it has been) (?:well[- ]known|widely (?:known|accepted|believed)|established|shown|demonstrated)|"
    r"has (?:been|long been) (?:shown|demonstrated|observed|reported|documented)|"
    r"evidence (?:suggests|shows|indicates)|experiments? (?:show|have shown|demonstrate)|"
    r"recent (?:work|studies|research|papers?|results)|the literature|"
    r"meta-analys[ie]s|clinical trials?|randomi[sz]ed (?:controlled )?trials?|empirical(?:ly)? (?:work|studies|evidence|findings)|"
    r"surveys? (?:show|found)|data (?:show|suggest|indicate)|a (?:recent|landmark|well-known) (?:paper|study)|"
    r"\d+(?:\.\d+)?\s?(?:%|\\%|percent) of)", re.I)
WORK_RE = re.compile(r"\b[A-Z][a-zA-Z\-']+(?: and [A-Z][a-zA-Z\-']+)? et al\.?|\b[A-Z][a-zA-Z\-']+ \((?:1[5-9]|20)\d\d[a-z]?\)|\b[A-Z][a-zA-Z\-']+'s (?:\d{4}|paper|study|book|article)\b|\b[Aa]ccording to [A-Z][a-z]+\b(?! (?:view|theory|account|picture|framework|model)\b)|arXiv[: ]\s?\d{4}\.\d{4,5}")


def strip_comments(text):
    out = []
    for line in text.split('\n'):
        m = re.search(r'(?<!\\)%', line)
        out.append(line[:m.start()] if m else line)
    return '\n'.join(out)


def plain_words(s):
    s = re.sub(r'\\begin\{(equation|align|gather|multline|tikzpicture|verbatim|lstlisting)\*?\}.*?\\end\{\1\*?\}', ' ', s, flags=re.S)
    s = s.replace('\\$', ' ')
    s = re.sub(r'\$\$(?:(?!\n\s*\n).)*?\$\$|\\\[(?:(?!\n\s*\n).)*?\\\]|\\\((?:(?!\n\s*\n).)*?\\\)|\$(?:(?!\n\s*\n)[^$])*?\$', ' ', s, flags=re.S)
    s = re.sub(r'\\[a-zA-Z@]+\*?(\[[^\]]*\])?', ' ', s)
    s = re.sub(r'[{}\\&~^_]', ' ', s)
    return re.findall(r"[A-Za-z][A-Za-z'\-]+", s)


def read(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return ''


def resolve_input(base_dir, root_dir, name):
    name = name.strip()
    cands = [name, name + '.tex']
    for d in (base_dir, root_dir):
        for c in cands:
            p = os.path.normpath(os.path.join(d, c))
            if os.path.isfile(p):
                return p
    return None


def expand(path, root_dir, seen, lines):
    """Return list of (file, lineno, text) with inputs expanded inline."""
    if path in seen:
        return
    seen.add(path)
    base = os.path.dirname(path)
    for i, line in enumerate(strip_comments(read(path)).split('\n'), 1):
        m = INPUT_RE.search(line)
        if m:
            sub = resolve_input(base, root_dir, m.group(1))
            if sub:
                lines.append((path, i, line[:m.start()]))
                expand(sub, root_dir, seen, lines)
                lines.append((path, i, line[m.end():]))
                continue
        lines.append((path, i, line))


def load_bib(doc_text, doc_dir, root_dir):
    keys = set(k.strip() for k in BIBITEM_RE.findall(doc_text))
    for m in BIBFILE_RE.finditer(doc_text):
        for name in m.group(1).split(','):
            name = name.strip()
            for c in (name, name + '.bib'):
                for d in (doc_dir, root_dir):
                    p = os.path.join(d, c)
                    if os.path.isfile(p):
                        keys |= set(BIBENTRY_RE.findall(read(p)))
    return keys


def sentences_with_lines(lines):
    """Yield (file, line, sentence) by splitting paragraph text on sentence ends."""
    buf, start = [], None
    for f, ln, text in lines + [(None, 0, '')]:
        if f is None or not text.strip():
            if buf:
                para = ' '.join(t for _, _, t in buf)
                # map sentences back to approximate line
                pos = 0
                offsets = []
                for bf, bl, t in buf:
                    offsets.append((pos, bf, bl))
                    pos += len(t) + 1
                for m in re.finditer(r'[^.!?]+[.!?]?', para):
                    s = m.group(0).strip()
                    if len(s) < 25:
                        continue
                    loc = max((o for o in offsets if o[0] <= m.start()), key=lambda o: o[0])
                    yield loc[1], loc[2], s
            buf = []
            continue
        buf.append((f, ln, text))


def short(s, n=160):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n - 1] + '…'


def analyze(doc_path, root_dir):
    lines = []
    expand(doc_path, root_dir, set(), lines)
    text = '\n'.join(t for _, _, t in lines)
    body_m = re.search(r'\\begin\{document\}', text)
    words = plain_words(text[body_m.end():] if body_m else text)
    cited = []
    for m in CITE_RE.finditer(text):
        cited += [k.strip() for k in m.group(1).split(',') if k.strip()]
    bib = load_bib(text, os.path.dirname(doc_path), root_dir)
    cited_set = set(cited)
    flags = defaultdict(list)

    def rel(f):
        return os.path.relpath(f, root_dir)

    # claims / named works without citation
    in_bib = False
    for f, ln, s in sentences_with_lines(lines):
        if 'thebibliography' in s or '\\bibitem' in s:
            in_bib = True
        if in_bib or CITE_RE.search(s) or '\\href' in s or '\\url' in s:
            continue
        if CLAIM_RE.search(s):
            flags['uncited_claims'].append((rel(f), ln, short(s)))
        elif WORK_RE.search(s):
            flags['uncited_works'].append((rel(f), ln, short(s)))

    # sections and stubs
    secs = []
    for idx, (f, ln, t) in enumerate(lines):
        for m in SECTION_RE.finditer(t):
            secs.append((idx, m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip(), f, ln))
    levels = {'part': 0, 'chapter': 1, 'section': 2, 'subsection': 3}
    for k, (idx, lvl, title, f, ln) in enumerate(secs):
        nxt = secs[k + 1][0] if k + 1 < len(secs) else len(lines)
        has_child = k + 1 < len(secs) and levels[secs[k + 1][1]] > levels[lvl]
        body = '\n'.join(t for _, _, t in lines[idx:nxt])
        body = SECTION_RE.sub(' ', body, count=1)
        if re.search(r'\\end\{document\}', body):
            body = body[:body.index('\\end{document}')]
        n = len(plain_words(body))
        raw = len(body.split())
        if lvl in ('part', 'chapter') or (has_child and n < STUB_WORDS):
            continue
        if title.lower() in ('references', 'bibliography', 'acknowledgments', 'acknowledgements'):
            continue
        if n < STUB_WORDS and raw < 2.5 * STUB_WORDS:
            flags['stub_sections'].append((rel(f), ln, f'{lvl} "{short(title, 80)}" ({n} words)'))

    # unproved formal statements
    for idx, (f, ln, t) in enumerate(lines):
        m = THM_RE.search(t)
        if not m:
            continue
        window = '\n'.join(tt for _, _, tt in lines[idx:idx + 60])
        end = window.find('\\end{' + m.group(1) + '}')
        after = window[end:end + 1500] if end >= 0 else ''
        if m.group(1) != 'conjecture' and '\\begin{proof' not in after and 'Proof' not in after[:300]:
            flags['unproved'].append((rel(f), ln, m.group(1)))

    for f, ln, t in lines:
        for m in MARKER_RE.finditer(t):
            flags['markers'].append((rel(f), ln, short(t.strip())))
            break
        if re.search(r'(?<!\\)\?\?', t) and '\\ref' not in t:
            pass

    # if almost none of the cited keys are in the bib we found, we probably
    # resolved the wrong .bib file; don't report key-level mismatches then
    overlap = len(cited_set & bib)
    bib_ok = bool(bib) and (not cited_set or overlap >= 0.2 * len(cited_set))
    missing = sorted(k for k in cited_set if bib_ok and k not in bib)
    unused = sorted(k for k in bib if bib_ok and k not in cited_set)
    if not bib_ok and cited_set:
        bib = bib if bib and overlap else set()
        bib_note = 'bibliography file not resolved'
    else:
        bib_note = ''
    nw = len(words)
    cpk = 1000 * len(cited) / nw if nw else 0
    title_m = re.search(r'\\title\{((?:[^{}]|\{[^{}]*\})*)\}', text)
    title = short(re.sub(r'\\\\|\\[a-zA-Z]+|[{}]', ' ', title_m.group(1)), 100) if title_m else os.path.basename(doc_path)

    # gap score: per 1k words, so long and short documents compare fairly
    k = max(nw, 500) / 1000
    score = (
        3.0 * len(flags['uncited_claims']) / k
        + 1.5 * len(flags['uncited_works']) / k
        + 1.0 * len(flags['stub_sections']) / k
        + 1.0 * len(flags['unproved']) / k
        + 2.0 * len(flags['markers']) / k
        + (4.0 if len(bib) == 0 and not cited and nw > 1500 else 0)
        + (2.0 if cpk < 1 and nw > 1500 else 0)
        + min(0.5 * len(missing), 10)
    )
    return {
        'path': rel(doc_path), 'title': title, 'words': nw, 'files': len({f for f, _, _ in lines}),
        'cites': len(cited), 'cites_per_1k': round(cpk, 2), 'bib_entries': len(bib),
        'unused_bib': unused, 'missing_keys': missing, 'bib_note': bib_note, 'score': round(score, 2),
        'flags': {k: v for k, v in flags.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='+')
    ap.add_argument('--csv'); ap.add_argument('--json'); ap.add_argument('--md')
    ap.add_argument('--min-words', type=int, default=800, help='skip documents shorter than this')
    a = ap.parse_args()

    results, seen_hash = [], set()
    for root in a.roots:
        root = os.path.abspath(root)
        texs = []
        for d, dirs, fs in os.walk(root):
            dirs[:] = [x for x in dirs if not x.startswith('.')]
            texs += [os.path.join(d, f) for f in fs if f.endswith('.tex')]
        for p in sorted(texs):
            t = read(p)
            if '\\documentclass' not in t:
                continue
            h = hashlib.sha1(re.sub(r'\s+', '', t).encode()).hexdigest()
            if h in seen_hash:
                continue
            seen_hash.add(h)
            try:
                r = analyze(p, root)
            except Exception as e:  # keep going on odd files
                print(f'skip {p}: {e}', file=sys.stderr)
                continue
            if r['words'] >= a.min_words:
                parts = root.split(os.sep)
                owner = parts[-2] if len(parts) > 2 and parts[-3] == 'sources' else 'standardgalactic'
                r['repo'] = os.path.basename(root) if owner == 'standardgalactic' else f'{owner}/{os.path.basename(root)}'
                results.append(r)

    results.sort(key=lambda r: -r['score'])
    fields = ['repo', 'path', 'title', 'words', 'cites', 'cites_per_1k', 'bib_entries', 'score']
    counts = ['uncited_claims', 'uncited_works', 'stub_sections', 'unproved', 'markers']
    if a.csv:
        with open(a.csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(fields + counts + ['missing_keys', 'unused_bib'])
            for r in results:
                w.writerow([r[k] for k in fields] + [len(r['flags'].get(c, [])) for c in counts]
                           + [len(r['missing_keys']), len(r['unused_bib'])])
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=1)
    if a.md:
        with open(a.md, 'w', encoding='utf-8') as f:
            # raw block stops GitHub Pages (Jekyll/Liquid) from parsing {{ }} or {% %} in LaTeX snippets
            f.write('{% raw %}\n')
            for r in results:
                f.write(f"## {r['title']}\n`{r['repo']}/{r['path']}` · {r['words']} words · "
                        f"{r['cites']} cites ({r['cites_per_1k']}/1k) · {r['bib_entries']} bib entries\n\n")
                for c in counts:
                    for fp, ln, s in r['flags'].get(c, []):
                        f.write(f"- [ ] **{c}** `{fp}:{ln}` {s}\n")
                if r['missing_keys']:
                    f.write(f"- [ ] **missing bib keys**: {', '.join(r['missing_keys'])}\n")
                f.write('\n')
            f.write('{% endraw %}\n')
    print(f'{len(results)} documents analyzed', file=sys.stderr)
    for r in results[:15]:
        print(f"{r['score']:7.2f}  {r['words']:6d}w  {r['cites']:4d}c  {r['repo']}/{r['path']}")


if __name__ == '__main__':
    main()
