"""Command line and automation interface. GPL-3.0-or-later."""

import argparse
import importlib.util
import json
import os
import platform
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

from . import __version__, core


def format_report(report):
    action = report.get("action")
    lines = [f"SecOps CodeMark {__version__} | {action}"]
    if action in ("mark", "unmark"):
        lines.append(
            ("Aplicado" if report["applied"] else "Prévia, sem alterações")
            + f": {report['planned']} arquivo(s)."
        )
        if "owner" in report:
            lines.append(
                f"Titular informado: {report['owner']} | Projeto: {report['project']}"
            )
        lines.extend(report.get("paths", [])[:30])
    elif action == "verify":
        lines.append("Integridade: " + ("OK" if report["ok"] else "DIVERGÊNCIAS"))
        lines.append(
            "Referência: "
            + (
                "assinatura e chave fixada verificadas"
                if report["authenticated"]
                else "manifesto local, sem autenticação"
            )
        )
        for field, label in (
            ("changed", "Alterado"),
            ("missing", "Ausente"),
            ("untracked", "Novo/não registrado"),
            ("invalid_marks", "Marca ausente/inválida"),
        ):
            lines.extend(f"{label}: {path}" for path in report[field])
    elif action == "compare":
        lines.append(
            f"{len(report['matches'])} candidato(s); similaridade não é prova de plágio."
        )
        for item in report["matches"][:100]:
            lines.append(
                f"{item['similarity']:.0%} [{item['method']}] {item['reference']} -> {item['candidate']}"
            )
        if len(report["matches"]) > 100:
            lines.append("Lista abreviada; use --json para o relatório completo.")
    elif action == "sign":
        lines.extend(
            [f"Assinatura: {report['signature']}", f"Chave: {report['fingerprint']}"]
        )
    elif action == "doctor":
        lines.extend(
            f"{key}: {value}" for key, value in report.items() if key != "action"
        )
    elif action == "self-test":
        lines.append("Autoteste: " + ("OK" if report["ok"] else "FALHOU"))
        lines.extend(
            f"{item['status']}: {item['name']}"
            + (": " + item["detail"] if item.get("detail") else "")
            for item in report["checks"]
        )
        lines.append(report["scope"])
    if report.get("skipped"):
        lines.append(
            f"Fora da cobertura: {len(report['skipped'])} entrada(s); detalhes em --json."
        )
    if report.get("note"):
        lines.append(report["note"])
    lines.append(
        "Marcas são removíveis. Código público continua sujeito a estudo e cópia."
    )
    return "\n".join(lines)


@contextmanager
def report_file(destination, roots=()):
    """Reserve an external new file before any project operation can mutate."""
    if destination is None:
        yield None
        return
    path = Path(os.path.abspath(destination))
    try:
        target = path.resolve()
        for root in roots:
            if root and target.is_relative_to(Path(root).resolve()):
                raise core.CodeMarkError(
                    "Salve o relatório fora das árvores do projeto e da comparação."
                )
    except (OSError, RuntimeError) as error:
        raise core.CodeMarkError(
            "Caminho do relatório inválido; confira diretórios e links."
        ) from error
    try:
        handle = path.open("x", encoding="utf-8", newline="\n")
    except OSError as error:
        raise core.CodeMarkError(
            "Não foi possível criar o relatório; o destino deve ser novo e gravável."
        ) from error
    identity = os.fstat(handle.fileno())
    complete = False
    try:
        yield handle
        if not handle.closed:
            finish_report(handle)
        complete = True
    finally:
        try:
            handle.close()
        except (OSError, UnicodeError):
            pass  # Preserve the original write/flush error and still remove partial output.
        finally:
            if not complete:
                try:
                    current = path.lstat()
                    if not path.is_symlink() and (current.st_ino, current.st_dev) == (
                        identity.st_ino,
                        identity.st_dev,
                    ):
                        path.unlink()
                except OSError:
                    pass


def finish_report(handle):
    """Complete all report I/O before allowing a project mutation to commit."""
    handle.flush()
    os.fsync(handle.fileno())
    handle.close()


def save_report(destination, content, roots=()):
    with report_file(destination, roots) as handle:
        if handle is None:
            raise core.CodeMarkError("Escolha um caminho para salvar o relatório.")
        handle.write(content + "\n")


def parser():
    cli = argparse.ArgumentParser(
        prog="codemark",
        description="Marca de procedência reversível e comparação de fontes, offline.",
    )
    cli.add_argument(
        "--version", action="version", version="SecOps CodeMark " + __version__
    )
    commands = cli.add_subparsers(dest="command")
    for name in ("mark", "unmark", "verify", "compare", "sign", "doctor", "self-test"):
        command = commands.add_parser(name)
        if name not in ("doctor", "self-test"):
            command.add_argument("root", type=Path)
        if name in ("mark", "unmark"):
            command.add_argument(
                "--apply",
                action="store_true",
                help="gravar alterações; sem isso mostra prévia",
            )
        if name == "mark":
            command.add_argument(
                "--owner", help="titular informado; obrigatório na primeira aplicação"
            )
            command.add_argument(
                "--project", help="nome do projeto; padrão: nome da pasta"
            )
        if name == "compare":
            command.add_argument("suspect", type=Path)
            command.add_argument("--threshold", type=float, default=0.65)
        if name == "sign":
            backend = command.add_mutually_exclusive_group(required=True)
            backend.add_argument(
                "--key", help="fingerprint completo da chave GPG existente"
            )
            backend.add_argument(
                "--ssh-key",
                type=Path,
                help="chave privada Ed25519 existente, fora do projeto, com .pub adjacente",
            )
        if name == "verify":
            command.add_argument("--require-signature", action="store_true")
            command.add_argument("--keyring", type=Path)
            command.add_argument("--fingerprint")
            command.add_argument("--ssh-public-key", type=Path)
            command.add_argument("--ssh-fingerprint")
        command.add_argument(
            "--json", action="store_true", help="relatório legível por máquinas"
        )
        command.add_argument(
            "--output", type=Path, help="salvar relatório em arquivo novo"
        )
    commands.add_parser("gui", help="abrir interface local opcional")
    return cli


def perform(args, before_commit=None):
    if args.command == "mark":
        return core.mark(
            args.root, args.owner, args.project, args.apply, before_commit=before_commit
        )
    if args.command == "unmark":
        return core.unmark(args.root, args.apply, before_commit=before_commit)
    if args.command == "verify":
        signature_options = (
            args.require_signature,
            bool(args.keyring),
            bool(args.fingerprint),
        )
        ssh_options = (bool(args.ssh_public_key), bool(args.ssh_fingerprint))
        if any(signature_options) and any(ssh_options):
            raise core.CodeMarkError("Escolha uma verificação por vez: GPG ou SSH.")
        if any(signature_options) and not all(signature_options):
            raise core.CodeMarkError(
                "Use --require-signature, --keyring e --fingerprint juntos."
            )
        if any(ssh_options) and not all(ssh_options):
            raise core.CodeMarkError("Use --ssh-public-key e --ssh-fingerprint juntos.")
        report = core.verify(args.root)
        authenticated = None
        if args.require_signature:
            from .signing import verify_signature

            authenticated = verify_signature(args.root, args.keyring, args.fingerprint)
        elif all(ssh_options):
            from .ssh_signing import verify_ssh

            authenticated = verify_ssh(
                args.root, args.ssh_public_key, args.ssh_fingerprint
            )
        if authenticated:
            if authenticated["manifest_sha256"] != report["manifest_sha256"]:
                raise core.CodeMarkError("Manifesto mudou durante a verificação.")
            report.update(authenticated)
            report["note"] = (
                "Assinatura válida para a chave fixada; não comprova data ou titularidade legal."
            )
        return report
    if args.command == "compare":
        return core.compare(args.root, args.suspect, args.threshold)
    if args.command == "sign":
        if args.ssh_key:
            from .ssh_signing import sign_ssh

            return sign_ssh(args.root, args.ssh_key, before_commit=before_commit)
        from .signing import sign

        return sign(args.root, args.key, before_commit=before_commit)
    if args.command == "self-test":
        from .selftest import run

        return run()
    return {
        "action": "doctor",
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.system(),
        "tkinter": importlib.util.find_spec("tkinter") is not None,
        "display_configured": bool(
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        )
        or os.name == "nt",
        "gpg": bool(shutil.which("gpg")),
        "gpgv": bool(shutil.which("gpgv")),
        "ssh_keygen": bool(shutil.which("ssh-keygen")),
        "network_required": False,
    }


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    if not args.command:
        cli.print_help()
        return 0
    try:
        if args.command == "gui":
            try:
                from .gui import launch

                launch()
            except (ImportError, RuntimeError) as error:
                raise core.CodeMarkError(
                    "Interface indisponível; instale Tkinter e use uma sessão gráfica, ou utilize a CLI."
                ) from error
            return 0
        roots = [getattr(args, "root", None), getattr(args, "suspect", None)]
        with report_file(args.output, roots) as destination:

            def write_report(report):
                if destination is None:
                    raise core.CodeMarkError(
                        "O destino do relatório não foi reservado."
                    )
                content = (
                    json.dumps(report, ensure_ascii=True, indent=2)
                    if args.json
                    else format_report(report)
                )
                destination.write(content + "\n")
                finish_report(destination)

            report = perform(args, before_commit=write_report if destination else None)
            content = (
                json.dumps(report, ensure_ascii=True, indent=2)
                if args.json
                else format_report(report)
            )
            if destination and not destination.closed:
                write_report(report)
        print(content)
        if args.command == "verify" and not report["ok"]:
            return 1
        if args.command == "compare" and report["matches"]:
            return 1
        if args.command == "self-test" and not report["ok"]:
            return 1
        return 0
    except (core.CodeMarkError, OSError, UnicodeError) as error:
        message = (
            str(error)
            if isinstance(error, core.CodeMarkError)
            else "Falha de acesso ou codificação; confira arquivos e permissões."
        )
        print(
            json.dumps({"error": message}, ensure_ascii=True)
            if getattr(args, "json", False)
            else "Erro: " + message,
            file=sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        print("Operação interrompida.", file=sys.stderr)
        return 2
