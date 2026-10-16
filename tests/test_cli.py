import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "my-project"
        self.root.mkdir()
        (self.root / "code.scm").write_text("(define (hello name) (display name))\n")

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "codemark", *map(str, args)],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_and_doctor_do_not_require_gui_or_gpg(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mark", result.stdout)
        doctor = self.run_cli("doctor", "--json")
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        self.assertEqual(json.loads(doctor.stdout)["network_required"], False)

    def test_preview_apply_verify_tamper_and_unmark_cli(self):
        result = self.run_cli("mark", self.root, "--owner", "Security Ops", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["applied"])
        self.assertFalse((self.root / ".codemark").exists())
        result = self.run_cli(
            "mark", self.root, "--owner", "Security Ops", "--apply", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cli("verify", self.root, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        path = self.root / "code.scm"
        path.write_bytes(path.read_bytes() + b'\n(display "changed")')
        result = self.run_cli("verify", self.root, "--json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("code.scm", json.loads(result.stdout)["changed"])
        result = self.run_cli("unmark", self.root, "--apply", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(b"CodeMark v1", path.read_bytes())
        self.assertIn(b"changed", path.read_bytes())

    def test_missing_owner_and_invalid_root_return_two_without_traceback(self):
        for args in [("mark", self.root), ("verify", self.root / "missing")]:
            result = self.run_cli(*args, "--json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", json.loads(result.stderr))
            self.assertNotIn("Traceback", result.stderr)

    def test_json_report_is_saved_and_existing_files_are_preserved(self):
        destination = Path(self.temp.name) / "report.json"
        result = self.run_cli(
            "mark",
            self.root,
            "--owner",
            "Security Ops",
            "--json",
            "--output",
            destination,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(destination.read_text())["files"], 1)
        destination.write_text("do not overwrite")
        result = self.run_cli(
            "mark", self.root, "--owner", "Security Ops", "--output", destination
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(destination.read_text(), "do not overwrite")

    def test_compare_exit_code_and_report(self):
        marking = self.run_cli("mark", self.root, "--owner", "Security Ops", "--apply")
        self.assertEqual(marking.returncode, 0, marking.stderr)
        suspect = Path(self.temp.name) / "suspect"
        suspect.mkdir()
        (suspect / "copied.scm").write_text("(define (hello name) (display name))\n")
        result = self.run_cli("compare", self.root, suspect, "--json")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["matches"][0]["method"], "exact-content"
        )

    def test_signature_flags_must_be_used_together(self):
        self.run_cli("mark", self.root, "--owner", "Security Ops", "--apply")
        result = self.run_cli("verify", self.root, "--require-signature", "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))


if __name__ == "__main__":
    unittest.main()
