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

# Невід'ємність вимірів і справжні коди виходу перевіряє сам Bash-механізм.
bash scripts/test_law_stage_clock.sh
bash scripts/test_sens_law_hotspots_empty.sh

fail() {
  local id="$1" layer="$2" expected="$3" actual="$4"
  # Передаємо точний шар відмови до квитанції, без повторної евристики stderr.
  if [[ -d "$evidence/$id" ]]; then
    printf '%s\n' "$layer" > "$evidence/$id/failure-layer.txt"
  fi
  echo "::error title=SENS Lisp/T5M::REGRESSION id=$id layer=$layer expected=$expected actual=$actual" >&2
  exit 1
}

# Діагностичний бенчмарк етапів *реального* Lisp → Zig/T5M → SENS.
# Вимірюємо повний процес кожного етапу (запуск CLI включно), без host-оракула.
# Одна проба на етап: це профіль для пошуку вузького місця, НЕ p50 або speedup.
profile_stage() {
  local id="$1" stage="$2" started_us ended_us elapsed_us code=0
  shift 2
  # Одна назва sens-standalone раніше змішувала різні виконувані CLI.
  # Маршрут — частина виміру; заміна runner не може виглядати як speedup.
  if [[ "$stage" == sens-standalone ]]; then
    if [[ "${1:-}" == timeout && "${3:-}" == "$sens" ]]; then
      stage=sens-standalone-sens
    elif [[ "${1:-}" == timeout && "${3:-}" == "$trit" && "${4:-}" == eval ]]; then
      stage=sens-standalone-trit-clean
    elif [[ "${1:-}" == timeout && "${3:-}" == "$trit" && "${4:-}" == eval-core4 ]]; then
      stage=sens-standalone-trit-core4
    else
      echo "::error::SENS_STAGE_EXECUTOR_UNKNOWN id=$id stage=$stage" >&2
      return 2
    fi
  fi
  # Bash-годинник без fork/exec: зовнішній date спотворює короткі етапи.
  started_us="${EPOCHREALTIME/./}"
  "$@" || code=$?
  ended_us="${EPOCHREALTIME/./}"
  elapsed_us="$((ended_us - started_us))"
  printf '%s\t%s\t%s\t%s\n' "$id" "$stage" "$code" "$elapsed_us" >> "$evidence/law-stage-timings.tsv"
  return "$code"
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

# Прямий SENS уже прочитав файл, коли повідомляє невідоме зв'язування.
# Це не помилка reader-а й не доказ хибності семантичного закону.
# Класифікація стосується тільки діагностики; сам RED залишається RED.
direct_failure_layer() {
  local log="$1"
  if grep -Fq 'a lexical slot has no source datum' "$log"; then
    printf '%s\n' 'sens-lexical-binding'
  elif grep -Fq 'macros must return proper lists' "$log"; then
    printf '%s\n' 'sens-macro-expansion'
  elif grep -Fq 'domain identity is not callable under its ratified law: D6 ' "$log"; then
    printf '%s\n' 'sens-d6-admission'
  elif grep -Fq 'domain identity is not callable under its ratified law: D7 ' "$log"; then
    printf '%s\n' 'sens-d7-admission'
  elif grep -Fq 'domain identity is not callable under its ratified law' "$log"; then
    printf '%s\n' 'sens-admission'
  elif grep -Fq 'unknown symbol' "$log"; then
    printf '%s\n' 'sens-binding'
  elif grep -Fq 'Parse error:' "$log"; then
    printf '%s\n' 'lisp-reader'
  elif grep -Eq 'kind=Type|expects a non-empty list|expects two atoms' "$log"; then
    printf '%s\n' 'sens-direct-type'
  else
    printf '%s\n' 'sens-direct'
  fi
}

# Не плутати відмову допуску D6 чи D7-структури з несправним кодеком.
# Це лише точні шари діагностики: кожен випадок лишається RED.
paired_failure_layer() {
  local log="$1"
  if grep -Fq 'domain identity is not callable under its ratified law: D6 ' "$log"; then
    printf '%s\n' 'sens-d6-admission'
  elif grep -Fq 'domain identity is not callable under its ratified law: D7 ' "$log"; then
    printf '%s\n' 'sens-d7-admission'
  elif grep -Fq 'domain identity is not callable under its ratified law' "$log"; then
    printf '%s\n' 'sens-admission'
  elif grep -Fq 'unknown Text7 binding' "$log"; then
    printf '%s\n' 'sens-binding'
  elif grep -Eq 'car expects a non-empty list|eq expects two atoms|kind=Type' "$log"; then
    printf '%s\n' 'sens-paired-type'
  else
    printf '%s\n' 'sens-paired'
  fi
}

# Квитанція RED: індекс фізичної форми зіставляємо з рядком Lisp.
# Це діагностика джерела, а не мовний оракул і не новий допуск.
# Перелік форм із дужкою в першій колонці є лише candidate mapping.
report_physical_red_source() {
  local id="$1" source="$2" physical="$3" error_log="$4"
  local report="$evidence/$id/form-location.txt" line
  # Лексично скануємо КОЖНУ верхньорівневу форму, а не /^(/ першої колонки.
  # Коментарі, цитовані рядки та екрановані дужки не додають форм.
  if ! bash scripts/diagnose-sens-physical-form.sh "$source" "$error_log" "$id" >"$report" 2>&1; then
    echo "::warning title=SENS form-location::id=$id candidate=UNRESOLVED status=RED" >&2
  fi
  cat "$report" >&2
  line="$(sed -n 's/.* source_line=\([0-9][0-9]*\) lexical_form_count=.*/\1/p' "$report" | head -n1)"
  if [[ "$line" =~ ^[0-9]+$ ]]; then
    echo "::error file=$source,line=$line,title=SENS physical failure::RED id=$id source_form=CANDIDATE semantic=NOT_ASSERTED" >&2
  fi
  sha256sum "$source" "$physical" >&2
}

run_law() {
  local id="$1" source="$2" expected="$3" dir physical actual
  local profile="${4:-clean}"
  local -a paired_args=()
  local standalone_verb=eval
  case "$profile" in
    clean) ;;
    core4) paired_args=(--core4-runtime); standalone_verb=eval-core4 ;;
    *) fail "$id" harness "profile=clean-or-core4" "$profile" ;;
  esac
  dir="$evidence/$id"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  test -f "$source" && test ! -L "$source" ||
    fail "$id" source "regular-Lisp" "missing-or-symlink"

  # Семантичний доказ не записує очікувану логіку іншою мовою.
  if ! profile_stage "$id" direct timeout 45s "$sens" "$source" >"$dir/direct.out" 2>"$dir/direct.err"; then
    cat "$dir/direct.err" >&2
    fail "$id" "$(direct_failure_layer "$dir/direct.err")" "SENS-execution" "rejected"
  fi
  # Кодек створює байти T5M; Zig відкриває і перевіряє точне подання.
  if ! profile_stage "$id" codec-mint timeout 45s "$sens" --t5m-mint-pair "$source" "$physical" >"$dir/mint.out" 2>"$dir/mint.err"; then
    cat "$dir/mint.err" >&2
    fail "$id" codec "T5M-mint" "rejected"
  fi
  test -s "$physical" || fail "$id" codec "nonempty-T5M" "empty"
  if ! profile_stage "$id" zig-open timeout 45s "$trit" open "$physical" >"$dir/program" 2>"$dir/open.err" ||
     ! profile_stage "$id" zig-verify timeout 45s "$trit" verify-view "$physical" >"$dir/inverse.out" 2>"$dir/inverse.err"; then
    for error_log in "$dir/open.err" "$dir/inverse.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi
  # Розрізняємо парний і самостійний фізичні шляхи, але профіль Core4
  # має відповідати прямому Lisp та парному виконавцю. Байтам усе ще немає
  # доступу до source чи binding-source: sens-trit декодує лише фізичний
  # .sens, а Core4 явно підвантажує SENS, як вимагає контракт цих законів.
  if ! profile_stage "$id" sens-paired timeout 45s "$sens" --t5m-pair "$source" "$physical" "${paired_args[@]}" >"$dir/paired.out" 2>"$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    report_physical_red_source "$id" "$source" "$physical" "$dir/paired.err"
    # Діагностика відмінності середовищ: прямий файл має Core4,
    # а парний фізичний маршрут запускається в чистому SENS.
    # Код виходу 0 означає лише завершення процесу, не PASS мовного свідка.
    # Додатковий запуск ніколи не змінює RED на PASS.
    if [[ "$profile" == clean ]] && grep -Fq 'domain identity is not callable under its ratified law: D7 ' "$dir/paired.err"; then
      if profile_stage "$id" sens-paired-core4-diagnostic timeout 45s "$sens" \
        --t5m-pair "$source" "$physical" --core4-runtime \
        >"$dir/paired-core4.out" 2>"$dir/paired-core4.err"; then
        if cmp -s "$dir/direct.out" "$dir/paired-core4.out"; then
          echo "SENS_D7_PROFILE_DIAGNOSTIC id=$id clean=RED core4=EXIT0 output=BYTE_PARITY verdict=RED" >&2
        else
          echo "SENS_D7_PROFILE_DIAGNOSTIC id=$id clean=RED core4=EXIT0 output=DIVERGENT verdict=RED" >&2
          sha256sum "$dir/direct.out" "$dir/paired-core4.out" >&2
        fi
      else
        echo "SENS_D7_PROFILE_DIAGNOSTIC id=$id clean=RED core4=EXIT_NONZERO verdict=RED" >&2
        sed -n '1,8p' "$dir/paired-core4.err" >&2
      fi
    fi
    fail "$id" "$(paired_failure_layer "$dir/paired.err")" "source-matched-physical-execution" "rejected"
  fi
  # Парний і автономний SENS мають виконувати той самий мовний профіль.
  if ! profile_stage "$id" sens-standalone timeout 45s "$trit" "$standalone_verb" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
    cat "$dir/physical.err" >&2
    fail "$id" sens-standalone "standalone-physical-execution-$profile" "rejected"
  fi
  cmp -s "$dir/direct.out" "$dir/paired.out" ||
    report_output_divergence "$id" direct "$dir/direct.out" paired "$dir/paired.out"
  cmp -s "$dir/paired.out" "$dir/physical.out" ||
    report_output_divergence "$id" paired "$dir/paired.out" physical "$dir/physical.out"

  actual="$(cat "$dir/physical.out")"
  if [[ "$actual" != "$expected" ]]; then
    fail "$id" sens-logic "result:$expected" "$actual"
  fi
  echo "::notice file=$source,title=SENS Lisp→T5M→SENS::PASS id=$id result=$actual native=SENS"
  sha256sum "$source" "$physical" >"$dir/sha256.txt"
  printf '%s\n' "id=$id source=$source expected=$expected actual=$actual" >>"$evidence/results.txt"
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

  if ! profile_stage "$id" direct timeout 45s "$sens" "$combined" >"$dir/direct.out" 2>"$dir/direct.err"; then
    cat "$dir/direct.err" >&2
    fail "$id" "$(direct_failure_layer "$dir/direct.err")" "SENS-execution" "rejected"
  fi
  if ! profile_stage "$id" codec-mint timeout 45s "$sens" --t5m-mint-pair "$combined" "$physical" >"$dir/mint.out" 2>"$dir/mint.err"; then
    cat "$dir/mint.err" >&2
    fail "$id" codec "T5M-mint" "rejected"
  fi
  test -s "$physical" || fail "$id" codec "nonempty-T5M" "empty"
  if ! profile_stage "$id" zig-open timeout 45s "$trit" open "$physical" >"$dir/program" 2>"$dir/open.err" ||
     ! profile_stage "$id" zig-verify timeout 45s "$trit" verify-view "$physical" >"$dir/inverse.out" 2>"$dir/inverse.err"; then
    for error_log in "$dir/open.err" "$dir/inverse.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi
  # Розрізняємо помилку парного виконання та standalone: це різні шари.
  # Нативний SENS надає діагностику; shell не підміняє жоден Lisp-вердикт.
  if ! profile_stage "$id" sens-paired timeout 45s "$sens" --t5m-pair "$combined" "$physical" >"$dir/paired.out" 2>"$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    fail "$id" "$(paired_failure_layer "$dir/paired.err")" "source-matched-physical-execution" "rejected"
  fi
  if ! profile_stage "$id" sens-standalone timeout 45s "$sens" "$physical" >"$dir/physical.out" 2>"$dir/physical.err"; then
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
run_error_rejection() {
  # Перевіряємо названий клас помилки на прямому, парному та фізичному шляху.
  # Bash лише класифікує справжню діагностику SENS, не створює семантичний вирок.
  local id="$1" source="$2" expected_kind="$3" diagnostic="$4" dir physical
  local profile="${5:-clean}"
  local -a paired_args=() physical_command=()
  dir="$evidence/$id"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  case "$profile" in
    clean) physical_command=("$sens" "$physical") ;;
    core4)
      paired_args=(--core4-runtime)
      physical_command=("$trit" eval-core4 "$physical")
      ;;
    *) fail "$id" harness "profile=clean-or-core4" "$profile" ;;
  esac
  test -f "$source" && test ! -L "$source" ||
    fail "$id" source "regular-Lisp" "missing-or-symlink"

  if profile_stage "$id" direct timeout 45s "$sens" "$source" >"$dir/direct.out" 2>"$dir/direct.err"; then
    fail "$id" sens-direct "$expected_kind-rejection" "unexpected-success"
  fi
  if ! grep -Fq "$diagnostic" "$dir/direct.err"; then
    cat "$dir/direct.err" >&2
    fail "$id" sens-direct "expected-$expected_kind-diagnostic" "unclassified-rejection"
  fi

  if ! profile_stage "$id" codec-mint timeout 45s "$sens" --t5m-mint-pair "$source" "$physical" >"$dir/mint.out" 2>"$dir/mint.err"; then
    cat "$dir/mint.err" >&2
    fail "$id" codec "T5M-mint" "rejected"
  fi
  test -s "$physical" || fail "$id" codec "nonempty-T5M" "empty"
  if ! profile_stage "$id" zig-open timeout 45s "$trit" open "$physical" >"$dir/program" 2>"$dir/open.err" ||
     ! profile_stage "$id" zig-verify timeout 45s "$trit" verify-view "$physical" >"$dir/inverse.out" 2>"$dir/inverse.err"; then
    for error_log in "$dir/open.err" "$dir/inverse.err"; do
      if [[ -f "$error_log" ]]; then cat "$error_log" >&2; fi
    done
    fail "$id" zig-transport "canonical-roundtrip" "rejected"
  fi

  if profile_stage "$id" sens-paired timeout 45s "$sens" --t5m-pair "$source" "$physical" "${paired_args[@]}" >"$dir/paired.out" 2>"$dir/paired.err"; then
    fail "$id" sens-physical "$expected_kind-rejection" "paired-accepted"
  fi
  if ! grep -Fq "$diagnostic" "$dir/paired.err" ||
     ! grep -Fq "kind=$expected_kind" "$dir/paired.err"; then
    cat "$dir/paired.err" >&2
    fail "$id" sens-physical "$expected_kind" "unexpected-paired-error"
  fi
  if profile_stage "$id" sens-standalone timeout 45s "${physical_command[@]}" >"$dir/physical.out" 2>"$dir/physical.err"; then
    fail "$id" sens-physical "$expected_kind-rejection" "standalone-accepted"
  fi
  if ! grep -Fq "$diagnostic" "$dir/physical.err"; then
    cat "$dir/physical.err" >&2
    fail "$id" sens-physical "$expected_kind" "unexpected-standalone-error"
  fi

  sha256sum "$source" "$physical" >"$dir/sha256.txt"
  echo "::notice file=$source,title=SENS Lisp→T5M→SENS::PASS id=$id expected=$expected_kind diagnostic=$diagnostic direct=REJECTED paired=REJECTED physical=REJECTED"
  printf '%s\n' "id=$id source=$source expected=$expected_kind actual=$expected_kind" >>"$evidence/results.txt"
}

run_type_rejection() {
  run_error_rejection "$1" "$2" Type "$3"
}

run_division_by_zero_rejection() {
  run_error_rejection "$1" "$2" DivisionByZero "$3" core4
}

: >"$evidence/results.txt"
# Не маскуємо збої: всі незалежні закони запускаються, але хоч один RED
# робить загальний результат RED. Жодних substitute verdict з Rust/Python.
checked=0
passed=0
failed=0
failed_ids=()
# Спільні причини RED — діагностика, не мовний оракул і не карантин.
red_d7_ids=()
red_d3_car_ids=()
red_d3_cdr_ids=()
red_other_ids=()
# Час кожного реального SENS→Zig/T5M→SENS виконання; не мовний оракул.
# Одна проба на свідок: діагностичний wall-time, не p50 і не порівняння мов.
printf 'id\tstatus\twall_ms\n' > "$evidence/law-timings.tsv"
printf 'id\tstage\texit\telapsed_us\n' > "$evidence/law-stage-timings.tsv"
# Відтворювані докази RED без додаткових запусків SENS або кодека.
# source/input, фізичний носій, бітовий перегляд і точна позиція відмови.
printf 'id\tlayer\tsource_sha256\tphysical_sha256\tview_sha256\tphysical_form_index\n' > "$evidence/law-red-receipts.tsv"
red_receipt() {
  local id="$1" source_path="$2" dir="$evidence/$1"
  local source_hash=NOT_PRODUCED physical_hash=NOT_PRODUCED view_hash=NOT_PRODUCED
  local form_index=NOT_REPORTED layer=NOT_CLASSIFIED line
  if [[ -f "$source_path" && ! -L "$source_path" ]]; then
    source_hash="$(sha256sum "$source_path" | cut -d' ' -f1)"
  fi
  if [[ -f "$dir/program.sens" && ! -L "$dir/program.sens" ]]; then
    physical_hash="$(sha256sum "$dir/program.sens" | cut -d' ' -f1)"
  fi
  if [[ -f "$dir/program" && ! -L "$dir/program" ]]; then
    view_hash="$(sha256sum "$dir/program" | cut -d' ' -f1)"
  fi
  if [[ -s "$dir/failure-layer.txt" ]]; then
    layer="$(head -n 1 "$dir/failure-layer.txt")"
  elif [[ -f "$dir/paired.err" ]]; then
    layer="$(paired_failure_layer "$dir/paired.err")"
  elif [[ -f "$dir/direct.err" ]]; then
    layer="$(direct_failure_layer "$dir/direct.err")"
  fi
  # Шар відмови та індекс фізичної форми — незалежні поля квитанції.
  # fail() уже записав шар, але paired.err усе одно містить точну позицію.
  if [[ -f "$dir/paired.err" ]]; then
    while IFS= read -r line; do
      if [[ "$line" =~ physical_form_index=([0-9]+) ]]; then
        form_index="${BASH_REMATCH[1]}"
        break
      fi
    done < "$dir/paired.err"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$id" "$layer" "$source_hash" "$physical_hash" "$view_hash" "$form_index" \
    >> "$evidence/law-red-receipts.tsv"
  echo "SENS_RED_RECEIPT id=$id layer=$layer source_sha256=$source_hash physical_sha256=$physical_hash view_sha256=$view_hash physical_form_index=$form_index file=$evidence/law-red-receipts.tsv"
}
run_case() {
  local id="$2" start_us end_us wall_ms status
  start_us="${EPOCHREALTIME/./}"
  checked=$((checked + 1))
  if ( "$@" ); then
    status=PASS
    passed=$((passed + 1))
  else
    status=RED
    failed=$((failed + 1))
    failed_ids+=("$id")
    # Цитата й фізичний індекс пояснюють один RED. Сама помилка лишається RED.
    red_receipt "$id" "${3:-}"
  fi
  end_us="${EPOCHREALTIME/./}"
  wall_ms="$(((end_us - start_us) / 1000))"
  printf '%s\t%s\t%s\n' "$id" "$status" "$wall_ms" >> "$evidence/law-timings.tsv"
  echo "SENS_LAW_WALL_TIME id=$id status=$status wall_ms=$wall_ms scope=full-execution"
  # Діагностика поза редиректами stdout/stderr справжнього SENS.
  while IFS=$'\t' read -r measured_id stage phase_code elapsed_us; do
    [[ "$measured_id" == "$id" ]] || continue
    echo "SENS_LAW_STAGE id=$id stage=$stage exit=$phase_code elapsed_us=$elapsed_us scope=full-process"
  done < "$evidence/law-stage-timings.tsv"
  if [[ "$status" == RED ]]; then
    # Класифікуємо фактичний paired.err, але не змінюємо failed чи статус.
    if [[ -f "$evidence/$id/paired.err" ]] &&
       grep -Fq 'domain identity is not callable under its ratified law: D7 ' "$evidence/$id/paired.err"; then
      red_d7_ids+=("$id")
    elif [[ -f "$evidence/$id/paired.err" ]] &&
         grep -Fq 'car expects a non-empty list' "$evidence/$id/paired.err"; then
      red_d3_car_ids+=("$id")
    elif [[ -f "$evidence/$id/paired.err" ]] &&
         grep -Fq 'cdr expects a non-empty list' "$evidence/$id/paired.err"; then
      red_d3_cdr_ids+=("$id")
    else
      red_other_ids+=("$id")
    fi
    # Вже документований борг D6 LENGTH: фізичне викликання ще не допущено.
    # TRANSITIONAL не змінює RED на PASS і не пропускає жодного свідка.
    if [[ -f "$evidence/$id/paired.err" ]] &&
       grep -Fq 'domain identity is not callable under its ratified law: D6 000000' "$evidence/$id/paired.err"; then
      echo "::warning title=TRANSITIONAL #5854::id=$id layer=sens-paired gate=D6_LENGTH physical=NOT_CERTIFIED status=RED" >&2
    fi
    # Спільне падіння bootstrap — не 69 незалежних семантичних регресій.
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
# Самоперевірка українського D3: EQ приймає тільки точні атоми.
run_case run_law d3-ukr-self-verdict tests/semantic/d3-ukr-language-self-verdict.lisp 1
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
# D3: після першого істинного guard наступний guard з CAR NIL не обчислюється.
# Позитив і негатив обов'язково проходять direct → Zig/T5M → paired → standalone.
run_case run_law d3-cond-guard-short-circuit-positive tests/semantic/d3-cond-guard-short-circuit-law.lisp 1
run_case run_law d3-cond-guard-short-circuit-mutant tests/semantic/d3-cond-guard-short-circuit-mutant.lisp 0
run_case run_law d3-quote-short-circuit-positive tests/semantic/d3-cond-quote-lazy-law.lisp 1
run_case run_law d3-quote-short-circuit-mutant tests/semantic/d3-cond-quote-lazy-mutant.lisp 0
# QUOTE не обчислює цитовану форму: структура лишається даними.
run_case run_law d3-quote-inert-data-positive tests/semantic/language-law-quote-inertness.lisp 1
run_case run_law d3-quote-inert-data-mutant tests/semantic/language-mutant-quote-inertness.lisp 0
# Одногліфовий D7 у викличній голові: лише вже зв'язаний параметр D4.
# Повний фізичний маршрут і негативний свідок зберігають точні D1 вердикти.
run_case run_law d7-single-glyph-bound-head-positive tests/semantic/d7-single-glyph-bound-head-law.lisp 1
run_case run_law d7-single-glyph-bound-head-mutant tests/semantic/d7-single-glyph-bound-head-mutant.lisp 0
# Д4 EVAL: цитований Lisp повертає порожнечу, а мутант підміняє результат.
run_case run_law d4-eval-quote-positive tests/semantic/d4-eval-value-call-laws.lisp 1
run_case run_law d4-eval-quote-mutant tests/semantic/d4-eval-value-call-mutant.lisp 0
run_case run_law d4-lambda-application-positive tests/semantic/d4-lambda-application-law.lisp 1
run_case run_law d4-lambda-application-mutant tests/semantic/d4-lambda-application-mutant.lisp 0
run_case run_law d4-late-binding-positive tests/semantic/d4-late-definition-binding-law.lisp 1
# Д4: негативний самовердикт повторного визначення, тільки Lisp/SENS.
run_case run_law d4-late-binding-redefinition-mutant tests/semantic/d4-late-definition-binding-mutant.lisp 0
# D4: параметр внутрішньої LAMBDA повинен затінити зовнішній.
run_case run_law d4-parameter-shadow-positive tests/semantic/language-law-d4-parameter-shadowing.lisp 1
run_case run_law d4-parameter-shadow-mutant tests/semantic/language-mutant-d4-parameter-shadowing.lisp 0
# Передавання першокласного предиката — виключно Lisp-закон Д4.
# Композицію двох першокласних функцій і контрприклад формулює Lisp/SENS.
run_case run_law d4-higher-order-composition-positive tests/semantic/d4-higher-order-composition-law.lisp 1
run_case run_law d4-higher-order-composition-mutant tests/semantic/d4-higher-order-composition-mutant.lisp 0
run_case run_law d4-first-class-predicate-positive tests/semantic/d4-first-class-predicate-law.lisp 1
run_case run_law d4-first-class-predicate-mutant tests/semantic/d4-first-class-predicate-mutant.lisp 0
# D6 COMPOSE/FLIP/CURRY are derived SENS functions, so their law and
# counterexample must pass the same physical Zig/T5M -> SENS route.
run_case run_law d6-compose-flip-positive tests/semantic/d6-compose-flip-law.lisp 1
run_case run_law d6-compose-flip-order-mutant tests/semantic/d6-compose-flip-mutant.lisp 0
# D6-квантори перевіряємо нижче як повні програми з визначеннями Core4.
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
# D3 гарячий SENS-бенчмарк: семантика належить Lisp, Zig тільки T5M.
d3_hot_law="$evidence/d3-proper-tail-hot-positive.lisp"
d3_hot_mutant="$evidence/d3-proper-tail-hot-mutant.lisp"
cat -- benchmarks/d3-proper-tail-hot.lisp tests/semantic/d3-proper-tail-hot-law.lisp > "$d3_hot_law"
cat -- benchmarks/d3-proper-tail-hot.lisp tests/semantic/d3-proper-tail-hot-mutant.lisp > "$d3_hot_mutant"
run_case run_law d3-proper-tail-hot-positive "$d3_hot_law" 1
run_case run_law d3-proper-tail-hot-mutant "$d3_hot_mutant" 0
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
# Д4: вибірка трьома селекторами; самовердикт D1 і хибний вибір цілі.
run_case run_law d4-selector-domain-positive tests/semantic/d4-selector-domain-law.lisp 1
run_case run_law d4-selector-domain-mutant tests/semantic/d4-selector-domain-mutant.lisp 0
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
# Сувора границя SRFI-1: неправильний D1-хвіст не можна приймати за NIL.
# Прямий SENS, Zig T5M і фізичний SENS мусять відхилити тим самим Type.
d11_find_tail_bad="$evidence/d11-srfi1-find-tail-improper-complete.lisp"
cat -- lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-improper-tail-negative.lisp > "$d11_find_tail_bad"
run_case run_type_rejection d11-find-tail-improper-d1-type-negative "$d11_find_tail_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-laws.lisp > "$evidence/d11-find-tail-inputs.sha256"
# Фізичні закони Д3 не залежать від недопущеного виклику D6 LENGTH.
run_case run_law d3-structural-positive tests/semantic/d3-structural-native-t5m-law.lisp 1
run_case run_law d3-structural-mutant tests/semantic/d3-structural-native-t5m-mutant.lisp 0
# Великий корпус Д3 як окремий Lisp-бенчмарк: direct, mint, Zig roundtrip,
# paired і standalone отримують фазові wall-time виміри, але не хост-вердикт.
run_case run_law d3-cons-batch-positive tests/semantic/d3-cons-batch-law.lisp 1
run_case run_law d3-cons-batch-mutant tests/semantic/d3-cons-batch-mutant.lisp 0
# Д3 COND: SENS сам доводить лінивий вибір гілки; негатив лишається D1:ні.
# Невибраний CAR над порожнечею є пасткою Type, але не повинен виконуватись.
run_case run_law d3-cond-lazy-positive tests/semantic/language-law-d3-cond-lazy-ukr.lisp 1
run_case run_law d3-cond-lazy-mutant tests/semantic/language-mutant-d3-cond-lazy-ukr.lisp 0
# Ізолювати D8 структурну рівність D7-даних від рекурсії/уніфікації.
# Обидва свідки проходять direct, Zig/T5M, paired та standalone SENS.
run_case run_law d8-d7-equal-physical-positive tests/semantic/d8-d7-equal-physical-law.lisp 1
run_case run_law d8-d7-equal-physical-mutant tests/semantic/d8-d7-equal-physical-mutant.lisp 0
# D8 STRING->SYMBOL уже визначений точним механізмом D8.
# Точні результати пари формує сам Lisp; Zig лише переносить T5M.
run_case run_law d8-string-symbol-roundtrip-positive tests/semantic/d8-string-symbol-roundtrip-law.lisp 1
run_case run_law d8-string-symbol-roundtrip-mutant tests/semantic/d8-string-symbol-roundtrip-mutant.lisp 0
# UTF-8 межі та D24+ частка/остача — мовні закони, не Rust-таблиця очікувань.
# Bash лише додає наявну Lisp-бібліотеку; пряме й фізичне виконання — справжній SENS.
utf8_boundary_law_bundle="$evidence/utf8-boundary-positive-complete.lisp"
utf8_boundary_mutant_bundle="$evidence/utf8-boundary-negative-complete.lisp"
cat -- lib/utf8.lisp tests/semantic/utf8-boundary-laws.lisp > "$utf8_boundary_law_bundle"
cat -- lib/utf8.lisp tests/semantic/utf8-boundary-mutant.lisp > "$utf8_boundary_mutant_bundle"
run_case run_law utf8-boundary-positive "$utf8_boundary_law_bundle" 1
run_case run_law utf8-boundary-mutant "$utf8_boundary_mutant_bundle" 0
utf8_quotient_law_bundle="$evidence/utf8-quotient-positive-complete.lisp"
utf8_quotient_mutant_bundle="$evidence/utf8-quotient-negative-complete.lisp"
cat -- lib/utf8.lisp tests/semantic/utf8-quotient-laws.lisp > "$utf8_quotient_law_bundle"
cat -- lib/utf8.lisp tests/semantic/utf8-quotient-mutant.lisp > "$utf8_quotient_mutant_bundle"
run_case run_law utf8-quotient-positive "$utf8_quotient_law_bundle" 1
run_case run_law utf8-quotient-mutant "$utf8_quotient_mutant_bundle" 0
# Кореневі числові тотожності UTF-8 перевіряє сам Lisp/SENS, включно з мутантом.
utf8_roots_positive="$evidence/utf8-numeric-foundations-positive-complete.lisp"
utf8_roots_mutant="$evidence/utf8-numeric-foundations-mutant-complete.lisp"
cat -- lib/utf8.lisp tests/semantic/utf8-numeric-foundations-law.lisp > "$utf8_roots_positive"
cat -- lib/utf8.lisp tests/semantic/utf8-numeric-foundations-mutant.lisp > "$utf8_roots_mutant"
run_case run_law utf8-numeric-foundations-positive "$utf8_roots_positive" 1
run_case run_law utf8-numeric-foundations-mutant "$utf8_roots_mutant" 0
# Негативний тип перевіряє сама мова; Rust/Zig не є семантичним оракулом.
run_case run_type_rejection d8-string-symbol-nontext-type-negative tests/semantic/d8-string-symbol-nontext-type-negative.lisp 'string->symbol expects a string'
# Окремий Type-закон: контекстний D1 предикат заборонено записувати як дані.
run_case run_type_rejection d8-contextual-d1-serialize-type-negative tests/semantic/d8-contextual-d1-serialize-type-negative.lisp 'write-to-string cannot serialize contextual predicate results'
# Ділення на обчислений нуль є мовним DivisionByZero, не довільною помилкою reader-а.
run_case run_division_by_zero_rejection d24-computed-zero-denominator tests/semantic/d24-reader-zero-denominator-negative.lisp 'division by zero'
# D24+ арифметика використовує ті самі справжні визначення Core4 на всіх
# трьох маршрутах; позитив і мутант доводять точні D1:1 / D1:0.
run_case run_law exact-arithmetic-positive tests/semantic/exact-arithmetic-laws.lisp 1 core4
run_case run_law exact-arithmetic-mutant tests/semantic/exact-arithmetic-mutant.lisp 0 core4
# D1 хибне значення як голова CONS ≠ порожній D3-список.
# Обидва результати вираховує Lisp/SENS; Zig лише фізично переносить слова.
run_case run_law d3-d1-false-cons-head-positive tests/semantic/language-law-d3-d1-false-head-ukr.lisp 1
run_case run_law d3-d1-false-cons-head-mutant tests/semantic/language-mutant-d3-d1-false-head-ukr.lisp 0
# D1:ні — точний однобітний предикат, D3:() — структурні дані.
# Позитив і негатив виконуються самою мовою SENS після Zig/T5M.
run_case run_law d1-d3-nil-distinction-positive tests/semantic/d1-d3-nil-distinction-law.lisp 1
run_case run_law d1-d3-nil-distinction-mutant tests/semantic/d1-d3-nil-distinction-mutant.lisp 0
# Першокласне значення D3 ATOM: перевіряє сама SENS у прямому та фізичному маршрутах.
run_case run_law d3-first-class-domain-invoke tests/semantic/закон-першокласний-доменний-виклик.lisp 1
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
run_case run_type_rejection d3-car-atomic-dotted-tail-type-negative tests/semantic/d3-car-atomic-dotted-tail-type-negative.lisp 'car expects a non-empty list'
run_case run_type_rejection d3-cdr-empty-list-type-negative tests/semantic/d3-cdr-empty-list-type-negative.lisp 'cdr expects a non-empty list'
run_case run_type_rejection d3-cdr-atom-type-negative tests/semantic/d3-cdr-atom-type-negative.lisp 'cdr expects a non-empty list'
run_case run_type_rejection d3-cond-nil-condition-type-negative tests/semantic/d3-cond-nil-condition-type-negative.lisp 'D3:110 COND expects exact D1:1 / D1:0'
# D4 NOT — часткова функція тільки над D1 PredicateBit, ніколи над структурним NIL.
run_case run_type_rejection d4-not-nonpredicate-type-negative tests/semantic/d4-not-nonpredicate-type-negative.lisp 'NOT requires an exact D1 PredicateBit'
# D5/D24+ потребує D6 LENGTH, яку Core4 визначає мовою SENS.
# Прямий Lisp має цей Core4-профіль. Відтворюємо ТОЙ САМИЙ профіль
# для фізичного Zig/T5M (парного та автономного), без host-арифметики.
# Якщо exact D6:000000 не отримає реального замикання, це чесний RED.
run_case run_law d5-arithmetic-native-t5m-law tests/semantic/d5-arithmetic-native-t5m-law.lisp 1 core4
run_case run_law d5-arithmetic-native-t5m-mutant tests/semantic/d5-arithmetic-native-t5m-mutant.lisp 0 core4
# Залежні закони Д11 SPAN/BREAK: мова задає і функції, і твердження.
# Цей повний Lisp-пакет кодується Zig/T5M і виконується фізичним SENS.
# Відокремлений .lisp-свідок не є автономною програмою — без lib/ він не викличний.
d11_span_bundle="$evidence/d11-srfi1-span-break-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-laws.lisp > "$d11_span_bundle"
sha256sum lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-laws.lisp > "$evidence/d11-srfi1-inputs.sha256"
run_case run_law d11-srfi1-span-break-physical "$d11_span_bundle" 1
# Д11: НЕ втрачати бенчмарк сімейств, навіть коли він не змінювався в commit.
# Композиції й позитив/мутант — виключно справжній Lisp/SENS; Bash тільки
# складає допущені джерела й перевіряє D1/точні фізичні байти.
d11_families_source="$evidence/d11-families-source.lisp"
cat -- lib/d11-family-selection.lisp \
       lib/d11-srfi1-alist-protocol.lisp \
       lib/d11-clojure-group-by.lisp \
       lib/d11-clojure-frequencies-unary.lisp \
       benchmarks/d11-families.lisp > "$d11_families_source"
d11_families_law="$evidence/d11-families-positive.lisp"
d11_families_mutant="$evidence/d11-families-mutant.lisp"
cat -- "$d11_families_source" tests/semantic/d11-families-benchmark-law.lisp > "$d11_families_law"
cat -- "$d11_families_source" tests/semantic/d11-families-benchmark-mutant.lisp > "$d11_families_mutant"
sha256sum lib/d11-family-selection.lisp lib/d11-srfi1-alist-protocol.lisp \
  lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp \
  benchmarks/d11-families.lisp tests/semantic/d11-families-benchmark-law.lisp \
  tests/semantic/d11-families-benchmark-mutant.lisp > "$evidence/d11-families-inputs.sha256"
run_case run_law d11-families-benchmark-positive "$d11_families_law" 1
run_case run_law d11-families-benchmark-mutant "$d11_families_mutant" 0
# Вимірюємо ТІЛЬКИ справжній фізичний SENS, після доведеного D1 закону.
# Це p50 цілого процесу на shared runner, не ізольований час eval.
# Сирі зразки + SHA залишаються в артефакті CI; червоне не маскуємо.
d11_bench_evidence="$evidence/d11-families-benchmark-positive"
if [[ -s "$d11_bench_evidence/program.sens" &&
      -f "$d11_bench_evidence/physical.out" ]] &&
   grep -Fq 'id=d11-families-benchmark-positive source=' "$evidence/results.txt"; then
  d11_bench_samples="$evidence/d11-families-physical-wall-us.tsv"
  source_sha256="$(sha256sum "$d11_families_law" | cut -d' ' -f1)"
  physical_sha256="$(sha256sum "$d11_bench_evidence/program.sens" | cut -d' ' -f1)"
  printf 'sample\telapsed_us\tstdout_sha256\tsource_sha256\tphysical_sha256\n' > "$d11_bench_samples"
  for iteration in {1..11}; do
    start_us="${EPOCHREALTIME/./}"
    if ! timeout 45s "$sens" "$d11_bench_evidence/program.sens" > "$evidence/d11-families-physical-$iteration.out" 2>"$evidence/d11-families-physical-$iteration.err"; then
      cat "$evidence/d11-families-physical-$iteration.err" >&2
      echo "::error title=SENS D11 benchmark::REGRESSION layer=physical-repeatability iteration=$iteration expected=SENS-execution actual=rejected" >&2
      exit 1
    fi
    end_us="${EPOCHREALTIME/./}"
    if ! cmp -s "$d11_bench_evidence/physical.out" "$evidence/d11-families-physical-$iteration.out"; then
      echo "::error title=SENS D11 benchmark::REGRESSION layer=output-parity iteration=$iteration expected=byte-exact-SENS actual=divergent" >&2
      exit 1
    fi
    sample_sha256="$(sha256sum "$evidence/d11-families-physical-$iteration.out" | cut -d' ' -f1)"
    printf '%s\t%s\t%s\t%s\t%s\n' \
      "$iteration" "$((end_us - start_us))" \
      "$sample_sha256" "$source_sha256" "$physical_sha256" >> "$d11_bench_samples"
  done
  mapfile -t sorted_wall < <(tail -n +2 "$d11_bench_samples" | cut -f2 | sort -n)
  if (( ${#sorted_wall[@]} != 11 )); then
    echo "::error title=SENS D11 benchmark::REGRESSION layer=sample-count expected=11 actual=${#sorted_wall[@]}" >&2
    exit 1
  fi
  source_bytes="$(wc -c < "$d11_families_law" | tr -d '[:space:]')"
  physical_bytes="$(wc -c < "$d11_bench_evidence/program.sens" | tr -d '[:space:]')"
  printf 'p50_us\t%s\np90_us\t%s\nmin_us\t%s\nmax_us\t%s\nsamples\t11\nsource_bytes\t%s\nphysical_bytes\t%s\nsource_sha256\t%s\nphysical_sha256\t%s\n' \
    "${sorted_wall[5]}" "${sorted_wall[9]}" "${sorted_wall[0]}" "${sorted_wall[10]}" \
    "$source_bytes" "$physical_bytes" "$source_sha256" "$physical_sha256" > "$evidence/d11-families-benchmark-metrics.tsv"
  echo "::notice title=SENS D11 physical benchmark::MEASURED p50_us=${sorted_wall[5]} p90_us=${sorted_wall[9]} min_us=${sorted_wall[0]} max_us=${sorted_wall[10]} source_bytes=$source_bytes physical_bytes=$physical_bytes samples=11 native=SENS semantic=D1:1 verified=YES source_sha256=$source_sha256 physical_sha256=$physical_sha256 scope=whole-process"
  if (( sorted_wall[5] > 0 && sorted_wall[9] > sorted_wall[5] * 2 )); then
    echo "::warning title=SENS D11 physical benchmark::HIGH_JITTER p50_us=${sorted_wall[5]} p90_us=${sorted_wall[9]} ratio_gt_2=true shared_runner=true" >&2
  fi
else
  echo "::warning title=SENS D11 physical benchmark::NOT_MEASURED reason=law-not-physically-certified release=NOT_CERTIFIED"
fi
# Дев'ять D11 законів шостого елемента належать самому Lisp/SENS.
# Повний MetaEval починає з D6 LENGTH, ще невикличного у фізичному T5M:
# він не є передумовою цієї незалежної композиції п'яти CDR і одного CAR.
# Беремо точне НЕЗМІНЕНЕ визначення з lib/meta-eval.lisp, а не копіюємо
# алгоритм чи семантичний оракул у shell/Rust/Zig. Зсув вихідної форми
# або дубль її DEFINE є жорсткою помилкою, не SKIP.
meta_sixth_definition="$evidence/d11-meta-sixth-source-definition.lisp"
if ! awk '
  /^\(визначити шосте-значення-групи$/ {
    if (found++) exit 2
    copying = 1
  }
  copying && NF == 0 {
    copying = 0
    complete++
    next
  }
  copying { print }
  END { if (found != 1 || complete != 1 || copying) exit 2 }
' lib/meta-eval.lisp > "$meta_sixth_definition"; then
  echo "::error::D11_META_SIXTH_SOURCE_NOT_ISOLATABLE source=lib/meta-eval.lisp" >&2
  exit 2
fi
test -s "$meta_sixth_definition" || { echo "::error::D11_META_SIXTH_SOURCE_EMPTY" >&2; exit 2; }
sha256sum lib/meta-eval.lisp "$meta_sixth_definition" > "$evidence/d11-meta-sixth-source.sha256"
meta_sixth_law_bundle="$evidence/d11-meta-sixth-positive-complete.lisp"
meta_sixth_mutant_bundle="$evidence/d11-meta-sixth-mutant-complete.lisp"
cat -- "$meta_sixth_definition" tests/semantic/d11-meta-sixth-laws.lisp > "$meta_sixth_law_bundle"
cat -- "$meta_sixth_definition" tests/semantic/d11-meta-sixth-mutant.lisp > "$meta_sixth_mutant_bundle"
run_case run_law d11-meta-sixth-positive "$meta_sixth_law_bundle" 1
run_case run_law d11-meta-sixth-mutant "$meta_sixth_mutant_bundle" 0
# Д11: повний закон належить Lisp/SENS. Беремо незмінене за структурою
# визначення з lib/meta-eval.lisp, а не завантажуємо залежний D6 LENGTH.
# Імена операторів порівнюються нормативною D8 однакові?, не частковою D3 EQ.
meta_compare_definition="$evidence/d11-meta-compare-source-definition.lisp"
if ! awk -v target="(визначити порівняти-два-значення-мета" '
  $0 == target {
    if (found++) exit 2
    copying = 1
  }
  copying && NF == 0 {
    copying = 0
    complete++
    next
  }
  copying { print }
  END { if (found != 1 || complete != 1 || copying) exit 2 }
' lib/meta-eval.lisp > "$meta_compare_definition"; then
  echo "::error::D11_META_COMPARE_SOURCE_NOT_ISOLATABLE source=lib/meta-eval.lisp" >&2
  exit 2
fi
test -s "$meta_compare_definition" || { echo "::error::D11_META_COMPARE_SOURCE_EMPTY" >&2; exit 2; }
sha256sum lib/meta-eval.lisp "$meta_compare_definition" > "$evidence/d11-meta-compare-source.sha256"
meta_compare_law_bundle="$evidence/d11-meta-compare-positive-complete.lisp"
meta_compare_mutant_bundle="$evidence/d11-meta-compare-mutant-complete.lisp"
cat -- "$meta_compare_definition" tests/semantic/d11-meta-compare-laws.lisp > "$meta_compare_law_bundle"
cat -- "$meta_compare_definition" tests/semantic/d11-meta-compare-mutant.lisp > "$meta_compare_mutant_bundle"
run_case run_law d11-meta-compare-positive "$meta_compare_law_bundle" 1
run_case run_law d11-meta-compare-mutant "$meta_compare_mutant_bundle" 0
# Незалежні Д1-операнди не потребують D6 LENGTH: точний Lisp-закон
# і негативний мутант виконуються через той самий фізичний Zig/T5M.
meta_compare_d1_law_bundle="$evidence/d11-meta-compare-d1-positive-complete.lisp"
meta_compare_d1_mutant_bundle="$evidence/d11-meta-compare-d1-mutant-complete.lisp"
cat -- "$meta_compare_definition" tests/semantic/d11-meta-compare-d1-law.lisp > "$meta_compare_d1_law_bundle"
cat -- "$meta_compare_definition" tests/semantic/d11-meta-compare-d1-mutant.lisp > "$meta_compare_d1_mutant_bundle"
run_case run_law d11-meta-compare-d1-positive "$meta_compare_d1_law_bundle" 1
run_case run_law d11-meta-compare-d1-mutant "$meta_compare_d1_mutant_bundle" 0
# Interlisp DWIM / Masterscope — 22 мовні закони і два контрприклади.
# Ці DEFINE фізично пакуються Zig/T5M, D1 вирішує лише SENS.
for suite in dwim masterscope; do
  interlisp_positive="$evidence/d11-interlisp-$suite-positive-complete.lisp"
  interlisp_mutant="$evidence/d11-interlisp-$suite-mutant-complete.lisp"
  cat -- lib/d11-interlisp-safe-analysis.lisp "tests/semantic/d11-interlisp-$suite-laws.lisp" > "$interlisp_positive"
  cat -- lib/d11-interlisp-safe-analysis.lisp "tests/semantic/d11-interlisp-$suite-mutant.lisp" > "$interlisp_mutant"
  run_case run_law "d11-interlisp-$suite-positive" "$interlisp_positive" 1
  run_case run_law "d11-interlisp-$suite-mutant" "$interlisp_mutant" 0
done
# LAST-DEFINE: D7-текст має D8-рівність у нормативному Lisp, не D3 EQ Rust.
# Повний MetaEval починається з невикличного D6 LENGTH (#5854). Для цієї
# незалежної функції беремо ТОЧНО її визначення з чинного Lisp-файлу.
# Відсутність, дублювання або злам меж DEFINE — RED, не підміна закону.
last_define_definition="$evidence/d11-meta-last-define-source-definition.lisp"
if ! awk -v target="(визначити останнє-ім'я-визначення-лямбди" '
  $0 == target {
    if (found++) exit 2
    copying = 1
  }
  copying && NF == 0 {
    copying = 0
    complete++
    next
  }
  copying { print }
  END { if (found != 1 || complete != 1 || copying) exit 2 }
' lib/meta-eval.lisp > "$last_define_definition"; then
  echo "::error::D11_META_LAST_DEFINE_SOURCE_NOT_ISOLATABLE source=lib/meta-eval.lisp" >&2
  exit 2
fi
test -s "$last_define_definition" || { echo "::error::D11_META_LAST_DEFINE_SOURCE_EMPTY" >&2; exit 2; }
sha256sum lib/meta-eval.lisp "$last_define_definition" > "$evidence/d11-meta-last-define-source.sha256"
last_define_positive_bundle="$evidence/d11-meta-last-define-positive-complete.lisp"
last_define_mutant_bundle="$evidence/d11-meta-last-define-mutant-complete.lisp"
cat -- "$last_define_definition" tests/semantic/d11-meta-last-define-laws.lisp > "$last_define_positive_bundle"
cat -- "$last_define_definition" tests/semantic/d11-meta-last-define-mutant.lisp > "$last_define_mutant_bundle"
run_case run_law d11-meta-last-define-positive "$last_define_positive_bundle" 1
run_case run_law d11-meta-last-define-mutant "$last_define_mutant_bundle" 0
# Д11 juxt: першокласні одномісні функції та контрприклад перевіряє SENS.
# Bash лише додає чинні DEFINE та проводить обидва свідки через Zig/T5M.
d11_juxt_law_bundle="$evidence/d11-clojure-juxt-positive-complete.lisp"
d11_juxt_mutant_bundle="$evidence/d11-clojure-juxt-mutant-complete.lisp"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-laws.lisp > "$d11_juxt_law_bundle"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-mutant.lisp > "$d11_juxt_mutant_bundle"
sha256sum lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-laws.lisp tests/semantic/d11-clojure-juxt-mutant.lisp > "$evidence/d11-clojure-juxt-inputs.sha256"
run_case run_law d11-clojure-juxt-positive "$d11_juxt_law_bundle" 1
run_case run_law d11-clojure-juxt-mutant "$d11_juxt_mutant_bundle" 0
# Д11 JUХT: атом Д1:ні не є завершенням списку функцій.
# Фізичний і прямий SENS мусять дати Type при D3 ПЕРШЕ, а не
# сховати крапковий хвіст під пустим результатом через АТОМ?.
d11_juxt_improper_bundle="$evidence/d11-clojure-juxt-improper-d1-complete.lisp"
cat -- lib/d11-clojure-juxt.lisp \
  tests/semantic/d11-clojure-juxt-improper-d1-tail-negative.lisp > "$d11_juxt_improper_bundle"
run_case run_type_rejection d11-clojure-juxt-improper-d1-type-negative \
  "$d11_juxt_improper_bundle" 'car expects a non-empty list'

# Д11 Clojure: два комплекти законів перенесено з Rust у справжній Lisp.
# Їхня залежність SRFI-1 SPAN завантажується перед DEFINE групування.
for suite in d11-clojure-partition-by d11-clojure-dedupe; do
  combined="$evidence/$suite-complete.lisp"
  cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp "tests/semantic/$suite-laws.lisp" > "$combined"
  run_case run_law "$suite-physical" "$combined" 1
done
# Д11: атом Д1 не є завершенням правильного списку. Потрібен SENS Type,
# а не фальшивий PASS порожнього результату від ATOM? замість ПОРОЖНІЙ?.
for kind in partition dedupe; do
  invalid="$evidence/d11-clojure-${kind}-improper-d1-tail-complete.lisp"
  cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp \
    "tests/semantic/d11-clojure-${kind}-improper-d1-tail-negative.lisp" > "$invalid"
  # D1-атом не є NIL; спочатку оцінюється CDR у перевірці singleton,
  # тому нормативний Type тут належить D3 CDR, а не D3 CAR.
  run_case run_type_rejection "d11-clojure-${kind}-improper-d1-type-negative" \
    "$invalid" 'cdr expects a non-empty list'
done
# Один quoted D7-гліф має бути точним W7-атомом; вкладений список лишається D2.
# Багатогліфовий Text7 далі є послідовністю, а не таємно interned-атомом.
d11_partition_d7_bundle="$evidence/d11-clojure-partition-by-d7-parity.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-by-d7-parity.lisp > "$d11_partition_d7_bundle"
run_case run_law d11-clojure-partition-by-d7-parity "$d11_partition_d7_bundle" 1

# The result-status law stays in Ukrainian Lisp; only the runner bundles its admitted library.
result_status_bundle="$evidence/result-status-bundle.lisp"
cat lib/result-status.lisp tests/semantic/result-status-laws.lisp > "$result_status_bundle"
run_case run_law result-status-source "$result_status_bundle" 1
# Вузька пара D7-мiток: саме правило зв'язування text7-гліфів з D8
# та негативний чужий тег. Не замінюємо мовний вирок Bash-обчисленням.
result_status_d7_law="$evidence/result-status-d7-label-positive.lisp"
result_status_d7_mutant="$evidence/result-status-d7-label-mutant.lisp"
cat -- lib/result-status.lisp tests/semantic/result-status-d7-label-law.lisp > "$result_status_d7_law"
cat -- lib/result-status.lisp tests/semantic/result-status-d7-label-mutant.lisp > "$result_status_d7_mutant"
sha256sum lib/result-status.lisp tests/semantic/result-status-d7-label-law.lisp \
  tests/semantic/result-status-d7-label-mutant.lisp > "$evidence/result-status-d7-inputs.sha256"
run_case run_law result-status-d7-label-positive "$result_status_d7_law" 1
run_case run_law result-status-d7-label-mutant "$result_status_d7_mutant" 0
# Незалежна Lisp-пара локалізує правильний UNKNOWN проти крапкового D7-хвоста.
# Shell лише завантажує реальні визначення; D1:так/ні визначає сам SENS.
result_status_dotted_law_bundle="$evidence/result-status-dotted-positive.lisp"
result_status_dotted_mutant_bundle="$evidence/result-status-dotted-mutant.lisp"
cat -- lib/result-status.lisp tests/semantic/result-status-dotted-law.lisp > "$result_status_dotted_law_bundle"
cat -- lib/result-status.lisp tests/semantic/result-status-dotted-mutant.lisp > "$result_status_dotted_mutant_bundle"
run_case run_law result-status-dotted-positive "$result_status_dotted_law_bundle" 1
run_case run_law result-status-dotted-mutant "$result_status_dotted_mutant_bundle" 0
result_status_d3_law_bundle="$evidence/result-status-proper-list-d3-positive.lisp"
result_status_d3_mutant_bundle="$evidence/result-status-proper-list-d3-mutant.lisp"
cat -- lib/result-status.lisp tests/semantic/result-status-proper-list-d3-law.lisp > "$result_status_d3_law_bundle"
cat -- lib/result-status.lisp tests/semantic/result-status-proper-list-d3-mutant.lisp > "$result_status_d3_mutant_bundle"
run_case run_law result-status-proper-list-d3-positive "$result_status_d3_law_bundle" 1
run_case run_law result-status-proper-list-d3-mutant "$result_status_d3_mutant_bundle" 0
# Д9: окремий Lisp-доказ D1 для правильних/крапкових міток і цілей NOT.
# Реальний SENS після Zig/T5M перевіряє весь набір, без очікувань у Rust.
result_status_goal_tags_bundle="$evidence/result-status-goal-tags-positive.lisp"
result_status_goal_tags_mutant_bundle="$evidence/result-status-goal-tags-mutant.lisp"
cat -- lib/result-status.lisp tests/semantic/result-status-goal-tags-law.lisp > "$result_status_goal_tags_bundle"
cat -- lib/result-status.lisp tests/semantic/result-status-goal-tags-mutant.lisp > "$result_status_goal_tags_mutant_bundle"
run_case run_law result-status-goal-tags-positive "$result_status_goal_tags_bundle" 1
run_case run_law result-status-goal-tags-mutant "$result_status_goal_tags_mutant_bundle" 0

# Д5-помічники, D9-предикати та D10-конструктори існують у lib/core4.lisp,
# але мінімальний корпус свідка не завантажує весь core4 з макросами.
# Витягаємо ТІЛЬКИ точні чинні Lisp DEFINE без копії реалізації чи host-оракула.
# Відсутнє/дубльоване визначення — помилка, а не замовчуваний SKIP.
epistemic_constructor_source="$evidence/epistemic-canonical-core4-dependencies.lisp"
: > "$epistemic_constructor_source"
for constructor in значення-у-списку? знайти-за-ключем створити-спостереження створити-твердження створити-доказ створити-намір спостереження? твердження? доказ? намір?; do
  if ! awk -v target="(визначити $constructor" '
    $0 == target {
      if (found++) exit 2
      copying = 1
    }
    copying && NF == 0 {
      copying = 0
      complete++
      next
    }
    copying { print }
    END { if (found != 1 || complete != 1 || copying) exit 2 }
  ' lib/core4.lisp >> "$epistemic_constructor_source"; then
    echo "::error::EPISTEMIC_D10_SOURCE_NOT_ISOLATABLE function=$constructor source=lib/core4.lisp" >&2
    exit 2
  fi
  printf '\n' >> "$epistemic_constructor_source"
done
# D10:0001110110 має дві ратифіковані українські поверхні.
# Мінімальний Lisp-корпус зв’язує повну назву з уже визначеною функцією.
# Це зв’язування виконує SENS, без хостового дублювання закону.
printf '(визначити створити-структуроване-твердження створити-твердження)\n' >> "$epistemic_constructor_source"
test -s "$epistemic_constructor_source" || {
  echo "::error::EPISTEMIC_D10_SOURCE_EMPTY" >&2
  exit 2
}
sha256sum lib/core4.lisp "$epistemic_constructor_source" > "$evidence/epistemic-core4-dependencies.sha256"

# Епістемічні закони належать Lisp: посилання, вимоги та вкладена рівність.
# Той самий живий SENS-корпус спрацьовує на позитиві, а хибне очікування
# повертає named fail із самого Lisp. Rust не містить таблиці очікувань.
# Замкнене мінімальне джерело: точні залежності вже взяті з core4 вище.
# Сторонні бібліотеки Reason/Knowledge/Time виконують D6 LENGTH та інші
# незалежні закони; їхні ранні помилки не є вердиктом цього тесту.
# Якщо власна епістемічна функція не працює, фізичний SENS лишається RED.
epistemic_sources=(lib/epistemic.lisp tests/fixtures/witness-runner.lisp
                   tests/fixtures/epistemic-authority-witness.lisp)
epistemic_law_bundle="$evidence/epistemic-record-logic-positive-complete.lisp"
epistemic_mutant_bundle="$evidence/epistemic-record-logic-mutant-complete.lisp"
# Явні D1 імена, потрібні чинним D9 Lisp-предикатам із core4.
# Самостійному корпусу заборонено покладатися на неявні host-зв'язування.
epistemic_d1_source="tests/fixtures/epistemic-d1-names.lisp"
test -f "$epistemic_d1_source" && test ! -L "$epistemic_d1_source" || {
  echo "::error::EPISTEMIC_D1_NAMES_MISSING source=$epistemic_d1_source" >&2
  exit 2
}
cat -- "$epistemic_d1_source" "$epistemic_constructor_source" "${epistemic_sources[@]}" tests/semantic/language-law-epistemic-records.lisp > "$epistemic_law_bundle"
cat -- "$epistemic_d1_source" "$epistemic_constructor_source" "${epistemic_sources[@]}" tests/semantic/language-mutant-epistemic-records.lisp > "$epistemic_mutant_bundle"
sha256sum "$epistemic_d1_source" "$epistemic_constructor_source" "${epistemic_sources[@]}" tests/semantic/language-law-epistemic-records.lisp tests/semantic/language-mutant-epistemic-records.lisp > "$evidence/epistemic-record-logic-inputs.sha256"
run_case run_law epistemic-record-logic-positive "$epistemic_law_bundle" 1 core4
# Назва, статус, фактичний та очікуваний D1 доведені D8 всередині Lisp.
# Перевіряємо рівно один D1:1 від усіх фізичних виконавців без host-проєкції D7.
run_case run_law epistemic-record-logic-mutant "$epistemic_mutant_bundle" 1 core4
# Д7/D8: окремі малі закони про текстові теги без LET чи числових літералів.
# Бібліотека та предикати — Lisp; Zig відповідає лише за фізичний носій.
# Сам модуль Epistemic при завантаженні зв'язує чинне ім'я
# СТВОРИТИ-ТВЕРДЖЕННЯ з канонічним DEFINE Core4. Без цього першого
# зв'язування фізична перевірка може відхилитися ще до закону D7.
# Використовуємо той самий SHA-доведений точний виріз Core4, що й
# повний епістемічний свідок вище; не додаємо Rust/host реалізацію.
# Не завантажуємо сторонній Reason/Knowledge, де поки невиклична D6 LENGTH.
# За будь-якої семантичної чи D7-помилки фізичний SENS все одно повертає RED.
d7_tag_sources=("$epistemic_constructor_source" lib/epistemic.lisp)
d7_tag_positive="$evidence/d7-epistemic-structural-tag-positive.lisp"
d7_tag_mutant="$evidence/d7-epistemic-structural-tag-mutant.lisp"
cat -- "${d7_tag_sources[@]}" tests/semantic/d7-epistemic-structural-tag-law.lisp > "$d7_tag_positive"
cat -- "${d7_tag_sources[@]}" tests/semantic/d7-epistemic-structural-tag-mutant.lisp > "$d7_tag_mutant"
run_case run_law d7-epistemic-structural-tag-positive "$d7_tag_positive" 1
run_case run_law d7-epistemic-structural-tag-mutant "$d7_tag_mutant" 0
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
# Д3: нативний структурний бенчмарк — позитив і мутант через Zig/T5M.
d3_hot_law="$evidence/d3-structural-bench-positive.lisp"
d3_hot_mutant="$evidence/d3-structural-bench-mutant.lisp"
cat -- benchmarks/d3-structural-bench.lisp tests/semantic/d3-structural-bench-law.lisp > "$d3_hot_law"
cat -- benchmarks/d3-structural-bench.lisp tests/semantic/d3-structural-bench-mutant.lisp > "$d3_hot_mutant"
sha256sum benchmarks/d3-structural-bench.lisp tests/semantic/d3-structural-bench-law.lisp tests/semantic/d3-structural-bench-mutant.lisp > "$evidence/d3-structural-bench-inputs.sha256"
run_case run_law d3-structural-bench-positive "$d3_hot_law" 1
run_case run_law d3-structural-bench-mutant "$d3_hot_mutant" 0

# Семантика D6 ALL — виконувані мовні закони з чинним визначенням Core4.
d6_quantifier_source="$evidence/d6-first-class-predicate-quantifiers.lisp"
: > "$d6_quantifier_source"
for quantifier in будь-яке? усі?; do
  if ! awk -v target="(визначити $quantifier" '
    $0 == target {
      if (found++) exit 2
      copying = 1
    }
    copying && NF == 0 {
      copying = 0
      complete++
      next
    }
    copying { print }
    END { if (found != 1 || complete != 1 || copying) exit 2 }
  ' lib/core4-parts/core4-d6b.lisp >> "$d6_quantifier_source"; then
    echo "::error::SENS_D6_QUANTIFIER_SOURCE_NOT_ISOLATABLE function=$quantifier source=lib/core4-parts/core4-d6b.lisp" >&2
    exit 2
  fi
  printf '\n' >> "$d6_quantifier_source"
done
all_quantifier_law_bundle="$evidence/all-predicate-quantifier.lisp"
all_quantifier_mutant_bundle="$evidence/all-predicate-quantifier-mutant.lisp"
any_quantifier_law_bundle="$evidence/any-predicate-quantifier.lisp"
any_quantifier_mutant_bundle="$evidence/any-predicate-quantifier-mutant.lisp"
cat -- tests/fixtures/epistemic-d1-names.lisp "$d6_quantifier_source" tests/semantic/усі-за-предикатом-law.lisp > "$all_quantifier_law_bundle"
cat -- tests/fixtures/epistemic-d1-names.lisp "$d6_quantifier_source" tests/semantic/усі-за-предикатом-mutant.lisp > "$all_quantifier_mutant_bundle"
cat -- tests/fixtures/epistemic-d1-names.lisp "$d6_quantifier_source" tests/semantic/існує-за-предикатом-law.lisp > "$any_quantifier_law_bundle"
cat -- tests/fixtures/epistemic-d1-names.lisp "$d6_quantifier_source" tests/semantic/існує-за-предикатом-mutant.lisp > "$any_quantifier_mutant_bundle"
sha256sum lib/core4-parts/core4-d6b.lisp tests/fixtures/epistemic-d1-names.lisp tests/semantic/усі-за-предикатом-law.lisp tests/semantic/усі-за-предикатом-mutant.lisp tests/semantic/існує-за-предикатом-law.lisp tests/semantic/існує-за-предикатом-mutant.lisp > "$evidence/d6-quantifier-inputs.sha256"
run_case run_law all-predicate-quantifier-law "$all_quantifier_law_bundle" 1
run_case run_law all-predicate-quantifier-mutant "$all_quantifier_mutant_bundle" 0
run_case run_law exists-predicate-quantifier-law "$any_quantifier_law_bundle" 1
run_case run_law exists-predicate-quantifier-mutant "$any_quantifier_mutant_bundle" 0

# Класифікуємо кореневі причини без повторного запуску SENS.
printf 'SENS_RED_CAUSE root=d7-value-call count=%d ids=%s\n' "${#red_d7_ids[@]}" "${red_d7_ids[*]}"
printf 'SENS_RED_CAUSE root=d3-car-type count=%d ids=%s\n' "${#red_d3_car_ids[@]}" "${red_d3_car_ids[*]}"
printf 'SENS_RED_CAUSE root=d3-cdr-type count=%d ids=%s\n' "${#red_d3_cdr_ids[@]}" "${red_d3_cdr_ids[*]}"
printf 'SENS_RED_CAUSE root=other-or-direct count=%d ids=%s\n' "${#red_other_ids[@]}" "${red_other_ids[*]}"
if (( ${#red_d7_ids[@]} + ${#red_d3_car_ids[@]} + ${#red_d3_cdr_ids[@]} + ${#red_other_ids[@]} != failed )); then
  echo "::error title=SENS RED grouping::REGRESSION expected=all-failures-classified actual=count-mismatch" >&2
  exit 1
fi
# Звіт із фактично завершених програм: дорогі та червоні свідки поруч.
# Семантику визначав Lisp/SENS; shell тільки заміряє тривалість і сортує.
echo "SENS_LAW_BENCHMARK_SUMMARY measured=$checked failed=$failed file=$evidence/law-timings.tsv"
# Профілювання фаз за реальними CSV/TSV-вимірами, без повторного запуску SENS.
# Навіть за RED звіт має показувати, де саме був найдорожчий етап.
stage_report="$evidence/law-stage-benchmark-report.md"
bash scripts/report-sens-law-stage-benchmarks.sh "$evidence/law-stage-timings.tsv" > "$stage_report"
echo "SENS_LAW_STAGE_BENCHMARK_REPORT source=$evidence/law-stage-timings.tsv file=$stage_report"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  cat "$stage_report" >> "$GITHUB_STEP_SUMMARY"
fi
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo '## Час фізичних Lisp-законів — direct + T5M + paired + standalone'
    echo
    echo "Завершено свідків: **$checked**, червоних: **$failed**. Це одноразовий wall-time кожного повного коридору, не p50."
    echo
    echo '| Свідок | Статус | wall-time, мс |'
    echo '|---|---|---:|'
    tail -n +2 "$evidence/law-timings.tsv" |
      sort -t "$(printf '\t')" -k3,3nr |
      sed -n '1,8p' |
      while IFS="$(printf '\t')" read -r id status ms; do
        printf '| `%s` | %s | %s |\n' "$id" "$status" "$ms"
      done
    echo
  } >> "$GITHUB_STEP_SUMMARY"
fi

if (( failed > 0 )); then
  echo "::error title=SENS Lisp/T5M::REGRESSION checked=$checked passed=$passed failed=$failed ids=${failed_ids[*]}" >&2
  exit 1
fi
echo "SENS_LISP_T5M_LAWS_PASS count=$checked passed=$passed failed=$failed physical=ZIG_T5M"
