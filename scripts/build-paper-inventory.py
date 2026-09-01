#!/usr/bin/env python3
"""Build the first laboratory paper inventory slice.

The scanner covers root-level files, direct children of source/, and the
structured Sproll curriculum bundle. Other directories are reported as
deferred rather than silently ignored. Existing manual revision statuses in
inventory/papers.json survive regeneration.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

SCHEMA_VERSION = 3
SCANNED_DIRECTORIES = [".", "source", "sproll-curriculum-bundle"]
DEFERRED_DIRECTORIES = ["continuation-geometry", "processing", "projects", "working"]
SOURCE_SUFFIXES = {".tex"}
OUTPUT_SUFFIXES = {".pdf"}
VARIANT_SUFFIX = re.compile(r"(?:[-_](?:draft|notes|extended|revised|final)|\s*\(\d+\))$", re.I)
TITLE_RE = re.compile(r"\\title(?:\[[^]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", re.S)


def is_companion_asset(path: Path) -> bool:
    """Detect the repository's companion-asset naming convention.

    Canonical LaTeX manuscripts and their built PDFs use lowercase,
    hyphenated (or underscored) basenames, e.g. `attention-compiler.tex`,
    `deployment_native_ternary_learning.pdf`. Slide decks, narrated audio,
    and other auxiliary presentation assets instead use TitleCase basenames
    with underscores, e.g. `The_Attention_Compiler.pdf`,
    `Borrowed_Intuition.pdf`. When more than one such asset shares a title,
    an additional `-word` suffix distinguishes them (e.g.
    `The_Attention_Compiler-notes.pdf`, `The_Attention_Compiler-draft.pdf`)
    rather than indicating a competing manuscript revision. A companion
    asset is not a build output of a paper and must never be folded into
    that paper's duplicate-family detection; it also does not necessarily
    correspond to any single paper in this inventory.
    """
    stem = path.stem
    return "_" in stem and any(char.isupper() for char in stem)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def family_key(path: Path) -> str:
    stem = path.stem.strip().lower().replace("_", "-").replace(" ", "-")
    while True:
        reduced = VARIANT_SUFFIX.sub("", stem)
        if reduced == stem:
            return re.sub(r"-+", "-", stem).strip("-")
        stem = reduced


def identity_key(path: Path, root: Path) -> str:
    """Keep structured curriculum tracks distinct from global paper families."""
    relative = path.relative_to(root)
    if relative.parts[0] == "sproll-curriculum-bundle":
        return relative.with_suffix("").as_posix()
    return family_key(path)


def provenance(path: Path | None, root: Path) -> tuple[str | None, str | None]:
    if path is None:
        return "laboratory", None
    relative = path.relative_to(root)
    if relative.parts[0] != "sproll-curriculum-bundle":
        return "laboratory", None
    return "sproll-curriculum", relative.parts[1] if len(relative.parts) > 2 else None


def latex_title(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = TITLE_RE.search(text)
    if not match:
        return None
    title = re.sub(r"\\(?:textbf|emph)\{([^{}]*)\}", r"\1", match.group(1))
    title = re.sub(r"\\vspace\*?\{[^{}]*\}", "", title)
    title = title.replace("\\\\", ": ")
    title = re.sub(r"\[[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:em|ex|pt|in|cm|mm)\]", "", title)
    title = re.sub(r"\\[A-Za-z]+\*?(?:\[[^]]*\])?", "", title)
    title = re.sub(r"\s*,\s*:", ":", title)
    title = re.sub(r"\s+([,;:])", r"\1", title)
    return re.sub(r"\s+", " ", title.replace("{", "").replace("}", "")).strip() or None


def display_title(key: str, sources: list[Path]) -> str:
    for source in sources:
        title = latex_title(source)
        if title:
            return title
    return key.replace("-", " ").title()


def engine_for(path: Path) -> tuple[str | None, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, "unavailable"
    if re.search(r"\\usepackage(?:\[[^]]*\])?\{(?:fontspec|polyglossia)\}", text):
        return "lualatex", "inferred-from-fontspec"
    if "\\documentclass" in text:
        return "pdflatex", "inferred-from-preamble"
    return None, "unavailable"


def page_count(path: Path) -> tuple[int | None, str]:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return None, "pdfinfo-unavailable"
    try:
        result = subprocess.run(
            [pdfinfo, str(path)], check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None, "pdfinfo-failed"
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.M)
    return (int(match.group(1)), "pdfinfo") if match else (None, "pdfinfo-failed")


def load_manual_statuses(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item["id"]: item["revision_status"]
        for item in data.get("papers", [])
        if item.get("revision_status_source") == "manual"
    }


def load_canonical_overrides(path: Path) -> dict[str, dict]:
    """Load human-reviewed canonical picks for duplicate families.

    A duplicate family (multiple sources or multiple outputs sharing a
    normalized basename) cannot be resolved automatically: it requires a
    person to read the candidates and decide which is the manuscript of
    record. Once decided, set `canonical_source_path` and/or
    `canonical_output_path` on that paper's entry in papers.json (each must
    be one of the recorded candidates) and add an `editorial_note`
    explaining the decision. These survive regeneration; every candidate
    remains listed for provenance.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    overrides = {}
    for item in data.get("papers", []):
        picked = {
            key: item[key]
            for key in ("canonical_source_path", "canonical_output_path", "editorial_note")
            if item.get(key)
        }
        if picked:
            overrides[item["id"]] = picked
    return overrides


def load_companion_links(path: Path) -> dict[str, str]:
    """Preserve manually assigned linked_paper_id values across regeneration."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        item["path"]: item["linked_paper_id"]
        for item in data.get("companion_assets", [])
        if item.get("linked_paper_id")
    }


def discover(root: Path, output_json: Path) -> dict:
    candidates: list[Path] = []
    companion_assets: list[Path] = []
    for directory in SCANNED_DIRECTORIES:
        base = root if directory == "." else root / directory
        if not base.is_dir():
            continue
        iterator = base.rglob("*") if directory == "sproll-curriculum-bundle" else base.iterdir()
        for path in iterator:
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES | OUTPUT_SUFFIXES:
                continue
            if path.suffix.lower() in OUTPUT_SUFFIXES and is_companion_asset(path):
                companion_assets.append(path)
            else:
                candidates.append(path)

    families: dict[str, dict[str, list[Path]]] = {}
    for path in sorted(candidates):
        bucket = families.setdefault(identity_key(path, root), {"sources": [], "outputs": []})
        bucket["sources" if path.suffix.lower() in SOURCE_SUFFIXES else "outputs"].append(path)

    manual_statuses = load_manual_statuses(output_json)
    canonical_overrides = load_canonical_overrides(output_json)
    companion_links = load_companion_links(output_json)
    papers = []
    for key, paths in sorted(families.items()):
        sources = sorted(paths["sources"])
        outputs = sorted(paths["outputs"])
        override = canonical_overrides.get(key, {})

        canonical_source = sources[0] if len(sources) == 1 else None
        if override.get("canonical_source_path"):
            picked = root / override["canonical_source_path"]
            if picked in sources:
                canonical_source = picked

        canonical_output = outputs[0] if len(outputs) == 1 else None
        if override.get("canonical_output_path"):
            picked = root / override["canonical_output_path"]
            if picked in outputs:
                canonical_output = picked

        representative = canonical_source or canonical_output
        collection, track = provenance(representative, root)
        resolved_by_override = bool(override.get("canonical_source_path") or override.get("canonical_output_path"))
        blockers = []
        if outputs and not sources:
            blockers.append("editable-source-missing")
        if sources and not outputs:
            blockers.append("output-pdf-missing")
        if (len(sources) > 1 or len(outputs) > 1) and not resolved_by_override:
            blockers.append("duplicate-family-requires-canonical-review")
        elif (len(sources) > 1 or len(outputs) > 1) and resolved_by_override:
            blockers.append("duplicate-family-resolved-by-editorial-override")

        engine, engine_source = engine_for(canonical_source) if canonical_source else (None, "ambiguous-or-missing-source")
        pages, pages_source = page_count(canonical_output) if canonical_output else (None, "ambiguous-or-missing-output")
        derived_status = (
            "superseded" if collection == "sproll-curriculum" and track == "superseded" else
            "published" if resolved_by_override and canonical_source and canonical_output else
            "recovery-blocked" if outputs and not sources else
            "duplicate-review" if len(sources) > 1 or len(outputs) > 1 else
            "published" if sources and outputs else
            "source-only"
        )
        status = manual_statuses.get(key, derived_status)
        papers.append({
            "id": key,
            "title": display_title(key, sources),
            "collection": collection,
            "track": track,
            "source_path": rel(canonical_source, root) if canonical_source else None,
            "source_candidates": [rel(path, root) for path in sources],
            "output_path": rel(canonical_output, root) if canonical_output else None,
            "output_candidates": [rel(path, root) for path in outputs],
            "canonical_source_path": override.get("canonical_source_path"),
            "canonical_output_path": override.get("canonical_output_path"),
            "editorial_note": override.get("editorial_note"),
            "build_engine": engine,
            "build_engine_source": engine_source,
            "page_count": pages,
            "page_count_source": pages_source,
            "revision_status": status,
            "revision_status_source": "manual" if key in manual_statuses else "derived",
            "recovery_blockers": blockers,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "scope": {
            "scanned_directories": SCANNED_DIRECTORIES,
            "deferred_directories": DEFERRED_DIRECTORIES,
            "recursive_directories": ["sproll-curriculum-bundle"],
        },
        "papers": papers,
        "companion_assets": [
            {
                "path": rel(path, root),
                "linked_paper_id": companion_links.get(rel(path, root)),
                "note": "TitleCase_With_Underscores basename: presentation/slide-deck or other "
                        "auxiliary asset, not a manuscript build output. Set linked_paper_id "
                        "manually in papers.json's companion_assets to associate it with a paper.",
            }
            for path in sorted(companion_assets)
        ],
    }


def markdown(data: dict) -> str:
    counts: dict[str, int] = {}
    for paper in data["papers"]:
        status = paper["revision_status"]
        counts[status] = counts.get(status, 0) + 1
    lines = [
        "# Laboratory paper inventory", "",
        "This file is generated from `inventory/papers.json`. Run `python3 scripts/build-paper-inventory.py` to refresh both files.", "",
        "## Scope", "",
        "The inventory scans repository-root manuscripts, direct children of `source/`, and the "
        "structured `sproll-curriculum-bundle/`. "
        "The following directories remain deliberately deferred: " + ", ".join(f"`{item}/`" for item in data["scope"]["deferred_directories"]) + ".", "",
        "## Status summary", "",
    ]
    lines.extend(f"- `{name}`: {count}" for name, count in sorted(counts.items()))
    lines.extend(["", "## Build matrix", "", "| Paper | Collection / track | Source | Output | Engine | Pages | Status | Blockers |", "|---|---|---|---|---|---:|---|---|"])
    for paper in data["papers"]:
        source = paper["source_path"] or "<br>".join(f"`{p}`" for p in paper["source_candidates"]) or "—"
        output = paper["output_path"] or "<br>".join(f"`{p}`" for p in paper["output_candidates"]) or "—"
        if paper["source_path"]:
            source = f"`{source}`"
        if paper["output_path"]:
            output = f"`{output}`"
        blockers = ", ".join(paper["recovery_blockers"]) or "—"
        location = paper["collection"] + (f" / {paper['track']}" if paper["track"] else "")
        lines.append(f"| {paper['title']} | {location} | {source} | {output} | {paper['build_engine'] or '—'} | {paper['page_count'] if paper['page_count'] is not None else '—'} | {paper['revision_status']} | {blockers} |")
    lines.extend(["", "## Provenance rules", "", "Engine values are inferred from the LaTeX preamble in this first slice. Page counts are measured with `pdfinfo`. A family with multiple source or output candidates remains unresolved unless a human has recorded a `canonical_source_path`/`canonical_output_path` override in `inventory/papers.json`; the generator always records every candidate for provenance.", ""])
    companion_assets = data.get("companion_assets", [])
    if companion_assets:
        lines.extend([
            "## Companion assets", "",
            "These files follow the repository's `TitleCase_With_Underscores` naming convention for "
            "slide decks, narrated audio companions, and other presentation assets. They are not "
            "manuscript build outputs and are excluded from duplicate-family detection above. "
            "`linked_paper_id` is set manually in `inventory/papers.json` when an asset is confirmed "
            "to accompany a specific paper.", "",
            "| Asset | Linked paper |", "|---|---|",
        ])
        for asset in companion_assets:
            lines.append(f"| `{asset['path']}` | {asset['linked_paper_id'] or '—'} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true", help="fail if committed outputs are stale")
    args = parser.parse_args()
    root = args.root.resolve()
    json_path = root / "inventory" / "papers.json"
    md_path = root / "inventory" / "PAPERS.md"
    data = discover(root, json_path)
    json_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    md_text = markdown(data)
    if args.check:
        # generated_at is intentionally ignored during deterministic checks
        try:
            old = json.loads(json_path.read_text(encoding="utf-8"))
            old["generated_at"] = data["generated_at"]
            json_same = old == data
            md_same = md_path.read_text(encoding="utf-8") == md_text
        except (OSError, json.JSONDecodeError):
            json_same = md_same = False
        if not (json_same and md_same):
            print("paper inventory is stale; run scripts/build-paper-inventory.py")
            return 1
        return 0
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    print(f"wrote {json_path.relative_to(root)} and {md_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
