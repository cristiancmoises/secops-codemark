# Security model

SecOps Codemark provides file-integrity references, hybrid authentication, linked local attestations, optional encrypted exports, and removable source comments. Each operation has a separate coverage and trust boundary.

## What each layer provides

| Layer | Provides | Limit |
| --- | --- | --- |
| SHA-256 + SHA-512 snapshot | File-byte and mode differences against a saved reference | An unsigned local reference can also be replaced |
| ML-DSA-87 + Ed25519 attestations | Both signatures and independently pinned latest signer identities | No trusted time, legal ownership, or automatic revocation |
| Linked canonical history | Signature, sequence, project and previous-record consistency | A valid old whole history needs an independent expected checkpoint to reject rollback |
| Recipient-encrypted Zupt bundle | Explicit private export using ML-KEM-768 + X25519 | The chosen recipient can read included content; key loss may prevent recovery |
| Source comment and token sketch | Removable identifiers and source-copy candidates | Forgeable marks, false positives and negatives |

Neither a hash nor a signature hides content. Confidentiality requires the explicit encrypted bundle operation. Public source archives remain unencrypted. Public code remains available for study and copying under its license.

## Independent trust

Hybrid authentication requires both complete trusted public-key fingerprints. Embedded keys do not establish trust. Keep the expected latest checkpoint outside the party-controlled tree to detect substitution by an older valid history. A locally recorded time is not a trusted timestamp.

The operator manages key origin, compromise, rotation, revocation policy, archived trust records and the verification executable. There is no online identity, revocation, timestamp or transparency service. A compromised private key or host invalidates assumptions the application cannot repair.

## Filesystem boundary

Operate on a stable local tree. Snapshot enumeration refuses symlinks, special files, malformed metadata, detected races and resource-limit violations. It excludes `.codemark`, `.git`, `.hg` and `.svn` components with reasons. Other regular-file formats are included regardless of extension.

Detection of concurrent changes is not a guarantee against a malicious kernel, deliberate adversarial filesystem races, or hostile local account. Snapshot coverage is files, not empty directories, a complete filesystem image, or automatic backup.

Legacy comment operations have different exclusions, source-format restrictions, smaller limits and per-file rollback. Forced termination or power loss can leave partial state. Preserve a recoverable commit or backup and remove a leftover lock only after confirming no operation is running.

## Privacy of exports and metadata

The CLI runs locally and does not upload your project. It is not a secret scanner. A snapshot and attestation can reveal paths, hashes, project identity, key fingerprints and local times.

A private bundle includes regular files in the selected tree, including version-control history and `.codemark`. Review its scope, keep secrets and all private keys outside the selected root, and share only with intended recipients. Encryption does not make a public repository private or conceal copies that already exist.

## Cryptographic scope

Hybrid signing uses OpenSSL 3.5's default provider; private bundles delegate their established recipient format to Zupt. SecOps Codemark does not claim FIPS 140 certification, a formal proof of its Python implementation, host isolation, universal post-quantum protection, or a benchmark not recorded in release evidence.

Read the [cryptography wiki](wiki/cryptography.md) for standards and [Validation](validation.md) for actual versions, exercised negative cases and platform limits.

## Report a vulnerability

Follow the [security policy](../../SECURITY.md). Use synthetic reproducers and do not include credentials, private keys, private source or personal data in public reports.
