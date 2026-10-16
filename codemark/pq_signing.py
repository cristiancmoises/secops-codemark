"""Pinned ML-DSA-87 and Ed25519 attestations through native OpenSSL.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import base64
import binascii
import hashlib
import hmac
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .core import CodeMarkError

ALGORITHM = "ML-DSA-87+Ed25519"
DOMAIN = "secops-codemark:integrity:v1"
ALGORITHMS = ("ML-DSA-87", "Ed25519")
FORMAT = "secops-codemark-attestation-v1"
MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024
MAX_RECORD_BYTES = 32 * 1024
MAX_CHAIN_BYTES = 32 * 1024 * 1024
MAX_RECORDS = 1000
MAX_KEY_BYTES = 1024 * 1024
MAX_PASSPHRASE_BYTES = 32 * 1024
_NAMES = ("mldsa87", "ed25519")
_PREFIXES = {
    "mldsa87": bytes.fromhex("30820a32300b060960864801650304031303820a2100"),
    "ed25519": bytes.fromhex("302a300506032b6570032100"),
}
_PUBLIC_SIZES = {"mldsa87": 2614, "ed25519": 44}
_SIGNATURE_SIZES = {"mldsa87": 4627, "ed25519": 64}
_PAYLOAD_FIELDS = {
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
}


def canonical_bytes(value):
    """Encode only JSON types, rejecting ambiguous keys and nonfinite numbers."""
    pending = [(value, 0)]
    try:
        while pending:
            item, depth = pending.pop()
            if depth > 64:
                raise ValueError("JSON nesting limit")
            if type(item) is dict:
                if any(type(key) is not str for key in item):
                    raise ValueError("non-string object key")
                pending.extend((child, depth + 1) for child in item.values())
            elif type(item) is list:
                pending.extend((child, depth + 1) for child in item)
            elif type(item) not in (str, int, float, bool, type(None)):
                raise ValueError("non-JSON type")
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (ValueError, TypeError, RecursionError, OverflowError):
        raise CodeMarkError(
            "A canonical JSON value with finite numbers is required."
        ) from None


def fingerprint(public_spki_der):
    if type(public_spki_der) is not bytes or len(public_spki_der) > MAX_KEY_BYTES:
        raise CodeMarkError("A bounded public SPKI byte string is required.")
    return "SHA256:" + base64.b64encode(
        hashlib.sha256(public_spki_der).digest()
    ).decode("ascii").rstrip("=")


def _hex(value, length):
    return (
        type(value) is str
        and re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is not None
    )


def _pin(value):
    if type(value) is not str or not re.fullmatch(r"SHA256:[A-Za-z0-9+/]{43}", value):
        raise CodeMarkError(
            "Both complete SHA256 public-key fingerprints are required."
        )
    try:
        raw = base64.b64decode(value[7:] + "=", validate=True)
    except (ValueError, binascii.Error):
        raise CodeMarkError("Invalid public-key fingerprint.") from None
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii").rstrip("=") != value[7:]:
        raise CodeMarkError("Noncanonical public-key fingerprint.")
    return value


def _project_id(value):
    try:
        if type(value) is not str or len(value) != 36 or str(uuid.UUID(value)) != value:
            raise ValueError("noncanonical UUID")
    except (ValueError, AttributeError, TypeError):
        raise CodeMarkError("A canonical project UUID is required.") from None
    return value


def _decode(value, size):
    if type(value) is not str or len(value) != 4 * ((size + 2) // 3):
        raise CodeMarkError("Invalid hybrid key/signature encoding or size.")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise CodeMarkError("Invalid hybrid base64 encoding.") from None
    if len(raw) != size or base64.b64encode(raw).decode("ascii") != value:
        raise CodeMarkError("Noncanonical hybrid base64 encoding.")
    return raw


def _public_key(raw, name):
    if len(raw) != _PUBLIC_SIZES[name] or not raw.startswith(_PREFIXES[name]):
        raise CodeMarkError(
            "The signing key must have the exact required algorithm and SPKI encoding."
        )
    return raw


def _record(value):
    if type(value) is not dict or set(value) != {
        "payload",
        "public_keys",
        "signatures",
    }:
        raise CodeMarkError("Invalid attestation record fields.")
    payload = value["payload"]
    if type(payload) is not dict or set(payload) != _PAYLOAD_FIELDS:
        raise CodeMarkError("Invalid attestation payload fields.")
    payload = dict(payload)
    for item in [payload["signers"], value["public_keys"], value["signatures"]]:
        if type(item) is not dict or set(item) != set(_NAMES):
            raise CodeMarkError(
                "Both hybrid components and only their known fields are required."
            )
    if (
        type(payload["format"]) is not str
        or payload["format"] != FORMAT
        or type(payload["algorithms"]) is not list
        or payload["algorithms"] != list(ALGORITHMS)
    ):
        raise CodeMarkError("Unsupported attestation format or algorithm downgrade.")
    payload["algorithms"] = list(payload["algorithms"])
    payload["signers"] = dict(payload["signers"])
    _project_id(payload["project_id"])
    if not _hex(payload["manifest_sha256"], 64) or not _hex(
        payload["manifest_sha512"], 128
    ):
        raise CodeMarkError("Invalid manifest digests.")
    sequence = payload["sequence"]
    if type(sequence) is not int or not 1 <= sequence <= MAX_RECORDS:
        raise CodeMarkError("Invalid attestation sequence.")
    previous = payload["previous_record_sha512"]
    if (sequence == 1 and previous is not None) or (
        sequence > 1 and not _hex(previous, 128)
    ):
        raise CodeMarkError("Invalid previous-record digest.")
    created = payload["created_at"]
    if type(created) is not str or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", created
    ):
        raise CodeMarkError("Invalid UTC attestation timestamp.")
    try:
        datetime.strptime(created, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        raise CodeMarkError("Invalid UTC attestation timestamp.") from None
    version = payload["tool_version"]
    if (
        type(version) is not str
        or len(version) > 64
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[.-][A-Za-z0-9]+)*", version)
    ):
        raise CodeMarkError("Invalid attestation tool version.")
    public = {}
    signatures = {}
    for name in _NAMES:
        public[name] = _public_key(
            _decode(value["public_keys"][name], _PUBLIC_SIZES[name]), name
        )
        signatures[name] = _decode(value["signatures"][name], _SIGNATURE_SIZES[name])
        if not hmac.compare_digest(
            _pin(payload["signers"][name]), fingerprint(public[name])
        ):
            raise CodeMarkError("Embedded public key and signer fingerprint disagree.")
    frozen = {
        "payload": payload,
        "public_keys": dict(value["public_keys"]),
        "signatures": dict(value["signatures"]),
    }
    encoded = canonical_bytes(frozen)
    if len(encoded) > MAX_RECORD_BYTES:
        raise CodeMarkError("Attestation record exceeds 32 KiB.")
    return frozen, encoded, public, signatures


def _key_file(value, maximum):
    try:
        path = Path(os.path.abspath(os.fspath(value)))
        status = path.lstat()
        if not stat.S_ISREG(status.st_mode) or status.st_size > maximum:
            raise ValueError("not a bounded regular file")
    except (OSError, ValueError, TypeError):
        raise CodeMarkError(
            "Keys and passphrase inputs must be bounded regular files without symlinks."
        ) from None
    identity = (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )
    return path, identity


def _unchanged(file, maximum):
    if _key_file(file[0], maximum) != file:
        raise CodeMarkError("A key or passphrase input changed during signing.")


class _OpenSSL:
    def __init__(self, directory):
        found = shutil.which("openssl")
        if not found:
            raise CodeMarkError(
                "Hybrid signatures require OpenSSL 3.5+ with ML-DSA-87 and Ed25519."
            )
        try:
            self.executable = str(Path(found).resolve(strict=True))
            if not Path(self.executable).is_file():
                raise OSError("not a file")
        except OSError:
            raise CodeMarkError("The OpenSSL executable is unavailable.") from None
        self.directory = Path(directory)
        providers = self.directory / "empty-providers"
        providers.mkdir(mode=0o700)
        self.env = {
            name: os.environ[name]
            for name in ("SystemRoot", "WINDIR", "PATH")
            if name in os.environ
        }
        self.env.update(
            OPENSSL_CONF=os.devnull,
            OPENSSL_MODULES=str(providers),
            OPENSSL_ENGINES=str(providers),
            HOME=str(self.directory),
            USERPROFILE=str(self.directory),
            TMPDIR=str(self.directory),
            TEMP=str(self.directory),
            TMP=str(self.directory),
            LC_ALL="C",
        )

    def run(self, *args):
        try:
            result = subprocess.run(
                [self.executable, *args],
                env=self.env,
                cwd=self.directory,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=45,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise CodeMarkError(
                "OpenSSL is unavailable or exceeded the 45-second operation limit."
            ) from None
        if result.returncode:
            raise CodeMarkError(
                "OpenSSL rejected the hybrid key, signature, passphrase, or provider."
            )
        return result.stdout

    def info(self):
        version = self.run("version").decode("ascii", errors="replace").strip()
        if len(version) > 256:
            raise CodeMarkError("Unexpected OpenSSL version response.")
        match = re.match(r"OpenSSL ([0-9]+)\.([0-9]+)\.", version)
        if not match or (int(match[1]), int(match[2])) < (3, 5):
            raise CodeMarkError("Hybrid signatures require OpenSSL 3.5 or later.")
        listing = self.run("list", "-signature-algorithms", "-provider", "default")
        if b"ML-DSA-87" not in listing or b"ED25519" not in listing:
            raise CodeMarkError(
                "The OpenSSL default provider lacks a required hybrid algorithm."
            )
        try:
            with Path(self.executable).open("rb") as stream:
                checksum = hashlib.sha256()
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    checksum.update(block)
                binary_hash = checksum.hexdigest()
        except OSError:
            raise CodeMarkError(
                "Cannot fingerprint the selected OpenSSL executable."
            ) from None
        return {
            "available": True,
            "version": version,
            "binary_sha256": binary_hash,
            "algorithms": list(ALGORITHMS),
            "executable": self.executable,
        }

    def put(self, name, data):
        path = self.directory / name
        path.write_bytes(data)
        path.chmod(0o600)
        return path

    def output(self, name, maximum):
        path = self.directory / name
        try:
            with path.open("rb") as stream:
                data = stream.read(maximum + 1)
        except OSError:
            raise CodeMarkError(
                "OpenSSL did not produce the required public output."
            ) from None
        if len(data) > maximum:
            raise CodeMarkError("OpenSSL public output exceeds its size limit.")
        return data

    def verify(self, prepared):
        record, _, public, signatures = prepared
        message = self.put("payload.json", canonical_bytes(record["payload"]))
        for name in _NAMES:
            key = self.put("public.der", public[name])
            signature = self.put("signature.bin", signatures[name])
            arguments = [
                "pkeyutl",
                "-verify",
                "-rawin",
                "-pubin",
                "-keyform",
                "DER",
                "-in",
                str(message),
                "-inkey",
                str(key),
                "-sigfile",
                str(signature),
                "-provider",
                "default",
            ]
            if name == "mldsa87":
                arguments.extend(["-pkeyopt", "context-string:" + DOMAIN])
            self.run(*arguments)


def capabilities():
    try:
        with tempfile.TemporaryDirectory(
            prefix="secops-codemark-capabilities-"
        ) as directory:
            return _OpenSSL(directory).info()
    except CodeMarkError as error:
        return {
            "available": False,
            "version": None,
            "binary_sha256": None,
            "algorithms": [],
            "executable": None,
            "reason": str(error),
        }


def create_record(
    snapshot_bytes,
    project_id,
    pq_key,
    classical_key,
    *,
    previous=None,
    passphrase_file=None,
):
    if type(snapshot_bytes) is not bytes or len(snapshot_bytes) > MAX_SNAPSHOT_BYTES:
        raise CodeMarkError("Snapshot must be bytes and at most 64 MiB.")
    _project_id(project_id)
    keys = {
        "mldsa87": _key_file(pq_key, MAX_KEY_BYTES),
        "ed25519": _key_file(classical_key, MAX_KEY_BYTES),
    }
    password = (
        _key_file(passphrase_file, MAX_PASSPHRASE_BYTES)
        if passphrase_file is not None
        else None
    )
    prepared = _record(previous) if previous is not None else None
    if prepared and (
        prepared[0]["payload"]["project_id"] != project_id
        or prepared[0]["payload"]["sequence"] >= MAX_RECORDS
    ):
        raise CodeMarkError(
            "Previous record belongs to another project or exhausts the chain limit."
        )
    with tempfile.TemporaryDirectory(prefix="secops-codemark-sign-") as directory:
        native = _OpenSSL(directory)
        native.info()
        if prepared:
            native.verify(prepared)
        public = {}
        password_args = ["-passin", "file:" + str(password[0])] if password else []
        for name in _NAMES:
            _unchanged(keys[name], MAX_KEY_BYTES)
            output = native.directory / (name + "-public.der")
            native.run(
                "pkey",
                "-in",
                str(keys[name][0]),
                "-pubout",
                "-outform",
                "DER",
                "-out",
                str(output),
                "-provider",
                "default",
                *password_args,
            )
            _unchanged(keys[name], MAX_KEY_BYTES)
            public[name] = _public_key(
                native.output(output.name, _PUBLIC_SIZES[name]), name
            )
        payload = {
            "format": FORMAT,
            "algorithms": list(ALGORITHMS),
            "project_id": project_id,
            "manifest_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
            "manifest_sha512": hashlib.sha512(snapshot_bytes).hexdigest(),
            "sequence": prepared[0]["payload"]["sequence"] + 1 if prepared else 1,
            "previous_record_sha512": hashlib.sha512(prepared[1]).hexdigest()
            if prepared
            else None,
            "created_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "tool_version": __version__,
            "signers": {name: fingerprint(public[name]) for name in _NAMES},
        }
        message = native.put("payload-to-sign.json", canonical_bytes(payload))
        signatures = {}
        for name in _NAMES:
            _unchanged(keys[name], MAX_KEY_BYTES)
            output = native.directory / (name + "-signature.bin")
            arguments = [
                "pkeyutl",
                "-sign",
                "-rawin",
                "-in",
                str(message),
                "-inkey",
                str(keys[name][0]),
                "-out",
                str(output),
                "-provider",
                "default",
                *password_args,
            ]
            if name == "mldsa87":
                arguments.extend(["-pkeyopt", "context-string:" + DOMAIN])
            native.run(*arguments)
            _unchanged(keys[name], MAX_KEY_BYTES)
            signatures[name] = base64.b64encode(
                native.output(output.name, _SIGNATURE_SIZES[name])
            ).decode("ascii")
        if password:
            _unchanged(password, MAX_PASSPHRASE_BYTES)
        record = {
            "payload": payload,
            "public_keys": {
                name: base64.b64encode(public[name]).decode("ascii") for name in _NAMES
            },
            "signatures": signatures,
        }
        validated = _record(record)
        native.verify(validated)
        return validated[0]


def verify_chain(records, pq_fingerprint, classical_fingerprint, *, checkpoint=None):
    expected = {"mldsa87": _pin(pq_fingerprint), "ed25519": _pin(classical_fingerprint)}
    if type(records) is not list or not 1 <= len(records) <= MAX_RECORDS:
        raise CodeMarkError("An attestation chain must contain 1 to 1000 records.")
    if checkpoint is not None and not _hex(checkpoint, 128):
        raise CodeMarkError("Checkpoint must be a complete lowercase SHA-512 digest.")
    prepared = []
    total = 2
    previous_hash = None
    project = None
    for index, value in enumerate(records, 1):
        item = _record(value)
        record, encoded, _, _ = item
        total += len(encoded) + (1 if index > 1 else 0)
        if total > MAX_CHAIN_BYTES:
            raise CodeMarkError("Attestation chain exceeds 32 MiB.")
        payload = record["payload"]
        if (
            payload["sequence"] != index
            or (previous_hash is None and payload["previous_record_sha512"] is not None)
            or (
                previous_hash is not None
                and not hmac.compare_digest(
                    payload["previous_record_sha512"], previous_hash
                )
            )
        ):
            raise CodeMarkError(
                "Attestation sequence or previous-record hash is invalid."
            )
        if project is not None and payload["project_id"] != project:
            raise CodeMarkError(
                "Attestation project identity changed within the chain."
            )
        project = payload["project_id"]
        previous_hash = hashlib.sha512(encoded).hexdigest()
        prepared.append(item)
    latest = prepared[-1][0]["payload"]
    latest_hash = hashlib.sha512(prepared[-1][1]).hexdigest()
    for name in _NAMES:
        if not hmac.compare_digest(latest["signers"][name], expected[name]):
            raise CodeMarkError(
                "The latest attestation does not match both independent trusted fingerprints."
            )
    if checkpoint is not None and not hmac.compare_digest(checkpoint, latest_hash):
        raise CodeMarkError(
            "Checkpoint mismatch: attestation truncation, rollback, or replacement detected."
        )
    with tempfile.TemporaryDirectory(prefix="secops-codemark-verify-") as directory:
        native = _OpenSSL(directory)
        native.info()
        for item in prepared:
            native.verify(item)
    continuity = all(
        hmac.compare_digest(item[0]["payload"]["signers"][name], expected[name])
        for item in prepared
        for name in _NAMES
    )
    return {
        "authenticated": True,
        "post_quantum": True,
        "hybrid": True,
        "manifest_sha256": latest["manifest_sha256"],
        "manifest_sha512": latest["manifest_sha512"],
        "checkpoint": latest_hash,
        "records": len(prepared),
        "project_id": project,
        "rollback_protected": checkpoint is not None,
        "historical_key_continuity": continuity,
        "trusted_timestamp": False,
    }
