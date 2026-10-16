# Cryptography and trust

SecOps Codemark uses established implementations for cryptographic operations. Its application policy requires both ML-DSA-87 and Ed25519 signatures for hybrid attestations; optional private bundles delegate ML-KEM-768 + X25519 recipient encryption to Zupt.

## Different jobs, different keys

| Operation | Mechanism | Trust input |
| --- | --- | --- |
| File inventory | SHA-256 and SHA-512 of file bytes | A saved reference; authentication is separate |
| Hybrid attestation | ML-DSA-87 and Ed25519, both required | Two independently trusted public-key fingerprints |
| Rollback detection | Exact latest-record SHA-512 checkpoint | An expected checkpoint retained outside the untrusted tree |
| Private export | Zupt ML-KEM-768 + X25519 recipient encryption | An independently trusted recipient public-key fingerprint |
| Legacy source-manifest signature | OpenSSH Ed25519 or OpenPGP | The backend's independently trusted key pin |

Do not add the bit strengths of two hashes or two signatures to claim a combined security level. Key exchange, signatures, encryption, and trusted timestamps solve different problems.

## Standards and implementation

[ML-DSA is specified in NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final). [ML-KEM is specified in NIST FIPS 203](https://csrc.nist.gov/pubs/fips/203/final). These are algorithm standards, not certification of this application, its host, or a deployed configuration.

Hybrid attestation uses the [OpenSSL 3.5 default provider](https://docs.openssl.org/3.5/man7/OSSL_PROVIDER-default/). SecOps Codemark does not claim FIPS 140 validation. The use of an algorithm whose standard has FIPS in its name does not establish such validation.

The release evidence must identify the actual OpenSSL and Zupt versions and the exercised paths. Do not infer implementation correctness, side-channel resistance, performance, or platform qualification from an algorithm name alone.

## What the signatures bind

Both signatures cover a canonical record payload containing the exact snapshot bytes' SHA-256 and SHA-512 hashes, project identity, signer fingerprints, sequence, local time, and previous-record link. They are not a signature over a human-rendered view of the JSON.

The ML-DSA context separates this protocol from other uses of that key. Embedded public keys are checked against complete independent pins. The report distinguishes historical key continuity from authentication of the latest record.

## Trust and recovery

Keep private keys and passphrase files outside the selected project. Back up keys according to your recovery policy. Keep a separate record of both public-key pins, approved source revision, snapshot, history, and expected checkpoint.

There is no online identity, revocation, timestamp, or transparency service. The operator handles key compromise, rotation, trusted-channel updates, and acceptance of historical signatures. Loss of a recipient private key can make an encrypted export unrecoverable.

Read [Signing](../signing.md), [Traceability](../traceability.md), [Encryption](../encryption.md), and [Security](../security.md).
