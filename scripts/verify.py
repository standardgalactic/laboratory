#!/usr/bin/env python3
"""Verify the laboratory collection: manuscripts, references, assets, indexes, pages.

No third-party dependencies. Designed as a pull-request gate:

  * a broken link, or a standalone manuscript without its PDF, **fails** when the
    offending file is part of the change under review;
  * the same problem elsewhere is **reported as a warning**, so pre-existing debt
    is visible without blocking unrelated work (the repository currently carries
    some: a couple of placeholder images in README.md, `reports/` vs `report/`,
    and a set of `continuation-geometry` filename mismatches);
  * the repository-root redirect is always enforced.

Usage:
    scripts/verify.py                     # full audit; fails only on the root redirect
    scripts/verify.py --changed <base-ref>  # gate: fail on problems in changed files
    scripts/verify.py --strict-all        # fail on every problem (for a cleanup pass)

`.github/verify-baseline.txt` lists accepted gaps (raw target or "doc: target").
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / ".github" / "verify-baseline.txt"
SKIP_DIRS = {".git", ".github", "_site", "node_modules", "__pycache__"}
TINY_BYTES = 2048


def baseline() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {
        s.strip()
        for s in BASELINE.read_text().splitlines()
        if s.strip() and not s.strip().startswith("#")
    }


def walk(*suffixes: str):
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(suffixes):
                yield Path(dirpath) / name


def git_changed(base: str) -> set[str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout
    except Exception as exc:  # pragma: no cover - diagnostic only
        print(f"  [warn] could not diff against {base}: {exc}")
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def site_url_to_local(url: str) -> str | None:
    m = re.search(r"standardgalactic\.github\.io/laboratory/([^?#]*)", url)
    if m:
        return m.group(1)
    m = re.search(r"github\.com/standardgalactic/laboratory/(?:blob|tree)/main/([^?#]+)", url)
    if m:
        return m.group(1)
    return None


LINK_RE = re.compile(r'(?:\]\(([^)\s]+)\))|(?:href="([^"]+)")|(?:src="([^"]+)")')


def links_in(text: str):
    for m in LINK_RE.finditer(text):
        target = m.group(1) or m.group(2) or m.group(3)
        if target:
            yield target


def pdf_pages(pdf: Path) -> int | str:
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return "?"
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else "?"


class Report:
    def __init__(self, strict: set[str], strict_all: bool):
        self.strict = strict
        self.strict_all = strict_all
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.based: list[str] = []

    def problem(self, rel_doc: str, message: str, key: str | None = None) -> None:
        base = baseline()
        if key and (key in base or (key.split(": ", 1)[-1] in base)):
            self.based.append(key)
            print(f"  [BASE] {key}")
            return
        is_strict = self.strict_all or rel_doc in self.strict
        if is_strict:
            self.failures.append(message)
            print(f"  [FAIL] {message}")
        else:
            self.warnings.append(message)
            print(f"  [warn] {message}")


def check_manuscripts(rep: Report) -> None:
    print("manuscripts")
    for tex in sorted(walk(".tex")):
        rel = tex.relative_to(ROOT)
        text = tex.read_text(errors="replace")
        if "\\documentclass" not in text:
            continue  # fragment consumed via \input
        pdf = tex.with_suffix(".pdf")
        if not pdf.exists():
            rep.problem(str(rel), f"standalone manuscript has no PDF: {rel}", key=None)
            continue
        size = pdf.stat().st_size
        pages = pdf_pages(pdf)
        flag = ""
        if size < TINY_BYTES:
            flag = "  [tiny]"
            rep.warnings.append(f"tiny PDF: {pdf.relative_to(ROOT)} ({size} B)")
        print(f"  [OK]   {rel} -> {pdf.name}  {size:>8} B  pages={pages}{flag}")


def check_links(rep: Report) -> None:
    print("links & assets")
    for doc in sorted(list(walk(".md")) + list(walk(".html"))):
        rel_doc = str(doc.relative_to(ROOT))
        seen: set[str] = set()
        for target in links_in(doc.read_text(errors="replace")):
            if target.startswith(("#", "mailto:", "data:", "javascript:")):
                continue
            local = site_url_to_local(target)
            if local is None:
                if re.match(r"^[a-z]+://", target):
                    continue
                local = target
            local = local.split("#", 1)[0].split("?", 1)[0]
            key = f"{rel_doc}: {target}"
            if key in seen:
                continue
            seen.add(key)
            if local == "" or local == "/":
                continue
            resolved = ROOT / local.lstrip("/") if local.startswith("/") else doc.parent / local
            ok = resolved.exists() or resolved.with_suffix(".html").exists()
            if not ok and resolved.is_dir() is False:
                ok = (resolved / "index.html").exists()
            if ok:
                continue
            rep.problem(rel_doc, f"broken link in {rel_doc}: {target}", key=key)


def check_root_redirect(rep: Report) -> None:
    print("root redirect")
    index = ROOT / "index.html"
    if not index.exists():
        rep.failures.append("missing repository-root index.html")
        print("  [FAIL] no index.html at root")
        return
    text = index.read_text(errors="replace")
    m = re.search(r'content="\d+;\s*url=([^"]+)"', text) or re.search(
        r"location\.replace\(\s*[`'\"]([^`'\"]+)", text
    )
    if not m:
        rep.warnings.append("root index.html has no detectable redirect target")
        print("  [note] no redirect target found")
        return
    target = m.group(1).split("#")[0].split("?")[0].rstrip("/")
    resolved = ROOT / (target.lstrip("/") if target.startswith("/") else target)
    has_index = (resolved / "index.html").exists()
    if resolved.exists() and (resolved.is_dir() is False or has_index):
        print(f"  [OK]   redirect -> {target} (index={'yes' if has_index else 'n/a'})")
    else:
        rep.failures.append(f"root redirect target missing: {target}")
        print(f"  [FAIL] redirect -> {target} (missing)")


def main(argv: list[str]) -> int:
    strict_all = "--strict-all" in argv
    strict: set[str] = set()
    if "--changed" in argv:
        i = argv.index("--changed")
        base = argv[i + 1] if i + 1 < len(argv) else "origin/main"
        strict = git_changed(base)
        print(f"gate mode: {len(strict)} changed file(s) vs {base}")

    rep = Report(strict, strict_all)
    print(f"laboratory verify  root={ROOT}\n")
    check_manuscripts(rep)
    print()
    check_links(rep)
    print()
    check_root_redirect(rep)
    print()

    if rep.based:
        print(f"allowlisted (baseline): {len(rep.based)}")
    if rep.warnings:
        print(f"warnings: {len(rep.warnings)}")
        for w in rep.warnings[:20]:
            print(f"  - {w}")
        if len(rep.warnings) > 20:
            print(f"  ... and {len(rep.warnings) - 20} more")
    print()
    if rep.failures:
        print(f"RESULT: FAIL ({len(rep.failures)} failure(s))")
        for f in rep.failures:
            print(f"  - {f}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
