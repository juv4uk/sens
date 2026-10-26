#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: run real library + SENS-authored D1/COND proof.
# Nothing here assigns meaning to a domain code, a predicate or an error.
# Без Python, JSON, SHA-256 — лише native sens + cmp.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo 'usage: bash scripts/prove-meta-eval-graph-d1.sh [native-sens-cli]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
id=meta-eval-graph-d1
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-graph-d1-law.lisp
mutant=tests/semantic/meta-eval-graph-d1-mutant.lisp
reproduce="bash scripts/prove-meta-eval-graph-d1.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=executor-missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
positive="$(sed '/^[[:space:]]*;/d' "$law")"
negative="$(sed '/^[[:space:]]*;/d' "$mutant")"
before="(ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є (requested)))"
after="(ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є (other)))"
count_fixed() {
  local remaining="$1" needle="$2" occurrences=0
  while [[ "$remaining" == *"$needle"* ]]; do
    remaining="${remaining#*"$needle"}"
    (( occurrences += 1 ))
  done
  printf '%s' "$occurrences"
}
if [[ "$(count_fixed "$positive" "$before")" != 1 ||
      "$negative" != "${positive/"$before"/"$after"}" ]]; then
  echo "META_GRAPH_FIXTURE_RED: mutant must change one SENS call" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat "$lib" "$law" > "$tmp/positive.lisp"
cat "$lib" "$mutant" > "$tmp/mutant.lisp"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s\n' "$id" "$cli" "$("$cli" --version 2>/dev/null || echo unknown)"
printf '1\n' > "$tmp/expected"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s actual=execution-error\n' "$id" "$law" >&2
  cat "$tmp/positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s actual=wrong-verdict\n' "$id" "$law" >&2
  exit 1
fi
printf '0\n' > "$tmp/expected-mutant"
if ! "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=eval actual=execution-error\n' "$id" >&2
  cat "$tmp/mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-mutant" "$tmp/mutant.out"; then
  printf 'REGRESSION id=%s-mutant layer=eval actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
physical_law="${law%.lisp}.sens"
physical_mutant="${mutant%.lisp}.sens"
for physical in "$physical_law" "$physical_mutant"; do
  if [[ ! -s "$physical" || -L "$physical" ]]; then
    printf 'REGRESSION id=%s layer=physical-f4 fixture=%s actual=missing\n' "$id" "$physical" >&2
    exit 1
  fi
done
if ! "$cli" --t5m-pair "$law" "$physical_law" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-positive.out" 2> "$tmp/paired-positive.err"; then
  printf 'REGRESSION id=%s layer=physical-f4 actual=execution-error\n' "$id" >&2
  cat "$tmp/paired-positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/paired-positive.out"; then
  printf 'REGRESSION id=%s layer=physical-f4 actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if ! "$cli" --t5m-pair "$mutant" "$physical_mutant" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-mutant.out" 2> "$tmp/paired-mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 actual=execution-error\n' "$id" >&2
  cat "$tmp/paired-mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-mutant" "$tmp/paired-mutant.out"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 actual=wrong-verdict\n' "$id" >&2
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
