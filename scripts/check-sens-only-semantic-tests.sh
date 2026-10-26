#!/usr/bin/env bash
# Owner allowlist for test/benchmark evidence: Rust, Zig, native SENS, Guile, C,
# and Assembler. Scan all active GitHub Actions workflows for other-language
# runners. Excluded runner references are NOT_VERIFIED, never evidence of PASS.
set -euo pipefail
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

archive="docs/language-policy-archive.md"
if [[ ! -f "$archive" ]]; then echo "ARCHIVE_GATE=FAIL missing_registry"; exit 1; fi
archive_count="$(grep -cE '^\|.*\| ARCHIVE \|$' "$archive" || true)"
summary="ARCHIVE (поза мовним коридором): $archive_count артефактів — $archive"
echo "$summary"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then echo "$summary" >> "$GITHUB_STEP_SUMMARY"; fi
archive_admitted() { grep -Fq "| \`$1\` |" "$archive"; }
if [[ "${1:-}" == "--self-test" ]]; then
  archive_admitted ".github/workflows/human-key-trial.yml" || { echo "ARCHIVE_POSITIVE=FAIL"; exit 1; }
  if archive_admitted "tests/semantic/new-unregistered-test.py"; then echo "ARCHIVE_NEGATIVE=FAIL"; exit 1; fi
  echo "ARCHIVE_POSITIVE=OK ARCHIVE_NEGATIVE=OK"
  exit 0
fi
if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" ]]; then
  base="${GITHUB_BASE_REF:-main}"
  git fetch --no-tags origin "$base" >/dev/null 2>&1 || { echo "SENS_FIRST_GATE=FAIL cannot_fetch_base"; exit 1; }
  added="$(git diff --name-only --diff-filter=A "origin/$base"...HEAD -- tests benchmarks)"
  if printf '%s\n' "$added" | grep -Eq '^(tests|benchmarks)/.*\.(py|js|ts|rb|go|lua|scm|rkt)$'; then
    echo "SENS_FIRST_GATE=FAIL new_foreign_test_or_benchmark"; exit 1
  fi
fi
if grep -nHE "$pattern" "${files[@]}" > "$matches"; then
  echo "FOREIGN_TEST_BENCH_POLICY=FAIL active_foreign_runner_without_archive"
  sed -n '1,40p' "$matches"
  exit 1
fi
echo "FOREIGN_TEST_BENCH_POLICY=NO_DISALLOWED_RUNNERS_FOUND workflows=${#files[@]}"
