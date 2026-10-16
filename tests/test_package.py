import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codemark import __version__

REPO = Path(__file__).resolve().parents[1]


class PortablePackageTests(unittest.TestCase):
    def builder(self):
        spec = importlib.util.spec_from_file_location(
            "codemark_builder", REPO / "scripts/build.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_symlink_is_rejected_before_a_portable_artifact_is_written(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            (root / "codemark").mkdir(parents=True)
            (root / "COPYING").write_text("test license")
            private = base / "private-data.py"
            private.write_text("never publish this")
            try:
                (root / "codemark" / "leak.py").symlink_to(private)
            except OSError:
                self.skipTest("Creating symlinks is unavailable on this platform")
            output = base / "output"
            with patch.object(builder, "ROOT", root), self.assertRaises(RuntimeError):
                builder.build(output)
            self.assertFalse((output / "codemark.pyz").exists())

    def test_selected_source_directory_symlinks_are_rejected(self):
        builder = self.builder()
        for name in ("codemark", "docs"):
            with (
                self.subTest(directory=name),
                tempfile.TemporaryDirectory() as directory,
            ):
                base = Path(directory)
                root = base / "source"
                root.mkdir()
                (root / "COPYING").write_text("test license")
                private = base / "private"
                private.mkdir()
                (private / "private.py").write_text("never publish this")
                try:
                    (root / name).symlink_to(private, target_is_directory=True)
                except (OSError, NotImplementedError):
                    self.skipTest("Creating symlinks is unavailable on this platform")
                output = base / "output"
                with (
                    patch.object(builder, "ROOT", root),
                    self.assertRaises(RuntimeError),
                ):
                    builder.build(output)
                self.assertFalse((output / "codemark.pyz").exists())

    def test_existing_generated_files_are_rejected_before_any_artifact_write(self):
        builder = self.builder()
        names = ("codemark.pyz", "SHA256SUMS", f"secops-codemark-{__version__}.zupt")
        for name in names:
            with (
                self.subTest(artifact=name),
                tempfile.TemporaryDirectory() as directory,
            ):
                base = Path(directory)
                root = base / "source"
                (root / "codemark").mkdir(parents=True)
                (root / "COPYING").write_text("test license")
                output = base / "output"
                output.mkdir()
                existing = output / name
                existing.write_bytes(b"existing release artifact")
                with (
                    patch.object(builder, "ROOT", root),
                    patch.object(builder.shutil, "which", return_value=None),
                    self.assertRaisesRegex(RuntimeError, "fresh --output"),
                ):
                    builder.build(output, archive=name.endswith(".zupt"))
                self.assertEqual(existing.read_bytes(), b"existing release artifact")
                self.assertEqual({path.name for path in output.iterdir()}, {name})

    def test_output_artifact_symlinks_cannot_overwrite_external_files(self):
        builder = self.builder()
        names = ("codemark.pyz", "SHA256SUMS", f"secops-codemark-{__version__}.zupt")
        for name in names:
            with (
                self.subTest(artifact=name),
                tempfile.TemporaryDirectory() as directory,
            ):
                base = Path(directory)
                root = base / "source"
                (root / "codemark").mkdir(parents=True)
                (root / "COPYING").write_text("test license")
                private = base / "private-data"
                private.write_bytes(b"never overwrite this")
                private.chmod(0o600)
                original_mode = stat.S_IMODE(private.stat().st_mode)
                output = base / "output"
                output.mkdir()
                try:
                    (output / name).symlink_to(private)
                except (OSError, NotImplementedError):
                    self.skipTest("Creating symlinks is unavailable on this platform")
                with (
                    patch.object(builder, "ROOT", root),
                    patch.object(builder.shutil, "which", return_value=None),
                    self.assertRaisesRegex(RuntimeError, "fresh --output"),
                ):
                    builder.build(output, archive=name.endswith(".zupt"))
                self.assertEqual(private.read_bytes(), b"never overwrite this")
                if os.name == "posix":
                    self.assertEqual(
                        stat.S_IMODE(private.stat().st_mode), original_mode
                    )
                self.assertEqual({path.name for path in output.iterdir()}, {name})

    def test_dangling_output_symlink_is_rejected_without_creating_its_target(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            (root / "codemark").mkdir(parents=True)
            (root / "COPYING").write_text("test license")
            output = base / "output"
            output.mkdir()
            missing = base / "missing-private-target"
            try:
                (output / "codemark.pyz").symlink_to(missing)
            except (OSError, NotImplementedError):
                self.skipTest("Creating symlinks is unavailable on this platform")
            with patch.object(builder, "ROOT", root), self.assertRaises(RuntimeError):
                builder.build(output)
            self.assertFalse(missing.exists())

    def test_missing_archiver_is_rejected_before_output_directory_creation(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            (root / "codemark").mkdir(parents=True)
            (root / "COPYING").write_text("test license")
            output = base / "output"
            with (
                patch.object(builder, "ROOT", root),
                patch.object(builder.shutil, "which", return_value=None),
                self.assertRaisesRegex(RuntimeError, "ZUPT is required"),
            ):
                builder.build(output, archive=True)
            self.assertFalse(output.exists())

    def test_source_staging_excludes_local_execution_instructions(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            (root / "codemark").mkdir(parents=True)
            (root / "COPYING").write_text("test license")
            for name in (
                "PROMPT-GOD-TIER.md",
                "AGENTS.md",
                "docs/superpowers/plan.md",
                "docs/AGENTS.md",
                "website/public/stale.html",
                "docs/.codex/skills/fixture/SKILL.md",
                "scripts/.claude/local.md",
                "examples/.agents/local.md",
                "docs/private-task-prompt.md",
                "docs/release-plan.md",
                "docs/agent-instructions.txt",
                "docs/agent.md",
                "docs/SKILL.md",
            ):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("private instructions")
            (root / "docs" / "public.md").write_text("public documentation")
            with patch.object(builder, "ROOT", root):
                package = builder.build(base / "output")
            names = {
                path.relative_to(package).as_posix()
                for path in package.rglob("*")
                if path.is_file()
            }
            self.assertIn("docs/public.md", names)
            self.assertFalse(
                any(
                    "private instructions" in path.read_text()
                    for path in package.rglob("*.md")
                )
            )
            self.assertFalse(
                any(
                    "PROMPT" in name
                    or "AGENTS.md" in name
                    or "superpowers" in name
                    or name.startswith("website/public/")
                    for name in names
                )
            )

    @unittest.skipUnless(os.name == "posix", "requires POSIX executable mode bits")
    def test_source_staging_preserves_executable_intent_without_suffix_guesses(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            (root / "codemark").mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "COPYING").write_text("test license")
            executable = root / "codemark" / "cli.py"
            executable.write_bytes(b"print('executable source')\n")
            executable.chmod(0o741)
            plain = root / "docs" / "plain.sh"
            plain.write_bytes(b"plain non-executable source\n")
            plain.chmod(0o640)
            output = base / "output"
            with patch.object(builder, "ROOT", root):
                staged = builder.build(output)
            self.assertEqual(
                (staged / "codemark/cli.py").read_bytes(), executable.read_bytes()
            )
            self.assertEqual(
                (staged / "docs/plain.sh").read_bytes(), plain.read_bytes()
            )
            for path, expected in (
                (staged / "codemark/cli.py", 0o755),
                (staged / "docs/plain.sh", 0o644),
                (staged / "codemark.pyz", 0o755),
                (staged / "SHA256SUMS", 0o644),
                (output / "codemark.pyz", 0o755),
                (output / "SHA256SUMS", 0o644),
            ):
                with self.subTest(path=path):
                    self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected)

    def test_reproducible_portable_package_runs_outside_repository(self):
        builder = REPO / "scripts/build.py"
        self.assertTrue(builder.is_file(), "portable builder is not implemented")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            first, second = base / "first", base / "second"
            for output in (first, second):
                result = subprocess.run(
                    [sys.executable, str(builder), "--output", str(output)],
                    cwd=base,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (first / "codemark.pyz").read_bytes(),
                (second / "codemark.pyz").read_bytes(),
            )
            package = first / f"secops-codemark-{__version__}"
            self.assertTrue(package.is_dir(), "source staging is not implemented")
            self.assertTrue((package / "COPYING").is_file())
            self.assertFalse(list(first.glob("*.zip")), "source releases must use ZUPT")
            self.assertFalse(list(package.rglob("PROMPT*.md")))
            self.assertFalse((package / "docs/superpowers").exists())
            self.assertFalse((package / ".git").exists())
            for line in (package / "SHA256SUMS").read_text().splitlines():
                expected, name = line.split("  ", 1)
                data = (package / name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
                self.assertEqual(data, (second / package.name / name).read_bytes())
            executable = first / "codemark.pyz"
            result = subprocess.run(
                [sys.executable, "-I", str(executable), "doctor", "--json"],
                cwd=base,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["version"], __version__)
            result = subprocess.run(
                [sys.executable, "-I", str(executable), "self-test", "--json"],
                cwd=base,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])
            project = base / "project"
            project.mkdir()
            script = project / "hello.py"
            original = b'print("portable")\n'
            script.write_bytes(original)
            for args in [
                ("mark", project, "--owner", "Package Test", "--apply"),
                ("verify", project),
                ("unmark", project, "--apply"),
            ]:
                result = subprocess.run(
                    [sys.executable, "-I", str(executable), *map(str, args)],
                    cwd=base,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(script.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
