#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: SENS бенчмарк-свідок медіани. Без Python/JSON/SHA-256.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=бенчмарк-медіана
law=tests/semantic/бенчмарк-медіана-law.lisp
mutant=tests/semantic/бенчмарк-медіана-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"
if ! "$cli" "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2
  cat "$tmp/err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if "$cli" "$mutant" > "$tmp/mutant.out" 2>"$tmp/mutant.err"; then
  if cmp -s "$tmp/expected" "$tmp/mutant.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2
    exit 1
  fi
fi
echo "БЕНЧМАРК_МЕДІАНА=OK evidence=native-sens"
