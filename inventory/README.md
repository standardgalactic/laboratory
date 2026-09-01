# Paper inventory

`papers.json` is the authoritative machine-readable inventory. `PAPERS.md` is a generated human-readable build matrix; it must not be edited directly.

Run the generator from the repository root:

```sh
python3 scripts/build-paper-inventory.py
```

The inventory scans root-level `.tex` and `.pdf` files, direct children of `source/`, and the complete `sproll-curriculum-bundle/`. It reports `continuation-geometry/`, `processing/`, `projects/`, and `working/` as deferred scope. The Sproll bundle is scanned recursively because its directories are meaningful curriculum tracks rather than undifferentiated draft locations.

The generator groups files by a conservative normalized basename. Suffixes such as `-draft`, `-notes`, `-extended`, and numbered-copy suffixes remain recorded as provenance within a family. When a family has more than one possible source or output, `source_path` or `output_path` remains null, every candidate is retained, and the row is marked `duplicate-review`.

A PDF without an editable source is marked `recovery-blocked`. A source without a PDF is marked `source-only`. Engine values are provisional inferences from the LaTeX preamble; page counts are measured by `pdfinfo` when it is installed. Each value carries a companion provenance field.

Sproll records carry `collection: "sproll-curriculum"` and a `track` value. Their IDs include the bundle-relative path so primary readers, workbooks, the formal essay, the methodology monograph, and superseded drafts cannot be collapsed into false duplicate families. Files under `superseded/` are retained as provenance and marked `superseded`, never `published`.

To preserve a deliberately assigned revision status across regeneration, edit `revision_status` in `papers.json` and set `revision_status_source` to `manual`. All other generated fields will be refreshed.

The check mode is suitable for later CI integration:

```sh
python3 scripts/build-paper-inventory.py --check
```
