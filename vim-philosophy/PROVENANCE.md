# Provenance

This folder is a copy of [peterlodri-sec/vim-philosophy](https://github.com/peterlodri-sec/vim-philosophy) at commit `2721d89` (2026-08-04), brought into this repository so the writing is also kept under the author's own account.

## Authorship

- **Flyxion (standardgalactic)** wrote the contents, added in commit `2721d89`: the book *Thinking in Vim: A Structural Reference to Modal Editing* (`essays/thinking-in-vim/`), the essay *Modal Editing: Compositional Constraint in Text Interaction*, *Building Forth from Spherepop Primitives*, *Beyond Optimal Foraging*, and the `zebra`, `zebra-prototype`, `writing-workbench` and `ollama-benchmark` projects.
- **Péter Lodri** set up the original repository in commits `2570734` and `062f005`: `README.md`, `Makefile`, `.gitignore`, `_config.yml`, `index.md` and the placeholder files. His README still describes those placeholders.

## Changes in this copy

- `essays/modal-editing.tex`: an unescaped `$` inside `\texttt{}` (line 72) is now `\$`. Before this fix the essay stopped compiling at page 4.
- Compiled PDFs were added next to their sources: `essays/thinking-in-vim/main.pdf` (137 pages), `essays/modal-editing.pdf` (39 pages), `building-forth.pdf` and `beyond-optimal-foraging.pdf` (13 pages each). The book and the essays use `fontspec`, so they need XeLaTeX or LuaLaTeX. The PDFs here were built with XeLaTeX.
