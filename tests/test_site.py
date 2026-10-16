import importlib.util
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


class SiteBuildTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "codemark_site_builder", REPO / "scripts/build_site.py"
        )
        assert spec is not None and spec.loader is not None
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.base = Path(stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.root = self.base / "source"
        self.site = self.root / "website"
        stack.enter_context(patch.object(self.builder, "ROOT", self.root))
        stack.enter_context(patch.object(self.builder, "SITE", self.site))
        (self.site / "assets").mkdir(parents=True)
        (self.site / "data").mkdir()
        (self.site / "assets/styles.css").write_text("body { color: black; }\n")
        (self.site / "assets/favicon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"/>\n'
        )
        (self.root / "COPYING").write_text("Fixture license\n")
        for filename in ("SECURITY.md", "CONTRIBUTING.md"):
            (self.root / filename).write_text("# Fixture policy\n")
        for settings in self.builder.TEXT.values():
            docs = self.root / "docs" / settings["source_dir"]
            (docs / "wiki").mkdir(parents=True)
            for folder, names in (
                (docs, self.builder.DOCS),
                (docs / "wiki", self.builder.WIKI),
            ):
                for name in names:
                    (folder / (name + ".md")).write_text("# Fixture guide\n")
        self.data = {
            "version": "0.4.1",
            "date": "2026-10-16",
            "commit": "fixture",
            "site_url": "https://example.invalid",
            "status": "pending",
            "scope": "Private test fixture",
            "repositories": [],
            "checks": [],
            "metrics": [],
            "reports": [],
            "downloads": [],
        }

    def write_reports(self, *names):
        for number, name in enumerate(names):
            source = self.root / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                json.dumps({"report": number})
                if source.suffix == ".json"
                else f"# Fixture report {number}\n"
            )
            self.data["reports"].append(
                {
                    "path": name,
                    "title": f"Fixture report {number}",
                    "date": "2026-10-16",
                    "scope": "Private test fixture",
                    "status": "current",
                }
            )
        (self.site / "data/release.json").write_text(json.dumps(self.data))

    def output_contents(self, output):
        if not output.exists():
            return None
        return {
            path.relative_to(output).as_posix(): (
                path.read_bytes() if path.is_file() else None
            )
            for path in output.rglob("*")
        }

    def assert_rejected_without_writing(self, message):
        for existing in (False, True):
            with self.subTest(existing_output=existing):
                output = self.base / ("existing" if existing else "new")
                if existing:
                    for name in (
                        "assets/styles.css",
                        "data/release.json",
                        "reports/existing.txt",
                        "index.html",
                    ):
                        path = output / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text("Preserve existing output\n")
                before = self.output_contents(output)
                with self.assertRaisesRegex(ValueError, message):
                    self.builder.build(output)
                self.assertEqual(self.output_contents(output), before)

    def test_duplicate_report_stems_are_rejected_before_output_changes(self):
        self.write_reports("docs/reports/a/same.md", "docs/reports/b/same.json")
        self.assert_rejected_without_writing(
            "Published report route stems must be unique"
        )

    def test_duplicate_report_filenames_are_rejected_before_output_changes(self):
        self.write_reports("docs/reports/a/same.md", "docs/reports/b/same.md")
        self.assert_rejected_without_writing(
            "Published report filenames must be unique"
        )

    def test_distinct_reports_keep_raw_files_and_bilingual_readable_routes(self):
        names = ("docs/reports/a/first.md", "docs/reports/b/second.json")
        self.write_reports(*names)
        output = self.base / "output"
        count = self.builder.build(output)
        self.assertEqual(self.builder.check_site(output), count)
        for name in names:
            source = self.root / name
            self.assertEqual(
                (output / "reports" / source.name).read_bytes(), source.read_bytes()
            )
            for language in ("en", "pt-br"):
                self.assertTrue(
                    (
                        output / language / "reports" / source.stem / "index.html"
                    ).is_file()
                )


if __name__ == "__main__":
    unittest.main()
