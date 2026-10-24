#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: run real library + SENS-authored D1/COND proof.
# Nothing here assigns meaning to a domain code, a predicate or an error.
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
# Контроль форми мутанта — лише байтова інваріанта свідків.
# Жоден Python/JSON і жодна оболонка не обчислює закон D1:
# обидва вироки нижче виконує виключно нативний SENS.
positive="$(sed '/^[[:space:]]*;/d' "$law")"
negative="$(sed '/^[[:space:]]*;/d' "$mutant")"
before="(ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є requested))"
after="(ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є other))"

# Підрахунок буквальних викличних голів: лапки і '?' — дані, не glob.
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
for witness in \
  'має-перехідну-гілку-за-умовою?:2' \
  "ім'я-зв'язане-формальними-параметрами?:3" \
  "форма-посилається-на-ім'я?:1" \
  'досяжність-залежностей-графа?:1'; do
  name="${witness%:*}"
  expected="${witness##*:}"
  actual="$(count_fixed "$positive" "($name ")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'META_GRAPH_FIXTURE_RED: %s expected=%s actual=%s\n' "$name" "$expected" "$actual" >&2
    exit 1
  fi
done
if [[ "$positive" == *'#d1:'* || "$positive" == *'(ні)'* || "$positive" == *'(так)'* ]]; then
  echo "META_GRAPH_FIXTURE_RED: historical D1 text cannot run in SENS" >&2
  exit 1
fi
echo "META_GRAPH_MUTATION_CHECK input=one-exact-quoted-symbol positive=D1:1 mutant=D1:0"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cat "$lib" "$law" > "$tmp/positive.lisp"
cat "$lib" "$mutant" > "$tmp/mutant.lisp"
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s reproduce=%q\n' "$id" "$cli" "$("$cli" --version)" "$reproduce"
sha256sum "$cli" "$lib" "$law" "$mutant" "$tmp/positive.lisp" "$tmp/mutant.lisp"
printf '1\n' > "$tmp/expected"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2> "$tmp/positive.err"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=D1:YES actual=execution-error first_diff=unknown reproduce=%q\n' "$id" "$law" "$reproduce" >&2
  cat "$tmp/positive.err" >&2
  sha256sum "$tmp/expected" "$tmp/actual" >&2
  exit 1
fi
printf 'NATIVE_SENS_DIGESTS id=%s expected_sha256=' "$id"
sha256sum "$tmp/expected"
printf 'NATIVE_SENS_DIGESTS id=%s actual_sha256=' "$id"
sha256sum "$tmp/actual"
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=eval fixture=%s expected=D1:YES actual=wrong-verdict first_diff=0 reproduce=%q\n' "$id" "$law" "$reproduce" >&2
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
physical_law="${law%.lisp}.sens"
physical_mutant="${mutant%.lisp}.sens"
for physical in "$physical_law" "$physical_mutant"; do
  if [[ ! -s "$physical" || -L "$physical" ]]; then
    printf 'REGRESSION id=%s layer=physical-f4 fixture=%s expected=committed-T5M actual=missing-or-invalid\n' "$id" "$physical" >&2
    exit 1
  fi
done
sha256sum "$physical_law" "$physical_mutant"
if ! "$cli" --t5m-pair "$law" "$physical_law" --binding-source "$lib" \
    > "$tmp/paired-positive.out" 2> "$tmp/paired-positive.err"; then
  printf 'REGRESSION id=%s layer=physical-f4 fixture=%s expected=D1:1 actual=execution-error\n' "$id" "$physical_law" >&2
  cat "$tmp/paired-positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/paired-positive.out"; then
  printf 'REGRESSION id=%s layer=physical-f4 fixture=%s expected=D1:1 actual=wrong-verdict\n' "$id" "$physical_law" >&2
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
if "$cli" --t5m-pair "$mutant" "$physical_law" --binding-source "$lib" \
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
printf 'NATIVE_SENS_PASS id=%s checks=7 mutant=D1:0 semantic_authority=SENS\n' "$id"
