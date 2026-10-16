# Release verification example

[English integration guide](../../docs/en/integration.md) · [Guia de integração em português](../../docs/pt-BR/integration.md)

`verify-release.sh` checks every inventoried regular file, both pinned signatures and the independently stored latest checkpoint. It exits unsuccessfully on changed files, missing trust values, invalid signatures or a stale checkpoint. It creates a new private report outside the release tree.

The example needs Python 3.10+, a checksum-verified `codemark.pyz`, OpenSSL 3.5+ with ML-DSA-87 and Ed25519, a prepared release tree and six configured environment variables. It does not need a signing key. Configure both fingerprints and the checkpoint from a trusted channel separate from the release being checked.

The sample workflow is manual and does not install tools, download releases or acquire artifacts. Add your existing artifact retrieval step and verify the portable's SHA-256 before running it. Hosted runner images change; `doctor --json` records capabilities, and `audit` fails when the required crypto backend is unavailable. A green integrity check establishes agreement with a signed reference; it does not test the application or establish that the contents are safe.

Use a separate trusted release stage to run `snapshot --apply`, then `sign --pq-key ... --classical-key ...`. Keep private signing keys outside the release tree and off untrusted contribution jobs. Save the resulting checkpoint independently before distribution. Review intended changes before replacing a snapshot or advancing a checkpoint.

The evidence guide records measured command times and the example's line and configuration counts. Those observations do not measure a person's setup time or long-term maintenance effort.
