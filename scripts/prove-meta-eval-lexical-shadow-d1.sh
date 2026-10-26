#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: SENS lexical-shadow D1 laws and mutants.
# Every verdict is emitted by native SENS; Zig supplies physical T5M only.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=meta-eval-lexical-shadow-d1
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-lexical-shadow-d1-law.lisp
mutants=tests/semantic/meta-eval-lexical-shadow-d1-mutants.lisp
first_mutant=tests/semantic/meta-eval-lexical-shadow-d1-mutant.lisp
physical_law="${law%.lisp}.sens"

if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing path=%s\n' "$id" "$cli" >&2
  exit 1
fi
for fixture in "$lib" "$law" "$mutants" "$first_mutant" "$physical_law"; do
  if [[ ! -s "$fixture" || -L "$fixture" ]]; then
    printf 'REGRESSION test_id=%s layer=fixture missing-or-invalid=%s\n' "$id" "$fixture" >&2
    exit 1
  fi
done

# Fixtures are single-line SENS forms. Shell separates forms only; SENS owns
# every predicate and D1 result. No Python parser or external truth table.
mapfile -t law_forms < <(awk '!/^[[:space:]]*;/ && /[^[:space:]]/ { print }' "$law")
mapfile -t mutant_forms < <(awk '!/^[[:space:]]*;/ && /[^[:space:]]/ { print }' "$mutants")
if (( ${#law_forms[@]} != 8 || ${#mutant_forms[@]} != 8 )); then
  printf 'REGRESSION test_id=%s layer=fixture expected=8-laws-8-mutants actual=%s-%s\n' \
    "$id" "${#law_forms[@]}" "${#mutant_forms[@]}" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

run_form() {
  local role="$1" number="$2" form="$3" expected="$4"
  local source="$tmp/$role-$number.lisp"
  local output="$tmp/$role-$number.out"
  local err="$tmp/$role-$number.err"
  printf '%s\n' "$form" > "$tmp/form.lisp"
  cat "$lib" "$tmp/form.lisp" > "$source"
  if ! timeout 45s "$cli" "$source" > "$output" 2> "$err"; then
    if [[ "$expected" == "0" ]]; then
      printf 'NATIVE_SENS_NEGATIVE id=%s case=%s mode=execution-reject\n' "$role" "$number"
      return 0
    fi
    printf 'REGRESSION test_id=%s case=%s layer=SENS-law expected=D1:%s actual=execution-error\n' "$id" "$number" "$expected" >&2
    cat "$err" >&2
    return 1
  fi
  printf '%s\n' "$expected" > "$tmp/expected"
  if ! cmp -s "$tmp/expected" "$output"; then
    printf 'REGRESSION test_id=%s case=%s layer=SENS-law expected=D1:%s actual=wrong-verdict\n' "$id" "$number" "$expected" >&2
    return 1
  fi
  printf 'NATIVE_SENS_PASS test_id=%s case=%s verdict=D1:%s\n' "$role" "$number" "$expected"
}

for i in "${!law_forms[@]}"; do
  number=$((i + 1))
  run_form "$id-law" "$number" "${law_forms[$i]}" "1"
done
for i in "${!mutant_forms[@]}"; do
  number=$((i + 1))
  run_form "$id-mutant" "$number" "${mutant_forms[$i]}" "0"
done

# The singular fixture deliberately changes only the first law; the remaining
# seven forms are positive controls, so execute its first form by itself.
first_form="$(awk '!/^[[:space:]]*;/ && /[^[:space:]]/ { print; exit }' "$first_mutant")"
if [[ -z "$first_form" ]]; then
  printf 'REGRESSION test_id=%s layer=fixture empty-first-mutant\n' "$id" >&2
  exit 1
fi
run_form "$id-first-mutant" 1 "$first_form" "0"

# Test a physical T5M law pair from checked-in source, with the native SENS
# evaluator deciding the verdict. The carrier itself is not a semantic oracle.
if ! timeout 45s "$cli" --t5m-pair "$law" "$physical_law" --core4-runtime --binding-source "$lib" \
    > "$tmp/physical-law.out" 2> "$tmp/physical-law.err"; then
  printf 'REGRESSION test_id=%s layer=physical-T5M actual=execution-error\n' "$id" >&2
  cat "$tmp/physical-law.err" >&2
  exit 1
fi
printf '1\n' > "$tmp/expected-physical"
if ! cmp -s "$tmp/expected-physical" "$tmp/physical-law.out"; then
  printf 'REGRESSION test_id=%s layer=physical-T5M expected=D1:1 actual=wrong-verdict\n' "$id" >&2
  exit 1
fi

# Mint a temporary physical pair for the one-form negative mutant, then let
# native SENS execute that exact pair. No report file, digest, or JSON is made.
printf '%s\n' "$first_form" > "$tmp/first-mutant.lisp"
if ! timeout 45s "$cli" --t5m-mint-pair "$tmp/first-mutant.lisp" "$tmp/first-mutant.sens" --binding-source "$lib" \
    > "$tmp/mint.out" 2> "$tmp/mint.err"; then
  printf 'REGRESSION test_id=%s layer=physical-mutant-mint actual=execution-error\n' "$id" >&2
  cat "$tmp/mint.err" >&2
  exit 1
fi
if timeout 45s "$cli" --t5m-pair "$tmp/first-mutant.lisp" "$tmp/first-mutant.sens" --core4-runtime --binding-source "$lib" \
    > "$tmp/physical-mutant.out" 2> "$tmp/physical-mutant.err"; then
  printf '0\n' > "$tmp/expected-mutant"
  if ! cmp -s "$tmp/expected-mutant" "$tmp/physical-mutant.out"; then
    printf 'REGRESSION test_id=%s layer=physical-mutant expected=D1:0 actual=false-positive\n' "$id" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_NEGATIVE id=%s-first-mutant layer=physical-T5M verdict=D1:0\n' "$id"
else
  printf 'NATIVE_SENS_NEGATIVE id=%s-first-mutant layer=physical-T5M mode=execution-reject\n' "$id"
fi
printf 'NATIVE_SENS_PASS id=%s laws=8 mutants=8 authority=SENS carrier=Zig/T5M\n' "$id"
