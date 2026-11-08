#!/bin/sh
# Capture the evidence files a reader needs; run from a clean clone at the freeze.
set -e
cd "$(dirname "$0")/.."
mkdir -p docs/evidence
{ echo "# make check, $(date -u +%Y-%m-%dT%H:%M:%SZ), commit $(git rev-parse --short HEAD)"; make check 2>&1; } | tee docs/evidence/make-check.txt
{ echo "# make demo, $(date -u +%Y-%m-%dT%H:%M:%SZ), commit $(git rev-parse --short HEAD)"; /usr/bin/time -p make demo 2>&1; } | tee docs/evidence/make-demo.txt
git ls-files | grep -v "^data/acaps-api/\|^ui/package-lock" > docs/evidence/tree.txt
echo "evidence written to docs/evidence/"
