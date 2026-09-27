[Open Threads Ledger](https://standardgalactic.github.io/laboratory/report/open-threads-ledger.pdf) — *Brief*

[Full Report](https://standardgalactic.github.io/laboratory/report/open-threads-ledger-full.pdf)

* [Dashboard](https://standardgalactic.github.io/laboratory/report/)

# Contributor Queues

These queues separate mechanically different kinds of work that the full ledger combines for discovery. Complete an item only after checking the source at the recorded location; the flags are static-analysis prompts, not adjudications.

Only the latest draft of each essay is included: 602 essays, with 229 earlier drafts set aside. Drafts are grouped by path (draft-01/, draft 03, -v2, (3) removed) or by shared title, and the kept draft is the one edited most recently in the repository history. When drafts were committed together, the highest draft number wins unless another is clearly more developed. Every grouping and the reason for each pick is in [draft-groups.csv](draft-groups.csv); 21 picks marked CHECK are worth a glance. To force a different draft, add its `repo/path` to [keep.txt](keep.txt) and rerun.

| Queue | Findings | Documents | Intended use |
|---|---:|---:|---|
| [Citation Repairs](citation-repairs.md) | 881 | 265 | Bounded source work: verify the sentence, locate an appropriate source, and add or repair the corresponding bibliography entry and citation. |
| [Unfinished Material](unfinished-material.md) | 72 | 33 | Explicit TODO, placeholder, or similar markers. Confirm the intended content before replacing a marker whose wording does not determine it. |
| [Proof Obligations](proof-obligations.md) | 1,673 | 242 | Formal statements for which the static scan found no nearby proof. First confirm that a proof is genuinely absent rather than merely remote. |
| [Short Sections: Author Review](short-sections-author-review.md) | 11,370 | 362 | Possible skeletal sections. These are review prompts, not presumed defects: concise sections, structural headings, and mathematical sections may be complete as written. |

Each queue is also available as CSV (in [queues/](queues/)) for sorting, assignment, and automated passes.

## Regenerating

```
python3 essay_gaps.py REPO_DIRS... --json gaps.json
python3 content_mtimes.py gaps.json BARE_CLONES... > tex_mtimes.json
python3 dedupe_drafts.py gaps.json tex_mtimes.json gaps_latest.json --groups draft-groups.csv --roots . --keep keep.txt
python3 gaps_outputs.py gaps_latest.json gaps.md gaps.csv
python3 split_queues.py gaps.md queues .
python3 gaps_to_latex.py gaps_latest.json open-threads-ledger-full.tex --full
```

The queue index is written to `queues/queue-index.md`, so this README is never overwritten. Run `python3 test_split_queues.py` after changing the splitter.

Bare clones for dating need history but no file contents: `git clone --bare --filter=blob:none URL owner_repo`.
