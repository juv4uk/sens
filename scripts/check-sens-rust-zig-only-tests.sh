#!/usr/bin/env bash
# Canonical release policy: executable tests/benchmarks may use only the
# owner-approved languages/mechanisms: Rust, Zig, SENS, Guile, C, and Assembler.
# Python and all other foreign-language test/benchmark runners are excluded.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
files=(
  .github/workflows/ci.yml
  .github/workflows/release-preflight.yml
  .github/workflows/ci-heavy.yml
  .github/workflows/benchmark-registry.yml
)
if grep -nE '^[[:space:]]*(run:[[:space:]]*)?python3[[:space:]]+-m[[:space:]]+(unittest|pytest)([[:space:]]|$)|^[[:space:]]*pytest([[:space:]]|$)|python3[[:space:]]+benchmarks/[^[:space:]]+/(run|bench|test)[^[:space:]]*\.py' "${files[@]}"; then
  echo "EXECUTION_LANGUAGE_POLICY=FAIL python_test_or_benchmark_runner"
  exit 1
fi
echo "EXECUTION_LANGUAGE_POLICY=PASS allowed=Rust,Zig,SENS,Guile,C,Assembler python_tests=EXCLUDED foreign_tests=EXCLUDED python_benchmarks=EXCLUDED foreign_benchmarks=EXCLUDED native_replacements=REQUIRED"
