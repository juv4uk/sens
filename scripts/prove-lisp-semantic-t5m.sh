#!/usr/bin/env bash
# Нативні мовні закони: Lisp -> Zig/T5M -> фізичний .sens -> SENS.
# Bash перевіряє тільки статус, оберненість байтів і кінцеві D1-вердикти.
# Семантика COND/QUOTE/EQ/ATOM належить тільки текстовим Lisp-свідкам.
set -euo pipefail

if (( $# != 3 )); then
  echo "Використання: $0 SENS_BINARY SENS_TRIT_BINARY EVIDENCE_DIR" >&2
  exit 2
fi
sens="$1"
trit="$2"
evidence="$3"
test -x "$sens" && test -x "$trit"
mkdir -p "$evidence"

fail() {
  local id="$1" layer="$2" expected="$3" actual="$4"
  echo "::error title=SENS Lisp/T5M::REGRESSION id=$id layer=$layer expected=$expected actual=$actual" >&2
  exit 1
}

run_law() {
  local id="$1" source="$2" expected="$3" dir physical actual
  dir="$evidence/$id"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  test -f "$source" && test ! -L "$source" ||
    fail "$id" source "regular-Lisp" "missing-or-symlink"

  # Семантичний доказ не записує очікувану логіку іншою мовою.
  if ! timeout 45s "$sens" "$source" >"$dir/direct.out" 2>"$dir/direct.err"; then
    cat "$dir/direct.err" >&2
    fail "$id" lisp-reader "SENS-execution" "rejected"
  fi
  # Кодек створює байти T5M; Zig відкриває і перевіряє точне подання.
  if ! timeout 45s "$sens" --t5m-mint "$source" "$physical" >"$dir/mint.out" 2>"$dir/mint.err"; then
    cat "$dir/mint.err" >&2
    fail "$id" codec "T5M-mint" "rejected"
  fi
  test -s "$physical" || fail "$id" codec "nonempty-T5M" "empty"
  if ! timeout 45s "$trit" open "$physical" >"$dir/program" 2>"$dir/open.err" ||
     ! timeout 45s "$trit" verify-view "$physical" >"$dir/inverse.out" 2>"$dir/inverse.err"; then
    cat "$dir/open.err" "$dir/inverse.err" >&2 || true
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi
  if ! timeout 45s "$sens" --t5m-pair "$source" "$physical" >"$dir/paired.out" 2>"$dir/paired.err" ||
     ! timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    cat "$dir/paired.err" "$dir/physical.err" >&2 || true
    fail "$id" sens-physical "paired-and-standalone-execution" "rejected"
  fi
  cmp -s "$dir/direct.out" "$dir/paired.out" ||
    fail "$id" carrier "direct-equals-paired" "divergent"
  cmp -s "$dir/paired.out" "$dir/physical.out" ||
    fail "$id" carrier "paired-equals-physical" "divergent"

  actual="$(cat "$dir/physical.out")"
  if [[ "$actual" != "$expected" ]]; then
    fail "$id" sens-logic "D1:$expected" "$actual"
  fi
  echo "::notice file=$source,title=SENS Lisp→T5M→SENS::PASS id=$id D1=$actual native=SENS"
  sha256sum "$source" "$physical" >"$dir/sha256.txt"
  printf '%s\n' "id=$id source=$source expected=D1:$expected actual=D1:$actual" >>"$evidence/results.txt"
}

# Логічний шар уніфікації — окремий Lisp-свідок із чинною бібліотекою.
# Повний вихідний текст виконується й кодується разом; хост не обчислює occurs-check.
run_bound_law() {
  local id="$1" source="$2" expected="$3" dir combined physical actual
  dir="$evidence/$id"
  combined="$dir/combined.lisp"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  cat -- lib/unify.lisp "$source" > "$combined"

  if ! timeout 45s "$sens" "$combined" >"$dir/direct.out" 2>"$dir/direct.err"; then
    cat "$dir/direct.err" >&2
    fail "$id" lisp-reader "SENS-execution" "rejected"
  fi
  if ! timeout 45s "$sens" --t5m-mint "$combined" "$physical" >"$dir/mint.out" 2>"$dir/mint.err"; then
    cat "$dir/mint.err" >&2
    fail "$id" codec "T5M-mint" "rejected"
  fi
  test -s "$physical" || fail "$id" codec "nonempty-T5M" "empty"
  if ! timeout 45s "$trit" open "$physical" >"$dir/program" 2>"$dir/open.err" ||
     ! timeout 45s "$trit" verify-view "$physical" >"$dir/inverse.out" 2>"$dir/inverse.err"; then
    cat "$dir/open.err" "$dir/inverse.err" >&2 || true
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi
  if ! timeout 45s "$sens" --t5m-pair "$combined" "$physical" >"$dir/paired.out" 2>"$dir/paired.err" ||
     ! timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    cat "$dir/paired.err" "$dir/physical.err" >&2 || true
    fail "$id" sens-physical "paired-and-standalone-execution" "rejected"
  fi
  cmp -s "$dir/direct.out" "$dir/paired.out" ||
    fail "$id" carrier "direct-equals-paired" "divergent"
  cmp -s "$dir/paired.out" "$dir/physical.out" ||
    fail "$id" carrier "paired-equals-physical" "divergent"

  actual="$(cat "$dir/physical.out")"
  [[ "$actual" == "$expected" ]] ||
    fail "$id" sens-logic "D1:$expected" "$actual"
  echo "::notice file=$source,title=SENS unification law::PASS id=$id D1=$actual native=SENS carrier=Zig/T5M"
  sha256sum "$source" lib/unify.lisp "$physical" >"$dir/sha256.txt"
  printf '%s\n' "id=$id source=$source dependency=lib/unify.lisp expected=D1:$expected actual=D1:$actual" >>"$evidence/results.txt"
}

: >"$evidence/results.txt"
# Повна пара власне мовного заперечення Д1: джерело тільки Lisp.
run_law d1-not-positive tests/semantic/d1-not-law.lisp 1
run_law d1-not-mutant tests/semantic/d1-not-mutant.lisp 0
run_law d3-selection-positive tests/semantic/d3-d4-logic-selection-law.lisp 1
run_law d3-selection-mutant tests/semantic/d3-d4-logic-selection-mutant.lisp 0
run_law d3-demorgan-four-cases tests/semantic/d3-demorgan-truth-table-law.lisp 1
run_law d3-demorgan-mutant tests/semantic/d3-demorgan-truth-table-mutant.lisp 0
run_law d3-quote-short-circuit-positive tests/semantic/d3-cond-quote-lazy-law.lisp 1
run_law d3-quote-short-circuit-mutant tests/semantic/d3-cond-quote-lazy-mutant.lisp 0
run_law d4-late-binding-positive tests/semantic/d4-late-definition-binding-law.lisp 1
run_law d4-escaped-closure-positive tests/semantic/d4-escaped-lexical-closure-law.lisp 1
run_law d4-escaped-closure-mutant tests/semantic/d4-escaped-lexical-closure-mutant.lisp 0
# Фізичні закони Д3 не залежать від недопущеного виклику D6 LENGTH.
run_law d3-structural-positive tests/semantic/d3-structural-native-t5m-law.lisp 1
run_law d3-structural-mutant tests/semantic/d3-structural-native-t5m-mutant.lisp 0
# TRANSITIONAL #5854: арифметичні Lisp-свідки існують і перевіряються
# прямим SENS у ci.yml, але фізичний T5M не атестовано до реалізації LENGTH.
# Не оголошувати PASS і не замінювати семантику D6 хостовим оракулом.
echo "::warning file=tests/semantic/d5-arithmetic-native-t5m-law.lisp,title=TRANSITIONAL #5854::D6 LENGTH (D6 000000) поки невикличний у фізичному SENS; D5 T5M=NOT_CERTIFIED"
# The result-status law stays in Ukrainian Lisp; only the runner bundles its admitted library.
result_status_bundle="$evidence/result-status-bundle.lisp"
cat lib/result-status.lisp tests/semantic/result-status-laws.lisp > "$result_status_bundle"
run_law result-status-source "$result_status_bundle" 1
run_bound_law unification-occurs-check-positive tests/semantic/unification-occurs-check-law.lisp 1
run_bound_law unification-occurs-check-mutant tests/semantic/unification-occurs-check-mutant.lisp 0
echo "SENS_LISP_T5M_LAWS_PASS count=16 positive=9 mutants=7 physical=ZIG_T5M"
