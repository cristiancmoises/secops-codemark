# Sign a trusted reference

A signature authenticates the manifest against a pinned key. It does not establish a trusted timestamp, originality, or legal ownership. Keep private keys outside the marked project and distribute public keys and full fingerprints through an independent trusted channel.

## OpenSSH Ed25519

Use an existing Ed25519 private key with an adjacent `.pub` file. The system `ssh-keygen` must support signing with `-Y`.

```sh
python3 codemark.pyz sign /project --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /project --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:YOUR_COMPLETE_FINGERPRINT'
```

Replace the example fingerprint with the exact complete value for your key. OpenSSH handles any passphrase through its local facilities. Prepare your key and agent before unattended use.

CodeMark checks that the tree is intact before signing and verifies the generated signature before publishing `.codemark/manifest.json.sshsig`. Verification pins one Ed25519 key and the `codemark-manifest-v1` namespace. A wrong key, wrong namespace, or changed manifest must fail.

## OpenPGP

This optional backend requires `gpg` to sign and `gpgv` to verify. Use an existing full key fingerprint and a dedicated exported public keyring.

```sh
python3 codemark.pyz sign /project --key YOUR_COMPLETE_FINGERPRINT
gpg --export YOUR_COMPLETE_FINGERPRINT > owner-public.gpg
python3 codemark.pyz verify /project --require-signature --keyring /trusted/owner-public.gpg --fingerprint YOUR_COMPLETE_FINGERPRINT
```

Use `--require-signature`, `--keyring`, and `--fingerprint` together. Do not combine GPG verification options with OpenSSH options. CodeMark does not create keys or accept passphrases as arguments.

`gpgv` trusts the specified keyring and does not perform online revocation discovery. The operator must manage trusted keys, rotation, revocation, expiry policy, and the origin of the verification executable.

## Preserve the reference

Keep a separate trusted copy of the manifest, signature, public key, and pinned fingerprint. A public key supplied by the same untrusted change you are checking is not a trusted reference.

After an intentional change, review the source, refresh the manifest with `mark --apply`, run project tests, and sign again. Do not automatically refresh the reference before a CI verification.

For measured backend and platform coverage, read [Validation](validation.md).
