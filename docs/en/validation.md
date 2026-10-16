# Validation and release evidence

A release decision must identify the version, source revision, date, environment, commands, raw results, and excluded components. Passing fixtures is evidence about those fixtures in that environment.

## Current release

The website's Evidence page is generated from `website/data/release.json`. Results remain `pending` until the release operator records measurements. That file is a publication summary; the linked reports retain the actual scope and limitations.

Do not carry a previous version's passing counts or qualification forward as evidence for changed source. Optional-tool skips remain visible. Agent review is identified as agent review and does not claim an external professional audit or certification.

Version 0.4.1 corrects release packaging and website report routing while preserving the 0.4.0 runtime formats. It has its own test, portable and review records. Native-tool and platform qualification must identify the exact measured source.

## Reproduce locally

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py --output /tmp/codemark-validation-0.4.1
python3 -I /tmp/codemark-validation-0.4.1/codemark.pyz self-test --json
```

Use a new output directory for each build. Stage the release downloads before running the strict website check; see the [release workflow](releasing.md).

Use the build script's actual dependencies and read any unavailable-tool errors. Execute the portable outside the repository when testing package isolation. Build reproducibility applies to the same source and declared environment; do not infer cross-platform bit-for-bit reproducibility.

## What the tests exercise

The repository contains tests for reversible marking, byte preservation, token candidates, metadata and report failures, all-file inventory, limits, package isolation, hybrid signatures, independent key pins and linked-history checks. Consult the current logs for the exact executed cases, tool versions and skips. Private-export and platform results must be recorded separately.

The self-test creates temporary fixtures and ephemeral keys. It can execute language fixtures only when their toolchains are available. It does not exercise arbitrary user projects, all supported languages, a hostile operating system, GUI rendering, or legal claims.

## Historical 0.4.0 record

The 0.4.0 [qualification](../reports/0.4.0-validation.json), [test log](../reports/0.4.0-tests.txt), [portable checks](../reports/0.4.0-self-test.json) and [focused review](../reports/0.4.0-review.md) retain their original source revisions and scope. Its similarity and pipeline measurements remain historical experiments, with their exact tool and source hashes. They do not replace 0.4.1 release checks.

## Historical 0.3.0 record

These records apply to version 0.3.0 and are dated **2026-10-16 UTC**. Its recorded qualification covers the local GNU/Linux CLI; Windows and GUI rendering were excluded. They remain unchanged as historical evidence.

- [Qualification JSON](../reports/0.3.0-validation.json)
- [Complete test log](../reports/0.3.0-tests.txt)
- [Portable checks](../reports/0.3.0-self-test.json)
- [Focused source and packaging review](../reports/0.3.0-review.md)
- [Website validation](../reports/0.3.0-website.json)

The 0.3.0 record reports 81 GNU/Linux tests and nine portable checks. Those results apply to the original source and environment, not changed source in later releases.

## Historical 0.2.0 record

The following files are preserved as historical evidence for version 0.2.0, dated **2026-10-16 UTC**. Their original numbers and verdict apply to their stated scope, not automatically to a later release.

- [Qualification JSON](../QUALIFICATION.json)
- [Agent review after fixes](../REVIEW_0.2.0.md)
- [Historical validation narrative](../VALIDATION.md)
- [Historical operational scope](../PRODUCTION.md)

The original 0.2.0 record reports 71 tests and excludes several optional components and platforms. Read the complete record before using it. A newer release must publish its own result.
