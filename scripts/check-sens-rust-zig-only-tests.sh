#!/usr/bin/env bash
# Canonical release policy: semantic tests and benchmarks must execute through
# Rust, Zig, or the native SENS runtime. Python unit suites and Python-driven
# benchmark runners are excluded and never reported as passing evidence.
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
echo "EXECUTION_LANGUAGE_POLICY=PASS allowed=Rust,Zig,SENS python_tests=EXCLUDED python_benchmarks=EXCLUDED native_replacements=REQUIRED"
