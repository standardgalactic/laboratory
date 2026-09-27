#!/usr/bin/env python3
"""Regression tests for split_queues.py.

Run from the report directory:  python3 test_split_queues.py
"""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import split_queues  # noqa: E402

SAMPLE = """{% raw %}
## A Titled Essay: With Subtitle
`alphabet/essays/titled.tex` · 2400 words · 3 cites (1.25/1k) · 5 bib entries

Latest draft (edited 2026-03-01, chosen by date); earlier drafts set aside: `alphabet/essays/draft-01/titled.tex`

- [ ] **uncited_claims** `essays/titled.tex:12` Studies show that most readers skim.
- [ ] **uncited_works** `essays/titled.tex:40` As Smith et al. argued, the effect is small.
- [ ] **stub_sections** `essays/titled.tex:55` section "Background" (12 words)
- [ ] **unproved** `essays/titled.tex:80` theorem
- [ ] **markers** `essays/titled.tex:99` TODO: add figure
- [ ] **missing bib keys**: smith2020, jones2019

##
`kitbash/untitled.tex` · 900 words · 0 cites (0.0/1k) · 0 bib entries

- [ ] **uncited_claims** `untitled.tex:7` Recent work suggests otherwise.

## Owner-Qualified Repository
`8b-is:8b-public-documents/working/doc.tex` · 1200 words · 1 cites (0.83/1k) · 1 bib entries

- [ ] **unproved** `working/doc.tex:3` lemma

{% endraw %}
"""


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name) / "gaps.md"
        self.src.write_text(SAMPLE, encoding="utf-8")
        self.rows = split_queues.parse(self.src)

    def tearDown(self):
        self.tmp.cleanup()

    def queue_of(self, kind):
        return {r["queue"] for r in self.rows if r["kind"] == kind}

    def test_every_flag_is_classified(self):
        self.assertEqual(len(self.rows), 8)
        self.assertEqual(self.queue_of("uncited_claims"), {"citation-repairs"})
        self.assertEqual(self.queue_of("uncited_works"), {"citation-repairs"})
        self.assertEqual(self.queue_of("missing bib keys"), {"citation-repairs"})
        self.assertEqual(self.queue_of("markers"), {"unfinished-material"})
        self.assertEqual(self.queue_of("unproved"), {"proof-obligations"})
        self.assertEqual(self.queue_of("stub_sections"), {"short-sections-author-review"})

    def test_untitled_document_falls_back_to_file_name(self):
        rows = [r for r in self.rows if r["document"] == "untitled.tex"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "untitled.tex")

    def test_locations_and_metadata(self):
        row = next(r for r in self.rows if r["kind"] == "uncited_claims" and r["repository"] == "alphabet")
        self.assertEqual((row["source_path"], row["line"]), ("essays/titled.tex", 12))
        self.assertEqual((row["words"], row["citations"], row["bibliography_entries"]), (2400, 3, 5))
        keys = next(r for r in self.rows if r["kind"] == "missing bib keys")
        self.assertEqual(keys["line"], "")
        self.assertIn("smith2020", keys["finding"])

    def test_draft_note_is_not_a_finding(self):
        self.assertFalse(any("set aside" in r["finding"] for r in self.rows))

    def test_owner_qualified_repository_stays_whole(self):
        row = next(r for r in self.rows if r["document"].endswith("doc.tex"))
        self.assertEqual(row["repository"], "8b-is:8b-public-documents")
        self.assertEqual(row["document"], "working/doc.tex")


class OutputTests(unittest.TestCase):
    def test_readme_is_never_overwritten_and_totals_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gaps.md").write_text(SAMPLE, encoding="utf-8")
            readme = root / "README.md"
            readme.write_text("hand-written\n", encoding="utf-8")
            subprocess.run([sys.executable, str(HERE / "split_queues.py"), "gaps.md", "queues", "."],
                           cwd=root, check=True, capture_output=True)
            self.assertEqual(readme.read_text(encoding="utf-8"), "hand-written\n")
            self.assertFalse((root / "queues" / "README.md").exists())
            self.assertTrue((root / "queues" / "queue-index.md").exists())
            total = 0
            for queue in split_queues.QUEUE_TITLES:
                md = (root / f"{queue}.md").read_text(encoding="utf-8")
                self.assertTrue(md.startswith("{% raw %}") and md.rstrip().endswith("{% endraw %}"))
                with open(root / "queues" / f"{queue}.csv", encoding="utf-8") as fh:
                    n = sum(1 for _ in csv.DictReader(fh))
                self.assertEqual(md.count("- [ ] **"), n, queue)
                total += n
            self.assertEqual(total, 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
