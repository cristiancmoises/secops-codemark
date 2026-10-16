"""Optional GPG detached signatures with explicit verifier trust.

SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .core import (CodeMarkError, MAX_METADATA_BYTES, atomic_write, checked_root,
                   digest, project_lock, read_manifest, read_regular)


def full_fingerprint(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})', value):
        raise CodeMarkError('Use o fingerprint OpenPGP completo, com 40 ou 64 caracteres hexadecimais.')
    return value.upper()


def run_gpg(arguments):
    try:
        result = subprocess.run(arguments, stdin=subprocess.DEVNULL,
            capture_output=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CodeMarkError('GPG indisponível ou excedeu 45 segundos; confira o agente/chave local.') from error
    if result.returncode:
        raise CodeMarkError('GPG recusou a operação. Confira chave, assinatura, keyring e agente local.')
    return result


def sign(root, key, *, before_commit=None):
    key = full_fingerprint(key)
    executable = shutil.which('gpg')
    if not executable:
        raise CodeMarkError('Assinatura opcional exige GPG instalado.')
    root = checked_root(root)
    with project_lock(root):
        raw = read_regular(root / '.codemark/manifest.json', MAX_METADATA_BYTES)
        read_manifest(root, raw)
        with tempfile.TemporaryDirectory(prefix='codemark-sign-') as directory:
            frozen = Path(directory) / 'manifest.json'
            signature = Path(directory) / 'manifest.json.asc'
            frozen.write_bytes(raw)
            run_gpg([executable, '--batch', '--armor', '--detach-sign', '--local-user', key,
                     '--output', str(signature), str(frozen)])
            signature_data = read_regular(signature, 1024 * 1024)
        if digest(read_regular(root / '.codemark/manifest.json', MAX_METADATA_BYTES)) != digest(raw):
            raise CodeMarkError('Manifesto mudou durante a assinatura; tente novamente.')
        target = root / '.codemark/manifest.json.asc'
        report = {'action': 'sign', 'signature': str(target), 'fingerprint': key,
                  'manifest_sha256': digest(raw), 'note': 'Preserve a chave pública e uma cópia independente do manifesto.'}
        if before_commit:
            before_commit(report)
        atomic_write(target, signature_data, 0o644)
    return report


def verify_signature(root, keyring, fingerprint):
    expected = full_fingerprint(fingerprint)
    executable = shutil.which('gpgv')
    if not executable:
        raise CodeMarkError('Verificação autenticada exige gpgv instalado.')
    root = checked_root(root)
    raw = read_regular(root / '.codemark/manifest.json', MAX_METADATA_BYTES)
    signature = read_regular(root / '.codemark/manifest.json.asc', 1024 * 1024)
    public_key = read_regular(Path(keyring).absolute(), 8 * 1024 * 1024)
    # All three inputs are frozen. Do not consult the user's default keyring.
    with tempfile.TemporaryDirectory(prefix='codemark-verify-') as directory:
        temp = Path(directory)
        (temp / 'manifest.json').write_bytes(raw)
        (temp / 'signature.asc').write_bytes(signature)
        (temp / 'public.gpg').write_bytes(public_key)
        result = run_gpg([executable, '--homedir', str(temp), '--keyring', str(temp / 'public.gpg'),
                          '--status-fd=1', str(temp / 'signature.asc'), str(temp / 'manifest.json')])
    valid = []
    for line in result.stdout.decode('utf-8', 'replace').splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[:2] == ['[GNUPG:]', 'VALIDSIG']:
            # Accept the pinned primary key or its cryptographically bound signing subkey.
            if expected in (fields[2].upper(), fields[-1].upper()):
                valid.append(fields[2].upper())
    if not valid:
        raise CodeMarkError('A assinatura não corresponde ao fingerprint fixado.')
    return {'authenticated': True, 'fingerprint': expected,
            'signing_fingerprint': valid[0], 'manifest_sha256': digest(raw)}
