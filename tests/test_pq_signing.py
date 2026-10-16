"""Hybrid attestation acceptance and rejection checks using native OpenSSL."""

import base64
import copy
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codemark import __version__, pq_signing
from codemark.core import CodeMarkError

PROJECT = "41acbe6a-c60c-4921-887b-97f749a1cbce"
DOMAIN = "secops-codemark:integrity:v1"


class CanonicalTests(unittest.TestCase):
    def test_canonical_json_has_one_ascii_representation(self):
        self.assertEqual(
            pq_signing.canonical_bytes({"z": "é", "a": [True, None, 3]}),
            b'{"a":[true,null,3],"z":"\\u00e9"}',
        )

    def test_non_json_types_and_nonfinite_numbers_are_rejected(self):
        for value in [
            {1: "numeric key"},
            ("tuple",),
            {"set"},
            b"bytes",
            float("nan"),
            float("inf"),
        ]:
            with (
                self.subTest(value=type(value).__name__),
                self.assertRaises(CodeMarkError),
            ):
                pq_signing.canonical_bytes(value)
        circular = []
        circular.append(circular)
        with self.assertRaises(CodeMarkError):
            pq_signing.canonical_bytes(circular)

    def test_fingerprint_uses_sha256_and_unpadded_base64(self):
        self.assertEqual(
            pq_signing.fingerprint(b"abc"),
            "SHA256:ungWv48Bz+pBQUDeXa4iI7ADYaOWF3qctBD/YfIAFa0",
        )

    def test_missing_backend_reports_unavailable_and_never_falls_back(self):
        with patch("shutil.which", return_value=None):
            result = pq_signing.capabilities()
            self.assertFalse(result["available"])
            self.assertEqual(result["algorithms"], [])
            with self.assertRaises(CodeMarkError):
                pq_signing.create_record(b"snapshot", PROJECT, "missing", "missing")


class HybridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = shutil.which("openssl") or ""
        if not cls.executable or not pq_signing.capabilities()["available"]:
            raise unittest.SkipTest("OpenSSL 3.5+ ML-DSA-87 and Ed25519 are required")
        cls.temp = tempfile.TemporaryDirectory(prefix="codemark-pq-test-")
        cls.home = Path(cls.temp.name)
        cls.env = {
            **{
                key: value
                for key, value in os.environ.items()
                if not key.startswith("OPENSSL_")
            },
            "OPENSSL_CONF": os.devnull,
            "OPENSSL_MODULES": str(cls.home),
            "OPENSSL_ENGINES": str(cls.home),
        }
        cls.pairs = []
        for number in range(2):
            pair = []
            for algorithm, stem in [("ML-DSA-87", "pq"), ("ED25519", "ed")]:
                key = cls.home / f"{stem}-{number}.pem"
                cls.native(
                    "genpkey",
                    "-algorithm",
                    algorithm,
                    "-out",
                    str(key),
                    "-provider",
                    "default",
                )
                key.chmod(0o600)
                pair.append(key)
            cls.pairs.append(tuple(pair))
        cls.passphrase = cls.home / "passphrase.txt"
        cls.passphrase.write_text("temporary qualification passphrase\n")
        cls.passphrase.chmod(0o600)
        cls.encrypted = cls.home / "encrypted-pq.pem"
        cls.native(
            "genpkey",
            "-algorithm",
            "ML-DSA-87",
            "-aes-256-cbc",
            "-pass",
            "file:" + str(cls.passphrase),
            "-out",
            str(cls.encrypted),
            "-provider",
            "default",
        )
        cls.encrypted.chmod(0o600)
        cls.first = pq_signing.create_record(b"first snapshot", PROJECT, *cls.pairs[0])
        cls.pins = cls.first["payload"]["signers"]

    @classmethod
    def native(cls, *args):
        result = subprocess.run(
            [cls.executable, *args],
            env=cls.env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=45,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("Native OpenSSL fixture operation failed")
        return result

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def verify(self, records, **kwargs):
        return pq_signing.verify_chain(
            records, self.pins["mldsa87"], self.pins["ed25519"], **kwargs
        )

    def test_native_roundtrip_records_exact_manifest_and_trust_boundaries(self):
        record = self.first
        payload = record["payload"]
        self.assertEqual(
            set(payload),
            {
                "format",
                "algorithms",
                "project_id",
                "manifest_sha256",
                "manifest_sha512",
                "sequence",
                "previous_record_sha512",
                "created_at",
                "tool_version",
                "signers",
            },
        )
        self.assertEqual(payload["algorithms"], ["ML-DSA-87", "Ed25519"])
        self.assertEqual(
            payload["manifest_sha256"], hashlib.sha256(b"first snapshot").hexdigest()
        )
        self.assertEqual(
            payload["manifest_sha512"], hashlib.sha512(b"first snapshot").hexdigest()
        )
        self.assertEqual(payload["tool_version"], __version__)
        self.assertEqual(len(base64.b64decode(record["signatures"]["mldsa87"])), 4627)
        self.assertEqual(len(base64.b64decode(record["signatures"]["ed25519"])), 64)
        result = self.verify([record])
        for name in [
            "authenticated",
            "post_quantum",
            "hybrid",
            "historical_key_continuity",
        ]:
            self.assertTrue(result[name])
        self.assertFalse(result["trusted_timestamp"])
        self.assertFalse(result["rollback_protected"])
        self.assertEqual(result["records"], 1)
        self.assertEqual(result["project_id"], PROJECT)
        self.assertEqual(result["manifest_sha256"], payload["manifest_sha256"])
        self.assertEqual(result["manifest_sha512"], payload["manifest_sha512"])

    def test_both_independent_pins_are_mandatory(self):
        wrong = "SHA256:" + base64.b64encode(b"x" * 32).decode().rstrip("=")
        for pq, ed in [
            (wrong, self.pins["ed25519"]),
            (self.pins["mldsa87"], wrong),
            (None, self.pins["ed25519"]),
            (self.pins["mldsa87"], ""),
        ]:
            with self.subTest(pq=pq, ed=ed), self.assertRaises(CodeMarkError):
                pq_signing.verify_chain([self.first], pq, ed)

    def test_each_component_signature_is_required_and_mathematically_verified(self):
        for algorithm in ["mldsa87", "ed25519"]:
            changed = copy.deepcopy(self.first)
            signature = bytearray(base64.b64decode(changed["signatures"][algorithm]))
            signature[len(signature) // 2] ^= 1
            changed["signatures"][algorithm] = base64.b64encode(signature).decode()
            with self.subTest(algorithm=algorithm), self.assertRaises(CodeMarkError):
                self.verify([changed])
            del changed["signatures"][algorithm]
            with self.assertRaises(CodeMarkError):
                self.verify([changed])

    def test_changed_payload_and_unknown_algorithm_cannot_downgrade(self):
        for change in [
            lambda p: p.update(manifest_sha256="a" * 64),
            lambda p: p.update(algorithms=["Ed25519"]),
            lambda p: p.update(sequence=True),
            lambda p: p.update(created_at="2026-02-30T00:00:00Z"),
        ]:
            record = copy.deepcopy(self.first)
            change(record["payload"])
            with self.assertRaises(CodeMarkError):
                self.verify([record])

    def test_unknown_fields_and_noncanonical_base64_are_rejected(self):
        for target in [None, "payload", "public_keys", "signatures"]:
            record = copy.deepcopy(self.first)
            (record if target is None else record[target])["extra"] = {}
            with self.subTest(target=target), self.assertRaises(CodeMarkError):
                self.verify([record])
        record = copy.deepcopy(self.first)
        record["signatures"]["ed25519"] += "="
        with self.assertRaises(CodeMarkError):
            self.verify([record])

    def test_wrong_context_signature_is_rejected_even_with_valid_classical_signature(
        self,
    ):
        with tempfile.TemporaryDirectory(dir=self.home) as directory:
            root = Path(directory)
            message, signature = root / "message", root / "signature"
            message.write_bytes(pq_signing.canonical_bytes(self.first["payload"]))
            self.native(
                "pkeyutl",
                "-sign",
                "-rawin",
                "-in",
                str(message),
                "-inkey",
                str(self.pairs[0][0]),
                "-out",
                str(signature),
                "-pkeyopt",
                "context-string:wrong-domain",
                "-provider",
                "default",
            )
            record = copy.deepcopy(self.first)
            record["signatures"]["mldsa87"] = base64.b64encode(
                signature.read_bytes()
            ).decode()
            with self.assertRaises(CodeMarkError):
                self.verify([record])

    def test_rotation_authenticates_prefix_without_claiming_historical_key_continuity(
        self,
    ):
        second = pq_signing.create_record(
            b"second snapshot", PROJECT, *self.pairs[1], previous=self.first
        )
        pins = second["payload"]["signers"]
        result = pq_signing.verify_chain(
            [self.first, second], pins["mldsa87"], pins["ed25519"]
        )
        self.assertFalse(result["historical_key_continuity"])
        self.assertTrue(result["authenticated"])
        self.assertEqual(
            second["payload"]["previous_record_sha512"],
            hashlib.sha512(pq_signing.canonical_bytes(self.first)).hexdigest(),
        )
        changed = copy.deepcopy(self.first)
        changed["payload"]["manifest_sha512"] = "0" * 128
        with self.assertRaises(CodeMarkError):
            pq_signing.verify_chain([changed, second], pins["mldsa87"], pins["ed25519"])

    def test_checkpoint_rejects_prefix_rollback_reorder_and_duplicate_records(self):
        second = pq_signing.create_record(
            b"second snapshot", PROJECT, *self.pairs[0], previous=self.first
        )
        result = self.verify([self.first, second])
        checked = self.verify([self.first, second], checkpoint=result["checkpoint"])
        self.assertTrue(checked["rollback_protected"])
        for records in [
            [self.first],
            [second, self.first],
            [second],
            [self.first, self.first],
        ]:
            with self.subTest(records=len(records)), self.assertRaises(CodeMarkError):
                self.verify(records, checkpoint=result["checkpoint"])

    def test_private_key_types_symlinks_and_sizes_are_rejected(self):
        for pair in [
            (self.pairs[0][1], self.pairs[0][1]),
            (self.pairs[0][0], self.pairs[0][0]),
        ]:
            with self.assertRaises(CodeMarkError):
                pq_signing.create_record(b"snapshot", PROJECT, *pair)
        with tempfile.TemporaryDirectory(dir=self.home) as directory:
            root = Path(directory)
            oversized = root / "large.pem"
            oversized.write_bytes(b"x" * (1024 * 1024 + 1))
            with self.assertRaises(CodeMarkError):
                pq_signing.create_record(
                    b"snapshot", PROJECT, oversized, self.pairs[0][1]
                )
            link = root / "link.pem"
            try:
                link.symlink_to(self.pairs[0][0])
            except OSError:
                return
            with self.assertRaises(CodeMarkError):
                pq_signing.create_record(b"snapshot", PROJECT, link, self.pairs[0][1])

    def test_encrypted_key_uses_native_passphrase_file_without_python_reading_secrets(
        self,
    ):
        original_open = Path.open
        protected = {self.encrypted, self.pairs[0][1], self.passphrase}

        def guarded_open(path, *args, **kwargs):
            if path in protected:
                raise AssertionError(
                    "Python attempted to read private key/passphrase material"
                )
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            record = pq_signing.create_record(
                b"snapshot",
                PROJECT,
                self.encrypted,
                self.pairs[0][1],
                passphrase_file=self.passphrase,
            )
        pins = record["payload"]["signers"]
        self.assertTrue(
            pq_signing.verify_chain([record], pins["mldsa87"], pins["ed25519"])[
                "authenticated"
            ]
        )
        with self.assertRaises(CodeMarkError):
            pq_signing.create_record(
                b"snapshot", PROJECT, self.encrypted, self.pairs[0][1]
            )

    def test_ambient_configuration_and_provider_directories_are_ignored(self):
        bad = self.home / "bad-openssl.cnf"
        bad.write_text("this is not valid OpenSSL configuration\n")
        with patch.dict(
            os.environ,
            {
                "OPENSSL_CONF": str(bad),
                "OPENSSL_MODULES": str(bad),
                "OPENSSL_ENGINES": str(bad),
            },
        ):
            self.assertTrue(pq_signing.capabilities()["available"])
            record = pq_signing.create_record(b"snapshot", PROJECT, *self.pairs[0])
            self.assertTrue(self.verify([record])["authenticated"])

    def test_backend_identity_works_without_python_311_file_digest(self):
        with patch.object(hashlib, "file_digest", None, create=True):
            info = pq_signing.capabilities()
        self.assertTrue(info["available"])
        self.assertRegex(info["binary_sha256"], r"^[0-9a-f]{64}$")

    def test_bounds_and_malformed_previous_fail_closed(self):
        for records in [[], {}, [self.first] * 1001]:
            with self.assertRaises(CodeMarkError):
                self.verify(records)
        for snapshot, project in [("not bytes", PROJECT), (b"snapshot", "not-a-uuid")]:
            with self.assertRaises(CodeMarkError):
                pq_signing.create_record(snapshot, project, *self.pairs[0])
        with (
            patch.object(pq_signing, "MAX_SNAPSHOT_BYTES", 3),
            self.assertRaises(CodeMarkError),
        ):
            pq_signing.create_record(b"four", PROJECT, *self.pairs[0])
        previous = copy.deepcopy(self.first)
        previous["payload"]["project_id"] = "23f1408a-70bb-4385-b43f-2b2af2d3b21a"
        with self.assertRaises(CodeMarkError):
            pq_signing.create_record(
                b"snapshot", PROJECT, *self.pairs[0], previous=previous
            )


if __name__ == "__main__":
    unittest.main()
