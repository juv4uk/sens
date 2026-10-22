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
# Нативний SENS reader/eval і Zig T5M — єдиний маршрут перевірки.
# Жоден прапорець середовища не повинен повертати Python/JSON оракул.
if [[ "${SENS_NATIVE_T5M:-1}" != 1 ]]; then
  echo "::error::SENS_NATIVE_T5M_INVALID expected=1; historical Python fallback retired" >&2
  exit 2
fi
native_open="${SENS_T5M_OPEN:-$(dirname "$binary")/sens-trit}"
test -x "$native_open" || { echo "::error::SENS_NATIVE_VIEW_READER_MISSING path=$native_open" >&2; exit 2; }
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
# Фізична оберненість і виконання доводяться SENS/Zig; окремий
# дослідницький Python-мігратор не бере участі в цьому CI-маршруті.
run_native_t5m_program() {
  local physical="$dir/$(basename "$file" .lisp).sens"
  local view="${physical%.sens}"
  local committed="$(dirname "$file")/$(basename "$file" .lisp).sens"
  local committed_view="${committed%.sens}"
  local status=0
  local source_bytes native_timeout
  source_bytes=$(wc -c < "$file")
  native_timeout=45s
  # Мінімальний свідок може підвантажувати 300+ KiB визначень.
  # Дати бюджет СУМІ реальних Lisp-входів, інакше CI хибно
  # вважає живий SENS-закон непрацездатним через timeout=124.
  # Ні Python, ні JSON не беруть участі у reader чи семантиці.
  local total_input_bytes="$source_bytes"
  local dependency
  for ((i=1; i<${#binding_sources[@]}; i+=2)); do
    dependency="${binding_sources[i]}"
    if [[ ! -f "$dependency" || -L "$dependency" ]]; then
      echo "::error::T5M_NATIVE_BINDING_SOURCE_MISSING source=$file binding=$dependency" >&2
      mark_file_failed
      return
    fi
    (( total_input_bytes += $(wc -c < "$dependency") ))
  done
  if (( total_input_bytes >= 262144 )); then
    native_timeout=180s
  fi
  echo "T5M_NATIVE_BUDGET source=$file input_bytes=$total_input_bytes timeout=$native_timeout"
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
    if [[ "$file" == "tests/semantic/meta-fc-predicates-d1-mutant.lisp" ]]; then
      echo "::error::T5M_META_FC_MUTANT_ACCEPTED source=$file" >&2
      mark_file_failed
      return
    fi
    # Д11-позитив: точний SENS D1:YES, не успіх довільної відповіді.
    if [[ "$file" == "tests/semantic/meta-fc-predicates-d1-law.lisp" ]]; then
      printf '1\n' > "$dir/meta-fc-d1.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/meta-fc-d1.expected"; then
        echo "::error::T5M_META_FC_WRONG_POSITIVE source=$file expected=D1:1" >&2
        mark_file_failed
        return
      fi
    fi
    native_paired_executed_paths["$file"]=1
    if timeout "$native_timeout" "$binary" "$physical" \
        >"$dir/native-standalone.stdout" 2>"$dir/native-standalone.stderr"; then
      if ! cmp -s "$dir/native-standalone.stdout" "$dir/native-paired.stdout"; then
        echo "::error::T5M_NATIVE_EXECUTION_OUTPUT_DRIFT source=$file" >&2
        mark_file_failed
        return
      fi
      # Виконувані аксіоми: тільки D1:1, не структурне D3 () чи host truthiness.
      # Негативний змінений текст повинен дати саме D1:0 через SENS/Zig.
      if [[ "$file" == "lib/axioms-d1-principle-five.lisp" ]]; then
        printf '1\n' > "$dir/d1-true.expected"
        if ! cmp -s "$dir/native-standalone.stdout" "$dir/d1-true.expected"; then
          echo "::error::SENS_D1_AXIOMS_P5_WRONG_POSITIVE source=$file expected=D1:1 actual=$(cat "$dir/native-standalone.stdout")" >&2
          mark_file_failed
          return
        fi
        negative_source="$dir/axioms-mutant.lisp"
        negative_physical="$dir/axioms-mutant.sens"
        sed 's/(earth is a planet))))/(earth was a planet))))/' "$file" > "$negative_source"
        if cmp -s "$file" "$negative_source"; then
          echo "::error::SENS_D1_AXIOMS_P5_MUTANT_NOT_CREATED source=$file" >&2
          mark_file_failed
          return
        fi
        # Mint створює фізичний носій. Canonical bit-view генерує Zig open,
        # тому verify-view не має права перевіряти ще не створений перегляд.
        if ! timeout "$native_timeout" "$binary" --t5m-mint "$negative_source" "$negative_physical" >"$dir/axioms-negative-mint.out" 2>"$dir/axioms-negative-mint.err" ||
           ! timeout "$native_timeout" "$native_open" open "$negative_physical" >"${negative_physical%.sens}" 2>"$dir/axioms-negative-open.err" ||
           ! timeout "$native_timeout" "$native_open" verify-view "$negative_physical" >"$dir/axioms-negative-view.out" 2>"$dir/axioms-negative-view.err" ||
           ! timeout "$native_timeout" "$binary" --t5m-pair "$negative_source" "$negative_physical" >"$dir/axioms-negative-paired.out" 2>"$dir/axioms-negative-paired.err" ||
           ! timeout "$native_timeout" "$binary" "$negative_physical" >"$dir/axioms-negative-standalone.out" 2>"$dir/axioms-negative-standalone.err"; then
          echo "::error::SENS_D1_AXIOMS_P5_NEGATIVE_EXECUTION_FAILED source=$file" >&2
          for diagnostic in "$dir"/axioms-negative-*.err; do
            [[ -f "$diagnostic" ]] && sed 's/^/SENS negative: /' "$diagnostic" >&2
          done
          mark_file_failed
          return
        fi
        printf '0\n' > "$dir/d1-false.expected"
        if ! cmp -s "$dir/axioms-negative-paired.out" "$dir/d1-false.expected" ||
           ! cmp -s "$dir/axioms-negative-standalone.out" "$dir/d1-false.expected"; then
          echo "::error::SENS_D1_AXIOMS_P5_WRONG_NEGATIVE source=$file expected=D1:0 actual=$(cat "$dir/axioms-negative-standalone.out")" >&2
          mark_file_failed
          return
        fi
        echo "SENS_D1_AXIOMS_P5_EXECUTED_PASS source=$file positive=D1:1 mutant=D1:0 physical=ZIG_T5M native=SENS"
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
    # Негативний SENS-свідок повинен відмовити саме на невикличній формі.
    if [[ "$file" == "tests/semantic/meta-fc-predicates-d1-mutant.lisp" ]] &&
       (( status != 124 && status != 137 )) &&
       grep -Eq 'kind=(Type|InvalidForm)' "$dir/native-paired.stderr"; then
      echo "T5M_META_FC_NATIVE_MUTANT_REJECTED source=$file native=SENS"
      return
    fi
    sed 's/^/SENS native paired: /' "$dir/native-paired.stderr" >&2
    echo "::error::T5M_NATIVE_PAIRED_EXECUTION_FAIL source=$file status=$status release=NOT_CERTIFIED" >&2
    mark_file_failed
  fi
}
checked_files=0
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
  elif [[ "$file" == "tests/fixtures/island-lowering-1048-witness.lisp" ]]; then
    # Чотири зовнішні механізми вибирає SENS, не Python/JSON;
    # точні D24+ операнди переносяться Zig без рядкових літералів.
    binding_sources=(--binding-source lib/mechanism-selector.lisp --binding-source lib/island-lowering.lisp)
  elif [[ "$file" == "tests/fixtures/mechanism-selector-1047-witness.lisp" ]]; then
    # Іменовані SENS DEFINE механізмів походять із мовних бібліотек,
    # а не з вигаданих D9/D10 resident callables чи host-функцій.
    # Чинний селектор використовує тільки ратифіковану українську
    # проєкцію й паспорт допущених маршрутів, без плоского SID8 API.
    binding_sources=(--binding-source lib/mechanism-selector.lisp)
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
  elif [[ "$file" == "tests/semantic/meta-fc-predicates-d1-law.lisp" ||
          "$file" == "tests/semantic/meta-fc-predicates-d1-mutant.lisp" ]]; then
    binding_sources=(--binding-source lib/meta-eval-first-class.lisp)
  fi
  run_native_t5m_program
done < "$manifest"
printf 'T5M_CHANGED_SUMMARY files_checked=%s files_failed=%s native_view_roundtrip=%s native_paired_executed=%s native_standalone_parity=%s scope=changed_manifest semantic=NOT_CERTIFIED release=NOT_CERTIFIED\n' \
  "$checked_files" "$failed_files" \
  "${#native_view_roundtrip_paths[@]}" "${#native_paired_executed_paths[@]}" "${#native_standalone_parity_paths[@]}"
if (( failed_files > 0 )); then
  exit 2
fi
