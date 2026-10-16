# Architecture

SecOps Codemark separates source comments, all-file inventory, cryptographic attestation, command orchestration and optional private export. Base Python code uses the standard library. Native OpenSSL and Zupt perform their respective optional cryptographic operations.

## Modules and boundaries

| Component | Responsibility |
| --- | --- |
| `codemark/core.py` | Source inventories, comments, legacy manifests, bounded mutations and rollback |
| `codemark/integrity.py` | Streaming regular-file SHA-256/SHA-512 inventories and comparison |
| `codemark/pq_signing.py` | Canonical hybrid records, OpenSSL ML-DSA-87/Ed25519 calls and chain verification |
| `codemark/fingerprint.py` | Normalized source-token sketches and similarity |
| `codemark/cli.py` | Arguments, reports, mode selection and exit status |
| `codemark/ssh_signing.py` | Legacy OpenSSH source-manifest signing |
| `codemark/signing.py` | Legacy OpenPGP source-manifest signing |
| Bundle command | Explicit Zupt recipient-encrypted export of the selected regular-file tree |
| `codemark/selftest.py` | Temporary host fixtures and explicit optional-tool skips |
| `codemark/gui.py` | Optional Tkinter source-comment workflow |

## Integrity flow

```text
Stable selected tree
  -> streamed regular-file hashes and explicit exclusions
  -> exact integrity.json bytes
  -> canonical record binding both snapshot digests
  -> mandatory ML-DSA-87 and Ed25519 signatures
  -> attestations.json linked history

Current tree + saved snapshot + history
  + two independent trusted signer pins
  + optional independently retained expected latest checkpoint
  -> integrity and authentication report
```

`verify` selects the full-file snapshot when present and can report unauthenticated integrity without pins. `audit` requires the snapshot, history and both pins. Legacy source-manifest signature options do not authenticate the full snapshot.

## Other flows

Source marking inserts removable comments only in supported first-party source formats. Comparison reads suspect source as data and produces candidates; it does not execute it. The self-test executes only its own fixtures.

Private bundling exports the selected regular-file tree through Zupt, including VCS and `.codemark` contents. It has an explicit recipient and output destination and is separate from public unencrypted source distribution.

## Local trust

The operator controls the host, stable tree, verification executable, private keys, trusted pins, recipient identity and expected checkpoint. Local timestamps do not create an external timestamp authority. See [Cryptography](cryptography.md) and [Security](../security.md).

The documentation site is prebuilt HTML/CSS/SVG with no JavaScript, analytics, remote fonts or hosted application backend.
