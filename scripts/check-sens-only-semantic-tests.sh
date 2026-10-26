#!/usr/bin/env bash
# Enforce the language boundary: no Python unit-test runner in canonical CI.
# Python may remain as mechanical tooling; SENS semantic evidence must be native.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
files=(.github/workflows/ci.yml .github/workflows/release-preflight.yml)
if grep -nE '^[[:space:]]*(run:[[:space:]]*)?python3[[:space:]]+-m[[:space:]]+(unittest|pytest)([[:space:]]|$)|^[[:space:]]*python3[[:space:]]+tests/test_[^[:space:]]+\.py([[:space:]]|$)|^[[:space:]]*pytest([[:space:]]|$)' "${files[@]}"; then
  echo "SENS_LANGUAGE_BOUNDARY=FAIL python_unit_test_runner_in_release_path"
  exit 1
fi
echo "SENS_LANGUAGE_BOUNDARY=PASS semantic_authority=SENS python_unit_tests=EXCLUDED native_equivalence=NOT_VERIFIED"
