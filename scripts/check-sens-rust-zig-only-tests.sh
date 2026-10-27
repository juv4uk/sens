#!/usr/bin/env bash
# Canonical release policy: executable tests/benchmarks may use only the
# owner-approved languages/mechanisms: Rust, Zig, SENS, Guile, C, and Assembler.
# Python and all other foreign-language test/benchmark runners are excluded.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
cd "$root"
files=(
  # Canonical CI, benchmark registry, and every release entry point.
  .github/workflows/ci.yml
  .github/workflows/ci-heavy.yml
  .github/workflows/benchmark-registry.yml
  .github/workflows/release-preflight.yml
  .github/workflows/release.yml
  .github/workflows/release-publish.yml
  .github/workflows/release-smoke-short.yml
  .github/workflows/sens-rust-zig-corridor-guard.yml
  .github/workflows/binary-only-authority.yml
  .github/workflows/vertical-day-immutable-smoke.yml
  .github/workflows/vertical-day-smoke.yml
  .github/workflows/physical-t5-evidence-integrity.yml
)
# These are execution commands, not mentions in comments. Do not match the
# explicitly allowed Guile, C, Assembler, Rust, Zig, or native SENS runners.
# Дозволені мови-острови (execution islands): Common Lisp, Prolog, CLIPS,
# Datalog — межа в contracts/island-compat-contract.lisp (#749). Острів дає
# спостереження ОДНОГО завершеного виклику (native-observation), не семантику:
# kernel-interpretation / semantic-authority / universal-result-coercion —
# forbidden. Тому вони дозволені як свідки, але не як джерело істини.
foreign_runner='^[[:space:]]*((run:[[:space:]]*)?((python3?|pypy3?)[[:space:]]+-m[[:space:]]+(unittest|pytest)([[:space:]]|$)|pytest([[:space:]]|$)|python3?[[:space:]]+.*(--self-test|tests?/|benchmarks?/|test_[^/[:space:]]*\.py|[^/[:space:]]*_test\.py|[^/[:space:]]*bench[^/[:space:]]*\.py|run\.py)|node[[:space:]]+.*(test|bench|benchmark|/run\.)|npm[[:space:]]+(test|run[[:space:]]+(test|bench|benchmark))|npx[[:space:]]+(jest|vitest|mocha)|bun[[:space:]]+test|deno[[:space:]]+test|go[[:space:]]+test([[:space:]]|$)|racket[[:space:]]+.*(test|bench)|lua[0-9.]*[[:space:]]+.*(test|bench)|ruby[[:space:]]+.*(test|bench)|php[[:space:]]+.*(test|bench)|mvn[[:space:]]+test|gradle[[:space:]]+test))'
if grep -nE "$foreign_runner" "${files[@]}"; then
  echo "EXECUTION_LANGUAGE_POLICY=FAIL foreign_test_or_benchmark_runner"
  exit 1
fi
echo "EXECUTION_LANGUAGE_POLICY=PASS allowed=Rust,Zig,SENS,Guile,C,Assembler,CommonLisp,Prolog,CLIPS,Datalog python_tests=EXCLUDED foreign_tests=EXCLUDED python_benchmarks=EXCLUDED foreign_benchmarks=EXCLUDED native_replacements=REQUIRED islands=ALLOWED_WITNESS_ONLY"
