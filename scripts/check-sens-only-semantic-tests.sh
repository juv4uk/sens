#!/usr/bin/env bash
# Foreign-language test/benchmark runners may not be treated as SENS evidence.
# Mechanical Python helpers outside this forbidden runner set are tooling only.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
files=(
  .github/workflows/ci.yml
  .github/workflows/ci-heavy.yml
  .github/workflows/release-preflight.yml
  .github/workflows/release.yml
  .github/workflows/bija123-recursive-cube.yml
  .github/workflows/bija3-pure-cube.yml
  .github/workflows/cross-language-native-baseline.yml
  .github/workflows/lisp-vs-sens-bench.yml
  .github/workflows/lisp-vs-sens-speed.yml
  .github/workflows/physical-sens-benchmark.yml
  .github/workflows/physical-binary-performance.yml
  .github/workflows/packed-vs-visible-bench.yml
)
if grep -nE '^[[:space:]]*(run:[[:space:]]*)?python3[[:space:]]+-m[[:space:]]+(unittest|pytest)([[:space:]]|$)|^[[:space:]]*python3[[:space:]]+tests/test_[^[:space:]]+\.py([[:space:]]|$)|^[[:space:]]*pytest([[:space:]]|$)|^[[:space:]]*python3[[:space:]]+benchmarks/[^[:space:]]+.*(run\.py|\.py)([[:space:]\\]|$)|^[[:space:]]*python3[[:space:]]+-[[:space:]]+<<'PY'([[:space:]]|$)' "${files[@]}"; then
  echo "FOREIGN_TEST_BENCH_POLICY=FAIL runner_language_not_allowed"
  exit 1
fi
echo "FOREIGN_TEST_BENCH_POLICY=PASS runners=Rust,Zig,SENS foreign_python_test_bench=EXCLUDED"
