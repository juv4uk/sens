#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: only native SENS judges eight lexical laws.
# One source form per case: report the first precise failing case.
set -euo pipefail
cd "$(dirname "$0")/.."
fixture_only=false
if [[ "${1:-}" == "--check-fixtures" ]]; then
  if [[ $# -ne 1 ]]; then
    echo "usage: bash scripts/prove-meta-eval-lexical-shadow-d1.sh --check-fixtures" >&2
    exit 2
  fi
  fixture_only=true
elif [[ $# -gt 1 ]]; then
  echo "usage: bash scripts/prove-meta-eval-lexical-shadow-d1.sh [native-sens-path|--check-fixtures]" >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-lexical-shadow-d1-law.lisp
mutant=tests/semantic/meta-eval-lexical-shadow-d1-mutant.lisp
mutants=tests/semantic/meta-eval-lexical-shadow-d1-mutants.lisp
id=meta-eval-lexical-shadow-d1
reproduce="bash scripts/prove-meta-eval-lexical-shadow-d1.sh $cli"


# Transport-only: exact source equality outside ONE D1 bit and D2 balance.
# This code does not evaluate quote, binder lookup, or D1 semantic truth.
python3 - "$law" "$mutant" "$mutants" "$lib" <<'PY'
from pathlib import Path
import hashlib
import sys

def forms(path):
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith(";")]

positive, first_mutant, negative = map(forms, sys.argv[1:4])
if any(len(rows) != 8 for rows in (positive, first_mutant, negative)):
    raise SystemExit("META_LEXICAL_FIXTURE_RED: required eight independent forms")

yes = "(атом? (як-є ()))"
no = "(атом? (сполучити (як-є ()) (як-є ())))"
heads = ["вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення?"] * 5
heads += ["визначення-посилається-на-ім'я?"] * 3
expected = [False, True, False, True, False, False, True, False]
library = Path(sys.argv[4]).read_text(encoding="utf-8")

def extract_call(source, case):
    prefix = "(за-умовою ("
    if not source.startswith(prefix):
        raise SystemExit(f"META_LEXICAL_FIXTURE_RED: wrong COND case={case}")
    pos = len(prefix)
    if source[pos] != "(":
        raise SystemExit(f"META_LEXICAL_FIXTURE_RED: no predicate case={case}")
    depth = 0
    for i in range(pos, len(source)):
        depth += (source[i] == "(") - (source[i] == ")")
        if depth == 0:
            return source[pos:i + 1]
    raise SystemExit(f"META_LEXICAL_FIXTURE_RED: missing D2 close case={case}")

def form(call, truth):
    return f"(за-умовою ({call} {yes if truth else no}) ({yes} {no if truth else yes}))"

for i, (good, bad, head, truth) in enumerate(zip(positive, negative, heads, expected), 1):
    call = extract_call(good, i)
    if not call.startswith("(" + head + " ") or "(визначити " + head not in library:
        raise SystemExit(f"META_LEXICAL_FIXTURE_RED: obsolete call-head case={i}")
    if good != form(call, truth) or bad != form(call, not truth):
        raise SystemExit(f"META_LEXICAL_FIXTURE_RED: invalid SENS COND or mutant case={i}")
if first_mutant != [negative[0], *positive[1:]]:
    raise SystemExit("META_LEXICAL_FIXTURE_RED: first mutant differs beyond one SENS verdict")
for i, (good, bad) in enumerate(zip(positive, negative), 1):
    for role, source in (("law", good), ("mutant", bad)):
        digest = hashlib.sha256((library + "\n" + source + "\n").encode()).hexdigest()
        print(f"META_LEXICAL_SOURCE_SHA case={i} role={role} sha256={digest}")
print("META_LEXICAL_FIXTURE_PASS positive=8 mutants=8 semantic_pass=NOT_INFERRED")
PY

if [[ "$fixture_only" == true ]]; then
  printf 'META_LEXICAL_FIXTURES_VERIFIED_ONLY positive_forms=8 negative_forms=8 semantic_pass=NOT_RUN\n'
  exit 0
fi
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval expected=native-executor actual=missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
mapfile -t forms < <(grep -v '^[[:space:]]*;' "$law" | sed '/^[[:space:]]*$/d')
mapfile -t mutant_forms < <(grep -v '^[[:space:]]*;' "$mutants" | sed '/^[[:space:]]*$/d')
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR id=%s path=%s version=%s reproduce=%q\n' "$id" "$cli" "$("$cli" --version)" "$reproduce"
sha256sum "$cli" "$lib" "$law" "$mutant" "$mutants"
printf '1\n' > "$tmp/expected"
for i in "${!forms[@]}"; do
  case_no=$((i+1))
  case_id="$id-$case_no"
  { cat "$lib"; printf '\n%s\n' "${forms[$i]}"; } > "$tmp/$case_no.lisp"
  printf 'NATIVE_SENS_CASE id=%s layer=eval test_case=%s fixture=%s reproduce=%q\n' "$case_id" "$case_no" "$law" "$reproduce"
  sha256sum "$tmp/$case_no.lisp"
  if ! "$cli" "$tmp/$case_no.lisp" > "$tmp/actual" 2> "$tmp/stderr"; then
    printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:1 actual=execution-error first_diff=unknown reproduce=%q\n' "$case_id" "$law" "$reproduce" >&2
    cat "$tmp/stderr" >&2
    sha256sum "$tmp/expected" "$tmp/actual" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_DIGESTS test_id=%s expected_sha256=' "$case_id"
  sha256sum "$tmp/expected"
  printf 'NATIVE_SENS_DIGESTS test_id=%s actual_sha256=' "$case_id"
  sha256sum "$tmp/actual"
  if ! cmp -s "$tmp/expected" "$tmp/actual"; then
    first_diff="$(cmp "$tmp/expected" "$tmp/actual" 2>/dev/null | head -n1 || true)"
    printf 'REGRESSION test_id=%s layer=eval fixture=%s expected=D1:1 actual=wrong-verdict first_diff=%q reproduce=%q\n' "$case_id" "$law" "$first_diff" "$reproduce" >&2
    exit 1
  fi
  { cat "$lib"; printf '\n%s\n' "${mutant_forms[$i]}"; } > "$tmp/mutant-$case_no.lisp"
  printf 'NATIVE_SENS_MUTANT id=%s-mutant-%s fixture=%s reproduce=%q\n' "$id" "$case_no" "$mutants" "$reproduce"
  sha256sum "$tmp/mutant-$case_no.lisp"
  printf '0\n' > "$tmp/expected-mutant"
  if ! "$cli" "$tmp/mutant-$case_no.lisp" > "$tmp/mutant.out" 2> "$tmp/mutant.err"; then
    printf 'REGRESSION test_id=%s-mutant-%s layer=eval fixture=%s expected=D1:0 actual=execution-error reproduce=%q\n' "$id" "$case_no" "$mutants" "$reproduce" >&2
    cat "$tmp/mutant.err" >&2
    exit 1
  fi
  if ! cmp -s "$tmp/expected-mutant" "$tmp/mutant.out"; then
    printf 'REGRESSION test_id=%s-mutant-%s layer=eval fixture=%s expected=D1:0 actual=wrong-verdict reproduce=%q\n' "$id" "$case_no" "$mutants" "$reproduce" >&2
    sha256sum "$tmp/expected-mutant" "$tmp/mutant.out" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant-%s expected=D1:0 actual_sha256=' "$id" "$case_no"
  sha256sum "$tmp/mutant.out"
done
# F4: агрегатор робить усі вісім D1-висновків спостережуваними одним
# результатом парного фізичного запуску. Його мутант змінює перший закон.
physical_law="${law%.lisp}.sens"
physical_mutant="${mutant%.lisp}.sens"
for physical in "$physical_law" "$physical_mutant"; do
  if [[ ! -s "$physical" || -L "$physical" ]]; then
    printf 'REGRESSION test_id=%s layer=physical-f4 fixture=%s expected=committed-T5M actual=missing-or-invalid reproduce=%q\n' "$id" "$physical" "$reproduce" >&2
    exit 1
  fi
done
sha256sum "$physical_law" "$physical_mutant"
physical_aggregate=tests/semantic/meta-eval-lexical-shadow-d1-physical-law.lisp
physical_aggregate_carrier="${physical_aggregate%.lisp}.sens"
physical_aggregate_mutant=tests/semantic/meta-eval-lexical-shadow-d1-physical-mutant.lisp
physical_aggregate_mutant_carrier="${physical_aggregate_mutant%.lisp}.sens"
for physical in "$physical_aggregate" "$physical_aggregate_carrier" "$physical_aggregate_mutant" "$physical_aggregate_mutant_carrier"; do
  if [[ ! -s "$physical" || -L "$physical" ]]; then
    printf 'REGRESSION test_id=%s layer=physical-f4 fixture=%s expected=committed-aggregate-source-pair actual=missing-or-invalid reproduce=%q\n' "$id" "$physical" "$reproduce" >&2
    exit 1
  fi
done
sha256sum "$physical_aggregate" "$physical_aggregate_carrier" "$physical_aggregate_mutant" "$physical_aggregate_mutant_carrier"
if ! "$cli" --t5m-pair "$physical_aggregate" "$physical_aggregate_carrier" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-positive.out" 2> "$tmp/paired-positive.err"; then
  printf 'REGRESSION test_id=%s layer=physical-f4 fixture=%s expected=aggregate-D1:1 actual=execution-error reproduce=%q\n' "$id" "$physical_aggregate_carrier" "$reproduce" >&2
  cat "$tmp/paired-positive.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/paired-positive.out"; then
  printf 'REGRESSION test_id=%s layer=physical-f4 fixture=%s expected=aggregate-D1:1 actual=wrong-verdict reproduce=%q\n' "$id" "$physical_aggregate_carrier" "$reproduce" >&2
  sha256sum "$tmp/expected" "$tmp/paired-positive.out" >&2
  exit 1
fi
if ! "$cli" --t5m-pair "$physical_aggregate_mutant" "$physical_aggregate_mutant_carrier" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-mutant.out" 2> "$tmp/paired-mutant.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=physical-f4 fixture=%s expected=aggregate-D1:0 actual=execution-error reproduce=%q\n' "$id" "$physical_aggregate_mutant_carrier" "$reproduce" >&2
  cat "$tmp/paired-mutant.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-mutant" "$tmp/paired-mutant.out"; then
  printf 'REGRESSION test_id=%s-mutant layer=physical-f4 fixture=%s expected=aggregate-D1:0 actual=wrong-verdict reproduce=%q\n' "$id" "$physical_aggregate_mutant_carrier" "$reproduce" >&2
  sha256sum "$tmp/expected-mutant" "$tmp/paired-mutant.out" >&2
  exit 1
fi
# Носій першого мутанта не може бути підмінений під чинне джерело.
if "$cli" --t5m-pair "$physical_aggregate_mutant" "$physical_aggregate_carrier" --core4-runtime --binding-source "$lib" \
    > "$tmp/paired-foreign.out" 2> "$tmp/paired-foreign.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=physical-f4 expected=pair-rejection actual=accepted reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
if ! grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$tmp/paired-foreign.err"; then
  printf 'REGRESSION test_id=%s-mutant layer=physical-f4 expected=pair-mismatch actual=other-rejection reproduce=%q\n' "$id" "$reproduce" >&2
  cat "$tmp/paired-foreign.err" >&2
  exit 1
fi
printf 'NATIVE_SENS_PHYSICAL_F4_PASS test_id=%s positive_forms=8 aggregate=D1:1 mutant=aggregate-D1:0 paired_source=EXACT physical=Zig/T5M\n' "$id"
printf 'NATIVE_SENS_PASS test_id=%s positive_forms=8 negative_forms=8 mutant=D1:0 authority=SENS\n' "$id"
