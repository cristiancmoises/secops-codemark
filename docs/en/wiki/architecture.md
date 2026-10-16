# Architecture

CodeMark separates source handling, comparison, command-line orchestration, optional signing, and the optional graphical interface. Runtime implementation uses Python's standard library.

## Modules

| Module | Responsibility |
| --- | --- |
| `codemark/core.py` | Bounded inventories, provenance comments, manifests, verification, mutations and rollback |
| `codemark/fingerprint.py` | Normalized token fingerprints and similarity |
| `codemark/cli.py` | Argument parsing, reports, exit status and command dispatch |
| `codemark/ssh_signing.py` | OpenSSH Ed25519 signatures and pinned verification |
| `codemark/signing.py` | Optional OpenPGP signing and dedicated-keyring verification |
| `codemark/selftest.py` | Temporary host fixtures and explicit optional-tool skips |
| `codemark/gui.py` | Optional Tkinter interface |

## Data flow

```text
Selected first-party tree
  -> bounded source inventory
  -> preview or reversible provenance comment
  -> SHA-256 manifest and token sketches
  -> optional signature against an existing key

Saved reference + current tree -> integrity report
Saved reference + suspect tree -> candidate comparison report
```

The comparison path reads suspect source as data. It does not execute it. The self-test executes only its own temporary fixtures.

## Trust boundary

An unsigned manifest is a local reference. Authentication needs a separately trusted public key and pinned fingerprint. The operator controls the local machine, source revision, signing keys, and CI environment.

The project has no hosted runtime backend. This documentation website is prebuilt HTML and CSS, with no JavaScript, analytics, external fonts, or third-party asset requests.

See [formats](formats.md) for storage and [security](../security.md) for limits.
