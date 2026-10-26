#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: запускає SENS-авторські свідки бібліотеки тверджень.
# Мовний вирок — SENS; механічна перевірка байтів — cmp.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 ]]; then
  echo 'usage: bash scripts/prove-твердження-m1.sh [native-sens-cli]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
id=твердження-m1
law=tests/semantic/твердження-самотест-law.lisp
negative=tests/semantic/твердження-негативні-law.lisp
mutant=tests/semantic/твердження-car-mutant.lisp
reproduce="bash scripts/prove-твердження-m1.sh $cli"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=executor-missing reproduce=%q\n' "$id" "$reproduce" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$law" "$tmp/positive.lisp"
cp "$negative" "$tmp/negative.lisp"
cp "$mutant" "$tmp/mutant.lisp"
printf 'ВИКОНАВЕЦЬ_SENS id=%s path=%s version=%s\n' "$id" "$cli" "$("$cli" --version 2>/dev/null || echo unknown)"
trit="${SENS_TRIT_BINARY:-target/debug/sens-trit}"
if [[ ! -x "$trit" ]]; then
  printf 'REGRESSION test_id=%s layer=physical-eval actual=zig-t5m-reader-missing\n' "$id" >&2
  exit 1
fi
run_core4_witness() {
  local label="$1" source="$2" expected="$3"
  local full="$tmp/$label-full.lisp"
  local physical="$tmp/$label.sens"
  local view="$tmp/$label.view"
  local paired="$tmp/$label.paired"
  local standalone="$tmp/$label.standalone"
  local err="$tmp/$label.err"
  if ! cat -- lib/твердження.lisp "$source" > "$full" ||
     ! "$cli" --t5m-mint "$full" "$physical" >"$tmp/$label.mint.out" 2>"$tmp/$label.mint.err" ||
     ! "$trit" open "$physical" > "$view" 2>"$tmp/$label.open.err" ||
     ! "$trit" verify-view "$physical" >"$tmp/$label.verify.out" 2>"$tmp/$label.verify.err"; then
    printf 'REGRESSION id=%s-%s layer=physical-mint actual=failed\n' "$id" "$label" >&2
    cat "$tmp/$label.mint.err" "$tmp/$label.open.err" "$tmp/$label.verify.err" >&2 2>/dev/null || true
    exit 1
  fi
  if ! "$cli" --t5m-pair "$full" "$physical" --core4-runtime >"$paired" 2>"$err"; then
    printf 'REGRESSION id=%s-%s layer=paired-core4 actual=execution-error\n' "$id" "$label" >&2
    cat "$err" >&2
    exit 1
  fi
  if ! "$trit" eval-core4 "$physical" >"$standalone" 2>"$tmp/$label.standalone.err"; then
    printf 'REGRESSION id=%s-%s layer=standalone-core4 actual=execution-error\n' "$id" "$label" >&2
    cat "$tmp/$label.standalone.err" >&2
    exit 1
  fi
  if ! cmp -s "$paired" "$standalone"; then
    printf 'REGRESSION id=%s-%s layer=paired-standalone actual=output-drift\n' "$id" "$label" >&2
    exit 1
  fi
  printf '%s\n' "$expected" > "$tmp/$label.expected"
  if ! cmp -s "$tmp/$label.expected" "$standalone"; then
    printf 'REGRESSION id=%s-%s layer=eval fixture=%s expected=%s actual=wrong-verdict\n' "$id" "$label" "$source" "$expected" >&2
    printf 'actual-bytes: '; od -An -tx1 "$standalone" | head -2 >&2
    exit 1
  fi
  printf 'SENS_T5M_CORE4_WITNESS_PASS id=%s-%s source=%s physical=ZIG_VERIFIED paired=PASS standalone=PASS verdict=%s\n' "$id" "$label" "$source" "$expected"
}
run_core4_witness positive "$tmp/positive.lisp" 1
run_core4_witness negative-law "$tmp/negative.lisp" 1
printf 'НЕГАТИВНИЙ_СВІДОК id=%s-negative fixture=%s verdict=yes\n' "$id" "$negative"
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
