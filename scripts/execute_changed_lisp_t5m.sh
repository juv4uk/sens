#!/usr/bin/env bash
# Людський .lisp спершу пакує Zig/T5M; виконується тільки фізичний .sens.
# Відсутність допущеного механізму лишається явним боргом, не GO.
set -euo pipefail
if (( $# != 3 )); then
  echo "usage: $0 SENS_BINARY CHANGED_LISP_LIST EVIDENCE_DIR" >&2
  exit 2
fi
binary="$1"
manifest="$2"
outdir="$3"
test -x "$binary"
test -f "$manifest"
mkdir -p "$outdir"
# Лише committed `.sens`, що пройшли Zig-пару й самостійне виконання,
# потрапляють до наступного фізичного бенчмарка.
benchmark_manifest="$outdir/benchmark-binaries.txt"
: > "$benchmark_manifest"
# Нативний SENS/Zig — єдиний типовий маршрут. Невідомий режим
# НЕ має права непомітно запускати допоміжний Python/JSON мігратор.
# Історичний preview доступний тільки після явного SENS_NATIVE_T5M=0.
case "${SENS_NATIVE_T5M:-1}" in
  1)
    native_open="${SENS_T5M_OPEN:-$(dirname "$binary")/sens-trit}"
    test -x "$native_open" || { echo "::error::SENS_NATIVE_VIEW_READER_MISSING path=$native_open" >&2; exit 2; }
    ;;
  0) ;;
  *)
    echo "::error::SENS_NATIVE_T5M_INVALID expected=0_or_1 source=environment; Python fallback forbidden" >&2
    exit 2
    ;;
esac
failed_files=0
# Показники виконання належать тільки реальному SENS CLI та Zig T5M;
# це не дозвіл на семантичну або релізну атестацію.
declare -A native_view_roundtrip_paths=()
declare -A native_paired_executed_paths=()
declare -A native_standalone_parity_paths=()
# Одне джерело може мати кілька реальних порушень (байти, перегляд,
# виконання). Звітуємо всі, але files_failed рахує саме файли.
declare -A failed_file_paths=()
mark_file_failed() {
  if [[ -z "${failed_file_paths[$file]+present}" ]]; then
    failed_file_paths["$file"]=1
    failed_files=$((failed_files + 1))
  fi
}
# Лише в явному історичному режимі SENS_NATIVE_T5M=0: за розходження 
# Python preview із SENS/T5M діагностуємо відповідну розбіжність. 
# Основний маршрут SENS_NATIVE_T5M=1 не залежить від Python/JSON.
# На справжній розбіжності source ↔ Python minted T5M залучаємо
# чинний SENS reader як незалежне джерело точних слів. Він користується
# тим самим Zig codec, що й --t5m-pair. Помилку не приховуємо:
# обидва фізичні файли лишаються в evidence для адресного ремонту.
diagnose_sens_authority_mint() {
  local paired_error="$1"
  grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$paired_error" || return 0
  local authority="$dir/sens-authority.sens"
  if ! timeout 45s "$binary" --t5m-mint "$file" "$authority" \
       >"$dir/sens-authority.mint.stdout" 2>"$dir/sens-authority.mint.stderr"; then
    sed 's/^/T5M SENS mint stderr: /' "$dir/sens-authority.mint.stderr" >&2
    echo "::error::T5M_SENS_AUTHORITY_MINT_FAILED source=$file action=repair-source-law" >&2
    return 0
  fi
  if [[ ! -s "$authority" ]]; then
    echo "::error::T5M_SENS_AUTHORITY_MINT_EMPTY source=$file" >&2
    return 0
  fi
  if timeout 45s "$binary" --t5m-pair "$file" "$authority" \
       >"$dir/sens-authority.paired.stdout" 2>"$dir/sens-authority.paired.stderr"; then
    if cmp -s "$pair" "$authority"; then
      echo "T5M_SENS_AUTHORITY_MATCH source=$file exact=ZIG_AND_SENS"
    else
      echo "::error::T5M_INDEPENDENT_PROJECTION_DIVERGENCE source=$file migrated=$pair authority=$authority action=repair-migrator-or-source physical=NOT_CERTIFIED" >&2
    fi
  else
    sed 's/^/T5M SENS authority stderr: /' "$dir/sens-authority.paired.stderr" >&2
    echo "::error::T5M_SENS_AUTHORITY_EXECUTION_FAILED source=$file authority=$authority" >&2
  fi
}
# Основний CI-шлях: точні слова належать SENS reader, байти — Zig.
# Не читаємо JSON, не викликаємо Python, не проголошуємо байти семантикою.
# Старий незалежний Python-мігратор лишається лише інструментом порівняння
# та для його окремих регресійних тестів, а не обов'язковим входом SENS.
run_native_t5m_program() {
  local physical="$dir/$(basename "$file" .lisp).sens"
  local view="${physical%.sens}"
  local committed="$(dirname "$file")/$(basename "$file" .lisp).sens"
  local committed_view="${committed%.sens}"
  local status=0
  local source_bytes native_timeout
  source_bytes=$(wc -c < "$file")
  native_timeout=45s
  # Реальне core4.lisp має ~0,5 MiB: 45s перериває SENS mint
  # раніше від результату (CI status=124), не доводячи помилки джерела.
  # Ліміт лишається кінцевим; лише велике джерело дістає час на
  # справжній SENS reader → Zig/T5M → обернення → виконання.
  if (( source_bytes >= 262144 )); then
    native_timeout=180s
  fi
  echo "T5M_NATIVE_BUDGET source=$file bytes=$source_bytes timeout=$native_timeout"
  # Для модулів з DEFINE-залежностями використовуємо новий SENS CLI.
  # Mint і парна перевірка відбуваються з однаковими binding-source.
  local mint_flag=--t5m-mint
  if (( ${#binding_sources[@]} != 0 )); then
    mint_flag=--t5m-mint-pair
  fi
  if timeout "$native_timeout" "$binary" "$mint_flag" "$file" "$physical" "${binding_sources[@]}" \
      >"$dir/native-mint.stdout" 2>"$dir/native-mint.stderr"; then
    if [[ ! -s "$physical" ]]; then
      echo "::error::T5M_NATIVE_MINT_EMPTY source=$file" >&2
      mark_file_failed
      return
    fi
  else
    status=$?
    if (( status == 124 )); then
      echo "::error::T5M_NATIVE_MINT_TIMEOUT source=$file bytes=$source_bytes timeout=$native_timeout" >&2
    fi
    sed 's/^/SENS native mint: /' "$dir/native-mint.stderr" >&2
    echo "::error::T5M_NATIVE_MINT_FAILED source=$file status=$status release=NOT_CERTIFIED" >&2
    mark_file_failed
    return
  fi

  # Той самий Zig-носій відкривається незалежним фізичним reader.
  # Це точний бітовий перегляд, не повторний парсинг Python/JSON.
  if timeout "$native_timeout" "$native_open" open "$physical" >"$view" 2>"$dir/native-view.stderr"; then
    if [[ ! -s "$view" ]]; then
      echo "::error::T5M_NATIVE_VIEW_EMPTY source=$file" >&2
      mark_file_failed
      return
    fi
  else
    status=$?
    sed 's/^/SENS physical view: /' "$dir/native-view.stderr" >&2
    echo "::error::T5M_NATIVE_VIEW_FAILED source=$file status=$status" >&2
    mark_file_failed
    return
  fi
  # Байтове обернення Zig T5M та канонічного бітового перегляду D24+.
  if timeout "$native_timeout" "$native_open" verify-view "$physical" \
      >"$dir/native-inverse.stdout" 2>"$dir/native-inverse.stderr"; then
    :
  else
    status=$?
    sed 's/^/SENS physical inverse: /' "$dir/native-inverse.stderr" >&2
    echo "::error::T5M_NATIVE_VIEW_ROUNDTRIP_FAILED source=$file status=$status" >&2
    mark_file_failed
    return
  fi
  native_view_roundtrip_paths["$file"]=1
  if [[ -e "$committed" || -L "$committed" ]]; then
    if [[ ! -f "$committed" || -L "$committed" ]]; then
      echo "::error::T5M_COMMITTED_PAIR_NOT_REGULAR source=$file companion=$committed" >&2
      mark_file_failed
    elif ! cmp -s "$physical" "$committed"; then
      echo "::error::T5M_COMMITTED_PAIR_DRIFT source=$file companion=$committed action=refresh-via-sens-zig" >&2
      mark_file_failed
    fi
    if [[ ! -f "$committed_view" || -L "$committed_view" ]]; then
      echo "::error::T5M_COMMITTED_VIEW_MISSING source=$file companion=$committed_view" >&2
      mark_file_failed
    elif ! cmp -s "$view" "$committed_view"; then
      echo "::error::T5M_COMMITTED_VIEW_DRIFT source=$file companion=$committed_view action=refresh-via-sens-zig" >&2
      mark_file_failed
    fi
  elif [[ -e "$committed_view" || -L "$committed_view" ]]; then
    echo "::error::T5M_ORPHAN_VIEW source=$file view=$committed_view" >&2
    mark_file_failed
  else
    echo "::notice::T5M_NATIVE_NOT_COMMITTED source=$file release=NOT_CERTIFIED"
  fi

  # Критичний доказ — реальне парне виконання фізичних Zig-байтів.
  if timeout "$native_timeout" "$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}" \
      >"$dir/native-paired.stdout" 2>"$dir/native-paired.stderr"; then
    native_paired_executed_paths["$file"]=1
    if timeout "$native_timeout" "$binary" "$physical" \
        >"$dir/native-standalone.stdout" 2>"$dir/native-standalone.stderr"; then
      if ! cmp -s "$dir/native-standalone.stdout" "$dir/native-paired.stdout"; then
        echo "::error::T5M_NATIVE_EXECUTION_OUTPUT_DRIFT source=$file" >&2
        mark_file_failed
        return
      fi
      native_standalone_parity_paths["$file"]=1
      if [[ -f "$committed" && ! -L "$committed" ]] && cmp -s "$physical" "$committed"; then
        printf '%s\n' "$committed" >> "$benchmark_manifest"
      fi
      echo "T5M_NATIVE_STANDALONE_AND_PAIRED_PASS source=$file physical=ZIG_VERIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
    else
      status=$?
      # Лише названі відмови фізичного reader D24+/D7 допускають
      # paired-only. Panic, тайм-аути й невідомі збої — справжній RED.
      if (( status != 124 && status != 137 )) &&
         { grep -Fq 'T5M requires exact source projection to D24+ before transport' "$dir/native-standalone.stderr" ||
           grep -Fq 'unknown Text7 binding:' "$dir/native-standalone.stderr" ||
           { grep -Fq 'Фізичне T5M-декодування зберегло точні ширини слів' "$dir/native-standalone.stderr" &&
             grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$dir/native-standalone.stderr"; }; }; then
        sed 's/^/SENS paired-only known limit: /' "$dir/native-standalone.stderr" >&2
        echo "::notice::T5M_NATIVE_PAIRED_ONLY source=$file standalone_status=$status physical=ZIG_VERIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
      else
        sed 's/^/SENS standalone unexpected error: /' "$dir/native-standalone.stderr" >&2
        echo "::error::T5M_NATIVE_STANDALONE_UNEXPECTED_FAIL source=$file status=$status physical=NOT_CERTIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED" >&2
        mark_file_failed
      fi
    fi
  else
    status=$?
    sed 's/^/SENS native paired: /' "$dir/native-paired.stderr" >&2
    echo "::error::T5M_NATIVE_PAIRED_EXECUTION_FAIL source=$file status=$status release=NOT_CERTIFIED" >&2
    mark_file_failed
  fi
}
checked_files=0
physical_not_supported=0
while IFS= read -r file || [[ -n "$file" ]]; do
  [[ -n "$file" ]] || continue
  checked_files=$((checked_files + 1))
  if [[ "$file" != *.lisp || ! -f "$file" || -L "$file" ]]; then
    echo "::error::T5M_CHANGED_SOURCE_INVALID path=$file" >&2
    mark_file_failed
    continue
  fi
  # Відхиляємо підставлений фізичний носій ДО мігратора й будь-якого
  # виконання. Симлінк (навіть dangling), каталог або FIFO не є .sens.
  # Інакше перевірка після mint дозволяє непотрібні сторонні дії.
  committed_input="$(dirname "$file")/$(basename "$file" .lisp).sens"
  if [[ -e "$committed_input" || -L "$committed_input" ]] &&
     [[ ! -f "$committed_input" || -L "$committed_input" ]]; then
    echo "::error::T5M_COMMITTED_PAIR_NOT_REGULAR source=$file companion=$committed_input" >&2
    mark_file_failed
    continue
  fi
  id="$(printf '%s' "$file" | sha256sum | cut -c1-16)"
  dir="$outdir/$id"
  mkdir -p "$dir"
  report="$dir/migration.json"
  echo "T5M_CHANGED_SOURCE path=$file"
  binding_sources=()
  # Механізм D9 «уніфікувати» справді визначено в lib/unify.lisp.
  # Це точне джерело завантажуваного DEFINE, не дозвіл викликати
  # кожного резидента D9 без реалізації.
  if [[ "$file" == "lib/reason.lisp" || "$file" == "lib/forward.lisp" ]]; then
    # Чинний D9 уніфікатор визначено в українському Lisp, не в самій таблиці.
    binding_sources=(--binding-source lib/unify.lisp)
  # preload_t5m_binding_sources виконує DEFINE послідовно у SENS;
  # залежність завжди завантажується РАНІШЕ за користувача.
  elif [[ "$file" == "lib/narrate.lisp" ]]; then
    # Пояснення бере «походження» з живого DEFINE lib/reason.lisp;
    # Reason, у свою чергу, користується визначеннями уніфікації.
    # Обидва джерела лише свідчать завантажувані механізми — не вигадують D9.
    binding_sources=(--binding-source lib/unify.lisp --binding-source lib/reason.lisp)
  elif [[ "$file" == "lib/result-status.lisp" ]]; then
    # D9 модуль-відомий? та модуль-клаузи-зараз визначено в Knowledge;
    # забезпечити-індекс-міркування й міркувати — у Reason.
    # До перевірки T5M надаємо лише справжні Lisp DEFINE та їхні SHA.
    # Резидент каталогу D9 без DEFINE надалі лишається недопущеним.
    binding_sources=(--binding-source lib/unify.lisp
                     --binding-source lib/knowledge.lisp
                     --binding-source lib/reason.lisp)
  elif [[ "$file" == "tests/fixtures/mechanism-selector-1047-witness.lisp" ]]; then
    # Іменовані SENS DEFINE механізмів походять із мовних бібліотек,
    # а не з вигаданих D9/D10 resident callables чи host-функцій.
    # Передувати залежностям повинен реєстр українських проєкцій.
    binding_sources=(--binding-source lib/surface/semantic-registry-api.lisp
                     --binding-source lib/mechanism-selector.lisp)
  elif [[ "$file" == "lib/translation.lisp" ]]; then
    # Переклад викликає лише реальні визначення: знання/світ та D8
    # класифікацію тексту з Yantra. Каталог D9/D10 сам по собі
    # не надає виконуваності; парний SENS надалі перевіряє семантику.
    binding_sources=(--binding-source lib/unify.lisp
                     --binding-source lib/knowledge.lisp
                     --binding-source lib/reason.lisp
                     --binding-source lib/world.lisp
                     --binding-source lib/yantra.lisp
                     --binding-source lib/result-status.lisp)
  elif [[ "$file" == "tests/semantic/d9-world-shape-module-events-laws.lisp" ||
          "$file" == "tests/semantic/world-exact-arity-witness.lisp" ]]; then
    # Обидва живі свідки світу викликають DEFINE з lib/world.lisp.
    # Без цього SENS правильно відхиляє невідомий D7 Text7-символ «світ?».
    # Не підміняємо виконання хостовим оракулом і не тягнемо весь Reason.
    binding_sources=(--binding-source lib/world.lisp)
  fi
  if [[ "${SENS_NATIVE_T5M:-1}" == 1 ]]; then
    run_native_t5m_program
    continue
  fi
  code=0
  python3 scripts/migrate-three-pass.py "$file" \
    --out "$dir" --report "$report" --codec t5m --source-surface укр "${binding_sources[@]}" \
    >"$dir/migration.log" 2>&1 || code=$?
  if [[ ! -s "$report" ]]; then
    cat "$dir/migration.log" >&2
    echo "::error::T5M_MIGRATION_NO_REPORT path=$file status=$code" >&2
    mark_file_failed
    continue
  fi
  report_status=0
  outcome="$(python3 - "$report" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
summary = report["summary"]
# Типово некоректний JSON-лічильник не можна віддавати арифметиці Bash.
# bool є підкласом int у Python, але true не є кількістю файлів.
for key in ("files_written", "files_blocked", "files_not_program"):
    count = summary[key]
    if type(count) is not int or count < 0:
        raise ValueError("invalid migration counter: " + key)
for row in report["files"]:
    if row["status"] == "blocked":
        print("T5M_MIGRATION_DEBT path=" + row["path"] + " reason=" + row["reason"], file=sys.stderr)
print(summary["files_written"], summary["files_blocked"], summary["files_not_program"])
PY
)" || report_status=$?
  if (( report_status != 0 )); then
    echo "::error::T5M_MIGRATION_REPORT_INVALID path=$file status=$report_status" >&2
    mark_file_failed
    continue
  fi
  read -r written blocked not_program <<< "$outcome"
  # Для одного вхідного Lisp результат є рівно одним із трьох станів.
  # Подвійний статус written + not-program не може приховати програму.
  if (( written + blocked + not_program != 1 )); then
    echo "::error::T5M_MIGRATION_REPORT_COUNTS_INVALID path=$file written=$written blocked=$blocked not_program=$not_program" >&2
    mark_file_failed
    continue
  fi
  if (( code > 2 )); then
    echo "::error::T5M_MIGRATION_INTERNAL_FAILURE path=$file status=$code" >&2
    mark_file_failed
    continue
  fi
  if (( blocked > 0 )); then
    echo "::error::T5M_MIGRATION_UNPROVEN path=$file blocked=$blocked semantic=NOT_CERTIFIED" >&2
    mark_file_failed
    continue
  fi
  # Позначка DATA у JSON не анулює справжню помилку процесу міграції.
  # Інакше exit 1 + files_not_program=1 непомітно перетворювалися на PASS.
  if (( code != 0 )); then
    echo "::error::T5M_MIGRATION_FAILED path=$file status=$code written=$written not_program=$not_program" >&2
    mark_file_failed
    continue
  fi
  if (( not_program > 0 )); then
    # Джерело вже не є програмою. Стара однойменна .sens, якщо лишилася,
    # не може тихо вважатися правильною: це колишній виконуваний артефакт,
    # якого нове джерело вже не визначає. Не зачіпаємо чужі файли.
    stale_pair="$(dirname "$file")/$(basename "$file" .lisp).sens"
    stale_view="${stale_pair%.sens}"
    # Похідний перегляд без носія так само є залишком колишньої програми.
    # Перевіряємо і dangling symlink, не лише звичайний файл.
    if [[ -e "$stale_pair" || -L "$stale_pair" || -e "$stale_view" || -L "$stale_view" ]]; then
      echo "::error::T5M_NONPROGRAM_STALE_PAIR source=$file companion=$stale_pair view=$stale_view action=remove-obsolete-pair-and-view-or-restore-source" >&2
      mark_file_failed
      continue
    fi
    echo "T5M_NOT_PROGRAM path=$file"
    continue
  fi
  if (( code != 0 || written != 1 )); then
    echo "::error::T5M_MIGRATION_INCONSISTENT path=$file status=$code written=$written" >&2
    mark_file_failed
    continue
  fi
  pair="$dir/$(basename "$file" .lisp).sens"
  if [[ ! -s "$pair" ]]; then
    echo "::error::T5M_MINTED_PAIR_MISSING path=$file" >&2
    mark_file_failed
    continue
  fi
  committed="$(dirname "$file")/$(basename "$file" .lisp).sens"
  staged_view="${pair%.sens}"
  committed_view="${committed%.sens}"
  if [[ ! -f "$staged_view" || -L "$staged_view" ]]; then
    echo "::error::T5M_MINTED_VIEW_MISSING source=$file expected=$staged_view" >&2
    mark_file_failed
    continue
  fi
  if [[ -e "$committed" || -L "$committed" ]]; then
    # Опублікований носій повинен бути звичайним файлом, не symlink,
    # каталогом чи іншим об'єктом, що імітує фізичну T5M-пару.
    if [[ ! -f "$committed" || -L "$committed" ]]; then
      echo "::error::T5M_COMMITTED_PAIR_NOT_REGULAR source=$file companion=$committed" >&2
      mark_file_failed
      continue
    fi
    # Застаріла регулярна пара — це реальний борг на виправлення,
    # але НЕ причина пропускати запуск щойно створеного Zig T5M.
    # CI лишається червоним, проте реальний SENS показує наступну помилку.
    if ! cmp -s "$pair" "$committed"; then
      echo "::error::T5M_COMMITTED_PAIR_DRIFT source=$file companion=$committed action=refresh-pair" >&2
      mark_file_failed
    fi
    if [[ ! -f "$committed_view" || -L "$committed_view" ]]; then
      echo "::error::T5M_COMMITTED_VIEW_MISSING source=$file expected=$committed_view action=refresh-view" >&2
      mark_file_failed
    elif ! cmp -s "$staged_view" "$committed_view"; then
      echo "::error::T5M_COMMITTED_VIEW_DRIFT source=$file companion=$committed_view action=refresh-view" >&2
      mark_file_failed
    fi
  else
    # Без фізичного .sens однойменний перегляд не може засвідчувати пару.
    # Не зупиняємо новий SENS-виклик: покажемо його результат попри борг.
    if [[ -e "$committed_view" || -L "$committed_view" ]]; then
      echo "::error::T5M_ORPHAN_VIEW source=$file view=$committed_view companion=$committed action=refresh-complete-pair" >&2
      mark_file_failed
    else
      echo "::notice::T5M_PAIR_NOT_COMMITTED path=$file release=NOT_CERTIFIED"
    fi
  fi
  stdout="$dir/runtime.stdout"
  stderr="$dir/runtime.stderr"
  if timeout 45s "$binary" "$pair" >"$stdout" 2>"$stderr"; then
    # Успішне виконання фізичних байтів не доводить їхню відповідність
    # актуальному Lisp. Парний SENS-вхід мусить відбутися також на PASS.
    standalone_sha="$(sha256sum "$stdout" | cut -d ' ' -f 1)"
    if timeout 45s "$binary" --t5m-pair "$file" "$pair" >"$dir/paired.stdout" 2>"$dir/paired.stderr"; then
      paired_sha="$(sha256sum "$dir/paired.stdout" | cut -d ' ' -f 1)"
      # Успішні коди завершення ще не доводять однакове виконання.
      # Порівнюємо фактичний вивід двох SENS-входів без host-оракула.
      if cmp -s "$stdout" "$dir/paired.stdout"; then
        echo "T5M_FILE_EXECUTION PASS path=$file pair=$pair standalone_sha256=$standalone_sha paired_sha256=$paired_sha physical=ZIG_VERIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
      else
        echo "::error::T5M_PAIRED_RESULT_MISMATCH path=$file pair=$pair standalone_sha256=$standalone_sha paired_sha256=$paired_sha semantic=NOT_CERTIFIED" >&2
        mark_file_failed
      fi
    else
      status=$?
      sed 's/^/T5M paired stderr: /' "$dir/paired.stderr" >&2
      diagnose_sens_authority_mint "$dir/paired.stderr"
      echo "::error::T5M_PAIRED_SOURCE_EXECUTION_FAIL path=$file pair=$pair status=$status" >&2
      mark_file_failed
    fi
  else
    status=$?
    # Фізичний T5M зберігає W24 без втрат. Проте W24 сам по собі
    # не позначає домен: старий BinarySourceWord приймає лише W1–W9.
    # Це НЕ дає права приписати байтам D24 та оголосити physical PASS.
    # Для W24+ використовуємо точний парний маршрут: джерело лише
    # посвідчує домен, Zig декодує наданий .sens, SENS перевіряє кожний біт.
    # Новий SENS називає цю межу без згадок старого BinarySourceWord.
    # Обидва точні діагностичні варіанти запускають ОДИН парний маршрут:
    # невідомі/семантичні помилки не маскуємо і не перетворюємо на PASS.
    if { grep -Fq 'Фізичне T5M-декодування зберегло точні ширини слів' "$stderr" &&
         grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$stderr"; } ||
       grep -Fq 'T5M requires exact source projection to D24+ before transport' "$stderr"; then
      physical_not_supported=$((physical_not_supported + 1))
      echo "::notice::T5M_STANDALONE_D24_NOT_SUPPORTED source=$file pair=$pair status=$status"
      if timeout 45s "$binary" --t5m-pair "$file" "$pair" >"$stdout" 2>"$stderr"; then
        result_sha="$(sha256sum "$stdout" | cut -d ' ' -f 1)"
        echo "T5M_PHYSICAL_PAIRED_D24_PASS source=$file pair=$pair physical=ZIG_VERIFIED result_sha256=$result_sha semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
        continue
      else
        # Код береться з реального невдалого SENS, не з порожнього if.
        status=$?
      fi
      sed 's/^/T5M paired stderr: /' "$stderr" >&2
      diagnose_sens_authority_mint "$stderr"
      echo "::error::T5M_PHYSICAL_PAIRED_D24_FAIL source=$file pair=$pair status=$status" >&2
      mark_file_failed
      continue
    fi
    # Нове T5M D7: виконуване людське ім'я може мати лише Text7
    # транспортне слово. Голий .sens не знає його джерельного зв'язування.
    # Парний вхід перевіряє exact width+bits через Zig, потім виконує SENS.
    # UnknownSymbol після парної перевірки все ще реальна помилка, не PASS.
    if grep -Fq 'unknown Text7 binding:' "$stderr"; then
      echo "::notice::T5M_STANDALONE_D7_NEEDS_SOURCE_AUTHORITY source=$file pair=$pair status=$status"
      if timeout 45s "$binary" --t5m-pair "$file" "$pair" >"$stdout" 2>"$stderr"; then
        result_sha="$(sha256sum "$stdout" | cut -d ' ' -f 1)"
        echo "T5M_PHYSICAL_PAIRED_D7_PASS source=$file pair=$pair physical=ZIG_VERIFIED result_sha256=$result_sha semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
        continue
      else
        status=$?
        sed 's/^/T5M paired D7 stderr: /' "$stderr" >&2
        diagnose_sens_authority_mint "$stderr"
        echo "::error::T5M_PHYSICAL_PAIRED_D7_FAIL source=$file pair=$pair status=$status"
        mark_file_failed
        continue
      fi
    fi
    # Замість розпізнавати всі майбутні помилки за старими повідомленнями,
    # перевіряємо чинний парний вхід. Zig звіряє фізичні слова з джерелом,
    # а справжній SENS виконує результат; жодної Python-семантики.
    # Розходження чи невдача SENS лишаються червоними з обома діагнозами.
    standalone_status=$status
    cp "$stderr" "$dir/standalone.stderr"
    if timeout 45s "$binary" --t5m-pair "$file" "$pair" >"$stdout" 2>"$stderr"; then
      result_sha="$(sha256sum "$stdout" | cut -d ' ' -f 1)"
      echo "T5M_PHYSICAL_PAIRED_GENERIC_PASS source=$file pair=$pair physical=ZIG_VERIFIED result_sha256=$result_sha semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
      continue
    else
      status=$?
    fi
    sed 's/^/T5M standalone stderr: /' "$dir/standalone.stderr" >&2
    sed 's/^/T5M paired stderr: /' "$stderr" >&2
    diagnose_sens_authority_mint "$stderr"
    echo "::error::T5M_FILE_EXECUTION_FAIL path=$file pair=$pair standalone_status=$standalone_status paired_status=$status" >&2
    mark_file_failed
    continue
  fi
done < "$manifest"
printf 'T5M_CHANGED_SUMMARY files_checked=%s files_failed=%s physical_not_supported=%s native_view_roundtrip=%s native_paired_executed=%s native_standalone_parity=%s scope=changed_manifest semantic=NOT_CERTIFIED release=NOT_CERTIFIED\n' \
  "$checked_files" "$failed_files" "$physical_not_supported" \
  "${#native_view_roundtrip_paths[@]}" "${#native_paired_executed_paths[@]}" "${#native_standalone_parity_paths[@]}"
if (( failed_files > 0 )); then
  exit 2
fi
