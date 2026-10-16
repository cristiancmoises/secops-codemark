# Get started

CodeMark adds a reversible provenance comment to source files, records SHA-256 integrity, and searches for possible source copies. It runs locally with Python 3.10 or newer and the standard library. The CLI does not need a network connection, an AI model, or a pip dependency.

## Install and inspect

Download the portable `codemark.pyz` from a verified project release, or run the source checkout with `python3 -m codemark`. Verify a downloaded artifact against a checksum obtained from a trusted channel. A checksum alone does not authenticate its publisher.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
```

The self-test uses temporary fixtures and ephemeral signing keys. Read every `skip`: an absent optional tool has not passed a test. The self-test does not certify your project or every supported language.

## Preview a first-party module

Start with a clean, versioned checkout and working project tests. Select a directory containing your own source. Keep vendored libraries, generated files, signed source formats, and private keys outside it.

```sh
python3 codemark.pyz mark /path/to/project --owner "Your name or organization"
```

Without `--apply`, `mark` only previews the operation. Inspect the file list and the `skipped` entries in JSON before proceeding.

```sh
python3 codemark.pyz mark /path/to/project --owner "Your name or organization" --apply
python3 codemark.pyz verify /path/to/project --json
```

Run your project's tests after marking. Commit the intended marked sources and `.codemark/project.json` and `.codemark/manifest.json`. Keep `.codemark/lock` out of version control. Preserve an independent reference copy.

## After legitimate edits

Review your changes, run `mark /path/to/project --apply`, and run your project's tests again. If you use signing, sign the new manifest again. An earlier signature does not authenticate a replacement manifest.

## Remove comments

```sh
python3 codemark.pyz unmark /path/to/project
python3 codemark.pyz unmark /path/to/project --apply
```

The first command previews. The second removes only this project's marks while preserving later source edits. The old manifest remains and verification will report missing marks. Use Git or a backup to recover an earlier source version.

## Optional local interface

```sh
python3 codemark.pyz gui
```

The interface requires Tkinter and a graphical session. On Windows, replace `python3` with `py -3`. Platform qualification and optional-component results are listed in [Validation](validation.md).

Continue with the [CLI reference](cli.md), [signing guide](signing.md), and [security model](security.md).
