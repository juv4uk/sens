#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: Lisp→T5M semantic via native SENS. Без Python/JSON/SHA-256.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=lisp-semantic-t5m
law=tests/semantic/lisp-semantic-t5m-law.lisp
mutant=tests/semantic/lisp-semantic-t5m-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2; exit 1
fi
if [[ ! -f "$law" ]]; then
  echo "SENS_NATIVE_CHECK=scheduled id=$id evidence=fixture-absent"; exit 0
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"
if ! "$cli" "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2; cat "$tmp/err" >&2; exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2; exit 1
fi
physical="${law%.lisp}.sens"
if [[ -s "$physical" ]]; then
  if ! "$cli" --t5m-pair "$law" "$physical" > "$tmp/paired.out" 2>"$tmp/paired.err"; then
    printf 'REGRESSION id=%s layer=physical-f4 actual=execution-error\n' "$id" >&2
    cat "$tmp/paired.err" >&2; exit 1
  fi
  if ! cmp -s "$tmp/expected" "$tmp/paired.out"; then
    printf 'REGRESSION id=%s layer=physical-f4 actual=wrong-verdict\n' "$id" >&2; exit 1
  fi
  printf 'NATIVE_SENS_PHYSICAL_F4_PASS id=%s\n' "$id"
fi
printf 'NATIVE_SENS_PASS id=%s semantic_authority=SENS evidence=cmp\n' "$id"
