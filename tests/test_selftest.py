import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codemark import selftest

REPO = Path(__file__).resolve().parents[1]


class SelfTestTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(selftest, "portable self-test is not implemented")

    def test_actual_selftest_checks_core_and_available_signer(self):
        report = selftest.run()
        self.assertTrue(report["ok"], report)
        passed = {
            check["name"] for check in report["checks"] if check["status"] == "pass"
        }
        self.assertTrue(
            {
                "mark",
                "verify",
                "tamper",
                "compare",
                "unmark",
                "python-runtime",
                "whole-file-integrity",
            }
            <= passed,
            report,
        )
        if shutil.which("ssh-keygen"):
            self.assertIn("openssh-signature", passed)
        from codemark.pq_signing import capabilities

        if capabilities()["available"]:
            self.assertIn("hybrid-authentication", passed)
        self.assertNotIn("production_ready", report)

    def test_optional_tool_absence_is_explicit_without_hiding_core_results(self):
        with patch.object(selftest.shutil, "which", return_value=None):
            report = selftest.run()
        self.assertTrue(report["ok"], report)
        skipped = {
            check["name"] for check in report["checks"] if check["status"] == "skip"
        }
        self.assertTrue(
            {
                "openssh-signature",
                "javascript-runtime",
                "guile-runtime",
                "hybrid-authentication",
            }
            <= skipped,
            report,
        )

    def test_unavailable_python_execution_is_reported_as_failure(self):
        with patch.object(selftest.sys, "executable", "/nonexistent/codemark-python"):
            report = selftest.run()
        self.assertFalse(report["ok"])
        failed = {
            check["name"] for check in report["checks"] if check["status"] == "fail"
        }
        self.assertIn("python-runtime", failed)

    def test_temporary_sources_and_ephemeral_keys_are_cleaned(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(selftest.tempfile, "tempdir", directory):
                self.assertTrue(selftest.run()["ok"])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_cli_selftest_runs_with_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(REPO / "codemark.py"), "self-test", "--json"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
