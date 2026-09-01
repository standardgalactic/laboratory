# Paper inventory

`papers.json` is the authoritative machine-readable inventory. `PAPERS.md` is a generated human-readable build matrix; it must not be edited directly.

Run the generator from the repository root:

```sh
python3 scripts/build-paper-inventory.py
```

The initial slice scans only root-level `.tex` and `.pdf` files plus direct children of `source/`. It reports `continuation-geometry/`, `processing/`, `projects/`, and `working/` as deferred scope. This boundary keeps the first implementation reviewable while making the omission visible in the data.

The generator groups files by a conservative normalized basename. Suffixes such as `-draft`, `-notes`, `-extended`, and numbered-copy suffixes remain recorded as provenance within a family. When a family has more than one possible source or output, `source_path` or `output_path` remains null, every candidate is retained, and the row is marked `duplicate-review`.

A PDF without an editable source is marked `recovery-blocked`. A source without a PDF is marked `source-only`. Engine values are provisional inferences from the LaTeX preamble; page counts are measured by `pdfinfo` when it is installed. Each value carries a companion provenance field.

To preserve a deliberately assigned revision status across regeneration, edit `revision_status` in `papers.json` and set `revision_status_source` to `manual`. All other generated fields will be refreshed.

The check mode is suitable for later CI integration:

```sh
python3 scripts/build-paper-inventory.py --check
```
