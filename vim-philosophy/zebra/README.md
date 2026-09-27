# Zebra

Zebra is a small, real, working implementation of the "operating system for
ideas" design: a CLI that treats a writing/research project as an
**event-sourced graph** of tasks and artifacts, not a folder of Markdown
files you edit in place.

This is not the bootstrap Python scaffold from earlier — every command
below is real Rust, compiled, tested, and exercised end to end.

## The model, in one paragraph

A **task** is a declarative build rule (`tasks/*.yaml`): named inputs,
named outputs, a prompt, a backend role. Running a task assembles its
context from `project.md` and the current outputs of whatever it depends
on, sends that to a model backend, and writes the result as a new
**immutable artifact** (`artifacts/A0000042.md`). `current/<output>.md` is
never itself content — it's a symlink into the artifact store, exactly
like a Git ref. Nothing is ever edited in place. Every run appends one
record to the **journal** (`journal/0000042.yaml`); project state is never
stored directly, only reconstructed by folding over journal events.

That's the entire engine. Everything else — dependency resolution,
provenance, graph queries — falls out of those four ideas (task, artifact,
current pointer, journal event).

## Quick start

```sh
cargo build --release
export PATH="$PWD/target/release:$PATH"

zebra new my-essay
cd my-essay
# edit project.md, tweak tasks/*.yaml and prompts/*.md as needed
# use runner = "mock" in zebra.toml if you don't have ollama installed,
# or runner = "ollama" with a real model pulled

zebra status              # what's done, what's pending
zebra run publish         # resolves and runs every dependency in order
zebra journal             # full provenance log
zebra query task=review   # filter the journal
zebra why draft           # upstream: what draft depends on
zebra trace classify      # downstream: what depends on classify
zebra inspect revise      # exactly what revise will load, and its hashes
zebra verify              # integrity check of current/ pointers
zebra metadata            # machine-readable JSON, cargo-metadata style
```

## Commands implemented

| Command | Does |
|---|---|
| `zebra new NAME` | Scaffold a project with the default 8-stage pipeline (classify → analyze → outline → draft → review → revise → proof → publish) |
| `zebra status` | Show each workflow step and whether its output(s) exist |
| `zebra run TASK [--force]` | Topologically resolve and run all unmet dependencies, then the task itself; skips tasks whose outputs already exist unless `--force` |
| `zebra metadata` | JSON summary: project, models, task/artifact counts |
| `zebra trace NAME` | BFS downstream — what (transitively) consumes this task's output |
| `zebra why NAME` | BFS upstream — what this task (transitively) depends on |
| `zebra inspect TASK` | Direct inputs, their current artifact ids, prompt/context hashes |
| `zebra journal [--task X]` | List journal events, optionally filtered by task |
| `zebra query k=v k=v` | Filter journal events by task/model/run/event |
| `zebra verify` | Confirm every `current/*.md` pointer resolves to a real artifact |

## What's real vs. what's future work

**Implemented and tested:** the node/edge task graph, dependency
resolution with cycle detection, the append-only journal, immutable
content-addressed artifacts, symlink-based current pointers, prompt/context
hashing for provenance, an `ollama`-or-`mock` backend (mock lets the whole
pipeline run without a model installed, which is how the test run below
was done), and `trace`/`why`/`inspect`/`verify`/`query`.

**Sketched in the design but not built here** (each is a natural next
slice, not a redesign): compiled prompt/theory bundles with caching,
`zebra diff` (what's invalidated when a source file changes), `zebra
replay`/`zebra freeze` for full reproducibility snapshots, branches/merge
for divergent drafts, and a package registry for theory modules. The
current architecture — everything is a Node, everything is an Edge, state
is folded from the journal — is exactly the substrate those would be built
on; none of them require changing what's here.

## Example run (mock backend)

```
$ zebra run publish
[zebra] classify: running (granite4.1:3b) inputs=[project]
[zebra] classify: wrote A0000001 in 0.00s  (mock)
[zebra] analyze: running (granite4.1:3b) inputs=[project, classification]
[zebra] analyze: wrote A0000002 in 0.00s  (mock)
[zebra] outline: running (granite4.1:3b) inputs=[project, classification, analysis]
[zebra] outline: wrote A0000003 in 0.00s  (mock)
[zebra] draft: running (granite4.1:3b) inputs=[project, outline, analysis]
[zebra] draft: wrote A0000004 in 0.00s  (mock)
[zebra] review: running (granite4.1:8b) inputs=[project, draft]
[zebra] review: wrote A0000005 in 0.00s  (mock)
[zebra] revise: running (granite4.1:3b) inputs=[draft, review]
[zebra] revise: wrote A0000006 in 0.00s  (mock)
[zebra] proof: running (granite4.1:8b) inputs=[revision]
[zebra] proof: wrote A0000007 in 0.00s  (mock)
[zebra] publish: running (granite4.1:3b) inputs=[proof, revision]
[zebra] publish: wrote A0000008 in 0.00s  (mock)

$ zebra why draft
draft
  └─ outline
  └─ analyze
    └─ classify

$ zebra inspect revise
revise
  prompt: prompts/revise.md
  backend role: generator
  outputs: revision
  inputs:
    - draft  (current -> A0000004)
    - review  (current -> A0000005)

  prompt_hash:  379aa60a3196e28433fb8786a72707c2c6976614a6be0c9b4b7fa6be729a36f9
  context_hash: c3f4d36034af2a1d4004e563007ab796e0e8c07b1a7db485dce46f234c2b6ca5
```

## Layout of a project directory

```
my-essay/
  zebra.toml          # project name, workflow, backend/model config
  project.md           # goal / audience / constraints — loaded as "project" input
  tasks/*.yaml          # declarative build rules
  prompts/*.md           # one prompt file per task
  theory/                # optional reference material for prompts to cite
  workflows/default.yml  # ordered step list, used by `zebra status`
  artifacts/A#######.md  # immutable — never edited after being written
  current/<output>.md    # symlinks into artifacts/, the only "mutable" state
  journal/#######.yaml   # append-only event log; state is folded from this
```

## Tests

```sh
cargo test
```

Covers topological build ordering, dependency-cycle detection, and
downstream-consumer lookup in the task graph (`src/model.rs`).
