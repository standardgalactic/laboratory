#!/usr/bin/env python3
"""Split gaps.md into task-specific contributor queues.

Usage:
    python3 split_queues.py gaps.md CSV_DIR [MD_DIR]

CSVs go to CSV_DIR; the readable queue documents go to MD_DIR (default CSV_DIR).
The queue index is written as CSV_DIR/queue-index.md, never README.md, so a
hand-written README next to the queues is never overwritten.

The scanner's Markdown output is the canonical input because it retains every
flagged location.  The generated queues deliberately separate bounded repairs
from authorial decisions instead of inheriting the composite gap score.
"""

import csv
import re
import sys
from collections import Counter
from pathlib import Path


QUEUE_FOR_KIND = {
    "uncited_claims": "citation-repairs",
    "uncited_works": "citation-repairs",
    "missing bib keys": "citation-repairs",
    "markers": "unfinished-material",
    "unproved": "proof-obligations",
    "stub_sections": "short-sections-author-review",
}

QUEUE_TITLES = {
    "citation-repairs": "Citation Repairs",
    "unfinished-material": "Unfinished Material",
    "proof-obligations": "Proof Obligations",
    "short-sections-author-review": "Short Sections: Author Review",
}

QUEUE_NOTES = {
    "citation-repairs": (
        "Bounded source work: verify the sentence, locate an appropriate source, "
        "and add or repair the corresponding bibliography entry and citation."
    ),
    "unfinished-material": (
        "Explicit TODO, placeholder, or similar markers. Confirm the intended "
        "content before replacing a marker whose wording does not determine it."
    ),
    "proof-obligations": (
        "Formal statements for which the static scan found no nearby proof. "
        "First confirm that a proof is genuinely absent rather than merely remote."
    ),
    "short-sections-author-review": (
        "Possible skeletal sections. These are review prompts, not presumed "
        "defects: concise sections, structural headings, and mathematical sections "
        "may be complete as written."
    ),
}

META_RE = re.compile(
    r"^`(?P<full_path>.+)` · (?P<words>[\d,]+) words · "
    r"(?P<cites>[\d,]+) cites \((?P<density>[\d.]+)/1k\) · "
    r"(?P<bib_entries>[\d,]+) bib entries$"
)
FLAG_RE = re.compile(
    r"^- \[ \] \*\*(?P<kind>[^*]+)\*\*"
    r"(?: `(?P<location>[^`]+)`)?(?:\s*:)?\s*(?P<finding>.*)$"
)


def parse(source):
    title = None
    meta = None
    rows = []
    for raw in source.read_text(encoding="utf-8").splitlines():
        if raw.rstrip() == "##" or raw.startswith("## "):
            # "##" alone is an untitled document (editors strip the trailing space)
            title = raw[2:].strip()
            meta = None
            continue
        match = META_RE.match(raw)
        if match:
            meta = match.groupdict()
            repo, path = meta["full_path"].split("/", 1)
            meta.update(repo=repo, document_path=path)
            continue
        match = FLAG_RE.match(raw)
        if not match or title is None or not meta:
            continue
        item = match.groupdict()
        kind = item["kind"].strip()
        queue = QUEUE_FOR_KIND.get(kind)
        if not queue:
            continue
        location = item["location"] or meta["document_path"]
        source_path, line = split_location(location)
        rows.append({
            "queue": queue,
            "kind": kind,
            "repository": meta["repo"],
            "document": meta["document_path"],
            "title": title or Path(meta["document_path"]).name,
            "source_path": source_path,
            "line": line,
            "words": int(meta["words"].replace(",", "")),
            "citations": int(meta["cites"].replace(",", "")),
            "citations_per_1k": float(meta["density"]),
            "bibliography_entries": int(meta["bib_entries"].replace(",", "")),
            "finding": item["finding"].strip(),
        })
    return rows


def split_location(location):
    path, colon, suffix = location.rpartition(":")
    if colon and suffix.isdigit():
        return path, int(suffix)
    return location, ""


def write_csv(path, rows):
    fields = [
        "kind", "repository", "document", "title", "source_path", "line",
        "words", "citations", "citations_per_1k", "bibliography_entries",
        "finding",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in rows)


def write_markdown(path, queue, rows):
    counts = Counter(row["kind"] for row in rows)
    documents = len({(row["repository"], row["document"]) for row in rows})
    lines = [
        "{% raw %}",
        f"# {QUEUE_TITLES[queue]}",
        "",
        QUEUE_NOTES[queue],
        "",
        f"{len(rows):,} findings across {documents:,} documents.",
        "",
    ]
    if len(counts) > 1:
        lines.extend([
            "Kinds: " + ", ".join(f"{kind} ({count:,})" for kind, count in sorted(counts.items())),
            "",
        ])
    current = None
    for row in rows:
        document = (row["repository"], row["document"])
        if document != current:
            current = document
            lines.extend([
                f"## {row['title']}",
                "",
                f"`{row['repository']}/{row['document']}` · "
                f"{row['words']:,} words · {row['citations']} citations "
                f"({row['citations_per_1k']:.2f}/1k)",
                "",
            ])
        location = row["source_path"] + (f":{row['line']}" if row["line"] != "" else "")
        detail = f" {row['finding']}" if row["finding"] else ""
        lines.append(f"- [ ] **{row['kind']}** `{location}`{detail}")
    lines.extend(["", "{% endraw %}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(path, grouped):
    lines = [
        "# Contributor Queues",
        "",
        "These queues separate mechanically different kinds of work that the full "
        "ledger combines for discovery. Complete an item only after checking the "
        "source at the recorded location; the flags are static-analysis prompts, "
        "not adjudications.",
        "",
        "| Queue | Findings | Documents | Intended use |",
        "|---|---:|---:|---|",
    ]
    for queue in QUEUE_TITLES:
        rows = grouped[queue]
        documents = len({(row["repository"], row["document"]) for row in rows})
        lines.append(
            f"| [{QUEUE_TITLES[queue]}]({queue}.md) | {len(rows):,} | "
            f"{documents:,} | {QUEUE_NOTES[queue]} |"
        )
    lines.extend([
        "",
        "Each queue is also available as CSV for sorting, assignment, and automated passes.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: split_queues.py gaps.md CSV_DIR [MD_DIR]")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    md_dir = Path(sys.argv[3]) if len(sys.argv) == 4 else output
    output.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)
    rows = parse(source)
    grouped = {queue: [] for queue in QUEUE_TITLES}
    for row in rows:
        grouped[row["queue"]].append(row)
    for queue, queue_rows in grouped.items():
        write_markdown(md_dir / f"{queue}.md", queue, queue_rows)
        write_csv(output / f"{queue}.csv", queue_rows)
    write_index(output / "queue-index.md", grouped)
    print(f"wrote {len(rows):,} findings to {len(grouped)} queues in {output}")


if __name__ == "__main__":
    main()
