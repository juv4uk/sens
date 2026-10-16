#!/usr/bin/env bash
# Single targeted automatic native SENS witness: positive, empty, negative orientation.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
fixture="tests/semantic/d8-products-swapped-main-laws.lisp"
sha="$(git rev-parse HEAD 2>/dev/null || printf unknown)"
reproduce="bash scripts/prove-d8-products-main.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'UNVERIFIED id=d8-zip-swapped layer=eval source_sha=%s fixture=%s expected=native-executor actual=missing reproduce=%q\n' "$sha" "$fixture" "$reproduce" >&2
  exit 1
fi
if ! output="$("$cli" "$fixture" 2>&1)"; then
  printf 'REGRESSION id=d8-zip-swapped layer=eval source_sha=%s fixture=%s expected=(1 1 0) actual=execution-error first_diff=execution reproduce=%q\n' "$sha" "$fixture" "$reproduce" >&2
  printf '%s\n' "$output" >&2
  exit 1
fi
observed="${output##*$'\n'}"
if [[ "$observed" != '(1 1 0)' ]]; then
  printf 'REGRESSION id=d8-zip-swapped layer=eval source_sha=%s fixture=%s expected=(1 1 0) actual=%q first_diff=predicate-vector reproduce=%q\n' "$sha" "$fixture" "$observed" "$reproduce" >&2
  exit 1
fi
printf 'SENS_D8_PRODUCT_ORIENTATION_PASS id=d8-zip-swapped source_sha=%s expected=(1 1 0) actual=%s\n' "$sha" "$observed"
sha256sum "$fixture" lib/core4.lisp "$cli"
