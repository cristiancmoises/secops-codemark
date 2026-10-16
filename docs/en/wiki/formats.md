# Formats and coverage

## Provenance comment

A mark contains a format version, project UUID, file identifier, and JSON-quoted owner. The comment delimiter follows the file extension.

```scheme
;; CodeMark v1 project=<uuid> file=<id> owner="Your organization"
```

CodeMark preserves recognized shebangs, encoding declarations, XML declarations, CSS charset directives, supported editor cookies, UTF-8 BOM, and CRLF line endings. Existing copyright and license notices remain.

## Metadata directory

| Path | Meaning |
| --- | --- |
| `.codemark/project.json` | Project identity and declared owner |
| `.codemark/manifest.json` | Saved content hashes and comparison reference |
| `.codemark/manifest.json.sshsig` | Optional OpenSSH signature |
| `.codemark/manifest.json.asc` | Optional OpenPGP signature |
| `.codemark/lock` | Operation lock; do not commit |

Treat metadata as evidence with the same care as source. Keep an independent trusted copy. Removing marks leaves the prior manifest, so verification reports the resulting differences.

## Language families

| Comment style | Examples |
| --- | --- |
| `#` | Python, shell, Ruby, Perl, PowerShell, Nix, YAML, TOML, CMake |
| `;;` | Scheme, Emacs Lisp, Common Lisp, Clojure, Racket |
| `//` | JavaScript, TypeScript, C, C++, Rust, Go, Java, C#, Kotlin, Swift, Dart |
| `/* … */` | CSS, SCSS, Less |
| `<!-- … -->` | HTML, XML, SVG, Vue, Svelte |
| `--` | SQL, Lua |

This is comment-format coverage, not a language-specific compiler proof. Run your project tests after marking.

## Skipped or refused input

Only supported UTF-8 source is marked. JSON, PHP, binary and compressed data, other encodings, minified packages, signed PowerShell files, and isolated protected prologues without a newline remain outside marking coverage.

Known excluded directories include `.git`, `.hg`, `.svn`, `.codemark`, virtual environments, `node_modules`, `vendor`, `third_party`, `third-party`, `dist`, `build`, `target`, and common caches. Other third-party directories must be kept outside your selected root.

Inspect the JSON `skipped` field. Symlinks and special files are refused. See the [CLI limits](../cli.md).

## Similarity sketch

Approximate comparison ignores comments and normalizes variable and function names while retaining literals, keywords, and operations. It uses groups of five tokens, up to 256 fingerprint hashes, and Jaccard similarity. Approximate scoring requires at least 40 tokens and eight fingerprints.

A score describes these sketches. It is not a semantic proof, plagiarism verdict, or percentage of copied lines.
