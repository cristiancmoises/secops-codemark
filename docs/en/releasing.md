# Build and publish a release

Use a reviewed, clean checkout and Python 3.10+. A public source archive additionally requires native Zupt 5.2.10+. The commands below use a POSIX shell and new temporary directories; on Windows, use equivalent quoted paths and run multiline Python as a saved script.

## Review inputs and choose fresh outputs

Inspect `git status --short --untracked-files=all`, the selected source directories and the actual files to be shipped. Keep keys, credentials, private histories and unrelated data outside them. Filename screening does not prove absence of secrets inside ordinary source files.

Version 0.4.1 rejects linked source roots and conflicting release targets before packaging. Use a fresh output for every attempt. Do not delete or replace an existing artifact merely to make a retry pass. A native archiver or archive-test failure can leave incomplete output; retain its diagnostic log and start a new attempt elsewhere.

## Build and exercise the portable

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py --output /tmp/secops-codemark-release-0.4.1 --archive
python3 -I /tmp/secops-codemark-release-0.4.1/codemark.pyz self-test --json
zupt test /tmp/secops-codemark-release-0.4.1/secops-codemark-0.4.1.zupt
```

Run the portable from a working directory outside the source checkout as well. Record tool versions, exits, optional-tool skips and the exact source revision. The public source package is a genuine unencrypted `.zupt`; the Python executable remains `codemark.pyz`.

Extract the source package into a new verification directory and compare every tracked file byte for byte with the intended revision. Permit only the two generated additions: `codemark.pyz` and the internal `SHA256SUMS`. Verify the internal checksum list covers all source files and the included portable, and that this portable equals the standalone asset. Reject missing, extra or changed files. Native Zupt 5.2.10 does not restore POSIX modes or ACLs; this comparison qualifies bytes.

## Stage downloads before the strict site check

The site builder creates documentation and local download links. It does not build release archives. Its strict `--check` must fail when a declared local download is absent. First build a clean site directory:

```sh
python3 scripts/build_site.py --output /tmp/secops-codemark-site-0.4.1
```

Verify the two asset checksums and copy all three release files to its new downloads directory:

```sh
python3 - <<'PY'
import hashlib
import shutil
from pathlib import Path

release = Path('/tmp/secops-codemark-release-0.4.1')
downloads = Path('/tmp/secops-codemark-site-0.4.1/downloads')
rows = [line.split('  ', 1) for line in (release / 'SHA256SUMS').read_text().splitlines()]
checks = {name: digest for digest, name in rows}
assert len(rows) == len(checks) == 2
assert set(checks) == {'codemark.pyz', 'secops-codemark-0.4.1.zupt'}
for name, expected in checks.items():
    assert hashlib.sha256((release / name).read_bytes()).hexdigest() == expected
downloads.mkdir(parents=True, exist_ok=False)
for name in (*checks, 'SHA256SUMS'):
    shutil.copyfile(release / name, downloads / name)
PY
python3 scripts/build_site.py --output /tmp/secops-codemark-site-0.4.1 --check
```

Checksum agreement detects differences against that list; it does not independently authenticate the publisher. Keep the source revision and expected published hashes in a trusted release record. An explicit download `path` in site metadata may instead copy a regular file from `dist/`; local URLs still have to match the filename.

The generator rejects duplicate report filenames and route stems before writing the site. Different extensions do not make two reports with the same stem safe to publish at one route.

## Publication gates

- Require the full test run, portable checks, source review and the final Linux/Windows CI matrix for the intended revision. Preserve failures and skips accurately.
- Record new evidence for changed source. Historical similarity and pipeline measurements keep their original versions and hashes.
- Confirm the source tree, archive contents and release metadata contain no private execution material or credentials. Review ordinary source contents as well as filenames.
- Create a new annotated tag through the configured Git identity. Push reviewed commits and the new tag to the intended verified accounts; preserve existing refs and releases.
- Publish the genuine unencrypted `.zupt`, `codemark.pyz` and `SHA256SUMS`, then download and hash every published asset. Native external Forgejo assets may reference verified versioned files on another forge; disclose that hosting explicitly.
- Activate only a checked static site, using an atomic directory switch and retaining the previous release. Verify both languages, reports, HTTPS headers and exact public download bytes after activation. Use a real browser for layout, keyboard and reduced-motion checks.

See [Validation](validation.md), [Integration](integration.md) and the [website build reference](../../website/README.md).
