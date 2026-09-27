# vim-philosophy

Philosophical writing on modal editing, thinking-in-tool, and the
cognitive structure of text interaction. Companion to the writing
produced in the Flyxion session (2026-08-04).

## Layout

```
essays/                  finished essays (Markdown + compiled PDF)
  modal-editing.md       "Modal Editing: Compositional Constraint in Text Interaction"
  thinking-in-vim.md     "Thinking in Vim" (draft)
papers/
  beyond-optimal-foraging/   LaTeX paper (optimal foraging theory applied
                             to cognition / attention)
    beyond-optimal-foraging.tex
    references.bib
source-material/         original source .md files from prior conversations
notes/                   outlines, scratch, revisions
```

## Documents

| Doc | Status | File |
|-----|--------|------|
| Modal Editing essay | placeholder — paste content | `essays/modal-editing.md` |
| Thinking in Vim | placeholder — paste content | `essays/thinking-in-vim.md` |
| Beyond Optimal Foraging (LaTeX) | placeholder — paste content | `papers/beyond-optimal-foraging/beyond-optimal-foraging.tex` |
| Philosophical source material | placeholder — paste content | `source-material/philosophical-source-material.md` |
| Modal editing essay source | placeholder — paste content | `source-material/modal-editing-essay-source.md` |

## Build

`make pdf` compiles the LaTeX paper (requires TeX Live + fontspec/TeX Gyre Pagella).
