# Laboratory paper inventory

This file is generated from `inventory/papers.json`. Run `python3 scripts/build-paper-inventory.py` to refresh both files.

## Scope

The first slice scans only repository-root manuscripts and direct children of `source/`. The following directories remain deliberately deferred: `continuation-geometry/`, `processing/`, `projects/`, `working/`.

## Status summary

- `duplicate-review`: 4
- `published`: 10
- `recovery-blocked`: 7

## Build matrix

| Paper | Source | Output | Engine | Pages | Status | Blockers |
|---|---|---|---|---:|---|---|
| Address Before Operator: From the Typewriter Carriage to Vim's Grammar | `address-before-operator.tex` | `address-before-operator.pdf` | lualatex | 7 | published | — |
| The Attention Compiler and the Thin-Walled Archive: Content Routing, Bubbles, and the Triage of Novel Ideas | `source/attention-compiler-extended.tex`<br>`source/attention-compiler.tex` | `source/attention-compiler-extended.pdf`<br>`source/attention-compiler.pdf` | — | — | duplicate-review | duplicate-family-requires-canonical-review |
| Borrowed Intuition: Compression Without Experience | `borrowed-intuition.tex` | `Borrowed_Intuition.pdf`<br>`borrowed-intuition.pdf` | lualatex | — | duplicate-review | duplicate-family-requires-canonical-review |
| Consensus Without Independence: Sycophancy, Context Reification, and Positive Feedback in Persona Ensembles | `consensus-without-independence.tex`<br>`source/consensus-without-independence.tex` | `consensus-without-independence.pdf` | — | 10 | duplicate-review | duplicate-family-requires-canonical-review |
| The Crinkle-Cut Supercube: Constraint-Directed Infolding, Hidden Surface Area: and the Geometry of Emergent Boundaries | `source/crinkle-cut-supercube.tex` | `source/crinkle-cut-supercube.pdf` | pdflatex | 84 | published | — |
| Deployment-Native Ternary Learning: Reproducible Training, Executable Model Streams: and Continuously Curated Synthetic Corpora | `deployment_native_ternary_learning.tex` | `deployment_native_ternary_learning.pdf` | lualatex | 13 | published | — |
| Depth Before Derivation | — | `depth_before_derivation.pdf` | — | 9 | recovery-blocked | editable-source-missing |
| Distinction And Continuation | — | `distinction-and-continuation.pdf` | — | 177 | recovery-blocked | editable-source-missing |
| Emotional Differentiation: Categorization, Prediction, and the Formation of Conscious Feeling | `source/emotional-differentiation.tex` | `source/emotional-differentiation.pdf` | pdflatex | 23 | published | — |
| Interaction Residue | — | `Interaction_Residue.pdf` | — | 15 | recovery-blocked | editable-source-missing |
| The Latency of Evidence: Why Facts Can Exist Before a System Becomes Capable of Knowing Them | `latency-of-evidence.tex`<br>`source/latency-of-evidence.tex` | `latency-of-evidence.pdf` | — | 11 | duplicate-review | duplicate-family-requires-canonical-review |
| The Monotonic Learning Series: Programmed Texts in Distinction, Repair, and Continuation: Full Series Plan --- Detailed Edition | `source/monotonic-learning-plan.tex` | `source/monotonic-learning-plan.pdf` | lualatex | 10 | published | — |
| The Operational Residue: The Noncommutativity of Preservation and Action | `source/operator-residue.tex` | `source/operator-residue.pdf` | lualatex | 32 | published | — |
| A Relativistic Theory of Longevity | `source/relativistic-longevity.tex` | `source/relativistic-longevity.pdf` | pdflatex | 21 | published | — |
| Relativistic Persistence | — | `source/Relativistic_Persistence.pdf` | — | 15 | recovery-blocked | editable-source-missing |
| Representational Simplicity: Sufficient Projection, Obstruction-Sensitive Routing, and Repair Under Finite Attention | `source/representational-simplicity.tex` | `source/representational-simplicity.pdf` | lualatex | 264 | published | — |
| Sufficiency Under Compression: Exact Decoding, Admissible Projection, and Operational Coupling in Clio and Hydra | `source/sufficiency-under-compression.tex` | `source/sufficiency-under-compression.pdf` | lualatex | 15 | published | — |
| The Architecture Of Feeling | — | `source/The_Architecture_of_Feeling.pdf` | — | 15 | recovery-blocked | editable-source-missing |
| The Attention Compiler | — | `source/The_Attention_Compiler-draft.pdf`<br>`source/The_Attention_Compiler-notes.pdf`<br>`source/The_Attention_Compiler.pdf` | — | — | recovery-blocked | editable-source-missing, duplicate-family-requires-canonical-review |
| Verifiable Ml Deployment Architecture | — | `Verifiable_ML_Deployment_Architecture.pdf` | — | 15 | recovery-blocked | editable-source-missing |
| Why No One Talks Backwards:: Developmental Exploration, Reachability, and the Absence of: Temporal Reversal as a Grammatical Operation | `source/why-no-one-talks-backwards.tex` | `source/why-no-one-talks-backwards.pdf` | pdflatex | 13 | published | — |

## Provenance rules

Engine values are inferred from the LaTeX preamble in this first slice. Page counts are measured with `pdfinfo`. A family with multiple source or output candidates remains unresolved; the generator records every candidate and does not select a canonical file.
