#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: SENS lexical-shadow D1. Без Python, JSON, SHA-256.
# Виконання і вирок — лише native sens + побайтове cmp.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=meta-eval-lexical-shadow-d1
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-lexical-shadow-d1-physical-law.lisp
mutant=tests/semantic/meta-eval-lexical-shadow-d1-physical-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat "$lib" "$law" > "$tmp/positive.lisp"
cat "$lib" "$mutant" > "$tmp/mutant.lisp"
printf '1\n' > "$tmp/expected"
printf '0\n' > "$tmp/expected-mutant"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s\n' "$id" "$cli"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2
  cat "$tmp/err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if ! "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2>"$tmp/mutant.err"; then
  printf 'NATIVE_SENS_NEGATIVE id=%s-mutant mode=execution-reject\n' "$id"
else
  if cmp -s "$tmp/expected" "$tmp/mutant.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_NEGATIVE id=%s-mutant mode=verdict-not-yes\n' "$id"
fi
# Physical F4 if committed .sens exist
physical_law="${law%.lisp}.sens"
physical_mutant="${mutant%.lisp}.sens"
for physical in "$physical_law" "$physical_mutant"; do
  if [[ ! -s "$physical" || -L "$physical" ]]; then
    printf 'REGRESSION id=%s layer=physical-f4 fixture=%s actual=missing\n' "$id" "$physical" >&2
    exit 1
  fi
done
if ! "$cli" --t5m-pair "$law" "$physical_law" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired.out" 2> "$tmp/paired.err"; then
  printf 'REGRESSION id=%s layer=physical-f4 expected=D1:1 actual=execution-error\n' "$id" >&2
  cat "$tmp/paired.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/paired.out"; then
  printf 'REGRESSION id=%s layer=physical-f4 expected=D1:1 actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if ! "$cli" --t5m-pair "$mutant" "$physical_mutant" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-mutant.out" 2> "$tmp/paired-mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 expected=D1:0 actual=execution-error\n' "$id" >&2
  cat "$tmp/paired-mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-mutant" "$tmp/paired-mutant.out"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 expected=D1:0 actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if "$cli" --t5m-pair "$mutant" "$physical_law" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-foreign.out" 2> "$tmp/paired-foreign.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 expected=pair-rejection actual=accepted\n' "$id" >&2
  exit 1
fi
if ! grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$tmp/paired-foreign.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 expected=pair-mismatch\n' "$id" >&2
  cat "$tmp/paired-foreign.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_PHYSICAL_F4_PASS id=%s positive=D1:1 mutant=D1:0 physical=Zig/T5M\n' "$id"
printf 'NATIVE_SENS_PASS id=%s semantic_authority=SENS evidence=cmp\n' "$id"
