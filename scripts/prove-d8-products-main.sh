#!/usr/bin/env bash
# One targeted native SENS runner for derived D8 laws, with positive/negative witnesses.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
sha="$(git rev-parse HEAD 2>/dev/null || printf unknown)"
reproduce="bash scripts/prove-d8-products-main.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'UNVERIFIED id=d8-derived layer=eval source_sha=%s expected=native-executor actual=missing reproduce=%q\n' "$sha" "$reproduce" >&2
  exit 1
fi
check() {
  local id="$1" fixture="$2" expected="$3" output observed
  if ! output="$("$cli" "$fixture" 2>&1)"; then
    printf 'REGRESSION id=%s layer=eval source_sha=%s fixture=%s expected=%s actual=execution-error first_diff=execution reproduce=%q\n' "$id" "$sha" "$fixture" "$expected" "$reproduce" >&2
    printf '%s\n' "$output" >&2
    return 1
  fi
  observed="${output##*$'\n'}"
  if [[ "$observed" != "$expected" ]]; then
    printf 'REGRESSION id=%s layer=eval source_sha=%s fixture=%s expected=%s actual=%q first_diff=predicate-vector reproduce=%q\n' "$id" "$sha" "$fixture" "$expected" "$observed" "$reproduce" >&2
    return 1
  fi
  printf 'SENS_D8_NATIVE_PASS id=%s source_sha=%s expected=%s actual=%s\n' "$id" "$sha" "$expected" "$observed"
}
check d8-zip-orientation tests/semantic/d8-products-swapped-main-laws.lisp '(1 1 0)'
check d8-notany tests/semantic/d8-notany-main-laws.lisp '(1 0 1)'
check d8-acons-swapped tests/semantic/d8-acons-swapped-main-laws.lisp '(1 1 0)'
check d8-maplist-right tests/semantic/d8-maplist-right-main-laws.lisp '(1 1 0)'
check d8-nth-right tests/semantic/d8-nth-right-main-laws.lisp '(1 1 0)'
check d8-position-tree-equ tests/semantic/d8-position-tree-equ-main-laws.lisp '(1 1 1 0 1 0)'
check d8-mapc-native tests/semantic/d8-mapc-main-laws.lisp '(1 1 0)'
# Negative proves every callback is evaluated: second CAR(atom) must reject.
bad="tests/semantic/d8-mapc-call-each-negative.lisp"
if negative_output="$("$cli" "$bad" 2>&1)"; then
  printf 'REGRESSION id=d8-mapc-callback layer=eval source_sha=%s fixture=%s expected=CAR-atom-rejected actual=accepted first_diff=negative-exit reproduce=%q\n' "$sha" "$bad" "$reproduce" >&2
  exit 1
fi
if ! grep -Eiq 'car|pair|пара|D3 100' <<< "$negative_output"; then
  printf 'UNINFORMATIVE-NEGATIVE id=d8-mapc-callback layer=eval source_sha=%s fixture=%s expected=CAR-pair-diagnostic actual=%q first_diff=diagnostic reproduce=%q\n' "$sha" "$bad" "$negative_output" "$reproduce" >&2
  exit 1
fi
printf 'SENS_D8_NATIVE_PASS id=d8-mapc-callback source_sha=%s expected=CAR-atom-rejected\n' "$sha"

sha256sum tests/semantic/d8-products-swapped-main-laws.lisp tests/semantic/d8-notany-main-laws.lisp tests/semantic/d8-acons-swapped-main-laws.lisp tests/semantic/d8-maplist-right-main-laws.lisp tests/semantic/d8-nth-right-main-laws.lisp tests/semantic/d8-position-tree-equ-main-laws.lisp tests/semantic/d8-mapc-main-laws.lisp tests/semantic/d8-mapc-call-each-negative.lisp lib/core4.lisp "$cli"
