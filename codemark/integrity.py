"""Bounded, read-only file hashing; inventories disclose paths, never file content.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import hashlib
import io
import json
import os
import re
import stat
import uuid
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath

from . import __version__, core

MANIFEST_FILE = "integrity.json"
FORMAT = "secops-codemark-integrity-v1"
CHUNK_BYTES = 1024 * 1024
MAX_FILE_BYTES = 100 * 1024**3
MAX_TOTAL_BYTES = 1024**4
MAX_FILES = 100000
MAX_ENTRIES = 200000
MAX_METADATA_BYTES = 64 * 1024**2
MAX_PATH_BYTES = 4096
EXCLUDED_DIRECTORIES = {".codemark", ".git", ".hg", ".svn"}
DIRECTORY_FDS = os.open in os.supports_dir_fd and os.scandir in os.supports_fd
FIELDS = {
    "format",
    "project_id",
    "tool_version",
    "created_at",
    "algorithms",
    "files",
    "excluded",
    "file_count",
    "total_bytes",
}
RECORD_FIELDS = {"size", "mode", "sha256", "sha512"}


def _invalid(message="Manifesto de integridade inválido."):
    raise core.CodeMarkError(message)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _invalid("Chave JSON duplicada no manifesto de integridade.")
        result[key] = value
    return result


def _constant(value):
    _invalid("Constante JSON não finita no manifesto de integridade.")


def _path(value):
    if not core.safe_relative(value):
        _invalid("Caminho relativo inseguro no inventário de integridade.")
    try:
        if len(value.encode("utf-8")) > MAX_PATH_BYTES:
            _invalid("Caminho excede o limite do inventário de integridade.")
    except UnicodeError as error:
        raise core.CodeMarkError("Nome de arquivo não é UTF-8 válido.") from error
    if any(part in EXCLUDED_DIRECTORIES for part in PurePosixPath(value).parts[:-1]):
        _invalid("Registro dentro de diretório excluído do inventário.")
    return value


def _integer(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def _validate(manifest):
    if (
        not isinstance(manifest, dict)
        or set(manifest) != FIELDS
        or manifest["format"] != FORMAT
    ):
        _invalid()
    try:
        ident = manifest["project_id"]
        if not isinstance(ident, str) or str(uuid.UUID(ident)) != ident:
            _invalid()
        version = manifest["tool_version"]
        if not isinstance(version, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9.+-]{0,63}", version
        ):
            _invalid()
        created = manifest["created_at"]
        if (
            not isinstance(created, str)
            or len(created) > 40
            or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)",
                created,
            )
        ):
            _invalid()
        if datetime.fromisoformat(
            created.replace("Z", "+00:00")
        ).utcoffset() != timedelta(0):
            _invalid()
    except (ValueError, AttributeError, TypeError) as error:
        raise core.CodeMarkError(
            "Identidade/data inválida no manifesto de integridade."
        ) from error
    if manifest["algorithms"] != ["sha256", "sha512"]:
        _invalid()
    files, excluded = manifest["files"], manifest["excluded"]
    if (
        not isinstance(files, dict)
        or len(files) > MAX_FILES
        or not isinstance(excluded, list)
        or len(excluded) + len(files) > MAX_ENTRIES
    ):
        _invalid()
    if not _integer(manifest["file_count"], MAX_FILES) or manifest["file_count"] != len(
        files
    ):
        _invalid()
    if not _integer(manifest["total_bytes"], MAX_TOTAL_BYTES):
        _invalid()
    total = 0
    for name, record in files.items():
        _path(name)
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            _invalid()
        if not _integer(record["size"], MAX_FILE_BYTES) or not _integer(
            record["mode"], 0o7777
        ):
            _invalid()
        for algorithm, length in (("sha256", 64), ("sha512", 128)):
            value = record[algorithm]
            if not isinstance(value, str) or not re.fullmatch(
                "[0-9a-f]{" + str(length) + "}", value
            ):
                _invalid()
        total += record["size"]
        if total > MAX_TOTAL_BYTES:
            _invalid()
    if total != manifest["total_bytes"]:
        _invalid()
    seen = set()
    for item in excluded:
        if not isinstance(item, dict) or set(item) != {"path", "reason"}:
            _invalid()
        name = _path(item["path"])
        reason = item["reason"]
        if (
            PurePosixPath(name).name not in EXCLUDED_DIRECTORIES
            or name in seen
            or name in files
        ):
            _invalid()
        if (
            not isinstance(reason, str)
            or not reason.strip()
            or len(reason) > 200
            or any(ord(char) < 32 or ord(char) == 127 for char in reason)
        ):
            _invalid()
        try:
            reason.encode("utf-8")
        except UnicodeError as error:
            raise core.CodeMarkError("Motivo de exclusão inválido.") from error
        seen.add(name)
    return manifest


def read_snapshot(root, raw=None):
    """Validate a frozen UTF-8 manifest, rejecting ambiguous JSON and schemas."""
    root = core.checked_root(root)
    if raw is None:
        raw = core.read_regular(root / ".codemark" / MANIFEST_FILE, MAX_METADATA_BYTES)
    if not isinstance(raw, bytes) or len(raw) > MAX_METADATA_BYTES:
        _invalid()
    try:
        manifest = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant
        )
    except (ValueError, UnicodeError, RecursionError) as error:
        raise core.CodeMarkError("JSON de integridade inválido.") from error
    return _validate(manifest)


def _stamp(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        stat.S_IMODE(info.st_mode),
    )


def _hash_file(path, before, directory_fd, name):
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )
    options = {"dir_fd": directory_fd} if directory_fd is not None else {}
    descriptor = os.open(name if directory_fd is not None else path, flags, **options)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or getattr(opened, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            or _stamp(opened) != _stamp(before)
        ):
            _invalid("Arquivo alterado durante a abertura do inventário.")
        first, second = hashlib.sha256(), hashlib.sha512()
        size = 0
        while data := os.read(descriptor, CHUNK_BYTES):
            size += len(data)
            if size > MAX_FILE_BYTES or size > opened.st_size:
                _invalid("Arquivo alterado/excessivo durante o cálculo de integridade.")
            first.update(data)
            second.update(data)
        after = os.fstat(descriptor)
        current = (
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if directory_fd is not None
            else path.lstat()
        )
        if (
            size != opened.st_size
            or getattr(current, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            or _stamp(after) != _stamp(opened)
            or _stamp(current) != _stamp(opened)
        ):
            _invalid("Arquivo alterado durante o cálculo de integridade.")
        return {
            "size": size,
            "mode": stat.S_IMODE(opened.st_mode),
            "sha256": first.hexdigest(),
            "sha512": second.hexdigest(),
        }
    finally:
        os.close(descriptor)


def _inventory(root):
    files, excluded = {}, []
    entries_seen, total = 0, 0
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )

    def walk(directory, descriptor):
        nonlocal entries_seen, total
        before = os.fstat(descriptor) if descriptor is not None else directory.lstat()
        if not stat.S_ISDIR(before.st_mode) or getattr(
            before, "st_file_attributes", 0
        ) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            _invalid("Diretório alterado durante o inventário de integridade.")
        entries = []
        with os.scandir(
            descriptor if descriptor is not None else directory
        ) as iterator:
            for entry in iterator:
                entries_seen += 1
                if entries_seen > MAX_ENTRIES:
                    _invalid(
                        "Limite de entradas excedido no inventário de integridade."
                    )
                entries.append(entry)
        for entry in sorted(entries, key=lambda item: item.name):
            path = directory / entry.name
            relative = _path(path.relative_to(root).as_posix())
            # Cached DirEntry metadata omits file identity on Windows.
            info = (
                os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                if descriptor is not None
                else path.lstat()
            )
            if stat.S_ISLNK(info.st_mode) or getattr(
                info, "st_file_attributes", 0
            ) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                _invalid("Link simbólico não aceito no inventário de integridade.")
            if stat.S_ISDIR(info.st_mode):
                if entry.name in EXCLUDED_DIRECTORIES:
                    reason = (
                        "Metadados do CodeMark"
                        if entry.name == ".codemark"
                        else "Diretório de controle de versão"
                    )
                    excluded.append({"path": relative, "reason": reason})
                    continue
                child = (
                    os.open(entry.name, flags, dir_fd=descriptor)
                    if descriptor is not None
                    else None
                )
                try:
                    if child is not None and _stamp(os.fstat(child)) != _stamp(info):
                        _invalid("Diretório alterado durante a abertura do inventário.")
                    walk(path, child)
                finally:
                    if child is not None:
                        os.close(child)
                continue
            if not stat.S_ISREG(info.st_mode):
                _invalid("Arquivo especial não aceito no inventário de integridade.")
            if (
                info.st_size > MAX_FILE_BYTES
                or total + info.st_size > MAX_TOTAL_BYTES
                or len(files) >= MAX_FILES
            ):
                _invalid(
                    "Limite de arquivos/bytes excedido no inventário de integridade."
                )
            record = _hash_file(path, info, descriptor, entry.name)
            files[relative] = record
            total += record["size"]
        after = os.fstat(descriptor) if descriptor is not None else directory.lstat()
        if _stamp(after) != _stamp(before):
            _invalid("Diretório alterado durante o inventário de integridade.")

    descriptor = None
    try:
        descriptor = os.open(root, flags) if DIRECTORY_FDS else None
        walk(root, descriptor)
    except (OSError, RecursionError) as error:
        raise core.CodeMarkError(
            "Falha de acesso/estabilidade no inventário de integridade."
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return files, sorted(excluded, key=lambda item: item["path"]), total


def _serialize(manifest):
    output = io.BytesIO()
    encoder = json.JSONEncoder(ensure_ascii=True, sort_keys=True, indent=2)
    for fragment in encoder.iterencode(manifest):
        encoded = fragment.encode("utf-8")
        if output.tell() + len(encoded) + 1 > MAX_METADATA_BYTES:
            _invalid("Manifesto de integridade excede o limite de metadados.")
        output.write(encoded)
    output.write(b"\n")
    return output.getvalue()


def _manifest_hashes(raw):
    return {
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "manifest_sha512": hashlib.sha512(raw).hexdigest(),
    }


def snapshot(root, *, apply=False, before_commit=None):
    """Inventory every regular file; only optional metadata is written."""
    root = core.checked_root(root)
    with core.project_lock(root) if apply else nullcontext():
        target = root / ".codemark" / MANIFEST_FILE
        if target.exists():
            project_id = read_snapshot(root)["project_id"]
        elif (root / ".codemark/project.json").exists():
            project_id = core.load_config(root)["project_id"]
        else:
            project_id = str(uuid.uuid4())
        files, excluded, total = _inventory(root)
        manifest = {
            "format": FORMAT,
            "project_id": project_id,
            "tool_version": __version__,
            "created_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "algorithms": ["sha256", "sha512"],
            "files": files,
            "excluded": excluded,
            "file_count": len(files),
            "total_bytes": total,
        }
        raw = _serialize(_validate(manifest))
        report = {
            "action": "snapshot",
            "applied": apply,
            "files": len(files),
            "total_bytes": total,
            "project_id": project_id,
            "coverage_mode": "all-regular-files",
            "excluded": excluded,
            **_manifest_hashes(raw),
        }
        if apply:
            if before_commit:
                before_commit(report)
            core.checked_root(root)
            core.atomic_write(target, raw, 0o600)
        return report


def verify_snapshot(root, raw=None):
    """Compare all current file types with one frozen, validated inventory."""
    root = core.checked_root(root)
    if raw is None:
        raw = core.read_regular(root / ".codemark" / MANIFEST_FILE, MAX_METADATA_BYTES)
    manifest = read_snapshot(root, raw)
    current, excluded, total = _inventory(root)
    reference = manifest["files"]
    common = sorted(set(current) & set(reference))
    changed = [
        name
        for name in common
        if any(
            current[name][key] != reference[name][key]
            for key in ("size", "sha256", "sha512")
        )
    ]
    mode_changed = [
        name for name in common if current[name]["mode"] != reference[name]["mode"]
    ]
    missing = sorted(set(reference) - set(current))
    untracked = sorted(set(current) - set(reference))
    return {
        "action": "verify",
        "ok": not (changed or mode_changed or missing or untracked),
        "files": len(reference),
        "total_bytes": total,
        "project_id": manifest["project_id"],
        "coverage_mode": "all-regular-files",
        "excluded": excluded,
        "changed": changed,
        "missing": missing,
        "untracked": untracked,
        "mode_changed": mode_changed,
        **_manifest_hashes(raw),
        "authenticated": False,
    }
