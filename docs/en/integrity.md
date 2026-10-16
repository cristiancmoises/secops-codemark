# Inventory every regular file

`snapshot` records file bytes without inserting comments or changing their contents. It streams SHA-256 and SHA-512 for regular files regardless of extension: source, JSON, documentation, hidden files, extensionless files, images, executables, archives, and ISO images.

## Preview, then save

```sh
python3 codemark.pyz snapshot /project --json
python3 codemark.pyz snapshot /project --apply --json
```

Without `--apply`, the command produces a preview. Applying writes `.codemark/integrity.json`. Keep the project stable while it is read. Review the reported file count, total bytes, exclusions, and manifest digests before treating a snapshot as your reference.

The inventory excludes path components named `.codemark`, `.git`, `.hg`, and `.svn`, with reasons recorded. This keeps its own metadata and version-control internals outside the reference. Other directories, including build outputs and dependencies, are part of the inventory when they contain regular files. Select the root deliberately.

## Filesystem boundaries

Symlinks and special files are refused. The reader checks file identity and metadata while opening, streaming, and completing a hash; a detected concurrent change fails the operation. These checks do not make a hostile local operating system trustworthy. Stop concurrent editors, builds, and sync clients before a snapshot or verification.

A snapshot covers files, not empty directories. It is neither a backup nor a filesystem image. It records relative paths, sizes, hashes, and permission modes; restoring equivalent content on another platform can still expose mode differences.

## Verify the saved snapshot

```sh
python3 codemark.pyz verify /project --json
```

Read the report's coverage mode. In all-regular-file mode, differences include changed bytes, missing or new files, and changed permission modes. An unsigned local reference is editable by anyone who can write to it.

For an authenticated reference, use [hybrid signing](signing.md) with both independently trusted key fingerprints. Preserve the manifest's exact bytes: reformatting its JSON changes the signed reference even when the values look equivalent.

## Capacity limits

| Resource | Snapshot limit |
| --- | --- |
| One regular file | 100 GiB |
| Combined regular-file bytes | 1 TiB |
| Regular files | 100,000 |
| Directory entries | 200,000 |
| Serialized manifest | 64 MiB |

The operation fails when a ceiling is reached; it does not present a partial inventory as complete. Streaming avoids loading a whole large file into memory. Published limits describe acceptance ceilings, not measured throughput or a promise that every host can process a maximum-sized tree.

## Keep marking separate

`mark` remains a reversible comment operation for supported source formats, with its own exclusions and smaller limits. It does not mark JSON, binaries, or ISO images. You can mark selected first-party source and then snapshot the wider release tree. Complete all intended source edits before taking the reference you will sign.

See [formats](wiki/formats.md), [traceability](traceability.md), and [security](security.md).

## Filesystem metadata

Snapshots include file permission bits. Verification on another operating system or filesystem can report `mode_changed` even when bytes match. Prepare and verify the reference on the intended release filesystem; investigate differences rather than silently accepting them. POSIX mode bits do not capture Windows ACLs, extended attributes, ownership or complete operating-system access policy.
