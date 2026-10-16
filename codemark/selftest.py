"""Host smoke tests use only generated fixtures and temporary keys.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import __version__, core

PYTHON_SOURCE = b"""def calculate_total(items, tax):
    total = 0
    for item in items:
        if item > 10:
            total += item * 2
        else:
            total += item + 3
    if total > 100:
        total -= 7
    return round(total * (1 + tax), 2)

print("codemark-ok")
"""


def _require(condition, detail):
    if not condition:
        raise core.CodeMarkError(detail)


def _execute(arguments):
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in ("NODE_OPTIONS", "NODE_PATH")
    }
    environment["GUILE_AUTO_COMPILE"] = "0"
    result = subprocess.run(
        arguments,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=15,
        env=environment,
        check=False,
    )
    _require(
        result.returncode == 0 and result.stdout.strip() == "codemark-ok",
        "A fixture não executou com o resultado esperado.",
    )


def run():
    checks = []

    def check(name, operation):
        try:
            operation()
            checks.append({"name": name, "status": "pass"})
        # A failed smoke check must be recorded without suppressing later checks.
        except Exception as error:  # noqa: BLE001
            checks.append({"name": name, "status": "fail", "detail": str(error)})

    def skip(name, reason):
        checks.append({"name": name, "status": "skip", "detail": reason})

    with tempfile.TemporaryDirectory(prefix="codemark-selftest-") as directory:
        base = Path(directory)
        root, suspect = base / "project", base / "candidate"
        root.mkdir()
        suspect.mkdir()
        originals = {
            "app.py": PYTHON_SOURCE,
            "app.js": b'"use strict";\nconsole.log("codemark-ok");\n',
            "app.scm": b'(display "codemark-ok")(newline)\n',
        }
        for name, data in originals.items():
            (root / name).write_bytes(data)
        (suspect / "copy.py").write_bytes(
            PYTHON_SOURCE.replace(b"calculate_total", b"compute_total")
            .replace(b"items", b"products")
            .replace(b"total", b"subtotal")
        )
        check(
            "mark",
            lambda: _require(
                core.mark(root, owner="CodeMark self-test", apply=True)["changed"] == 3,
                "Marcação incompleta.",
            ),
        )
        check(
            "verify",
            lambda: _require(core.verify(root)["ok"], "Integridade inicial incorreta."),
        )
        check(
            "python-runtime",
            lambda: _execute([sys.executable, "-I", str(root / "app.py")]),
        )
        node = shutil.which("node")
        if node:
            check("javascript-runtime", lambda: _execute([node, str(root / "app.js")]))
        else:
            skip(
                "javascript-runtime",
                "Node não disponível; execução JavaScript não testada.",
            )
        guile = shutil.which("guile")
        if guile:
            check(
                "guile-runtime",
                lambda: _execute(
                    [guile, "--no-auto-compile", "-s", str(root / "app.scm")]
                ),
            )
        else:
            skip("guile-runtime", "Guile não disponível; execução Scheme não testada.")
        ssh = shutil.which("ssh-keygen")
        if ssh:

            def signature_check():
                from .ssh_signing import sign_ssh, verify_ssh

                key = base / "ephemeral-signing-key"
                generated = subprocess.run(
                    [
                        ssh,
                        "-q",
                        "-t",
                        "ed25519",
                        "-N",
                        "",
                        "-C",
                        "codemark ephemeral self-test",
                        "-f",
                        str(key),
                    ],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=15,
                    check=False,
                )
                _require(
                    generated.returncode == 0,
                    "Não foi possível gerar a chave efêmera de teste.",
                )
                signed = sign_ssh(root, key)
                public = Path(str(key) + ".pub")
                _require(
                    verify_ssh(root, public, signed["fingerprint"])["authenticated"],
                    "Assinatura não autenticada.",
                )
                fingerprint = signed["fingerprint"]
                wrong = (
                    "SHA256:"
                    + ("B" if fingerprint[7] != "B" else "A")
                    + fingerprint[8:]
                )
                try:
                    verify_ssh(root, public, wrong)
                except core.CodeMarkError:
                    return
                raise core.CodeMarkError("Fingerprint incorreto foi aceito.")

            check("openssh-signature", signature_check)
        else:
            skip(
                "openssh-signature",
                "ssh-keygen não disponível; assinatura SSH não testada.",
            )

        def tamper_check():
            path = root / "app.py"
            marked = path.read_bytes()
            try:
                path.write_bytes(marked + b"# controlled self-test change\n")
                result = core.verify(root)
                _require(
                    not result["ok"] and "app.py" in result["changed"],
                    "Adulteração não detectada.",
                )
            finally:
                path.write_bytes(marked)

        check("tamper", tamper_check)
        check(
            "compare",
            lambda: _require(
                any(
                    item["candidate"] == "copy.py"
                    for item in core.compare(root, suspect)["matches"]
                ),
                "Cópia controlada não identificada.",
            ),
        )

        def unmark_check():
            core.unmark(root, apply=True)
            _require(
                all(
                    (root / name).read_bytes() == data
                    for name, data in originals.items()
                ),
                "Remoção não preservou os bytes originais.",
            )

        check("unmark", unmark_check)

        from . import attestations, integrity, pq_signing

        complete = base / "complete-project"
        complete.mkdir()
        (complete / "securityopsctl").write_bytes(b"#!/bin/sh\nexit 0\n")
        (complete / "settings.json").write_bytes(b'{"fixture":true}\n')
        (complete / "disk.iso").write_bytes(b"\0" * (2 * 1024 * 1024 + 1))

        def whole_file_check():
            inventory = integrity.snapshot(complete, apply=True)
            _require(inventory["files"] == 3, "Inventário completo incorreto.")
            _require(
                integrity.verify_snapshot(complete)["ok"],
                "Inventário completo não verificou.",
            )
            target = complete / "settings.json"
            previous = target.read_bytes()
            try:
                target.write_bytes(b"{}")
                _require(
                    "settings.json" in integrity.verify_snapshot(complete)["changed"],
                    "JSON adulterado não detectado.",
                )
            finally:
                target.write_bytes(previous)

        check("whole-file-integrity", whole_file_check)
        backend = pq_signing.capabilities()
        if backend["available"]:

            def hybrid_check():
                environment = {
                    key: os.environ[key]
                    for key in ("SystemRoot", "WINDIR", "PATH")
                    if key in os.environ
                }
                environment.update(
                    OPENSSL_CONF=os.devnull,
                    OPENSSL_MODULES=str(base),
                    OPENSSL_ENGINES=str(base),
                )
                keys = []
                for algorithm in ("ML-DSA-87", "ED25519"):
                    key = base / (algorithm + ".pem")
                    generated = subprocess.run(
                        [
                            backend["executable"],
                            "genpkey",
                            "-algorithm",
                            algorithm,
                            "-provider",
                            "default",
                            "-out",
                            str(key),
                        ],
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        timeout=30,
                        check=False,
                        env=environment,
                    )
                    _require(
                        generated.returncode == 0,
                        "Chave temporária híbrida não criada.",
                    )
                    key.chmod(0o600)
                    keys.append(key)
                signed = attestations.sign_hybrid(complete, keys[0], keys[1])
                pins = signed["fingerprints"]
                verified = attestations.verify_hybrid(
                    complete,
                    pins["mldsa87"],
                    pins["ed25519"],
                    checkpoint=signed["checkpoint"],
                )
                _require(
                    verified["ok"]
                    and verified["authenticated"]
                    and verified["rollback_protected"],
                    "Autenticação híbrida não verificou.",
                )
                (complete / "settings.json").write_bytes(b"{}")
                _require(
                    not attestations.verify_hybrid(
                        complete, pins["mldsa87"], pins["ed25519"]
                    )["ok"],
                    "Adulteração autenticada não detectada.",
                )

            check("hybrid-authentication", hybrid_check)
        else:
            skip(
                "hybrid-authentication",
                "OpenSSL 3.5+ com ML-DSA-87 e Ed25519 não disponível.",
            )
    return {
        "action": "self-test",
        "version": __version__,
        "ok": all(item["status"] != "fail" for item in checks),
        "checks": checks,
        "scope": "Fixtures temporárias de CLI neste host; não certifica projetos ou plataformas.",
        "note": "Nenhuma chave ou fonte do usuário foi usada. GUI e GPG não são exercitados por este autoteste.",
    }
