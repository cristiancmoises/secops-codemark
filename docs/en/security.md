# Security model

CodeMark records a relationship between a source tree, a declared identity, and a particular content reference. It is a provenance and integrity tool, with heuristic source-copy triage.

## What each layer means

| Layer | Provides | Limit |
| --- | --- | --- |
| Provenance comment | A project and file identifier that survives renaming | Removable and forgeable |
| SHA-256 manifest | Integrity differences against the saved reference | An unsigned local manifest can also be edited |
| Pinned-key signature | Authentication of that manifest against one key | No legal ownership, trusted date, or originality proof |
| Normalized token sketch | Candidates after some identifier and comment changes | False positives and negatives; per-file approximation |

Public code remains available for study and copying under its license. A comment does not block reverse engineering, decompilation, or independent reimplementation. Source licenses and existing copyright notices remain applicable.

## Operational boundary

Work on a stable local tree with no concurrent editors or builds writing to it. Symlinks in the selected path or tree, special files, malformed metadata, and resource-limit violations are refused. Known dependency and build directories are excluded without traversal.

Operations use per-file replacement and rollback for ordinary errors. Forced termination or loss of power can leave a partial state. Keep a recoverable commit or backup. Remove a stale `.codemark/lock` only after confirming no operation is active.

The filesystem and local account are trusted. A hostile kernel, deliberate filesystem races, a stolen signing key, compromised CI, and a replaced verification executable are outside this boundary.

## Privacy and key handling

The CLI does not upload source, call an AI model, or require a network connection. It does not scan secrets. A manifest can reveal relative file paths, the declared owner, and content fingerprints; review metadata before sharing it.

Use existing signing keys and keep their private files outside the project. CodeMark delegates signing to local OpenSSH or GnuPG facilities. Manage rotation and revocation independently; no online revocation service is queried.

## Interpreting a match

A match is a lead for inspection. Common boilerplate can match. Rewritten, split, merged, or independently implemented code can fail to match. A similarity score is not a legal finding or a literal fraction of copied source.

## Report a vulnerability

Follow the repository's [security policy](../../SECURITY.md). Never include private keys, credentials, private project source, or another person's personal data in a public report.

The [evidence page](validation.md) distinguishes current release checks from historical reports. No audit record is a guarantee that defects do not exist.
