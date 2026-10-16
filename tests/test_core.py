"""Regression cases exercise real files, not the marker's implementation."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codemark import core

LONG_SOURCE = """def calculate_total(products, tax):
    total = 0
    for product in products:
        if product > 10:
            total += product * 2
        else:
            total += product + 3
    if total > 100:
        total -= 7
    result = total * (1 + tax)
    return round(result, 2)

def report(products):
    subtotal = calculate_total(products, 0.05)
    return {"subtotal": subtotal, "currency": "BRL"}
"""


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(core, "marking core is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)
        return path

    def mark(self, **options):
        return core.mark(self.root, owner="Security Ops", apply=True, **options)

    def test_preview_writes_nothing(self):
        path = self.put("hello.py", "print(42)")
        report = core.mark(self.root, owner="Security Ops")
        self.assertEqual(report["planned"], 1)
        self.assertEqual(path.read_bytes(), b"print(42)")
        self.assertFalse((self.root / ".codemark").exists())

    def test_mark_verify_unmark_is_byte_exact_across_languages(self):
        fixtures = {
            "main.py": b"#!/usr/bin/env python3\r\n# coding: utf-8\r\nprint(42)",
            "module.scm": b"(define (square x) (* x x))\n",
            "main.js": b'#!/usr/bin/env node\n"use strict";\nconsole.log(42);',
            "main.c": b"/* SPDX-License-Identifier: GPL-3.0-or-later */\nint main(void){return 0;}",
            "style.css": b"body { color: cyan; }\r\n",
            "app.xml": b'\xef\xbb\xbf<?xml version="1.0"?>\n<app/>',
            "module.rs": b'fn main() { println!("hello"); }\n',
            "script.fish": b"#!/usr/bin/env fish\necho hello\n",
        }
        for name, content in fixtures.items():
            self.put(name, content)
        self.mark()
        self.assertTrue(core.verify(self.root)["ok"])
        for name in fixtures:
            self.assertIn(b"CodeMark v1", (self.root / name).read_bytes())
        core.unmark(self.root, apply=True)
        for name, original in fixtures.items():
            self.assertEqual((self.root / name).read_bytes(), original, name)

    def test_python_shebang_encoding_docstring_and_future_import_survive(self):
        script = self.put(
            "program.py",
            '#!/usr/bin/env python3\n# coding: utf-8\n"""Module."""\nfrom __future__ import annotations\nprint("olá")\n',
        )
        self.mark()
        self.assertTrue(
            script.read_bytes().startswith(b"#!/usr/bin/env python3\n# coding: utf-8\n")
        )
        result = subprocess.run(
            [sys.executable, str(script)], capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "olá")

    def test_mark_is_idempotent_including_manifest(self):
        path = self.put("code.py", LONG_SOURCE)
        self.mark()
        before = path.read_bytes()
        manifest = (self.root / ".codemark/manifest.json").read_bytes()
        result = core.mark(self.root, apply=True)
        self.assertEqual(result["changed"], 0)
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(manifest, (self.root / ".codemark/manifest.json").read_bytes())

    def test_licenses_dependencies_and_generated_files_are_not_marked(self):
        self.put("main.scm", '(display "hi")')
        names = [
            "COPYING",
            "LICENSE",
            "node_modules/lib/index.js",
            "vendor/other.py",
            "dist/main.js",
            ".git/hooks/pre-commit",
            "a.min.js",
            "data.json",
        ]
        for name in names:
            self.put(name, "third-party material")
        self.mark()
        for name in names:
            self.assertEqual(
                (self.root / name).read_text(), "third-party material", name
            )

    def test_unmark_preserves_edits_and_lookalike_comment(self):
        original = "# CodeMark v1 do not remove my ordinary comment\nprint(1)\n"
        path = self.put("code.py", original)
        self.mark()
        path.write_bytes(path.read_bytes().replace(b"print(1)", b"print(2)"))
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_text(), original.replace("print(1)", "print(2)"))

    def test_changed_missing_and_untracked_files_are_reported(self):
        self.put("changed.py", "print(1)\n")
        missing = self.put("gone.scm", "(display 1)")
        self.mark()
        path = self.root / "changed.py"
        path.write_bytes(path.read_bytes().replace(b"print(1)", b"print(2)"))
        missing.unlink()
        self.put("new.js", "alert(1)")
        result = core.verify(self.root)
        self.assertFalse(result["ok"])
        self.assertEqual(set(result["changed"]), {"changed.py"})
        self.assertEqual(result["missing"], ["gone.scm"])
        self.assertEqual(result["untracked"], ["new.js"])

    def test_unmark_preview_does_not_write(self):
        path = self.put("main.scm", "(display 1)")
        self.mark()
        content = path.read_bytes()
        result = core.unmark(self.root)
        self.assertEqual(result["planned"], 1)
        self.assertEqual(path.read_bytes(), content)

    def test_owner_cannot_escape_block_or_html_comment(self):
        path = self.put("code.css", "body{}")
        self.put("index.html", "<p>hi</p>")
        core.mark(self.root, owner="A */ --> <tag>\n B", apply=True)
        self.assertEqual(path.read_bytes().count(b"*/"), 1)
        self.assertTrue(core.verify(self.root)["ok"])
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_text(), "body{}")

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits")
    def test_permissions_survive(self):
        path = self.put("run.sh", "#!/bin/sh\necho hello\n")
        path.chmod(0o750)
        self.mark()
        self.assertEqual(path.stat().st_mode & 0o777, 0o750)

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symlinks")
    def test_symlink_is_rejected_without_reading_target(self):
        outside = Path(self.temp.name) / "outside.py"
        outside.write_text("do not touch")
        try:
            (self.root / "link.py").symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation is unavailable on this host")
        with self.assertRaises(core.CodeMarkError):
            self.mark()
        self.assertEqual(outside.read_text(), "do not touch")

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symlinks")
    def test_symlink_metadata_directory_is_rejected(self):
        target = Path(self.temp.name) / "metadata"
        target.mkdir()
        try:
            (self.root / ".codemark").symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation is unavailable on this host")
        self.put("main.py", "pass")
        with self.assertRaises(core.CodeMarkError):
            self.mark()
        self.assertEqual(list(target.iterdir()), [])

    def test_overlarge_source_does_not_silently_disappear(self):
        self.put("large.py", b"x" * (2 * 1024 * 1024 + 1))
        with self.assertRaises(core.CodeMarkError):
            self.mark()

    def test_file_count_limit_fails_before_writes(self):
        one = self.put("one.py", "pass")
        self.put("two.py", "pass")
        with patch.object(core, "MAX_FILES", 1), self.assertRaises(core.CodeMarkError):
            self.mark()
        self.assertEqual(one.read_text(), "pass")

    def test_unsupported_encoding_is_reported(self):
        self.put("good.py", "pass")
        bad = self.put("legacy.py", b'# coding: latin-1\nprint("\xe9")')
        result = self.mark()
        self.assertTrue(any(item["path"] == "legacy.py" for item in result["skipped"]))
        self.assertNotIn(b"CodeMark", bad.read_bytes())

    def test_malformed_manifest_fails_cleanly(self):
        self.put("main.py", "pass")
        self.mark()
        manifest = self.root / ".codemark/manifest.json"
        for content in [
            "{}",
            "[1]",
            '{"format": 1, "files": {"../escape.py": {}}}',
            "bad json",
        ]:
            manifest.write_text(content)
            with self.subTest(content=content), self.assertRaises(core.CodeMarkError):
                core.verify(self.root)

    def test_malformed_config_fails_cleanly(self):
        self.put("main.py", "pass")
        self.mark()
        (self.root / ".codemark/project.json").write_text('{"project_id": "invalid"}')
        with self.assertRaises(core.CodeMarkError):
            core.mark(self.root, apply=True)

    def test_transaction_rolls_back_after_write_failure(self):
        one = self.put("one.py", "print(1)")
        two = self.put("two.py", "print(2)")
        real = core.atomic_write

        def fail_second(path, data, mode=None):
            if Path(path).name == "two.py" and b"CodeMark v1" in data:
                raise OSError("controlled disk failure")
            return real(path, data, mode)

        with (
            patch.object(core, "atomic_write", side_effect=fail_second),
            self.assertRaises(core.CodeMarkError),
        ):
            self.mark()
        self.assertEqual(one.read_bytes(), b"print(1)")
        self.assertEqual(two.read_bytes(), b"print(2)")
        self.assertFalse((self.root / ".codemark/manifest.json").exists())

    def test_active_lock_prevents_changes(self):
        self.put("main.py", "pass")
        self.mark()
        (self.root / ".codemark/lock").write_text("1234")
        with self.assertRaises(core.CodeMarkError):
            core.mark(self.root, apply=True)

    def test_compare_detects_copy_without_marker_and_with_renamed_variables(self):
        self.put("original.py", LONG_SOURCE)
        self.mark()
        suspect = Path(self.temp.name) / "suspect"
        suspect.mkdir()
        renamed = (
            LONG_SOURCE.replace("products", "items")
            .replace("product", "entry")
            .replace("total", "sum_value")
            .replace("tax", "rate")
            .replace("calculate_", "compute_")
        )
        (suspect / "renamed.py").write_text("# someone removed the mark\n" + renamed)
        result = core.compare(self.root, suspect)
        matches = result["matches"]
        self.assertTrue(
            any(
                m["candidate"] == "renamed.py" and m["reference"] == "original.py"
                for m in matches
            ),
            result,
        )

    def test_compare_exact_small_file_and_visible_mark(self):
        self.put("tiny.scm", '(display "hello")\n')
        self.mark()
        suspect = Path(self.temp.name) / "suspect"
        suspect.mkdir()
        (suspect / "copy.scm").write_bytes((self.root / "tiny.scm").read_bytes())
        (suspect / "without.scm").write_bytes(b'(display "hello")\n')
        reasons = {m["method"] for m in core.compare(self.root, suspect)["matches"]}
        self.assertIn("watermark", reasons)
        self.assertIn("exact-content", reasons)

    def test_short_unrelated_files_are_not_similar_just_due_to_identifiers(self):
        self.put("a.py", "a = b + c\n")
        self.mark()
        suspect = Path(self.temp.name) / "suspect"
        suspect.mkdir()
        (suspect / "other.py").write_text("x = y + z\n")
        self.assertEqual(core.compare(self.root, suspect)["matches"], [])

    def test_compare_rejects_invalid_threshold(self):
        self.put("a.py", "pass")
        self.mark()
        with self.assertRaises(core.CodeMarkError):
            core.compare(self.root, self.root, float("nan"))

    def test_plain_manifest_does_not_claim_authenticated_authorship(self):
        self.put("a.py", "pass")
        self.mark()
        report = core.verify(self.root)
        self.assertFalse(report["authenticated"])


if __name__ == "__main__":
    unittest.main()
