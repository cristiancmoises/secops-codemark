"""Production integration regressions: failed reports and bounded workloads."""

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from codemark import core
from codemark.cli import main

REPO = Path(__file__).resolve().parents[1]


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = self.root / "app.py"
        self.source.write_bytes(b"print(1)\n")

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "codemark", *map(str, args)],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_existing_report_prevents_all_project_mutations(self):
        destination = self.base / "report.json"
        destination.write_text("previous evidence")
        result = self.cli(
            "mark",
            self.root,
            "--owner",
            "Test",
            "--apply",
            "--output",
            destination,
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")
        self.assertFalse((self.root / ".codemark").exists())
        self.assertEqual(destination.read_text(), "previous evidence")

    def test_unwritable_report_prevents_all_project_mutations(self):
        result = self.cli(
            "mark",
            self.root,
            "--owner",
            "Test",
            "--apply",
            "--output",
            self.base / "missing/report.json",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")
        self.assertFalse((self.root / ".codemark").exists())

    def test_report_inside_project_is_rejected_before_writes(self):
        destination = self.root / "report.py"
        result = self.cli(
            "mark",
            self.root,
            "--owner",
            "Test",
            "--apply",
            "--output",
            destination,
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(destination.exists())
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")

    def test_failed_operation_cleans_reserved_report(self):
        destination = self.base / "new.json"
        result = self.cli("mark", self.root, "--output", destination, "--json")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(destination.exists())

    def test_successful_operation_saves_a_complete_external_report(self):
        destination = self.base / "new.json"
        result = self.cli(
            "mark",
            self.root,
            "--owner",
            "Test",
            "--apply",
            "--output",
            destination,
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(destination.read_bytes())["applied"])
        self.assertTrue(core.verify(self.root)["ok"])

    def test_project_write_failure_removes_finished_report_and_reverts_sources(self):
        destination = self.base / "new.json"
        original_write = core.atomic_write

        def fail_manifest(path, data, mode=None):
            if path.name == "manifest.json":
                # The report has finished before any transaction writes begin.
                self.assertTrue(json.loads(destination.read_bytes())["applied"])
                raise OSError("project filesystem full")
            return original_write(path, data, mode)

        with (
            patch.object(core, "atomic_write", side_effect=fail_manifest),
            redirect_stderr(io.StringIO()),
            redirect_stdout(io.StringIO()),
        ):
            code = main(
                [
                    "mark",
                    str(self.root),
                    "--owner",
                    "Test",
                    "--apply",
                    "--output",
                    str(destination),
                    "--json",
                ]
            )
        self.assertEqual(code, 2)
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")
        self.assertFalse((self.root / ".codemark/manifest.json").exists())
        self.assertFalse((self.root / ".codemark/project.json").exists())
        self.assertFalse(destination.exists())

    def limited_cli(self, *args):
        bootstrap = (
            "import resource, signal, sys; "
            "signal.signal(signal.SIGXFSZ, signal.SIG_IGN); "
            "resource.setrlimit(resource.RLIMIT_FSIZE, (2048, 2048)); "
            "from codemark.cli import main; sys.exit(main(sys.argv[1:]))"
        )
        return subprocess.run(
            [sys.executable, "-c", bootstrap, *map(str, args)],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )

    @unittest.skipUnless(
        sys.platform.startswith("linux"), "requires Linux file size limits"
    )
    def test_late_report_write_and_flush_failures_do_not_mark_sources(self):
        for count in (25, 60):
            with self.subTest(unsupported_files=count):
                root = self.base / str(count)
                root.mkdir()
                source = root / "app.py"
                source.write_bytes(b"print(1)\n")
                for n in range(count):
                    (root / f"data{n}.txt").write_text("unsupported")
                destination = self.base / f"mark-{count}.json"
                result = self.limited_cli(
                    "mark",
                    root,
                    "--owner",
                    "Test",
                    "--apply",
                    "--output",
                    destination,
                    "--json",
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("error", json.loads(result.stderr))
                self.assertEqual(source.read_bytes(), b"print(1)\n")
                self.assertFalse((root / ".codemark/manifest.json").exists())
                self.assertFalse((root / ".codemark/project.json").exists())
                self.assertFalse(destination.exists(), "truncated report retained")

    @unittest.skipUnless(
        sys.platform.startswith("linux"), "requires Linux file size limits"
    )
    def test_late_report_write_and_flush_failures_do_not_unmark_sources(self):
        for count in (25, 60):
            with self.subTest(unsupported_files=count):
                root = self.base / str(count)
                root.mkdir()
                source = root / "app.py"
                source.write_bytes(b"print(1)\n")
                for n in range(count):
                    (root / f"data{n}.txt").write_text("unsupported")
                core.mark(root, owner="Test", apply=True)
                previous = source.read_bytes()
                manifest = (root / ".codemark/manifest.json").read_bytes()
                destination = self.base / f"unmark-{count}.json"
                result = self.limited_cli(
                    "unmark", root, "--apply", "--output", destination, "--json"
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("error", json.loads(result.stderr))
                self.assertEqual(source.read_bytes(), previous)
                self.assertEqual(
                    (root / ".codemark/manifest.json").read_bytes(), manifest
                )
                self.assertTrue(core.verify(root)["ok"])
                self.assertFalse(destination.exists(), "truncated report retained")

    def test_comparison_refuses_excessive_match_results(self):
        self.assertTrue(
            hasattr(core, "MAX_MATCHES"), "comparison result budget is not implemented"
        )
        (self.root / "second.py").write_bytes(self.source.read_bytes())
        core.mark(self.root, owner="Test", apply=True)
        suspect = self.base / "suspect"
        suspect.mkdir()
        (suspect / "a.py").write_bytes(b"print(1)\n")
        (suspect / "b.py").write_bytes(b"print(1)\n")
        with (
            patch.object(core, "MAX_MATCHES", 3),
            self.assertRaises(core.CodeMarkError),
        ):
            core.compare(self.root, suspect)

    def test_entry_budget_is_enforced_for_unsupported_files(self):
        self.assertTrue(
            hasattr(core, "MAX_ENTRIES"),
            "directory enumeration budget is not implemented",
        )
        for n in range(5):
            (self.root / f"data{n}.json").write_text("{}")
        with (
            patch.object(core, "MAX_ENTRIES", 3),
            self.assertRaises(core.CodeMarkError),
        ):
            core.mark(self.root, owner="Test", apply=True)
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")

    def test_report_symlink_loop_fails_cleanly_before_mutation(self):
        loop = self.base / "loop"
        try:
            loop.symlink_to(loop, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable")
        result = self.cli(
            "mark",
            self.root,
            "--owner",
            "Test",
            "--apply",
            "--output",
            loop / "report.json",
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))
        self.assertEqual(self.source.read_bytes(), b"print(1)\n")


if __name__ == "__main__":
    unittest.main()
