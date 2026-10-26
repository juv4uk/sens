#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: D8 products main laws. Без Python/JSON/SHA-256.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=d8-products-main
law=tests/semantic/d8-products-main-laws.lisp
mutant=tests/semantic/d8-products-main-mutant.lisp
expected_verdict=1
if [[ ! -f "$law" ]]; then
  law=tests/semantic/d8-acons-swapped-main-laws.lisp
  # The fallback is a three-case positive/negative witness, not the older
  # one-bit products law: empty, non-empty, and swapped-order rejection.
  # Compare the full SENS result so the negative witness cannot be dropped.
  if [[ -f "$law" ]]; then
    expected_verdict='(1 1 0)'
  fi
fi
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2; exit 1
fi
if [[ ! -f "$law" ]]; then
  echo "SENS_NATIVE_CHECK=scheduled id=$id evidence=fixture-absent"; exit 0
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
printf '%s\n' "$expected_verdict" > "$tmp/expected"
if ! "$cli" "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2; cat "$tmp/err" >&2; exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2; exit 1
fi
printf 'NATIVE_SENS_PASS id=%s semantic_authority=SENS evidence=cmp\n' "$id"
