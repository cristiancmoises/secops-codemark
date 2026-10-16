# SecOps Codemark

**File integrity, hybrid signatures, and local provenance.**

[Português brasileiro](README.pt-BR.md) · [Documentation](https://codemark.securityops.co/en/docs/) · [Wiki](https://codemark.securityops.co/en/wiki/) · [Release evidence](https://codemark.securityops.co/en/evidence/)

Version **0.4.1** · **GPL-3.0-or-later** · [Full license](COPYING)

SecOps Codemark records SHA-256 and SHA-512 for regular files of any format, authenticates their saved reference with **ML-DSA-87 + Ed25519**, and links attestations into a verifiable local history. An explicit private export can use **Zupt ML-KEM-768 + X25519** recipient encryption. Reversible source comments and source-copy candidate analysis remain separate tools.

The CLI runs locally with Python 3.10+ and its standard library. Hybrid signing additionally requires compatible **OpenSSL 3.5+ with the default provider**; private bundles require **native Zupt 5.2.10+**. No network service is required. The importable module and portable filename remain `codemark` and `codemark.pyz`; the site remains `codemark.securityops.co`.

A signature does not hide content, prove legal ownership, or establish a trusted date. Detecting replacement by an older valid history requires an independently retained expected checkpoint. Algorithm standards do not constitute FIPS 140 certification of this application. Read [Security](docs/en/security.md).

## Start with a file snapshot

Download `codemark.pyz` or the genuine **unencrypted** `secops-codemark-0.4.1.zupt` public source archive from [Downloads](https://codemark.securityops.co/en/downloads/). Verify SHA-256 checksums against an independently trusted reference. Extract source releases with Zupt; the Python portable does not need extraction.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
python3 codemark.pyz snapshot /project --json
python3 codemark.pyz snapshot /project --apply --json
python3 codemark.pyz verify /project --json
```

`snapshot` previews without `--apply`. It streams regular files, including JSON, hidden and extensionless files, documentation, binaries, archives, and ISOs, without changing their content. It records explicit exclusions for `.codemark`, `.git`, `.hg` and `.svn`. Symlinks, special files and detected concurrent changes are refused. The snapshot covers files, not empty directories or a complete filesystem image.

Limits are **100 GiB per file, 1 TiB total and 100,000 regular files**; other metadata and enumeration limits also apply. These are capacity ceilings, not throughput benchmarks. Use a stable selected tree and inspect the reported scope. See [Integrity](docs/en/integrity.md).

On Windows, use `py -3` and quoted native paths. Source checkouts also support `python3 -m codemark`. Read every self-test `skip` and the current [platform evidence](https://codemark.securityops.co/en/evidence/).

## Authenticate with two keys

Use existing ML-DSA-87 and Ed25519 PEM private keys outside the project. Both signatures are required; verification requires both independently trusted full public-key fingerprints.

```sh
python3 codemark.pyz sign /project --pq-key /outside/keys/mldsa87.pem --classical-key /outside/keys/ed25519.pem --json
python3 codemark.pyz audit /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --json
```

The example uses unencrypted key files protected by your key-storage policy. Encrypted keys require a shared `--passphrase-file`; there is no interactive signing prompt. See [Signing](docs/en/signing.md) for public DER SPKI fingerprint computation and key handling.

The exact `.codemark/integrity.json` bytes are bound by their SHA-256 and SHA-512 digests in a canonical signed payload. `.codemark/attestations.json` stores the linked records. Save the returned latest-record checkpoint outside the tree and supply `--checkpoint COMPLETE_LOWERCASE_SHA512` to detect rollback to an older valid chain. See [Traceability](docs/en/traceability.md).

`verify` selects the all-file snapshot when present; without both pins it reports unauthenticated integrity. `audit` requires the snapshot, history, and both pins. Legacy GPG/OpenSSH options authenticate only the source-comment manifest and cannot authenticate a selected full-file snapshot.

## Encrypt an explicit private export

```sh
python3 codemark.pyz bundle /project --recipient-key /trusted/recipient.pub --recipient-fingerprint 'SHA256:YOUR_RECIPIENT_FINGERPRINT' --archive /exports/private.zupt --json
python3 codemark.pyz bundle /project --recipient-key /trusted/recipient.pub --recipient-fingerprint 'SHA256:YOUR_RECIPIENT_FINGERPRINT' --archive /exports/private.zupt --apply --json
```

This is a separate confidentiality operation. It includes regular files in the selected tree, including VCS history and `.codemark` metadata. Keep private keys, passphrase files and unrelated secrets outside that tree, inspect the preview, and use a new external archive destination. A recipient can read included content after decryption. Public project source releases remain unencrypted. See [Encryption](docs/en/encryption.md) for recipient generation, fingerprinting and restoration.

Native Zupt 5.2.10 extraction uses the current umask and does not restore POSIX modes. Read the [restoration guidance](docs/en/encryption.md#restore-and-verify) before auditing an extracted tree.

## Source comments and candidate comparison

```sh
python3 codemark.pyz mark /first-party-module --owner "Your name or organization"
python3 codemark.pyz mark /first-party-module --owner "Your name or organization" --apply
python3 codemark.pyz compare /first-party-module /suspect --threshold 0.80 --json
python3 codemark.pyz unmark /first-party-module --apply
```

`mark` is still a source-comment operation with supported language formats, dependency exclusions and smaller limits. It does not mark JSON, binaries or ISOs. Run your project's tests after marking. Comments are removable and do not change the source license. Candidate similarity is a bounded token-sketch score, not a plagiarism verdict or percentage of copied lines.

The optional Tkinter GUI handles this legacy source-comment workflow. Use the CLI for all-file snapshots and hybrid attestations. If using both workflows, finish intended source edits before taking the snapshot to sign.

## Documentation and evidence

| Topic | English | Português brasileiro |
| --- | --- | --- |
| Start | [Get started](docs/en/getting-started.md) | [Primeiros passos](docs/pt-BR/getting-started.md) |
| File coverage | [Integrity](docs/en/integrity.md) | [Integridade](docs/pt-BR/integrity.md) |
| Commands | [CLI reference](docs/en/cli.md) | [Referência da CLI](docs/pt-BR/cli.md) |
| Hybrid and legacy keys | [Signing](docs/en/signing.md) | [Assinaturas](docs/pt-BR/signing.md) |
| History and rollback | [Traceability](docs/en/traceability.md) | [Rastreabilidade](docs/pt-BR/traceability.md) |
| Private exports | [Encryption](docs/en/encryption.md) | [Criptografia](docs/pt-BR/encryption.md) |
| CI and maintenance | [Integration](docs/en/integration.md) | [Integração](docs/pt-BR/integration.md) |
| Examples and evaluation | [Evidence](docs/en/evidence.md) | [Evidências](docs/pt-BR/evidence.md) |
| Scope and test results | [Validation](docs/en/validation.md) | [Validação](docs/pt-BR/validation.md) |
| Trust | [Security](docs/en/security.md) | [Segurança](docs/pt-BR/security.md) |
| Wiki | [Architecture](docs/en/wiki/architecture.md) | [Arquitetura](docs/pt-BR/wiki/architecture.md) |

Historical 0.2.0 and 0.3.0 reports remain unchanged and labeled by version. They do not qualify changed source or new cryptographic paths. Current results, skips, dates and scopes are published on the [Evidence page](https://codemark.securityops.co/en/evidence/). Already used in the maintainer’s projects.

## Develop

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py --check
```

The build produces a portable, source staging tree and SHA-256 manifest; `--archive` uses installed Zupt for a genuine public `.zupt` archive. Test and compare its extraction with the intended source revision. See [Contributing](CONTRIBUTING.md) and [Security policy](SECURITY.md).

The site uses static HTML, CSS and local SVG with no JavaScript, tracking or remote fonts. Build instructions are in [website/README.md](website/README.md).

## Repositories

- [GitHub · cristiancmoises/secops-codemark](https://github.com/cristiancmoises/secops-codemark)
- [Codeberg · berkeley/secops-codemark](https://codeberg.org/berkeley/secops-codemark)
- [Security Ops Forgejo · git.securityops.co](https://git.securityops.co/cristiancmoises/secops-codemark)
- [Security Ops Forgejo · git.securityops.com.br](https://git.securityops.com.br/cristiancmoises/secops-codemark)

Copyright (C) 2026 SecOps Codemark contributors. GPL-3.0-or-later, without warranty. Existing licenses of marked projects remain applicable.

## Build and release reliability

Version 0.4.1 hardens source packaging and website report routing. Use fresh build outputs, keep private material outside the selected source directories and follow the [release workflow](docs/en/releasing.md). Filename screening does not prove that source contents contain no secrets.
