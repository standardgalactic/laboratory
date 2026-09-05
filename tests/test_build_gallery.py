"""Unit tests for gallery validation that do not require Blender."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build-gallery.py"
SPEC = importlib.util.spec_from_file_location("build_gallery", SCRIPT)
assert SPEC and SPEC.loader
gallery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gallery)


def entry(**changes):
    value = {
        "id": "sample_scene",
        "repository": "calculus",
        "filter": "calculus",
        "title": "Sample",
        "alt": "Sample render",
        "description": "A sample scene.",
        "question": "Does it work?",
        "related": [],
    }
    value.update(changes)
    return value


class MetadataValidationTests(unittest.TestCase):
    def test_accepts_complete_entry(self):
        self.assertEqual(gallery.validate_metadata([entry()]), [])

    def test_rejects_duplicate_ids(self):
        problems = gallery.validate_metadata([entry(), entry(title="Duplicate")])
        self.assertIn("duplicate metadata entry id: 'sample_scene'", problems)

    def test_rejects_unknown_filter(self):
        problems = gallery.validate_metadata([entry(filter="unlisted")])
        self.assertIn("metadata entry 'sample_scene' uses unknown filter: 'unlisted'", problems)

    def test_rejects_path_escape(self):
        related = [{"label": "Outside", "path": "../outside.tex"}]
        problems = gallery.validate_metadata([entry(related=related)])
        self.assertTrue(any("must stay inside the repository" in problem for problem in problems))

    def test_render_includes_provenance_links(self):
        rendered = gallery.render_figure(entry(), has_thumb=True)
        self.assertIn('href="experiments/sample_scene.py"', rendered)
        self.assertIn('href="metadata.json"', rendered)
        self.assertIn('href="output/sample_scene.blend"', rendered)


@unittest.skipIf(gallery.Image is None, "Pillow is required for thumbnail checks")
class ThumbnailValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.previous = gallery.THUMBS_DIR
        gallery.THUMBS_DIR = Path(self.temporary.name)

    def tearDown(self):
        gallery.THUMBS_DIR = self.previous
        self.temporary.cleanup()

    def test_rejects_orphaned_thumbnail(self):
        gallery.Image.new("RGB", (32, 32)).save(gallery.THUMBS_DIR / "orphan.jpg")
        problems = gallery.ensure_thumbnails([], {}, check_only=True)
        self.assertIn(
            "orphaned thumbnail with no metadata entry: experiments/output/thumbs/orphan.jpg",
            problems,
        )

    def test_rejects_corrupt_thumbnail(self):
        (gallery.THUMBS_DIR / "sample_scene.jpg").write_bytes(b"not an image")
        problems = gallery.ensure_thumbnails(
            [entry()], {"sample_scene": Path("sample_scene.png")}, check_only=True
        )
        self.assertTrue(any("invalid thumbnail for 'sample_scene'" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
