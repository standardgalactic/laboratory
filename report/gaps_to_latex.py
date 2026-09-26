#!/usr/bin/env python3
"""gaps_to_latex.py - turn essay_gaps.py JSON output into a LaTeX report.

Usage: python3 gaps_to_latex.py gaps.json report.tex [--detail N | --full]
"""
import json, re, sys, statistics
from collections import Counter, defaultdict

src, dst = sys.argv[1], sys.argv[2]
DETAIL = int(sys.argv[sys.argv.index('--detail') + 1]) if '--detail' in sys.argv else 40
R = json.load(open(src, encoding='utf-8'))
R.sort(key=lambda r: -r['score'])
for r in R:
    r['title'] = r['title'].strip() or r['path'].rsplit('/', 1)[-1]

KINDS = [('uncited_claims', 'Uncited claims'), ('uncited_works', 'Named works without a citation'),
         ('markers', 'Unfinished markers'), ('unproved', 'Statements without a proof'),
         ('stub_sections', 'Short sections')]
PER_KIND = {'uncited_claims': 25, 'uncited_works': 20, 'markers': 15, 'unproved': 15, 'stub_sections': 12}
FULL = '--full' in sys.argv
if FULL:  # every document, every flag, no truncation
    DETAIL = 10 ** 9
    PER_KIND = {k: 10 ** 9 for k in PER_KIND}

SPECIAL = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '$': r'\$', '&': r'\&', '#': r'\#',
           '%': r'\%', '_': r'\_', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}',
           '<': r'\textless{}', '>': r'\textgreater{}', '|': r'\textbar{}'}


def esc(s):
    s = ''.join(SPECIAL.get(c, c) for c in str(s))
    uni = {'\u2014': '---', '\u2013': '--', '\u2026': r'\ldots{}', '\u2018': '`', '\u2019': "'",
           '\u201c': '``', '\u201d': "''", '\u2192': r'$\to$', '\u2212': '-', '\u00a0': '~'}
    return ''.join(uni.get(c, c if ord(c) < 0x100 else '?') for c in s)


def plain(s):
    """Make a flagged LaTeX sentence readable: drop math and command names, keep words."""
    s = re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)|\$[^$]*\$', ' [math] ', s)
    s = re.sub(r'\\(?:emph|textit|textbf|text|mathrm|textsc)\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\(?:begin|end|label|ref|eqref)\{[^}]*\}', ' ', s)
    s = re.sub(r'\\[a-zA-Z]+\*?', ' ', s)
    s = re.sub(r'[{}]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def path(s):
    return r'\texttt{' + esc(s).replace('/', r'/\allowbreak{}').replace(r'\_', r'\_\allowbreak{}') + '}'


tot = Counter()
for r in R:
    for k, v in r['flags'].items():
        tot[k] += len(v)
words = sum(r['words'] for r in R)
med = statistics.median(r['cites_per_1k'] for r in R)
nocite = [r for r in R if r['cites'] == 0 and r['words'] > 1500]
missing_docs = [r for r in R if r['missing_keys']]
by_repo = defaultdict(list)
for r in R:
    by_repo[r['repo']].append(r)

out = []
w = out.append
w(r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{charter}
\usepackage[scaled=0.92]{helvet}
\usepackage{courier}
\usepackage[margin=1in]{geometry}
\usepackage{microtype,booktabs,longtable,array,xcolor,enumitem}
\usepackage[hidelinks]{hyperref}
\definecolor{muted}{HTML}{5F6B66}
\setlist{nosep,leftmargin=1.2em}
\setlength{\parskip}{0.4em}\setlength{\parindent}{0pt}
\newcommand{\loc}[1]{{\small\color{muted}\texttt{#1}}}
\title{Open Threads Ledger\\[0.3em]\large Where the Essays Need References, Proofs, and Detail}
\author{Flyxion\\Independent Researcher}
\date{September 26, 2026}
\begin{document}
\maketitle
""")

w(r"\begin{abstract}" + "\n" + esc(
    f"A static scan of {len(R)} LaTeX documents ({words:,} words) drawn from {len(by_repo)} public "
    f"repositories identifies places where the writing asserts empirical results without citation, "
    f"names prior work without citing it, states formal results without proof, or leaves sections "
    f"skeletal. The median document carries {med:.2f} citations per thousand words, and {len(nocite)} "
    f"documents longer than 1,500 words cite nothing. The report ranks documents by gap density and "
    f"lists each flagged location by file and line, so the work can be divided among contributors "
    f"or handed to automated passes one bounded task at a time.") + "\n" + r"\end{abstract}" + "\n")

w(r"\section{Purpose}" + "\n")
w(esc("Most of these documents are active projects that were published as they were written. What they "
      "lack is mostly not argument but apparatus: references for claims that rest on outside work, proofs "
      "for stated results, and development of sections that were outlined and left short. That kind of "
      "work divides well. A contributor who knows a literature can supply citations for one essay without "
      "understanding the whole corpus, and an automated pass does far better with a list of specific gaps "
      "than with an instruction to improve a document in general. This report is that list.") + "\n")

w(r"\section{Method}" + "\n")
w(esc("A document is any .tex file containing a document class declaration. Files it pulls in with input "
      "or include commands are expanded in place, so chapter-based monographs are scanned as one document. "
      "Byte-identical copies are counted once; different drafts of the same essay are counted separately. "
      "Documents under 800 words are skipped. Six kinds of gap are flagged:") + "\n")
w(r"\begin{description}[leftmargin=1em,style=nextline]")
defs = [
    ("Uncited claims", "Sentences with empirical wording (studies show, has been shown, recent work, evidence suggests, a percentage of a population) and no citation command in the same sentence."),
    ("Named works", "Mentions of the form Author et al., Author (1999), or an arXiv number with no citation command."),
    ("Unfinished markers", "TODO, TBD, FIXME, placeholder, to be written, citation needed, and similar."),
    ("Unproved statements", "Theorem, lemma, proposition, corollary or claim environments with no proof following them. Conjectures are excluded."),
    ("Short sections", "Sections or subsections with fewer than 60 words of prose once mathematics is removed, excluding headings that only introduce subsections."),
    ("Bibliography mismatches", "Citation keys with no bibliography entry, and bibliography entries never cited. When the bibliography file cannot be matched to the citations, key checks are skipped."),
]
for a, b in defs:
    w(r"\item[" + esc(a) + "] " + esc(b))
w(r"\end{description}")
w(esc("The gap score is the weighted number of flags per thousand words (uncited claims 3, markers 2, "
      "named works 1.5, unproved statements and short sections 1), plus 4 for a document over 1,500 words "
      "with no citations, 2 for fewer than one citation per thousand words, and up to 10 for missing "
      "bibliography keys. The score ranks where to look first. It does not measure quality, and the "
      "pattern matching produces some false positives, especially for short sections in heavily "
      "subdivided monographs.") + "\n")

w(r"\section{Summary}" + "\n")
w(r"\begin{center}\begin{tabular}{lr}\toprule")
for label, val in [("Documents scanned", f"{len(R):,}"), ("Words", f"{words:,}"),
                   ("Median citations per 1,000 words", f"{med:.2f}"),
                   ("Documents over 1,500 words with no citations", f"{len(nocite):,}"),
                   ("Uncited claims", f"{tot['uncited_claims']:,}"),
                   ("Named works without a citation", f"{tot['uncited_works']:,}"),
                   ("Statements without a proof", f"{tot['unproved']:,}"),
                   ("Unfinished markers", f"{tot['markers']:,}"),
                   ("Short sections", f"{tot['stub_sections']:,}"),
                   ("Documents with missing bibliography keys", f"{len(missing_docs):,}")]:
    w(esc(label) + " & " + esc(val) + r" \\")
w(r"\bottomrule\end{tabular}\end{center}")

w(r"\subsection*{By repository}")
w(r"\begin{center}\begin{tabular}{lrrrrr}\toprule")
w(r"Repository & Docs & Words & Cites/1k & Uncited & Unproved \\\midrule")
for repo in sorted(by_repo, key=lambda k: -len(by_repo[k])):
    rs = by_repo[repo]
    wds = sum(r['words'] for r in rs)
    cps = 1000 * sum(r['cites'] for r in rs) / wds if wds else 0
    w(f"{esc(repo)} & {len(rs)} & {wds:,} & {cps:.2f} & "
      f"{sum(len(r['flags'].get('uncited_claims', [])) for r in rs)} & "
      f"{sum(len(r['flags'].get('unproved', [])) for r in rs)} \\\\")
w(r"\bottomrule\end{tabular}\end{center}")

w(r"\subsection*{Where to start}")
w(esc("Three kinds of task are well suited to outside help. Uncited claims and named works are the most "
      "bounded: each is one sentence that needs one source, and a contributor can check the claim while "
      "finding it. Missing bibliography keys are mechanical repairs. Unproved statements need someone "
      "with the relevant mathematics and are best offered one document at a time. Short sections are the "
      "least suited to outside work, since expanding them depends on the author's intent.") + "\n")

w(r"\section{Documents in detail}" + "\n")
w(esc((f"All {len(R)} documents follow in order of gap score, with every flagged location. " if FULL else
      f"The {min(DETAIL, len(R))} highest-scoring documents follow, each with its flagged locations. Long "
      "lists are truncated; the full list for every document is in the markdown output of the scanner. ") +
      "Flagged sentences are shown as plain text with mathematics replaced by [math].") + "\n")
for i, r in enumerate(R[:DETAIL], 1):
    w(r"\subsection{" + esc(r['title']) + "}")
    w(r"\loc{" + esc(r['repo'] + '/' + r['path']).replace('/', r'/\allowbreak{}') + "}\\par")
    bits = [f"score {r['score']:.1f}", f"{r['words']:,} words", f"{r['cites']} citations ({r['cites_per_1k']}/1k)",
            f"{r['bib_entries']} bibliography entries"]
    if r['unused_bib']:
        bits.append(f"{len(r['unused_bib'])} never cited")
    w(esc(', '.join(bits) + '.') + "\n")
    if r['cites'] == 0 and r['words'] > 1500:
        w(r"\textbf{No citations.} " + esc("The document cites nothing; a reference pass is the first task.") + "\n")
    elif r.get('bib_note'):
        w(esc("The bibliography file could not be matched to the citations, so key checks were skipped.") + "\n")
    for k, label in KINDS:
        items = r['flags'].get(k, [])
        if not items:
            continue
        w(r"\paragraph{" + esc(label) + f" ({len(items)})" + "}")
        w(r"\begin{itemize}")
        for f, ln, s in items[:PER_KIND[k]]:
            text = plain(s) if k in ('uncited_claims', 'uncited_works', 'markers') else s
            w(r"\item \loc{" + esc(f"{f}:{ln}").replace('/', r'/\allowbreak{}') + "} " + esc(text))
        if len(items) > PER_KIND[k]:
            w(r"\item[] {\color{muted}\small " + esc(f"and {len(items) - PER_KIND[k]} more") + "}")
        w(r"\end{itemize}")
    if r['missing_keys']:
        keys = r['missing_keys']
        w(r"\paragraph{Cited keys missing from the bibliography (" + str(len(keys)) + ")}")
        w(r"{\small\ttfamily\raggedright " + esc(', '.join(keys[:40]) + (' ...' if len(keys) > 40 else '')) + r"\par}")

w(r"\appendix")
w(r"\section{All documents by gap score}")
w(r"{\small\setlength{\tabcolsep}{4pt}")
w(r"\begin{longtable}{@{}r>{\raggedright\arraybackslash}p{0.52\textwidth}rrrr@{}}")
head = r"Score & Document & Words & Cites & Uncited & Unproved \\\midrule"
w(r"\toprule " + head + r"\endfirsthead")
w(r"\toprule " + head + r"\endhead")
w(r"\bottomrule\endfoot")
for r in R:
    w(f"{r['score']:.1f} & " + esc(r['title']) + r"\newline\loc{" + esc(r['repo'] + '/' + r['path']).replace('/', r'/\allowbreak{}')
      + f"}} & {r['words']:,} & {r['cites']} & {len(r['flags'].get('uncited_claims', []))} & {len(r['flags'].get('unproved', []))} \\\\")
w(r"\end{longtable}}")
w(r"\end{document}")
open(dst, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('wrote', dst)
