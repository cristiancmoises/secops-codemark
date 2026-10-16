"""Whole-project authentication and atomic history regressions."""

import base64
import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codemark import attestations, cli, integrity, pq_signing
from codemark.core import CodeMarkError


class AttestationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pq_signing.capabilities()["available"]:
            raise unittest.SkipTest("OpenSSL ML-DSA-87 and Ed25519 are required")
        cls.keys = tempfile.TemporaryDirectory()
        cls.pq = Path(cls.keys.name) / "pq.pem"
        cls.ed = Path(cls.keys.name) / "ed.pem"
        executable = shutil.which("openssl")
        assert executable is not None
        for algorithm, path in [("ML-DSA-87", cls.pq), ("ED25519", cls.ed)]:
            subprocess.run(
                [executable, "genpkey", "-algorithm", algorithm, "-out", str(path)],
                check=True,
                capture_output=True,
            )

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "keys"):
            cls.keys.cleanup()

    def setUp(self):
        self.assertIsNotNone(attestations, "Whole-project authentication is missing")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        (self.root / "securityopsctl").write_bytes(b"#!/bin/sh\necho ready\n")
        (self.root / "settings.json").write_bytes(b'{"enabled":true}\n')
        integrity.snapshot(self.root, apply=True)

    def signed(self):
        report = attestations.sign_hybrid(self.root, self.pq, self.ed)
        records = attestations.read_history(self.root)
        pins = records[-1]["payload"]["signers"]
        return report, pins

    def test_authenticates_all_files_without_changing_them(self):
        original = (self.root / "settings.json").read_bytes()
        signed, pins = self.signed()
        result = attestations.verify_hybrid(
            self.root, pins["mldsa87"], pins["ed25519"], checkpoint=signed["checkpoint"]
        )
        self.assertTrue(result["ok"])
        self.assertTrue(result["authenticated"])
        self.assertTrue(result["rollback_protected"])
        self.assertEqual(result["coverage_mode"], "all-regular-files")
        self.assertEqual((self.root / "settings.json").read_bytes(), original)

    def test_authenticated_reference_detects_json_and_new_binary_changes(self):
        _, pins = self.signed()
        (self.root / "settings.json").write_text("{}")
        (self.root / "disk.iso").write_bytes(b"new binary")
        result = attestations.verify_hybrid(self.root, pins["mldsa87"], pins["ed25519"])
        self.assertTrue(result["authenticated"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["changed"], ["settings.json"])
        self.assertEqual(result["untracked"], ["disk.iso"])

    def test_unsigned_replacement_snapshot_is_rejected(self):
        _, pins = self.signed()
        (self.root / "settings.json").write_text("{}")
        integrity.snapshot(self.root, apply=True)
        with self.assertRaises(CodeMarkError):
            attestations.verify_hybrid(self.root, pins["mldsa87"], pins["ed25519"])

    def test_history_appends_and_external_checkpoint_detects_rollback(self):
        first, pins = self.signed()
        old = (self.root / ".codemark/attestations.json").read_bytes()
        second, _ = self.signed()
        self.assertEqual(second["records"], 2)
        self.assertNotEqual(first["checkpoint"], second["checkpoint"])
        (self.root / ".codemark/attestations.json").write_bytes(old)
        with self.assertRaises(CodeMarkError):
            attestations.verify_hybrid(
                self.root,
                pins["mldsa87"],
                pins["ed25519"],
                checkpoint=second["checkpoint"],
            )

    def test_report_failure_preserves_existing_history(self):
        self.signed()
        path = self.root / ".codemark/attestations.json"
        previous = path.read_bytes()

        def fail(_):
            raise OSError("report unavailable")

        with self.assertRaises(OSError):
            attestations.sign_hybrid(self.root, self.pq, self.ed, before_commit=fail)
        self.assertEqual(path.read_bytes(), previous)
        self.assertFalse((self.root / ".codemark/lock").exists())

    def test_concurrent_history_append_is_preserved(self):
        self.signed()
        path = self.root / ".codemark/attestations.json"
        records = attestations.read_history(self.root)
        raw = (self.root / ".codemark/integrity.json").read_bytes()
        concurrent = pq_signing.create_record(
            raw,
            integrity.read_snapshot(self.root)["project_id"],
            self.pq,
            self.ed,
            previous=records[-1],
        )
        replacement = pq_signing.canonical_bytes([*records, concurrent]) + b"\n"

        def replace(_):
            path.write_bytes(replacement)

        with self.assertRaises(CodeMarkError):
            attestations.sign_hybrid(self.root, self.pq, self.ed, before_commit=replace)
        self.assertEqual(path.read_bytes(), replacement)

    def test_stale_snapshot_and_keys_inside_project_are_refused(self):
        (self.root / "settings.json").write_text("{}")
        with self.assertRaises(CodeMarkError):
            attestations.sign_hybrid(self.root, self.pq, self.ed)
        inside = self.root / "private.pem"
        inside.write_bytes(self.pq.read_bytes())
        integrity.snapshot(self.root, apply=True)
        with self.assertRaises(CodeMarkError):
            attestations.sign_hybrid(self.root, inside, self.ed)
        self.assertFalse((self.root / ".codemark/attestations.json").exists())

    def test_manifest_changed_during_signing_does_not_commit(self):
        original = pq_signing.create_record

        def raced(*args, **kwargs):
            value = original(*args, **kwargs)
            (self.root / ".codemark/integrity.json").write_bytes(b"{}")
            return value

        with (
            patch.object(pq_signing, "create_record", side_effect=raced),
            self.assertRaises(CodeMarkError),
        ):
            attestations.sign_hybrid(self.root, self.pq, self.ed)
        self.assertFalse((self.root / ".codemark/attestations.json").exists())

    def test_duplicate_json_fields_and_nonfinite_values_are_rejected(self):
        path = self.root / ".codemark/attestations.json"
        for raw in [b'[{"payload":1,"payload":2}]', b"[NaN]", b"{}", b"[]"]:
            path.write_bytes(raw)
            with self.subTest(raw=raw), self.assertRaises(CodeMarkError):
                attestations.read_history(self.root)

    def test_independent_pins_are_required(self):
        _, pins = self.signed()
        wrong = "SHA256:" + base64.b64encode(bytes(32)).decode().rstrip("=")
        with self.assertRaises(CodeMarkError):
            attestations.verify_hybrid(self.root, wrong, pins["ed25519"])
        data = json.loads((self.root / ".codemark/attestations.json").read_text())
        self.assertEqual(len(data), 1)

    def test_cli_sign_and_audit_use_both_keys_and_checkpoint(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(
                [
                    "sign",
                    str(self.root),
                    "--pq-key",
                    str(self.pq),
                    "--classical-key",
                    str(self.ed),
                    "--json",
                ]
            )
        self.assertEqual(status, 0)
        signed = json.loads(output.getvalue())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = cli.main(
                [
                    "audit",
                    str(self.root),
                    "--pq-fingerprint",
                    signed["fingerprints"]["mldsa87"],
                    "--classical-fingerprint",
                    signed["fingerprints"]["ed25519"],
                    "--checkpoint",
                    signed["checkpoint"],
                    "--json",
                ]
            )
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(output.getvalue())["rollback_protected"])
