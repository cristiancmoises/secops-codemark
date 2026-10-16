# Formats and coverage

## Two references

| Path | Purpose |
| --- | --- |
| `.codemark/integrity.json` | All-regular-file snapshot: paths, sizes, modes, SHA-256 and SHA-512 |
| `.codemark/attestations.json` | Canonical linked hybrid attestation records |
| `.codemark/project.json` | Legacy source-comment project identity and declared owner |
| `.codemark/manifest.json` | Legacy source hashes and token-sketch reference |
| `.codemark/manifest.json.sshsig` | Optional legacy OpenSSH signature |
| `.codemark/manifest.json.asc` | Optional legacy OpenPGP signature |
| `.codemark/lock` | Operation lock; do not commit |

Do not reformat an authenticated snapshot: signatures bind the digests of its exact bytes. A history record binds both snapshot digests, project identity, sequence, previous canonical record SHA-512, local time, version and both signer fingerprints. See [Traceability](../traceability.md).

Snapshot coverage is regular files regardless of extension or encoding, with `.codemark` and VCS components explicitly excluded. Private bundles include those regular-file directories as well. Neither operation should be confused with the narrower source-comment formats below.

## Legacy source provenance comment

The existing wire format remains `CodeMark v1` for compatibility despite the SecOps Codemark display name:

```scheme
;; CodeMark v1 project=<uuid> file=<id> owner="Your organization"
```

A comment contains format version, project UUID, file identifier and JSON-quoted owner. Recognized shebangs, encoding declarations, XML declarations, CSS charset directives, supported editor cookies, UTF-8 BOM and CRLF are preserved. Existing copyright and license notices remain.

## Source-comment families

| Style | Examples |
| --- | --- |
| `#` | Python, shell, Ruby, Perl, PowerShell, Nix, YAML, TOML, CMake |
| `;;` | Scheme, Emacs Lisp, Common Lisp, Clojure, Racket |
| `//` | JavaScript, TypeScript, C/C++, Rust, Go, Java, C#, Kotlin, Swift, Dart |
| `/* … */` | CSS, SCSS, Less |
| `<!-- … -->` | HTML, XML, SVG, Vue, Svelte |
| `--` | SQL, Lua |

This is comment-format coverage, not compiler qualification for every language. JSON, PHP, binaries, other encodings, minified packages, signed PowerShell and protected isolated prologues remain outside source marking; regular-file snapshots can still hash their bytes.

Known dependency/build directories are excluded from source marking, not automatically from full snapshots or private bundles. Keep third-party source outside any module you mark as your own. Read source marking's `skipped` entries and snapshot's explicit `excluded` list.

## Similarity sketches

Approximate source comparison ignores comments and normalizes variable/function names while retaining literals, keywords and operations. It uses groups of five tokens, up to 256 hashes and Jaccard similarity, requiring at least 40 tokens and eight fingerprints.

A score describes these bounded sketches, not semantic equivalence, copied-line percentage or a plagiarism finding. Compare tools only within the stated input, configuration and measured scope; see [Evidence](../evidence.md).
