"""Atomic whole-project attestations with independently pinned hybrid keys.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import hashlib
import hmac
import json
from pathlib import Path

from . import core, integrity, pq_signing

HISTORY_FILE = "attestations.json"


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise core.CodeMarkError("Duplicate attestation JSON field.")
        value[key] = item
    return value


def _constant(_):
    raise core.CodeMarkError("Nonfinite attestation JSON value.")


def read_history(root, raw=None):
    root = core.checked_root(root)
    if raw is None:
        raw = core.read_regular(
            root / ".codemark" / HISTORY_FILE, pq_signing.MAX_CHAIN_BYTES
        )
    if type(raw) is not bytes or len(raw) > pq_signing.MAX_CHAIN_BYTES:
        raise core.CodeMarkError("Attestation history exceeds its bounded byte format.")
    try:
        records = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise core.CodeMarkError("Invalid attestation history JSON.") from None
    if type(records) is not list or not 1 <= len(records) <= pq_signing.MAX_RECORDS:
        raise core.CodeMarkError("Attestation history requires 1 to 1000 records.")
    return records


def _internal_chain(records):
    """Check mathematics before extending; embedded pins do not establish trust."""
    try:
        pins = records[-1]["payload"]["signers"]
        return pq_signing.verify_chain(records, pins["mldsa87"], pins["ed25519"])
    except (KeyError, TypeError, IndexError):
        raise core.CodeMarkError("Invalid attestation history fields.") from None


def _external_file(root, value):
    path = Path(value).absolute()
    try:
        if path.resolve().is_relative_to(root.resolve()):
            raise core.CodeMarkError(
                "Keep signing keys and passphrases outside the project."
            )
    except (OSError, RuntimeError):
        raise core.CodeMarkError("Invalid signing key or passphrase path.") from None
    return path


def _snapshot_bytes(root):
    raw = core.read_regular(
        root / ".codemark" / integrity.MANIFEST_FILE, integrity.MAX_METADATA_BYTES
    )
    return raw, integrity.read_snapshot(root, raw)


def _unchanged(root, raw):
    if not hmac.compare_digest(_snapshot_bytes(root)[0], raw):
        raise core.CodeMarkError(
            "Integrity snapshot changed during signing or verification."
        )


def sign_hybrid(
    root, pq_key, classical_key, *, passphrase_file=None, before_commit=None
):
    root = core.checked_root(root)
    pq_key = _external_file(root, pq_key)
    classical_key = _external_file(root, classical_key)
    if passphrase_file is not None:
        passphrase_file = _external_file(root, passphrase_file)
    with core.project_lock(root):
        raw, snapshot = _snapshot_bytes(root)
        if not integrity.verify_snapshot(root, raw)["ok"]:
            raise core.CodeMarkError(
                "Project differs from its snapshot; review and snapshot it before signing."
            )
        target = root / ".codemark" / HISTORY_FILE
        previous_raw = (
            core.read_regular(target, pq_signing.MAX_CHAIN_BYTES)
            if target.exists()
            else None
        )
        records = read_history(root, previous_raw) if previous_raw is not None else []
        if records and _internal_chain(records)["project_id"] != snapshot["project_id"]:
            raise core.CodeMarkError(
                "Attestation and snapshot project identities differ."
            )
        record = pq_signing.create_record(
            raw,
            snapshot["project_id"],
            pq_key,
            classical_key,
            previous=records[-1] if records else None,
            passphrase_file=passphrase_file,
        )
        records.append(record)
        verified = _internal_chain(records)
        encoded = pq_signing.canonical_bytes(records) + b"\n"
        if len(encoded) > pq_signing.MAX_CHAIN_BYTES:
            raise core.CodeMarkError("Attestation history exceeds 32 MiB.")
        report = {
            **verified,
            "action": "sign",
            "signature": ".codemark/" + HISTORY_FILE,
            "algorithm": pq_signing.ALGORITHM,
            "fingerprints": record["payload"]["signers"],
            "coverage_mode": "all-regular-files",
            "files": snapshot["file_count"],
            "note": "Store both fingerprints and this checkpoint independently. Local time is not a trusted timestamp.",
        }
        if before_commit:
            before_commit(report)
        _unchanged(root, raw)
        if not integrity.verify_snapshot(root, raw)["ok"]:
            raise core.CodeMarkError(
                "Project changed during signing; history was preserved."
            )
        core.checked_root(root)
        current_raw = (
            core.read_regular(target, pq_signing.MAX_CHAIN_BYTES)
            if target.exists()
            else None
        )
        if current_raw != previous_raw:
            raise core.CodeMarkError(
                "Attestation history changed during signing; concurrent history was preserved."
            )
        core.atomic_write(target, encoded, 0o600)
        return report


def verify_hybrid(root, pq_fingerprint, classical_fingerprint, *, checkpoint=None):
    root = core.checked_root(root)
    raw, snapshot = _snapshot_bytes(root)
    verified = pq_signing.verify_chain(
        read_history(root),
        pq_fingerprint,
        classical_fingerprint,
        checkpoint=checkpoint,
    )
    if (
        verified["project_id"] != snapshot["project_id"]
        or not hmac.compare_digest(
            verified["manifest_sha256"], hashlib.sha256(raw).hexdigest()
        )
        or not hmac.compare_digest(
            verified["manifest_sha512"], hashlib.sha512(raw).hexdigest()
        )
    ):
        raise core.CodeMarkError(
            "The current integrity snapshot is not the signed reference."
        )
    report = integrity.verify_snapshot(root, raw)
    _unchanged(root, raw)
    report.update(verified)
    report["note"] = (
        "Both signatures match the independently pinned keys. Legal ownership and trusted time are not established."
    )
    return report
