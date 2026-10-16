"""Whole-file inventories include opaque bytes and fail closed on coverage gaps."""

import hashlib
import json
import os
import stat
import tempfile
import tracemalloc
import unittest
from pathlib import Path
from unittest.mock import patch

from codemark import core, integrity


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            integrity, "whole-file integrity inventory is not implemented"
        )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def snapshot(self):
        return integrity.snapshot(self.root, apply=True)

    def manifest(self):
        return self.root / ".codemark" / integrity.MANIFEST_FILE

    def test_all_file_types_are_hashed_without_modifying_bytes(self):
        fixtures = {
            "securityopsctl": b"#!/bin/sh\necho command\n",
            "config.json": b'{"enabled":true}\n',
            "docs/guide.md": "Documentação\n".encode(),
            ".hidden": b"hidden\x00\xff",
            "system.bin": bytes(range(256)),
            "release.iso": b"\x00\xffISO" * (600 * 1024),
            "vendor/data.txt": b"third party coverage is explicit\n",
        }
        for name, data in fixtures.items():
            self.put(name, data)
        report = self.snapshot()
        manifest = integrity.read_snapshot(self.root)
        self.assertEqual(set(manifest["files"]), set(fixtures))
        self.assertEqual(report["coverage_mode"], "all-regular-files")
        self.assertEqual(report["files"], 7)
        self.assertEqual(report["total_bytes"], sum(map(len, fixtures.values())))
        for name, data in fixtures.items():
            self.assertEqual((self.root / name).read_bytes(), data)
            self.assertEqual(
                manifest["files"][name]["sha256"], hashlib.sha256(data).hexdigest()
            )
            self.assertEqual(
                manifest["files"][name]["sha512"], hashlib.sha512(data).hexdigest()
            )
        self.assertTrue(integrity.verify_snapshot(self.root)["ok"])

    def test_preview_creates_no_metadata(self):
        path = self.put("data.json", b"{}")
        report = integrity.snapshot(self.root)
        self.assertFalse(report["applied"])
        self.assertEqual(path.read_bytes(), b"{}")
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_changed_missing_and_untracked_include_unmarkable_files(self):
        changed = self.put("data.json", b"{}")
        missing = self.put("manual.md", b"docs")
        self.snapshot()
        changed.write_bytes(b'{"changed":true}')
        missing.unlink()
        self.put("new.iso", b"\x00binary")
        report = integrity.verify_snapshot(self.root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["changed"], ["data.json"])
        self.assertEqual(report["missing"], ["manual.md"])
        self.assertEqual(report["untracked"], ["new.iso"])
        self.assertFalse(report["authenticated"])

    @unittest.skipUnless(os.name == "posix", "requires POSIX mode bits")
    def test_mode_changes_are_recorded_and_detected(self):
        path = self.put("securityopsctl", b"command")
        path.chmod(0o750)
        self.snapshot()
        self.assertEqual(
            integrity.read_snapshot(self.root)["files"]["securityopsctl"]["mode"], 0o750
        )
        path.chmod(0o640)
        report = integrity.verify_snapshot(self.root)
        self.assertFalse(report["ok"])
        self.assertEqual(report["mode_changed"], ["securityopsctl"])
        self.assertEqual(report["changed"], [])

    def test_only_actual_vcs_and_metadata_directories_are_excluded(self):
        self.put(".git/config", b"private VCS state")
        self.put("nested/.hg/store", b"history")
        self.put("node_modules/package.json", b"{}")
        self.put(".cache/result", b"cached")
        self.put(".svn", b"regular file with excluded directory name")
        report = self.snapshot()
        excluded = {item["path"] for item in report["excluded"]}
        self.assertEqual(excluded, {".git", "nested/.hg", ".codemark"})
        self.assertEqual(
            set(integrity.read_snapshot(self.root)["files"]),
            {"node_modules/package.json", ".cache/result", ".svn"},
        )
        self.assertTrue(all(item["reason"] for item in report["excluded"]))

    def test_project_identity_survives_repeated_snapshot(self):
        self.put("data.json", b"{}")
        first = self.snapshot()
        self.assertEqual(self.snapshot()["project_id"], first["project_id"])

    def test_legacy_identity_and_metadata_are_preserved(self):
        self.put("main.py", b"pass\n")
        legacy = core.mark(self.root, owner="Test", apply=True)
        old = {
            name: (self.root / ".codemark" / name).read_bytes()
            for name in ("manifest.json", "project.json")
        }
        self.assertEqual(self.snapshot()["project_id"], legacy["project_id"])
        for name, data in old.items():
            self.assertEqual((self.root / ".codemark" / name).read_bytes(), data)

    def test_callback_failure_preserves_existing_snapshot_and_sources(self):
        source = self.put("data.json", b"{}")
        self.snapshot()
        previous = self.manifest().read_bytes()
        source.write_bytes(b"changed")

        def fail(report):
            self.assertTrue(report["applied"])
            raise OSError("cannot complete report")

        with self.assertRaises(OSError):
            integrity.snapshot(self.root, apply=True, before_commit=fail)
        self.assertEqual(self.manifest().read_bytes(), previous)
        self.assertEqual(source.read_bytes(), b"changed")
        self.assertFalse((self.root / ".codemark/lock").exists())

    def test_workload_limits_fail_before_metadata_write(self):
        self.put("one.json", b"1234")
        self.put("two.json", b"5678")
        for name, value in (
            ("MAX_FILE_BYTES", 3),
            ("MAX_TOTAL_BYTES", 7),
            ("MAX_FILES", 1),
            ("MAX_ENTRIES", 1),
            ("MAX_METADATA_BYTES", 100),
        ):
            with (
                self.subTest(limit=name),
                patch.object(integrity, name, value),
                self.assertRaises(core.CodeMarkError),
            ):
                self.snapshot()
            self.assertFalse(self.manifest().exists())
        self.assertEqual((self.root / "one.json").read_bytes(), b"1234")

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symlinks")
    def test_symlink_files_directories_and_excluded_names_fail_closed(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "secret").write_bytes(b"outside bytes")
        for name, target in (
            ("linked", outside / "secret"),
            ("directory", outside),
            (".git", outside),
        ):
            link = self.root / name
            try:
                link.symlink_to(target, target_is_directory=target.is_dir())
            except OSError:
                self.skipTest("symlink creation unavailable")
            try:
                with self.assertRaises(core.CodeMarkError):
                    self.snapshot()
            finally:
                link.unlink()
        self.assertFalse(self.manifest().exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires FIFO support")
    def test_special_file_is_rejected_without_blocking(self):
        os.mkfifo(self.root / "pipe")
        with self.assertRaises(core.CodeMarkError):
            self.snapshot()
        self.assertFalse(self.manifest().exists())

    @unittest.skipUnless(os.name == "posix", "requires POSIX byte filenames")
    def test_non_utf8_filename_is_rejected(self):
        path = os.fsencode(self.root) + b"/invalid-\xff"
        descriptor = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(descriptor)
        with self.assertRaises(core.CodeMarkError):
            self.snapshot()

    @unittest.skipUnless(os.name == "posix", "requires a colon in a filename")
    def test_unsafe_relative_filename_is_rejected(self):
        self.put("unsafe:name", b"bytes")
        with self.assertRaises(core.CodeMarkError):
            self.snapshot()

    @unittest.skipUnless(os.name == "posix", "requires POSIX permissions")
    def test_unreadable_file_is_a_failure(self):
        path = self.put("private.json", b"unreadable")
        path.chmod(0)
        self.addCleanup(path.chmod, 0o600)
        if os.access(path, os.R_OK):
            self.skipTest("test user can override file permissions")
        with self.assertRaises(core.CodeMarkError):
            self.snapshot()

    def test_change_during_hashing_is_rejected(self):
        path = self.put("data.bin", b"first")
        real_read = os.read
        changed = False

        def read_and_change(descriptor, count):
            nonlocal changed
            data = real_read(descriptor, count)
            if data and not changed and stat.S_ISREG(os.fstat(descriptor).st_mode):
                changed = True
                path.write_bytes(b"different bytes")
            return data

        with (
            patch.object(integrity.os, "read", side_effect=read_and_change),
            self.assertRaises(core.CodeMarkError),
        ):
            self.snapshot()
        self.assertFalse(self.manifest().exists())

    def test_large_binary_hashing_uses_bounded_memory(self):
        path = self.root / "large.iso"
        with path.open("wb") as stream:
            for _ in range(16):
                stream.write(b"\xff" * (1024 * 1024))
        tracemalloc.start()
        try:
            report = integrity.snapshot(self.root)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(report["total_bytes"], 16 * 1024 * 1024)
        self.assertLess(peak, 8 * 1024 * 1024)

    def test_raw_manifest_is_frozen_and_hashes_cover_exact_bytes(self):
        self.put("data.json", b"{}")
        report = self.snapshot()
        raw = self.manifest().read_bytes()
        self.assertEqual(report["manifest_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(report["manifest_sha512"], hashlib.sha512(raw).hexdigest())
        self.manifest().write_bytes(b"invalid")
        self.assertTrue(integrity.verify_snapshot(self.root, raw)["ok"])

    def test_strict_json_rejects_duplicate_keys_nan_and_unknown_fields(self):
        self.put("data.json", b"{}")
        self.snapshot()
        raw = self.manifest().read_bytes()
        cases = [
            b'{"format":"x","format":"y"}',
            raw.replace(b'"file_count": 1', b'"file_count": NaN'),
            raw[:-2] + b', "extra": 1}\n',
        ]
        for malformed in cases:
            with (
                self.subTest(raw=malformed[:60]),
                self.assertRaises(core.CodeMarkError),
            ):
                integrity.read_snapshot(self.root, malformed)

    def test_strict_schema_rejects_forged_counts_paths_and_types(self):
        self.put("data.json", b"{}")
        self.snapshot()
        original = json.loads(self.manifest().read_bytes())
        mutations = [
            lambda d: d.update(file_count=True),
            lambda d: d.update(total_bytes=999),
            lambda d: d.update(algorithms=["sha256"]),
            lambda d: d.update(created_at="yesterday"),
            lambda d: d.update(project_id="not-a-uuid"),
            lambda d: d.update(tool_version="x" * 100),
            lambda d: d["files"].update({"../escape": d["files"].pop("data.json")}),
            lambda d: d["files"]["data.json"].update(size=True),
            lambda d: d["files"]["data.json"].update(mode=0o10000),
            lambda d: d["files"]["data.json"].update(sha512="a" * 127),
            lambda d: d["files"]["data.json"].update(extra="unknown"),
            lambda d: d["excluded"].append({"path": "../bad", "reason": "invalid"}),
        ]
        for mutate in mutations:
            data = json.loads(json.dumps(original))
            mutate(data)
            with self.subTest(mutation=mutate), self.assertRaises(core.CodeMarkError):
                integrity.read_snapshot(self.root, json.dumps(data).encode())

    def test_verification_never_accepts_failed_current_file_as_covered(self):
        path = self.put("data.json", b"{}")
        self.snapshot()
        path.unlink()
        if hasattr(os, "mkfifo"):
            os.mkfifo(path)
            with self.assertRaises(core.CodeMarkError):
                integrity.verify_snapshot(self.root)

    class ReparseStat:
        st_file_attributes = 0x400

        def __init__(self, original):
            self.original = original

        def __getattr__(self, name):
            return getattr(self.original, name)

    def test_inventory_rejects_reparse_attributes_on_files_and_directories(self):
        original_scandir = os.scandir
        reparse_stat = self.ReparseStat

        class Entry:
            def __init__(self, original):
                self.original = original
                self.name = original.name
                self.path = original.path

            def stat(self, **kwargs):
                value = self.original.stat(**kwargs)
                return reparse_stat(value) if self.name == "reparse" else value

        class Iterator:
            def __init__(self, path):
                self.original = original_scandir(path)

            def __enter__(self):
                return (Entry(entry) for entry in self.original)

            def __exit__(self, *args):
                self.original.close()

        for directory in (False, True):
            path = self.root / "reparse"
            if directory:
                path.mkdir()
                (path / "external-content").write_bytes(b"must not be followed")
            else:
                path.write_bytes(b"must not be followed")
            with (
                self.subTest(directory=directory),
                patch("os.scandir", side_effect=Iterator),
                self.assertRaises(core.CodeMarkError),
            ):
                integrity.snapshot(self.root)
            if directory:
                (path / "external-content").unlink()
                path.rmdir()
            else:
                path.unlink()

    def test_checked_root_rejects_reparse_ancestors_and_metadata(self):
        metadata = self.root / ".codemark"
        metadata.mkdir()
        record = metadata / "integrity.json"
        record.write_bytes(b"{}")
        original_lstat = Path.lstat
        for target in (self.root, self.root.parent, metadata, record):

            def substituted(path, target=target):
                value = original_lstat(path)
                return self.ReparseStat(value) if path == target else value

            with (
                self.subTest(target=target),
                patch.object(Path, "lstat", substituted),
                self.assertRaises(core.CodeMarkError),
            ):
                core.checked_root(self.root)

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "mkfifo"), "requires POSIX FIFO"
    )
    def test_metadata_read_rejects_regular_to_fifo_race_without_blocking(self):
        import signal

        target = self.put("metadata.json", b"{}")
        original_open = os.open

        def raced_open(path, flags, *args, **kwargs):
            target.unlink()
            os.mkfifo(target)
            return original_open(path, flags, *args, **kwargs)

        def deadline(_signum, _frame):
            raise AssertionError("metadata FIFO race blocked the reader")

        old = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, 2)
        try:
            with (
                patch("os.open", side_effect=raced_open),
                self.assertRaises(core.CodeMarkError),
            ):
                core.read_regular(target, 1024)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)


if __name__ == "__main__":
    unittest.main()
