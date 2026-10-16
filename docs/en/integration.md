# Integrate with a release workflow

CodeMark is a local CLI. It requires no daemon, browser extension, service account, telemetry endpoint, or background process.

## A repeatable release

1. Start from the intended clean source revision and run your project's tests.
2. Preview marking a first-party module and inspect exclusions.
3. Apply the marks and run the project's tests again.
4. Review and commit the intended sources and manifest metadata.
5. Sign the manifest with an existing trusted key when authentication is required.
6. Preserve the source revision, manifest, signature, and public-key reference independently.

Mark only code for which the declared owner is appropriate. Known dependency directories are excluded, but arbitrary third-party paths cannot be recognized automatically.

## Verification in CI

```sh
python3 /trusted/codemark.pyz verify /checkout --ssh-public-key /trusted/codemark.pub --ssh-fingerprint 'SHA256:YOUR_COMPLETE_FINGERPRINT' --json
```

Check out the revision you intend to verify. Protect the executable, key, and fingerprint from the untrusted contribution under review. In verification jobs, run `verify` against the approved reference. Running `mark --apply` first would accept the current changes as a new baseline.

A local optional Git hook may execute the same command. CodeMark installs no hooks. Verification examines the working tree, not Git's staged snapshot.

## Store reports outside the tree

```sh
python3 codemark.pyz verify /checkout --json --output /reports/verification-NEW.json
```

Use a new destination outside the checked trees, wait for the process to exit, and record its exit status. Store both failed and successful evidence when making a release decision.

## GNU Guix

The CLI uses the Python in your profile. A possible temporary environment is:

```sh
guix shell python -- python3 codemark.pyz doctor --json
```

Signing also needs OpenSSH or GnuPG. Tkinter and a graphical session are required for the optional GUI. These examples are usage guidance; they do not claim a qualified Guix package or a platform build. Consult the current [validation record](validation.md).

## Source distribution

For development and artifact creation, see [Contributing](wiki/contributing.md). Release archive format and build checks follow the repository's current build script and release documentation. Checksums require an independently trusted reference.
