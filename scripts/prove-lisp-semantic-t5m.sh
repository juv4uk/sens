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
    for error_log in "$dir/paired.err" "$dir/physical.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
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
    for error_log in "$dir/paired.err" "$dir/physical.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
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

# Негатив типу: мовний текст застосовує EQ до пари й атома.
# Не перетворюємо Type у false; транспорт лише зберігає фізичну форму.
run_eq_type_rejection() {
  local id="$1" source="$2" dir physical
  dir="$evidence/$id"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  test -f "$source" && test ! -L "$source" ||
    fail "$id" source "regular-Lisp" "missing-or-symlink"

  if timeout 45s "$sens" "$source" >"$dir/direct.out" 2>"$dir/direct.err"; then
    fail "$id" sens-direct "Type-rejection" "unexpected-success"
  fi
  grep -Fq 'eq expects two atoms' "$dir/direct.err" ||
    fail "$id" sens-direct "EQ-atom-type-error" "unclassified-rejection"

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

  if timeout 45s "$sens" --t5m-pair "$source" "$physical" >"$dir/paired.out" 2>"$dir/paired.err"; then
    fail "$id" sens-physical "EQ-Type-rejection" "paired-accepted"
  fi
  if ! grep -Fq 'eq expects two atoms' "$dir/paired.err" ||
     ! grep -Fq 'kind=Type' "$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    fail "$id" sens-physical "EQ-Type" "unexpected-paired-error"
  fi
  if timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    fail "$id" sens-physical "EQ-Type-rejection" "standalone-accepted"
  fi
  if ! grep -Fq 'eq expects two atoms' "$dir/physical.err"; then
    cat "$dir/physical.err" >&2
    fail "$id" sens-physical "EQ-Type" "unexpected-standalone-error"
  fi

  sha256sum "$source" "$physical" >"$dir/sha256.txt"
  echo "::notice file=$source,title=SENS Lisp→T5M→SENS::PASS id=$id expected=EQ-Type direct=REJECTED paired=REJECTED physical=REJECTED"
  printf '%s\n' "id=$id source=$source expected=EQ-Type actual=EQ-Type" >>"$evidence/results.txt"
}

: >"$evidence/results.txt"
# Не маскуємо збої: всі незалежні закони запускаються, але хоч один RED
# робить загальний результат RED. Жодних substitute verdict з Rust/Python.
checked=0
passed=0
failed=0
failed_ids=()
run_case() {
  local id="$2"
  checked=$((checked + 1))
  if ( "$@" ); then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    failed_ids+=("$id")
    echo "::warning title=SENS Lisp/T5M::CONTINUE_AFTER_RED id=$id remaining_witnesses=will_run" >&2
  fi
}
# Повна пара власне мовного заперечення Д1: джерело тільки Lisp.
run_case run_law d1-not-positive tests/semantic/d1-not-law.lisp 1
run_case run_law d1-not-mutant tests/semantic/d1-not-mutant.lisp 0
run_case run_law d3-selection-positive tests/semantic/d3-d4-logic-selection-law.lisp 1
run_case run_law d3-selection-mutant tests/semantic/d3-d4-logic-selection-mutant.lisp 0
run_case run_law d3-demorgan-four-cases tests/semantic/d3-demorgan-truth-table-law.lisp 1
run_case run_law d3-demorgan-mutant tests/semantic/d3-demorgan-truth-table-mutant.lisp 0
# Д3: перша істинна гілка COND має пріоритет навіть коли повертає Д1:ні.
# Позитив і мутант проходять однаковий фізичний SENS/Zig/T5M коридор.
run_case run_law d3-cond-first-match-false-positive tests/semantic/d3-cond-first-match-false-law.lisp 1
run_case run_law d3-cond-first-match-false-mutant tests/semantic/d3-cond-first-match-false-mutant.lisp 0
run_case run_law d3-quote-short-circuit-positive tests/semantic/d3-cond-quote-lazy-law.lisp 1
run_case run_law d3-quote-short-circuit-mutant tests/semantic/d3-cond-quote-lazy-mutant.lisp 0
# QUOTE не обчислює цитовану форму: структура лишається даними.
run_case run_law d3-quote-inert-data-positive tests/semantic/language-law-quote-inertness.lisp 1
run_case run_law d3-quote-inert-data-mutant tests/semantic/language-mutant-quote-inertness.lisp 0
# Д4 EVAL: цитований Lisp повертає порожнечу, а мутант підміняє результат.
run_case run_law d4-eval-quote-positive tests/semantic/d4-eval-value-call-laws.lisp 1
run_case run_law d4-eval-quote-mutant tests/semantic/d4-eval-value-call-mutant.lisp 0
run_case run_law d4-late-binding-positive tests/semantic/d4-late-definition-binding-law.lisp 1
# D4: параметр внутрішньої LAMBDA повинен затінити зовнішній.
run_case run_law d4-parameter-shadow-positive tests/semantic/language-law-d4-parameter-shadowing.lisp 1
run_case run_law d4-parameter-shadow-mutant tests/semantic/language-mutant-d4-parameter-shadowing.lisp 0
# Передавання першокласного предиката — виключно Lisp-закон Д4.
# Композицію двох першокласних функцій і контрприклад формулює Lisp/SENS.
run_case run_law d4-higher-order-composition-positive tests/semantic/d4-higher-order-composition-law.lisp 1
run_case run_law d4-higher-order-composition-mutant tests/semantic/d4-higher-order-composition-mutant.lisp 0
run_case run_law d4-first-class-predicate-positive tests/semantic/d4-first-class-predicate-law.lisp 1
run_case run_law d4-first-class-predicate-mutant tests/semantic/d4-first-class-predicate-mutant.lisp 0
# D4 рекурсивна правильність списків: позитив та навмисне порушення.
run_case run_law d4-proper-list-positive tests/semantic/d4-proper-list-recursion-law.lisp 1
run_case run_law d4-proper-list-mutant tests/semantic/d4-proper-list-recursion-mutant.lisp 0

# Закон і мутант працюють із точно тим самим Lisp-кодом бенчмарку.
# Shell тільки з'єднує джерела; SENS визначає результат через Zig/T5M.
recursion_law_bundle="$evidence/d4-recursion-benchmark-positive.lisp"
recursion_mutant_bundle="$evidence/d4-recursion-benchmark-negative.lisp"
cat -- benchmarks/recursion.lisp tests/semantic/d4-recursion-benchmark-law.lisp > "$recursion_law_bundle"
cat -- benchmarks/recursion.lisp tests/semantic/d4-recursion-benchmark-mutant.lisp > "$recursion_mutant_bundle"
run_case run_law d4-recursion-benchmark-positive "$recursion_law_bundle" 1
run_case run_law d4-recursion-benchmark-mutant "$recursion_mutant_bundle" 0
sha256sum benchmarks/recursion.lisp tests/semantic/d4-recursion-benchmark-law.lisp tests/semantic/d4-recursion-benchmark-mutant.lisp > "$evidence/d4-recursion-inputs.sha256"
# Складені селектори Д4: шість тверджень у Lisp та точний D1-негатив.
run_case run_law d4-selector-composition-positive tests/semantic/d4-selector-composition-law.lisp 1
run_case run_law d4-selector-composition-mutant tests/semantic/d4-selector-composition-mutant.lisp 0
run_case run_law d4-escaped-closure-positive tests/semantic/d4-escaped-lexical-closure-law.lisp 1
run_case run_law d4-escaped-closure-mutant tests/semantic/d4-escaped-lexical-closure-mutant.lisp 0
# D4 lexical capture/shadowing: SENS Lisp — єдиний семантичний оракул.
# Замінює колишню Rust-перевірку арифметичного результату замикання.
run_case run_law d4-lexical-scope-positive tests/semantic/d4-lexical-scope-law.lisp 1
run_case run_law d4-lexical-scope-mutant tests/semantic/d4-lexical-scope-mutant.lisp 0
# Д4/Д5: двопараметровий виклик має зберігати порядок аргументів.
# Позитив і одноаргументна мутація проходять direct, Zig/T5M, paired, standalone.
# Лише Lisp формулює закон, shell звіряє кінцевий D1; Rust не є оракулом.
run_case run_law d4-d5-ordered-arguments-positive tests/semantic/language-law-d5-ordered-arguments-ukr.lisp 1
run_case run_law d4-d5-ordered-arguments-mutant tests/semantic/language-mutant-d5-ordered-arguments-ukr.lisp 0
# SRFI-1 list=: алгоритм з чинної lib/D11, очікувані предикати тільки в Lisp.
# Не тестуємо D11-операцію Rust-оракулом; Zig тільки кодує фізичні байти.
d11_list_equal_law_bundle="$evidence/d11-list-equality-positive.lisp"
d11_list_equal_mutant_bundle="$evidence/d11-list-equality-negative.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-law.lisp > "$d11_list_equal_law_bundle"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-mutant.lisp > "$d11_list_equal_mutant_bundle"
run_case run_law d11-srfi1-list-equality-positive "$d11_list_equal_law_bundle" 1
run_case run_law d11-srfi1-list-equality-mutant "$d11_list_equal_mutant_bundle" 0
sha256sum lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-law.lisp tests/semantic/d11-srfi1-list-equality-mutant.lisp > "$evidence/d11-list-equality-inputs.sha256"
# Фізичні закони Д3 не залежать від недопущеного виклику D6 LENGTH.
run_case run_law d3-structural-positive tests/semantic/d3-structural-native-t5m-law.lisp 1
run_case run_law d3-structural-mutant tests/semantic/d3-structural-native-t5m-mutant.lisp 0
run_case run_law d3-eq-atom-boundary-positive tests/semantic/d3-eq-atom-boundary-law.lisp 1
run_case run_law d3-eq-atom-boundary-mutant tests/semantic/d3-eq-atom-boundary-mutant.lisp 0
run_case run_eq_type_rejection d3-eq-nonatom-type-negative tests/semantic/d3-eq-nonatom-type-negative.lisp
# TRANSITIONAL #5854: арифметичні Lisp-свідки існують і перевіряються
# прямим SENS у ci.yml, але фізичний T5M не атестовано до реалізації LENGTH.
# Не оголошувати PASS і не замінювати семантику D6 хостовим оракулом.
echo "::warning file=tests/semantic/d5-arithmetic-native-t5m-law.lisp,title=TRANSITIONAL #5854::D6 LENGTH (D6 000000) поки невикличний у фізичному SENS; D5 T5M=NOT_CERTIFIED"
# Залежні закони Д11 SPAN/BREAK: мова задає і функції, і твердження.
# Цей повний Lisp-пакет кодується Zig/T5M і виконується фізичним SENS.
# Відокремлений .lisp-свідок не є автономною програмою — без lib/ він не викличний.
d11_span_bundle="$evidence/d11-srfi1-span-break-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-laws.lisp > "$d11_span_bundle"
sha256sum lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-laws.lisp > "$evidence/d11-srfi1-inputs.sha256"
run_case run_law d11-srfi1-span-break-physical "$d11_span_bundle" 1

# The result-status law stays in Ukrainian Lisp; only the runner bundles its admitted library.
result_status_bundle="$evidence/result-status-bundle.lisp"
cat lib/result-status.lisp tests/semantic/result-status-laws.lisp > "$result_status_bundle"
run_case run_law result-status-source "$result_status_bundle" 1
run_case run_bound_law unification-occurs-check-positive tests/semantic/unification-occurs-check-law.lisp 1
run_case run_bound_law unification-occurs-check-mutant tests/semantic/unification-occurs-check-mutant.lisp 0
if (( failed > 0 )); then
  echo "::error title=SENS Lisp/T5M::REGRESSION checked=$checked passed=$passed failed=$failed ids=${failed_ids[*]}" >&2
  exit 1
fi
echo "SENS_LISP_T5M_LAWS_PASS count=$checked passed=$passed failed=$failed physical=ZIG_T5M"
