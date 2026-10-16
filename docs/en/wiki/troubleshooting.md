# Troubleshooting

## Verification is intact but unauthenticated

Without both hybrid key pins, full-snapshot verification checks only the local reference. Use `audit` with independently trusted complete ML-DSA-87 and Ed25519 fingerprints. An embedded public key is not an independent trust input.

## Integrity verification returns 1

Inspect changed, missing, new and mode-changed files in JSON. Compare with the intended revision. Review legitimate changes before creating and signing a new snapshot; preserve evidence if the differences are unexpected.

## A valid chain fails the expected checkpoint

The expected checkpoint identifies the exact latest record, not an arbitrary ancestor. A mismatch can mean rollback, replacement or a legitimate newer record that has not been approved in your trusted release record. Investigate and update the trusted checkpoint only after reviewing the new reference. Do not drop the check to make an unexplained failure pass.

## OpenSSL cannot sign

Check `doctor --json` and the native OpenSSL version. Hybrid mode needs OpenSSL 3.5 with the default provider, an ML-DSA-87 PEM key and an Ed25519 PEM key. An OpenSSH private key is a different format.

Signing is noninteractive. Encrypted private keys require the same passphrase through a protected `--passphrase-file`. Missing, wrong or changed key/passphrase files fail; no weaker signing backend is substituted automatically.

## Legacy verification options are refused

If `integrity.json` exists, `verify` selects all-file mode. GPG/OpenSSH legacy options only authenticate `manifest.json` from source marking. Select the appropriate workflow and reference; do not treat a source signature as authentication of binaries and other snapshot data.

## A file is skipped or refused

For source marking, inspect `skipped`, format, encoding, prologue, dependency path and limits. For snapshots, inspect `excluded` and the all-file ceilings. Symlinks, special files and detected races are refused rather than silently included.

## A bundle fails recipient verification

Hash the entire Zupt recipient public file and compare its full fingerprint through a trusted channel. It is different from the DER SPKI fingerprint of a signing key. Keep private keys outside the selected tree and verify that the destination is new and external. See [Encryption](../encryption.md).

## A report cannot be written

`--output` needs a new file in a writable existing directory outside the checked trees. Wait for termination before consuming it. Preserve earlier evidence and inspect permissions and free space.

## A lock remains

Confirm no operation is active before removing `.codemark/lock`. Compare the tree with Git or backups after a forced stop. Ordinary rollback does not recover power loss.

## Ask for help

Include versions, platform, exact command, exit status and a synthetic reproducer. Redact private paths and never attach secret keys or passphrase files. Follow the [security policy](../../../SECURITY.md) for sensitive defects.
