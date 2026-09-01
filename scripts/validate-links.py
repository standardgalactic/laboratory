#!/usr/bin/env python3
"""Validate links and asset integrity across the laboratory site.

Checks, without external tooling:

* Every local href/src in the root and gallery `index.html` pages resolves
  to a file that exists on disk.
* The root redirect (`meta http-equiv="refresh"` / `location.replace`)
  target resolves to a directory that itself serves an `index.html`.
* Every `source_path` / `output_path` recorded in `inventory/papers.json`
  exists on disk.
* Every referenced output PDF starts with a `%PDF` header and is larger
  than a minimal-content threshold, catching truncated or empty artifacts.

Intended for CI (`python3 scripts/validate-links.py`); exits non-zero and
prints every problem found rather than stopping at the first one.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MIN_PDF_BYTES = 512
HREF_RE = re.compile(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', re.I)


def is_local(url: str) -> bool:
    if not url or url.startswith("#"):
        return False
    scheme = urlsplit(url).scheme
    return scheme in ("", "file")


def check_html_links(html_path: Path, problems: list[str]) -> None:
    text = html_path.read_text(encoding="utf-8")
    base = html_path.parent
    for match in HREF_RE.finditer(text):
        url = match.group(1)
        if not is_local(url):
            continue
        target = urlsplit(url).path
        if not target:
            continue
        candidate = (base / target).resolve()
        if not candidate.exists():
            problems.append(f"{html_path.relative_to(ROOT)}: broken local link '{url}'")


def check_root_redirect(problems: list[str]) -> None:
    root_index = ROOT / "index.html"
    if not root_index.exists():
        problems.append("index.html: repository-root redirect page is missing")
        return
    text = root_index.read_text(encoding="utf-8")
    refresh = re.search(r'''http-equiv=["']refresh["']\s+content=["'][^;]*;\s*url=([^"']+)["']''', text, re.I)
    if not refresh:
        problems.append("index.html: no meta refresh redirect found")
        return
    target = refresh.group(1).strip()
    target_dir = (ROOT / target.rstrip("/")).resolve()
    if not target_dir.is_dir() or not (target_dir / "index.html").exists():
        problems.append(f"index.html: redirect target '{target}' does not resolve to a directory with index.html")


def check_inventory(problems: list[str]) -> None:
    inventory_path = ROOT / "inventory" / "papers.json"
    if not inventory_path.exists():
        problems.append("inventory/papers.json is missing")
        return
    data = json.loads(inventory_path.read_text(encoding="utf-8"))
    for paper in data.get("papers", []):
        paper_id = paper.get("id", "<unknown>")
        for field in ("source_path", "output_path"):
            value = paper.get(field)
            paths = value if isinstance(value, list) else [value] if value else []
            for rel_path in paths:
                full = ROOT / rel_path
                if not full.exists():
                    problems.append(f"inventory: '{paper_id}' {field} does not exist: {rel_path}")
                elif field == "output_path" and full.suffix.lower() == ".pdf":
                    check_pdf(full, paper_id, problems)


def check_pdf(pdf_path: Path, paper_id: str, problems: list[str]) -> None:
    size = pdf_path.stat().st_size
    if size < MIN_PDF_BYTES:
        problems.append(f"inventory: '{paper_id}' output PDF is suspiciously small ({size} bytes): {pdf_path.relative_to(ROOT)}")
        return
    with pdf_path.open("rb") as fh:
        header = fh.read(5)
    if header != b"%PDF-":
        problems.append(f"inventory: '{paper_id}' output PDF has no valid %PDF header: {pdf_path.relative_to(ROOT)}")


def main() -> int:
    problems: list[str] = []

    for html_path in [ROOT / "index.html", ROOT / "experiments" / "index.html"]:
        if html_path.exists():
            check_html_links(html_path, problems)
        else:
            problems.append(f"{html_path.relative_to(ROOT)} is missing")

    check_root_redirect(problems)
    check_inventory(problems)

    if problems:
        for problem in problems:
            print(f"validate-links: {problem}", file=sys.stderr)
        print(f"validate-links: {len(problems)} problem(s) found", file=sys.stderr)
        return 1

    print("validate-links: all local links, redirects, and inventory assets resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
