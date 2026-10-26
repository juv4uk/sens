#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: manual native SENS execution of CURRENT meta-eval.
# The assertions themselves are SENS D3 EQ/COND; no host truth table.
# Без Python, JSON, SHA-256 — лише native sens + cmp.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo 'usage: bash scripts/prove-meta-eval-predicates-d1.sh [native-sens-path]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
lib=lib/meta-eval.lisp
positive=tests/semantic/meta-eval-predicates-d1-law.lisp
mutant=tests/semantic/meta-eval-predicates-d1-mutant.lisp
id=meta-eval-predicates-d1
reproduce="bash scripts/prove-meta-eval-predicates-d1.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat "$lib" "$positive" > "$tmp/positive.lisp"
cat "$lib" "$mutant" > "$tmp/mutant.lisp"
printf '1\n' > "$tmp/expected"
printf '0\n' > "$tmp/expected-mutant"
printf 'NATIVE_SENS_EXECUTOR id=%s\n' "$id"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2> "$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2
  cat "$tmp/err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if ! "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'NATIVE_SENS_NEGATIVE id=%s-mutant mode=execution-reject\n' "$id"
else
  if cmp -s "$tmp/expected" "$tmp/mutant.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2
    exit 1
  fi
fi
physical_law="${positive%.lisp}.sens"
physical_mutant="${mutant%.lisp}.sens"
if [[ -s "$physical_law" && -s "$physical_mutant" ]]; then
  if ! "$cli" --t5m-pair "$positive" "$physical_law" --core4-runtime --binding-source "$lib" \
      > "$tmp/paired.out" 2> "$tmp/paired.err"; then
    printf 'REGRESSION id=%s layer=physical-f4 actual=execution-error\n' "$id" >&2
    cat "$tmp/paired.err" >&2
    exit 1
  fi
  if ! cmp -s "$tmp/expected" "$tmp/paired.out"; then
    printf 'REGRESSION id=%s layer=physical-f4 actual=wrong-verdict\n' "$id" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_PHYSICAL_F4_PASS id=%s\n' "$id"
fi
printf 'NATIVE_SENS_PASS id=%s semantic_authority=SENS evidence=cmp\n' "$id"
