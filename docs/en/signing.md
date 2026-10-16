# Sign and authenticate a reference

Version 0.4.0 adds hybrid ML-DSA-87 + Ed25519 attestations for the all-file integrity snapshot. Both signatures are mandatory for this mode. Legacy OpenSSH and OpenPGP signatures remain separate options for the source-comment manifest.

A signature authenticates a reference against trusted keys. It does not encrypt files, establish a trusted date, or prove originality or legal ownership.

## Hybrid prerequisites

Use OpenSSL 3.5 or newer with its built-in default provider and existing ML-DSA-87 and Ed25519 PEM private keys. Hybrid `--classical-key` takes an OpenSSL PEM key, not the OpenSSH private-key format used by legacy `--ssh-key`.

```sh
openssl version
python3 codemark.pyz doctor --json
```

Keep both keys and any passphrase file outside the project. The signing process has no interactive stdin: encrypted keys need `--passphrase-file`, and both encrypted keys must use that file's same passphrase. With no passphrase file, use unencrypted keys protected by your local key-storage policy; encrypted keys are refused rather than prompting.

SecOps Codemark does not generate these signing keys. See the native [OpenSSL key-generation documentation](https://docs.openssl.org/3.5/man1/openssl-genpkey/) when preparing keys in your own protected environment. The implementation uses the default provider and does not claim FIPS 140 certification.

## Compute the two public-key fingerprints

Export each public key as DER SubjectPublicKeyInfo using OpenSSL. Direct native OpenSSL commands can use its own passphrase prompt for encrypted keys; this is separate from noninteractive SecOps Codemark signing.

```sh
openssl pkey -in /outside/keys/mldsa87.pem -pubout -outform DER -out /trusted/mldsa87-public.der
openssl pkey -in /outside/keys/ed25519.pem -pubout -outform DER -out /trusted/ed25519-public.der
```

The fingerprint is `SHA256:` plus unpadded Base64 of SHA-256 over the entire DER SPKI file. Compute it from public bytes:

```sh
python3 -c 'import base64, hashlib, pathlib, sys; print("SHA256:" + base64.b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode().rstrip("="))' /trusted/mldsa87-public.der
python3 -c 'import base64, hashlib, pathlib, sys; print("SHA256:" + base64.b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode().rstrip("="))' /trusted/ed25519-public.der
```

Record both complete fingerprints through an independent trusted channel. Do not pin a key merely because it was embedded in an untrusted attestation. PEM text hashes and a Zupt recipient public-file fingerprint are different inputs.

## Sign an intact snapshot

```sh
python3 codemark.pyz snapshot /project --apply --json
python3 codemark.pyz sign /project --pq-key /outside/keys/mldsa87.pem --classical-key /outside/keys/ed25519.pem --passphrase-file /outside/keys/signing-passphrase --json
```

Omit `--passphrase-file` only when using unencrypted private keys. Passphrase contents never belong in command arguments or shell history. Treat the passphrase file as a secret and protect its permissions.

Both signatures cover a canonical payload binding SHA-256 and SHA-512 of the exact `.codemark/integrity.json` bytes, project identity, both signer fingerprints, a sequence, local time, and the previous-record hash. The record is stored in `.codemark/attestations.json`. Reformatting the snapshot changes the authenticated reference.

## Authenticate and check history

```sh
python3 codemark.pyz verify /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --json
python3 codemark.pyz audit /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --json
```

Both pins are required for authentication. Check the integrity result as well as the authentication result. To detect substitution by an older valid history, also supply an independently retained expected `--checkpoint`; see [Traceability](traceability.md).

## Legacy OpenSSH Ed25519

The source-comment manifest supports the existing OpenSSH backend. It requires local `ssh-keygen` with `-Y`, an existing Ed25519 key outside the project, and its adjacent `.pub` file.

```sh
python3 codemark.pyz sign /project --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /project --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:YOUR_COMPLETE_OPENSSH_FINGERPRINT'
```

This backend uses the `codemark-manifest-v1` namespace and `.codemark/manifest.json.sshsig`. It is a classical signature, not the hybrid attestation mode. OpenSSH handles its own key-agent and passphrase facilities.

## Legacy OpenPGP

Optional OpenPGP signing requires `gpg` and `gpgv`, an existing full key fingerprint, and a dedicated public keyring.

```sh
python3 codemark.pyz sign /project --key YOUR_COMPLETE_GPG_FINGERPRINT
gpg --export YOUR_COMPLETE_GPG_FINGERPRINT > owner-public.gpg
python3 codemark.pyz verify /project --require-signature --keyring /trusted/owner-public.gpg --fingerprint YOUR_COMPLETE_GPG_FINGERPRINT
```

Use `--require-signature`, `--keyring`, and `--fingerprint` together. Do not combine signing backends in one operation. The operator manages key origin, rotation, compromise, and revocation; no online revocation discovery is performed.

Read [Validation](validation.md) for measured backend and platform coverage.
