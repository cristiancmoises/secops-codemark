# CODEMARK

**Local source provenance, integrity verification, and copy-candidate analysis.**

[Português brasileiro](README.pt-BR.md) · [Documentation](https://codemark.securityops.co/en/docs/) · [Wiki](https://codemark.securityops.co/en/wiki/) · [Release evidence](https://codemark.securityops.co/en/evidence/)

CodeMark adds reversible provenance comments to your source files, records a SHA-256 manifest, optionally signs that reference, and searches another tree for possible source copies. The CLI runs offline with **Python 3.10+ and its standard library**. No AI model, telemetry, server, or pip dependency is required.

Version **0.3.0** · **GPL-3.0-or-later** · [Full license](COPYING)

A mark can be removed or forged. A signature binds a manifest to a pinned key; it does not prove a trusted date, originality, or legal ownership. Similarity reports are leads for manual review. Marking does not change a project's license or prevent reverse engineering.

## Get started

Download the portable `codemark.pyz` or the genuine `.zupt` source release from the [project downloads](https://codemark.securityops.co/en/downloads/). Verify SHA-256 checksums against a trusted reference. Extract source releases with `zupt`; the portable needs only Python.

```sh
python3 codemark.pyz --version
python3 codemark.pyz doctor --json
python3 codemark.pyz self-test --json
```

Read each self-test `skip`: an unavailable optional tool is not validated. The test uses temporary fixtures and ephemeral keys, not your project source or signing keys. See the current [release evidence](https://codemark.securityops.co/en/evidence/) for measured scope and limitations.

Start with a clean, versioned first-party module and passing project tests. Preview before applying:

```sh
python3 codemark.pyz mark /path/to/project --owner "Your name or organization"
python3 codemark.pyz mark /path/to/project --owner "Your name or organization" --apply
python3 codemark.pyz verify /path/to/project --json
```

Run your project's tests again. Commit the intended marked files and `.codemark/project.json` and `.codemark/manifest.json`. Keep `.codemark/lock` out of version control. Preserve an independent reference copy. Later applications can omit `--owner`.

Source checkouts can use `python3 -m codemark` instead of `python3 codemark.pyz`. On Windows, replace `python3` with `py -3`.

## Compare and remove

```sh
python3 codemark.pyz compare /project /suspect --threshold 0.80 --json
python3 codemark.pyz unmark /project
python3 codemark.pyz unmark /project --apply
```

Comparison detects matching identifiers, identical unmarked content, and approximate token fingerprints. It can find candidates with renamed files and some renamed identifiers. Scores describe bounded token sketches, not percentages of copied lines. False positives and false negatives are possible.

`unmark` previews by default and preserves later edits when applied. The prior manifest remains, so `verify` reports the removed marks. Use Git or backups to recover earlier versions.

## Authenticate a reference

Optional OpenSSH Ed25519 signing requires local `ssh-keygen` with `-Y`. Use an existing private key outside the project and its adjacent `.pub` file:

```sh
python3 codemark.pyz sign /project --ssh-key ~/.ssh/codemark-signing
ssh-keygen -l -E sha256 -f ~/.ssh/codemark-signing.pub
python3 codemark.pyz verify /project --ssh-public-key ~/.ssh/codemark-signing.pub --ssh-fingerprint 'SHA256:YOUR_COMPLETE_FINGERPRINT'
```

Replace the example with your complete trusted fingerprint. CodeMark pins the key and `codemark-manifest-v1` namespace. Optional OpenPGP signing is also available. Read [Signing](docs/en/signing.md) before use, including key trust and revocation limits.

## Automation and coverage

| Exit | Meaning |
| --- | --- |
| `0` | Completed; intact; no candidates; or self-test without failures |
| `1` | Integrity differences, comparison candidates, or self-test failures |
| `2` | Input, access, required-tool, or interruption error |

Use `--json --output /reports/NEW.json` for a new report outside both checked trees. Consume it after the command exits and inspect the status. In CI, verify the reviewed reference; running `mark --apply` before verification would accept the current changes as the baseline.

Supported comment styles cover Python, shell, Scheme/Lisp, JavaScript/TypeScript, C/C++, Rust, Go, Java, CSS, HTML/XML, SQL, Lua, YAML, TOML, and others. This is comment-format coverage, not compilation qualification for every language. Supported UTF-8/BOM and CRLF inputs are preserved. JSON, PHP, binaries, minified packages, and specially signed formats are outside marking coverage. Inspect `skipped` in the JSON report.

Known dependency/build directories are excluded. Symlinks and special files are refused. Limits include 5,000 sources, 2 MiB per source, 64 MiB total, 20,000 entries, and bounded comparisons. Work on a stable tree; ordinary rollback does not provide crash recovery after power loss or forced termination. See [Formats](docs/en/wiki/formats.md) and [Security](docs/en/security.md).

The optional Tkinter GUI opens with `python3 codemark.pyz gui` and needs a graphical session. Optional components and platform qualification are reported separately.

## Documentation

| Topic | English | Português brasileiro |
| --- | --- | --- |
| Start | [Get started](docs/en/getting-started.md) | [Primeiros passos](docs/pt-BR/getting-started.md) |
| Commands | [CLI reference](docs/en/cli.md) | [Referência da CLI](docs/pt-BR/cli.md) |
| Signatures | [Signing](docs/en/signing.md) | [Assinaturas](docs/pt-BR/signing.md) |
| CI and releases | [Integration](docs/en/integration.md) | [Integração](docs/pt-BR/integration.md) |
| Security | [Threat model](docs/en/security.md) | [Modelo de segurança](docs/pt-BR/security.md) |
| Measured results | [Validation](docs/en/validation.md) | [Validação](docs/pt-BR/validation.md) |
| Wiki | [Architecture](docs/en/wiki/architecture.md) | [Arquitetura](docs/pt-BR/wiki/architecture.md) |

Historical 0.2.0 qualification and review records remain explicitly versioned. They do not qualify changed source in a later release. Current results, skips, report dates, and scopes are published on the [Evidence page](https://codemark.securityops.co/en/evidence/).

## Develop

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/build_site.py --check
```

The build produces a deterministic portable executable, source staging tree, and SHA-256 manifest. `python3 scripts/build.py --archive` additionally uses installed `zupt` to create a genuine `.zupt` source archive. Read [Contributing](CONTRIBUTING.md) and [Security](SECURITY.md).

The documentation site uses static HTML, CSS, and local SVG assets with no JavaScript. Build it with Python's standard library; see [website/README.md](website/README.md).

## Source repositories

- [GitHub · cristiancmoises/codemark](https://github.com/cristiancmoises/codemark)
- [Codeberg · berkeley/codemark](https://codeberg.org/berkeley/codemark)
- [Security Ops Forgejo · git.securityops.co](https://git.securityops.co/cristiancmoises/codemark)
- [Security Ops Forgejo · git.securityops.com.br](https://git.securityops.com.br/cristiancmoises/codemark)

Copyright (C) 2026 CodeMark contributors. Free software under the GNU GPL version 3 or any later version, distributed without warranty. Existing licenses of marked projects remain in force.
