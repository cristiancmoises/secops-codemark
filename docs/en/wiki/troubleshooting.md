# Troubleshooting

## Integrity verification returns 1

Inspect `changed`, `missing`, `untracked`, and `invalid_marks` in the JSON report. Compare with the intended source revision. If edits were legitimate, review them before creating and signing a new reference. Preserve the old evidence if the changes are unexpected.

## Comparison returns 1

Exit 1 means candidates were found. Read the matching method and inspect the files. Shared boilerplate and independently written code can produce misleading candidates. Do not treat the exit status as a plagiarism verdict.

## A file was not marked

Read `skipped` using `--json`. Check its extension, encoding, size, prologue, dependency path, and whether it is a signed format. Select a smaller first-party module when an operation reaches its resource ceiling.

## A report cannot be written

`--output` needs a new file in an existing writable directory outside both checked trees. It never overwrites an existing report. Wait for process termination before consuming output. Check disk space and access permissions without deleting earlier evidence.

## A signature does not verify

Check the exact full fingerprint, public-key origin, current manifest, and selected backend. OpenSSH requires an Ed25519 key and the expected namespace. GPG verification needs all three options: `--require-signature`, `--keyring`, and `--fingerprint`.

A legitimate manifest refresh makes an old signature invalid. Sign the reviewed new reference. Never replace the trusted key merely to make a failed check pass.

## An operation lock remains

Confirm that no CodeMark operation is running before removing `.codemark/lock`. Inspect the tree against Git or your backup after a forced stop. Ordinary rollback does not provide recovery after power loss.

## GUI or an optional tool is unavailable

Run `doctor --json`. The GUI needs Tkinter and a graphical session. OpenSSH needs `ssh-keygen` with `-Y`; GPG needs its signing and verification executables and a usable local agent. The CLI works without the GUI. A self-test `skip` records missing coverage.

## Ask for help

Include the CodeMark and Python versions, operating system, exact command, exit status, and a small synthetic reproducer. Redact source paths if private. Follow the [security policy](../../../SECURITY.md) for sensitive defects.
