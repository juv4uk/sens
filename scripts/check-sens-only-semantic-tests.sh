#!/usr/bin/env bash
# Language policy: test and benchmark evidence may run only through Rust, Zig,
# or the native SENS runtime. Scan every active GitHub Actions workflow so a
# legacy or research workflow cannot reintroduce a foreign-language runner.
# Python/other-language test suites excluded here are NOT_VERIFIED, not PASS.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
shopt -s nullglob
files=(.github/workflows/*.yml .github/workflows/*.yaml)
if (("${#files[@]}" == 0)); then
  echo "FOREIGN_TEST_BENCH_POLICY=FAIL no_workflows_found"
  exit 1
fi
pattern='^[[:space:]]*(run:[[:space:]]*)?(python3|python|pytest)[[:space:]]+(-m[[:space:]]+(unittest|pytest)([[:space:]]|$)|(-O[[:space:]]+)?tests/test_[^[:space:]]+\.py([[:space:]\\]|$)|benchmarks/[^[:space:]]+\.py([[:space:]\\]|$)|scripts/test_[^[:space:]]+\.py([[:space:]\\]|$))|^[[:space:]]*pytest([[:space:]]|$)|^[[:space:]]*(node[[:space:]]+--test|npm[[:space:]]+(test|run[[:space:]]+(test|bench|benchmark))|go[[:space:]]+test([[:space:]]|$)|bundle[[:space:]]+exec[[:space:]]+(rspec|rake[[:space:]]+test)|phpunit([[:space:]]|$)|prove([[:space:]]|$))'
if grep -nHE "$pattern" "${files[@]}"; then
  echo "FOREIGN_TEST_BENCH_POLICY=FAIL runner_language_not_allowed"
  exit 1
fi
echo "FOREIGN_TEST_BENCH_POLICY=PASS workflows=${#files[@]} allowed=Rust,Zig,SENS foreign_tests=EXCLUDED foreign_benchmarks=EXCLUDED native_equivalence=REQUIRED"
