#!/usr/bin/env python3
"""Measure a disposable release pipeline; never use real signing keys.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def execute(arguments, expected=0, *, environment=None):
    started = time.perf_counter()
    result = subprocess.run(
        arguments,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    seconds = time.perf_counter() - started
    if result.returncode != expected:
        raise RuntimeError(
            f"Pipeline command returned {result.returncode}; expected {expected}."
        )
    if expected == 2:
        payload = json.loads(result.stderr)
        if "error" not in payload:
            raise RuntimeError("Expected a structured verification error.")
    else:
        payload = json.loads(result.stdout)
    return payload, round(seconds, 6)


def measure(portable, repeats):
    prefix = [sys.executable, "-I", str(portable)]
    doctor, _ = execute([*prefix, "doctor", "--json"])
    backend = doctor["hybrid_signing"]
    if not backend["available"]:
        raise RuntimeError(
            "This experiment requires OpenSSL 3.5+ with ML-DSA-87 and Ed25519."
        )
    durations = {stage: [] for stage in ("snapshot", "sign", "audit")}
    failures = []
    with tempfile.TemporaryDirectory(prefix="codemark-pipeline-") as directory:
        base = Path(directory)
        project = base / "release"
        project.mkdir()
        fixtures = {
            "securityctl": b"#!/bin/sh\nexit 0\n",
            "settings.json": b'{"release":1}\n',
            "image.iso": bytes(2 * 1024 * 1024 + 1),
        }
        for name, data in fixtures.items():
            (project / name).write_bytes(data)
        environment = {
            key: os.environ[key]
            for key in ("PATH", "SystemRoot", "WINDIR")
            if key in os.environ
        }
        environment.update(
            HOME=str(base),
            OPENSSL_CONF=os.devnull,
            OPENSSL_MODULES=str(base),
            OPENSSL_ENGINES=str(base),
        )
        keys = []
        for algorithm in ("ML-DSA-87", "ED25519"):
            key = base / (algorithm + ".pem")
            result = subprocess.run(
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
                env=environment,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=60,
                check=False,
            )
            if result.returncode:
                raise RuntimeError("Ephemeral measurement key generation failed.")
            key.chmod(0o600)
            keys.append(key)

        def snapshot():
            return execute([*prefix, "snapshot", str(project), "--apply", "--json"])

        def sign():
            return execute(
                [
                    *prefix,
                    "sign",
                    str(project),
                    "--pq-key",
                    str(keys[0]),
                    "--classical-key",
                    str(keys[1]),
                    "--json",
                ]
            )

        def audit(signed, checkpoint, expected=0):
            return execute(
                [
                    *prefix,
                    "audit",
                    str(project),
                    "--pq-fingerprint",
                    signed["fingerprints"]["mldsa87"],
                    "--classical-fingerprint",
                    signed["fingerprints"]["ed25519"],
                    "--checkpoint",
                    checkpoint,
                    "--json",
                ],
                expected,
            )

        inventory = signed = None
        for _ in range(repeats):
            inventory, elapsed = snapshot()
            durations["snapshot"].append(elapsed)
            signed, elapsed = sign()
            durations["sign"].append(elapsed)
            checked, elapsed = audit(signed, signed["checkpoint"])
            durations["audit"].append(elapsed)
            if (
                not checked["ok"]
                or not checked["authenticated"]
                or not checked["rollback_protected"]
            ):
                raise RuntimeError(
                    "The baseline pipeline did not authenticate its fixture."
                )
        if inventory is None or signed is None:
            raise RuntimeError(
                "At least one successful measurement repeat is required."
            )

        target = project / "settings.json"
        target.write_bytes(b'{"release":2}\n')
        changed, elapsed = audit(signed, signed["checkpoint"], 1)
        if changed["ok"] or "settings.json" not in changed["changed"]:
            raise RuntimeError("The changed fixture was not rejected.")
        failures.append({"scenario": "changed-file", "exit": 1, "seconds": elapsed})
        _, refresh_snapshot = snapshot()
        refreshed, refresh_sign = sign()
        _, elapsed = audit(refreshed, signed["checkpoint"], 2)
        failures.append(
            {
                "scenario": "stale-checkpoint-after-intended-update",
                "exit": 2,
                "seconds": elapsed,
            }
        )
        updated, refresh_audit = audit(refreshed, refreshed["checkpoint"])
        if not updated["ok"]:
            raise RuntimeError(
                "The reviewed update did not verify with its advanced checkpoint."
            )
        _, elapsed = execute([*prefix, "audit", str(project), "--json"], 2)
        failures.append(
            {"scenario": "missing-trusted-pins", "exit": 2, "seconds": elapsed}
        )
        shell = shutil.which("sh")
        shell_result = None
        if shell:
            shell_environment = {
                **environment,
                "CODEMARK_PYZ": str(portable),
                "RELEASE_DIR": str(project),
                "PQ_FINGERPRINT": refreshed["fingerprints"]["mldsa87"],
                "CLASSICAL_FINGERPRINT": refreshed["fingerprints"]["ed25519"],
                "CHECKPOINT": refreshed["checkpoint"],
                "AUDIT_REPORT": str(base / "shell-audit.json"),
            }
            shell_report, shell_seconds = execute(
                [shell, str(Path(__file__).with_name("verify-release.sh"))],
                environment=shell_environment,
            )
            if (
                not shell_report["ok"]
                or json.loads((base / "shell-audit.json").read_text()) != shell_report
            ):
                raise RuntimeError(
                    "The shell integration example did not preserve its verified report."
                )
            shell_result = {
                "exit": 0,
                "seconds": shell_seconds,
                "saved_report_matches": True,
            }
        report = {
            "format": "secops-codemark-pipeline-measurement-v1",
            "version": doctor["version"],
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "portable_sha256": hashlib.sha256(portable.read_bytes()).hexdigest(),
            "environment": {
                "python": platform.python_version(),
                "system": platform.system(),
                "machine": platform.machine(),
                "openssl": backend["version"],
                "openssl_sha256": backend["binary_sha256"],
            },
            "fixture": {
                "files": inventory["files"],
                "bytes": inventory["total_bytes"],
                "initial_sha256": {
                    name: hashlib.sha256(data).hexdigest()
                    for name, data in fixtures.items()
                },
            },
            "repeats": repeats,
            "integration_surface": {
                "shell_lines": len(
                    Path(__file__)
                    .with_name("verify-release.sh")
                    .read_text()
                    .splitlines()
                ),
                "workflow_lines": len(
                    Path(__file__)
                    .with_name("verify-release.yml")
                    .read_text()
                    .splitlines()
                ),
                "required_environment_settings": 6,
                "verification_cli_commands": 1,
                "signing_private_keys_on_verifier": 0,
                "required_runtime_tools": [
                    "Python 3.10+",
                    "OpenSSL 3.5+",
                    "checksum-verified codemark.pyz",
                ],
                "normal_release_update": [
                    "review intended file changes",
                    "refresh snapshot",
                    "sign snapshot",
                    "store new checkpoint independently",
                    "verify release",
                ],
            },
            "stage_seconds": {
                stage: {
                    "samples": values,
                    "minimum": min(values),
                    "median": statistics.median(values),
                    "maximum": max(values),
                }
                for stage, values in durations.items()
            },
            "failure_scenarios": failures,
            "shell_example": shell_result,
            "intended_update": {
                "snapshot_seconds": refresh_snapshot,
                "sign_seconds": refresh_sign,
                "audit_seconds": refresh_audit,
                "checkpoint_advanced": True,
            },
            "scope": "Local CLI wall time includes Python startup, hashing and native signature processes. Signing repeats extend one history, increasing verification work. Key generation and dependency installation are excluded. Controlled fixtures are not independent adoption, human onboarding time or a long-term maintenance study.",
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codemark", type=Path, required=True, help="checksum-verified portable"
    )
    parser.add_argument("--output", type=Path, required=True, help="new JSON report")
    parser.add_argument("--repeats", type=int, default=5, choices=range(1, 11))
    args = parser.parse_args()
    portable = args.codemark.resolve(strict=True)
    if not portable.is_file() or not shutil.which("openssl"):
        parser.error("An existing portable and OpenSSL are required.")
    if args.output.exists() or args.output.is_symlink():
        parser.error("The output report must be a new file.")
    report = measure(portable, args.repeats)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    print(str(args.output))


if __name__ == "__main__":
    main()
