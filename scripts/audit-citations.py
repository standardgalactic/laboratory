#!/usr/bin/env python3
"""Audit citation/bibliography consistency across every LaTeX manuscript.

For issue #3 (references, citations, and claim-provenance audits), this
script provides the mechanical half of the work described in the issue:
detecting missing bibliography entries and orphaned references
automatically. It does not judge whether a citation is evidentially
appropriate for its claim; that judgment still requires a human reader.

A "document" is a `.tex` file containing `\\documentclass`, plus every file
it pulls in (recursively) via `\\input{...}` or `\\include{...}`. Citation
keys (`\\cite{...}`, `\\citep{...}`, comma-separated) used anywhere in a
document are cross-checked against `\\bibitem{...}` keys defined anywhere
in that same document (the repository's convention is inline
`thebibliography`, not external `.bib` files).

Reports, for every document:

* Undefined citations: a `\\cite`/`\\citep` key with no matching `\\bibitem`.
* Orphaned bibliography entries: a `\\bibitem` never cited anywhere in the
  document (dead weight, or evidence a claim using it was cut).
* Duplicate `\\bibitem` keys within one document.
* Documents that cite but have no bibliography in scope at all.

Usage:

    python3 scripts/audit-citations.py            # write inventory/CITATIONS.md and .json
    python3 scripts/audit-citations.py --check    # validate only, exit non-zero on any problem
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "inventory" / "citations.json"
REPORT_MD = ROOT / "inventory" / "CITATIONS.md"
EXCLUDE_DIR_NAMES = {".git"}

DOCUMENTCLASS_RE = re.compile(r"\\documentclass")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
CITE_RE = re.compile(r"\\cite[pt]?\*?(?:\[[^\]]*\])?\{([^}]+)\}")
BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}")


def all_tex_files() -> list[Path]:
    return [
        p for p in ROOT.rglob("*.tex")
        if not any(part in EXCLUDE_DIR_NAMES for part in p.relative_to(ROOT).parts)
    ]


def resolve_input(raw: str, including_file: Path) -> Path | None:
    name = raw if raw.endswith(".tex") else raw + ".tex"
    candidate = (including_file.parent / name).resolve()
    if candidate.exists():
        return candidate
    # LaTeX also resolves \input relative to the root document's directory.
    return None


def collect_document(root_file: Path, file_cache: dict[Path, str]) -> list[Path]:
    seen: list[Path] = []
    stack = [root_file]
    visited: set[Path] = set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        seen.append(current)
        text = file_cache.setdefault(current, current.read_text(encoding="utf-8", errors="replace"))
        for match in INPUT_RE.finditer(text):
            resolved = resolve_input(match.group(1), current)
            if resolved and resolved not in visited:
                stack.append(resolved)
    return seen


def split_keys(raw: str) -> list[str]:
    return [key.strip() for key in raw.split(",") if key.strip()]


def audit() -> dict:
    tex_files = all_tex_files()
    file_cache: dict[Path, str] = {}
    for path in tex_files:
        file_cache[path] = path.read_text(encoding="utf-8", errors="replace")

    roots = [p for p in tex_files if DOCUMENTCLASS_RE.search(file_cache[p])]
    included_by_some_root: set[Path] = set()

    documents = []
    for root_file in sorted(roots):
        members = collect_document(root_file, file_cache)
        included_by_some_root.update(members)

        cites: dict[str, list[str]] = {}
        bibitems: dict[str, list[str]] = {}
        for member in members:
            rel = member.relative_to(ROOT).as_posix()
            text = file_cache[member]
            for match in CITE_RE.finditer(text):
                for key in split_keys(match.group(1)):
                    cites.setdefault(key, []).append(rel)
            for match in BIBITEM_RE.finditer(text):
                key = match.group(1).strip()
                bibitems.setdefault(key, []).append(rel)

        undefined = sorted(set(cites) - set(bibitems))
        orphaned = sorted(set(bibitems) - set(cites))
        duplicates = sorted(key for key, locations in bibitems.items() if len(locations) > 1)

        documents.append({
            "root": root_file.relative_to(ROOT).as_posix(),
            "members": [m.relative_to(ROOT).as_posix() for m in sorted(members)],
            "citation_count": sum(len(v) for v in cites.values()),
            "unique_citations": len(cites),
            "bibitem_count": len(bibitems),
            "undefined_citations": [{"key": k, "cited_in": cites[k]} for k in undefined],
            "orphaned_bibitems": [{"key": k, "defined_in": bibitems[k]} for k in orphaned],
            "duplicate_bibitems": [{"key": k, "defined_in": bibitems[k]} for k in duplicates],
            "cites_without_any_bibliography": bool(cites) and not bibitems,
        })

    # Non-root files with \cite that aren't reachable from any \documentclass
    # root indicate either a missing \input wiring or an orphaned fragment.
    orphaned_fragments = []
    for path in sorted(tex_files):
        if path in included_by_some_root:
            continue
        text = file_cache[path]
        if CITE_RE.search(text) or BIBITEM_RE.search(text):
            orphaned_fragments.append(path.relative_to(ROOT).as_posix())

    return {
        "schema_version": 1,
        "documents": documents,
        "orphaned_fragments": orphaned_fragments,
    }


def markdown(data: dict) -> str:
    lines = [
        "# Citation and bibliography audit", "",
        "This file is generated by `scripts/audit-citations.py`; do not edit directly. "
        "It reports mechanical inconsistencies only (undefined citation keys, orphaned "
        "bibliography entries, duplicate keys). It does not evaluate whether a citation "
        "is an evidentially appropriate source for its claim.", "",
        "Documents that share an identical set of findings (for example, several "
        "standalone-compile `parts/partN.tex` variants of one manuscript that all pull "
        "in the same shared bibliography) are grouped into a single entry below.", "",
    ]

    def signature(doc: dict) -> tuple:
        return (
            tuple(sorted(item["key"] for item in doc["undefined_citations"])),
            tuple(sorted(item["key"] for item in doc["orphaned_bibitems"])),
            tuple(sorted(item["key"] for item in doc["duplicate_bibitems"])),
            doc["cites_without_any_bibliography"],
        )

    groups: dict[tuple, list[dict]] = {}
    for doc in data["documents"]:
        issues = doc["undefined_citations"] or doc["orphaned_bibitems"] or doc["duplicate_bibitems"] or doc["cites_without_any_bibliography"]
        if not issues:
            continue
        groups.setdefault(signature(doc), []).append(doc)

    problems = 0
    for docs in groups.values():
        problems += 1
        doc = docs[0]
        heading = " / ".join(f"`{d['root']}`" for d in docs)
        lines.append(f"## {heading}")
        lines.append("")
        if doc["cites_without_any_bibliography"]:
            lines.append("- Cites sources but has no `\\bibitem` in scope at all.")
        for item in doc["undefined_citations"]:
            locations = ", ".join(f"`{loc}`" for loc in item["cited_in"])
            lines.append(f"- Undefined citation key `{item['key']}` (cited in {locations})")
        for item in doc["orphaned_bibitems"]:
            locations = ", ".join(f"`{loc}`" for loc in item["defined_in"])
            lines.append(f"- Orphaned bibliography entry `{item['key']}` (defined in {locations}, never cited)")
        for item in doc["duplicate_bibitems"]:
            locations = ", ".join(f"`{loc}`" for loc in item["defined_in"])
            lines.append(f"- Duplicate `\\bibitem` key `{item['key']}` (defined in {locations})")
        lines.append("")

    if data["orphaned_fragments"]:
        problems += len(data["orphaned_fragments"])
        lines.append("## Orphaned fragments")
        lines.append("")
        lines.append(
            "These files contain `\\cite` or `\\bibitem` but are not reachable via "
            "`\\input`/`\\include` from any file with `\\documentclass`. Either they are "
            "missing from a document's input list, or they are dead drafts."
        )
        lines.append("")
        for frag in data["orphaned_fragments"]:
            lines.append(f"- `{frag}`")
        lines.append("")

    if problems == 0:
        lines.append("No citation or bibliography inconsistencies detected.")
        lines.append("")

    lines.append("## All documents scanned")
    lines.append("")
    lines.append("| Document | Files | Unique citations | Bibliography entries | Clean |")
    lines.append("|---|---:|---:|---:|---|")
    for doc in data["documents"]:
        clean = "yes" if not (doc["undefined_citations"] or doc["orphaned_bibitems"] or doc["duplicate_bibitems"] or doc["cites_without_any_bibliography"]) else "no"
        lines.append(f"| `{doc['root']}` | {len(doc['members'])} | {doc['unique_citations']} | {doc['bibitem_count']} | {clean} |")
    lines.append("")

    return "\n".join(lines)


def has_hard_errors(data: dict) -> bool:
    """Broken-reference errors: these indicate a real build/consistency defect.

    Orphaned bibliography entries are deliberately excluded: an unused
    `\\bibitem` is a scholarly content question (add the citation or trim
    the entry, per issue #2/#3) rather than a broken reference, so it must
    not fail CI or block a build. Report it, but don't gate on it.
    """
    if data["orphaned_fragments"]:
        return True
    return any(
        doc["undefined_citations"] or doc["duplicate_bibitems"] or doc["cites_without_any_bibliography"]
        for doc in data["documents"]
    )


def has_any_findings(data: dict) -> bool:
    if data["orphaned_fragments"]:
        return True
    return any(
        doc["undefined_citations"] or doc["orphaned_bibitems"] or doc["duplicate_bibitems"] or doc["cites_without_any_bibliography"]
        for doc in data["documents"]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only; do not write reports")
    args = parser.parse_args()

    data = audit()

    if args.check:
        any_findings = has_any_findings(data)
        if any_findings:
            for doc in data["documents"]:
                for item in doc["undefined_citations"]:
                    print(f"audit-citations: ERROR {doc['root']}: undefined citation '{item['key']}'", file=sys.stderr)
                for item in doc["duplicate_bibitems"]:
                    print(f"audit-citations: ERROR {doc['root']}: duplicate bibitem key '{item['key']}'", file=sys.stderr)
                if doc["cites_without_any_bibliography"]:
                    print(f"audit-citations: ERROR {doc['root']}: cites sources but has no bibliography", file=sys.stderr)
                for item in doc["orphaned_bibitems"]:
                    print(f"audit-citations: note {doc['root']}: orphaned bibliography entry '{item['key']}' (not a build failure)", file=sys.stderr)
            for frag in data["orphaned_fragments"]:
                print(f"audit-citations: ERROR orphaned fragment not reachable from any document root: {frag}", file=sys.stderr)
        if has_hard_errors(data):
            return 1
        print(f"audit-citations: {len(data['documents'])} document(s), no broken references"
              + (" (orphaned-entry notes above are informational only)" if any_findings else ""))
        return 0

    REPORT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(markdown(data), encoding="utf-8")
    print(f"wrote {REPORT_JSON.relative_to(ROOT)} and {REPORT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
