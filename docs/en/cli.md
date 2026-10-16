# CLI reference

Run `python3 codemark.pyz --help` and `python3 codemark.pyz COMMAND --help` for your artifact's parser. The module name remains `codemark`; source checkouts support `python3 -m codemark`. On Windows, use `py -3` and quoted native paths.

## Commands

| Command | Purpose | Main options |
| --- | --- | --- |
| `snapshot ROOT` | Preview or save all-regular-file hashes | `--apply` |
| `sign ROOT` | Sign a reviewed reference | Hybrid `--pq-key` plus `--classical-key`; optional `--passphrase-file`; or one legacy backend |
| `verify ROOT` | Compare the tree with its saved reference | Both hybrid fingerprint pins for authentication |
| `audit ROOT` | Authenticate a snapshot and its attestation chain against the current tree | Both hybrid fingerprint pins; optional expected `--checkpoint` |
| `bundle ROOT` | Preview or create a private recipient-encrypted archive | `--recipient-key`, `--recipient-fingerprint`, `--archive`, `--apply` |
| `mark ROOT` | Preview or apply source comments and update their manifest | `--owner`, `--project`, `--apply` |
| `unmark ROOT` | Preview or remove this project's source comments | `--apply` |
| `compare ROOT SUSPECT` | Find source-copy candidates | `--threshold` |
| `doctor` | Report runtime and optional-tool availability | `--json` |
| `self-test` | Exercise temporary fixtures on this host | `--json` |
| `gui` | Open the optional legacy source-comment interface | Tkinter and a graphical session |

## Integrity and authentication modes

When `.codemark/integrity.json` exists, `verify` selects the all-regular-file reference. Without hybrid pins it reports unauthenticated integrity. `audit` requires that snapshot, its attestation history, and both complete trusted fingerprints.

```sh
python3 codemark.pyz verify /project --json
python3 codemark.pyz audit /project --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --checkpoint YOUR_COMPLETE_LOWERCASE_SHA512_CHECKPOINT --json
```

Replace the three placeholders with complete trusted values. The checkpoint is optional syntactically but required to detect replacement by an older valid chain. Read [Traceability](traceability.md).

Legacy OpenSSH/GPG verification options authenticate only the source-comment manifest and are rejected when a full snapshot is selected. Do not combine backends. See [Signing](signing.md).

## Reports and exit status

Non-GUI commands support `--json` and a new external report destination with `--output`. An archive uses its own `--archive` destination. Keep reports and archives outside checked trees and do not overwrite earlier evidence.

| Status | Meaning |
| --- | --- |
| `0` | Operation completed; intact verification; comparison without candidates; or self-test without failures |
| `1` | Integrity differences, comparison candidates, or self-test failure |
| `2` | Invalid input, required-tool or authentication error, access failure, or interruption |

Check both integrity and authentication fields. A self-test can contain explicit `skip` results; exit 0 alone does not qualify absent optional tools. Consume reports only after process termination and inspect the exit code.

## Separate resource ceilings

| Resource | All-file snapshot | Source comments and comparison |
| --- | --- | --- |
| Files | 100,000 regular files | 5,000 supported sources |
| One file | 100 GiB | 2 MiB |
| Combined bytes | 1 TiB | 64 MiB excluding comment overhead |
| Directory entries | 200,000 | 20,000 |
| Metadata | 64 MiB | 64 MiB |
| Candidate comparison | Not applicable | 2,000,000 pairs and 10,000 candidates |

These are acceptance limits, not performance benchmarks. An exceeded limit fails the operation rather than presenting incomplete coverage as complete. Hybrid history has additional ceilings: 1,000 records, 32 MiB per chain, and 32 KiB per canonical record. Key files are bounded to 1 MiB and passphrase input to 32 KiB.

Source comparison defaults to `--threshold 0.65`. Scores describe Jaccard similarity between bounded token sketches, not a percentage of copied lines. See [Formats](wiki/formats.md).
