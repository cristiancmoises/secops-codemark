"""Independent review regressions: preservation, bounds and concurrency."""

import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from codemark import core, gui

REPO = Path(__file__).resolve().parents[1]


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()

    def put(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_same_line_xml_header_round_trip_and_idempotence(self):
        original = b'\xef\xbb\xbf<?xml version="1.0"?><app/>'
        path = self.put("one.xml", original)
        core.mark(self.root, owner="Test", apply=True)
        once = path.read_bytes()
        self.assertTrue(core.verify(self.root)["ok"])
        core.mark(self.root, apply=True)
        self.assertEqual(path.read_bytes(), once)
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_bytes(), original)

    def test_unterminated_encoding_only_header_is_skipped_without_mutation(self):
        original = b"# coding: utf-8"
        path = self.put("coding.py", original)
        self.put("real.py", b"pass\n")
        report = core.mark(self.root, owner="Test", apply=True)
        self.assertEqual(path.read_bytes(), original)
        self.assertTrue(any(item["path"] == "coding.py" for item in report["skipped"]))
        self.assertTrue(core.verify(self.root)["ok"])

    def test_complete_own_marker_inside_multiline_string_is_preserved(self):
        path = self.put("app.py", b"print(1)\n")
        core.mark(self.root, owner="Test", apply=True)
        header = path.read_bytes().splitlines(keepends=True)[0]
        documentation = b'\ndocumentation = """\n' + header + b'"""\n'
        path.write_bytes(path.read_bytes() + documentation)
        core.mark(self.root, apply=True)
        self.assertIn(documentation, path.read_bytes())
        self.assertTrue(core.verify(self.root)["ok"])
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_bytes(), b"print(1)\n" + documentation)

    def test_encoding_lookalike_inside_docstring_keeps_runtime_value(self):
        original = b'"""\n# coding: utf-8\n"""\nprint(__doc__, end="")\n'
        path = self.put("docstring.py", original)
        core.mark(self.root, owner="Test", apply=True)
        result = subprocess.run(
            [sys.executable, "-I", str(path)],
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"\n# coding: utf-8\n")
        self.assertTrue(core.verify(self.root)["ok"])
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_bytes(), original)

    def test_encoding_lookalike_inside_css_comment_keeps_comment_balanced(self):
        original = (
            b"/*\n# coding: utf-8\noriginal license comment */\nbody{color:cyan}\n"
        )
        path = self.put("comment.css", original)
        core.mark(self.root, owner="Test", apply=True)
        self.assertTrue(path.read_bytes().endswith(original))
        self.assertTrue(core.verify(self.root)["ok"])
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_bytes(), original)

    def test_emacs_ruby_and_css_prologues_remain_first(self):
        fixtures = {
            "closure.el": b";;; -*- lexical-binding: t; -*-\n(defun make-counter () (let ((n 0)) (lambda () (setq n (1+ n)))))\n",
            "frozen.rb": b'#!/usr/bin/env ruby\n# frozen_string_literal: true\nputs "hello"\n',
            "charset.css": b'@charset "UTF-8";body{color:cyan}',
        }
        for name, data in fixtures.items():
            self.put(name, data)
        core.mark(self.root, owner="Test", apply=True)
        self.assertTrue(
            (self.root / "closure.el")
            .read_bytes()
            .startswith(b";;; -*- lexical-binding: t; -*-\n")
        )
        self.assertTrue(
            (self.root / "frozen.rb")
            .read_bytes()
            .startswith(b"#!/usr/bin/env ruby\n# frozen_string_literal: true\n")
        )
        self.assertTrue(
            (self.root / "charset.css").read_bytes().startswith(b'@charset "UTF-8";')
        )
        self.assertTrue(core.verify(self.root)["ok"])
        core.unmark(self.root, apply=True)
        for name, data in fixtures.items():
            self.assertEqual((self.root / name).read_bytes(), data)

    def test_maximum_size_source_remains_readable_after_marking(self):
        original = b"x" * (2 * 1024 * 1024)
        path = self.put("boundary.py", original)
        core.mark(self.root, owner="Test", apply=True)
        self.assertTrue(core.verify(self.root)["ok"])
        core.unmark(self.root, apply=True)
        self.assertEqual(path.read_bytes(), original)

    def test_aggregate_source_limit_accounts_for_watermark_overhead(self):
        self.put("one.py", b"pass")
        self.put("two.py", b"pass")
        with patch.object(core, "MAX_TOTAL_BYTES", 8):
            core.mark(self.root, owner="Test", apply=True)
            self.assertTrue(core.verify(self.root)["ok"])
            core.unmark(self.root, apply=True)

    def test_generated_manifest_limit_is_checked_before_source_writes(self):
        path = self.put("app.py", b"pass")
        with (
            patch.object(core, "MAX_METADATA_BYTES", 150),
            self.assertRaises(core.CodeMarkError),
        ):
            core.mark(self.root, owner="Test", apply=True)
        self.assertEqual(path.read_bytes(), b"pass")
        self.assertFalse((self.root / ".codemark/manifest.json").exists())

    def test_full_5000_record_manifest_can_be_loaded(self):
        self.put("app.py", b"pass")
        core.mark(self.root, owner="Test", apply=True)
        path = self.root / ".codemark/manifest.json"
        manifest = json.loads(path.read_bytes())
        record = next(iter(manifest["files"].values()))
        record["sketch"] = [format(i, "016x") for i in range(256)]
        manifest["files"] = {f"module_{i:04d}.py": record for i in range(5000)}
        path.write_bytes(core.json_bytes(manifest))
        self.assertEqual(len(core.read_manifest(self.root)["files"]), 5000)

    def test_lock_precedes_configuration_snapshot(self):
        self.put("app.py", b"pass")
        real_lock = core.project_lock
        entered = False

        @contextmanager
        def interleaved(root):
            nonlocal entered
            if not entered:
                entered = True
                core.mark(root, owner="Other owner", apply=True)
            with real_lock(root):
                yield

        with (
            patch.object(core, "project_lock", interleaved),
            self.assertRaises(core.CodeMarkError),
        ):
            core.mark(self.root, owner="First owner", apply=True)
        self.assertEqual(core.load_config(self.root)["owner"], "Other owner")

    def test_gui_owner_selection_rejects_symlink_metadata_parent(self):
        self.assertTrue(
            hasattr(gui, "load_owner"), "safe GUI selection is not implemented"
        )
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        config = {
            "format": 1,
            "project_id": "12345678-1234-5678-1234-567812345678",
            "owner": "Outside",
            "project": "Outside",
        }
        (outside / "project.json").write_bytes(core.json_bytes(config))
        try:
            (self.root / ".codemark").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable on this host")
        with self.assertRaises(core.CodeMarkError):
            gui.load_owner(self.root)

    def test_gui_worker_finishes_transaction_before_process_exit(self):
        self.assertTrue(
            hasattr(gui, "start_worker"), "safe GUI worker lifecycle is not implemented"
        )
        self.put("one.py", b"pass")
        self.put("two.py", b"pass")
        script = """import queue, sys, time
from pathlib import Path
from codemark import core, gui
original = core.atomic_write
def slow_write(path, data, mode=None):
    result = original(path, data, mode)
    time.sleep(0.02)
    return result
core.atomic_write = slow_write
gui.start_worker(lambda: core.mark(Path(sys.argv[1]), owner="Worker", apply=True), queue.Queue())
"""
        result = subprocess.run(
            [sys.executable, "-c", script, str(self.root)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(core.verify(self.root)["ok"])
        self.assertFalse((self.root / ".codemark/lock").exists())


if __name__ == "__main__":
    unittest.main()
