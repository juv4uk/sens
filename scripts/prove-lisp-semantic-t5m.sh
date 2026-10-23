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

# Спочатку перевіряємо працездатність самого SENS-виконавця на наявному
# Lisp-свідку. Це перевірка запуску, НЕ семантичний оракул: точний D1
# нижче доводить run_law. Якщо Core4/reader зламаний глобально, не
# класифікуємо десятки залежних тестів як незалежні мовні REGRESSION.
bootstrap_source="tests/semantic/d1-not-law.lisp"
if [[ ! -f "$bootstrap_source" || -L "$bootstrap_source" ]]; then
  echo "::error::SENS_BOOTSTRAP_SOURCE_INVALID source=$bootstrap_source" >&2
  exit 2
fi
if ! timeout 45s "$sens" "$bootstrap_source" >"$evidence/bootstrap.stdout" 2>"$evidence/bootstrap.stderr"; then
  cat "$evidence/bootstrap.stderr" >&2
  echo "::error::SENS_BOOTSTRAP_BLOCKED layer=executor source=$bootstrap_source checked=0 semantic=NOT_CERTIFIED release=NOT_CERTIFIED" >&2
  exit 2
fi
echo "SENS_BOOTSTRAP_EXECUTABLE source=$bootstrap_source semantic=NOT_CERTIFIED"

fail() {
  local id="$1" layer="$2" expected="$3" actual="$4"
  echo "::error title=SENS Lisp/T5M::REGRESSION id=$id layer=$layer expected=$expected actual=$actual" >&2
  exit 1
}

# Доказовий розбір червоного маршруту: жодних підмін вердикту чи допуску.
# Показуємо обидва реальні потоки й першу різницю, не лише "divergent".
report_output_divergence() {
  local id="$1" left_name="$2" left="$3" right_name="$4" right="$5"
  printf 'T5M_OUTPUT_DIVERGENCE id=%s layer=carrier left=%s right=%s\n' \
    "$id" "$left_name" "$right_name" >&2
  wc -c "$left" "$right" >&2
  sha256sum "$left" "$right" >&2
  diff -u --label "$left_name" --label "$right_name" "$left" "$right" | head -n 40 >&2 || true
  fail "$id" carrier "$left_name-byte-exact-$right_name" divergent
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
    for error_log in "$dir/open.err" "$dir/inverse.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi
  # Розрізняємо помилку парного виконання та standalone: це різні шари.
  # Нативний SENS надає діагностику; shell не підміняє жоден Lisp-вердикт.
  if ! timeout 45s "$sens" --t5m-pair "$source" "$physical" >"$dir/paired.out" 2>"$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    fail "$id" sens-paired "source-matched-physical-execution" "rejected"
  fi
  if ! timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    cat "$dir/physical.err" >&2
    fail "$id" sens-standalone "standalone-physical-execution" "rejected"
  fi
  cmp -s "$dir/direct.out" "$dir/paired.out" ||
    report_output_divergence "$id" direct "$dir/direct.out" paired "$dir/paired.out"
  cmp -s "$dir/paired.out" "$dir/physical.out" ||
    report_output_divergence "$id" paired "$dir/paired.out" physical "$dir/physical.out"

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
    for error_log in "$dir/open.err" "$dir/inverse.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi
  # Розрізняємо помилку парного виконання та standalone: це різні шари.
  # Нативний SENS надає діагностику; shell не підміняє жоден Lisp-вердикт.
  if ! timeout 45s "$sens" --t5m-pair "$combined" "$physical" >"$dir/paired.out" 2>"$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    fail "$id" sens-paired "source-matched-physical-execution" "rejected"
  fi
  if ! timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    cat "$dir/physical.err" >&2
    fail "$id" sens-standalone "standalone-physical-execution" "rejected"
  fi
  cmp -s "$dir/direct.out" "$dir/paired.out" ||
    report_output_divergence "$id" direct "$dir/direct.out" paired "$dir/paired.out"
  cmp -s "$dir/paired.out" "$dir/physical.out" ||
    report_output_divergence "$id" paired "$dir/paired.out" physical "$dir/physical.out"

  actual="$(cat "$dir/physical.out")"
  [[ "$actual" == "$expected" ]] ||
    fail "$id" sens-logic "D1:$expected" "$actual"
  echo "::notice file=$source,title=SENS unification law::PASS id=$id D1=$actual native=SENS carrier=Zig/T5M"
  sha256sum "$source" lib/unify.lisp "$physical" >"$dir/sha256.txt"
  printf '%s\n' "id=$id source=$source dependency=lib/unify.lisp expected=D1:$expected actual=D1:$actual" >>"$evidence/results.txt"
}

# Негатив типу: мовний текст застосовує EQ до пари й атома.
# Не перетворюємо Type у false; транспорт лише зберігає фізичну форму.
run_type_rejection() {
  local id="$1" source="$2" diagnostic="$3" dir physical
  dir="$evidence/$id"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  test -f "$source" && test ! -L "$source" ||
    fail "$id" source "regular-Lisp" "missing-or-symlink"

  if timeout 45s "$sens" "$source" >"$dir/direct.out" 2>"$dir/direct.err"; then
    fail "$id" sens-direct "Type-rejection" "unexpected-success"
  fi
  grep -Fq "$diagnostic" "$dir/direct.err" ||
    fail "$id" sens-direct "expected-Type-diagnostic" "unclassified-rejection"

  if ! timeout 45s "$sens" --t5m-mint "$source" "$physical" >"$dir/mint.out" 2>"$dir/mint.err"; then
    cat "$dir/mint.err" >&2
    fail "$id" codec "T5M-mint" "rejected"
  fi
  test -s "$physical" || fail "$id" codec "nonempty-T5M" "empty"
  if ! timeout 45s "$trit" open "$physical" >"$dir/program" 2>"$dir/open.err" ||
     ! timeout 45s "$trit" verify-view "$physical" >"$dir/inverse.out" 2>"$dir/inverse.err"; then
    for error_log in "$dir/open.err" "$dir/inverse.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi

  if timeout 45s "$sens" --t5m-pair "$source" "$physical" >"$dir/paired.out" 2>"$dir/paired.err"; then
    fail "$id" sens-physical "Type-rejection" "paired-accepted"
  fi
  if ! grep -Fq "$diagnostic" "$dir/paired.err" ||
     ! grep -Fq 'kind=Type' "$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    fail "$id" sens-physical "Type" "unexpected-paired-error"
  fi
  if timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    fail "$id" sens-physical "Type-rejection" "standalone-accepted"
  fi
  if ! grep -Fq "$diagnostic" "$dir/physical.err"; then
    cat "$dir/physical.err" >&2
    fail "$id" sens-physical "Type" "unexpected-standalone-error"
  fi

  sha256sum "$source" "$physical" >"$dir/sha256.txt"
  echo "::notice file=$source,title=SENS Lisp→T5M→SENS::PASS id=$id expected=Type diagnostic=$diagnostic direct=REJECTED paired=REJECTED physical=REJECTED"
  printf '%s\n' "id=$id source=$source expected=Type actual=Type" >>"$evidence/results.txt"
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
    # Помилка завантаження спільного Core/process/macro шару не є незалежною
    # регресією кожного Lisp-свідка. Нативний SENS уже записав справжню
    # причину у direct.err. Зупиняємо цей набір без 69 повторних запусків,
    # але з обов'язковим RED; звичайні мовні збої надалі збираємо всі.
    if [[ -f "$evidence/$id/direct.err" ]] &&
       grep -Eq '^Error loading (process|core|macro|utf8|fs)[.]lisp:' "$evidence/$id/direct.err"; then
      echo "::error title=SENS bootstrap::REGRESSION id=$id layer=bootstrap expected=language-libraries-installed actual=startup-rejected remaining_witnesses=NOT_RUN" >&2
      exit 1
    fi
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
# Д3: перша вибрана гілка зберігає D3 NIL як структуру, не як D1:NO.
run_case run_law d3-cond-first-match-nil-positive tests/semantic/d3-cond-first-match-nil-law.lisp 1
run_case run_law d3-cond-first-match-nil-mutant tests/semantic/d3-cond-first-match-nil-mutant.lisp 0
run_case run_law d3-quote-short-circuit-positive tests/semantic/d3-cond-quote-lazy-law.lisp 1
run_case run_law d3-quote-short-circuit-mutant tests/semantic/d3-cond-quote-lazy-mutant.lisp 0
# QUOTE не обчислює цитовану форму: структура лишається даними.
run_case run_law d3-quote-inert-data-positive tests/semantic/language-law-quote-inertness.lisp 1
run_case run_law d3-quote-inert-data-mutant tests/semantic/language-mutant-quote-inertness.lisp 0
# Д4 EVAL: цитований Lisp повертає порожнечу, а мутант підміняє результат.
run_case run_law d4-eval-quote-positive tests/semantic/d4-eval-value-call-laws.lisp 1
run_case run_law d4-eval-quote-mutant tests/semantic/d4-eval-value-call-mutant.lisp 0
run_case run_law d4-lambda-application-positive tests/semantic/d4-lambda-application-law.lisp 1
run_case run_law d4-lambda-application-mutant tests/semantic/d4-lambda-application-mutant.lisp 0
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
# Відокремити форму атома/списку в рекурсії від власне обчислення.
run_case run_law d4-recursion-input-shapes-positive tests/semantic/d4-recursion-input-shapes-law.lisp 1
run_case run_law d4-recursion-input-shapes-mutant tests/semantic/d4-recursion-input-shapes-mutant.lisp 0
# D7 текст у D2-рамці поки не гарантує атомність джерельного символу.
# Залишаємо окремий чесний RED, а не змінюємо значення D3 ATOM чи очікуємо SKIP.
run_case run_law d4-recursion-d7-atom-parity tests/semantic/d4-recursion-d7-atom-parity-law.lisp 1
run_case run_law d4-recursion-benchmark-positive "$recursion_law_bundle" 1
run_case run_law d4-recursion-benchmark-mutant "$recursion_mutant_bundle" 0
# Ізолюємо D3 атомну рівність від D8 структурної рівності в тому самому обході.
# Це окрема позитивна/негативна пара SENS, не підміна червоного D8-тесту.
recursion_atom_law_bundle="$evidence/d4-recursion-atom-positive.lisp"
recursion_atom_mutant_bundle="$evidence/d4-recursion-atom-negative.lisp"
cat -- benchmarks/recursion.lisp tests/semantic/d4-recursion-atom-result-law.lisp > "$recursion_atom_law_bundle"
cat -- benchmarks/recursion.lisp tests/semantic/d4-recursion-atom-result-mutant.lisp > "$recursion_atom_mutant_bundle"
run_case run_law d4-recursion-atom-positive "$recursion_atom_law_bundle" 1
run_case run_law d4-recursion-atom-mutant "$recursion_atom_mutant_bundle" 0
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
# Залежний свідок Д11 FIND-TAIL має виконуватись із бібліотекою, а не окремо.
# Прямий Lisp, Zig/T5M, парне та фізичне SENS виконують тотожний пакет.
d11_find_tail_bundle="$evidence/d11-srfi1-find-tail-complete.lisp"
cat -- lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-laws.lisp > "$d11_find_tail_bundle"
run_case run_law d11-srfi1-find-tail-physical "$d11_find_tail_bundle" 1
sha256sum lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-laws.lisp > "$evidence/d11-find-tail-inputs.sha256"
# Фізичні закони Д3 не залежать від недопущеного виклику D6 LENGTH.
run_case run_law d3-structural-positive tests/semantic/d3-structural-native-t5m-law.lisp 1
run_case run_law d3-structural-mutant tests/semantic/d3-structural-native-t5m-mutant.lisp 0
# Ізолювати D8 структурну рівність D7-даних від рекурсії/уніфікації.
# Обидва свідки проходять direct, Zig/T5M, paired та standalone SENS.
run_case run_law d8-d7-equal-physical-positive tests/semantic/d8-d7-equal-physical-law.lisp 1
run_case run_law d8-d7-equal-physical-mutant tests/semantic/d8-d7-equal-physical-mutant.lisp 0
# D1 хибне значення як голова CONS ≠ порожній D3-список.
# Обидва результати вираховує Lisp/SENS; Zig лише фізично переносить слова.
run_case run_law d3-d1-false-cons-head-positive tests/semantic/language-law-d3-d1-false-head-ukr.lisp 1
run_case run_law d3-d1-false-cons-head-mutant tests/semantic/language-mutant-d3-d1-false-head-ukr.lisp 0
# Д3: два різні атоми в CONS мають зберігати позиції; негатив ловить їх підміну.
run_case run_law d3-cons-ordered-atoms-positive tests/semantic/language-law-d3-cons-order-ukr.lisp 1
run_case run_law d3-cons-ordered-atoms-mutant tests/semantic/language-mutant-d3-cons-order-ukr.lisp 0
# Д3 CONS допускає атомний (крапковий) хвіст: CAR/CDR повертають точні атоми.
# Мутант перевіряє хибну підміну хвоста головою; семантичні вердикти лише Lisp/SENS.
run_case run_law d3-cons-dotted-tail-positive tests/semantic/d3-cons-dotted-tail-law.lisp 1
run_case run_law d3-cons-dotted-tail-mutant tests/semantic/d3-cons-dotted-tail-mutant.lisp 0
run_case run_law d3-eq-atom-boundary-positive tests/semantic/d3-eq-atom-boundary-law.lisp 1
run_case run_law d3-eq-atom-boundary-mutant tests/semantic/d3-eq-atom-boundary-mutant.lisp 0
run_case run_type_rejection d3-eq-nonatom-type-negative tests/semantic/d3-eq-nonatom-type-negative.lisp 'eq expects two atoms'
# Д3 селектори на порожньому D3 NIL повинні дати точний Type у всіх носіях.
run_case run_type_rejection d3-car-empty-list-type-negative tests/semantic/d3-car-empty-list-type-negative.lisp 'car expects a non-empty list'
run_case run_type_rejection d3-cdr-empty-list-type-negative tests/semantic/d3-cdr-empty-list-type-negative.lisp 'cdr expects a non-empty list'
run_case run_type_rejection d3-cond-nil-condition-type-negative tests/semantic/d3-cond-nil-condition-type-negative.lisp 'D3:110 COND expects exact D1:1 / D1:0'
# D4 NOT — часткова функція тільки над D1 PredicateBit, ніколи над структурним NIL.
run_case run_type_rejection d4-not-nonpredicate-type-negative tests/semantic/d4-not-nonpredicate-type-negative.lisp 'NOT requires an exact D1 PredicateBit'
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
# Д11 Clojure: два комплекти законів перенесено з Rust у справжній Lisp.
# Їхня залежність SRFI-1 SPAN завантажується перед DEFINE групування.
for suite in d11-clojure-partition-by d11-clojure-dedupe; do
  combined="$evidence/$suite-complete.lisp"
  cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp "tests/semantic/$suite-laws.lisp" > "$combined"
  run_case run_law "$suite-physical" "$combined" 1
done

# The result-status law stays in Ukrainian Lisp; only the runner bundles its admitted library.
result_status_bundle="$evidence/result-status-bundle.lisp"
cat lib/result-status.lisp tests/semantic/result-status-laws.lisp > "$result_status_bundle"
run_case run_law result-status-source "$result_status_bundle" 1
# Незалежна Lisp-пара локалізує правильний UNKNOWN проти крапкового D7-хвоста.
# Shell лише завантажує реальні визначення; D1:так/ні визначає сам SENS.
result_status_dotted_law_bundle="$evidence/result-status-dotted-positive.lisp"
result_status_dotted_mutant_bundle="$evidence/result-status-dotted-mutant.lisp"
cat -- lib/result-status.lisp tests/semantic/result-status-dotted-law.lisp > "$result_status_dotted_law_bundle"
cat -- lib/result-status.lisp tests/semantic/result-status-dotted-mutant.lisp > "$result_status_dotted_mutant_bundle"
run_case run_law result-status-dotted-positive "$result_status_dotted_law_bundle" 1
run_case run_law result-status-dotted-mutant "$result_status_dotted_mutant_bundle" 0
# Локалізуємо фізичну розбіжність: форма змінної → входження → повна уніфікація.
# Визначення й закон належать тільки Lisp, Shell лише додає lib/unify.lisp.
# Незалежно локалізуємо D3/D4 форму змінної: позитив, негатив і мутант.
run_case run_bound_law unification-variable-shape-positive tests/semantic/unification-variable-shape-positive.lisp 1
run_case run_bound_law unification-variable-shape-negative tests/semantic/unification-variable-shape-negative.lisp 1
run_case run_bound_law unification-variable-shape-mutant tests/semantic/unification-variable-shape-mutant.lisp 0
# Узгодженість конструктора і предиката перевіряє SENS після фізичного Zig/T5M.
run_case run_bound_law unification-constructor-positive tests/semantic/unification-constructor-law.lisp 1
run_case run_bound_law unification-constructor-mutant tests/semantic/unification-constructor-mutant.lisp 0
run_case run_bound_law unification-variable-shape tests/semantic/unification-variable-shape-law.lisp 1
run_case run_bound_law unification-occurs-predicate-positive tests/semantic/unification-occurs-predicate-law.lisp 1
run_case run_bound_law unification-occurs-predicate-mutant tests/semantic/unification-occurs-predicate-mutant.lisp 0
run_case run_bound_law unification-occurs-check-positive tests/semantic/unification-occurs-check-law.lisp 1
run_case run_bound_law unification-occurs-check-mutant tests/semantic/unification-occurs-check-mutant.lisp 0
if (( failed > 0 )); then
  echo "::error title=SENS Lisp/T5M::REGRESSION checked=$checked passed=$passed failed=$failed ids=${failed_ids[*]}" >&2
  exit 1
fi
echo "SENS_LISP_T5M_LAWS_PASS count=$checked passed=$passed failed=$failed physical=ZIG_T5M"
