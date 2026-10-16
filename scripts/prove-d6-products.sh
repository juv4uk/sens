#!/usr/bin/env bash
# Один точковий тест законів D6/D8: позитив, перестановка і невірний протокол.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
reproduce="bash scripts/prove-d6-products.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'UNVERIFIED test_id=d6-d8-products layer=eval expected=native-executor actual=missing path=%s reproduce=%q\n' "$cli" "$reproduce" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
verify() {
  local id="$1" fixture="$2" expected="$3" observed last
  if ! observed="$("$cli" "$fixture" 2>"$tmp/stderr")"; then
    printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=%s actual=execution-error first_diff=exit reproduce=%q\n' "$id" "$fixture" "$expected" "$reproduce" >&2
    cat "$tmp/stderr" >&2
    return 1
  fi
  last="${observed##*$'\n'}"
  if [[ "$last" != "$expected" ]]; then
    printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=%s actual=%q first_diff=law-vector reproduce=%q\n' "$id" "$fixture" "$expected" "$last" "$reproduce" >&2
    return 1
  fi
  printf 'SENS_D6_D8_NATIVE_PASS test_id=%s expected=%s actual=%s\n' "$id" "$expected" "$last"
}
verify 'd6-zip-unzip' tests/semantic/d6-products-zip-unzip-laws.lisp '(1 1 0)'
verify 'd8-zip-unzip-swapped' tests/semantic/d8-products-swapped-laws.lisp '(1 1 0)'
bad="tests/semantic/d6-products-zip-unzip-mismatch.lisp"
if "$cli" "$bad" >"$tmp/out" 2>"$tmp/err"; then
  printf 'REGRESSION test_id=d6-zip-unequal layer=eval fixture=%s expected=reject actual=accepted first_diff=exit reproduce=%q\n' "$bad" "$reproduce" >&2
  exit 1
fi
if ! grep -Eiq 'car|pair|пара|перше' "$tmp/err"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=d6-zip-unequal layer=eval fixture=%s expected=CAR-PAIR-ERROR actual=unrelated-error reproduce=%q\n' "$bad" "$reproduce" >&2
  cat "$tmp/err" >&2
  exit 1
fi
sha256sum tests/semantic/d6-products-zip-unzip-laws.lisp tests/semantic/d8-products-swapped-laws.lisp "$bad"
printf 'SENS_D6_D8_PRODUCT_BATCHES_PASS products=4 negative=3 authority=binary-SENS\n'
