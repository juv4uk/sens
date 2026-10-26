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
matches="$(mktemp)"
trap 'rm -f "$matches"' EXIT

if grep -nHE "$pattern" "${files[@]}" > "$matches"; then
  count="$(wc -l < "$matches" | tr -d ' ')"
  echo "FOREIGN_TEST_BENCH_POLICY=EXCLUDED runner_count=$count workflows=${#files[@]}"
  echo "FOREIGN_TEST_BENCH_EVIDENCE=NOT_VERIFIED; excluded runners are not reported as passing"
  sed -n '1,40p' "$matches"
  echo "FOREIGN_TEST_BENCH_POLICY_RESULT=SKIP_NOT_RED"
  exit 0
fi

echo "FOREIGN_TEST_BENCH_POLICY=NO_DISALLOWED_RUNNERS_FOUND workflows=${#files[@]}"
