import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_cli import REPO

from codemark import core, signing


@unittest.skipUnless(shutil.which("gpg") and shutil.which("gpgv"), "GPG/gpgv optional")
class SigningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home_temp = tempfile.TemporaryDirectory()
        cls.home = Path(cls.home_temp.name)
        cls.home.chmod(0o700)
        cls.environment = dict(os.environ, GNUPGHOME=str(cls.home))
        result = subprocess.run(
            [
                "gpg",
                "--batch",
                "--pinentry-mode",
                "loopback",
                "--passphrase",
                "",
                "--quick-generate-key",
                "CodeMark Test <test@invalid.local>",
                "ed25519",
                "sign",
                "1d",
            ],
            env=cls.environment,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            cls.home_temp.cleanup()
            if (
                b"No agent running" in result.stderr
                or b"failed to start gpg-agent" in result.stderr
            ):
                raise unittest.SkipTest(
                    "Ambiente bloqueia sockets do gpg-agent; teste real de assinatura indisponível"
                )
            raise RuntimeError(result.stderr.decode())
        result = subprocess.run(
            ["gpg", "--batch", "--with-colons", "--list-secret-keys"],
            env=cls.environment,
            capture_output=True,
            text=True,
            check=True,
        )
        cls.key = next(
            line.split(":")[9]
            for line in result.stdout.splitlines()
            if line.startswith("fpr:")
        )
        result = subprocess.run(
            ["gpg", "--batch", "--export", cls.key],
            env=cls.environment,
            capture_output=True,
            check=True,
        )
        cls.keyring = cls.home / "public.gpg"
        cls.keyring.write_bytes(result.stdout)

    @classmethod
    def tearDownClass(cls):
        if shutil.which("gpgconf"):
            subprocess.run(
                ["gpgconf", "--kill", "gpg-agent"],
                env=cls.environment,
                capture_output=True,
                check=False,
            )
        cls.home_temp.cleanup()

    def setUp(self):
        self.assertIsNotNone(signing, "GPG provenance is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "main.py").write_text('print("hi")\n')
        core.mark(self.root, owner="Test", apply=True)
        self.environ_patch = patch.dict(os.environ, {"GNUPGHOME": str(self.home)})
        self.environ_patch.start()
        self.addCleanup(self.environ_patch.stop)

    def test_real_signature_verifies_with_pinned_public_key(self):
        result = signing.sign(self.root, self.key)
        self.assertTrue(Path(result["signature"]).is_file())
        verified = signing.verify_signature(self.root, self.keyring, self.key)
        self.assertTrue(verified["authenticated"])
        self.assertEqual(verified["fingerprint"], self.key)

    def test_stale_source_tree_cannot_be_signed(self):
        path = self.root / "main.py"
        path.write_bytes(path.read_bytes() + b'print("changed after marking")\n')
        with self.assertRaises(core.CodeMarkError):
            signing.sign(self.root, self.key)
        self.assertFalse((self.root / ".codemark/manifest.json.asc").exists())

    def test_wrong_pinned_fingerprint_is_rejected(self):
        signing.sign(self.root, self.key)
        with self.assertRaises(core.CodeMarkError):
            signing.verify_signature(self.root, self.keyring, "A" * 40)

    def test_tampered_manifest_is_rejected(self):
        signing.sign(self.root, self.key)
        path = self.root / ".codemark/manifest.json"
        data = json.loads(path.read_bytes())
        data["owner"] = "Different Owner"
        path.write_bytes(core.json_bytes(data))
        with self.assertRaises(core.CodeMarkError):
            signing.verify_signature(self.root, self.keyring, self.key)

    def test_invalid_signature_and_invalid_key_are_rejected(self):
        with self.assertRaises(core.CodeMarkError):
            signing.sign(self.root, "--anything")
        signing.sign(self.root, self.key)
        (self.root / ".codemark/manifest.json.asc").write_text("not a signature")
        with self.assertRaises(core.CodeMarkError):
            signing.verify_signature(self.root, self.keyring, self.key)

    def test_authenticated_cli_rejects_tampered_source(self):
        signing.sign(self.root, self.key)
        args = [
            sys.executable,
            "-m",
            "codemark",
            "verify",
            str(self.root),
            "--require-signature",
            "--keyring",
            str(self.keyring),
            "--fingerprint",
            self.key,
            "--json",
        ]
        result = subprocess.run(
            args,
            cwd=REPO,
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["authenticated"])
        path = self.root / "main.py"
        path.write_bytes(path.read_bytes() + b'print("altered")\n')
        result = subprocess.run(
            args,
            cwd=REPO,
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
