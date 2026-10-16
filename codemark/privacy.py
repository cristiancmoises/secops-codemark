"""Pinned native ML-KEM-768 and X25519 encrypted project bundles.

All regular files, including VCS data and Codemark state, are included. Source
bytes are streamed directly to the native archiver; there is no plaintext copy.
SPDX-License-Identifier: GPL-3.0-or-later
"""

import hashlib
import hmac
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from .core import CodeMarkError
from .integrity import MAX_FILE_BYTES, MAX_TOTAL_BYTES
from .pq_signing import fingerprint as public_fingerprint

MAX_ENTRIES = 200_000
MAX_FILES = 100_000
MAX_PATH_BYTES = 4096
PUBLIC_KEY_BYTES = 1232
NATIVE_ENCRYPTION_TYPE = 0x02


def _identity(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _node(info):
    return info.st_dev, info.st_ino


def _path(value, *, missing_leaf=False):
    """Reject symbolic links and Windows reparse points in every component."""
    path = Path(os.path.abspath(os.fspath(value)))
    chain = [*reversed(path.parents), path]
    for index, part in enumerate(chain):
        try:
            info = part.lstat()
        except FileNotFoundError:
            if missing_leaf and index == len(chain) - 1:
                return path
            raise CodeMarkError(
                "An existing path with regular ancestors is required."
            ) from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise CodeMarkError("Symbolic links and reparse points are not allowed.")
        if index < len(chain) - 1 and not stat.S_ISDIR(info.st_mode):
            raise CodeMarkError("Every ancestor must be a directory.")
    return path


def _inside(path, root):
    return path == root or root in path.parents


def _read_regular(path, *, maximum=None, public=False):
    """Hash one stable regular file without following its final component."""
    before = path.lstat()
    if maximum is None:
        maximum = MAX_FILE_BYTES
    if (
        not stat.S_ISREG(before.st_mode)
        or getattr(before, "st_file_attributes", 0) & 0x400
    ):
        raise CodeMarkError(
            "Every bundled file must be regular and not a symbolic link."
        )
    if maximum is not None and before.st_size > maximum:
        raise CodeMarkError("The public recipient key has an invalid size.")
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0),
    )
    sha256, sha512 = hashlib.sha256(), hashlib.sha512()
    parts = []
    total = 0
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        # Compare ctime only within one API: Windows path/fd semantics can differ.
        if _identity(opened)[:-1] != _identity(before)[:-1]:
            raise CodeMarkError("A file changed while its inventory was being read.")
        while chunk := stream.read(min(1024 * 1024, before.st_size - total + 1)):
            total += len(chunk)
            if total > before.st_size or total > maximum:
                raise CodeMarkError("A regular file grew beyond its inventoried size.")
            sha256.update(chunk)
            sha512.update(chunk)
            if public:
                parts.append(chunk)
        if _identity(os.fstat(stream.fileno())) != _identity(opened):
            raise CodeMarkError("A file changed while its inventory was being read.")
    if total != before.st_size or _identity(path.lstat()) != _identity(before):
        raise CodeMarkError("A file changed while its inventory was being read.")
    return _identity(before), sha256.hexdigest(), sha512.hexdigest(), b"".join(parts)


def _inventory(root):
    """Include every regular file, with no suffix, hidden-path or VCS exclusion."""
    inventory = {}
    files = total = 0
    pending = [root]
    while pending:
        path = pending.pop()
        name = path.relative_to(root).as_posix()
        if len(os.fsencode(name)) >= MAX_PATH_BYTES or len(inventory) >= MAX_ENTRIES:
            raise CodeMarkError(
                "The project exceeds the native bundle path or entry limit."
            )
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise CodeMarkError(
                "Symbolic links and reparse points are not allowed in bundles."
            )
        if stat.S_ISDIR(info.st_mode):
            before = _identity(info)
            with os.scandir(path) as entries:
                children = []
                for entry in entries:
                    if len(inventory) + len(pending) + len(children) >= MAX_ENTRIES:
                        raise CodeMarkError(
                            "The project exceeds the native bundle entry limit."
                        )
                    children.append(Path(entry.path))
                children.sort(reverse=True)
            if _identity(path.lstat()) != before:
                raise CodeMarkError(
                    "A directory changed while its inventory was being read."
                )
            inventory[name] = ("directory", before)
            pending.extend(children)
        elif stat.S_ISREG(info.st_mode):
            files += 1
            if files > MAX_FILES:
                raise CodeMarkError("The project exceeds the native bundle file limit.")
            if info.st_size > MAX_FILE_BYTES or info.st_size > MAX_TOTAL_BYTES - total:
                raise CodeMarkError(
                    "The project exceeds the bundle file or total byte limit."
                )
            identity, sha256, sha512, _ = _read_regular(
                path, maximum=min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - total)
            )
            if identity != _identity(info):
                raise CodeMarkError(
                    "A file changed while the project was being inventoried."
                )
            inventory[name] = ("file", identity, sha256, sha512)
            total += info.st_size
        else:
            raise CodeMarkError("Special files cannot be included in a private bundle.")
    if not files:
        raise CodeMarkError("The project must contain at least one regular file.")
    return inventory, files, total


def _environment(temporary=None):
    environment = {"PATH": "", "LC_ALL": "C", "LANG": "C"}
    for name in ("SystemRoot", "WINDIR"):
        if name in os.environ:
            environment[name] = os.environ[name]
    if temporary is not None:
        environment.update(
            HOME=str(temporary),
            TMPDIR=str(temporary),
            TEMP=str(temporary),
            TMP=str(temporary),
        )
    return environment


def _backend():
    found = shutil.which("zupt")
    if not found:
        raise CodeMarkError(
            "Native Zupt 5.2.10 or newer is required for encrypted bundles."
        )
    executable = Path(found).resolve(strict=True)
    identity, sha256, _, _ = _read_regular(executable)
    result = subprocess.run(
        [str(executable), "--version"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        env=_environment(),
        timeout=15,
        check=False,
    )
    version = re.match(rb"zupt (\d+)\.(\d+)\.(\d+)(?:\s|$)", result.stdout)
    if (
        result.returncode
        or not version
        or tuple(map(int, version.groups())) < (5, 2, 10)
    ):
        raise CodeMarkError(
            "Native Zupt 5.2.10 or newer is required for encrypted bundles."
        )
    return (
        executable,
        identity,
        {
            "name": "Zupt",
            "version": ".".join(part.decode("ascii") for part in version.groups()),
            "executable": str(executable),
            "binary_sha256": sha256,
            "algorithms": ["ML-KEM-768", "X25519"],
            "mode": "native-pq-hybrid-xor-sha3",
            "encryption_type": NATIVE_ENCRYPTION_TYPE,
            "payload_cipher": "AES-256-CTR+HMAC-SHA256",
        },
    )


def _varint(stream):
    value = 0
    for number in range(10):
        byte = stream.read(1)
        if not byte or (number == 9 and byte[0] > 1):
            raise CodeMarkError(
                "The native encrypted archive has an invalid block length."
            )
        value |= (byte[0] & 0x7F) << (7 * number)
        if not byte[0] & 0x80:
            if number and byte[0] == 0:
                raise CodeMarkError(
                    "The native encrypted archive has an invalid block length."
                )
            return value
    raise CodeMarkError("The native encrypted archive has an invalid block length.")


def _inspect_archive(path):
    """Read the binary encryption header, never infer mode from CLI wording."""
    before = path.lstat()
    descriptor = os.open(
        path,
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0),
    )
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or _identity(info)[:-1] != _identity(before)[:-1]
        ):
            raise CodeMarkError(
                "The native encrypted archive is not a stable regular file."
            )
        header = stream.read(64)
        if len(header) != 64 or header[:6] != b"ZUPT\x1a\x00":
            raise CodeMarkError("The native encrypted archive header is invalid.")
        flags = int.from_bytes(header[8:12], "little")
        required = (1 << 0) | (1 << 3) | (1 << 8) | (1 << 9)
        offset = int.from_bytes(header[36:44], "little")
        if flags & required != required or not 64 <= offset < info.st_size - 64:
            raise CodeMarkError(
                "The archive does not declare authenticated native hybrid encryption."
            )
        stream.seek(offset)
        prefix = stream.read(7)
        if prefix != b"\xbb\x01\x03\x00\x00\x00\x00":
            raise CodeMarkError("The native encryption header block is invalid.")
        original, stored = _varint(stream), _varint(stream)
        if original != 1137 or stored != 1137 or len(stream.read(8)) != 8:
            raise CodeMarkError("The native encryption header dimensions are invalid.")
        payload = stream.read(stored)
        if len(payload) != stored or payload[0] != NATIVE_ENCRYPTION_TYPE:
            raise CodeMarkError(
                "Only native ML-KEM-768 plus X25519 hybrid encryption is accepted."
            )
        if _identity(os.fstat(stream.fileno())) != _identity(info):
            raise CodeMarkError("The encrypted archive changed during validation.")
    if _identity(path.lstat()) != _identity(before):
        raise CodeMarkError("The encrypted archive changed during validation.")
    return _identity(before)


def _same_directory(path, identity):
    if _node(path.lstat()) != identity or not stat.S_ISDIR(path.lstat().st_mode):
        raise CodeMarkError("The bundle output directory changed during the operation.")


def _cleanup(temporary, directory_identity, archive, archive_identity):
    """Remove only the owned ciphertext and directory, preserving replacements."""
    try:
        if _node(temporary.lstat()) != directory_identity or not stat.S_ISDIR(
            temporary.lstat().st_mode
        ):
            return
        if archive.exists() or archive.is_symlink():
            info = archive.lstat()
            if not stat.S_ISREG(info.st_mode) or (
                archive_identity is not None
                and _node(info) != _node_from_identity(archive_identity)
            ):
                return
            archive.unlink()
        temporary.rmdir()
    except OSError:
        pass


def _node_from_identity(identity):
    return identity[0], identity[1]


def bundle(root, output, public_key, fingerprint, *, apply=False, before_commit=None):
    """Preview or exclusively publish a native encrypted archive outside root.

    The mandatory recipient fingerprint authenticates the external public key.
    Native key validation and compression use only that public key. Decryption
    verification requires the recipient's private key and is never claimed here.
    """
    temporary = None
    temporary_identity = archive_identity = None
    parent_descriptor = temporary_descriptor = None
    try:
        if type(apply) is not bool or (
            before_commit is not None and not callable(before_commit)
        ):
            raise CodeMarkError("Bundle apply and callback arguments are invalid.")
        root = _path(root)
        if root.parent == root or not root.is_dir():
            raise CodeMarkError(
                "A project directory below a filesystem root is required."
            )
        output = _path(output, missing_leaf=True)
        if _inside(output, root) or output.suffix != ".zupt" or output.exists():
            raise CodeMarkError("A new .zupt archive outside the project is required.")
        public_key = _path(public_key)
        if _inside(public_key, root):
            raise CodeMarkError("The public recipient key must be outside the project.")
        key_identity, _, _, key = _read_regular(
            public_key, maximum=PUBLIC_KEY_BYTES, public=True
        )
        if len(key) != PUBLIC_KEY_BYTES or key[:8] != b"ZKEY\x01\x00\x00\x00":
            raise CodeMarkError(
                "An exact native ZKEY v1 public recipient key is required."
            )
        actual_pin = public_fingerprint(key)
        if type(fingerprint) is not str or not hmac.compare_digest(
            actual_pin, fingerprint
        ):
            raise CodeMarkError(
                "The public recipient fingerprint does not match the required pin."
            )
        inventory, files, total = _inventory(root)
        executable, executable_identity, backend = _backend()
        report = {
            "action": "bundle",
            "applied": False,
            "root": str(root),
            "archive": str(output),
            "archive_info": None,
            "files": files,
            "bytes": total,
            "recipient_fingerprint": actual_pin,
            "backend": backend,
            "encrypted": True,
            "decryption_verified": False,
            "scope": {
                "all_regular_files": True,
                "vcs_included": True,
                "codemark_state_included": True,
            },
        }
        if not apply:
            return report
        parent_identity = _node(output.parent.lstat())
        if os.open in os.supports_dir_fd and os.link in os.supports_dir_fd:
            parent_descriptor = os.open(
                output.parent,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            if _node(os.fstat(parent_descriptor)) != parent_identity:
                raise CodeMarkError("The output directory changed before bundling.")
        temporary = Path(
            tempfile.mkdtemp(prefix=".codemark-bundle-", dir=output.parent)
        )
        temporary.chmod(0o700)
        temporary_identity = _node(temporary.lstat())
        archive = temporary / "encrypted.zupt"
        if parent_descriptor is not None:
            temporary_descriptor = os.open(
                temporary,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            if _node(os.fstat(temporary_descriptor)) != temporary_identity:
                raise CodeMarkError(
                    "The private ciphertext directory changed during creation."
                )
        _same_directory(output.parent, parent_identity)
        result = subprocess.run(
            [
                str(executable),
                "compress",
                "-t",
                "2",
                "--pq",
                str(public_key),
                str(archive),
                "./" + root.name,
            ],
            cwd=root.parent,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=_environment(temporary),
            timeout=300,
            check=False,
        )
        if archive.exists() and not archive.is_symlink():
            archive_identity = _identity(archive.lstat())
        if result.returncode:
            raise CodeMarkError("Native encrypted bundle creation failed.")
        if (
            _identity(public_key.lstat()) != key_identity
            or _identity(executable.lstat()) != executable_identity
        ):
            raise CodeMarkError(
                "A recipient key or native executable changed during bundling."
            )
        if _inventory(root)[0] != inventory:
            raise CodeMarkError("The project changed during native bundle creation.")
        _same_directory(output.parent, parent_identity)
        descriptor = os.open(
            archive,
            os.O_RDWR
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_BINARY", 0),
        )
        with os.fdopen(descriptor, "rb") as stream:
            if _node(os.fstat(stream.fileno())) != _node_from_identity(
                archive_identity
            ):
                raise CodeMarkError(
                    "The encrypted archive changed before permission restriction."
                )
            if hasattr(os, "fchmod"):
                os.fchmod(stream.fileno(), 0o600)
            else:
                os.chmod(archive, 0o600)
            os.fsync(stream.fileno())
        archive_identity = _inspect_archive(archive)
        identity, sha256, sha512, _ = _read_regular(archive)
        if identity != archive_identity:
            raise CodeMarkError("The encrypted archive changed during validation.")
        report["archive_info"] = {
            "sha256": sha256,
            "sha512": sha512,
            "size": archive.stat().st_size,
        }
        report["applied"] = True
        if before_commit is not None:
            before_commit(report)
        if (
            _inventory(root)[0] != inventory
            or _identity(public_key.lstat()) != key_identity
        ):
            raise CodeMarkError(
                "The project or recipient key changed before bundle publication."
            )
        _same_directory(output.parent, parent_identity)
        if _identity(archive.lstat()) != archive_identity:
            raise CodeMarkError("The encrypted archive changed before publication.")
        if parent_descriptor is not None:
            os.link(
                archive.name,
                output.name,
                src_dir_fd=temporary_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        else:
            os.link(archive, output, follow_symlinks=False)
        report["applied"] = True
        return report
    except CodeMarkError:
        raise
    except (OSError, ValueError, TypeError, subprocess.SubprocessError):
        raise CodeMarkError(
            "The encrypted bundle could not be safely created or published."
        ) from None
    finally:
        if temporary is not None and temporary_identity is not None:
            _cleanup(
                temporary,
                temporary_identity,
                temporary / "encrypted.zupt",
                archive_identity,
            )
        if temporary_descriptor is not None:
            os.close(temporary_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)
