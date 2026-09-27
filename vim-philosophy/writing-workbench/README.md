# Writing Workbench v1

Writing Workbench is a local, Markdown-first essay development environment for Ollama.

Its default model roles are:

- `granite4.1:3b` for generation, expansion, brainstorming, classification, and drafting.
- `granite4.1:8b` for structural review, contradiction detection, consistency checks, and final verification.

The program preserves each stage as a separate Markdown artifact. It does not silently overwrite prior drafts.

## Requirements

- Bash 4 or newer
- Ollama
- `granite4.1:3b`
- `granite4.1:8b`
- Optional: `fzf`, `bat`, `glow`, `pandoc`, and `git`

## Start

```bash
chmod +x bin/workbench
./bin/workbench
```

You may also run commands directly:

```bash
./bin/workbench new
./bin/workbench open PROJECT_NAME
./bin/workbench run PROJECT_NAME classify
./bin/workbench run PROJECT_NAME outline
./bin/workbench run PROJECT_NAME review-outline
./bin/workbench status PROJECT_NAME
```

## Project lifecycle

A normal project moves through these files:

```text
00-project.md
01-classification.md
02-topic-analysis.md
03-outline.md
04-outline-review.md
05-research-notes.md
06-draft-1.md
07-draft-review.md
08-draft-2.md
09-consistency-check.md
10-final.md
```

Additional artifacts are saved in `history/`, `sections/`, and `reviews/`.

## Design principles

The workbench treats writing as a trajectory rather than a single mutable document. Every important transformation leaves an inspectable artifact. The smaller model proposes and expands; the larger model diagnoses, checks, and constrains. Human judgment remains the authority for accepting revisions.
