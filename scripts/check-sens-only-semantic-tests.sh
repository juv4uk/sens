#!/usr/bin/env bash
# Owner allowlist for test/benchmark evidence: Rust, Zig, native SENS, Guile, C,
# and Assembler. Scan all active GitHub Actions workflows for other-language
# runners. Excluded runner references are NOT_VERIFIED, never evidence of PASS.
set -euo pipefail

print_archive_summary() {
  if [[ -f docs/language-policy-archive.md ]]; then
    archive_n="$(grep -cE '\| ARCHIVE \|' docs/language-policy-archive.md || true)"
    echo "ARCHIVE (поза мовним коридором): ${archive_n} артефактів — docs/language-policy-archive.md"
  else
    echo "ARCHIVE (поза мовним коридором): MISSING_REGISTRY — docs/language-policy-archive.md"
  fi
}
root="$(git rev-parse --show-toplevel)"
cd "$root"
shopt -s nullglob
files=(.github/workflows/*.yml .github/workflows/*.yaml)
if (("${#files[@]}" == 0)); then
  echo "FOREIGN_TEST_BENCH_POLICY=FAIL no_workflows_found"
  exit 1
fi
pattern='^[[:space:]]*(run:[[:space:]]*)?(python3?|pytest)[[:space:]]+(-m[[:space:]]+(unittest|pytest)([[:space:]]|$)|(-O[[:space:]]+)?tests/test_[^[:space:]]+\.py([[:space:]\\]|$)|benchmarks/[^[:space:]]+\.py([[:space:]\\]|$)|scripts/test_[^[:space:]]+\.py([[:space:]\\]|$))|^[[:space:]]*pytest([[:space:]]|$)|^[[:space:]]*(node[[:space:]]+--test|npm[[:space:]]+(test|run[[:space:]]+(test|bench|benchmark))|npx[[:space:]]+(jest|vitest|mocha)|bun[[:space:]]+test|deno[[:space:]]+test|go[[:space:]]+test([[:space:]]|$)|bundle[[:space:]]+exec[[:space:]]+(rspec|rake[[:space:]]+test)|ruby[[:space:]]+[^[:space:]]*test[^[:space:]]*\.rb|phpunit([[:space:]]|$)|prove([[:space:]]|$)|racket[[:space:]]+[^[:space:]]*(test|bench)|lua[[:space:]]+[^[:space:]]*(test|bench)|swift[[:space:]]+test|dotnet[[:space:]]+test|mvn[[:space:]]+test|gradle[[:space:]]+test)'
matches="$(mktemp)"
trap 'rm -f "$matches"' EXIT

if grep -nHE "$pattern" "${files[@]}" > "$matches"; then
  count="$(wc -l < "$matches" | tr -d ' ')"
  echo "EXECUTION_LANGUAGE_ALLOWLIST=Rust,Zig,SENS,Guile,C,Assembler"
  echo "FOREIGN_TEST_BENCH_POLICY=EXCLUDED runner_count=$count workflows=${#files[@]}"
  echo "FOREIGN_TEST_BENCH_EVIDENCE=NOT_VERIFIED; excluded runners are not reported as passing"
  sed -n '1,40p' "$matches"
  echo "FOREIGN_TEST_BENCH_POLICY_RESULT=SKIP_NOT_RED"
  print_archive_summary
  exit 0
fi

echo "EXECUTION_LANGUAGE_ALLOWLIST=Rust,Zig,SENS,Guile,C,Assembler"
echo "FOREIGN_TEST_BENCH_POLICY=NO_DISALLOWED_RUNNERS_FOUND workflows=${#files[@]}"
print_archive_summary
