"""CLI contracts for complete file coverage and explicit authentication."""

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class FullCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        (self.root / "securityopsctl").write_bytes(b"#!/bin/sh\nexit 0\n")
        (self.root / "config.json").write_bytes(b"{}\n")
        (self.root / "disk.iso").write_bytes(bytes(2 * 1024 * 1024 + 1))

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "codemark", *map(str, args)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_snapshot_preview_apply_and_verify_cover_every_file(self):
        preview = self.cli("snapshot", self.root, "--json")
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)["files"], 3)
        self.assertFalse((self.root / ".codemark").exists())
        applied = self.cli("snapshot", self.root, "--apply", "--json")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        verified = self.cli("verify", self.root, "--json")
        self.assertEqual(verified.returncode, 0, verified.stderr)
        report = json.loads(verified.stdout)
        self.assertEqual(report["coverage_mode"], "all-regular-files")
        self.assertFalse(report["authenticated"])
        (self.root / "config.json").write_bytes(b"changed")
        verified = self.cli("verify", self.root, "--json")
        self.assertEqual(verified.returncode, 1, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["changed"], ["config.json"])

    def test_audit_requires_both_independent_pins(self):
        self.cli("snapshot", self.root, "--apply")
        result = self.cli("audit", self.root, "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))
        self.assertNotIn("Traceback", result.stderr)

    def test_text_report_handles_full_snapshot_and_modes(self):
        self.cli("snapshot", self.root, "--apply")
        result = self.cli("verify", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3", result.stdout)
        self.assertIn("all-regular-files", result.stdout)

    def test_legacy_mark_report_names_its_limited_scope(self):
        (self.root / "main.py").write_text("print('ready')\n")
        result = self.cli("mark", self.root, "--owner", "Security Ops", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["coverage_mode"], "source-comments-only"
        )

    def test_failed_report_does_not_write_snapshot(self):
        result = self.cli(
            "snapshot",
            self.root,
            "--apply",
            "--output",
            Path(self.temp.name) / "missing/report.txt",
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / ".codemark/integrity.json").exists())

    @unittest.skipIf(os.name == "nt", "POSIX mode bits are not Windows ACLs")
    def test_report_is_private_even_with_permissive_process_umask(self):
        destination = Path(self.temp.name) / "report.json"
        previous = os.umask(0)
        try:
            result = self.cli("snapshot", self.root, "--output", destination, "--json")
        finally:
            os.umask(previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
