#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
set -eu

: "${CODEMARK_PYZ:?Set the path to a checksum-verified codemark.pyz}"
: "${RELEASE_DIR:?Set the release directory containing .codemark metadata}"
: "${PQ_FINGERPRINT:?Set the independently trusted ML-DSA-87 fingerprint}"
: "${CLASSICAL_FINGERPRINT:?Set the independently trusted Ed25519 fingerprint}"
: "${CHECKPOINT:?Set the independently stored latest SHA-512 checkpoint}"
: "${AUDIT_REPORT:?Set a new report path outside the release directory}"

exec python3 -I "$CODEMARK_PYZ" audit "$RELEASE_DIR" \
    --pq-fingerprint "$PQ_FINGERPRINT" \
    --classical-fingerprint "$CLASSICAL_FINGERPRINT" \
    --checkpoint "$CHECKPOINT" \
    --json --output "$AUDIT_REPORT"
