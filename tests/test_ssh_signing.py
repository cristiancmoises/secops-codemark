"""Real OpenSSH signatures, using ephemeral keys only."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from codemark import core, ssh_signing

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("ssh-keygen"), "OpenSSH optional")
class SSHSigningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory(prefix="codemark-test-keys-")
        cls.addClassCleanup(cls.keys.cleanup)
        cls.key = Path(cls.keys.name) / "signing key"
        cls.other = Path(cls.keys.name) / "other"
        for key in (cls.key, cls.other):
            subprocess.run(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
                capture_output=True,
                check=True,
                timeout=15,
            )
        cls.public = Path(str(cls.key) + ".pub")
        cls.other_public = Path(str(cls.other) + ".pub")
        cls.fingerprint = subprocess.run(
            ["ssh-keygen", "-l", "-E", "sha256", "-f", str(cls.public)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()[1]
        cls.other_fingerprint = subprocess.run(
            ["ssh-keygen", "-l", "-E", "sha256", "-f", str(cls.other_public)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()[1]

    def setUp(self):
        self.assertIsNotNone(ssh_signing, "OpenSSH signing is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        self.source = self.root / "app.py"
        self.source.write_bytes(b'print("signature fixture")\n')
        core.mark(self.root, owner="Ephemeral Test", apply=True)

    def test_real_signature_authenticates_a_pinned_key(self):
        result = ssh_signing.sign_ssh(self.root, self.key)
        self.assertEqual(result["fingerprint"], self.fingerprint)
        authenticated = ssh_signing.verify_ssh(self.root, self.public, self.fingerprint)
        self.assertTrue(authenticated["authenticated"])
        self.assertEqual(
            authenticated["manifest_sha256"], core.verify(self.root)["manifest_sha256"]
        )
        self.assertEqual(authenticated["backend"], "openssh-ed25519")

    def test_wrong_pinned_fingerprint_is_rejected(self):
        ssh_signing.sign_ssh(self.root, self.key)
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.verify_ssh(self.root, self.public, self.other_fingerprint)

    def test_wrong_public_key_is_rejected_even_with_its_correct_fingerprint(self):
        ssh_signing.sign_ssh(self.root, self.key)
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.verify_ssh(self.root, self.other_public, self.other_fingerprint)

    def test_modified_manifest_is_rejected(self):
        ssh_signing.sign_ssh(self.root, self.key)
        path = self.root / ".codemark/manifest.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.verify_ssh(self.root, self.public, self.fingerprint)

    def test_modified_signature_is_rejected(self):
        result = ssh_signing.sign_ssh(self.root, self.key)
        Path(result["signature"]).write_bytes(b"not a signature")
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.verify_ssh(self.root, self.public, self.fingerprint)

    def test_signature_from_another_namespace_is_rejected(self):
        frozen = self.base / "frozen.json"
        frozen.write_bytes((self.root / ".codemark/manifest.json").read_bytes())
        subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "sign",
                "-n",
                "other-app",
                "-f",
                str(self.key),
                str(frozen),
            ],
            capture_output=True,
            check=True,
            timeout=15,
        )
        (self.root / ".codemark/manifest.json.sshsig").write_bytes(
            Path(str(frozen) + ".sig").read_bytes()
        )
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.verify_ssh(self.root, self.public, self.fingerprint)

    def test_stale_tree_cannot_be_signed_as_a_fresh_release(self):
        self.source.write_bytes(self.source.read_bytes() + b"print(2)\n")
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.sign_ssh(self.root, self.key)
        self.assertFalse((self.root / ".codemark/manifest.json.sshsig").exists())

    def test_inconsistent_private_and_public_pair_is_rejected(self):
        key = self.base / "mismatched key"
        key.write_bytes(self.key.read_bytes())
        key.chmod(0o600)
        Path(str(key) + ".pub").write_bytes(self.other_public.read_bytes())
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.sign_ssh(self.root, key)
        self.assertFalse((self.root / ".codemark/manifest.json.sshsig").exists())

    def test_private_key_inside_source_tree_is_rejected(self):
        key = self.root / "sign-key"
        key.write_bytes(self.key.read_bytes())
        key.chmod(0o600)
        Path(str(key) + ".pub").write_bytes(self.public.read_bytes())
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.sign_ssh(self.root, key)

    def test_multiple_public_keys_are_rejected(self):
        ssh_signing.sign_ssh(self.root, self.key)
        public = self.base / "multiple.pub"
        public.write_bytes(self.public.read_bytes() + self.other_public.read_bytes())
        with self.assertRaises(core.CodeMarkError):
            ssh_signing.verify_ssh(self.root, public, self.fingerprint)

    def test_cli_sign_verify_and_tamper_exit_codes(self):
        def run(*args):
            return subprocess.run(
                [sys.executable, "-m", "codemark", *map(str, args), "--json"],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )

        result = run("sign", self.root, "--ssh-key", self.key)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run(
            "verify",
            self.root,
            "--ssh-public-key",
            self.public,
            "--ssh-fingerprint",
            self.fingerprint,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["authenticated"])
        self.source.write_bytes(self.source.read_bytes() + b"print(3)\n")
        result = run(
            "verify",
            self.root,
            "--ssh-public-key",
            self.public,
            "--ssh-fingerprint",
            self.fingerprint,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(json.loads(result.stdout)["authenticated"])
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_cli_refuses_incomplete_or_mixed_verification_modes(self):
        for flags in [
            ("--ssh-public-key", self.public),
            (
                "--ssh-public-key",
                self.public,
                "--ssh-fingerprint",
                self.fingerprint,
                "--require-signature",
            ),
        ]:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "codemark",
                    "verify",
                    str(self.root),
                    *map(str, flags),
                    "--json",
                ],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("error", json.loads(result.stderr))

    @unittest.skipUnless(
        sys.platform.startswith("linux"), "requires Linux file size limits"
    )
    def test_report_failure_does_not_publish_signature(self):
        root = self.base
        for n in range(9):
            root = root / ("x" * 239 + str(n))
        root = root / "project"
        root.mkdir(parents=True)
        (root / "app.py").write_bytes(b"print(1)\n")
        core.mark(root, owner="Test", apply=True)
        self.assertLess((root / ".codemark/manifest.json").stat().st_size, 2048)
        destination = self.base / "signature-report.json"
        bootstrap = (
            "import resource, signal, sys; "
            "signal.signal(signal.SIGXFSZ, signal.SIG_IGN); "
            "resource.setrlimit(resource.RLIMIT_FSIZE, (2048, 2048)); "
            "from codemark.cli import main; sys.exit(main(sys.argv[1:]))"
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                bootstrap,
                "sign",
                str(root),
                "--ssh-key",
                str(self.key),
                "--output",
                str(destination),
                "--json",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("error", json.loads(result.stderr))
        self.assertFalse((root / ".codemark/manifest.json.sshsig").exists())
        self.assertFalse(destination.exists(), "truncated report retained")
        self.assertTrue(core.verify(root)["ok"])


if __name__ == "__main__":
    unittest.main()
