# Integrate with a release workflow

SecOps Codemark is a local CLI. Keep the verifier, both trusted signer fingerprints, expected checkpoint and CI configuration protected from the untrusted contribution you are checking.

## Prepare a reference

1. Select the intended revision and run the project's tests.
2. If source comments are desired, mark only a first-party module and test it again.
3. Stop concurrent writers, preview the wider file snapshot and inspect exclusions.
4. Apply the snapshot and inspect its reported scope and digests.
5. Sign it using both existing hybrid keys kept outside the project.
6. Preserve the exact snapshot, attestation history, both independent key pins and latest checkpoint in a trusted release record.

Complete all source edits before taking the snapshot you will sign. Signing an editable local manifest without checking its source is not a review process.

## Verify in CI

```sh
python3 /trusted/codemark.pyz audit /checkout --pq-fingerprint 'SHA256:YOUR_MLDSA87_FINGERPRINT' --classical-fingerprint 'SHA256:YOUR_ED25519_FINGERPRINT' --checkpoint YOUR_COMPLETE_LOWERCASE_SHA512_CHECKPOINT --json
```

Use the full expected checkpoint from a trusted release record. Check out the exact intended revision and interpret both authentication and current-tree integrity. Do not refresh a snapshot or run `mark --apply` before a verification gate: doing so accepts current changes as a new baseline.

Windows jobs use `py -3`, native quoted paths and installed compatible external tools. Platform and provider availability are separate evidence, not implied by Linux success. See [Validation](validation.md).

## Reusable pipeline example

The repository includes a [small shell verification stage](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.1/examples/pipeline/verify-release.sh), a [manual GitHub Actions workflow](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.1/examples/pipeline/verify-release.yml) and [configuration guidance](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.1/examples/pipeline/README.md).

The stage requires six protected settings: `CODEMARK_PYZ`, `RELEASE_DIR`, `PQ_FINGERPRINT`, `CLASSICAL_FINGERPRINT`, `CHECKPOINT` and `AUDIT_REPORT`. Provide a checksum-verified portable, a prepared tree and compatible OpenSSL 3.5. It needs public trust values, not a private signing key.

The workflow is manually triggered and fails closed when required inputs or crypto capabilities are unavailable. Supply your own trusted artifact acquisition stage; the example does not fetch a release or install the crypto backend. Review the pinned actions and protected configuration in your own repository before use. Measured stage time and configuration size are distinct from human setup or maintenance time.

## Measured integration example

The [reproducible pipeline measurement](https://github.com/cristiancmoises/secops-codemark/blob/v0.4.0/examples/pipeline/measure.py) used three original fixture files totaling 2,097,184 bytes, including an extensionless executable, JSON and a binary image. Five local runs used Python 3.12.12 and OpenSSL 3.5.7 in a networkless GNU/Linux namespace. [Raw samples and tool hashes](../reports/0.4.0/pipeline-results.json) preserve the workload and failures.

| Stage | Median wall time | Observed range |
| --- | --- | --- |
| Snapshot | 0.071 s | 0.062–0.095 s |
| Hybrid sign | 0.210 s | 0.124–0.262 s |
| Authenticated audit | 0.110 s | 0.090–0.161 s |

The actual shell example also passed and saved a matching report. The experiment rejected changed JSON with exit 1, a stale checkpoint after an intended update with exit 2, and missing trusted pins with exit 2. A reviewed update verified after taking a new snapshot, signing and independently advancing the expected checkpoint.

The verification stage has **16 shell lines, 27 workflow lines, six required environment settings and one verification command**. The verifier holds no signing private key. Artifact retrieval, portable checksum verification, crypto installation, runner policy and protected configuration are additional integration work.

These are process wall times for a small controlled fixture, including Python startup and native signature operations. The five signing runs extend one history, so later runs verify more records. Key generation and dependency installation are excluded. No human onboarding time or long-term maintenance duration was measured. Use the [effort worksheet](../reports/0.4.0/integration-effort-template.csv) to record those observations in your own pipeline.

```sh
python3 examples/pipeline/measure.py --codemark dist/codemark.pyz --output /reports/pipeline-NEW.json --repeats 5
```

## Save reports

```sh
python3 codemark.pyz verify /checkout --json --output /reports/verification-NEW.json
```

Use a new report outside the checked trees, wait for completion and record the exit status. This example is an unauthenticated integrity report; use the audit command with both pins and expected checkpoint for an authenticated gate.

## Public and private archives

Public project releases are genuine unencrypted `.zupt` archives with SHA-256 checksums. They must be tested and extracted against the intended source revision before publishing.

For an explicit confidential export, use [Bundle encryption](encryption.md). That tree includes regular files in version-control directories and `.codemark`, so inspect its contents and keep private keys and passphrase files outside it. A private archive and its public source release have different purposes.

Native Zupt 5.2.10 extraction uses the current umask rather than restoring POSIX modes. See [restoration and verification](encryption.md#restore-and-verify) before an audit; byte equality does not qualify ACL or mode preservation.

## Maintenance responsibilities

| Trigger | Operator action |
| --- | --- |
| Intended file changes | Review changes, run project tests, refresh the snapshot and sign the new reference |
| Approved release | Retain both trusted key pins and the exact expected latest checkpoint independently |
| Key compromise or rotation | Review trust transitions and update protected verification policy through a trusted channel |
| OpenSSL or Zupt update | Re-run the relevant positive and negative tests in the target environment |
| Private export | Inspect the selected tree, recipient fingerprint and restored-byte result |

There is no SecOps Codemark runtime server to administer. Full-tree hashing reads the selected bytes; signing, key custody, checkpoint retention and dependency updates still require maintenance. Any measured time or cost belongs to the published environment and workload, not a universal estimate.

## GNU Guix and optional components

The base CLI uses Python from your profile. For example:

```sh
guix shell python -- python3 codemark.pyz doctor --json
```

Hybrid signing additionally needs compatible OpenSSL, legacy signing needs its corresponding tools, and private bundles need Zupt. These are environment requirements, not a claim that a Guix package or every platform is qualified. The optional GUI needs Tkinter and a graphical session and handles legacy source comments.

For packaging and publishing SecOps Codemark itself, follow the [release workflow](releasing.md). Historical pipeline timings above retain their original workload and revision.
