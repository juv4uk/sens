#!/usr/bin/env bash
# Semantic CI: ONLY SENS fixtures decide laws. This shell moves source text
# through the interactive REPL -> Zig T5M -> SENS and checks D1 replies.
# No Rust/Python semantic oracle, no JSON/digest receipts and no silent skip.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
[[ -x "$cli" ]] || { echo "SENS_REPL_CORPUS_BLOCKED missing-executor=$cli" >&2; exit 2; }

tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
verified=0

run_case() {
  local label="$1" expected="$2" witness="$3"
  shift 3
  local id="${label//\//-}"
  local request="$tmp/$id.input" output="$tmp/$id.out" error="$tmp/$id.err"
  : > "$request"
  local source
  # Every prerequisite is loaded through the SAME REPL session, preserving
  # SENS definitions; the final witness itself produces the D1 verdict.
  for source in "$@" "$witness"; do
    if [[ ! -f "$source" || -L "$source" ]]; then
      printf 'SENS_REPL_CORPUS_BLOCKED label=%s missing-or-linked=%s\n' "$label" "$source" >&2
      return 1
    fi
    printf ':завантажити %s\n' "$source" >> "$request"
  done
  if ! timeout 90s "$cli" --surface=укр < "$request" > "$output" 2> "$error"; then
    printf 'SENS_REPL_CORPUS_FAIL label=%s executor=error\n' "$label" >&2
    cat "$error" >&2
    return 1
  fi
  if [[ -s "$error" ]] || grep -Eq 'Помилка (REPL/T5M|завантаження|виконання)' "$output"; then
    printf 'SENS_REPL_CORPUS_FAIL label=%s unexpected-error\n' "$label" >&2
    cat "$error" "$output" >&2
    return 1
  fi
  # Require a witnessed LAST source, not a D1 printed by any prerequisite.
  # The REPL may attach its prompt to stdout for piped stdin.
  if ! awk -v marker="Завантажено: $witness" -v wanted="$expected" '
    index($0, marker) { admitted = 1; next }
    admitted && ($0 == wanted || $0 == "sens[укр]> " wanted) { correct = 1 }
    END { exit (admitted && correct ? 0 : 1) }
  ' "$output"; then
    printf 'SENS_REPL_CORPUS_FAIL label=%s expected=D1:%s actual=missing-or-wrong\n' "$label" "$expected" >&2
    cat "$output" >&2
    return 1
  fi
  printf 'SENS_REPL_WITNESS_PASS label=%s fixture=%s D1=%s path=REPL/Zig/T5M/SENS\n' "$label" "$witness" "$expected"
  verified=$((verified + 1))
}

# Explicit scope. These are execution witnesses, NOT a false claim that all
# 1024 D10 names or every historical semantic fixture are callable.
run_case d1-positive ТАК tests/semantic/lisp-language-laws.lisp
run_case d1-negative НІ tests/semantic/lisp-language-negative.lisp
run_case structure-positive ТАК tests/semantic/бенчмарк-структура-law.lisp lib/твердження.lisp
run_case structure-negative НІ tests/semantic/бенчмарк-структура-mutant.lisp lib/твердження.lisp
run_case trits-positive ТАК tests/semantic/ідентичність-тритів-law.lisp lib/твердження.lisp
run_case trits-negative НІ tests/semantic/ідентичність-тритів-mutant.lisp lib/твердження.lisp
run_case quote-positive ТАК tests/semantic/d3-як-є-щит-law.lisp lib/core4-parts/core4-language.lisp lib/твердження.lisp
run_case quote-negative НІ tests/semantic/d3-як-є-щит-mutant.lisp lib/core4-parts/core4-language.lisp lib/твердження.lisp
run_case median-positive ТАК tests/semantic/бенчмарк-медіана-law.lisp lib/твердження.lisp lib/бенчмарк.lisp
run_case median-negative НІ tests/semantic/бенчмарк-медіана-mutant.lisp lib/твердження.lisp lib/бенчмарк.lisp

[[ "$verified" -eq 10 ]] || { echo "SENS_REPL_CORPUS_FAIL incomplete=$verified" >&2; exit 1; }
echo "SENS_REPL_CORPUS=PASS witnesses=$verified families=5 scope=explicit-current-only extended-semantic-coverage=NOT_VERIFIED"
