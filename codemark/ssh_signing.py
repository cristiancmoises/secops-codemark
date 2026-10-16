"""Pinned OpenSSH Ed25519 signatures using the system implementation.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from . import core

NAMESPACE = "codemark-manifest-v1"
SIGNATURE_FILE = "manifest.json.sshsig"
FINGERPRINT = re.compile(r"SHA256:[A-Za-z0-9+/]{43}")


def _tool():
    executable = shutil.which("ssh-keygen")
    if not executable:
        raise core.CodeMarkError(
            "Assinatura SSH exige ssh-keygen com suporte a -Y (OpenSSH)."
        )
    return executable


def _run(arguments, data: bytes | None = None):
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            timeout=45,
            env=dict(os.environ, LC_ALL="C", SSH_ASKPASS_REQUIRE="never"),
            input=data,
            stdin=subprocess.DEVNULL if data is None else None,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise core.CodeMarkError(
            "OpenSSH indisponível ou excedeu 45 segundos; confira a chave e o agente local."
        ) from error
    if result.returncode:
        raise core.CodeMarkError(
            "OpenSSH recusou a operação; confira chave Ed25519, assinatura e suporte a -Y."
        )
    return result


def _public_key(data):
    try:
        lines = [line for line in data.decode("ascii").splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError("one key required")
        fields = lines[0].split()
        if (
            len(fields) < 2
            or fields[0] != "ssh-ed25519"
            or not re.fullmatch(r"[A-Za-z0-9+/]+=*", fields[1])
        ):
            raise ValueError("Ed25519 public key required")
        return (fields[0] + " " + fields[1] + "\n").encode("ascii")
    except (UnicodeError, ValueError) as error:
        raise core.CodeMarkError(
            "Forneça um arquivo com uma única chave pública OpenSSH Ed25519."
        ) from error


def _fingerprint(executable, public_file):
    result = _run([executable, "-l", "-E", "sha256", "-f", str(public_file)])
    fields = result.stdout.decode("ascii", "replace").split()
    if len(fields) < 2 or not FINGERPRINT.fullmatch(fields[1]):
        raise core.CodeMarkError("OpenSSH não retornou um fingerprint SHA256 válido.")
    return fields[1]


def _verify_bytes(raw, signature, public, expected):
    if not isinstance(expected, str) or not FINGERPRINT.fullmatch(expected):
        raise core.CodeMarkError(
            "Use o fingerprint OpenSSH completo no formato SHA256:... ."
        )
    executable = _tool()
    public = _public_key(public)
    with tempfile.TemporaryDirectory(prefix="codemark-ssh-verify-") as directory:
        temp = Path(directory)
        pub_file, sig_file, allowed = (
            temp / "key.pub",
            temp / "signature",
            temp / "allowed_signers",
        )
        pub_file.write_bytes(public)
        actual = _fingerprint(executable, pub_file)
        if actual != expected:
            raise core.CodeMarkError(
                "A chave pública não corresponde ao fingerprint fixado."
            )
        sig_file.write_bytes(signature)
        allowed.write_bytes(
            b'codemark namespaces="' + NAMESPACE.encode("ascii") + b'" ' + public
        )
        _run(
            [
                executable,
                "-Y",
                "verify",
                "-n",
                NAMESPACE,
                "-I",
                "codemark",
                "-f",
                str(allowed),
                "-s",
                str(sig_file),
            ],
            raw,
        )
    return {
        "authenticated": True,
        "fingerprint": actual,
        "backend": "openssh-ed25519",
        "manifest_sha256": core.digest(raw),
    }


def sign_ssh(root, key_file, *, before_commit=None):
    executable = _tool()
    root = core.checked_root(root)
    key = Path(os.path.abspath(key_file))
    try:
        info = key.lstat()
    except OSError as error:
        raise core.CodeMarkError(
            "Chave de assinatura não encontrada ou inacessível."
        ) from error
    if key.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024:
        raise core.CodeMarkError(
            "A chave privada deve ser um arquivo regular local de até 1 MiB."
        )
    if key.resolve().is_relative_to(root.resolve()):
        raise core.CodeMarkError("Mantenha a chave privada fora da árvore do projeto.")
    # Only the explicit public file is read by Python. The native tool reads the private key.
    public = _public_key(core.read_regular(Path(str(key) + ".pub"), 16 * 1024))
    with core.project_lock(root):
        report = core.verify(root)
        if not report["ok"]:
            raise core.CodeMarkError(
                "A árvore diverge do manifesto; confira as alterações e atualize a marca antes de assinar."
            )
        raw = core.read_regular(
            root / ".codemark/manifest.json", core.MAX_METADATA_BYTES
        )
        if core.digest(raw) != report["manifest_sha256"]:
            raise core.CodeMarkError(
                "Manifesto mudou durante a preparação da assinatura."
            )
        with tempfile.TemporaryDirectory(prefix="codemark-ssh-sign-") as directory:
            temp = Path(directory)
            frozen, pub_file = temp / "manifest.json", temp / "key.pub"
            frozen.write_bytes(raw)
            pub_file.write_bytes(public)
            fingerprint = _fingerprint(executable, pub_file)
            _run(
                [
                    executable,
                    "-Y",
                    "sign",
                    "-n",
                    NAMESPACE,
                    "-O",
                    "hashalg=sha512",
                    "-f",
                    str(key),
                    str(frozen),
                ]
            )
            signature = core.read_regular(Path(str(frozen) + ".sig"), 1024 * 1024)
            _verify_bytes(raw, signature, public, fingerprint)
        if core.digest(
            core.read_regular(root / ".codemark/manifest.json", core.MAX_METADATA_BYTES)
        ) != core.digest(raw):
            raise core.CodeMarkError("Manifesto mudou durante a assinatura.")
        target = root / ".codemark" / SIGNATURE_FILE
        report = {
            "action": "sign",
            "signature": str(target),
            "fingerprint": fingerprint,
            "manifest_sha256": core.digest(raw),
            "backend": "openssh-ed25519",
            "note": "Referência assinada; preserve a chave pública e o fingerprint por canal independente.",
        }
        if before_commit:
            before_commit(report)
        core.atomic_write(target, signature, 0o644)
    return report


def verify_ssh(root, public_key, fingerprint):
    root = core.checked_root(root)
    raw = core.read_regular(root / ".codemark/manifest.json", core.MAX_METADATA_BYTES)
    signature = core.read_regular(root / ".codemark" / SIGNATURE_FILE, 1024 * 1024)
    public = core.read_regular(Path(public_key).absolute(), 16 * 1024)
    return _verify_bytes(raw, signature, public, fingerprint)
