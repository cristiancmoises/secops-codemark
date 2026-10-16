# Traceability and trusted checkpoints

Hybrid signing links authenticated attestations to a saved integrity snapshot. The history records project identity, sequence, the previous canonical record's SHA-512 digest, the snapshot's SHA-256 and SHA-512 digests, key fingerprints, local creation time, and tool version.

## Create the next record

Create and review a snapshot before signing it:

```sh
python3 codemark.pyz snapshot /project --apply --json
python3 codemark.pyz sign /project --pq-key /outside/keys/mldsa87.pem --classical-key /outside/keys/ed25519.pem --json
```

Records are stored in `.codemark/attestations.json`. Both ML-DSA-87 and Ed25519 signatures must verify. They cover a canonical payload that binds the hashes of the exact raw `.codemark/integrity.json` bytes. Source files are not executed during verification.

## Pin both identities

```sh
python3 codemark.pyz audit /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --json
```

Replace both examples with independently trusted complete fingerprints. Public keys embedded in an attestation are evidence to check, not a source of trust by themselves. The newest record must match both pins. The audit checks the chain's signatures, sequence, project identity, and previous-record links.

Historical signatures are verified, but a past key is not independently trusted merely because it appears in the chain. Inspect `historical_key_continuity` and retain a trusted record of any key transition.

## Detect replacement by an older valid history

A self-consistent old chain can still have valid signatures. To detect its substitution, save the `checkpoint` returned by a successful signing or trusted audit outside the project, in a channel protected from the party whose tree you will verify.

```sh
python3 codemark.pyz audit /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --checkpoint YOUR_COMPLETE_LOWERCASE_SHA512_CHECKPOINT --json
```

The checkpoint is the latest canonical record's full 128-character lowercase SHA-512 hex digest. The supplied checkpoint must match the expected latest record exactly. It is not a timestamp and is not inferred from a checkpoint file in the untrusted tree.

Without an independently retained expected checkpoint, verification cannot detect replacement of the whole tree and its history with an older valid version. Inspect `rollback_protected`; valid signatures alone do not make rollback protection true.

## Time and ownership

Creation times come from the local clock. They are not a trusted timestamp or proof of publication time, legal ownership, or originality. A valid record shows that the relevant private keys signed the bound reference under the implemented policy.

## Retention and limits

Preserve the source revision, exact snapshot bytes, attestation history, both trusted fingerprints, and expected checkpoint independently. The chain is limited to 1,000 records and 32 MiB; one canonical record is limited to 32 KiB. Plan archival and any key transition before reaching the ceiling.

Read [Signing](signing.md) for keys and [Security](security.md) for the local trust boundary. Use [encrypted bundles](encryption.md) when an exported tree needs confidentiality.
