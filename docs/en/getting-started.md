# Get started

SecOps Codemark 0.4.1 inventories regular files, authenticates their reference with hybrid signatures, and can create an encrypted private export. Reversible source comments and source-copy comparison remain available as separate operations.

The Python CLI uses the standard library and runs locally. Hybrid signing additionally requires OpenSSL 3.5 with the default provider. Private bundles require compatible Zupt. Availability and measured platform coverage are reported separately.

## Inspect your host

Download the portable `codemark.pyz` or the genuine unencrypted `.zupt` source release from the project downloads. Verify the checksum against an independently trusted reference. Source checkouts also support `python3 -m codemark`.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
```

Read every `skip`; an absent tool has not passed its test. Fixtures do not certify your project. See [Validation](validation.md).

The examples use POSIX paths. On Windows, replace `python3` with `py -3` and use quoted native paths such as `"C:\Projects\release"` and `"C:\Keys\mldsa87.pem"`. OpenSSL and Zupt must be installed and available for their respective operations; do not infer Windows qualification from a Linux result.

## Choose the operation

| Goal | Operation | Coverage |
| --- | --- | --- |
| Record file integrity without changing content | `snapshot` | All regular-file formats, with explicit metadata/VCS exclusions |
| Authenticate an integrity reference and its history | Hybrid `sign`, then `audit` | Snapshot plus both signatures and independent trusted key pins |
| Export confidential project data | `bundle` | Explicit recipient-encrypted archive of the selected tree |
| Add removable provenance comments | `mark` | Supported first-party source formats only |
| Look for possible source copies | `compare` | Mark, exact-content, and token-sketch candidates |

## Take a file snapshot

Work on a stable tree. Keep signing keys, recipient private keys, passphrase files, and output archives outside it.

```sh
python3 codemark.pyz snapshot /project --json
python3 codemark.pyz snapshot /project --apply --json
python3 codemark.pyz verify /project --json
```

The first command previews; the second saves `.codemark/integrity.json`. JSON, hidden and extensionless files, binaries, and ISOs are covered as regular bytes. Read the exclusions and limits in [Integrity](integrity.md). Unsigned verification checks differences without authenticating the reference.

## Add authentication

Use existing ML-DSA-87 and Ed25519 PEM keys, then verify with both independently trusted complete fingerprints:

```sh
python3 codemark.pyz sign /project --pq-key /outside/keys/mldsa87.pem --classical-key /outside/keys/ed25519.pem --json
python3 codemark.pyz audit /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --json
```

This example assumes unencrypted key files protected by your key-storage policy. Encrypted keys require a shared `--passphrase-file`; there is no interactive prompt. Read [Signing](signing.md) before use. Save the returned checkpoint independently when you need to detect rollback to an older valid chain; see [Traceability](traceability.md).

## Optional source comments

Choose a first-party source module with passing project tests:

```sh
python3 codemark.pyz mark /first-party-module --owner "Your name or organization"
python3 codemark.pyz mark /first-party-module --owner "Your name or organization" --apply
python3 codemark.pyz unmark /first-party-module --apply
```

`mark` and `unmark` preview without `--apply`. Comments are removable and do not change the source license. Run the project's tests after marking. Source-comment coverage does not extend to binaries or JSON. If you also need an all-file snapshot, take it after completing your intended source edits.

The optional Tkinter interface opens with `python3 codemark.pyz gui` and handles the legacy source-comment workflow. Use the CLI for whole-file inventories and hybrid attestations.

Continue with [CLI reference](cli.md), [encrypted exports](encryption.md), and [Security](security.md).
