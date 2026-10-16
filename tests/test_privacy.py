"""Native hybrid encrypted bundles preserve every project byte safely."""

import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from codemark import cli, privacy
from codemark.core import CodeMarkError
from codemark.pq_signing import fingerprint


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.zupt = shutil.which("zupt") or ""
        if not cls.zupt:
            raise unittest.SkipTest("native Zupt is required")
        cls.zupt = str(Path(cls.zupt).resolve())
        cls.keys = tempfile.TemporaryDirectory(prefix="bundle-native-keys-")
        cls.keydir = Path(cls.keys.name)
        cls.env = {
            "PATH": str(Path(cls.zupt).parent),
            "HOME": str(cls.keydir),
            "LC_ALL": "C",
        }
        for name in ("recipient", "wrong"):
            cls.native("keygen", "-o", str(cls.keydir / (name + ".key")))
            cls.native(
                "keygen",
                "--pub",
                "-k",
                str(cls.keydir / (name + ".key")),
                "-o",
                str(cls.keydir / (name + ".pub")),
            )
        cls.public = cls.keydir / "recipient.pub"
        cls.pin = fingerprint(cls.public.read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    @classmethod
    def native(cls, *args, success=True):
        result = subprocess.run(
            [cls.zupt, *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env=cls.env,
            timeout=45,
            check=False,
        )
        if success and result.returncode:
            raise AssertionError("native Zupt qualification failed")
        return result

    def setUp(self):
        self.assertIsNotNone(privacy, "private bundle module is not implemented")
        self.temp = tempfile.TemporaryDirectory(prefix="bundle-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "project"
        self.root.mkdir()
        self.output = self.home / "project.zupt"
        self.fixtures = {
            "securityopsctl": b"#!/bin/sh\necho command\n",
            "settings.json": b'{"private": true}\n',
            "docs/guide.md": "Documentação privada\n".encode(),
            "release.iso": b"\x00\xffISO" * 1000,
            ".git/config": b"[core]\nrepositoryformatversion = 0\n",
            ".codemark/integrity.json": b'{"private": "state"}\n',
            ".hidden": b"hidden regular file\n",
        }
        for name, data in self.fixtures.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def bundle(self, **kwargs):
        return privacy.bundle(self.root, self.output, self.public, self.pin, **kwargs)

    def assert_no_temporary_output(self):
        self.assertEqual(set(self.home.iterdir()), {self.root})

    def test_preview_has_no_writes_and_includes_vcs_and_state(self):
        before = {str(p): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        with patch(
            "tempfile.mkdtemp",
            side_effect=AssertionError("preview wrote temporary data"),
        ):
            report = self.bundle()
        self.assertFalse(report["applied"])
        self.assertEqual(report["action"], "bundle")
        self.assertEqual(report["archive"], str(self.output))
        self.assertIsNone(report["archive_info"])
        self.assertEqual(report["files"], len(self.fixtures))
        self.assertEqual(report["bytes"], sum(map(len, self.fixtures.values())))
        self.assertTrue(report["scope"]["vcs_included"])
        self.assertTrue(report["scope"]["codemark_state_included"])
        self.assertEqual(
            before,
            {str(p): p.read_bytes() for p in self.home.rglob("*") if p.is_file()},
        )

    def test_real_encrypted_roundtrip_contains_every_regular_file(self):
        report = self.bundle(apply=True)
        archive = self.output.read_bytes()
        self.assertTrue(report["applied"])
        self.assertTrue(report["encrypted"])
        self.assertEqual(report["recipient_fingerprint"], self.pin)
        self.assertEqual(
            report["archive_info"]["sha256"], hashlib.sha256(archive).hexdigest()
        )
        self.assertEqual(
            report["archive_info"]["sha512"], hashlib.sha512(archive).hexdigest()
        )
        self.assertEqual(report["archive_info"]["size"], len(archive))
        self.assertEqual(report["backend"]["encryption_type"], 2)
        self.assertEqual(report["backend"]["algorithms"], ["ML-KEM-768", "X25519"])
        self.assertFalse(report["decryption_verified"])
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        self.native(
            "test", "--pq", str(self.keydir / "recipient.key"), str(self.output)
        )
        extracted = self.home / "restored"
        self.native(
            "extract",
            "--pq",
            str(self.keydir / "recipient.key"),
            "-o",
            str(extracted),
            str(self.output),
        )
        actual = {
            str(p.relative_to(extracted / self.root.name)): p.read_bytes()
            for p in (extracted / self.root.name).rglob("*")
            if p.is_file()
        }
        self.assertEqual(actual, self.fixtures)
        for data in self.fixtures.values():
            self.assertNotIn(data, archive)

    def test_wrong_private_key_and_ciphertext_tamper_fail_native_validation(self):
        self.bundle(apply=True)
        self.assertNotEqual(
            self.native(
                "test",
                "--pq",
                str(self.keydir / "wrong.key"),
                str(self.output),
                success=False,
            ).returncode,
            0,
        )
        data = bytearray(self.output.read_bytes())
        data[-40] ^= 1
        self.output.write_bytes(data)
        self.assertNotEqual(
            self.native(
                "test",
                "--pq",
                str(self.keydir / "recipient.key"),
                str(self.output),
                success=False,
            ).returncode,
            0,
        )

    def test_recipient_pin_is_required_and_checked_before_compression(self):
        for pin in ("", "SHA256:" + "A" * 43, self.pin + "=", None):
            with self.subTest(pin=pin), self.assertRaises(CodeMarkError):
                privacy.bundle(self.root, self.output, self.public, pin, apply=True)
        self.assert_no_temporary_output()

    def test_public_key_is_external_regular_exact_native_public_format(self):
        for data in (
            b"invalid",
            self.public.read_bytes() + b"extra",
            (self.keydir / "recipient.key").read_bytes(),
        ):
            bad = self.home / "bad.pub"
            bad.write_bytes(data)
            with self.assertRaises(CodeMarkError):
                privacy.bundle(
                    self.root, self.output, bad, fingerprint(data), apply=True
                )
            bad.unlink()
        local = self.root / "recipient.pub"
        local.write_bytes(self.public.read_bytes())
        with self.assertRaises(CodeMarkError):
            privacy.bundle(self.root, self.output, local, self.pin, apply=True)
        local.unlink()
        self.assert_no_temporary_output()

    def test_output_must_be_new_external_zupt_archive(self):
        for output in (
            self.root / "inside.zupt",
            self.home / "bundle.zip",
            self.root,
            self.home / "missing" / "bundle.zupt",
        ):
            with self.subTest(output=output), self.assertRaises(CodeMarkError):
                privacy.bundle(self.root, output, self.public, self.pin, apply=True)
        self.output.write_bytes(b"preserve existing output")
        with self.assertRaises(CodeMarkError):
            self.bundle(apply=True)
        self.assertEqual(self.output.read_bytes(), b"preserve existing output")

    @unittest.skipUnless(os.name == "posix", "requires POSIX symbolic links")
    def test_symbolic_links_anywhere_and_special_files_are_rejected(self):
        for kind in ("file", "directory", "key", "output", "root", "fifo"):
            link = self.root / "unsafe"
            if kind == "key":
                link = self.home / "key.pub"
                link.symlink_to(self.public)
                args = (self.root, self.output, link, self.pin)
            elif kind == "output":
                link = self.output
                link.symlink_to(self.home / "missing")
                args = (self.root, link, self.public, self.pin)
            elif kind == "root":
                link = self.home / "root-link"
                link.symlink_to(self.root, target_is_directory=True)
                args = (link, self.output, self.public, self.pin)
            else:
                args = (self.root, self.output, self.public, self.pin)
                if kind == "fifo":
                    os.mkfifo(link)
                else:
                    link.symlink_to(
                        self.root
                        if kind == "directory"
                        else self.root / "settings.json",
                        target_is_directory=kind == "directory",
                    )
            with self.subTest(kind=kind), self.assertRaises(CodeMarkError):
                privacy.bundle(*args, apply=True)
            link.unlink()
        self.assert_no_temporary_output()

    def test_before_commit_failure_rolls_back_ciphertext_only(self):
        def reject(_report):
            raise CodeMarkError("qualification rollback")

        with self.assertRaisesRegex(CodeMarkError, "qualification rollback"):
            self.bundle(apply=True, before_commit=reject)
        self.assert_no_temporary_output()
        for name, data in self.fixtures.items():
            self.assertEqual((self.root / name).read_bytes(), data)

    def test_source_changes_and_added_files_before_publish_are_rejected(self):
        for name in ("settings.json", "new-file"):

            def mutate(_report, name=name):
                (self.root / name).write_bytes(b"changed during bundle")

            with self.subTest(name=name), self.assertRaises(CodeMarkError):
                self.bundle(apply=True, before_commit=mutate)
            self.assert_no_temporary_output()

    def test_concurrent_output_creation_is_never_overwritten_or_removed(self):
        def collide(_report):
            self.output.write_bytes(b"concurrent owner")

        with self.assertRaises(CodeMarkError):
            self.bundle(apply=True, before_commit=collide)
        self.assertEqual(self.output.read_bytes(), b"concurrent owner")
        self.assertEqual(set(self.home.iterdir()), {self.root, self.output})

    def test_source_mutation_during_native_compression_is_rejected(self):
        native_run = subprocess.run

        def racing_run(args, **kwargs):
            result = native_run(args, **kwargs)
            if "compress" in args:
                (self.root / "settings.json").write_bytes(
                    b"mutation during compression"
                )
            return result

        with (
            patch("subprocess.run", side_effect=racing_run),
            self.assertRaises(CodeMarkError),
        ):
            self.bundle(apply=True)
        self.assert_no_temporary_output()

    def test_native_failure_and_missing_backend_fail_closed(self):
        with patch("shutil.which", return_value=None), self.assertRaises(CodeMarkError):
            self.bundle(apply=True)
        self.assert_no_temporary_output()
        native_run = subprocess.run

        def failed_compression(args, **kwargs):
            if "compress" in args:
                return subprocess.CompletedProcess(
                    args, 1, b"sensitive native output", b"sensitive native error"
                )
            return native_run(args, **kwargs)

        with (
            patch("subprocess.run", side_effect=failed_compression),
            self.assertRaises(CodeMarkError) as caught,
        ):
            self.bundle(apply=True)
        self.assertNotIn("sensitive", str(caught.exception))
        self.assert_no_temporary_output()

    def test_native_failure_partial_ciphertext_is_removed(self):
        native_run = subprocess.run

        def partial_compression(args, **kwargs):
            if "compress" in args:
                Path(args[args.index("--pq") + 2]).write_bytes(b"partial ciphertext")
                return subprocess.CompletedProcess(args, 1)
            return native_run(args, **kwargs)

        with (
            patch("subprocess.run", side_effect=partial_compression),
            self.assertRaises(CodeMarkError),
        ):
            self.bundle(apply=True)
        self.assert_no_temporary_output()

    def test_timeout_discards_ciphertext_and_hides_native_details(self):
        native_run = subprocess.run

        def timed_out(args, **kwargs):
            if "compress" in args:
                raise subprocess.TimeoutExpired(
                    args, 300, output=b"private native details"
                )
            return native_run(args, **kwargs)

        with (
            patch("subprocess.run", side_effect=timed_out),
            self.assertRaises(CodeMarkError) as caught,
        ):
            self.bundle(apply=True)
        self.assertNotIn("private native", str(caught.exception))
        self.assert_no_temporary_output()

    def test_binary_header_downgrades_are_rejected_before_publish(self):
        native_run = subprocess.run
        for position, value in ((0, 0), (8, 0), (36, 0)):

            def damaged_compression(args, position=position, value=value, **kwargs):
                result = native_run(args, **kwargs)
                if "compress" in args:
                    path = Path(args[args.index("--pq") + 2])
                    blob = bytearray(path.read_bytes())
                    blob[position] = value
                    path.write_bytes(blob)
                return result

            with (
                self.subTest(position=position),
                patch("subprocess.run", side_effect=damaged_compression),
                self.assertRaises(CodeMarkError),
            ):
                self.bundle(apply=True)
            self.assert_no_temporary_output()

    def test_encryption_type_is_read_from_binary_block_not_version_words(self):
        native_run = subprocess.run

        def wrong_type(args, **kwargs):
            result = native_run(args, **kwargs)
            if "compress" in args:
                path = Path(args[args.index("--pq") + 2])
                blob = bytearray(path.read_bytes())
                offset = int.from_bytes(blob[36:44], "little") + 7
                for _ in range(2):
                    while blob[offset] & 128:
                        offset += 1
                    offset += 1
                blob[offset + 8] = 6  # PQ-only is not the selected hybrid mode.
                path.write_bytes(blob)
            return result

        with (
            patch("subprocess.run", side_effect=wrong_type),
            self.assertRaises(CodeMarkError),
        ):
            self.bundle(apply=True)
        self.assert_no_temporary_output()

    def test_ciphertext_replacement_before_publish_is_preserved_but_not_published(self):
        replacement = None

        def replace(_report):
            nonlocal replacement
            temporary = next(self.home.glob(".codemark-bundle-*"))
            replacement = temporary / "encrypted.zupt"
            replacement.rename(temporary / "original.zupt")
            replacement.write_bytes(b"unrelated replacement")

        with self.assertRaises(CodeMarkError):
            self.bundle(apply=True, before_commit=replace)
        self.assertFalse(self.output.exists())
        assert replacement is not None
        self.assertEqual(replacement.read_bytes(), b"unrelated replacement")

    def test_child_environment_does_not_inherit_ambient_credentials(self):
        native_run = subprocess.run
        observed = []

        def inspect_environment(args, **kwargs):
            observed.append(kwargs["env"])
            return native_run(args, **kwargs)

        with (
            patch.dict(
                os.environ,
                {
                    "AWS_SECRET_ACCESS_KEY": "ambient-test-secret",
                    "ZUPT_PASSWORD": "ambient-test-secret",
                    "OPENSSL_CONF": "/not-trusted",
                },
            ),
            patch("subprocess.run", side_effect=inspect_environment),
        ):
            self.bundle(apply=True)
        self.assertTrue(observed)
        for environment in observed:
            self.assertNotIn("ambient-test-secret", environment.values())
            self.assertNotIn("OPENSSL_CONF", environment)

    def test_bundle_streams_files_without_read_bytes_or_plaintext_copy(self):
        with patch.object(
            Path, "read_bytes", side_effect=AssertionError("unbounded file read")
        ):
            report = self.bundle(apply=True)
        self.assertTrue(report["applied"])
        self.assertEqual(set(self.home.iterdir()), {self.root, self.output})

    def test_before_commit_receives_prepared_report_before_atomic_publish(self):
        observed = []

        def inspect(report):
            self.assertTrue(report["applied"])
            self.assertEqual(report["archive"], str(self.output))
            self.assertEqual(len(report["archive_info"]["sha256"]), 64)
            self.assertFalse(self.output.exists())
            observed.append(report)

        report = self.bundle(apply=True, before_commit=inspect)
        self.assertEqual(observed, [report])
        self.assertTrue(self.output.exists())

    def cli_arguments(self, report_path):
        return [
            "bundle",
            str(self.root),
            "--recipient-key",
            str(self.public),
            "--recipient-fingerprint",
            self.pin,
            "--archive",
            str(self.output),
            "--apply",
            "--json",
            "--output",
            str(report_path),
        ]

    def test_cli_output_success_writes_matching_prepared_report(self):
        report_path = self.home / "bundle-report.json"
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = cli.main(self.cli_arguments(report_path))
        self.assertEqual(result, 0, stderr.getvalue())
        saved = json.loads(report_path.read_text())
        self.assertEqual(saved, json.loads(stdout.getvalue()))
        self.assertTrue(saved["applied"])
        self.assertTrue(self.output.exists())
        self.assertEqual(
            saved["archive_info"]["sha256"],
            hashlib.sha256(self.output.read_bytes()).hexdigest(),
        )

    def test_cli_report_flush_failure_prevents_archive_and_removes_partial_report(self):
        report_path = self.home / "bundle-report.json"
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch(
                "codemark.cli.finish_report",
                side_effect=OSError("qualification report failure"),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            result = cli.main(self.cli_arguments(report_path))
        self.assertEqual(result, 2)
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertFalse(report_path.exists())
        self.assert_no_temporary_output()

    def test_file_and_total_size_limits_are_checked_before_hashing(self):
        with (
            patch.object(privacy, "MAX_FILE_BYTES", 1, create=True),
            self.assertRaises(CodeMarkError),
        ):
            self.bundle()
        with (
            patch.object(privacy, "MAX_TOTAL_BYTES", 1, create=True),
            self.assertRaises(CodeMarkError),
        ):
            self.bundle()
        self.assert_no_temporary_output()

    def test_file_growth_is_rejected_instead_of_consuming_an_unbounded_stream(self):
        target = self.root / "settings.json"
        real_fdopen = os.fdopen

        class GrowingReader:
            def __init__(self, stream):
                self.stream = stream
                self.reads = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.stream.close()

            def fileno(self):
                return self.stream.fileno()

            def read(self, size):
                self.reads += 1
                if self.reads > 2:
                    raise AssertionError("reader consumed an unbounded growing file")
                return b"x" * (target.stat().st_size + 1)

        def growing_fdopen(descriptor, mode):
            return GrowingReader(real_fdopen(descriptor, mode))

        with (
            patch("os.fdopen", side_effect=growing_fdopen),
            self.assertRaises(CodeMarkError),
        ):
            privacy._read_regular(target)

    @unittest.skipUnless(hasattr(os, "O_NONBLOCK"), "requires nonblocking open")
    def test_reader_cannot_block_on_a_regular_file_replaced_with_a_fifo(self):
        import signal

        actual_open = os.open
        target = self.root / "settings.json"

        def racing_open(path, flags, *args, **kwargs):
            target.unlink()
            os.mkfifo(target)
            return actual_open(path, flags, *args, **kwargs)

        def deadline(_signum, _frame):
            raise AssertionError("regular-to-FIFO race blocked the reader")

        old = signal.signal(signal.SIGALRM, deadline)
        signal.setitimer(signal.ITIMER_REAL, 2)
        try:
            with (
                patch("os.open", side_effect=racing_open),
                self.assertRaises(CodeMarkError),
            ):
                privacy._read_regular(target)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)

    def test_changed_public_key_after_compression_is_rejected(self):
        key = self.home / "recipient.pub"
        key.write_bytes(self.public.read_bytes())

        def mutate(_report):
            key.write_bytes((self.keydir / "wrong.pub").read_bytes())

        with self.assertRaises(CodeMarkError):
            privacy.bundle(
                self.root, self.output, key, self.pin, apply=True, before_commit=mutate
            )
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
