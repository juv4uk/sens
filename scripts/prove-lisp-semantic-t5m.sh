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
  local -a paired_args=() physical_command=() direct_command=()
  dir="$evidence/$id"
  physical="$dir/program.sens"
  mkdir -p "$dir"
  case "$profile" in
    clean)
      direct_command=("$sens" "$source")
      physical_command=("$sens" "$physical") ;;
    core4)
      direct_command=("$sens" "$source")
      paired_args=(--core4-runtime)
      physical_command=("$trit" eval-core4 "$physical") ;;
    core3)
      # Холодний SENS: жодного Core4 DEFINE у цій сесії.
      direct_command=("$sens" --core=3 "$source")
      physical_command=("$sens" --core=3 "$physical") ;;
    *) fail "$id" harness "profile=clean-or-core3-or-core4" "$profile" ;;
  esac
  test -f "$source" && test ! -L "$source" ||
    fail "$id" source "regular-Lisp" "missing-or-symlink"

  if profile_stage "$id" direct timeout 45s "${direct_command[@]}" >"$dir/direct.out" 2>"$dir/direct.err"; then
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
# Д4: вихідні селектори CAAR/CDAR/CADR є законами чинної драбини.
# Точні D1 значення й неправильний D1-хвіст доводить SENS, не host.
run_case run_law d4-selector-foundation-positive tests/semantic/d4-nested-pair-selectors-law.lisp 1
run_case run_law d4-selector-foundation-mutant tests/semantic/d4-nested-pair-selectors-mutant.lisp 0
run_case run_law d4-second-selector-positive tests/semantic/d4-second-selector-law.lisp 1
run_case run_law d4-second-selector-mutant tests/semantic/d4-second-selector-mutant.lisp 0
run_case run_type_rejection d4-second-improper-d1-tail tests/semantic/d4-second-improper-d1-tail-negative.lisp 'car expects a non-empty list'
sha256sum tests/semantic/d4-nested-pair-selectors-law.lisp \
  tests/semantic/d4-nested-pair-selectors-mutant.lisp \
  tests/semantic/d4-second-selector-law.lisp \
  tests/semantic/d4-second-selector-mutant.lisp \
  tests/semantic/d4-second-improper-d1-tail-negative.lisp > "$evidence/d4-selector-foundation-inputs.sha256"
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
# Д10:0011000010 — конкретне визначення SENS: черга-порожня?.
# Ратифікація 1024/1024 не підміняє фізичного позитиву й мутанта.
# Д9:110011110 — SENS D1 позитив та мутант, без host-string-оракула.
run_case run_law d9-string-append-physical-positive tests/semantic/d9-string-append-physical.lisp 1 core4
run_case run_law d9-string-append-physical-mutant tests/semantic/d9-string-append-physical-mutant.lisp 0 core4
sha256sum tests/semantic/d9-string-append-physical.lisp \
  tests/semantic/d9-string-append-physical-mutant.lisp > "$evidence/d9-string-append-inputs.sha256"
# D9/F6: канонізація лише десяти фіксованих ключів протоколу.
# SENS сам перевіряє D7/D8-еквівалентність, дублі, відсутнє/порожнє поле та malformed tail.
# Shell тільки з'єднує джерельні DEFINE і свідки; оцінює SENS через фізичний Zig/T5M.
d9_fs_keys_positive="$evidence/d9-f6-package-key-canonicalization-positive-complete.lisp"
d9_fs_keys_mutant="$evidence/d9-f6-package-key-canonicalization-mutant-complete.lisp"
# WRITE→READ повного кореня/об'єкта викликає реальні SENS-визначення
# immutable map → world content-address → content store → filesystem.
# Без цих бібліотек позитив хибно падає на unknown Text7 binding
# «внутрішня-мапа-список» ще до перевірки D9/F6 закону.
# Обидва свідки мають однаковий стек джерел; жодних host-оракулів.
cat -- lib/persistent-map.lisp lib/world.lisp lib/content-store.lisp \
  lib/lisp-fs.lisp tests/semantic/d9-f6-package-key-canonicalization-law.lisp > "$d9_fs_keys_positive"
cat -- lib/persistent-map.lisp lib/world.lisp lib/content-store.lisp \
  lib/lisp-fs.lisp tests/semantic/d9-f6-package-key-canonicalization-mutant.lisp > "$d9_fs_keys_mutant"
run_case run_law d9-f6-package-key-canonicalization-positive "$d9_fs_keys_positive" 1 core4
run_case run_law d9-f6-package-key-canonicalization-mutant "$d9_fs_keys_mutant" 0 core4
sha256sum lib/persistent-map.lisp lib/world.lisp lib/content-store.lisp lib/lisp-fs.lisp \
  tests/semantic/d9-f6-package-key-canonicalization-law.lisp \
  tests/semantic/d9-f6-package-key-canonicalization-mutant.lisp \
  > "$evidence/d9-f6-package-key-canonicalization-inputs.sha256"

# D9 MAP: перевірка хвоста ПІСЛЯ збігу; один позитив і два фізичні Type.
d9_map_tail_positive="$evidence/d9-map-hidden-tail-positive-complete.lisp"
d9_map_tail_get_negative="$evidence/d9-map-hidden-tail-get-negative-complete.lisp"
d9_map_tail_insert_negative="$evidence/d9-map-hidden-tail-insert-negative-complete.lisp"
cat -- lib/persistent-map.lisp tests/semantic/d9-map-hidden-tail-positive.lisp > "$d9_map_tail_positive"
cat -- lib/persistent-map.lisp tests/semantic/d9-map-hidden-tail-get-negative.lisp > "$d9_map_tail_get_negative"
cat -- lib/persistent-map.lisp tests/semantic/d9-map-hidden-tail-insert-negative.lisp > "$d9_map_tail_insert_negative"
run_case run_law d9-map-hidden-tail-positive "$d9_map_tail_positive" 1 core4
run_case run_error_rejection d9-map-hidden-tail-get "$d9_map_tail_get_negative" Type 'car expects a non-empty list' core4
run_case run_error_rejection d9-map-hidden-tail-insert "$d9_map_tail_insert_negative" Type 'car expects a non-empty list' core4
sha256sum lib/persistent-map.lisp tests/semantic/d9-map-hidden-tail-positive.lisp \
  tests/semantic/d9-map-hidden-tail-get-negative.lisp \
  tests/semantic/d9-map-hidden-tail-insert-negative.lisp > "$evidence/d9-map-hidden-tail-inputs.sha256"

# Д9/F6: перевірка структури кожного зв'язування без host-семантики.
d9_fs_bindings_positive="$evidence/d9-f6-bindings-shape-positive.lisp"
d9_fs_bindings_mutant="$evidence/d9-f6-bindings-shape-mutant.lisp"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-bindings-shape-law.lisp > "$d9_fs_bindings_positive"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-bindings-shape-mutant.lisp > "$d9_fs_bindings_mutant"
run_case run_law d9-f6-bindings-shape-positive "$d9_fs_bindings_positive" 1 core4
run_case run_law d9-f6-bindings-shape-mutant "$d9_fs_bindings_mutant" 0 core4
sha256sum lib/lisp-fs.lisp tests/semantic/d9-f6-bindings-shape-law.lisp \
  tests/semantic/d9-f6-bindings-shape-mutant.lisp > "$evidence/d9-f6-bindings-shape-inputs.sha256"

# Д9/F6: об'єктні адреси — тільки правильний D3-список.
# Один SENS DEFINE; прямий, парний і standalone Zig/T5M результати.
d9_fs_address_positive="$evidence/d9-f6-object-addresses-positive.lisp"
d9_fs_address_mutant="$evidence/d9-f6-object-addresses-mutant.lisp"
d9_fs_address_root_negative="$evidence/d9-f6-object-addresses-root-negative.lisp"
d9_fs_address_tail_negative="$evidence/d9-f6-object-addresses-tail-negative.lisp"
d9_fs_address_empty_negative="$evidence/d9-f6-object-addresses-empty-address-negative.lisp"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-object-addresses-law.lisp > "$d9_fs_address_positive"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-object-addresses-mutant.lisp > "$d9_fs_address_mutant"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-object-addresses-d1-root-negative.lisp > "$d9_fs_address_root_negative"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-object-addresses-d1-tail-negative.lisp > "$d9_fs_address_tail_negative"
cat -- lib/lisp-fs.lisp tests/semantic/d9-f6-object-addresses-empty-address-negative.lisp > "$d9_fs_address_empty_negative"
run_case run_law d9-f6-object-addresses-positive "$d9_fs_address_positive" 1 core4
run_case run_law d9-f6-object-addresses-mutant "$d9_fs_address_mutant" 0 core4
run_case run_error_rejection d9-f6-object-addresses-d1-root "$d9_fs_address_root_negative" Type 'car expects a non-empty list' core4
run_case run_error_rejection d9-f6-object-addresses-d1-tail "$d9_fs_address_tail_negative" Type 'car expects a non-empty list' core4
run_case run_error_rejection d9-f6-object-addresses-empty-address "$d9_fs_address_empty_negative" Type 'car expects a non-empty list' core4
sha256sum lib/lisp-fs.lisp tests/semantic/d9-f6-object-addresses-law.lisp \
  tests/semantic/d9-f6-object-addresses-mutant.lisp \
  tests/semantic/d9-f6-object-addresses-d1-root-negative.lisp \
  tests/semantic/d9-f6-object-addresses-d1-tail-negative.lisp \
  tests/semantic/d9-f6-object-addresses-empty-address-negative.lisp > "$evidence/d9-f6-object-addresses-inputs.sha256"

# Д11 PREFIX: похідний SENS D1/D3/D8 закон, а не нова координата.
# Кожний шлях має точну source → native SENS → Zig/T5M → SENS реєстрацію.
d11_prefix_positive="$evidence/d11-prefix-proper-positive.lisp"
d11_prefix_mutant="$evidence/d11-prefix-proper-mutant.lisp"
d11_prefix_left_tail="$evidence/d11-prefix-proper-left-tail-negative.lisp"
d11_prefix_right_hidden="$evidence/d11-prefix-proper-right-hidden-tail-negative.lisp"
d11_prefix_left_root="$evidence/d11-prefix-proper-left-root-negative.lisp"
cat -- lib/d11-prefix-proper.lisp tests/semantic/d11-prefix-proper-law.lisp > "$d11_prefix_positive"
cat -- lib/d11-prefix-proper.lisp tests/semantic/d11-prefix-proper-mutant.lisp > "$d11_prefix_mutant"
cat -- lib/d11-prefix-proper.lisp tests/semantic/d11-prefix-proper-left-tail-negative.lisp > "$d11_prefix_left_tail"
cat -- lib/d11-prefix-proper.lisp tests/semantic/d11-prefix-proper-right-hidden-tail-negative.lisp > "$d11_prefix_right_hidden"
cat -- lib/d11-prefix-proper.lisp tests/semantic/d11-prefix-proper-left-root-negative.lisp > "$d11_prefix_left_root"
run_case run_law d11-prefix-proper-positive "$d11_prefix_positive" 1 core4
run_case run_law d11-prefix-proper-mutant "$d11_prefix_mutant" 0 core4
run_case run_error_rejection d11-prefix-proper-left-tail "$d11_prefix_left_tail" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-prefix-proper-right-hidden "$d11_prefix_right_hidden" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-prefix-proper-left-root "$d11_prefix_left_root" Type 'car expects a non-empty list' core4
sha256sum lib/d11-prefix-proper.lisp \
  tests/semantic/d11-prefix-proper-law.lisp \
  tests/semantic/d11-prefix-proper-mutant.lisp \
  tests/semantic/d11-prefix-proper-left-tail-negative.lisp \
  tests/semantic/d11-prefix-proper-right-hidden-tail-negative.lisp \
  tests/semantic/d11-prefix-proper-left-root-negative.lisp \
  > "$evidence/d11-prefix-proper-inputs.sha256"

# Д10: чотири ратифіковані MAP-виклики, усі 12 SENS-предикатів — один D1 доказ.
# Негативний свідок повинен давати саме D1:ні, не Type і не host результат.
run_case run_law d10-map-derived-twelve-positive tests/semantic/d10-map-derived-native-laws.lisp 1 core4
run_case run_law d10-map-derived-empty-mutant tests/semantic/d10-map-derived-native-mutant.lisp 0 core4
sha256sum tests/semantic/d10-map-derived-native-laws.lisp \
  tests/semantic/d10-map-derived-native-mutant.lisp > "$evidence/d10-map-derived-inputs.sha256"
run_case run_law d10-empty-queue-positive tests/semantic/d10-empty-queue-law.lisp 1 core4
run_case run_law d10-empty-queue-mutant tests/semantic/d10-empty-queue-mutant.lisp 0 core4
# Д10:0100100110/0100100111 — CLIPS ASSERT/PRINTOUT як точні структурні дані.
# D8 однакові? не спричиняє D3 EQ Type для зовнішньої цитованої голови.
# Обидві форми доводить саме SENS; Zig/T5M лише переносить точні байти.
# Дві мінімальні незалежні D10:0100100110/0100100111 head-квитанції.
run_case run_law d10-clips-assert-head-direct-positive tests/semantic/d10-clips-assert-head-direct-law.lisp 1 core4
run_case run_law d10-clips-printout-head-direct-positive tests/semantic/d10-clips-printout-head-direct-law.lisp 1 core4
run_case run_law d10-clips-equal-head-positive tests/semantic/d10-clips-equal-head-law.lisp 1 core4
run_case run_law d10-clips-equal-head-mutant tests/semantic/d10-clips-equal-head-mutant.lisp 0 core4
run_case run_error_rejection d10-clips-all-asserts-improper-tail tests/semantic/d10-clips-all-asserts-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d10-clips-drop-printouts-improper-tail tests/semantic/d10-clips-drop-printouts-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4.lisp \
  tests/semantic/d10-clips-equal-head-law.lisp \
  tests/semantic/d10-clips-assert-head-direct-law.lisp \
  tests/semantic/d10-clips-printout-head-direct-law.lisp \
  tests/semantic/d10-clips-equal-head-mutant.lisp \
  tests/semantic/d10-clips-all-asserts-improper-tail-negative.lisp \
  tests/semantic/d10-clips-drop-printouts-improper-tail-negative.lisp > "$evidence/d10-clips-equal-head-inputs.sha256"
# Перевірка кореня D5: D3 CDR не повинен перетворювати D1:ні на D3:().
# SENS дає позитив D1:так і негатив D1:ні, Zig переносить лише фізичний код.
run_case run_law d3-d4-no-tail-boundary-positive tests/semantic/d3-d4-no-tail-boundary-law.lisp 1
run_case run_law d3-d4-no-tail-boundary-mutant tests/semantic/d3-d4-no-tail-boundary-mutant.lisp 0
sha256sum tests/semantic/d3-d4-no-tail-boundary-law.lisp \
  tests/semantic/d3-d4-no-tail-boundary-mutant.lisp > "$evidence/d3-d4-no-tail-boundary.sha256"

# Д5 REVERSE/REVERSE-ONTO: SENS-закон, порядок і дві точні Type-відмови.
run_case run_law d5-reverse-onto-proper-positive tests/semantic/d5-reverse-onto-proper-law.lisp 1 core4
run_case run_law d5-reverse-onto-order-mutant tests/semantic/d5-reverse-onto-order-mutant.lisp 0 core4
run_case run_error_rejection d5-reverse-onto-improper-tail tests/semantic/d5-reverse-onto-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d5-reverse-improper-tail tests/semantic/d5-reverse-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4.lisp \
  tests/semantic/d5-reverse-onto-proper-law.lisp \
  tests/semantic/d5-reverse-onto-order-mutant.lisp \
  tests/semantic/d5-reverse-onto-improper-tail-negative.lisp \
  tests/semantic/d5-reverse-improper-tail-negative.lisp > "$evidence/d5-reverse-inputs.sha256"
# Д5:11110 PAIRLIS: повні D3-списки, D1-позитив/мутант і три Type-негативи.
run_case run_law d5-pairlis-total-list-positive tests/semantic/d5-pairlis-total-list-law.lisp 1 core4
run_case run_law d5-pairlis-total-list-mutant tests/semantic/d5-pairlis-total-list-mutant.lisp 0 core4
run_case run_error_rejection d5-pairlis-improper-key-tail tests/semantic/d5-pairlis-improper-key-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d5-pairlis-improper-value-tail tests/semantic/d5-pairlis-improper-value-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d5-pairlis-extra-value tests/semantic/d5-pairlis-extra-value-negative.lisp Type 'car expects a non-empty list' core4
sha256sum \
  tests/semantic/d5-pairlis-total-list-law.lisp \
  tests/semantic/d5-pairlis-total-list-mutant.lisp \
  tests/semantic/d5-pairlis-improper-key-tail-negative.lisp \
  tests/semantic/d5-pairlis-improper-value-tail-negative.lisp \
  tests/semantic/d5-pairlis-extra-value-negative.lisp > "$evidence/d5-pairlis-inputs.sha256"

# D5/D24+: точні числові величини, мутант, неправильний D1-хвіст.
# Усі вердикти формулює SENS. Shell тільки з'єднує бібліотеку та свідки.
d5_exact_number_source=lib/залишити-точні-числа.lisp
d5_exact_number_law_bundle="$evidence/d5-exact-numbers-filter-law-complete.lisp"
d5_exact_number_mutant_bundle="$evidence/d5-exact-numbers-filter-mutant-complete.lisp"
d5_exact_number_negative_bundle="$evidence/d5-exact-numbers-filter-improper-tail-negative-complete.lisp"
cat -- "$d5_exact_number_source" tests/semantic/d5-exact-numbers-filter-law.lisp > "$d5_exact_number_law_bundle"
cat -- "$d5_exact_number_source" tests/semantic/d5-exact-numbers-filter-mutant.lisp > "$d5_exact_number_mutant_bundle"
cat -- "$d5_exact_number_source" tests/semantic/d5-exact-numbers-filter-improper-tail-negative.lisp > "$d5_exact_number_negative_bundle"
run_case run_law d5-exact-numbers-filter-positive "$d5_exact_number_law_bundle" 1 core4
run_case run_law d5-exact-numbers-filter-mutant "$d5_exact_number_mutant_bundle" 0 core4
run_case run_error_rejection d5-exact-numbers-filter-improper-tail "$d5_exact_number_negative_bundle" Type 'car expects a non-empty list' core4
sha256sum "$d5_exact_number_source" \
  tests/semantic/d5-exact-numbers-filter-law.lisp \
  tests/semantic/d5-exact-numbers-filter-mutant.lisp \
  tests/semantic/d5-exact-numbers-filter-improper-tail-negative.lisp > "$evidence/d5-exact-numbers-inputs.sha256"
# Д6:000010/000011 MIN-LIST/MAX-LIST, санскритські śreṇī-alpatara/śreṇī-brhattara.
# Залежності D3 CAR/CDR/CONS, D4 NULL, D5 LESSP/GREATERP, D12+ values.
# D3 структура перевіряється ДО числових порівнянь. Справжній SENS
# свідчить чотири відмови, а не host-оракул.
run_case run_law d6-min-max-preflight-positive tests/semantic/d6-min-max-list-d3-preflight-law.lisp 1 core4
run_case run_law d6-min-max-preflight-mutant tests/semantic/d6-min-max-list-d3-preflight-mutant.lisp 0 core4
run_case run_error_rejection d6-min-list-root-d1-type tests/semantic/d6-min-list-d1-root-type-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-min-list-late-poison-type tests/semantic/d6-min-list-poison-late-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-max-list-late-tail-type tests/semantic/d6-max-list-d1-tail-type-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-max-list-single-nonnumeric-type tests/semantic/d6-max-list-single-nonnumeric-type-negative.lisp Type 'math requires explicit D12+ operands' core4
run_case run_error_rejection d6-min-list-interior-nonnumeric-type tests/semantic/d6-min-list-interior-nonnumeric-type-negative.lisp Type 'math requires explicit D12+ operands' core4
run_case run_error_rejection d6-max-list-interior-nonnumeric-type tests/semantic/d6-max-list-interior-nonnumeric-type-negative.lisp Type 'math requires explicit D12+ operands' core4
sha256sum \
  tests/semantic/d6-min-max-list-d3-preflight-law.lisp \
  tests/semantic/d6-min-max-list-d3-preflight-mutant.lisp \
  tests/semantic/d6-min-list-d1-root-type-negative.lisp \
  tests/semantic/d6-min-list-poison-late-tail-negative.lisp \
  tests/semantic/d6-max-list-d1-tail-type-negative.lisp \
  tests/semantic/d6-max-list-single-nonnumeric-type-negative.lisp \
  tests/semantic/d6-min-list-interior-nonnumeric-type-negative.lisp \
  tests/semantic/d6-max-list-interior-nonnumeric-type-negative.lisp > "$evidence/d6-min-max-preflight-inputs.sha256"
# D6 NTH/MAPLIST: числовий індекс та D3 preflight до callback.
run_case run_law d6-nth-exact-index-positive tests/semantic/d6-nth-exact-index-d3-laws.lisp 1 core4
run_case run_law d6-nth-exact-index-mutant tests/semantic/d6-nth-exact-index-d3-mutant.lisp 0 core4
run_case run_error_rejection d6-nth-early-improper-tail tests/semantic/d6-nth-early-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_law d6-nth-choice-mutant tests/semantic/d6-nth-wrong-choice-mutant.lisp 0 core4
run_case run_error_rejection d6-nth-negative-index tests/semantic/d6-nth-negative-index-type-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-nth-d1-root tests/semantic/d6-nth-d1-root-type-negative.lisp Type 'car expects a non-empty list' core4
run_case run_law d6-maplist-preflight-positive tests/semantic/d6-maplist-preflight-laws.lisp 1 core4
run_case run_law d6-maplist-preflight-mutant tests/semantic/d6-maplist-preflight-mutant.lisp 0 core4
run_case run_law d6-maplist-suffix-identity tests/semantic/d6-maplist-suffix-identity-law.lisp 1 core4
run_case run_law d6-maplist-order-mutant tests/semantic/d6-maplist-suffix-order-mutant.lisp 0 core4
run_case run_error_rejection d6-maplist-poison-d1-tail tests/semantic/d6-maplist-poison-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-maplist-d1-root tests/semantic/d6-maplist-d1-root-type-negative.lisp Type 'car expects a non-empty list' core4
sha256sum \
 tests/semantic/d6-nth-exact-index-d3-laws.lisp \
 tests/semantic/d6-nth-exact-index-d3-mutant.lisp \
 tests/semantic/d6-nth-early-improper-tail-negative.lisp \
 tests/semantic/d6-maplist-preflight-laws.lisp \
 tests/semantic/d6-maplist-preflight-mutant.lisp \
 tests/semantic/d6-maplist-poison-improper-tail-negative.lisp \
 tests/semantic/d6-nth-negative-index-type-negative.lisp \
 tests/semantic/d6-nth-d1-root-type-negative.lisp \
 tests/semantic/d6-maplist-suffix-identity-law.lisp \
 tests/semantic/d6-maplist-suffix-order-mutant.lisp \
 tests/semantic/d6-maplist-d1-root-type-negative.lisp \
 tests/semantic/d6-nth-wrong-choice-mutant.lisp > "$evidence/d6-nth-maplist-inputs.sha256"
# D6 LET/LET*: D3 хребет і рівно два поля перед розгортанням.
run_case run_law d6-let-letstar-preflight-positive tests/semantic/d6-let-letstar-preflight-law.lisp 1 core4
run_case run_error_rejection d6-let-boolean-name tests/semantic/d6-let-boolean-name-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-letstar-false-name tests/semantic/d6-letstar-false-name-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-let-numeric-name tests/semantic/d6-let-numeric-name-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-let-three-fields tests/semantic/d6-let-malformed-three-fields-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-letstar-three-fields tests/semantic/d6-letstar-malformed-three-fields-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-let-d1-tail tests/semantic/d6-let-improper-spine-negative.lisp Type 'car expects a non-empty list' core4
sha256sum \
 tests/semantic/d6-let-letstar-preflight-law.lisp \
 tests/semantic/d6-let-boolean-name-negative.lisp \
 tests/semantic/d6-letstar-false-name-negative.lisp \
 tests/semantic/d6-let-numeric-name-negative.lisp \
 tests/semantic/d6-let-malformed-three-fields-negative.lisp \
 tests/semantic/d6-letstar-malformed-three-fields-negative.lisp \
 tests/semantic/d6-let-improper-spine-negative.lisp > "$evidence/d6-let-letstar-preflight-inputs.sha256"
# D6 COMPOSE/FLIP/CURRY are derived SENS functions, so their law and
# counterexample must pass the same physical Zig/T5M -> SENS route.
run_case run_law d6-compose-flip-positive tests/semantic/d6-compose-flip-law.lisp 1 core4
run_case run_law d6-compose-flip-order-mutant tests/semantic/d6-compose-flip-mutant.lisp 0 core4
# D6 FILTER: безпосередня SENS-рекурсія з D3/D4; закон і мутант.
# Д6:000000/000001 LENGTH та LENGTH-ONTO. Перевірка D3:() проти D1:ні.
# Фізичний D6 LENGTH наразі може залишатися TRANSITIONAL #5854.
# Усі нові позитиви/негативи зберігають RED, якщо допуску ще немає.
run_case run_law d6-length-onto-boundary-positive tests/semantic/d6-length-onto-d3-boundary-law.lisp 1 core4
run_case run_law d6-length-onto-boundary-mutant tests/semantic/d6-length-onto-d3-boundary-mutant.lisp 0 core4
run_case run_error_rejection d6-length-onto-d1-root-type tests/semantic/d6-length-onto-d1-root-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-length-onto-late-d1-tail-type tests/semantic/d6-length-onto-late-d1-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_law d6-filter-independent-positive tests/semantic/d6-filter-independent-law.lisp 1 core4
run_case run_law d6-filter-independent-mutant tests/semantic/d6-filter-independent-mutant.lisp 0 core4
# Д6:101000 MAP · повний SENS D3-preflight до виклику callback.
# Правильні D1-елементи зберігаються, перестановка відхиляється,
# а неправильний D1 CDR дає Type ще до спроби викликати D1:ні.
run_case run_law d6-map-preflight-positive tests/semantic/d6-map-preflight-positive.lisp 1 core4
run_case run_law d6-map-preflight-mutant tests/semantic/d6-map-preflight-mutant.lisp 0 core4
run_case run_error_rejection d6-map-preflight-before-callback tests/semantic/d6-map-preflight-before-callback-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-map-preflight-root-negative tests/semantic/d6-map-preflight-root-negative.lisp Type 'car expects a non-empty list' core4
# Д6:101010 MAP-ONTO · закон, мутант, неправильний D3-хвіст.
run_case run_law d6-map-onto-accumulator-positive tests/semantic/d6-map-onto-accumulator-law.lisp 1 core4
run_case run_law d6-map-onto-order-mutant tests/semantic/d6-map-onto-order-mutant.lisp 0 core4
run_case run_error_rejection d6-map-onto-improper-tail tests/semantic/d6-map-onto-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
# Д6:101110 REDUCE · порядок, порожня база й Type для неправильного хвоста.
run_case run_law d6-reduce-left-positive tests/semantic/d6-reduce-left-law.lisp 1 core4
run_case run_law d6-reduce-left-mutant tests/semantic/d6-reduce-left-mutant.lisp 0 core4
run_case run_error_rejection d6-reduce-improper-tail tests/semantic/d6-reduce-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
# Д6 SCAN: обчислити саме чинні DEFINE SENS, а не викликати Text7 без зв'язування.
# Витяг із єдиного чинного Core4-блоку; Type-негатив не можна зарахувати
# за невідоме ім'я, лише за нативне D3 CAR Type після фізичного виконання.
d6_scan_source="$evidence/d6-scan-tail-definitions.lisp"
if ! awk '
  $0 == "(визначити накопичувати-зворотні-стани" { found++; active = 1 }
  $0 == "(визначити накопичувати-до" { found++; active = 1 }
  $0 == "(визначити накопичувати" { if (found == 2) { stop = 1; exit }; bad = 1; exit }
  active { print }
  END { if (found != 2 || !stop || bad) exit 2 }
' lib/core4-parts/core4-d6b.lisp > "$d6_scan_source"; then
  echo "::error::D6_SCAN_SOURCE_NOT_ISOLATABLE" >&2
  exit 2
fi
d6_scan_law="$evidence/d6-scan-tail-law-complete.lisp"
d6_scan_mutant="$evidence/d6-scan-tail-mutant-complete.lisp"
d6_scan_improper="$evidence/d6-scan-tail-improper-complete.lisp"
cat -- "$d6_scan_source" tests/semantic/d6-scan-tail-state-law.lisp > "$d6_scan_law"
cat -- "$d6_scan_source" tests/semantic/d6-scan-tail-state-mutant.lisp > "$d6_scan_mutant"
cat -- "$d6_scan_source" tests/semantic/d6-scan-tail-improper-negative.lisp > "$d6_scan_improper"
run_case run_law d6-scan-tail-state-positive "$d6_scan_law" 1 core4
run_case run_law d6-scan-tail-state-mutant "$d6_scan_mutant" 0 core4
run_case run_error_rejection d6-scan-tail-improper "$d6_scan_improper" Type 'car expects a non-empty list' core4
sha256sum lib/core4-parts/core4-d6b.lisp \
  tests/semantic/d6-scan-tail-state-law.lisp \
  tests/semantic/d6-scan-tail-state-mutant.lisp \
  tests/semantic/d6-scan-tail-improper-negative.lisp \
  > "$evidence/d6-scan-tail-inputs.sha256"
# Д6:101111 SCAN: послідовність станів, зв'язок із REDUCE та структурні відмови.
run_case run_law d6-scan-reduce-terminal-positive tests/semantic/d6-scan-reduce-terminal-law.lisp 1 core4
run_case run_law d6-scan-missing-initial-mutant tests/semantic/d6-scan-missing-initial-mutant.lisp 0 core4
run_case run_error_rejection d6-scan-improper-tail tests/semantic/d6-scan-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-scan-onto-atom tests/semantic/d6-scan-onto-atom-negative.lisp Type 'car expects a non-empty list' core4
# Д8:10111001/10111011 — правий напрямок, закон SCAN та два Type-негативи.
run_case run_law d8-right-fold-scan-positive tests/semantic/d8-right-fold-scan-law.lisp 1 core4
run_case run_law d8-right-fold-order-mutant tests/semantic/d8-right-fold-order-mutant.lisp 0 core4
run_case run_law d8-right-scan-initial-mutant tests/semantic/d8-right-scan-missing-initial-mutant.lisp 0 core4
run_case run_error_rejection d8-right-fold-atom tests/semantic/d8-right-fold-atom-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d8-right-scan-atom tests/semantic/d8-right-scan-atom-negative.lisp Type 'car expects a non-empty list' core4
run_case run_law d8-right-empty-base tests/semantic/d8-right-empty-base-law.lisp 1 core4
run_case run_error_rejection d8-right-scan-improper-tail tests/semantic/d8-right-scan-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d8-right-fold-improper-tail tests/semantic/d8-right-fold-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
# Д8: структурна Type CAR перед незалежною помилкою дії CDR.
# Чинний Core4 вже завантажено SENS: не дублюємо bootstrap у джерелі.
# Direct, pair --core4-runtime і standalone eval-core4 мають однаковий закон.
run_case run_error_rejection d8-right-fold-structure-before-action tests/fixtures/d8-right-fold-improper-before-action-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d8-right-scan-structure-before-action tests/fixtures/d8-right-scan-improper-before-action-negative.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4.lisp tests/fixtures/d8-right-fold-improper-before-action-negative.lisp tests/fixtures/d8-right-scan-improper-before-action-negative.lisp > "$evidence/d8-right-before-action-inputs.sha256"
sha256sum lib/core4.lisp tests/semantic/d8-right-fold-scan-law.lisp \
  tests/semantic/d8-right-fold-order-mutant.lisp \
  tests/semantic/d8-right-scan-missing-initial-mutant.lisp \
  tests/semantic/d8-right-fold-atom-negative.lisp \
  tests/semantic/d8-right-scan-atom-negative.lisp \
  tests/semantic/d8-right-empty-base-law.lisp \
  tests/semantic/d8-right-scan-improper-tail-negative.lisp \
  tests/semantic/d8-right-fold-improper-tail-negative.lisp > "$evidence/d8-right-fold-scan-inputs.sha256"
# Д6 FILTER-ONTO: непорожній акумулятор має оборотний порядок; мутант хибний.
run_case run_law d6-filter-onto-accumulator-positive tests/semantic/d6-filter-onto-accumulator-law.lisp 1 core4
run_case run_law d6-filter-onto-accumulator-mutant tests/semantic/d6-filter-onto-accumulator-mutant.lisp 0 core4
# D6 FILTER must reject an improper tail with the actual SENS Type diagnostic.
run_case run_error_rejection d6-filter-improper-tail tests/semantic/d6-filter-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4.lisp tests/semantic/d6-filter-independent-law.lisp \
  tests/semantic/d6-filter-independent-mutant.lisp \
  tests/semantic/d6-filter-onto-accumulator-law.lisp \
  tests/semantic/d6-filter-onto-accumulator-mutant.lisp \
  tests/semantic/d6-map-onto-accumulator-law.lisp \
  tests/semantic/d6-map-onto-order-mutant.lisp \
  tests/semantic/d6-map-onto-improper-tail-negative.lisp \
  tests/semantic/d6-reduce-left-law.lisp \
  tests/semantic/d6-reduce-left-mutant.lisp \
  tests/semantic/d6-reduce-improper-tail-negative.lisp \
  tests/semantic/d6-scan-reduce-terminal-law.lisp \
  tests/semantic/d6-scan-missing-initial-mutant.lisp \
  tests/semantic/d6-scan-improper-tail-negative.lisp \
  tests/semantic/d6-scan-onto-atom-negative.lisp \
  tests/semantic/d6-scan-tail-state-law.lisp \
  tests/semantic/d6-scan-tail-state-mutant.lisp \
  tests/semantic/d6-scan-tail-improper-negative.lisp \
  tests/semantic/d6-filter-improper-tail-negative.lisp > "$evidence/d6-filter-inputs.sha256"
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
# Д5 MEMBER/ASSOC: виконувана поточна SENS-бібліотека, НЕ історичний bootstrap.
# Кожний свідок з'єднаний з власним D3-повним ядром: direct/paired/standalone.
# Rust/Zig лише транспорт і діагностика; семантика лишається в SENS.
d5_member_positive="$evidence/d5-member-total-list-positive-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-member-total-list-law.lisp > "$d5_member_positive"
run_case run_law d5-member-total-list-positive "$d5_member_positive" 1 core4
d5_member_mutant="$evidence/d5-member-total-list-mutant-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-member-total-list-mutant.lisp > "$d5_member_mutant"
run_case run_law d5-member-total-list-mutant "$d5_member_mutant" 0 core4
d5_member_tail="$evidence/d5-member-hidden-tail-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-member-hidden-tail-negative.lisp > "$d5_member_tail"
run_case run_error_rejection d5-member-hidden-tail "$d5_member_tail" Type 'car expects a non-empty list' core4
d5_member_root="$evidence/d5-member-nonlist-root-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-member-nonlist-negative.lisp > "$d5_member_root"
run_case run_error_rejection d5-member-nonlist-root "$d5_member_root" Type 'car expects a non-empty list' core4
d5_assoc_positive="$evidence/d5-assoc-total-list-positive-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-assoc-total-list-law.lisp > "$d5_assoc_positive"
run_case run_law d5-assoc-total-list-positive "$d5_assoc_positive" 1 core4
d5_assoc_mutant="$evidence/d5-assoc-total-list-mutant-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-assoc-total-list-mutant.lisp > "$d5_assoc_mutant"
run_case run_law d5-assoc-total-list-mutant "$d5_assoc_mutant" 0 core4
d5_assoc_tail="$evidence/d5-assoc-hidden-tail-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-assoc-hidden-tail-negative.lisp > "$d5_assoc_tail"
run_case run_error_rejection d5-assoc-hidden-tail "$d5_assoc_tail" Type 'car expects a non-empty list' core4
d5_assoc_record="$evidence/d5-assoc-late-record-current-source.lisp"
cat -- lib/core4-parts/core4-d6.lisp tests/semantic/d5-assoc-late-record-negative.lisp > "$d5_assoc_record"
run_case run_error_rejection d5-assoc-late-record "$d5_assoc_record" Type 'car expects a non-empty list' core4
sha256sum lib/core4-parts/core4-d6.lisp tests/semantic/d5-member-*.lisp \
  tests/semantic/d5-assoc-*.lisp > "$evidence/d5-member-assoc-current-source-inputs.sha256"

# Д5: композиції трьох рівнів D3→D4→D5, фізичні позитив і мутант.
run_case run_law d5-selector-derived-positive tests/semantic/d5-selector-derived-law.lisp 1
run_case run_law d5-selector-derived-mutant tests/semantic/d5-selector-derived-mutant.lisp 0
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
# Д11 ALIST: окремий SENS-закон пошуку/першого оновлення/збору,
# незалежний D1-мутант та строгі Type-свідки до виклику компаратора.
d11_association_positive="$evidence/d11-family-association-positive-complete.lisp"
d11_association_mutant="$evidence/d11-family-association-mutant-complete.lisp"
d11_association_late_record="$evidence/d11-family-association-late-record-negative-complete.lisp"
d11_association_invalid_update="$evidence/d11-family-association-invalid-update-negative-complete.lisp"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/semantic/d11-family-association-law.lisp > "$d11_association_positive"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/semantic/d11-family-association-mutant.lisp > "$d11_association_mutant"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/semantic/d11-family-association-late-record-negative.lisp > "$d11_association_late_record"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/semantic/d11-family-association-invalid-update-negative.lisp > "$d11_association_invalid_update"
run_case run_law d11-family-association-positive "$d11_association_positive" 1
run_case run_law d11-family-association-mutant "$d11_association_mutant" 0
run_case run_type_rejection d11-family-association-late-record-type "$d11_association_late_record" 'car expects a non-empty list'
run_case run_type_rejection d11-family-association-invalid-update-type "$d11_association_invalid_update" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-alist-protocol.lisp \
  tests/semantic/d11-family-association-law.lisp \
  tests/semantic/d11-family-association-mutant.lisp \
  tests/semantic/d11-family-association-late-record-negative.lisp \
  tests/semantic/d11-family-association-invalid-update-negative.lisp > "$evidence/d11-family-association-inputs.sha256"
# Д11 ALIST: явна присутність ЗНАЧЕННЯ запису, а не лише запису.
# Справжній SENS відрізняє знайдені D1:ні/D3:() від відсутнього ключа.
d11_alist_value_positive="$evidence/d11-alist-value-presence-positive-complete.lisp"
d11_alist_value_mutant="$evidence/d11-alist-value-presence-mutant-complete.lisp"
d11_alist_value_late="$evidence/d11-alist-value-presence-late-invalid-complete.lisp"
d11_alist_value_priority="$evidence/d11-alist-value-presence-priority-complete.lisp"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/semantic/d11-alist-value-presence-law.lisp > "$d11_alist_value_positive"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/semantic/d11-alist-value-presence-mutant.lisp > "$d11_alist_value_mutant"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/fixtures/d11-alist-value-presence-late-invalid-negative.lisp > "$d11_alist_value_late"
cat -- lib/d11-srfi1-alist-protocol.lisp tests/fixtures/d11-alist-value-presence-priority-negative.lisp > "$d11_alist_value_priority"
run_case run_law d11-alist-value-presence-positive "$d11_alist_value_positive" 1
run_case run_law d11-alist-value-presence-mutant "$d11_alist_value_mutant" 0
run_case run_type_rejection d11-alist-value-presence-late-invalid "$d11_alist_value_late" 'car expects a non-empty list'
run_case run_type_rejection d11-alist-value-presence-priority "$d11_alist_value_priority" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-alist-protocol.lisp \
  tests/semantic/d11-alist-value-presence-*.lisp \
  tests/fixtures/d11-alist-value-presence-*.lisp \
  > "$evidence/d11-alist-value-presence-inputs.sha256"

# Д11: видалення всіх alist-записів зі строгою перевіркою D3 структури.
# SENS сам визначає результат D1/Type; transport перевіряється реальною Zig/T5M парою.
d11_assoc_delete_source=lib/list-foundation-compositions.lisp
d11_assoc_delete_positive="$evidence/d11-assoc-delete-proper-law-complete.lisp"
d11_assoc_delete_mutant="$evidence/d11-assoc-delete-order-mutant-complete.lisp"
d11_assoc_delete_tail="$evidence/d11-assoc-delete-improper-tail-negative-complete.lisp"
d11_assoc_delete_record="$evidence/d11-assoc-delete-invalid-record-negative-complete.lisp"
cat -- "$d11_assoc_delete_source" tests/semantic/d11-assoc-delete-proper-law.lisp > "$d11_assoc_delete_positive"
cat -- "$d11_assoc_delete_source" tests/semantic/d11-assoc-delete-order-mutant.lisp > "$d11_assoc_delete_mutant"
cat -- "$d11_assoc_delete_source" tests/semantic/d11-assoc-delete-improper-tail-negative.lisp > "$d11_assoc_delete_tail"
cat -- "$d11_assoc_delete_source" tests/semantic/d11-assoc-delete-invalid-record-negative.lisp > "$d11_assoc_delete_record"
run_case run_law d11-assoc-delete-positive "$d11_assoc_delete_positive" 1 core4
run_case run_law d11-assoc-delete-mutant "$d11_assoc_delete_mutant" 0 core4
run_case run_error_rejection d11-assoc-delete-improper-tail "$d11_assoc_delete_tail" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-assoc-delete-invalid-record "$d11_assoc_delete_record" Type 'car expects a non-empty list' core4
sha256sum "$d11_assoc_delete_source" \
  tests/semantic/d11-assoc-delete-proper-law.lisp \
  tests/semantic/d11-assoc-delete-order-mutant.lisp \
  tests/semantic/d11-assoc-delete-improper-tail-negative.lisp \
  tests/semantic/d11-assoc-delete-invalid-record-negative.lisp > "$evidence/d11-assoc-delete-inputs.sha256"
# F11-TREE-TEST: двоаргументне SENS-замикання порівнює лише атомні листки.
# Д3 CAR/CDR перевіряє структуру, Zig — лише точний T5M-носій.
d11_tree_test_law_bundle="$evidence/d11-tree-test-law-complete.lisp"
d11_tree_test_mutant_bundle="$evidence/d11-tree-test-mutant-complete.lisp"
cat -- lib/d11-tree-equal-by-test.lisp tests/semantic/d11-tree-equal-by-test-law.lisp > "$d11_tree_test_law_bundle"
cat -- lib/d11-tree-equal-by-test.lisp tests/semantic/d11-tree-equal-by-test-mutant.lisp > "$d11_tree_test_mutant_bundle"
run_case run_law d11-tree-test-positive "$d11_tree_test_law_bundle" 1
run_case run_law d11-tree-test-mutant "$d11_tree_test_mutant_bundle" 0
# Справжній негатив: не-D1 результат листкового компаратора викликає Type.
d11_tree_test_invalid_bundle="$evidence/d11-tree-test-nonpredicate-negative-complete.lisp"
cat -- lib/d11-tree-equal-by-test.lisp tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp > "$d11_tree_test_invalid_bundle"
run_case run_error_rejection d11-tree-test-nonpredicate-negative "$d11_tree_test_invalid_bundle" Type 'D3:110 COND expects exact D1:1 / D1:0'
sha256sum lib/d11-tree-equal-by-test.lisp tests/semantic/d11-tree-equal-by-test-law.lisp \
  tests/semantic/d11-tree-equal-by-test-mutant.lisp \
  tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp > "$evidence/d11-tree-test-inputs.sha256"
# Д11 REASON INDEX: D8 порівнює складені ключі, без D3-atom gate.
reason_index_pair_law="$evidence/d11-reason-index-pair-key-law-complete.lisp"
reason_index_pair_mutant="$evidence/d11-reason-index-pair-key-mutant-complete.lisp"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-pair-key-law.lisp > "$reason_index_pair_law"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-pair-key-mutant.lisp > "$reason_index_pair_mutant"
run_case run_law d11-reason-index-pair-key-law "$reason_index_pair_law" 1 core4
run_case run_law d11-reason-index-pair-key-mutant "$reason_index_pair_mutant" 0 core4
sha256sum lib/reason.lisp \
  tests/semantic/d11-reason-index-pair-key-law.lisp \
  tests/semantic/d11-reason-index-pair-key-mutant.lisp > "$evidence/d11-reason-index-pair-key-inputs.sha256"
# Д11 REASON: точний хвіст перевіряється ще до першого збігу.
reason_early_hit_positive="$evidence/d11-reason-early-hit-proper-positive-complete.lisp"
reason_early_hit_bad_tail="$evidence/d11-reason-early-hit-bad-tail-complete.lisp"
reason_early_hit_mutant="$evidence/d11-reason-early-hit-proper-mutant-complete.lisp"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-early-hit-proper-law.lisp > "$reason_early_hit_positive"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-early-hit-proper-mutant.lisp > "$reason_early_hit_mutant"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-early-hit-improper-tail-negative.lisp > "$reason_early_hit_bad_tail"
run_case run_law d11-reason-early-hit-proper-positive "$reason_early_hit_positive" 1 core4
run_case run_law d11-reason-early-hit-proper-mutant "$reason_early_hit_mutant" 0 core4
run_case run_error_rejection d11-reason-early-hit-improper-tail-type "$reason_early_hit_bad_tail" Type 'car expects a non-empty list' core4
sha256sum lib/unify.lisp lib/reason.lisp \
  tests/semantic/d11-reason-early-hit-proper-law.lisp \
  tests/semantic/d11-reason-early-hit-proper-mutant.lisp \
  tests/semantic/d11-reason-early-hit-improper-tail-negative.lisp > "$evidence/d11-reason-early-hit-inputs.sha256"

# Д11: реальний SENS індекс — закон, мутант і три точні D3 Type-відмови.
reason_index_law_bundle="$evidence/d11-reason-index-law-complete.lisp"
reason_index_mutant_bundle="$evidence/d11-reason-index-mutant-complete.lisp"
reason_index_bad_reverse_bundle="$evidence/d11-reason-index-improper-reverse-complete.lisp"
reason_index_bad_buckets_bundle="$evidence/d11-reason-index-improper-buckets-complete.lisp"
reason_index_bad_rules_bundle="$evidence/d11-reason-index-improper-rules-complete.lisp"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-law.lisp > "$reason_index_law_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-mutant.lisp > "$reason_index_mutant_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-improper-reverse-negative.lisp > "$reason_index_bad_reverse_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-improper-buckets-negative.lisp > "$reason_index_bad_buckets_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-index-improper-rules-negative.lisp > "$reason_index_bad_rules_bundle"
run_case run_law d11-reason-index-law "$reason_index_law_bundle" 1 core4
run_case run_law d11-reason-index-mutant "$reason_index_mutant_bundle" 0 core4
run_case run_error_rejection d11-reason-index-improper-reverse "$reason_index_bad_reverse_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-index-improper-buckets "$reason_index_bad_buckets_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-index-improper-rules "$reason_index_bad_rules_bundle" Type 'car expects a non-empty list' core4
sha256sum lib/reason.lisp lib/unify.lisp tests/semantic/d11-reason-index-*.lisp > "$evidence/d11-reason-index-inputs.sha256"

# D11 proof-results: лише SENS визначає D1, Zig/T5M переносить реальний код.
reason_results_law_bundle="$evidence/d11-reason-proof-results-law-complete.lisp"
reason_results_mutant_bundle="$evidence/d11-reason-proof-results-mutant-complete.lisp"
reason_results_accum_bundle="$evidence/d11-reason-proof-results-improper-accum-complete.lisp"
reason_results_scan_bundle="$evidence/d11-reason-proof-results-improper-scan-complete.lisp"
reason_results_map_bundle="$evidence/d11-reason-proof-results-improper-map-complete.lisp"
reason_results_attach_bundle="$evidence/d11-reason-proof-results-improper-attach-complete.lisp"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-law.lisp > "$reason_results_law_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-mutant.lisp > "$reason_results_mutant_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-improper-accum-negative.lisp > "$reason_results_accum_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-improper-scan-negative.lisp > "$reason_results_scan_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-improper-map-negative.lisp > "$reason_results_map_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-improper-attach-negative.lisp > "$reason_results_attach_bundle"
run_case run_law d11-reason-proof-results-law "$reason_results_law_bundle" 1 core4
run_case run_law d11-reason-proof-results-mutant "$reason_results_mutant_bundle" 0 core4
run_case run_error_rejection d11-reason-proof-results-improper-accum "$reason_results_accum_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-proof-results-improper-scan "$reason_results_scan_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-proof-results-improper-map "$reason_results_map_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-proof-results-improper-attach "$reason_results_attach_bundle" Type 'car expects a non-empty list' core4
sha256sum lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-results-*.lisp > "$evidence/d11-reason-proof-results-inputs.sha256"

# D11 REASON PROVENANCE: точний SENS D3 NIL та D1-невідповідність.
provenance_leaf_law_bundle="$evidence/d11-reason-provenance-children-law-complete.lisp"
provenance_leaf_mutant_bundle="$evidence/d11-reason-provenance-children-mutant-complete.lisp"
provenance_bad_children_bundle="$evidence/d11-reason-provenance-improper-children-complete.lisp"
provenance_bad_explanation_bundle="$evidence/d11-reason-provenance-improper-explanation-complete.lisp"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-provenance-children-law.lisp > "$provenance_leaf_law_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-provenance-children-mutant.lisp > "$provenance_leaf_mutant_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-provenance-improper-children-negative.lisp > "$provenance_bad_children_bundle"
cat -- lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-provenance-improper-explanation-negative.lisp > "$provenance_bad_explanation_bundle"
run_case run_law d11-reason-provenance-children-law "$provenance_leaf_law_bundle" 1 core4
run_case run_law d11-reason-provenance-children-mutant "$provenance_leaf_mutant_bundle" 0 core4
run_case run_error_rejection d11-reason-provenance-improper-children "$provenance_bad_children_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-provenance-improper-explanation "$provenance_bad_explanation_bundle" Type 'car expects a non-empty list' core4
sha256sum lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-provenance-*.lisp > "$evidence/d11-reason-provenance-inputs.sha256"

# F11-PROOF-TRACE: нативний закон SENS, жодної додаткової D11-координати.
# Фактичні визначення беруться лише з lib/reason.lisp (та D9 уніфікатора).
# SENS виконує 2 D1 закони й 2 очікувані Type-помилки через Zig/T5M.
reason_trace_common="$evidence/d11-reason-proof-trace-definitions.lisp"
cat -- lib/unify.lisp lib/reason.lisp > "$reason_trace_common"
reason_trace_law_bundle="$evidence/d11-reason-proof-trace-law-complete.lisp"
reason_trace_mutant_bundle="$evidence/d11-reason-proof-trace-mutant-complete.lisp"
reason_trace_bad_provenance_bundle="$evidence/d11-reason-proof-trace-improper-provenance-negative-complete.lisp"
reason_trace_bad_count_bundle="$evidence/d11-reason-proof-trace-improper-count-negative-complete.lisp"
cat -- "$reason_trace_common" tests/semantic/d11-reason-proof-trace-law.lisp > "$reason_trace_law_bundle"
cat -- "$reason_trace_common" tests/semantic/d11-reason-proof-trace-mutant.lisp > "$reason_trace_mutant_bundle"
cat -- "$reason_trace_common" tests/semantic/d11-reason-proof-trace-improper-provenance-negative.lisp > "$reason_trace_bad_provenance_bundle"
cat -- "$reason_trace_common" tests/semantic/d11-reason-proof-trace-improper-count-negative.lisp > "$reason_trace_bad_count_bundle"
run_case run_law d11-reason-proof-trace-law "$reason_trace_law_bundle" 1 core4
run_case run_law d11-reason-proof-trace-mutant "$reason_trace_mutant_bundle" 0 core4
run_case run_error_rejection d11-reason-proof-trace-improper-provenance "$reason_trace_bad_provenance_bundle" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-reason-proof-trace-improper-count "$reason_trace_bad_count_bundle" Type 'car expects a non-empty list' core4
sha256sum lib/unify.lisp lib/reason.lisp tests/semantic/d11-reason-proof-trace-*.lisp > "$evidence/d11-reason-proof-trace-inputs.sha256"

# D11 SRFI-1 lset: позитив і мутант виконують справжні DEFINE мови SENS.
# Немає нових opcode; Zig/T5M лише фізично переносить код і значення.
d11_set_law_bundle="$evidence/d11-srfi1-set-relations-law-complete.lisp"
d11_set_mutant_bundle="$evidence/d11-srfi1-set-relations-mutant-complete.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-set-relations-law.lisp > "$d11_set_law_bundle"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-set-relations-mutant.lisp > "$d11_set_mutant_bundle"
run_case run_law d11-srfi1-set-relations-positive "$d11_set_law_bundle" 1
run_case run_law d11-srfi1-set-relations-mutant "$d11_set_mutant_bundle" 0
# Д11 lset<=/lset=: структурно хибний єдиний елемент не є множиною.
# Обидві точні D3 Type-відмови перевіряє direct + Zig/T5M + physical SENS.
d11_lset_subset_chain_bad="$evidence/d11-lset-subset-malformed-chain.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/fixtures/d11-lset-subset-malformed-chain-negative.lisp > "$d11_lset_subset_chain_bad"
run_case run_type_rejection d11-lset-subset-malformed-chain "$d11_lset_subset_chain_bad" 'car expects a non-empty list'
d11_lset_equality_chain_bad="$evidence/d11-lset-equality-malformed-chain.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/fixtures/d11-lset-equality-malformed-chain-negative.lisp > "$d11_lset_equality_chain_bad"
run_case run_type_rejection d11-lset-equality-malformed-chain "$d11_lset_equality_chain_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-set-relations.lisp tests/fixtures/d11-lset-{subset,equality}-malformed-chain-negative.lisp > "$evidence/d11-lset-chain-inputs.sha256"

sha256sum lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-set-relations-law.lisp tests/semantic/d11-srfi1-set-relations-mutant.lisp > "$evidence/d11-set-relations-inputs.sha256"
# Д11: точне D3:() для коренів і хвостів; D1:ні не є NULL списку.
# Обидва свідки містять лише чинні SENS DEFINE та виконуються на Zig/T5M.
d11_set_proper_law="$evidence/d11-set-proper-d3-empty-law-complete.lisp"
d11_set_proper_mutant="$evidence/d11-set-proper-d3-empty-mutant-complete.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-set-proper-d3-empty-law.lisp > "$d11_set_proper_law"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-set-proper-d3-empty-mutant.lisp > "$d11_set_proper_mutant"
run_case run_law d11-set-proper-d3-empty-positive "$d11_set_proper_law" 1
run_case run_law d11-set-proper-d3-empty-mutant "$d11_set_proper_mutant" 0
sha256sum lib/d11-srfi1-set-relations.lisp tests/semantic/d11-set-proper-d3-empty-law.lisp tests/semantic/d11-set-proper-d3-empty-mutant.lisp > "$evidence/d11-set-proper-d3-empty-inputs.sha256"
# D11 SRFI-1: навіть короткий шлях повернення ТАК не маскує пошкоджений хвіст.
# Обидва негативні свідки запускають справжню бібліотеку SENS через Zig/T5M.
d11_set_member_bad="$evidence/d11-srfi1-member-improper-hit-complete.lisp"
d11_set_subset_bad="$evidence/d11-srfi1-subset-improper-empty-complete.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-member-improper-hit-negative.lisp > "$d11_set_member_bad"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp > "$d11_set_subset_bad"
run_case run_type_rejection d11-srfi1-member-improper-hit "$d11_set_member_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-srfi1-subset-improper-empty "$d11_set_subset_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-member-improper-hit-negative.lisp tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp > "$evidence/d11-set-improper-inputs.sha256"
# Д11 SRFI-1 LIST-INDEX: точний Д24+ індекс і окремий Д1 прапорець.
# Повний D3 preflight ОБОХ списків до першого callback, навіть якщо
# лівий порожній або ранній збіг сховав би зіпсований правий хвіст.
d11_idx_library=lib/d11-srfi1-list-index-presence.lisp
d11_idx_law="$evidence/d11-list-index-law-complete.lisp"
d11_idx_mutant="$evidence/d11-list-index-mutant-complete.lisp"
cat -- "$d11_idx_library" tests/semantic/d11-srfi1-list-index-presence-law.lisp > "$d11_idx_law"
cat -- "$d11_idx_library" tests/semantic/d11-srfi1-list-index-presence-mutant.lisp > "$d11_idx_mutant"
run_case run_law d11-list-index-presence-law "$d11_idx_law" 1 core4
run_case run_law d11-list-index-presence-mutant "$d11_idx_mutant" 0 core4
for fixture in improper-after-hit pair-right-tail pair-empty-left-bad-right; do
  witness="$evidence/d11-list-index-$fixture-complete.lisp"
  cat -- "$d11_idx_library" "tests/fixtures/d11-srfi1-list-index-$fixture-negative.lisp" > "$witness"
  run_case run_error_rejection "d11-list-index-$fixture" "$witness" Type 'car expects a non-empty list' core4
done
d11_idx_bad_pred="$evidence/d11-list-index-nonpredicate-complete.lisp"
cat -- "$d11_idx_library" tests/fixtures/d11-srfi1-list-index-nonpredicate-negative.lisp > "$d11_idx_bad_pred"
run_case run_error_rejection d11-list-index-nonpredicate "$d11_idx_bad_pred" Type 'D3:110 COND expects exact D1:1 / D1:0' core4
sha256sum "$d11_idx_library" \
  tests/semantic/d11-srfi1-list-index-presence-{law,mutant}.lisp \
  tests/fixtures/d11-srfi1-list-index-*-negative.lisp > "$evidence/d11-list-index-presence-inputs.sha256"

# Д11 SRFI-1 APPEND-REVERSE: статичні SENS-джерела і явні маршрути.
# Rust ownership guard бачить конкретний SOURCE, не $kind-підміну.
rev_append_law="$evidence/d11-append-reverse-law-complete.lisp"
cat -- lib/d11-srfi1-append-reverse.lisp tests/semantic/d11-srfi1-append-reverse-law.lisp > "$rev_append_law"
run_case run_law d11-append-reverse-law "$rev_append_law" 1 core4

rev_append_mutant="$evidence/d11-append-reverse-mutant-complete.lisp"
cat -- lib/d11-srfi1-append-reverse.lisp tests/semantic/d11-srfi1-append-reverse-mutant.lisp > "$rev_append_mutant"
run_case run_law d11-append-reverse-mutant "$rev_append_mutant" 0 core4

rev_append_dotted="$evidence/d11-append-reverse-dotted-tail-law-complete.lisp"
cat -- lib/d11-srfi1-append-reverse.lisp tests/semantic/d11-srfi1-append-reverse-dotted-tail-law.lisp > "$rev_append_dotted"
run_case run_law d11-append-reverse-dotted-tail-law "$rev_append_dotted" 1 core4

rev_append_dotted_mutant="$evidence/d11-append-reverse-dotted-tail-mutant-complete.lisp"
cat -- lib/d11-srfi1-append-reverse.lisp tests/semantic/d11-srfi1-append-reverse-dotted-tail-mutant.lisp > "$rev_append_dotted_mutant"
run_case run_law d11-append-reverse-dotted-tail-mutant "$rev_append_dotted_mutant" 0 core4

for invalid in d1-root late-improper deep-improper; do
  rev_append_negative="$evidence/d11-append-reverse-$invalid-complete.lisp"
  cat -- lib/d11-srfi1-append-reverse.lisp \
    "tests/fixtures/d11-srfi1-append-reverse-$invalid-negative.lisp" > "$rev_append_negative"
  run_case run_error_rejection "d11-append-reverse-$invalid" \
    "$rev_append_negative" Type 'car expects a non-empty list' core4
done
sha256sum lib/d11-srfi1-append-reverse.lisp \
  tests/semantic/d11-srfi1-append-reverse-*.lisp \
  tests/fixtures/d11-srfi1-append-reverse-*-negative.lisp \
  > "$evidence/d11-append-reverse-inputs.sha256"

# SRFI-1 LIST-TABULATE: лише SENS створює елементи й виносить D1-вердикт.
# Усі три шляхи мають той самий Core4 (D24+, D3, D4, D6 REVERSE).
for kind in law values-law mutant; do
  tabulate_source="$evidence/d11-list-tabulate-$kind.lisp"
  cat -- lib/d11-srfi1-list-tabulate.lisp "tests/semantic/d11-srfi1-list-tabulate-$kind.lisp" > "$tabulate_source"
  tabulate_expected=1
  [[ "$kind" != mutant ]] || tabulate_expected=0
  run_case run_law "d11-list-tabulate-$kind" "$tabulate_source" "$tabulate_expected" core4
done
# Незалежний D11 мутант: D3:() всередині cons не є порожнім зовнішнім списком.
tabulate_empty_element_mutant="$evidence/d11-list-tabulate-empty-element-mutant.lisp"
cat -- lib/d11-srfi1-list-tabulate.lisp \
  tests/semantic/d11-srfi1-list-tabulate-empty-element-mutant.lisp > "$tabulate_empty_element_mutant"
run_case run_law d11-list-tabulate-empty-element-mutant "$tabulate_empty_element_mutant" 0 core4
for invalid in d1-count negative-count fraction-count; do
  tabulate_negative="$evidence/d11-list-tabulate-$invalid-type.lisp"
  cat -- lib/d11-srfi1-list-tabulate.lisp "tests/fixtures/d11-srfi1-list-tabulate-$invalid-negative.lisp" > "$tabulate_negative"
  run_case run_error_rejection "d11-list-tabulate-$invalid" "$tabulate_negative" \
    Type 'car expects a non-empty list' core4
done
sha256sum lib/d11-srfi1-list-tabulate.lisp \
  tests/semantic/d11-srfi1-list-tabulate-*.lisp \
  tests/fixtures/d11-srfi1-list-tabulate-*-negative.lisp \
  > "$evidence/d11-list-tabulate-inputs.sha256"



# Д11 Contract 12.0: пояснення окремим запитом без 3-го значення D1.
# Усі нормативні відповіді повертає SENS; Zig пакує фізичний T5M.
d11_status_law="$evidence/d11-query-status-positive-complete.lisp"
d11_status_mutant="$evidence/d11-query-status-mutant-complete.lisp"
d11_status_bad="$evidence/d11-query-status-improper-complete.lisp"
d11_status_preflight="$evidence/d11-query-status-preflight-complete.lisp"
cat -- lib/d11-query-unique.lisp tests/semantic/d11-query-status-law.lisp > "$d11_status_law"
cat -- lib/d11-query-unique.lisp tests/semantic/d11-query-status-mutant.lisp > "$d11_status_mutant"
cat -- lib/d11-query-unique.lisp tests/fixtures/d11-query-status-improper-negative.lisp > "$d11_status_bad"
cat -- lib/d11-query-unique.lisp tests/fixtures/d11-query-status-preflight-negative.lisp > "$d11_status_preflight"
run_case run_law d11-query-status-positive "$d11_status_law" 1 core4
run_case run_law d11-query-status-mutant "$d11_status_mutant" 0 core4
run_case run_error_rejection d11-query-status-improper "$d11_status_bad" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-query-status-preflight "$d11_status_preflight" Type 'car expects a non-empty list' core4
sha256sum lib/d11-query-unique.lisp tests/semantic/d11-query-status-*.lisp \
  tests/fixtures/d11-query-status-*-negative.lisp > "$evidence/d11-query-status-inputs.sha256"

# D11: два конкретні свідки неоднозначності без нової координати.
d11_two_law="$evidence/d11-query-two-witness-positive.lisp"
d11_two_mutant="$evidence/d11-query-two-witness-mutant.lisp"
d11_two_bad="$evidence/d11-query-two-witness-improper.lisp"
d11_two_poison="$evidence/d11-query-two-witness-preflight.lisp"
cat -- lib/d11-query-unique.lisp tests/semantic/d11-query-two-witness-law.lisp > "$d11_two_law"
cat -- lib/d11-query-unique.lisp tests/semantic/d11-query-two-witness-mutant.lisp > "$d11_two_mutant"
cat -- lib/d11-query-unique.lisp tests/fixtures/d11-query-two-witness-improper-negative.lisp > "$d11_two_bad"
cat -- lib/d11-query-unique.lisp tests/fixtures/d11-query-two-witness-preflight-negative.lisp > "$d11_two_poison"
run_case run_law d11-query-two-witness-positive "$d11_two_law" 1 core4
run_case run_law d11-query-two-witness-mutant "$d11_two_mutant" 0 core4
run_case run_error_rejection d11-query-two-witness-improper "$d11_two_bad" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-query-two-witness-preflight "$d11_two_poison" Type 'car expects a non-empty list' core4
sha256sum lib/d11-query-unique.lisp tests/semantic/d11-query-two-witness-*.lisp \
  tests/fixtures/d11-query-two-witness-*-negative.lisp > "$evidence/d11-query-two-witness-inputs.sha256"

# Д11: однозначний пошук — чистий SENS, без третьої істини чи D11 opcode.
# Два проходи: повний D3-хребет перед предикатом, потім вибір 0/1/2+.
d11_unique_law="$evidence/d11-unique-query-positive.lisp"
d11_unique_mutant="$evidence/d11-unique-query-mutant.lisp"
d11_unique_improper="$evidence/d11-unique-query-improper.lisp"
d11_unique_poisoned="$evidence/d11-unique-query-poisoned.lisp"
cat -- lib/d11-query-unique.lisp tests/semantic/d11-query-unique-law.lisp > "$d11_unique_law"
cat -- lib/d11-query-unique.lisp tests/semantic/d11-query-unique-mutant.lisp > "$d11_unique_mutant"
cat -- lib/d11-query-unique.lisp tests/fixtures/d11-query-unique-improper-negative.lisp > "$d11_unique_improper"
cat -- lib/d11-query-unique.lisp tests/fixtures/d11-query-unique-preflight-negative.lisp > "$d11_unique_poisoned"
run_case run_law d11-unique-query-positive "$d11_unique_law" 1 core4
run_case run_law d11-unique-query-mutant "$d11_unique_mutant" 0 core4
run_case run_error_rejection d11-unique-query-improper-tail "$d11_unique_improper" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-unique-query-preflight "$d11_unique_poisoned" Type 'car expects a non-empty list' core4
sha256sum lib/d11-query-unique.lisp tests/semantic/d11-query-unique-*.lisp \
  tests/fixtures/d11-query-unique-*-negative.lisp > "$evidence/d11-unique-query-inputs.sha256"

# SRFI-1 list=: алгоритм з чинної lib/D11, очікувані предикати тільки в Lisp.
# Не тестуємо D11-операцію Rust-оракулом; Zig тільки кодує фізичні байти.
d11_list_equal_law_bundle="$evidence/d11-list-equality-positive.lisp"
d11_list_equal_mutant_bundle="$evidence/d11-list-equality-negative.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-law.lisp > "$d11_list_equal_law_bundle"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-mutant.lisp > "$d11_list_equal_mutant_bundle"
run_case run_law d11-srfi1-list-equality-positive "$d11_list_equal_law_bundle" 1
# Три незалежні SENS-виконання ізолюють структуру, попарні закони та n=0.
# Будь-який D1:ні залишається RED; тут немає хостової семантики.
# Точна SENS-маршрутизація структури й мутанта потрібна також guard'у:
# динамічне ім'я $family саме по собі не є доказом конкретного SOURCE.
d11_list_equal_structure="$evidence/d11-list-equality-structure-isolated.lisp"
d11_list_equal_structure_mutant="$evidence/d11-list-equality-structure-mutant-isolated.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-structure-law.lisp > "$d11_list_equal_structure"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-structure-mutant.lisp > "$d11_list_equal_structure_mutant"
run_case run_law d11-srfi1-list-equality-structure-positive "$d11_list_equal_structure" 1
run_case run_law d11-srfi1-list-equality-structure-mutant "$d11_list_equal_structure_mutant" 0
# Д11 LIST=: WRONG D3 є Type, а не D1:ні. Після валідного префікса
# відмова повинна виникнути ДО порівнювача, навіть якщо він отруєний.
for improper in wrong-root late-improper-tail outer-improper-tail nested-improper-preflight; do
  list_equal_type_source="$evidence/d11-list-equality-$improper-expected-type.lisp"
  cat -- lib/d11-srfi1-list-equality.lisp \
    "tests/fixtures/d11-srfi1-list-equality-$improper-negative.lisp" > "$list_equal_type_source"
  run_case run_error_rejection "d11-list-equality-$improper" "$list_equal_type_source" \
    Type 'car expects a non-empty list' core4
done
sha256sum lib/d11-srfi1-list-equality.lisp \
  tests/semantic/d11-srfi1-list-equality-{law,structure-law,structure-mutant}.lisp \
  tests/fixtures/d11-srfi1-list-equality-*-negative.lisp \
  > "$evidence/d11-list-equality-d3-type-boundary.sha256"

for family in pairs nullary; do
  witness="$evidence/d11-list-equality-$family-isolated.lisp"
  cat -- lib/d11-srfi1-list-equality.lisp "tests/semantic/d11-srfi1-list-equality-$family-law.lisp" > "$witness"
  run_case run_law "d11-srfi1-list-equality-$family-positive" "$witness" 1
done
sha256sum tests/semantic/d11-srfi1-list-equality-{structure,pairs,nullary}-law.lisp > "$evidence/d11-list-equality-isolated-inputs.sha256"

run_case run_law d11-srfi1-list-equality-mutant "$d11_list_equal_mutant_bundle" 0
# Д11 LIST=: один точний шлях для кожного закону й мутанта.
d11_direction_0="$evidence/directed-law-witness.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-directed-law.lisp > "$d11_direction_0"
run_case run_law d11-direction-directed-law "$d11_direction_0" 1
d11_direction_1="$evidence/directed-mutant-witness.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-directed-mutant.lisp > "$d11_direction_1"
run_case run_law d11-direction-directed-mutant "$d11_direction_1" 0
d11_direction_2="$evidence/directed-pairs-law-witness.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-directed-pairs-law.lisp > "$d11_direction_2"
run_case run_law d11-direction-directed-pairs-law "$d11_direction_2" 1
d11_direction_3="$evidence/directed-pairs-mutant-witness.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-directed-pairs-mutant.lisp > "$d11_direction_3"
run_case run_law d11-direction-directed-pairs-mutant "$d11_direction_3" 0
d11_direction_4="$evidence/directed-adjacent-law-witness.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-directed-adjacent-law.lisp > "$d11_direction_4"
run_case run_law d11-direction-directed-adjacent-law "$d11_direction_4" 1
d11_direction_5="$evidence/directed-adjacent-mutant-witness.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-directed-adjacent-mutant.lisp > "$d11_direction_5"
run_case run_law d11-direction-directed-adjacent-mutant "$d11_direction_5" 0
sha256sum tests/semantic/d11-srfi1-list-equality-directed-law.lisp tests/semantic/d11-srfi1-list-equality-directed-mutant.lisp tests/semantic/d11-srfi1-list-equality-directed-pairs-law.lisp tests/semantic/d11-srfi1-list-equality-directed-pairs-mutant.lisp tests/semantic/d11-srfi1-list-equality-directed-adjacent-law.lisp tests/semantic/d11-srfi1-list-equality-directed-adjacent-mutant.lisp > "$evidence/d11-directed-inputs.sha256"


# SRFI-1 list= rejects malformed input even when early length/value cases could
# otherwise short-circuit. Each negative is checked as a real Type error through
# direct SENS, Zig/T5M paired execution, and standalone physical SENS.
d11_list_equal_bad_left="$evidence/d11-list-equality-improper-left-complete.lisp"
d11_list_equal_bad_right="$evidence/d11-list-equality-improper-right-complete.lisp"
d11_list_equal_bad_singleton="$evidence/d11-list-equality-invalid-singleton-complete.lisp"
d11_list_equal_bad_third="$evidence/d11-list-equality-invalid-third-complete.lisp"
cat -- lib/d11-srfi1-list-equality.lisp tests/fixtures/d11-list-equality-improper-left-must-error.lisp > "$d11_list_equal_bad_left"
cat -- lib/d11-srfi1-list-equality.lisp tests/fixtures/d11-list-equality-improper-right-must-error.lisp > "$d11_list_equal_bad_right"
cat -- lib/d11-srfi1-list-equality.lisp tests/fixtures/d11-list-equality-invalid-singleton-must-error.lisp > "$d11_list_equal_bad_singleton"
cat -- lib/d11-srfi1-list-equality.lisp tests/fixtures/d11-list-equality-invalid-third-must-error.lisp > "$d11_list_equal_bad_third"
# Поточна нативна SENS-реалізація Type через D3 ПЕРШЕ на D3 ().
# Старий D1 not-callable більше не є чинною помилкою цих законів.
d11_list_equal_type_error='car expects a non-empty list'
run_case run_type_rejection d11-list-equality-improper-left-type "$d11_list_equal_bad_left" "$d11_list_equal_type_error"
run_case run_type_rejection d11-list-equality-improper-right-type "$d11_list_equal_bad_right" "$d11_list_equal_type_error"
run_case run_type_rejection d11-list-equality-invalid-singleton-type "$d11_list_equal_bad_singleton" "$d11_list_equal_type_error"
run_case run_type_rejection d11-list-equality-invalid-third-type "$d11_list_equal_bad_third" "$d11_list_equal_type_error"
sha256sum lib/d11-srfi1-list-equality.lisp tests/semantic/d11-srfi1-list-equality-law.lisp tests/semantic/d11-srfi1-list-equality-mutant.lisp tests/fixtures/d11-list-equality-improper-left-must-error.lisp tests/fixtures/d11-list-equality-improper-right-must-error.lisp tests/fixtures/d11-list-equality-invalid-singleton-must-error.lisp tests/fixtures/d11-list-equality-invalid-third-must-error.lisp > "$evidence/d11-list-equality-inputs.sha256"
# Д11 SRFI-1 COUNT: без D24 та host-арифметики; результат — D1 унарний список.
# Незалежні SENS law/mutant і дві строгі помилки неправильного хвоста.
d11_unary_count_positive="$evidence/d11-unary-count-positive-complete.lisp"
d11_unary_count_mutant="$evidence/d11-unary-count-mutant-complete.lisp"
d11_unary_count_bad_tail="$evidence/d11-unary-count-bad-tail-complete.lisp"
d11_unary_count_bad_right="$evidence/d11-unary-count-bad-right-complete.lisp"
cat -- lib/d11-srfi1-unary-count.lisp tests/semantic/d11-srfi1-unary-count-law.lisp > "$d11_unary_count_positive"
cat -- lib/d11-srfi1-unary-count.lisp tests/semantic/d11-srfi1-unary-count-mutant.lisp > "$d11_unary_count_mutant"
cat -- lib/d11-srfi1-unary-count.lisp tests/semantic/d11-srfi1-unary-count-improper-tail-negative.lisp > "$d11_unary_count_bad_tail"
cat -- lib/d11-srfi1-unary-count.lisp tests/semantic/d11-srfi1-unary-count-improper-right-negative.lisp > "$d11_unary_count_bad_right"
run_case run_law d11-unary-count-positive "$d11_unary_count_positive" 1
run_case run_law d11-unary-count-mutant "$d11_unary_count_mutant" 0
run_case run_type_rejection d11-unary-count-improper-tail-type "$d11_unary_count_bad_tail" 'car expects a non-empty list'
run_case run_type_rejection d11-unary-count-improper-right-type "$d11_unary_count_bad_right" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-unary-count.lisp tests/semantic/d11-srfi1-unary-count-law.lisp tests/semantic/d11-srfi1-unary-count-mutant.lisp tests/semantic/d11-srfi1-unary-count-improper-tail-negative.lisp tests/semantic/d11-srfi1-unary-count-improper-right-negative.lisp > "$evidence/d11-unary-count-inputs.sha256"
# Д11 НАС-форм: перед раннім збігом обов'язкова правильна D3-структура.
# Перевірка здійснюється самим SENS на direct, Zig/T5M paired і standalone.
d11_form_positive="$evidence/d11-form-presence-positive-complete.lisp"
d11_form_mutant="$evidence/d11-form-presence-mutant-complete.lisp"
cat -- lib/d11-form-presence.lisp tests/semantic/d11-form-presence-law.lisp > "$d11_form_positive"
cat -- lib/d11-form-presence.lisp tests/semantic/d11-form-presence-mutant.lisp > "$d11_form_mutant"
run_case run_law d11-form-presence-positive "$d11_form_positive" 1
run_case run_law d11-form-presence-mutant "$d11_form_mutant" 0
d11_form_bad_match="$evidence/d11-form-presence-improper-match.lisp"
cat -- lib/d11-form-presence.lisp tests/fixtures/d11-form-presence-improper-match-negative.lisp > "$d11_form_bad_match"
run_case run_type_rejection d11-form-presence-improper-match "$d11_form_bad_match" 'car expects a non-empty list'
d11_form_bad_miss="$evidence/d11-form-presence-improper-miss.lisp"
cat -- lib/d11-form-presence.lisp tests/fixtures/d11-form-presence-improper-miss-negative.lisp > "$d11_form_bad_miss"
run_case run_type_rejection d11-form-presence-improper-miss "$d11_form_bad_miss" 'car expects a non-empty list'
# Вкладений D1-хвіст не приховується раннім збігом DEFINE.
d11_form_bad_deep="$evidence/d11-form-presence-deep-improper-complete.lisp"
cat -- lib/d11-form-presence.lisp tests/fixtures/d11-form-presence-deep-improper-negative.lisp > "$d11_form_bad_deep"
run_case run_type_rejection d11-form-presence-deep-improper "$d11_form_bad_deep" 'car expects a non-empty list'
sha256sum lib/d11-form-presence.lisp tests/fixtures/d11-form-presence-improper-{match,miss}-negative.lisp tests/fixtures/d11-form-presence-deep-improper-negative.lisp > "$evidence/d11-form-presence-inputs.sha256"
# Д11 LIST-TERMINATOR: D1:ні є даними неправильного хвоста, D3:() — кінець.
# Фізична SENS-бібліотека та незалежний позитив/мутант використовують одні DEFINE.
d11_terminator_positive="$evidence/d11-list-terminator-positive-complete.lisp"
d11_terminator_mutant="$evidence/d11-list-terminator-mutant-complete.lisp"
cat -- lib/d11-list-terminator-evidence.lisp tests/semantic/d11-list-terminator-law.lisp > "$d11_terminator_positive"
cat -- lib/d11-list-terminator-evidence.lisp tests/semantic/d11-list-terminator-mutant.lisp > "$d11_terminator_mutant"
run_case run_law d11-list-terminator-positive "$d11_terminator_positive" 1
run_case run_law d11-list-terminator-mutant "$d11_terminator_mutant" 0
sha256sum lib/d11-list-terminator-evidence.lisp tests/semantic/d11-list-terminator-law.lisp tests/semantic/d11-list-terminator-mutant.lisp > "$evidence/d11-list-terminator-inputs.sha256"
# Д11 FIND-PRESENCE: прапорець наявності незалежний від знайденого значення.
# Чинний SENS DEFINE, точний D1 позитив/мутант та неправильний D1-хвіст.
d11_presence_positive="$evidence/d11-srfi1-find-presence-positive-complete.lisp"
d11_presence_mutant="$evidence/d11-srfi1-find-presence-mutant-complete.lisp"
d11_presence_bad_tail="$evidence/d11-srfi1-find-presence-improper-tail-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp tests/semantic/d11-srfi1-find-presence-law.lisp > "$d11_presence_positive"
cat -- lib/d11-srfi1-find-presence.lisp tests/semantic/d11-srfi1-find-presence-mutant.lisp > "$d11_presence_mutant"
cat -- lib/d11-srfi1-find-presence.lisp tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp > "$d11_presence_bad_tail"
run_case run_law d11-srfi1-find-presence-positive "$d11_presence_positive" 1
run_case run_law d11-srfi1-find-presence-mutant "$d11_presence_mutant" 0
run_case run_type_rejection d11-srfi1-find-presence-improper-tail-type "$d11_presence_bad_tail" 'car expects a non-empty list'
d11_presence_atomic_root="$evidence/d11-find-presence-atomic-root-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp tests/fixtures/d11-find-presence-atomic-root-negative.lisp > "$d11_presence_atomic_root"
run_case run_type_rejection d11-find-presence-atomic-root-type "$d11_presence_atomic_root" 'car expects a non-empty list'
d11_presence_early="$evidence/d11-find-presence-early-improper.lisp"
cat -- lib/d11-srfi1-find-presence.lisp tests/semantic/d11-srfi1-find-presence-early-hit-improper-negative.lisp > "$d11_presence_early"
run_case run_type_rejection d11-find-presence-early-hit-improper "$d11_presence_early" "car expects a non-empty list"
sha256sum lib/d11-srfi1-find-presence.lisp tests/semantic/d11-srfi1-find-presence-law.lisp tests/semantic/d11-srfi1-find-presence-mutant.lisp tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp tests/semantic/d11-srfi1-find-presence-early-hit-improper-negative.lisp > "$evidence/d11-find-presence-inputs.sha256"
# Д11 FIND-LAST-PRESENCE: єдиний валідатор D3, чистий рекурсивний SENS.
# Залежності — точні DEFINE з FIND-PRESENCE та цього бібліотечного файла.
d11_last_positive="$evidence/d11-find-last-presence-positive.lisp"
d11_last_mutant="$evidence/d11-find-last-presence-mutant.lisp"
d11_last_invalid="$evidence/d11-find-last-presence-improper.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-presence.lisp \
  tests/semantic/d11-find-last-presence-law.lisp > "$d11_last_positive"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-presence.lisp \
  tests/semantic/d11-find-last-presence-mutant.lisp > "$d11_last_mutant"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-presence.lisp \
  tests/semantic/d11-find-last-presence-improper-negative.lisp > "$d11_last_invalid"
run_case run_law d11-find-last-presence-positive "$d11_last_positive" 1
run_case run_law d11-find-last-presence-mutant "$d11_last_mutant" 0
run_case run_type_rejection d11-find-last-presence-improper "$d11_last_invalid" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-presence.lisp \
  tests/semantic/d11-find-last-presence-*.lisp > "$evidence/d11-find-last-presence-inputs.sha256"

# Д11 FIRST-TAIL-PRESENCE: D1 наявність окремо від D3 суфікса.
# Нативний SENS → Zig/T5M → paired/standalone SENS, без host-оцінювання.
first_tail_presence_positive="$evidence/d11-find-first-tail-presence-positive.lisp"
first_tail_presence_mutant="$evidence/d11-find-first-tail-presence-mutant.lisp"
first_tail_presence_bad="$evidence/d11-find-first-tail-presence-improper.lisp"
first_tail_presence_helper_bad="$evidence/d11-find-first-tail-presence-helper-atom.lisp"
cat -- lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp \
  tests/semantic/d11-find-first-tail-presence-law.lisp > "$first_tail_presence_positive"
cat -- lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp \
  tests/semantic/d11-find-first-tail-presence-mutant.lisp > "$first_tail_presence_mutant"
cat -- lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp \
  tests/semantic/d11-find-first-tail-presence-improper-negative.lisp > "$first_tail_presence_bad"
run_case run_law d11-find-first-tail-presence-positive "$first_tail_presence_positive" 1
run_case run_law d11-find-first-tail-presence-mutant "$first_tail_presence_mutant" 0
run_case run_type_rejection d11-find-first-tail-presence-improper "$first_tail_presence_bad" 'car expects a non-empty list'
cat -- lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp \
  tests/semantic/d11-find-first-tail-presence-helper-atom-negative.lisp > "$first_tail_presence_helper_bad"
run_case run_type_rejection d11-find-first-tail-presence-helper-atom "$first_tail_presence_helper_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp \
  tests/semantic/d11-find-first-tail-presence-*.lisp > "$evidence/d11-find-first-tail-presence-inputs.sha256"

# Д11 LAST-TAIL: підтвердити суфікс останнього збігу лише мовою SENS.
last_tail_positive="$evidence/d11-last-tail-positive.lisp"
last_tail_mutant="$evidence/d11-last-tail-mutant.lisp"
last_tail_bad="$evidence/d11-last-tail-improper.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp tests/semantic/d11-find-last-tail-law.lisp > "$last_tail_positive"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp tests/semantic/d11-find-last-tail-mutant.lisp > "$last_tail_mutant"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp tests/semantic/d11-find-last-tail-improper-negative.lisp > "$last_tail_bad"
run_case run_law d11-find-last-tail-positive "$last_tail_positive" 1
run_case run_law d11-find-last-tail-mutant "$last_tail_mutant" 0
run_case run_type_rejection d11-find-last-tail-improper "$last_tail_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp tests/semantic/d11-find-last-tail-*.lisp > "$evidence/d11-last-tail-inputs.sha256"

# Д11 FIND-LAST-VALUE-PRESENCE: останнє D1/D3-значення з D1 прапорцем.
last_value_positive="$evidence/d11-find-last-value-presence-positive-complete.lisp"
last_value_mutant="$evidence/d11-find-last-value-presence-mutant-complete.lisp"
last_value_bad="$evidence/d11-find-last-value-presence-improper-complete.lisp"
last_value_precedence="$evidence/d11-find-last-value-presence-priority-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp lib/d11-srfi1-find-last-value-presence.lisp tests/semantic/d11-find-last-value-presence-law.lisp > "$last_value_positive"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp lib/d11-srfi1-find-last-value-presence.lisp tests/semantic/d11-find-last-value-presence-mutant.lisp > "$last_value_mutant"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp lib/d11-srfi1-find-last-value-presence.lisp tests/fixtures/d11-find-last-value-presence-improper-negative.lisp > "$last_value_bad"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp lib/d11-srfi1-find-last-value-presence.lisp tests/fixtures/d11-find-last-value-presence-predicate-priority-negative.lisp > "$last_value_precedence"
run_case run_law d11-find-last-value-presence-positive "$last_value_positive" 1
run_case run_law d11-find-last-value-presence-mutant "$last_value_mutant" 0
run_case run_type_rejection d11-find-last-value-presence-improper "$last_value_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-find-last-value-presence-before-predicate "$last_value_precedence" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp \
  lib/d11-srfi1-find-last-value-presence.lisp \
  tests/semantic/d11-find-last-value-presence-*.lisp \
  tests/fixtures/d11-find-last-value-presence-*.lisp \
  > "$evidence/d11-find-last-value-presence-inputs.sha256"

# Д11: розділити перед останнім збігом, явний D1 прапорець.
# Значення, порядок, хибна перша позиція й Type — SENS, не shell.
split_last_positive="$evidence/d11-split-last-positive.lisp"
split_last_mutant="$evidence/d11-split-last-mutant.lisp"
split_last_invalid="$evidence/d11-split-last-improper.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp tests/semantic/d11-split-before-last-law.lisp > "$split_last_positive"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp tests/semantic/d11-split-before-last-mutant.lisp > "$split_last_mutant"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp tests/semantic/d11-split-before-last-improper-negative.lisp > "$split_last_invalid"
run_case run_law d11-split-last-positive "$split_last_positive" 1
run_case run_law d11-split-last-mutant "$split_last_mutant" 0
run_case run_type_rejection d11-split-last-improper "$split_last_invalid" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp tests/semantic/d11-split-before-last-*.lisp > "$evidence/d11-split-last-inputs.sha256"

# Д11 APPEND-MAP: суворий SENS-профіль чинного D10:0011001010 MAPPEND.
# Core4 визначає сам D10 MAPPEND, бібліотека D11 додає лише перевірку D3.
# Джерело закону, результат і Type-відмови — SENS, не Shell/Rust/Python.
d11_append_map_positive="$evidence/d11-append-map-positive-complete.lisp"
d11_append_map_mutant="$evidence/d11-append-map-mutant-complete.lisp"
d11_append_map_bad_input="$evidence/d11-append-map-bad-input-complete.lisp"
d11_append_map_bad_output="$evidence/d11-append-map-bad-output-complete.lisp"
cat -- lib/d11-srfi1-append-map.lisp tests/semantic/d11-srfi1-append-map-law.lisp > "$d11_append_map_positive"
cat -- lib/d11-srfi1-append-map.lisp tests/semantic/d11-srfi1-append-map-mutant.lisp > "$d11_append_map_mutant"
cat -- lib/d11-srfi1-append-map.lisp tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp > "$d11_append_map_bad_input"
cat -- lib/d11-srfi1-append-map.lisp tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp > "$d11_append_map_bad_output"
run_case run_law d11-append-map-d10-equivalence "$d11_append_map_positive" 1 core4
run_case run_law d11-append-map-order-mutant "$d11_append_map_mutant" 0 core4
run_case run_error_rejection d11-append-map-improper-input "$d11_append_map_bad_input" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-append-map-improper-output "$d11_append_map_bad_output" Type 'car expects a non-empty list' core4
sha256sum lib/d11-srfi1-append-map.lisp tests/semantic/d11-srfi1-append-map-law.lisp \
  tests/semantic/d11-srfi1-append-map-mutant.lisp \
  tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp \
  tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp \
  > "$evidence/d11-append-map-inputs.sha256"

# Д11 SRFI-1 FILTER-MAP: D1:ні відкидається, структурне () зберігається.
# Справжній SENS source → Zig/T5M → парний і самостійний SENS.
d11_filter_map_positive="$evidence/d11-srfi1-filter-map-positive.lisp"
d11_filter_map_mutant="$evidence/d11-srfi1-filter-map-mutant.lisp"
cat -- lib/d11-srfi1-filter-map.lisp tests/semantic/d11-srfi1-filter-map-law.lisp > "$d11_filter_map_positive"
cat -- lib/d11-srfi1-filter-map.lisp tests/semantic/d11-srfi1-filter-map-mutant.lisp > "$d11_filter_map_mutant"
run_case run_law d11-srfi1-filter-map-positive "$d11_filter_map_positive" 1
run_case run_law d11-srfi1-filter-map-mutant "$d11_filter_map_mutant" 0
sha256sum lib/d11-srfi1-filter-map.lisp tests/semantic/d11-srfi1-filter-map-law.lisp tests/semantic/d11-srfi1-filter-map-mutant.lisp > "$evidence/d11-srfi1-filter-map-inputs.sha256"
# Д11 FILTER-MAP: атомарний корінь та D1-хвіст мають давати SENS Type,
# а не помилковий успіх, тихе усікання чи D7 UnknownSymbol.
d11_filter_bad_root="$evidence/d11-filter-map-improper-root-complete.lisp"
d11_filter_bad_tail="$evidence/d11-filter-map-improper-tail-complete.lisp"
cat -- lib/d11-srfi1-filter-map.lisp tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp > "$d11_filter_bad_root"
cat -- lib/d11-srfi1-filter-map.lisp tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp > "$d11_filter_bad_tail"
# Неправильні корінь та хвіст відхиляє точний нативний D3 CAR Type.
d11_filter_map_type_error='car expects a non-empty list'
run_case run_type_rejection d11-srfi1-filter-map-improper-root-type "$d11_filter_bad_root" "$d11_filter_map_type_error"
run_case run_type_rejection d11-srfi1-filter-map-improper-tail-type "$d11_filter_bad_tail" "$d11_filter_map_type_error"
# Д11 FILTER-MAP: перевірка структури має передувати mapper з іншою Type.
d11_filter_prevalidate_bad="$evidence/d11-filter-map-prevalidate-bad-complete.lisp"
cat -- lib/d11-srfi1-filter-map.lisp tests/fixtures/d11-filter-map-improper-precedes-transform-negative.lisp > "$d11_filter_prevalidate_bad"
run_case run_type_rejection d11-filter-map-prevalidate-before-transform-type "$d11_filter_prevalidate_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-filter-map.lisp tests/fixtures/d11-filter-map-improper-precedes-transform-negative.lisp > "$evidence/d11-filter-map-prevalidate-inputs.sha256"
sha256sum lib/d11-srfi1-filter-map.lisp tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp > "$evidence/d11-filter-map-improper-inputs.sha256"

# Д11 SRFI-1: UNFOLD/UNFOLD-RIGHT є чистими композиціями SENS.
# Джерело тестів — Lisp, Zig лише несе T5M; помилковий порядок = D1:ні.
d11_unfold_positive="$evidence/d11-srfi1-unfold-positive-complete.lisp"
d11_unfold_mutant="$evidence/d11-srfi1-unfold-mutant-complete.lisp"
cat -- lib/d11-srfi1-unfold.lisp tests/semantic/d11-srfi1-unfold-positive.lisp > "$d11_unfold_positive"
cat -- lib/d11-srfi1-unfold.lisp tests/semantic/d11-srfi1-unfold-mutant.lisp > "$d11_unfold_mutant"
run_case run_law d11-srfi1-unfold-positive "$d11_unfold_positive" 1
run_case run_law d11-srfi1-unfold-mutant "$d11_unfold_mutant" 0
sha256sum lib/d11-srfi1-unfold.lisp tests/semantic/d11-srfi1-unfold-positive.lisp tests/semantic/d11-srfi1-unfold-mutant.lisp > "$evidence/d11-srfi1-unfold-inputs.sha256"
# Д11 UNFOLD обох напрямків: структурний D3:() не є D1-предикатом.
# Два незалежні строгі SENS Type-свідки, Zig/T5M і повне фізичне виконання.
d11_unfold_bad_predicate="$evidence/d11-unfold-nonpredicate-stop-complete.lisp"
d11_unfold_right_bad_predicate="$evidence/d11-unfold-right-nonpredicate-stop-complete.lisp"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-nonpredicate-stop-must-error.lisp > "$d11_unfold_bad_predicate"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-right-nonpredicate-stop-must-error.lisp > "$d11_unfold_right_bad_predicate"
run_case run_error_rejection d11-unfold-nonpredicate-stop "$d11_unfold_bad_predicate" Type 'D3:110 COND expects exact D1:1 / D1:0'
run_case run_error_rejection d11-unfold-right-nonpredicate-stop "$d11_unfold_right_bad_predicate" Type 'D3:110 COND expects exact D1:1 / D1:0'
sha256sum lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-nonpredicate-stop-must-error.lisp \
  tests/fixtures/d11-unfold-right-nonpredicate-stop-must-error.lisp > "$evidence/d11-unfold-type-inputs.sha256"

# D11 UNFOLD: кінцевий хвіст має бути правильним D3-списком.
d11_unfold_bad_terminal_left_atom="$evidence/d11-unfold-terminal-left-atom.lisp"
d11_unfold_bad_terminal_left_dotted="$evidence/d11-unfold-terminal-left-dotted.lisp"
d11_unfold_bad_terminal_right_atom="$evidence/d11-unfold-terminal-right-atom.lisp"
d11_unfold_bad_terminal_right_dotted="$evidence/d11-unfold-terminal-right-dotted.lisp"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-terminal-left-atom-must-error.lisp > "$d11_unfold_bad_terminal_left_atom"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-terminal-left-dotted-must-error.lisp > "$d11_unfold_bad_terminal_left_dotted"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-terminal-right-atom-must-error.lisp > "$d11_unfold_bad_terminal_right_atom"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-terminal-right-dotted-must-error.lisp > "$d11_unfold_bad_terminal_right_dotted"
run_case run_type_rejection d11-unfold-terminal-left-atom "$d11_unfold_bad_terminal_left_atom" 'car expects a non-empty list'
run_case run_type_rejection d11-unfold-terminal-left-dotted "$d11_unfold_bad_terminal_left_dotted" 'car expects a non-empty list'
run_case run_type_rejection d11-unfold-terminal-right-atom "$d11_unfold_bad_terminal_right_atom" 'car expects a non-empty list'
run_case run_type_rejection d11-unfold-terminal-right-dotted "$d11_unfold_bad_terminal_right_dotted" 'car expects a non-empty list'
# D11: підтвердження D3 хвоста має випереджати отруйний callback.
d11_unfold_priority_atom="$evidence/d11-unfold-right-priority-atom-complete.lisp"
d11_unfold_priority_deep="$evidence/d11-unfold-right-priority-deep-complete.lisp"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-right-priority-atomic-tail-must-error.lisp > "$d11_unfold_priority_atom"
cat -- lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-right-priority-deep-tail-must-error.lisp > "$d11_unfold_priority_deep"
run_case run_type_rejection d11-unfold-right-priority-atom "$d11_unfold_priority_atom" 'car expects a non-empty list'
run_case run_type_rejection d11-unfold-right-priority-deep "$d11_unfold_priority_deep" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-unfold.lisp tests/fixtures/d11-unfold-terminal-*.lisp \
  tests/fixtures/d11-unfold-right-priority-*-tail-must-error.lisp > "$evidence/d11-unfold-terminal-inputs.sha256"


# Д11: повна композиція GROUP-BY → FREQUENCIES, з несуміжними ключами.
# Міняємо тільки SENS law/mutant, а не координати або хостову семантику.
d11_freq_key_positive="$evidence/d11-frequencies-key-order-positive-complete.lisp"
d11_freq_key_mutant="$evidence/d11-frequencies-key-order-mutant-complete.lisp"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-frequencies-key-order-law.lisp > "$d11_freq_key_positive"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-frequencies-key-order-mutant.lisp > "$d11_freq_key_mutant"
run_case run_law d11-frequencies-key-order-positive "$d11_freq_key_positive" 1 core4
run_case run_law d11-frequencies-key-order-mutant "$d11_freq_key_mutant" 0 core4
sha256sum lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp \
  tests/semantic/d11-frequencies-key-order-law.lisp tests/semantic/d11-frequencies-key-order-mutant.lisp > "$evidence/d11-frequencies-key-order-inputs.sha256"
# Д11 GROUP-BY: позитив, мутант, пріоритет структури D3 над ключем.
d11_gb_law="$evidence/d11-gb-spine-law.lisp"
d11_gb_mut="$evidence/d11-gb-spine-mutant.lisp"
d11_gb_early="$evidence/d11-gb-spine-early.lisp"
d11_gb_late="$evidence/d11-gb-spine-late.lisp"
cat -- lib/d11-clojure-group-by.lisp tests/semantic/d11-group-by-spine-priority-law.lisp > "$d11_gb_law"
cat -- lib/d11-clojure-group-by.lisp tests/semantic/d11-group-by-spine-priority-mutant.lisp > "$d11_gb_mut"
cat -- lib/d11-clojure-group-by.lisp tests/semantic/d11-group-by-spine-priority-early-negative.lisp > "$d11_gb_early"
cat -- lib/d11-clojure-group-by.lisp tests/semantic/d11-group-by-spine-priority-late-negative.lisp > "$d11_gb_late"
run_case run_law d11-group-by-spine-priority-law "$d11_gb_law" 1 core4
run_case run_law d11-group-by-spine-priority-mutant "$d11_gb_mut" 0 core4
run_case run_error_rejection d11-group-by-spine-priority-early "$d11_gb_early" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-group-by-spine-priority-late "$d11_gb_late" Type 'car expects a non-empty list' core4
sha256sum lib/d11-clojure-group-by.lisp \
  tests/semantic/d11-group-by-spine-priority-law.lisp \
  tests/semantic/d11-group-by-spine-priority-mutant.lisp \
  tests/semantic/d11-group-by-spine-priority-early-negative.lisp \
  tests/semantic/d11-group-by-spine-priority-late-negative.lisp > "$evidence/d11-group-by-spine-priority.sha256"
# Д11 GROUP-BY: чотири незалежні фізичні негативні свідки D3 Type.
# Кожен джерельний SENS-файл отримує ті ж DEFINE, що й позитивний закон.
# Жодне D7 текстове ім'я не підміняє неправильний D1-хвіст списку.
for variant in atom-input improper-tail remove-improper-tail select-improper-tail; do
  fixture="tests/fixtures/d11-group-by-${variant}-must-error.lisp"
  complete="$evidence/d11-group-by-${variant}-complete.lisp"
  cat -- lib/d11-clojure-group-by.lisp "$fixture" > "$complete"
  run_case run_error_rejection "d11-group-by-${variant}" "$complete" Type 'car expects a non-empty list' core4
done
sha256sum lib/d11-clojure-group-by.lisp \
  tests/fixtures/d11-group-by-*-must-error.lisp > "$evidence/d11-group-by-type-inputs.sha256"
# Д3/Д4: APPEND-GENERAL завершує тільки точне (), а не D1:ні.
# Всі три докази йдуть через SENS → Zig/T5M → SENS.
d4_append_positive="$evidence/d4-append-general-proper-complete.lisp"
d4_append_atom="$evidence/d4-append-general-atomic-left-complete.lisp"
d4_append_tail="$evidence/d4-append-general-improper-tail-complete.lisp"
cat -- lib/list-append-general.lisp tests/semantic/d4-append-general-proper-law.lisp > "$d4_append_positive"
cat -- lib/list-append-general.lisp tests/semantic/d4-append-general-atomic-left-negative.lisp > "$d4_append_atom"
cat -- lib/list-append-general.lisp tests/semantic/d4-append-general-improper-tail-negative.lisp > "$d4_append_tail"
run_case run_law d4-append-general-proper "$d4_append_positive" 1 core4
d4_append_mutant="$evidence/d4-append-general-proper-mutant-complete.lisp"
cat -- lib/list-append-general.lisp tests/semantic/d4-append-general-proper-mutant.lisp > "$d4_append_mutant"
run_case run_law d4-append-general-proper-mutant "$d4_append_mutant" 0 core4
run_case run_error_rejection d4-append-general-atomic-left "$d4_append_atom" Type 'car expects a non-empty list' core4
run_case run_error_rejection d4-append-general-improper-tail "$d4_append_tail" Type 'car expects a non-empty list' core4
d4_append_right_atom="$evidence/d4-append-general-atomic-right-complete.lisp"
d4_append_right_tail="$evidence/d4-append-general-improper-right-complete.lisp"
cat -- lib/list-append-general.lisp tests/semantic/d4-append-general-atomic-right-negative.lisp > "$d4_append_right_atom"
cat -- lib/list-append-general.lisp tests/semantic/d4-append-general-improper-right-negative.lisp > "$d4_append_right_tail"
run_case run_error_rejection d4-append-general-atomic-right "$d4_append_right_atom" Type 'car expects a non-empty list' core4
run_case run_error_rejection d4-append-general-improper-right "$d4_append_right_tail" Type 'car expects a non-empty list' core4
sha256sum lib/list-append-general.lisp tests/semantic/d4-append-general-proper-law.lisp \
  tests/semantic/d4-append-general-proper-mutant.lisp \
  tests/semantic/d4-append-general-atomic-left-negative.lisp \
  tests/semantic/d4-append-general-improper-tail-negative.lisp \
  tests/semantic/d4-append-general-atomic-right-negative.lisp tests/semantic/d4-append-general-improper-right-negative.lisp > "$evidence/d4-append-general-inputs.sha256"

# Д11 SRFI-1 LSET-DIFF+INTERSECTION: статично ідентифіковані фізичні джерела.
# Rust ownership guard пов'язує лише ЯВНИЙ SENS шлях у cat із run_case;
# приховане динамічне ім'я не є доказом реєстрації нового закону.
d11_lset_positive="$evidence/d11-lset-diff-intersection-law-complete.lisp"
d11_lset_mutant="$evidence/d11-lset-diff-intersection-mutant-complete.lisp"
d11_lset_bad_left="$evidence/d11-lset-diff-intersection-improper-left-complete.lisp"
d11_lset_bad_right="$evidence/d11-lset-diff-intersection-improper-right-complete.lisp"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-diff-intersection-law.lisp > "$d11_lset_positive"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-diff-intersection-mutant.lisp > "$d11_lset_mutant"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-diff-intersection-improper-left-negative.lisp > "$d11_lset_bad_left"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-diff-intersection-improper-right-negative.lisp > "$d11_lset_bad_right"
run_case run_law d11-lset-diff-intersection-law "$d11_lset_positive" 1 core4
run_case run_law d11-lset-diff-intersection-mutant "$d11_lset_mutant" 0 core4
run_case run_error_rejection d11-lset-diff-intersection-improper-left "$d11_lset_bad_left" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-lset-diff-intersection-improper-right "$d11_lset_bad_right" Type 'car expects a non-empty list' core4
sha256sum lib/d11-srfi1-lset-diff-intersection.lisp \
  tests/semantic/d11-srfi1-lset-diff-intersection-law.lisp \
  tests/semantic/d11-srfi1-lset-diff-intersection-mutant.lisp \
  tests/semantic/d11-srfi1-lset-diff-intersection-improper-left-negative.lisp \
  tests/semantic/d11-srfi1-lset-diff-intersection-improper-right-negative.lisp > "$evidence/d11-lset-diff-intersection-inputs.sha256"
# Д11 LSET-XOR: три справжні негативні виклики SENS із тим самим DEFINE.
# Лівий/правий атом D1 замість D3 () → CAR Type, компаратор D3 → COND Type.
d11_xor_bad_left="$evidence/d11-lset-xor-improper-left-complete.lisp"
d11_xor_bad_right="$evidence/d11-lset-xor-improper-right-complete.lisp"
d11_xor_bad_comparator="$evidence/d11-lset-xor-nonpredicate-complete.lisp"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-xor-improper-left-negative.lisp > "$d11_xor_bad_left"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-xor-improper-right-negative.lisp > "$d11_xor_bad_right"
cat -- lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-xor-nonpredicate-negative.lisp > "$d11_xor_bad_comparator"
run_case run_error_rejection d11-lset-xor-improper-left "$d11_xor_bad_left" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-lset-xor-improper-right "$d11_xor_bad_right" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-lset-xor-nonpredicate "$d11_xor_bad_comparator" Type 'D3:110 COND expects exact D1:1 / D1:0' core4
sha256sum lib/d11-srfi1-lset-diff-intersection.lisp tests/semantic/d11-srfi1-lset-xor-improper-left-negative.lisp tests/semantic/d11-srfi1-lset-xor-improper-right-negative.lisp tests/semantic/d11-srfi1-lset-xor-nonpredicate-negative.lisp > "$evidence/d11-lset-xor-negative-inputs.sha256"



# Д11 FREQUENCIES: окремий позитивний закон і мутант у SENS.
# Нормативна проєкція: не числа D24, а правильний список унарних "о".
# Всі DEFINE — канонічна Lisp-бібліотека, а фізичний шлях лише Zig/T5M.
d11_freq_positive="$evidence/d11-frequencies-unary-positive-complete.lisp"
d11_freq_mutant="$evidence/d11-frequencies-unary-mutant-complete.lisp"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-clojure-frequencies-unary-law.lisp > "$d11_freq_positive"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-clojure-frequencies-unary-mutant.lisp > "$d11_freq_mutant"
run_case run_law d11-frequencies-unary-positive "$d11_freq_positive" 1
run_case run_law d11-frequencies-unary-mutant "$d11_freq_mutant" 0
sha256sum lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp \
  tests/semantic/d11-clojure-frequencies-unary-law.lisp \
  tests/semantic/d11-clojure-frequencies-unary-mutant.lisp > "$evidence/d11-frequencies-unary-inputs.sha256"

# Д11 FREQUENCIES: точна пара (ключ елементи). У всіх чотирьох
# незалежних фізичних доказах використовуємо ті самі чинні DEFINE SENS.
d11_exact_group_positive="$evidence/d11-exact-group-pair-positive-complete.lisp"
d11_exact_group_mutant="$evidence/d11-exact-group-pair-mutant-complete.lisp"
d11_exact_group_extra="$evidence/d11-exact-group-pair-extra-type-complete.lisp"
d11_exact_group_missing="$evidence/d11-exact-group-pair-missing-type-complete.lisp"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/fixtures/d11-frequencies-exact-group-pair-law.lisp > "$d11_exact_group_positive"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/fixtures/d11-frequencies-exact-group-pair-mutant.lisp > "$d11_exact_group_mutant"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/fixtures/d11-frequencies-extra-group-field-negative.lisp > "$d11_exact_group_extra"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/fixtures/d11-frequencies-missing-group-field-negative.lisp > "$d11_exact_group_missing"
run_case run_law d11-exact-group-pair-positive "$d11_exact_group_positive" 1
run_case run_law d11-exact-group-pair-mutant "$d11_exact_group_mutant" 0
run_case run_type_rejection d11-exact-group-pair-extra-type "$d11_exact_group_extra" 'car expects a non-empty list'
run_case run_type_rejection d11-exact-group-pair-missing-type "$d11_exact_group_missing" 'car expects a non-empty list'
sha256sum lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp \
  tests/fixtures/d11-frequencies-exact-group-pair-law.lisp \
  tests/fixtures/d11-frequencies-exact-group-pair-mutant.lisp \
  tests/fixtures/d11-frequencies-extra-group-field-negative.lisp \
  tests/fixtures/d11-frequencies-missing-group-field-negative.lisp > "$evidence/d11-exact-group-pair-inputs.sha256"

# Д11: SENS-бібліотечна залежність FREQUENCIES від GROUP-BY.
# Маршрут не тлумачить закони: true/false і Type встановлює тільки SENS.
d11_freq_outer_positive="$evidence/d11-frequencies-outer-preflight-positive-complete.lisp"
d11_freq_outer_mutant="$evidence/d11-frequencies-outer-preflight-mutant-complete.lisp"
d11_freq_outer_bad="$evidence/d11-frequencies-outer-preflight-bad-complete.lisp"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-frequencies-outer-preflight-d1-law.lisp > "$d11_freq_outer_positive"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-frequencies-outer-preflight-d1-mutant.lisp > "$d11_freq_outer_mutant"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-frequencies-outer-before-inner-type-negative.lisp > "$d11_freq_outer_bad"
run_case run_law d11-frequencies-outer-preflight-d1-positive "$d11_freq_outer_positive" 1 core4
run_case run_law d11-frequencies-outer-preflight-d1-mutant "$d11_freq_outer_mutant" 0 core4
run_case run_error_rejection d11-frequencies-outer-before-inner-type "$d11_freq_outer_bad" Type 'car expects a non-empty list' core4
sha256sum lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp \
  tests/semantic/d11-frequencies-outer-preflight-d1-law.lisp \
  tests/semantic/d11-frequencies-outer-preflight-d1-mutant.lisp \
  tests/semantic/d11-frequencies-outer-before-inner-type-negative.lisp > "$evidence/d11-frequencies-outer-preflight-inputs.sha256"

# Д11 унарні частоти: негативні SENS-свідки завершення правильних списків.
# Усі визначення — в Lisp/SENS, Zig лише транспортує T5M.
d11_freq_bad_count="$evidence/d11-frequencies-bad-count.lisp"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-clojure-frequencies-improper-count-negative.lisp > "$d11_freq_bad_count"
# Рекурсивний виклик одержує (решта елементи) ще до входу до нового COND:
# неправильний D1 хвіст відхиляє саме D3 РЕШТА (CDR), не ПЕРШЕ (CAR).
run_case run_type_rejection d11-frequencies-improper-count-type "$d11_freq_bad_count" 'cdr expects a non-empty list'
d11_freq_bad_groups="$evidence/d11-frequencies-bad-groups.lisp"
cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-clojure-frequencies-improper-groups-negative.lisp > "$d11_freq_bad_groups"
run_case run_type_rejection d11-frequencies-improper-groups-type "$d11_freq_bad_groups" 'car expects a non-empty list'
sha256sum lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp tests/semantic/d11-clojure-frequencies-improper-count-negative.lisp tests/semantic/d11-clojure-frequencies-improper-groups-negative.lisp > "$evidence/d11-frequencies-improper-inputs.sha256"
# Залежний свідок Д11 FIND-TAIL має виконуватись із бібліотекою, а не окремо.
# Прямий Lisp, Zig/T5M, парне та фізичне SENS виконують тотожний пакет.
d11_find_tail_bundle="$evidence/d11-srfi1-find-tail-complete.lisp"
cat -- lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-laws.lisp > "$d11_find_tail_bundle"
run_case run_law d11-srfi1-find-tail-physical "$d11_find_tail_bundle" 1
# Д11 FIND-TAIL: незалежний негативний D1-мутант, не злитий з позитивом.
d11_find_tail_mutant="$evidence/d11-srfi1-find-tail-mutant-complete.lisp"
cat -- lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-mutant.lisp > "$d11_find_tail_mutant"
run_case run_law d11-srfi1-find-tail-mutant "$d11_find_tail_mutant" 0

# Сувора границя SRFI-1: неправильний D1-хвіст не можна приймати за NIL.
# Прямий SENS, Zig T5M і фізичний SENS мусять відхилити тим самим Type.
d11_find_tail_bad="$evidence/d11-srfi1-find-tail-improper-complete.lisp"
cat -- lib/d11-srfi1-find-tail.lisp tests/semantic/d11-srfi1-find-tail-improper-tail-negative.lisp > "$d11_find_tail_bad"
run_case run_type_rejection d11-find-tail-improper-d1-type-negative "$d11_find_tail_bad" 'car expects a non-empty list'
d11_find_tail_atomic_root="$evidence/d11-find-tail-atomic-root-complete.lisp"
cat -- lib/d11-srfi1-find-tail.lisp tests/fixtures/d11-find-tail-atomic-root-negative.lisp > "$d11_find_tail_atomic_root"
run_case run_type_rejection d11-find-tail-atomic-root-type "$d11_find_tail_atomic_root" 'car expects a non-empty list'
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
# D5:01000/01001 — мовні закони перевіряються SENS; фізичний D12 маршрут
# окремо доводить точну ширину після справжнього Zig/T5M round-trip.
run_case run_law d5-d12-numberp-ratio tests/semantic/d5-d12-numberp-law.lisp 1
run_case run_law d5-d12-zerop-computed-zero tests/semantic/d5-d12-zerop-law.lisp 1
run_case run_law d5-numberp-text-is-not-number tests/semantic/d5-numberp-nonnumber-law.lisp 0
sha256sum tests/semantic/d5-d12-numberp-law.lisp tests/semantic/d5-d12-zerop-law.lisp tests/semantic/d5-numberp-nonnumber-law.lisp > "$evidence/d5-d12-number-predicate-inputs.sha256"
# Д6:111110 INTEGERP і Д6:111111 RATIONALP: тільки SENS семантика чисел.
# Цей загальний маршрут перевіряє предикати; фізичну D12-ширину доводить
# окремий парний D12/T5M тест, а не розмір літерала у цих формах.
run_case run_law d6-exact-integer-rational tests/semantic/d6-d12-integer-rational-law.lisp 1 core4
run_case run_law d6-ratio-normalizes-integer tests/semantic/d6-d12-ratio-normalizes-integer-law.lisp 1 core4
run_case run_law d6-rationalp-text-mutant tests/semantic/d6-rationalp-text-negative.lisp 0 core4
run_case run_law d6-rationalp-list-mutant tests/semantic/d6-rationalp-list-negative.lisp 0 core4
run_case run_law d6-integerp-fraction-mutant tests/semantic/d6-integerp-ratio-mutant.lisp 0 core4
run_case run_law d6-integerp-text-mutant tests/semantic/d6-integerp-text-negative.lisp 0 core4
sha256sum lib/core4.lisp lib/core4-parts/core4-d6b.lisp \
  tests/semantic/d6-d12-integer-rational-law.lisp \
  tests/semantic/d6-d12-ratio-normalizes-integer-law.lisp \
  tests/semantic/d6-rationalp-text-negative.lisp \
  tests/semantic/d6-rationalp-list-negative.lisp \
  tests/semantic/d6-integerp-ratio-mutant.lisp \
  tests/semantic/d6-integerp-text-negative.lisp > "$evidence/d6-exact-number-predicate-inputs.sha256"

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

# Д11: відбір над канонічними D1/D3; позитив і мутант — SENS.
# Код і закон беруться з чинного lib/ та tests/semantic/, не з shell.
d11_selection_d1_law="$evidence/d11-family-selection-d1-structural-positive.lisp"
d11_selection_d1_mutant="$evidence/d11-family-selection-d1-structural-mutant.lisp"
cat -- lib/d11-family-selection.lisp tests/semantic/d11-family-selection-d1-structural-law.lisp > "$d11_selection_d1_law"
cat -- lib/d11-family-selection.lisp tests/semantic/d11-family-selection-d1-structural-mutant.lisp > "$d11_selection_d1_mutant"
run_case run_law d11-family-selection-d1-structural-positive "$d11_selection_d1_law" 1
run_case run_law d11-family-selection-d1-structural-mutant "$d11_selection_d1_mutant" 0
sha256sum lib/d11-family-selection.lisp \
  tests/semantic/d11-family-selection-d1-structural-law.lisp \
  tests/semantic/d11-family-selection-d1-structural-mutant.lisp > "$evidence/d11-family-selection-d1-inputs.sha256"

# D11 DROP-WHILE — суфікс чинного SPAN із повною перевіркою D3 до предиката.
d11_drop_while_law="$evidence/d11-drop-while-first-class-law-complete.lisp"
d11_drop_while_mutant="$evidence/d11-drop-while-first-class-mutant-complete.lisp"
d11_drop_while_root="$evidence/d11-drop-while-first-class-root-complete.lisp"
d11_drop_while_precedence="$evidence/d11-drop-while-first-class-precedence-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp tests/semantic/d11-drop-while-first-class-law.lisp > "$d11_drop_while_law"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp tests/semantic/d11-drop-while-first-class-mutant.lisp > "$d11_drop_while_mutant"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp tests/semantic/d11-drop-while-first-class-atomic-root-negative.lisp > "$d11_drop_while_root"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp tests/semantic/d11-drop-while-first-class-predicate-precedence-negative.lisp > "$d11_drop_while_precedence"
run_case run_law d11-drop-while-first-class-positive "$d11_drop_while_law" 1
run_case run_law d11-drop-while-first-class-mutant "$d11_drop_while_mutant" 0
run_case run_type_rejection d11-drop-while-first-class-atomic-root "$d11_drop_while_root" 'car expects a non-empty list'
run_case run_type_rejection d11-drop-while-first-class-predicate-precedence "$d11_drop_while_precedence" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp tests/semantic/d11-drop-while-first-class-*.lisp > "$evidence/d11-drop-while-first-class-inputs.sha256"

# D11 TAKE-WHILE: композиція єдиного чинного SENS SPAN, без нового opcode.
# Прямий і обидва фізичні шляхи обчислюють позитив, мутант та D3 Type.
d11_take_while_positive="$evidence/d11-take-while-first-class-positive-complete.lisp"
d11_take_while_mutant="$evidence/d11-take-while-first-class-mutant-complete.lisp"
d11_take_while_bad="$evidence/d11-take-while-first-class-improper-tail-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp \
  tests/semantic/d11-take-while-first-class-law.lisp > "$d11_take_while_positive"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp \
  tests/semantic/d11-take-while-first-class-mutant.lisp > "$d11_take_while_mutant"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp \
  tests/semantic/d11-take-while-first-class-improper-tail-negative.lisp > "$d11_take_while_bad"
run_case run_law d11-take-while-first-class-positive "$d11_take_while_positive" 1
run_case run_law d11-take-while-first-class-mutant "$d11_take_while_mutant" 0
run_case run_type_rejection d11-take-while-first-class-improper-tail "$d11_take_while_bad" 'car expects a non-empty list'
d11_take_while_precedence="$evidence/d11-take-while-precedence-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp tests/semantic/d11-take-while-first-class-predicate-precedence-negative.lisp > "$d11_take_while_precedence"
run_case run_type_rejection d11-take-while-first-class-type-precedence "$d11_take_while_precedence" 'car expects a non-empty list'
d11_take_while_root="$evidence/d11-take-while-first-class-atomic-root-complete.lisp"
d11_take_while_late="$evidence/d11-take-while-first-class-late-improper-complete.lisp"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp \
  tests/semantic/d11-take-while-first-class-atomic-root-negative.lisp > "$d11_take_while_root"
cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp \
  tests/semantic/d11-take-while-first-class-late-improper-negative.lisp > "$d11_take_while_late"
run_case run_type_rejection d11-take-while-first-class-atomic-root "$d11_take_while_root" 'car expects a non-empty list'
run_case run_type_rejection d11-take-while-first-class-late-improper "$d11_take_while_late" 'car expects a non-empty list'


sha256sum lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp \
  tests/semantic/d11-take-while-first-class-*.lisp > "$evidence/d11-take-while-first-class-inputs.sha256"

# Д11 SRFI-1 lset-adjoin: перевірка лише SENS через фізичний Zig/T5M.
# Негативні свідки мусять дати D3 ПЕРШЕ Type, а не мовчазний результат.
d11_adjoin_law_bundle="$evidence/d11-srfi1-adjoin-law-complete.lisp"
d11_adjoin_mutant_bundle="$evidence/d11-srfi1-adjoin-mutant-complete.lisp"
d11_adjoin_bad_empty_bundle="$evidence/d11-srfi1-adjoin-bad-empty-complete.lisp"
d11_adjoin_bad_duplicate_bundle="$evidence/d11-srfi1-adjoin-bad-duplicate-complete.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-adjoin-proper-law.lisp > "$d11_adjoin_law_bundle"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-adjoin-proper-mutant.lisp > "$d11_adjoin_mutant_bundle"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-adjoin-improper-empty-negative.lisp > "$d11_adjoin_bad_empty_bundle"
cat -- lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-adjoin-improper-duplicate-negative.lisp > "$d11_adjoin_bad_duplicate_bundle"
run_case run_law d11-srfi1-adjoin-proper-positive "$d11_adjoin_law_bundle" 1
run_case run_law d11-srfi1-adjoin-proper-mutant "$d11_adjoin_mutant_bundle" 0
run_case run_type_rejection d11-srfi1-adjoin-improper-empty "$d11_adjoin_bad_empty_bundle" 'car expects a non-empty list'
run_case run_type_rejection d11-srfi1-adjoin-improper-duplicate "$d11_adjoin_bad_duplicate_bundle" 'car expects a non-empty list'
# Д11 ADDJOIN: кандидатний D1:ні не є структурним завершенням D3:().
d11_adjoin_atomic_candidates="$evidence/d11-srfi1-adjoin-atomic-candidates.lisp"
d11_adjoin_improper_candidates_tail="$evidence/d11-srfi1-adjoin-improper-candidates-tail.lisp"
cat -- lib/d11-srfi1-set-relations.lisp tests/fixtures/d11-srfi1-adjoin-atomic-candidates-negative.lisp > "$d11_adjoin_atomic_candidates"
cat -- lib/d11-srfi1-set-relations.lisp tests/fixtures/d11-srfi1-adjoin-improper-candidates-tail-negative.lisp > "$d11_adjoin_improper_candidates_tail"
run_case run_type_rejection d11-srfi1-adjoin-atomic-candidates "$d11_adjoin_atomic_candidates" 'car expects a non-empty list'
run_case run_type_rejection d11-srfi1-adjoin-improper-candidates-tail "$d11_adjoin_improper_candidates_tail" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-set-relations.lisp tests/semantic/d11-srfi1-adjoin-*.lisp > "$evidence/d11-srfi1-adjoin-inputs.sha256"

# Д11 reductions / pair-fold: реальний SENS позитив, мутант і Type-відмови.
# Файли залежать від бібліотечних DEFINE; окремий запуск не є атестацією.
d11_scan_fold_law_bundle="$evidence/d11-scan-fold-d3-positive.lisp"
d11_scan_fold_mutant_bundle="$evidence/d11-scan-fold-d3-mutant.lisp"
d11_scan_fold_bad_scan="$evidence/d11-scan-fold-d3-scan-bad.lisp"
d11_scan_fold_bad_left="$evidence/d11-scan-fold-d3-left-bad.lisp"
d11_scan_fold_bad_right="$evidence/d11-scan-fold-d3-right-bad.lisp"
cat -- lib/d11-historical-scan-fold.lisp tests/semantic/d11-scan-fold-d3-tail-law.lisp > "$d11_scan_fold_law_bundle"
cat -- lib/d11-historical-scan-fold.lisp tests/semantic/d11-scan-fold-d3-tail-mutant.lisp > "$d11_scan_fold_mutant_bundle"
cat -- lib/d11-historical-scan-fold.lisp tests/semantic/d11-scan-fold-d3-tail-scan-improper-negative.lisp > "$d11_scan_fold_bad_scan"
cat -- lib/d11-historical-scan-fold.lisp tests/semantic/d11-scan-fold-d3-tail-left-improper-negative.lisp > "$d11_scan_fold_bad_left"
cat -- lib/d11-historical-scan-fold.lisp tests/semantic/d11-scan-fold-d3-tail-right-improper-negative.lisp > "$d11_scan_fold_bad_right"
run_case run_law d11-scan-fold-d3-positive "$d11_scan_fold_law_bundle" 1
run_case run_law d11-scan-fold-d3-mutant "$d11_scan_fold_mutant_bundle" 0
run_case run_type_rejection d11-scan-fold-d3-scan-bad "$d11_scan_fold_bad_scan" 'car expects a non-empty list'
run_case run_type_rejection d11-scan-fold-d3-left-bad "$d11_scan_fold_bad_left" 'car expects a non-empty list'
run_case run_type_rejection d11-scan-fold-d3-right-bad "$d11_scan_fold_bad_right" 'car expects a non-empty list'
sha256sum lib/d11-historical-scan-fold.lisp tests/semantic/d11-scan-fold-d3-tail-*.lisp > "$evidence/d11-scan-fold-d3-inputs.sha256"

d11_span_bundle="$evidence/d11-srfi1-span-break-complete.lisp"
d11_span_mutant_bundle="$evidence/d11-srfi1-span-break-mutant-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-laws.lisp > "$d11_span_bundle"
cat -- lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-mutant.lisp > "$d11_span_mutant_bundle"
sha256sum lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-break-laws.lisp \
  tests/semantic/d11-srfi1-span-break-mutant.lisp > "$evidence/d11-srfi1-inputs.sha256"
run_case run_law d11-srfi1-span-break-physical "$d11_span_bundle" 1
run_case run_law d11-srfi1-span-break-mutant "$d11_span_mutant_bundle" 0
# Д11: SPAN/BREAK не повинні пропускати атомний D1-хвіст суфікса.
d11_span_improper="$evidence/d11-srfi1-span-improper-suffix.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-improper-suffix-negative.lisp > "$d11_span_improper"
run_case run_type_rejection d11-srfi1-span-improper-suffix-type "$d11_span_improper" 'car expects a non-empty list'
d11_break_improper="$evidence/d11-srfi1-break-improper-suffix.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-break-improper-suffix-negative.lisp > "$d11_break_improper"
run_case run_type_rejection d11-srfi1-break-improper-suffix-type "$d11_break_improper" 'car expects a non-empty list'
# Д11 TAKE/DROP-UNTIL: повний D3-хвіст перевіряється ДО раннього D1-збігу
# та ДО помилкового першокласного предиката. Тільки справжня SENS Type.
d11_until_early_bad="$evidence/d11-take-until-early-hit-improper-complete.lisp"
d11_until_priority_bad="$evidence/d11-drop-until-structure-before-predicate-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/fixtures/d11-take-until-early-hit-improper-negative.lisp > "$d11_until_early_bad"
cat -- lib/d11-srfi1-span-break.lisp tests/fixtures/d11-drop-until-structure-before-predicate-negative.lisp > "$d11_until_priority_bad"
run_case run_type_rejection d11-take-until-early-hit-spine "$d11_until_early_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-drop-until-before-predicate "$d11_until_priority_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-span-break.lisp \
  tests/fixtures/d11-take-until-early-hit-improper-negative.lisp \
  tests/fixtures/d11-drop-until-structure-before-predicate-negative.lisp \
  > "$evidence/d11-until-type-priority-inputs.sha256"

# D11 SPAN/BREAK: CAR неправильного D3-хвоста мусить передувати
# іншій CDR Type усередині першокласного SENS-предиката.
d11_span_precedence_bad="$evidence/d11-span-structure-before-predicate-complete.lisp"
d11_break_precedence_bad="$evidence/d11-break-structure-before-predicate-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp tests/fixtures/d11-span-improper-before-predicate-negative.lisp > "$d11_span_precedence_bad"
cat -- lib/d11-srfi1-span-break.lisp tests/fixtures/d11-break-improper-before-predicate-negative.lisp > "$d11_break_precedence_bad"
run_case run_type_rejection d11-span-structure-before-predicate-type "$d11_span_precedence_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-break-structure-before-predicate-type "$d11_break_precedence_bad" 'car expects a non-empty list'
sha256sum lib/d11-srfi1-span-break.lisp tests/fixtures/d11-span-improper-before-predicate-negative.lisp tests/fixtures/d11-break-improper-before-predicate-negative.lisp > "$evidence/d11-span-break-precedence-inputs.sha256"
sha256sum lib/d11-srfi1-span-break.lisp tests/semantic/d11-srfi1-span-improper-suffix-negative.lisp tests/semantic/d11-srfi1-break-improper-suffix-negative.lisp > "$evidence/d11-span-break-improper-inputs.sha256"

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
# Д11 відбір: кожний із трьох готових SENS-свідків відхиляє атом
# саме D3 Type через ПЕРШЕ. Domain-not-callable від (ні) вже заборонений.
d11_family_filter_bad="$evidence/d11-family-selection-filter-bad.lisp"
d11_family_partition_bad="$evidence/d11-family-selection-partition-bad.lisp"
d11_family_reject_bad="$evidence/d11-family-selection-reject-bad.lisp"
d11_family_filter_atomic_bad="$evidence/d11-family-selection-filter-atomic-root-bad.lisp"
d11_family_filter_false_atomic_bad="$evidence/d11-family-selection-filter-false-atomic-root-bad.lisp"
d11_family_partition_atomic_bad="$evidence/d11-family-selection-partition-atomic-root-bad.lisp"
cat -- lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-filter-improper-tail-must-error.lisp > "$d11_family_filter_bad"
cat -- lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-partition-improper-tail-must-error.lisp > "$d11_family_partition_bad"
cat -- lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-reject-atom-must-error.lisp > "$d11_family_reject_bad"
cat -- lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-filter-atomic-root-must-error.lisp > "$d11_family_filter_atomic_bad"
cat -- lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-filter-atomic-false-root-must-error.lisp > "$d11_family_filter_false_atomic_bad"
cat -- lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-partition-atomic-root-must-error.lisp > "$d11_family_partition_atomic_bad"
run_case run_type_rejection d11-family-selection-filter-improper-tail-type "$d11_family_filter_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-family-selection-partition-improper-tail-type "$d11_family_partition_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-family-selection-reject-atom-type "$d11_family_reject_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-family-selection-filter-atomic-root-type "$d11_family_filter_atomic_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-family-selection-filter-false-atomic-root-type "$d11_family_filter_false_atomic_bad" 'car expects a non-empty list'
run_case run_type_rejection d11-family-selection-partition-atomic-root-type "$d11_family_partition_atomic_bad" 'car expects a non-empty list'
sha256sum lib/d11-family-selection.lisp tests/fixtures/d11-family-selection-*.lisp > "$evidence/d11-family-selection-type-inputs.sha256"
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
# Д11 DWIM: незалежний канонічний D3 закон і мутант.
# Явні шляхи дають Rust guard змогу підтвердити справжнє SENS-джерело.
d11_dwim_d3_proper="$evidence/d11-dwim-d3-proper-complete.lisp"
d11_dwim_d3_mutant="$evidence/d11-dwim-d3-mutant-complete.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/semantic/d11-interlisp-dwim-d3-proper-law.lisp > "$d11_dwim_d3_proper"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/semantic/d11-interlisp-dwim-d3-proper-mutant.lisp > "$d11_dwim_d3_mutant"
run_case run_law d11-interlisp-dwim-d3-proper "$d11_dwim_d3_proper" 1 core4
run_case run_law d11-interlisp-dwim-d3-mutant "$d11_dwim_d3_mutant" 0 core4
sha256sum lib/d11-interlisp-safe-analysis.lisp \
  tests/semantic/d11-interlisp-dwim-d3-proper-law.lisp \
  tests/semantic/d11-interlisp-dwim-d3-proper-mutant.lisp > "$evidence/d11-interlisp-dwim-d3-inputs.sha256"

# D11 DWIM: записи рівно з двох полів — SENS перевіряє ДО вибору кандидата.
d11_dwim_exact_context_positive="$evidence/d11-dwim-exact-context-positive.lisp"
d11_dwim_extra_field_bad="$evidence/d11-dwim-extra-field-bad.lisp"
d11_dwim_unrelated_extra_bad="$evidence/d11-dwim-unrelated-extra-bad.lisp"
d11_dwim_dotted_bad="$evidence/d11-dwim-dotted-record-bad.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-dwim-exact-context-positive.lisp > "$d11_dwim_exact_context_positive"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-dwim-extra-field-negative.lisp > "$d11_dwim_extra_field_bad"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-dwim-unrelated-extra-field-negative.lisp > "$d11_dwim_unrelated_extra_bad"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-dwim-dotted-record-negative.lisp > "$d11_dwim_dotted_bad"
run_case run_law d11-dwim-exact-context-positive "$d11_dwim_exact_context_positive" 1 core4
run_case run_error_rejection d11-dwim-extra-field-type "$d11_dwim_extra_field_bad" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-dwim-unrelated-extra-field-type "$d11_dwim_unrelated_extra_bad" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-dwim-dotted-record-type "$d11_dwim_dotted_bad" Type 'car expects a non-empty list' core4
# Masterscope: D3-форма перевіряється ПЕРЕД прямим збігом голови.
# D1:ні як неправильний хвіст мусить спричинити CAR Type, не D1:так.
d11_masterscope_bad_tail="$evidence/d11-masterscope-improper-root-tail-complete.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-improper-root-tail-negative.lisp > "$d11_masterscope_bad_tail"
run_case run_error_rejection d11-masterscope-improper-root-tail-type "$d11_masterscope_bad_tail" Type 'car expects a non-empty list' core4
# Вкладена D3-пара з пізнім D1-хвостом за раннім прямим збігом.
d11_masterscope_nested_bad="$evidence/d11-masterscope-improper-nested-tail-complete.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-improper-nested-tail-negative.lisp > "$d11_masterscope_nested_bad"
run_case run_error_rejection d11-masterscope-improper-nested-tail-type "$d11_masterscope_nested_bad" Type 'car expects a non-empty list' core4
# Дані під як-є є цитатою: навіть крапкова пара не є пошкодженим викликом.
d11_masterscope_quoted_datum="$evidence/d11-masterscope-quoted-improper-datum-complete.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-quoted-improper-datum-positive.lisp > "$d11_masterscope_quoted_datum"
run_case run_law d11-masterscope-quoted-improper-datum-positive "$d11_masterscope_quoted_datum" 1 core4
# Окрема D3-перевірка спискової голови до збігу в аргументах.
d11_masterscope_bad_head="$evidence/d11-masterscope-improper-call-head-complete.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-improper-call-head-negative.lisp > "$d11_masterscope_bad_head"
run_case run_error_rejection d11-masterscope-improper-call-head-type "$d11_masterscope_bad_head" Type 'car expects a non-empty list' core4
d11_masterscope_proper_head="$evidence/d11-masterscope-proper-call-head-complete.lisp"
cat -- lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-proper-call-head-positive.lisp > "$d11_masterscope_proper_head"
run_case run_law d11-masterscope-proper-call-head-positive "$d11_masterscope_proper_head" 1 core4
sha256sum lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-improper-call-head-negative.lisp tests/fixtures/d11-masterscope-proper-call-head-positive.lisp > "$evidence/d11-masterscope-call-head-inputs.sha256"
sha256sum lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-improper-nested-tail-negative.lisp tests/fixtures/d11-masterscope-quoted-improper-datum-positive.lisp > "$evidence/d11-masterscope-nested-form-inputs.sha256"
sha256sum lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-masterscope-improper-root-tail-negative.lisp > "$evidence/d11-masterscope-improper-root-tail-inputs.sha256"
sha256sum lib/d11-interlisp-safe-analysis.lisp tests/fixtures/d11-dwim-*.lisp > "$evidence/d11-dwim-exact-record-inputs.sha256"

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
# Компілятор D3/D5 · пошук авторитету: помилку даних не плутати з D3:().
# Точні SENS DEFINE беруться лише з чинного lib/compiler-nucleus.lisp.
compiler_authority_defs="$evidence/compiler-authority-exact-source-definitions.lisp"
: > "$compiler_authority_defs"
for name in знайти-авторитет-компілятора ядро-компілятора; do
  if ! awk -v target="(визначити $name" '
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
  ' lib/compiler-nucleus.lisp >> "$compiler_authority_defs"; then
    echo "::error::COMPILER_AUTHORITY_EXACT_SENS_DEFINITION_MISSING name=$name" >&2
    exit 2
  fi
done
test -s "$compiler_authority_defs" || { echo "::error::COMPILER_AUTHORITY_EMPTY_DEFINITIONS" >&2; exit 2; }
sha256sum lib/compiler-nucleus.lisp "$compiler_authority_defs" \
  tests/semantic/compiler-authority-proper-law.lisp \
  tests/semantic/compiler-authority-proper-mutant.lisp \
  tests/semantic/compiler-authority-d1-root-negative.lisp \
  tests/semantic/compiler-authority-improper-tail-negative.lisp \
  > "$evidence/compiler-authority-exact-inputs.sha256"
compiler_authority_positive="$evidence/compiler-authority-positive-complete.lisp"
compiler_authority_mutant="$evidence/compiler-authority-mutant-complete.lisp"
compiler_authority_root="$evidence/compiler-authority-root-complete.lisp"
compiler_authority_tail="$evidence/compiler-authority-tail-complete.lisp"
cat -- "$compiler_authority_defs" tests/semantic/compiler-authority-proper-law.lisp > "$compiler_authority_positive"
cat -- "$compiler_authority_defs" tests/semantic/compiler-authority-proper-mutant.lisp > "$compiler_authority_mutant"
cat -- "$compiler_authority_defs" tests/semantic/compiler-authority-d1-root-negative.lisp > "$compiler_authority_root"
cat -- "$compiler_authority_defs" tests/semantic/compiler-authority-improper-tail-negative.lisp > "$compiler_authority_tail"
run_case run_law compiler-authority-positive "$compiler_authority_positive" 1
run_case run_law compiler-authority-mutant "$compiler_authority_mutant" 0
run_case run_error_rejection compiler-authority-d1-root-type "$compiler_authority_root" Type 'car expects a non-empty list'
run_case run_error_rejection compiler-authority-improper-tail-type "$compiler_authority_tail" Type 'car expects a non-empty list'

# СЕНС · compiler APPEND: чинні DEFINE — єдине джерело семантики.
# Механічно витягаємо незмінні SENS-форми, не додаємо host-правил.
compiler_append_defs="$evidence/compiler-append-exact-source-definitions.lisp"
: > "$compiler_append_defs"
for name in істина-компілятора компілятор-приєднати; do
  if ! awk -v target="(визначити $name" '
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
  ' lib/compiler-nucleus.lisp >> "$compiler_append_defs"; then
    echo "::error::COMPILER_APPEND_EXACT_SENS_DEFINITION_MISSING name=$name" >&2
    exit 2
  fi
done
test -s "$compiler_append_defs" || { echo "::error::COMPILER_APPEND_EMPTY_SOURCE" >&2; exit 2; }
sha256sum lib/compiler-nucleus.lisp "$compiler_append_defs" \
  tests/semantic/compiler-append-proper-law.lisp \
  tests/semantic/compiler-append-proper-mutant.lisp \
  tests/semantic/compiler-append-d1-root-negative.lisp \
  tests/semantic/compiler-append-improper-tail-negative.lisp \
  > "$evidence/compiler-append-exact-inputs.sha256"
compiler_append_positive="$evidence/compiler-append-positive-complete.lisp"
compiler_append_mutant="$evidence/compiler-append-mutant-complete.lisp"
compiler_append_root="$evidence/compiler-append-d1-root-complete.lisp"
compiler_append_tail="$evidence/compiler-append-bad-tail-complete.lisp"
cat -- "$compiler_append_defs" tests/semantic/compiler-append-proper-law.lisp > "$compiler_append_positive"
cat -- "$compiler_append_defs" tests/semantic/compiler-append-proper-mutant.lisp > "$compiler_append_mutant"
cat -- "$compiler_append_defs" tests/semantic/compiler-append-d1-root-negative.lisp > "$compiler_append_root"
cat -- "$compiler_append_defs" tests/semantic/compiler-append-improper-tail-negative.lisp > "$compiler_append_tail"
run_case run_law compiler-append-positive "$compiler_append_positive" 1
run_case run_law compiler-append-mutant "$compiler_append_mutant" 0
run_case run_error_rejection compiler-append-d1-root-type "$compiler_append_root" Type 'car expects a non-empty list'
run_case run_error_rejection compiler-append-improper-tail-type "$compiler_append_tail" Type 'car expects a non-empty list'

# D5/D3 компіляторне обернення: беремо ТОЧНІ чинні DEFINE з SENS.
# Bash/AWK лише відділяє вже визначені форми; закон і Type — тільки SENS.
# Якщо форма відсутня, неоднозначна або не закінчується — fail-closed.
compiler_reverse_defs="$evidence/compiler-reverse-onto-exact-source-definitions.lisp"
: > "$compiler_reverse_defs"
for name in істина-компілятора компілятор-зворот-до; do
  if ! awk -v target="(визначити $name" '
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
  ' lib/compiler-nucleus.lisp >> "$compiler_reverse_defs"; then
    echo "::error::COMPILER_REVERSE_ONTO_EXACT_SENS_DEFINITION_MISSING name=$name" >&2
    exit 2
  fi
done
test -s "$compiler_reverse_defs" || { echo "::error::COMPILER_REVERSE_ONTO_EMPTY_SENS_DEFINITIONS" >&2; exit 2; }
sha256sum lib/compiler-nucleus.lisp "$compiler_reverse_defs" \
  tests/semantic/compiler-reverse-onto-proper-law.lisp \
  tests/semantic/compiler-reverse-onto-proper-mutant.lisp \
  tests/semantic/compiler-reverse-onto-improper-tail-negative.lisp \
  tests/semantic/compiler-reverse-onto-d1-root-negative.lisp \
  > "$evidence/compiler-reverse-onto-exact-inputs.sha256"

compiler_reverse_positive="$evidence/compiler-reverse-onto-positive-complete.lisp"
compiler_reverse_mutant="$evidence/compiler-reverse-onto-mutant-complete.lisp"
compiler_reverse_bad_tail="$evidence/compiler-reverse-onto-bad-tail-complete.lisp"
compiler_reverse_bad_root="$evidence/compiler-reverse-onto-bad-root-complete.lisp"
cat -- "$compiler_reverse_defs" tests/semantic/compiler-reverse-onto-proper-law.lisp > "$compiler_reverse_positive"
cat -- "$compiler_reverse_defs" tests/semantic/compiler-reverse-onto-proper-mutant.lisp > "$compiler_reverse_mutant"
cat -- "$compiler_reverse_defs" tests/semantic/compiler-reverse-onto-improper-tail-negative.lisp > "$compiler_reverse_bad_tail"
cat -- "$compiler_reverse_defs" tests/semantic/compiler-reverse-onto-d1-root-negative.lisp > "$compiler_reverse_bad_root"
run_case run_law compiler-reverse-onto-positive "$compiler_reverse_positive" 1
run_case run_law compiler-reverse-onto-order-mutant "$compiler_reverse_mutant" 0
run_case run_error_rejection compiler-reverse-onto-d1-root-type "$compiler_reverse_bad_root" Type 'car expects a non-empty list'
run_case run_error_rejection compiler-reverse-onto-improper-tail-type "$compiler_reverse_bad_tail" Type 'car expects a non-empty list'

# Д11 juxt: першокласні одномісні функції та контрприклад перевіряє SENS.
# Bash лише додає чинні DEFINE та проводить обидва свідки через Zig/T5M.
d11_juxt_law_bundle="$evidence/d11-clojure-juxt-positive-complete.lisp"
d11_juxt_mutant_bundle="$evidence/d11-clojure-juxt-mutant-complete.lisp"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-laws.lisp > "$d11_juxt_law_bundle"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-mutant.lisp > "$d11_juxt_mutant_bundle"
sha256sum lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-laws.lisp tests/semantic/d11-clojure-juxt-mutant.lisp > "$evidence/d11-clojure-juxt-inputs.sha256"
run_case run_law d11-clojure-juxt-positive "$d11_juxt_law_bundle" 1
run_case run_law d11-clojure-juxt-mutant "$d11_juxt_mutant_bundle" 0

# D11 JUХT: неправильний D1-хвіст має дати саме D3 CAR Type до
# сторонньої функції (вона дала б CDR) і вже в момент конструктора.
d11_juxt_bad_tail="$evidence/d11-clojure-juxt-poison-improper-tail-complete.lisp"
d11_juxt_bad_ctor="$evidence/d11-clojure-juxt-constructor-improper-tail-complete.lisp"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-poison-improper-tail-negative.lisp > "$d11_juxt_bad_tail"
cat -- lib/d11-clojure-juxt.lisp tests/semantic/d11-clojure-juxt-constructor-improper-tail-negative.lisp > "$d11_juxt_bad_ctor"
run_case run_error_rejection d11-clojure-juxt-poison-improper-tail "$d11_juxt_bad_tail" Type 'car expects a non-empty list'
run_case run_error_rejection d11-clojure-juxt-constructor-improper-tail "$d11_juxt_bad_ctor" Type 'car expects a non-empty list'
sha256sum tests/semantic/d11-clojure-juxt-poison-improper-tail-negative.lisp \
  tests/semantic/d11-clojure-juxt-constructor-improper-tail-negative.lisp > "$evidence/d11-clojure-juxt-negative-inputs.sha256"
# Д11 Clojure: два комплекти законів перенесено з Rust у справжній Lisp.
# Їхня залежність SRFI-1 SPAN завантажується перед DEFINE групування.
for suite in d11-clojure-partition-by d11-clojure-dedupe; do
  combined="$evidence/$suite-complete.lisp"
  cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp "tests/semantic/$suite-laws.lisp" > "$combined"
  run_case run_law "$suite-physical" "$combined" 1
done
# Д11 PARTITION-BY: singleton також зобов'язаний виконати функцію ключа.
d11_partition_singleton_law="$evidence/d11-clojure-partition-singleton-key-law-complete.lisp"
d11_partition_singleton_mutant="$evidence/d11-clojure-partition-singleton-key-mutant-complete.lisp"
d11_partition_singleton_bad="$evidence/d11-clojure-partition-singleton-key-error-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-singleton-key-law.lisp > "$d11_partition_singleton_law"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-singleton-key-mutant.lisp > "$d11_partition_singleton_mutant"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-singleton-key-error-negative.lisp > "$d11_partition_singleton_bad"
run_case run_law d11-clojure-partition-singleton-key-law "$d11_partition_singleton_law" 1
run_case run_law d11-clojure-partition-singleton-key-mutant "$d11_partition_singleton_mutant" 0
run_case run_error_rejection d11-clojure-partition-singleton-key-error "$d11_partition_singleton_bad" Type 'car expects a non-empty list'
sha256sum lib/d11-clojure-partition-by.lisp \
  tests/semantic/d11-clojure-partition-singleton-key-law.lisp \
  tests/semantic/d11-clojure-partition-singleton-key-mutant.lisp \
  tests/semantic/d11-clojure-partition-singleton-key-error-negative.lisp > "$evidence/d11-clojure-partition-singleton-key-inputs.sha256"

# Д11: атом D1:ні не є кінцем D3-списку. PARTITION використовує
# канонічний SPAN-валідатор перед викликом ключа, тому це D3 CAR Type.
d11_partition_bad_root="$evidence/d11-clojure-partition-improper-d1-tail-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-improper-d1-tail-negative.lisp > "$d11_partition_bad_root"
run_case run_type_rejection d11-clojure-partition-improper-d1-type-negative "$d11_partition_bad_root" 'car expects a non-empty list'
# DEDUPE має власний шлях, чинна точна D3 CDR Type-відмова незмінна.
d11_dedupe_bad_root="$evidence/d11-clojure-dedupe-improper-d1-tail-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-dedupe-improper-d1-tail-negative.lisp > "$d11_dedupe_bad_root"
run_case run_type_rejection d11-clojure-dedupe-improper-d1-type-negative "$d11_dedupe_bad_root" 'car expects a non-empty list'
d11_dedupe_bad_late="$evidence/d11-clojure-dedupe-late-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/fixtures/d11-clojure-dedupe-late-improper-tail-negative.lisp > "$d11_dedupe_bad_late"
run_case run_type_rejection d11-clojure-dedupe-late-improper-tail-type-negative "$d11_dedupe_bad_late" 'car expects a non-empty list'
# Суворий пріоритет D3-структури над першокласною функцією-ключем.
d11_partition_bad_early="$evidence/d11-clojure-partition-early-bad-tail-complete.lisp"
d11_partition_bad_late="$evidence/d11-clojure-partition-late-bad-tail-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-early-bad-tail-negative.lisp > "$d11_partition_bad_early"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp tests/semantic/d11-clojure-partition-late-bad-tail-negative.lisp > "$d11_partition_bad_late"
run_case run_error_rejection d11-clojure-partition-early-bad-tail "$d11_partition_bad_early" Type 'car expects a non-empty list'
run_case run_error_rejection d11-clojure-partition-late-bad-tail "$d11_partition_bad_late" Type 'car expects a non-empty list'
# Прямий helper: до першого callback пріоритет D3 CAR Type над D3 CDR Type.
d11_partition_direct_helper_bad="$evidence/d11-clojure-partition-direct-helper-bad-tail-complete.lisp"
cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp \
  tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp > "$d11_partition_direct_helper_bad"
run_case run_error_rejection d11-clojure-partition-direct-helper-bad-tail "$d11_partition_direct_helper_bad" Type 'car expects a non-empty list'
sha256sum lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp \
  tests/semantic/d11-clojure-partition-early-bad-tail-negative.lisp \
  tests/semantic/d11-clojure-partition-late-bad-tail-negative.lisp \
  tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp > "$evidence/d11-clojure-partition-spine-inputs.sha256"
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
for constructor in значення-у-списку?-ядро значення-у-списку? знайти-за-ключем-ядро знайти-за-ключем створити-спостереження створити-твердження створити-доказ створити-намір спостереження? твердження? доказ? намір?; do
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

# D6 ZIP: витягаємо лише канонічний SENS DEFINE із core4-d6b.
d6_zip_source="$evidence/d6-zip-define.lisp"
if ! awk -v target="(визначити спарувати-послідовності" '
  $0 == target { if (found++) exit 2; copying = 1 }
  copying && NF == 0 { copying = 0; complete++; next }
  copying { print }
  END { if (found != 1 || complete != 1 || copying) exit 2 }
' lib/core4-parts/core4-d6b.lisp > "$d6_zip_source"; then
  echo "::error::D6_ZIP_SOURCE_NOT_ISOLATABLE" >&2
  exit 2
fi
d6_zip_positive="$evidence/d6-zip-proper-complete.lisp"
d6_zip_mutant="$evidence/d6-zip-proper-mutant-complete.lisp"
d6_zip_bad_tail="$evidence/d6-zip-improper-tail-complete.lisp"
d6_zip_bad_root="$evidence/d6-zip-improper-root-complete.lisp"
d6_zip_order="$evidence/d6-zip-structural-order-complete.lisp"
d6_zip_right_root="$evidence/d6-zip-right-root-complete.lisp"
d6_zip_right_tail="$evidence/d6-zip-right-tail-complete.lisp"
cat -- "$d6_zip_source" tests/semantic/d6-zip-proper-law.lisp > "$d6_zip_positive"
cat -- "$d6_zip_source" tests/semantic/d6-zip-proper-mutant.lisp > "$d6_zip_mutant"
cat -- "$d6_zip_source" tests/semantic/d6-zip-improper-tail-negative.lisp > "$d6_zip_bad_tail"
cat -- "$d6_zip_source" tests/semantic/d6-zip-improper-root-negative.lisp > "$d6_zip_bad_root"
cat -- "$d6_zip_source" tests/semantic/d6-zip-structural-order-law.lisp > "$d6_zip_order"
cat -- "$d6_zip_source" tests/semantic/d6-zip-right-root-atom-negative.lisp > "$d6_zip_right_root"
cat -- "$d6_zip_source" tests/semantic/d6-zip-right-tail-atom-negative.lisp > "$d6_zip_right_tail"
sha256sum lib/core4.lisp lib/core4-parts/core4-d6b.lisp \
  tests/semantic/d6-zip-proper-law.lisp tests/semantic/d6-zip-proper-mutant.lisp \
  tests/semantic/d6-zip-improper-tail-negative.lisp \
  tests/semantic/d6-zip-improper-root-negative.lisp \
  tests/semantic/d6-zip-structural-order-law.lisp \
  tests/semantic/d6-zip-right-root-atom-negative.lisp \
  tests/semantic/d6-zip-right-tail-atom-negative.lisp \
  tests/semantic/d6-d8-zip-swap-interoperability-law.lisp > "$evidence/d6-zip-inputs.sha256"
run_case run_law d6-zip-proper "$d6_zip_positive" 1
run_case run_law d6-zip-proper-mutant "$d6_zip_mutant" 0
run_case run_type_rejection d6-zip-improper-tail "$d6_zip_bad_tail" 'car expects a non-empty list'
run_case run_type_rejection d6-zip-improper-root "$d6_zip_bad_root" 'car expects a non-empty list'
run_case run_law d6-zip-structural-order "$d6_zip_order" 1
run_case run_type_rejection d6-zip-right-root "$d6_zip_right_root" 'car expects a non-empty list'
run_case run_type_rejection d6-zip-right-tail "$d6_zip_right_tail" 'car expects a non-empty list'
run_case run_law d6-d8-zip-swap-interoperability tests/semantic/d6-d8-zip-swap-interoperability-law.lisp 1 core4
# Д6:111001 UNZIP · один SENS-обхід, проєкції та всі D3 Type-негативи.
run_case run_law d6-unzip-single-pass-positive tests/semantic/d6-unzip-single-pass-law.lisp 1 core4
run_case run_law d6-unzip-single-pass-mutant tests/semantic/d6-unzip-single-pass-mutant.lisp 0 core4
run_case run_error_rejection d6-unzip-atom-root tests/semantic/d6-unzip-atom-root-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-unzip-atom-tail tests/semantic/d6-unzip-atom-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-unzip-atom-element tests/semantic/d6-unzip-atom-element-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-unzip-empty-pair tests/semantic/d6-unzip-empty-pair-negative.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4.lisp lib/core4-parts/core4-d6b.lisp \
  tests/semantic/d6-unzip-single-pass-law.lisp \
  tests/semantic/d6-unzip-single-pass-mutant.lisp \
  tests/semantic/d6-unzip-atom-root-negative.lisp \
  tests/semantic/d6-unzip-atom-tail-negative.lisp \
  tests/semantic/d6-unzip-atom-element-negative.lisp \
  tests/semantic/d6-unzip-empty-pair-negative.lisp > "$evidence/d6-unzip-inputs.sha256"

# D6 UNION: одна точна SENS-бібліотека, лише витяг чинних DEFINE.
# Неправильний D1-хвіст має відхилятися Type, а не повертати обрізаний результат.
d6_union_source="$evidence/d6-union-exact-definitions.lisp"
: > "$d6_union_source"
for spec in 'lib/core4-parts/core4-d6.lisp|значення-у-списку?-ядро' \
  'lib/core4-parts/core4-d6.lisp|значення-у-списку?' \
  'lib/core4-parts/core4-d6b.lisp|об'"'"'єднання-перевірити-правий' \
  'lib/core4-parts/core4-d6b.lisp|об'"'"'єднання'; do
  d6_union_file="${spec%%|*}"
  d6_union_name="${spec#*|}"
  if ! awk -v target="(визначити $d6_union_name" '
    $0 == target { if (found++) exit 2; copying = 1 }
    copying && NF == 0 { copying = 0; complete++; next }
    copying { print }
    END { if (found != 1 || complete != 1 || copying) exit 2 }
  ' "$d6_union_file" >> "$d6_union_source"; then
    echo "::error::D6_UNION_DEFINITION_NOT_ISOLATABLE function=$d6_union_name source=$d6_union_file" >&2
    exit 2
  fi
  printf '\n' >> "$d6_union_source"
done
# Охоронець власності бачить точний SOURCE і одне використання кожного bundle.
# Семантика не переходить у shell: лише з'єднуємо канонічні DEFINE та SENS закон.
d6_union_proper_source="$evidence/d6-union-proper-law-complete.lisp"
d6_union_mutant_source="$evidence/d6-union-proper-mutant-complete.lisp"
cat -- "$d6_union_source" tests/semantic/d6-union-proper-law.lisp > "$d6_union_proper_source"
cat -- "$d6_union_source" tests/semantic/d6-union-proper-mutant.lisp > "$d6_union_mutant_source"
for kind in improper-tail-negative improper-root-negative; do
  cat -- "$d6_union_source" "tests/semantic/d6-union-$kind.lisp" > "$evidence/d6-union-$kind-complete.lisp"
done
run_case run_law d6-union-proper "$d6_union_proper_source" 1
run_case run_law d6-union-proper-mutant "$d6_union_mutant_source" 0
run_case run_type_rejection d6-union-improper-tail "$evidence/d6-union-improper-tail-negative-complete.lisp" 'car expects a non-empty list'
run_case run_type_rejection d6-union-improper-root "$evidence/d6-union-improper-root-negative-complete.lisp" 'car expects a non-empty list'
# Нові закони D6: права основа має бути правильним D3-списком.
# До кожного тесту долучаємо той самий канонічний SENS-витяг, без host-оракула.
for kind in right-validated-law right-root-negative right-tail-negative right-hidden-tail-negative; do
  cat -- "$d6_union_source" "tests/semantic/d6-union-$kind.lisp" > "$evidence/d6-union-$kind-complete.lisp"
done
run_case run_law d6-union-right-validated "$evidence/d6-union-right-validated-law-complete.lisp" 1
run_case run_type_rejection d6-union-right-root "$evidence/d6-union-right-root-negative-complete.lisp" 'car expects a non-empty list'
run_case run_type_rejection d6-union-right-tail "$evidence/d6-union-right-tail-negative-complete.lisp" 'car expects a non-empty list'
run_case run_type_rejection d6-union-right-hidden-tail "$evidence/d6-union-right-hidden-tail-negative-complete.lisp" 'car expects a non-empty list'
sha256sum lib/core4.lisp lib/core4-parts/core4-d6.lisp lib/core4-parts/core4-d6b.lisp \
  tests/semantic/d6-union-*.lisp > "$evidence/d6-union-inputs.sha256"

run_case run_law d6-intersection-order-positive tests/semantic/d6-intersection-order-law.lisp 1 core4
run_case run_law d6-intersection-duplicates-mutant tests/semantic/d6-intersection-duplicates-mutant.lisp 0 core4
run_case run_error_rejection d6-intersection-left-tail tests/semantic/d6-intersection-left-tail-negative.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4.lisp tests/semantic/d6-intersection-order-law.lisp \
  tests/semantic/d6-intersection-duplicates-mutant.lisp \
  tests/semantic/d6-intersection-left-tail-negative.lisp > "$evidence/d6-intersection-inputs.sha256"
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
# Д6: перший клас функцій — СЕНС одержує справжні DEFINE з Core4.
# Мутант має D1:ні. Хибну холодну відмову прибрано: D6 ANY/ALL мають DEFINE.
# Окремі свідки виконують чинні функції в Core4, без host-обчислення.
d6_first_class_law_bundle="$evidence/d6-any-all-first-class-law.lisp"
d6_first_class_mutant_bundle="$evidence/d6-any-all-first-class-mutant.lisp"
cat -- tests/fixtures/epistemic-d1-names.lisp "$d6_quantifier_source" tests/semantic/d6-any-all-first-class-law.lisp > "$d6_first_class_law_bundle"
cat -- tests/fixtures/epistemic-d1-names.lisp "$d6_quantifier_source" tests/semantic/d6-any-all-first-class-mutant.lisp > "$d6_first_class_mutant_bundle"
run_case run_law d6-any-all-first-class-law "$d6_first_class_law_bundle" 1
run_case run_law d6-any-all-first-class-mutant "$d6_first_class_mutant_bundle" 0
run_case run_law d6-any-all-native-call-law tests/semantic/d6-any-all-native-call-law.lisp 1 core4
run_case run_law d6-any-all-native-call-mutant tests/semantic/d6-any-all-native-call-mutant.lisp 0 core4
# D6 improper tails: real D1 NO is not D3 NIL.
run_case run_error_rejection d6-any-improper-tail-type tests/semantic/d6-any-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-all-improper-tail-type tests/semantic/d6-all-improper-tail-negative.lisp Type 'car expects a non-empty list' core4
# Д6 ANY/ALL і похідні Д8: точний D3:(), коротке замикання та Type.
run_case run_law d6-any-all-exact-empty tests/semantic/d6-any-all-exact-empty-law.lisp 1 core4
run_case run_law d6-any-vacuous-mutant tests/semantic/d6-any-vacuous-mutant.lisp 0 core4
run_case run_error_rejection d6-any-invalid-root tests/semantic/d6-any-invalid-root-law.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d6-all-invalid-root tests/semantic/d6-all-invalid-root-law.lisp Type 'car expects a non-empty list' core4
run_case run_law d8-quantifier-composition tests/semantic/d8-quantifier-composition-law.lisp 1 core4
run_case run_law d8-quantifier-composition-mutant tests/semantic/d8-quantifier-composition-mutant.lisp 0 core4
run_case run_error_rejection d8-notany-invalid-root tests/semantic/d8-notany-invalid-root-law.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d8-notevery-invalid-root tests/semantic/d8-notevery-invalid-root-law.lisp Type 'car expects a non-empty list' core4
run_case run_error_rejection d8-all-not-invalid-root tests/semantic/d8-all-not-invalid-root-law.lisp Type 'car expects a non-empty list' core4
sha256sum lib/core4-parts/core4-d6b.lisp tests/semantic/d6-any-all-native-call-law.lisp tests/semantic/d6-any-all-native-call-mutant.lisp > "$evidence/d6-any-all-native-call-inputs.sha256"
sha256sum lib/core4.lisp lib/core4-parts/core4-d6b.lisp \
  tests/semantic/d6-any-all-exact-empty-law.lisp \
  tests/semantic/d6-any-vacuous-mutant.lisp \
  tests/semantic/d6-any-invalid-root-law.lisp \
  tests/semantic/d6-all-invalid-root-law.lisp \
  tests/semantic/d8-quantifier-composition-law.lisp \
  tests/semantic/d8-quantifier-composition-mutant.lisp \
  tests/semantic/d8-notany-invalid-root-law.lisp \
  tests/semantic/d8-notevery-invalid-root-law.lisp \
  tests/semantic/d8-all-not-invalid-root-law.lisp > "$evidence/d6-d8-quantifier-inputs.sha256"

# Д11 ZIP-WITH: відображення двох списків із повним D3-доказом.
# Реальні позитив, мутант і два Type-негативи виконуються в SENS.
# Залежність завжди зберігаємо як канонічне Lisp DEFINE до самого свідка.
d11_zip_with_positive="$evidence/d11-zip-with-positive-complete.lisp"
d11_zip_with_mutant="$evidence/d11-zip-with-mutant-complete.lisp"
d11_zip_with_bad_left="$evidence/d11-zip-with-bad-left-complete.lisp"
d11_zip_with_bad_right="$evidence/d11-zip-with-bad-right-complete.lisp"
cat -- lib/d11-srfi1-zip-with.lisp tests/semantic/d11-srfi1-zip-with-law.lisp > "$d11_zip_with_positive"
cat -- lib/d11-srfi1-zip-with.lisp tests/semantic/d11-srfi1-zip-with-mutant.lisp > "$d11_zip_with_mutant"
cat -- lib/d11-srfi1-zip-with.lisp tests/semantic/d11-srfi1-zip-with-improper-left-negative.lisp > "$d11_zip_with_bad_left"
cat -- lib/d11-srfi1-zip-with.lisp tests/semantic/d11-srfi1-zip-with-improper-right-negative.lisp > "$d11_zip_with_bad_right"
run_case run_law d11-zip-with-order-shorter-positive "$d11_zip_with_positive" 1 core4
run_case run_law d11-zip-with-swapped-pair-mutant "$d11_zip_with_mutant" 0 core4
run_case run_error_rejection d11-zip-with-improper-left "$d11_zip_with_bad_left" Type 'car expects a non-empty list' core4
run_case run_error_rejection d11-zip-with-improper-right "$d11_zip_with_bad_right" Type 'car expects a non-empty list' core4
sha256sum lib/d11-srfi1-zip-with.lisp tests/semantic/d11-srfi1-zip-with-*.lisp > "$evidence/d11-zip-with-inputs.sha256"

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
