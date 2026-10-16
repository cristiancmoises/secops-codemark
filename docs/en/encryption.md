# Export an encrypted private bundle

A snapshot, mark, hash, or signature does not hide file contents. Confidentiality is an explicit export operation: `bundle` delegates recipient encryption to **native Zupt 5.2.10+** using its ML-KEM-768 + X25519 hybrid recipient format.

This is separate from ML-DSA-87 + Ed25519 signing. Signing keys authenticate records; a recipient key controls who can decrypt the private archive. Do not substitute one key type for the other.

## Prepare a recipient

Create or use a recipient key outside the selected project. The native Zupt commands are:

```sh
zupt keygen -o /outside/keys/recipient.key
zupt keygen --pub -k /outside/keys/recipient.key -o /trusted/recipient.pub
```

Keep the private recipient key protected and out of the project and release archive. Obtain the recipient public key and its full fingerprint through an independent trusted channel.

The recipient fingerprint is `SHA256:` followed by unpadded Base64 of SHA-256 over the entire `recipient.pub` file. It is not the fingerprint of a signing key or a decoded PEM body. Compute it from public data:

```sh
python3 -c 'import base64, hashlib, pathlib, sys; print("SHA256:" + base64.b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode().rstrip("="))' /trusted/recipient.pub
```

## Preview and create

```sh
python3 codemark.pyz bundle /project --recipient-key /trusted/recipient.pub --recipient-fingerprint 'SHA256:YOUR_RECIPIENT_FINGERPRINT' --archive /exports/private.zupt --json
python3 codemark.pyz bundle /project --recipient-key /trusted/recipient.pub --recipient-fingerprint 'SHA256:YOUR_RECIPIENT_FINGERPRINT' --archive /exports/private.zupt --apply --json
```

The output is an explicit private export. Use a new destination outside the project. Without `--apply`, inspect the preview before creating the archive.

## Understand what is included

The private bundle includes regular files in the selected tree, including `.codemark` metadata and version-control directories such as `.git`. It does not use the snapshot's exclusions to omit them. A Git history can contain old confidential material even when the current checkout looks clean.

Select the root carefully and inspect the planned coverage. Keep credentials, signing private keys, recipient private keys, and passphrase files outside it. Encryption does not authorize disclosure of unrelated data, and the recipient can read included content after decryption. No files outside the selected tree are intentionally added.

## Restore and verify

```sh
zupt extract --pq /outside/keys/recipient.key -o /restore/new-directory /exports/private.zupt
```

Native Zupt 5.2.10 extraction uses the current umask and does not restore POSIX permission modes. Restoration qualification covers exact file bytes, not ACL or mode preservation. An `audit` can therefore report `mode_changed` until you restore the expected modes from a trusted reference. Do not refresh the snapshot to hide that discrepancy.

Keep the restored tree stable and verify its integrity and attestations with independently trusted signing fingerprints and, when required, an independently retained checkpoint. Successful decryption alone does not prove the legal identity of a sender or make an older signed tree current.

## Public releases

Project source releases are genuine, unencrypted `.zupt` archives with SHA-256 checksums. The encrypted bundle command is for an explicit private export; it does not silently encrypt public releases.

The active release evidence states which Zupt version, environment, failure cases, and restoration checks were exercised. Algorithm names are not FIPS 140 certification. See the [cryptography wiki](wiki/cryptography.md).
