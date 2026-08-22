# Distinction and Continuation — repository

LaTeX source for *Distinction and Continuation: Admissibility, Repair,
and the Limits of Local Coherence* — a five-part, 22-chapter monograph. See
`dependency-ledger.md` (in this repo, or the canonical copy tracked
separately) for the full chapter-by-chapter dependency graph, source
mapping, and drafting-phase order.

## Structure

```
main.tex              Full-manuscript assembly (all 5 parts, all 22 chapters)
preamble.tex           Shared preamble: fonts, box environments, theorem styles
build.sh               Compile script (xelatex, two-pass)
front/
  abstract.tex          Front-matter abstract (stub)
parts/
  part1.tex .. part5.tex   Standalone compilable single-part documents,
                            for fast iteration while drafting one part
chapters/
  ch01-*.tex .. ch22-*.tex Chapter source files, one per chapter.
                            Each currently a stub with a provenance box
                            (source file(s), drafting status, dependencies)
                            per dependency-ledger.md.
back/
  bibliography.tex       thebibliography (not BibTeX), shared across
                          the full manuscript and all per-part builds
```

## Conventions carried over from prior book-scale projects

- Engine: XeLaTeX (fallback for LuaLaTeX font-cache issues seen in
  some environments); font: TeX Gyre Pagella via fontspec.
- Bibliography: `thebibliography`, not BibTeX, for standalone
  portability. No self-citations.
- Body prose: continuous academic paragraphs, no bulleted/itemized
  lists (itemize/enumerate reserved for proofs and formal definitions
  only).
- Two-pass compilation for cross-references and the table of contents.
- Title page date: month + year, not an exact date (avoids AI tools
  over-reacting to a precise recent date as "brand new/breaking").
- Author byline: Flyxion / Independent Researcher.

## Drafting order

Per the dependency ledger's 5-phase topological sort:

1. **Epistemic Anchors** — Ch. 1, 2, 3, 4 (all fully sourced, no
   open dependencies — start here)
2. **Geometric & Connective Core** — Ch. 5, 6, 9
3. **Event Calculus & Tiling** — Ch. 7, 8
4. **Systems, Verification & Representation** — Ch. 10–15, 17, 18
5. **Political Economy Synthesis** — Ch. 16, 19–22

Chapters marked "Fully Drafted" in their provenance box are
re-derivation/integration work (pulling an existing essay into the
monograph's shared notation and cross-referencing apparatus).
Chapters marked "Hybrid" combine two or more sources. Ch. 5 is the
only "Fresh" chapter with no direct source essay.

## Provenance boxes

Every chapter stub opens with a `provenance` box recording its
source file(s), drafting status, and direct dependencies, taken
from `dependency-ledger.md` (v3). These are a drafting aid — remove
or move to an appendix once a chapter's claims have been checked
against its source and the chapter is considered final.
