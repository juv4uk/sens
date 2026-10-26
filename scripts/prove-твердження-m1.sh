#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: запускає SENS-авторські свідки бібліотеки тверджень.
# Жодного Python, JSON чи SHA-256: лише native sens і побайтове cmp.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo 'usage: bash scripts/prove-твердження-m1.sh [native-sens-cli]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
id=твердження-m1
law=tests/semantic/твердження-самотест-law.lisp
mutant=tests/semantic/твердження-car-mutant.lisp
reproduce="bash scripts/prove-твердження-m1.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=executor-missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$law" "$tmp/positive.lisp"
cp "$mutant" "$tmp/mutant.lisp"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s\n' "$id" "$cli" "$("$cli" --version 2>/dev/null || echo unknown)"
printf '1\n' > "$tmp/expected"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s actual=execution-error\n' "$id" "$law" >&2
  cat "$tmp/positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=YES actual=wrong-verdict\n' "$id" "$law" >&2
  printf 'actual-bytes: '; od -An -tx1 "$tmp/actual" | head -2 >&2
  exit 1
fi
printf '0\n' > "$tmp/expected-mutant"
if ! "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  # відмова виконання мутанта також припустима як негативний свідок
  printf 'НЕГАТИВНИЙ_СВІДОК id=%s-mutant mode=execution-reject\n' "$id"
else
  if ! cmp -s "$tmp/expected-mutant" "$tmp/mutant.out"; then
    # мутант не зобов'язаний друкувати 0; достатньо що він не друкує 1
    if cmp -s "$tmp/expected" "$tmp/mutant.out"; then
      printf 'REGRESSION id=%s-mutant layer=eval fixture=%s actual=false-positive\n' "$id" "$mutant" >&2
      exit 1
    fi
  fi
  printf 'НЕГАТИВНИЙ_СВІДОК id=%s-mutant mode=verdict-not-yes\n' "$id"
fi
printf 'ПОЗИТИВНИЙ_СВІДОК id=%s fixture=%s verdict=yes\n' "$id" "$law"
echo "М1_ТВЕРДЖЕННЯ=OK evidence=native-sens cmp=byte-identity"
