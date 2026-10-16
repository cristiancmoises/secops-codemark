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
    return {
        "action": "self-test",
        "version": __version__,
        "ok": all(item["status"] != "fail" for item in checks),
        "checks": checks,
        "scope": "Fixtures temporárias de CLI neste host; não certifica projetos ou plataformas.",
        "note": "Nenhuma chave ou fonte do usuário foi usada. GUI e GPG não são exercitados por este autoteste.",
    }
