# Validation and release evidence

A release decision must identify the version, source revision, date, environment, commands, raw results, and excluded components. Passing fixtures is evidence about those fixtures in that environment.

## Current release

The website's Evidence page is generated from `website/data/release.json`. Results remain `pending` until the release operator records measurements. That file is a publication summary; the linked reports retain the actual scope and limitations.

Do not carry a previous version's passing counts or qualification forward as evidence for changed source. Optional-tool skips remain visible. Agent review is identified as agent review and does not claim an external professional audit or certification.

## Reproduce locally

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 -I dist/codemark.pyz self-test --json
python3 scripts/build_site.py --check
```

Use the build script's actual dependencies and read any unavailable-tool errors. Execute the portable outside the repository when testing package isolation. Build reproducibility applies to the same source and declared environment; do not infer cross-platform bit-for-bit reproducibility.

## What the tests exercise

The repository contains tests for reversible marking, integrity differences, token comparisons, source prologues and byte preservation, metadata validation, report failures, CLI behavior, resource limits, package isolation, and signing backends.

The self-test creates temporary fixtures and ephemeral keys. It can execute language fixtures only when their toolchains are available. It does not exercise arbitrary user projects, all supported languages, a hostile operating system, GUI rendering, or legal claims.

## Historical 0.2.0 record

The following files are preserved as historical evidence for version 0.2.0, dated **2026-10-16 UTC**. Their original numbers and verdict apply to their stated scope, not automatically to a later release.

- [Qualification JSON](../QUALIFICATION.json)
- [Agent review after fixes](../REVIEW_0.2.0.md)
- [Historical validation narrative](../VALIDATION.md)
- [Historical operational scope](../PRODUCTION.md)

The original 0.2.0 record reports 71 tests and excludes several optional components and platforms. Read the complete record before using it. A newer release must publish its own result.
