# CLI reference

Run `python3 codemark.pyz --help` and `python3 codemark.pyz COMMAND --help` for the parser shipped with your artifact. Source checkouts also support `python3 -m codemark`.

## Commands

| Command | Purpose | Main options |
| --- | --- | --- |
| `mark ROOT` | Preview or apply provenance comments and update the manifest | `--owner`, `--project`, `--apply` |
| `verify ROOT` | Compare the tree with its manifest | GPG or OpenSSH verification options |
| `compare ROOT SUSPECT` | Find mark, exact-content, and token-similarity candidates | `--threshold` |
| `unmark ROOT` | Preview or remove this project's comments | `--apply` |
| `sign ROOT` | Sign an intact manifest with an existing key | `--ssh-key` or `--key` |
| `doctor` | Report runtime and optional-tool availability | `--json` |
| `self-test` | Exercise temporary fixtures on this host | `--json` |
| `gui` | Open the optional Tkinter interface | Requires a display |

`--owner` is required on the first application. Use the actual rights holder. The project name defaults to the directory name. The inserted comment neither changes the source license nor restricts removal.

## Machine-readable reports

Every command except `gui` supports `--json` and `--output NEW_FILE`. The destination must be a new file outside both the reference and suspect trees.

```sh
python3 codemark.pyz verify /project --json --output /reports/new-verification.json
python3 codemark.pyz compare /project /suspect --threshold 0.80 --json
```

The default comparison threshold is `0.65`. The threshold is a Jaccard score over bounded token-fingerprint sketches, not a percentage of copied lines. Comparison reports candidates for manual inspection.

A report is reserved, written, flushed, synchronized, and closed before a mutation is committed. A failed project transaction removes the report. Consume a report only after the process exits and check its exit code.

## Exit status

| Status | Meaning |
| --- | --- |
| `0` | Operation completed; verification intact; no comparison candidates; or no self-test failures |
| `1` | Integrity differences, comparison candidates, or a self-test failure |
| `2` | Invalid input, unavailable required tool, access failure, or interrupted operation |

A successful self-test can contain `skip` results. Inspect the structured checks rather than treating exit status alone as coverage of optional tools.

## Resource limits

| Resource | Limit per operation |
| --- | --- |
| Supported source files | 5,000 |
| Bytes per source | 2 MiB |
| Combined source bytes | 64 MiB, excluding mark overhead |
| Directory entries | 20,000 |
| Directory depth | 64 levels |
| Comparison pairs | 2,000,000 |
| Comparison candidates | 10,000 |
| Metadata | 64 MiB |

Exceeding a limit raises an error. A partial search is not presented as complete. Select a smaller first-party module when needed. See [formats and coverage](wiki/formats.md).
