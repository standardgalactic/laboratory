#!/usr/bin/env python3
"""Generate the headless Blender experiment gallery from repository state.

The gallery page (`experiments/index.html`) is generated output; it must not
be edited directly. Edit `experiments/metadata.json` for captions,
structural questions, and related-paper links, then re-run this script.

    python3 scripts/build-gallery.py

Validation-only mode, suitable for CI, exits non-zero on any inconsistency
between scripts, rendered outputs, thumbnails, and metadata without writing
anything:

    python3 scripts/build-gallery.py --check
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT / "experiments"
SCRIPTS_DIR = EXPERIMENTS_DIR / "experiments"
OUTPUT_DIR = EXPERIMENTS_DIR / "output"
THUMBS_DIR = OUTPUT_DIR / "thumbs"
METADATA_PATH = EXPERIMENTS_DIR / "metadata.json"
INDEX_PATH = EXPERIMENTS_DIR / "index.html"
THUMB_MAX_SIDE = 640
REQUIRED_FIELDS = ("id", "repository", "filter", "title", "alt", "description", "question")
ID_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")

try:
    from PIL import Image
except ImportError:  # pragma: no cover - degraded mode without Pillow.
    Image = None


def load_metadata() -> tuple[list[dict], list[str]]:
    try:
        data = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"cannot read {METADATA_PATH.relative_to(ROOT)}: {exc}"]
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return [], ["metadata.json must be an object with schema_version 1"]
    entries = data.get("experiments")
    if not isinstance(entries, list):
        return [], ["metadata.json field 'experiments' must be a list"]
    return entries, validate_metadata(entries)


def validate_metadata(entries: list[dict]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    allowed_filters = {name for name, _ in FILTERS_ORDER if name != "all"}

    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"metadata entry {position} must be an object")
            continue
        label = entry.get("id", f"at position {position}")
        missing = [
            field
            for field in REQUIRED_FIELDS
            if not isinstance(entry.get(field), str) or not entry[field].strip()
        ]
        if missing:
            problems.append(f"metadata entry '{label}' has missing or invalid fields: {', '.join(missing)}")
        eid = entry.get("id")
        if isinstance(eid, str):
            if not ID_RE.fullmatch(eid):
                problems.append(f"metadata entry id '{eid}' must use lowercase snake_case")
            if eid in seen:
                problems.append(f"duplicate metadata entry id: '{eid}'")
            seen.add(eid)
        filt = entry.get("filter")
        if isinstance(filt, str) and filt not in allowed_filters:
            problems.append(f"metadata entry '{label}' uses unknown filter: '{filt}'")
        related = entry.get("related", [])
        if not isinstance(related, list):
            problems.append(f"metadata entry '{label}' field 'related' must be a list")
            continue
        for link in related:
            valid_link = isinstance(link, dict) and all(
                isinstance(link.get(key), str) and link[key].strip()
                for key in ("label", "path")
            )
            if not valid_link:
                problems.append(f"metadata entry '{label}' has an invalid related link")
                continue
            path = Path(link["path"])
            if path.is_absolute() or ".." in path.parts:
                problems.append(f"metadata entry '{label}' related path must stay inside the repository: {link['path']}")
    return problems


def discover_scripts() -> dict[str, Path]:
    return {p.stem: p for p in sorted(SCRIPTS_DIR.glob("*.py"))}


def discover_outputs() -> tuple[dict[str, Path], dict[str, Path]]:
    pngs = {p.stem: p for p in sorted(OUTPUT_DIR.glob("*.png"))}
    blends = {p.stem: p for p in sorted(OUTPUT_DIR.glob("*.blend"))}
    return pngs, blends


def cross_check(entries: list[dict], scripts: dict, pngs: dict, blends: dict) -> list[str]:
    problems = []
    valid_entries = [e for e in entries if isinstance(e, dict) and isinstance(e.get("id"), str)]
    entry_ids = {e["id"] for e in valid_entries}

    for entry in valid_entries:
        eid = entry["id"]
        if eid not in scripts:
            problems.append(f"metadata entry '{eid}' has no matching script in experiments/experiments/")
        if eid not in pngs:
            problems.append(f"metadata entry '{eid}' has no rendered PNG in experiments/output/")
        if eid not in blends:
            problems.append(f"metadata entry '{eid}' has no .blend file in experiments/output/")
        for link in entry.get("related", []):
            if not (ROOT / link["path"]).exists():
                problems.append(f"metadata entry '{eid}' related link is missing: {link['path']}")

    for sid in scripts:
        if sid not in entry_ids:
            problems.append(f"orphaned script with no metadata entry: experiments/experiments/{sid}.py")

    for pid in pngs:
        if pid not in entry_ids:
            problems.append(f"orphaned render with no metadata entry: experiments/output/{pid}.png")

    for bid in blends:
        if bid not in entry_ids:
            problems.append(f"orphaned .blend with no metadata entry: experiments/output/{bid}.blend")

    return problems


def ensure_thumbnails(entries: list[dict], pngs: dict, check_only: bool) -> list[str]:
    problems = []
    if Image is None:
        problems.append("Pillow is not installed; cannot generate or verify efficient thumbnails (pip install Pillow)")
        return problems

    if not check_only:
        THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    entry_ids = {
        entry["id"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    for thumb in sorted(THUMBS_DIR.glob("*.jpg")):
        if thumb.stem not in entry_ids:
            problems.append(f"orphaned thumbnail with no metadata entry: experiments/output/thumbs/{thumb.name}")

    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        eid = entry["id"]
        src = pngs.get(eid)
        if src is None:
            continue
        thumb = THUMBS_DIR / f"{eid}.jpg"
        if check_only:
            if not thumb.exists():
                problems.append(f"missing thumbnail for '{eid}': experiments/output/thumbs/{eid}.jpg")
                continue
            try:
                with Image.open(thumb) as im:
                    im.verify()
                with Image.open(thumb) as im:
                    if max(im.size) > THUMB_MAX_SIDE:
                        problems.append(f"thumbnail for '{eid}' exceeds {THUMB_MAX_SIDE}px: {im.size[0]}x{im.size[1]}")
            except (OSError, ValueError) as exc:
                problems.append(f"invalid thumbnail for '{eid}': {exc}")
            continue
        if thumb.exists() and thumb.stat().st_mtime >= src.stat().st_mtime:
            continue
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((THUMB_MAX_SIDE, THUMB_MAX_SIDE))
            im.save(thumb, "JPEG", quality=82, optimize=True)
    return problems


FILTERS_ORDER = [
    ("all", "All"),
    ("calculus", "calculus"),
    ("tartan", "TARTAN"),
    ("hydra", "HYDRA"),
    ("autogenerative", "autogenerative-dynamics"),
    ("cliodynamics", "cliodynamics"),
    ("spherepop", "spherepop"),
    ("chloroplasts", "Chloroplasts"),
    ("alphabet", "alphabet"),
]

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Flyxion Headless Experiments</title>
  <style>
    :root {{
      --background: #070a0f;
      --panel: #0d131c;
      --line: #243243;
      --text: #e7edf2;
      --muted: #91a0ad;
      --cyan: #59d9ff;
      --amber: #ff8a3d;
    }}

    * {{ box-sizing: border-box; }}

    html {{ background: var(--background); }}

    body {{
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 15% -10%, #123047 0, transparent 32rem),
        radial-gradient(circle at 90% 5%, #39180e 0, transparent 28rem),
        var(--background);
      font-family: ui-monospace, "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      min-height: 100vh;
    }}

    header, main, footer {{
      width: min(1540px, calc(100% - 32px));
      margin-inline: auto;
    }}

    header {{ padding: 72px 0 34px; }}

    .eyebrow {{
      margin: 0 0 14px;
      color: var(--cyan);
      font-size: .78rem;
      letter-spacing: .18em;
      text-transform: uppercase;
    }}

    h1 {{
      max-width: 900px;
      margin: 0;
      font: 500 clamp(2.4rem, 7vw, 6.4rem)/.94 Georgia, serif;
      letter-spacing: -.055em;
    }}

    .intro {{
      max-width: 760px;
      margin: 28px 0 0;
      color: var(--muted);
      line-height: 1.75;
    }}

    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 32px;
    }}

    button {{
      appearance: none;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 9px 14px;
      color: var(--muted);
      background: rgba(13, 19, 28, .8);
      font: inherit;
      font-size: .76rem;
      cursor: pointer;
    }}

    button[aria-pressed="true"] {{
      color: var(--background);
      background: var(--cyan);
      border-color: var(--cyan);
    }}

    .count {{
      margin: 28px 0 18px;
      color: var(--muted);
      font-size: .78rem;
    }}

    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 22px;
      padding-bottom: 40px;
    }}

    figure {{
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
      background: var(--panel);
    }}

    figure a {{ display: block; }}

    figure img {{
      display: block;
      width: 100%;
      aspect-ratio: 16 / 10;
      object-fit: cover;
    }}

    figcaption {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: start;
      padding: 14px 16px 16px;
    }}

    h2 {{
      margin: 0 0 6px;
      font-size: 1rem;
      font-weight: 600;
    }}

    .description {{
      margin: 0;
      color: var(--muted);
      font-size: .82rem;
      line-height: 1.5;
    }}

    .links {{
      margin: 8px 0 0;
      padding: 0;
      list-style: none;
      font-size: .72rem;
    }}

    .links li {{ margin: 2px 0; }}
    .links a {{ color: var(--cyan); }}

    .tag {{
      color: var(--amber);
      font-size: .68rem;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}

    dialog {{
      width: min(96vw, 1400px);
      max-width: none;
      padding: 0;
      border: 1px solid #405469;
      border-radius: 4px;
      color: var(--text);
      background: #030507;
    }}

    dialog::backdrop {{ background: rgba(0, 0, 0, .88); }}

    dialog img {{
      display: block;
      width: 100%;
      max-height: 88vh;
      object-fit: contain;
    }}

    .close {{
      position: fixed;
      top: 16px;
      right: 16px;
      z-index: 2;
      color: white;
      background: rgba(0, 0, 0, .78);
    }}

    footer {{
      padding: 40px 0 60px;
      color: var(--muted);
      font-size: .72rem;
    }}

    @media (max-width: 760px) {{
      header {{ padding-top: 42px; }}
      .gallery {{ grid-template-columns: 1fr; }}
      figcaption {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <p class="eyebrow">Flyxion &middot; Procedural research objects</p>
    <h1>Headless Blender Experiments</h1>
    <p class="intro">{count} reproducible scenes translating structural questions into inspectable geometry. Select a repository to isolate its experiments, or open any render at full resolution.</p>
    <nav class="controls" aria-label="Filter experiments">
{filter_buttons}
    </nav>
  </header>

  <main>
    <p class="count" aria-live="polite"><span id="visible-count">{count}</span> experiments visible</p>
    <section class="gallery" aria-label="Experiment renders">
{figures}
    </section>
  </main>

  <footer>Generated headlessly in Blender &middot; deterministic source scenes retained alongside each render &middot; page generated by scripts/build-gallery.py, do not edit directly.</footer>

  <dialog id="viewer" aria-label="Full-resolution render">
    <button class="close" type="button" aria-label="Close full-resolution view">Close</button>
    <img src="" alt="">
  </dialog>

  <script>
    const figures = [...document.querySelectorAll('figure[data-repository]')];
    const filters = [...document.querySelectorAll('[data-filter]')];
    const count = document.querySelector('#visible-count');
    const dialog = document.querySelector('#viewer');
    const dialogImage = dialog.querySelector('img');

    for (const button of filters) {{
      button.addEventListener('click', () => {{
        const filter = button.dataset.filter;
        for (const control of filters) control.setAttribute('aria-pressed', String(control === button));
        for (const figure of figures) figure.hidden = filter !== 'all' && figure.dataset.repository !== filter;
        count.textContent = String(figures.filter(figure => !figure.hidden).length);
      }});
    }}

    for (const link of document.querySelectorAll('figure a.full')) {{
      link.addEventListener('click', event => {{
        if (!dialog.showModal) return;
        event.preventDefault();
        const thumbnail = link.querySelector('img');
        dialogImage.src = link.href;
        dialogImage.alt = thumbnail.alt;
        dialog.showModal();
      }});
    }}

    dialog.querySelector('.close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {{ if (event.target === dialog) dialog.close(); }});
  </script>
</body>
</html>
"""


def render_figure(entry: dict, has_thumb: bool) -> str:
    eid = entry["id"]
    thumb_src = f"output/thumbs/{eid}.jpg" if has_thumb else f"output/{eid}.png"
    links = [
        ("script", f"experiments/{eid}.py"),
        ("metadata", "metadata.json"),
        (".blend", f"output/{eid}.blend"),
    ]
    for rel_link in entry.get("related", []):
        links.append((html.escape(rel_link["label"]), "../" + rel_link["path"]))
    links_html = "".join(
        f'<li><a href="{html.escape(href, quote=True)}">{label}</a></li>'
        for label, href in links
    )
    return f"""      <figure data-repository="{entry['filter']}">
        <a class="full" href="output/{eid}.png"><img src="{thumb_src}" alt="{html.escape(entry['alt'])}" loading="lazy"></a>
        <figcaption>
          <div>
            <h2>{html.escape(entry['title'])}</h2>
            <p class="description">{html.escape(entry['description'])}</p>
            <p class="description"><em>{html.escape(entry['question'])}</em></p>
          </div>
          <div>
            <span class="tag">{html.escape(entry['repository'])}</span>
            <ul class="links">{links_html}</ul>
          </div>
        </figcaption>
      </figure>"""


def render_page(entries: list[dict], has_thumb: dict[str, bool]) -> str:
    buttons = []
    for filt, label in FILTERS_ORDER:
        pressed = "true" if filt == "all" else "false"
        buttons.append(f'      <button type="button" data-filter="{filt}" aria-pressed="{pressed}">{html.escape(label)}</button>')
    figures = "\n".join(render_figure(e, has_thumb.get(e["id"], False)) for e in entries)
    return PAGE_TEMPLATE.format(
        count=len(entries),
        filter_buttons="\n".join(buttons),
        figures=figures,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate consistency without writing files")
    args = parser.parse_args()

    entries, problems = load_metadata()
    if problems:
        for problem in problems:
            print(f"gallery {'check' if args.check else 'build'}: {problem}", file=sys.stderr)
        return 1
    scripts = discover_scripts()
    pngs, blends = discover_outputs()

    problems += cross_check(entries, scripts, pngs, blends)
    problems += ensure_thumbnails(entries, pngs, check_only=args.check)

    if args.check:
        rendered = render_page(entries, {e["id"]: True for e in entries})
        current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
        if rendered != current:
            problems.append("experiments/index.html is stale; run python3 scripts/build-gallery.py")
        if problems:
            for problem in problems:
                print(f"gallery check: {problem}", file=sys.stderr)
            return 1
        print(f"gallery check: {len(entries)} experiments consistent")
        return 0

    if problems:
        for problem in problems:
            print(f"gallery build: {problem}", file=sys.stderr)
        return 1

    INDEX_PATH.write_text(render_page(entries, {e["id"]: True for e in entries}), encoding="utf-8")
    print(f"experiments/index.html regenerated with {len(entries)} experiments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
