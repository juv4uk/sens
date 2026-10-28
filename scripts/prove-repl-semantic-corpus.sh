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
  # Require the final *non-empty* REPL reply following the last witness
  # load. Earlier matching output (from a prerequisite or side effect)
  # cannot turn a later wrong verdict into a false PASS.
  # Non-TTY REPL has no prompt; allow the exact interactive-prefix form too.
  if ! awk -v marker="Завантажено: $witness" -v wanted="$expected" '
    index($0, marker) { admitted = 1; last = ""; next }
    admitted && NF { last = $0 }
    END { exit (admitted && (last == wanted || last == "sens[укр]> " wanted) ? 0 : 1) }
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
run_case d1-not-positive ТАК tests/semantic/d1-not-law.lisp
run_case d1-not-negative НІ tests/semantic/d1-not-mutant.lisp
run_case d2-laziness-positive ТАК tests/semantic/d2-cond-laziness-law.lisp
run_case d2-laziness-negative НІ tests/semantic/d2-cond-laziness-mutant.lisp
run_case d4-lambda-positive ТАК tests/semantic/d4-lambda-application-law.lisp
run_case d4-lambda-negative НІ tests/semantic/d4-lambda-application-mutant.lisp
run_case d5-arithmetic-positive ТАК tests/semantic/d5-arithmetic-native-t5m-law.lisp
run_case d5-arithmetic-negative НІ tests/semantic/d5-arithmetic-native-t5m-mutant.lisp
# Fundamental D1/D2/D3 truth is decided inside executable SENS programs.
# A mutant returns exact D1 false; this shell does not reimplement any law.
run_case not-positive ТАК tests/semantic/d1-not-law.lisp
run_case not-negative НІ tests/semantic/d1-not-mutant.lisp
run_case cond-positive ТАК tests/semantic/d2-cond-laziness-law.lisp
run_case cond-negative НІ tests/semantic/d2-cond-laziness-mutant.lisp
run_case d3-positive ТАК tests/semantic/d3-structure-law.lisp
run_case d3-negative НІ tests/semantic/d3-structure-mutant.lisp
run_case structure-positive ТАК tests/semantic/бенчмарк-структура-law.lisp lib/твердження.lisp
run_case structure-negative НІ tests/semantic/бенчмарк-структура-mutant.lisp lib/твердження.lisp
run_case trits-positive ТАК tests/semantic/ідентичність-тритів-law.lisp lib/твердження.lisp
run_case trits-negative НІ tests/semantic/ідентичність-тритів-mutant.lisp lib/твердження.lisp
run_case quote-positive ТАК tests/semantic/d3-як-є-щит-law.lisp lib/core4-parts/core4-language.lisp lib/твердження.lisp
run_case quote-negative НІ tests/semantic/d3-як-є-щит-mutant.lisp lib/core4-parts/core4-language.lisp lib/твердження.lisp
run_case median-positive ТАК tests/semantic/бенчмарк-медіана-law.lisp lib/твердження.lisp lib/бенчмарк.lisp
run_case median-negative НІ tests/semantic/бенчмарк-медіана-mutant.lisp lib/твердження.lisp lib/бенчмарк.lisp

# Додаткові автономні SENS D1/D3/D4 докази без хостового інтерпретатора.
run_case d1-empty-positive ТАК tests/semantic/d1-empty-identity-law.lisp
run_case d1-empty-negative НІ tests/semantic/d1-empty-identity-mutant.lisp
run_case d1-empty-predicate-positive ТАК tests/semantic/d1-порожність-law.lisp
run_case d1-empty-predicate-negative НІ tests/semantic/d1-порожність-mutant.lisp
run_case d3-structural-positive ТАК tests/semantic/d3-structural-native-t5m-law.lisp
run_case d3-structural-negative НІ tests/semantic/d3-structural-native-t5m-mutant.lisp
run_case d3-pair-positive ТАК tests/semantic/d3-cons-pair-roundtrip-law.lisp
run_case d3-pair-negative НІ tests/semantic/d3-cons-pair-roundtrip-mutant.lisp
run_case d3-d4-selection-positive ТАК tests/semantic/d3-d4-logic-selection-law.lisp
run_case d3-d4-selection-negative НІ tests/semantic/d3-d4-logic-selection-mutant.lisp
run_case d3-demorgan-positive ТАК tests/semantic/d3-demorgan-truth-table-law.lisp
run_case d3-demorgan-negative НІ tests/semantic/d3-demorgan-truth-table-mutant.lisp

[[ "$verified" -eq 36 ]] || { echo "SENS_REPL_CORPUS_FAIL incomplete=$verified" >&2; exit 1; }
echo "SENS_REPL_CORPUS=PASS witnesses=$verified families=18 scope=explicit-current-only extended-semantic-coverage=NOT_VERIFIED"

# The corpus is the declared release-scope smoke proof, not the entire language.
tracked_laws="$(find tests/semantic -maxdepth 1 -type f -name '*-law.lisp' -print | wc -l | tr -d ' ')"
echo "REPL_SEMANTIC_COVERAGE=PARTIAL tracked_law_sources=$tracked_laws repl_families=18 complete_language_proof=NOT_VERIFIED"
