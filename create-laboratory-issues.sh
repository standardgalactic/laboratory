#!/usr/bin/env bash
set -euo pipefail

repo="standardgalactic/laboratory"
apply=false

usage() {
    printf 'Usage: %s [--apply] [--repo OWNER/REPO]\n' "${0##*/}"
    printf 'Preview is the default. Use --apply to create the issues.\n'
}

while (($#)); do
    case "$1" in
        --apply) apply=true; shift ;;
        --repo)
            [[ $# -ge 2 ]] || { printf 'Missing value after --repo\n' >&2; exit 2; }
            repo="$2"
            shift 2
            ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

existing_titles=""
if $apply; then
    command -v gh >/dev/null 2>&1 || {
        printf 'GitHub CLI (gh) is required.\n' >&2
        exit 1
    }
    gh auth status >/dev/null
    existing_titles="$(
        gh issue list --repo "$repo" --state all --limit 1000 \
            --json title --jq '.[].title'
    )"
fi

create_issue() {
    local title="$1"
    local body
    body="$(cat)"

    if ! $apply; then
        printf '\n[%s]\n%s\n' "$title" "$body"
        return
    fi

    if grep -Fqx -- "$title" <<<"$existing_titles"; then
        printf 'Skipping existing issue: %s\n' "$title"
        return
    fi

    gh issue create --repo "$repo" --title "$title" --body "$body"
    existing_titles+="${existing_titles:+$'\n'}$title"
}

create_issue "Create a canonical inventory and build matrix for every laboratory paper" <<'EOF'
## Objective

Create a version-controlled inventory that connects every published paper to its editable source, build command, output PDF, subject area, and revision status.

## Work

- [ ] Discover papers from the repository rather than maintaining a hand-copied partial list.
- [ ] Record title, source path, output path, build engine, page count, word count, and last substantive revision.
- [ ] Mark PDF-only papers whose editable sources must be recovered.
- [ ] Track derivations, proofs, references, appendices, figures, and final review independently.
- [ ] Detect duplicate drafts and identify the canonical manuscript without deleting provenance.
- [ ] Link papers to associated code, datasets, visual experiments, and deployed pages.
- [ ] Add per-directory and repository-wide completion summaries.
- [ ] Make the inventory reproducible with a documented script.

## Completion criterion

Every published paper has one canonical row pointing to a source and reproducible build, or an explicit recovery blocker.
EOF

create_issue "Expand derivations, proofs, countermodels, and limiting cases" <<'EOF'
## Objective

Strengthen the formal papers by exposing the reasoning between definitions and conclusions. The revision should distinguish proved results from models, analogies, conjectures, and interpretive extensions.

## Work

- [ ] Audit every equation and formal claim across the paper collection.
- [ ] State assumptions, domains, boundary conditions, conventions, and approximation regimes.
- [ ] Supply omitted intermediate derivations and dimensional checks.
- [ ] Recast central results as propositions, lemmas, bounds, criteria, or clearly qualified conjectures.
- [ ] Test zero, limiting, degenerate, noisy, and adversarial cases where relevant.
- [ ] Add counterexamples for claims that fail outside their intended domain.
- [ ] Separate mathematical equivalence from analogy or structural correspondence.
- [ ] Add worked examples that instantiate new operators and quantities.
- [ ] Cross-check reused definitions across papers for semantic drift.

## Completion criterion

A technically competent reader can reproduce each central inference without supplying missing algebra or guessing whether a passage is formal or metaphorical.
EOF

create_issue "Complete references, citations, and claim-provenance audits" <<'EOF'
## Objective

Bring every laboratory paper to a consistent scholarly citation standard and make the evidential role of each source visible.

## Work

- [ ] Cite technical, quantitative, historical, psychological, biological, and contested claims at their point of use.
- [ ] Prefer primary literature for direct empirical and theoretical claims.
- [ ] Add independent and constraining sources rather than citing only congenial formulations.
- [ ] Label sources by role: direct evidence, theoretical background, constraint, illustration, or synthesis.
- [ ] Verify authors, titles, dates, page ranges, identifiers, URLs, and quotation locators.
- [ ] Remove or qualify claims for which the cited source does not provide adequate support.
- [ ] Standardize bibliography style and citation keys across manuscripts.
- [ ] Detect missing bibliography entries and orphaned references automatically.
- [ ] Archive fragile web references where appropriate.

## Completion criterion

Every consequential external claim is traceable to an appropriately scoped source, and citations with different evidential roles no longer appear interchangeable.
EOF

create_issue "Standardize technical appendices and reproducibility packages" <<'EOF'
## Objective

Give each paper a consistent appendix layer for notation, extended derivations, methods, parameter tables, limitations, and reproducibility material.

## Work

- [ ] Add notation and glossary appendices where papers introduce new operators or terminology.
- [ ] Move lengthy derivations and proof variants into linked technical appendices when they interrupt the main argument.
- [ ] Add methods, dataset, prompt, model, software, and hardware details to computational work.
- [ ] Record random seeds, versions, configuration files, and parameter ranges for generative experiments.
- [ ] Include ablations, negative controls, failure cases, and uncertainty estimates.
- [ ] Link every figure and table to its generating source or document a manual provenance path.
- [ ] Add limitations and non-claims sections to prevent later analogical overextension.
- [ ] Verify that a clean checkout can rebuild the deliverables with documented commands.

## Completion criterion

Each paper has the appendices appropriate to its evidential type, and all computational or visual results carry enough provenance to be regenerated or critically evaluated.
EOF

create_issue "Integrate the headless Blender experiments into the laboratory site" <<'EOF'
## Objective

Turn the PNG collection under experiments/output into a navigable, reproducible experiment gallery connected to its Blender generators and research context.

## Work

- [ ] Generate gallery entries from the output directory so new renders appear without hand-editing the page.
- [ ] Link every image to its generator script, render settings, and explanatory caption.
- [ ] Identify orphaned outputs and scripts during the build.
- [ ] Preserve full-resolution access while serving efficient thumbnails.
- [ ] Make labels and captions readable on phones and desktop displays.
- [ ] Add direct links to related papers or project repositories.
- [ ] Keep the repository-root redirect aligned with the experiments gallery deployment path.
- [ ] Add a headless batch-render and gallery-validation command suitable for CI.
- [ ] Document the Blender version and dependencies required for reproduction.

## Completion criterion

The deployed gallery exposes every intended render, its provenance, and its research purpose, while a clean checkout can rebuild and validate both images and index.
EOF

create_issue "Add continuous build and publication verification" <<'EOF'
## Objective

Detect broken papers, missing assets, stale indexes, and failed site deployments before they reach the public laboratory collection.

## Work

- [ ] Compile changed LaTeX manuscripts in CI using the correct engine and fonts.
- [ ] Treat undefined references, missing citations, absent assets, and fatal layout errors as failures.
- [ ] Validate links between source manuscripts, PDFs, experiments, and index pages.
- [ ] Check that expected PDFs and gallery outputs exist after a build.
- [ ] Report page-count changes and unexpectedly empty or tiny artifacts.
- [ ] Validate HTML and ensure the repository-root redirect resolves to the intended gallery.
- [ ] Cache dependencies without caching generated research outputs as authoritative results.
- [ ] Publish only from a verified build and retain enough logs to diagnose failures.

## Completion criterion

A pull request receives a clear pass or failure for manuscripts, references, assets, experiment indexes, and deployable pages before merge.
EOF

if ! $apply; then
    printf '\nPreview only. Run %s --apply to create these issues in %s.\n' "${0##*/}" "$repo"
fi
