#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: manual native SENS execution of CURRENT meta-eval.
# The assertions themselves are SENS D3 EQ/COND; no host truth table.
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
  printf 'REGRESSION test_id=%s layer=eval actual=missing-executor reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# Тільки структурна перевірка: SENS сам обчислює всі чотири D1 закони.
# Жоден Python / JSON / хостовий Lisp тут не підміняє позитив чи мутант.
positive_code="$(sed '/^[[:space:]]*;/d' "$positive")"
mutant_code="$(sed '/^[[:space:]]*;/d' "$mutant")"
old="(це-макрос? (як-є приклад))"
new="(це-макрос? (як-є (macro приклад)))"

count_fixed() {
  local remaining="$1" needle="$2" occurrences=0
  while [[ "$remaining" == *"$needle"* ]]; do
    remaining="${remaining#*"$needle"}"
    (( occurrences += 1 ))
  done
  printf '%s' "$occurrences"
}

if [[ "$(count_fixed "$positive_code" "$old")" != 1 ||
      "$mutant_code" != "${positive_code/"$old"/"$new"}" ]]; then
  echo "META_D1_FIXTURE_RED: mutant must change one executable SENS call" >&2
  exit 1
fi
for name in \
  'це-макрос?' \
  'це-замикання?' \
  'це-рекурсивне-замикання?' \
  'лямбда-має-параметр-залишку?'; do
  actual="$(count_fixed "$positive_code" "($name ")"
  if [[ "$actual" != 1 ]]; then
    printf 'META_D1_FIXTURE_RED: missing or duplicated callable %s count=%s\n' "$name" "$actual" >&2
    exit 1
  fi
done
echo "META_D1_MUTATION_CHECK changed=quoted-macro-input expected=positive-1-mutant-0"
cat "$lib" "$positive" > "$tmp/positive.lisp"
cat "$lib" "$mutant" > "$tmp/mutant.lisp"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s reproduce=%q\n' "$id" "$cli" "$("$cli" --version)" "$reproduce"
sha256sum "$cli" "$lib" "$positive" "$mutant" "$tmp/positive.lisp" "$tmp/mutant.lisp"
printf '1\n' > "$tmp/expected"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2> "$tmp/stderr"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=D1:1 actual=execution-error first_diff=unknown reproduce=%q\n' "$id" "$positive" "$reproduce" >&2
  cat "$tmp/stderr" >&2
  sha256sum "$tmp/expected" "$tmp/actual" >&2
  exit 1
fi
printf 'NATIVE_SENS_DIGESTS id=%s expected_sha256=' "$id"
sha256sum "$tmp/expected"
printf 'NATIVE_SENS_DIGESTS id=%s actual_sha256=' "$id"
sha256sum "$tmp/actual"
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=D1:1 actual=wrong-verdict first_diff=0 reproduce=%q\n' "$id" "$positive" "$reproduce" >&2
  exit 1
fi
printf '0\n' > "$tmp/expected-mutant"
if ! "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=eval fixture=%s expected=D1:0 actual=execution-error reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
  cat "$tmp/mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-mutant" "$tmp/mutant.out"; then
  printf 'REGRESSION id=%s-mutant layer=eval fixture=%s expected=D1:0 actual=wrong-verdict reproduce=%q\n' "$id" "$mutant" "$reproduce" >&2
  sha256sum "$tmp/expected-mutant" "$tmp/mutant.out" >&2
  exit 1
fi
printf 'NATIVE_SENS_NEGATIVE id=%s-mutant expected=D1:0 actual_sha256=' "$id"
sha256sum "$tmp/mutant.out"
# F4 — committed physical T5M is the authority for the binary witness.
# F2 source evaluation above does not attest any .sens carrier bytes.
physical_positive="${positive%.lisp}.sens"
physical_mutant="${mutant%.lisp}.sens"
for physical in "$physical_positive" "$physical_mutant"; do
  if [[ ! -s "$physical" || -L "$physical" ]]; then
    printf 'REGRESSION id=%s layer=physical-f4 fixture=%s expected=committed-T5M actual=missing-or-invalid\n' "$id" "$physical" >&2
    exit 1
  fi
done
sha256sum "$physical_positive" "$physical_mutant"
if ! "$cli" --t5m-pair "$positive" "$physical_positive" --binding-source "$lib" \
    > "$tmp/paired-positive.out" 2> "$tmp/paired-positive.err"; then
  printf 'REGRESSION id=%s layer=physical-f4 fixture=%s expected=D1:1 actual=execution-error\n' "$id" "$physical_positive" >&2
  cat "$tmp/paired-positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/paired-positive.out"; then
  printf 'REGRESSION id=%s layer=physical-f4 fixture=%s expected=D1:1 actual=wrong-verdict\n' "$id" "$physical_positive" >&2
  sha256sum "$tmp/expected" "$tmp/paired-positive.out" >&2
  exit 1
fi
if ! "$cli" --t5m-pair "$mutant" "$physical_mutant" --binding-source "$lib" \
    > "$tmp/paired-mutant.out" 2> "$tmp/paired-mutant.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 fixture=%s expected=D1:0 actual=execution-error\n' "$id" "$physical_mutant" >&2
  cat "$tmp/paired-mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-mutant" "$tmp/paired-mutant.out"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 fixture=%s expected=D1:0 actual=wrong-verdict\n' "$id" "$physical_mutant" >&2
  sha256sum "$tmp/expected-mutant" "$tmp/paired-mutant.out" >&2
  exit 1
fi
# Same bytes with different Lisp must fail at the exact domain-word identity gate.
if "$cli" --t5m-pair "$mutant" "$physical_positive" --binding-source "$lib" \
    > "$tmp/paired-foreign.out" 2> "$tmp/paired-foreign.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 expected=pair-rejection actual=accepted\n' "$id" >&2
  exit 1
fi
if ! grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$tmp/paired-foreign.err"; then
  printf 'REGRESSION id=%s-mutant layer=physical-f4 expected=pair-mismatch actual=other-rejection\n' "$id" >&2
  cat "$tmp/paired-foreign.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_PHYSICAL_F4_PASS id=%s positive=D1:1 mutant=D1:0 paired_source=EXACT physical=Zig/T5M\n' "$id"
printf 'NATIVE_SENS_PASS id=%s predicate_checks=4 mutant=D1:0 semantic_authority=SENS\n' "$id"
