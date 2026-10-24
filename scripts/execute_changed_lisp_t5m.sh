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
declare -A native_fragment_parity_paths=()
declare -A native_paired_executed_paths=()
declare -A native_standalone_parity_paths=()
# Успішний explicit Core4 є окремим фізичним класом, не bare SENS.
declare -A native_explicit_core4_parity_paths=()
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
  local -a paired_runtime_args=() standalone_runtime=("$binary") direct_runtime=("$binary")
  # D24+ корені «число-*» та мовна Д6 «довжина» створюються Core4;
  # профіль однаковий для парного й автономного фізичного виконання.
  case "$file" in
    tests/semantic/exact-arithmetic-laws.lisp|tests/semantic/exact-arithmetic-mutant.lisp|tests/semantic/d5-arithmetic-native-t5m-law.lisp|tests/semantic/d5-arithmetic-native-t5m-mutant.lisp|tests/semantic/d11-frequencies-key-order-law.lisp|tests/semantic/d11-frequencies-key-order-mutant.lisp|tests/semantic/d10-empty-queue-law.lisp|tests/semantic/d10-empty-queue-mutant.lisp|lib/lisp-fs.lisp)
      paired_runtime_args=(--core4-runtime)
      standalone_runtime=("$native_open" eval-core4)
      ;;
  esac
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

  # Частини Core4 — складові одного послідовного Lisp-завантаження, а не
  # незалежні програми. Для кожної окремо доведено T5M/бітову оберненість
  # і перевірено committed пару (якщо вона є); спільне виконання перевіряє
  # наявний Rust-тест t5m_core4_parts_load_sequentially_through_one_session.
  # Не називати відсутнє самостійне виконання PASS.
  if [[ "$file" == lib/core4-parts/*.lisp ]]; then
    if [[ -n "${failed_file_paths[$file]+present}" ]]; then
      return
    fi
    native_fragment_parity_paths["$file"]=1
    echo "::notice file=$file,title=SENS Core4 fragment::T5M_PARITY_ONLY source=$file standalone=NOT_APPLICABLE integrated=Rust-sequential-SENS"
    return
  fi

  # Типові негативні свідки: помилка Type є мовним результатом SENS,
  # а не провалом кодека. Zig спершу зберіг точні байти й перевірив roundtrip.
  # Названі випадки проходять і paired, і standalone; інша причина відмови — RED.
  local negative_type_diagnostic=""
  case "$file" in
    tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp|tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp)
      negative_type_diagnostic='domain identity is not callable under its ratified law: D1 ' ;;
    tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d3-eq-nonatom-type-negative.lisp)
      negative_type_diagnostic='eq expects two atoms' ;;
    tests/semantic/d4-not-nonpredicate-type-negative.lisp)
      negative_type_diagnostic='NOT requires an exact D1 PredicateBit' ;;
    tests/semantic/d3-cond-nil-condition-type-negative.lisp|tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp)
      negative_type_diagnostic='D3:110 COND expects exact D1:1 / D1:0' ;;
    tests/semantic/d3-car-empty-list-type-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/core-d3-car-cdr-cons-mutant.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-member-improper-hit-negative.lisp|tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-find-tail-improper-tail-negative.lisp|tests/semantic/d11-family-aggregation-mutant.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-span-improper-suffix-negative.lisp|tests/semantic/d11-srfi1-break-improper-suffix-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d6-union-improper-tail-negative.lisp|tests/semantic/d6-union-improper-root-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d3-car-atomic-dotted-tail-type-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d3-cdr-empty-list-type-negative.lisp)
      negative_type_diagnostic='cdr expects a non-empty list' ;;
    tests/semantic/d3-cdr-atom-type-negative.lisp)
      negative_type_diagnostic='cdr expects a non-empty list' ;;
    tests/semantic/d8-string-symbol-nontext-type-negative.lisp)
      negative_type_diagnostic='string->symbol expects a string' ;;
    tests/semantic/d8-contextual-d1-serialize-type-negative.lisp)
      negative_type_diagnostic='write-to-string cannot serialize contextual predicate results' ;;
  esac
  if [[ -n "$negative_type_diagnostic" ]]; then
    local rejection_status
    # Третій незалежний свідок: пряме українське Lisp-джерело.
    # Помилка Type має збігатися до і після фізичного Zig/T5M.
    # Залежний D11-свідок запускається з живим DEFINE, а не з host-оракулом.
    local direct_source="$file"
    if [[ "$file" == "tests/semantic/d11-srfi1-member-improper-hit-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp" ]]; then
      direct_source="$dir/d11-set-relations-bound-negative.lisp"
      cat -- lib/d11-srfi1-set-relations.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp" ||
            "$file" == "tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp" ]]; then
      direct_source="$dir/d11-filter-map-bound-negative.lisp"
      cat -- lib/d11-srfi1-filter-map.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp" ]]; then
      direct_source="$dir/d11-tree-test-bound-negative.lisp"
      cat -- lib/d11-tree-equal-by-test.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp" ]]; then
      direct_source="$dir/d11-find-presence-bound-negative.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-find-tail-improper-tail-negative.lisp" ]]; then
      direct_source="$dir/d11-find-tail-bound-negative.lisp"
      cat -- lib/d11-srfi1-find-tail.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-family-aggregation-mutant.lisp" ]]; then
      direct_source="$dir/d11-aggregation-bound-negative.lisp"
      cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d6-union-improper-tail-negative.lisp" ||
            "$file" == "tests/semantic/d6-union-improper-root-negative.lisp" ]]; then
      direct_source="$dir/d6-union-bound-negative.lisp"
      cat -- "$dir/d6-union-exact-binding.lisp" "$file" > "$direct_source"
    fi
    if timeout "$native_timeout" "${direct_runtime[@]}" "$direct_source" \
        >"$dir/native-direct.stdout" 2>"$dir/native-direct.stderr"; then
      echo "::error::T5M_EXPECTED_TYPE_DIRECT_ACCEPTED source=$file" >&2
      mark_file_failed
      return
    else
      rejection_status=$?
    fi
    if (( rejection_status == 124 || rejection_status == 137 )) ||
       ! grep -Fq "$negative_type_diagnostic" "$dir/native-direct.stderr"; then
      sed 's/^/SENS negative direct: /' "$dir/native-direct.stderr" >&2
      echo "::error::T5M_EXPECTED_TYPE_DIRECT_MISMATCH source=$file status=$rejection_status" >&2
      mark_file_failed
      return
    fi
    if timeout "$native_timeout" "$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}" \
        >"$dir/native-paired.stdout" 2>"$dir/native-paired.stderr"; then
      echo "::error::T5M_EXPECTED_TYPE_PAIRED_ACCEPTED source=$file" >&2
      mark_file_failed
      return
    else
      rejection_status=$?
    fi
    if (( rejection_status == 124 || rejection_status == 137 )) ||
       ! grep -Fq "$negative_type_diagnostic" "$dir/native-paired.stderr" ||
       ! grep -Fq 'kind=Type' "$dir/native-paired.stderr"; then
      sed 's/^/SENS negative paired: /' "$dir/native-paired.stderr" >&2
      echo "::error::T5M_EXPECTED_TYPE_PAIRED_MISMATCH source=$file status=$rejection_status" >&2
      mark_file_failed
      return
    fi
    if timeout "$native_timeout" "$binary" "$physical" \
        >"$dir/native-standalone.stdout" 2>"$dir/native-standalone.stderr"; then
      echo "::error::T5M_EXPECTED_TYPE_STANDALONE_ACCEPTED source=$file" >&2
      mark_file_failed
      return
    else
      rejection_status=$?
    fi
    # D11-бібліотечне DEFINE передається як binding-source для парного
    # виконання, але не є частиною автономного файла. Тому standalone
    # може чесно відхилити невідому D7-проєкцію імені, ще не дійшовши
    # до тестованої помилки Type. Це не семантичний PASS: прямий та
    # парний SENS уже мають збігтися з точним Type-діагнозом вище.
    if (( ${#binding_sources[@]} != 0 )) &&
       { grep -Fq 'unknown Text7 binding:' "$dir/native-standalone.stderr" ||
         { [[ "$file" == "tests/semantic/d11-srfi1-member-improper-hit-negative.lisp" ||
              "$file" == "tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp" ]] &&
           grep -Fq 'domain identity is not callable under its ratified law: D7 ' "$dir/native-standalone.stderr"; }; }; then
      native_paired_executed_paths["$file"]=1
      echo "::notice file=$file,title=SENS negative Type::PASS direct=REJECTED paired=REJECTED standalone=NOT_APPLICABLE reason=external-D11-binding diagnostic=$negative_type_diagnostic"
      return
    fi
    if (( rejection_status == 124 || rejection_status == 137 )) ||
       ! grep -Fq "$negative_type_diagnostic" "$dir/native-standalone.stderr"; then
      sed 's/^/SENS negative standalone: /' "$dir/native-standalone.stderr" >&2
      echo "::error::T5M_EXPECTED_TYPE_STANDALONE_MISMATCH source=$file status=$rejection_status" >&2
      mark_file_failed
      return
    fi
    # У випадках, де standalone має всі зв'язування, три шляхи
    # відхиляються незалежно з однаковою очікуваною Type-помилкою.
    native_paired_executed_paths["$file"]=1
    native_standalone_parity_paths["$file"]=1
    echo "::notice file=$file,title=SENS negative Type::PASS physical=Zig/T5M direct=REJECTED paired=REJECTED standalone=REJECTED diagnostic=$negative_type_diagnostic"
    return
  fi

  # Критичний доказ — реальне парне виконання фізичних Zig-байтів.
  if timeout "$native_timeout" "$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}" "${paired_runtime_args[@]}" \
      >"$dir/native-paired.stdout" 2>"$dir/native-paired.stderr"; then
    if [[ "$file" == "tests/semantic/meta-fc-predicates-d1-mutant.lisp" ]]; then
      echo "::error::T5M_META_FC_MUTANT_ACCEPTED source=$file" >&2
      mark_file_failed
      return
    fi
    # Точна арифметика: сам Lisp завершує D1, shell лише порівнює
    # фактичний SENS-вердикт 1/0 після фізичного Zig/T5M.
    if [[ "$file" == "tests/semantic/exact-arithmetic-laws.lisp" ||
          "$file" == "tests/semantic/exact-arithmetic-mutant.lisp" ]]; then
      local expected_exact_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_exact_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_exact_d1" ]]; then
        echo "::error::T5M_EXACT_ARITHMETIC_WRONG_D1 source=$file layer=sens-paired expected=$expected_exact_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
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
    # Обидва епістемічні свідки перевіряють named record самим Lisp/D8.
    # Зовнішній вердикт позитиву й мутанта — точний D1:1, а не текстовий dump.
    if [[ "$file" == "tests/semantic/language-law-epistemic-records.lisp" ]]; then
      printf '1\n' > "$dir/epistemic-law.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/epistemic-law.expected"; then
        echo "::error file=$file,title=SENS epistemic law::WRONG_D1 expected=1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "::notice file=$file,title=SENS epistemic law::PASS native=SENS result=D1:1 carrier=Zig/T5M"
    elif [[ "$file" == tests/semantic/language-law-*.lisp ||
            "$file" == "tests/semantic/lisp-d4-lexical-closure-laws.lisp" ]]; then
      printf '1\n' > "$dir/language-d1.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/language-d1.expected"; then
        echo "::error file=$file,title=SENS language law::WRONG_D1 expected=1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "::notice file=$file,title=SENS language law::PASS native=SENS result=D1:1 carrier=Zig/T5M"
    fi
    # Мутант перевіряє named fail-record всередині Lisp та теж має D1:1,
    # коли реалізація правильно виявляє хибне твердження.
    if [[ "$file" == "tests/semantic/language-mutant-epistemic-records.lisp" ]]; then
      printf '1\n' > "$dir/epistemic-mutant.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/epistemic-mutant.expected"; then
        echo "::error file=$file,title=SENS epistemic mutant::WRONG_D1 expected=1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "::notice file=$file,title=SENS epistemic mutant::PASS native=SENS result=D1:1 fail-record-verified=YES carrier=Zig/T5M"
    elif [[ "$file" == tests/semantic/language-mutant-*.lisp ]]; then
      printf '0\n' > "$dir/language-d1-mutant.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/language-d1-mutant.expected"; then
        echo "::error file=$file,title=SENS language mutant::WRONG_D1 expected=0 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "::notice file=$file,title=SENS language mutant::PASS native=SENS result=D1:0 carrier=Zig/T5M"
    fi
    # Закони CAR/CDR/CONS/COND/NULL належать виконуваному Lisp.
    # Shell порівнює тільки кінцевий точний D1-біт нативного SENS.
    # Це не стороння модель EQ, COND або структурних правил.
    case "$file" in
      tests/semantic/ukr-d3-pair-identity-law.lisp|tests/semantic/ukr-d3-cond-control-law.lisp|tests/semantic/ukr-d3-structural-selftest.lisp|tests/semantic/d11-clojure-juxt-laws.lisp|tests/semantic/d11-srfi1-span-break-laws.lisp|tests/semantic/d11-srfi1-find-tail-laws.lisp|tests/semantic/d11-family-aggregation-law.lisp)
        echo 1 > "$dir/ukr-d3-law.expected"
        if ! cmp -s "$dir/native-paired.stdout" "$dir/ukr-d3-law.expected"; then
          echo "::error::SENS_LISP_SEMANTIC_LAW_WRONG_D1 source=$file expected=D1:1 actual=$(cat "$dir/native-paired.stdout")" >&2
          mark_file_failed
          return
        fi
        echo "SENS_LISP_SEMANTIC_LAW_PASS source=$file result=D1:1 oracle=SENS carrier=ZIG_T5M"
        ;;
    esac
    # Нативні Д3/Д5 закони та мутанти: вердикт формулює Lisp,
    # Zig пакує, SENS виконує фізичний T5M, Shell лише звіряє D1.
    case "$file" in
      tests/semantic/d5-arithmetic-native-t5m-law.lisp|tests/semantic/d5-arithmetic-native-t5m-mutant.lisp|tests/semantic/d3-structural-native-t5m-law.lisp|tests/semantic/d3-structural-native-t5m-mutant.lisp|tests/semantic/d3-proper-tail-hot-law.lisp|tests/semantic/d3-proper-tail-hot-mutant.lisp|tests/semantic/d3-structural-bench-law.lisp|tests/semantic/d3-structural-bench-mutant.lisp)
        local_expected=1
        if [[ "$file" == *-mutant.lisp ]]; then
          local_expected=0
        fi
        printf '%s\n' "$local_expected" > "$dir/d5-language.expected"
        if ! cmp -s "$dir/native-paired.stdout" "$dir/d5-language.expected"; then
          echo "::error file=$file,title=SENS D3/D5 language::REGRESSION layer=semantics expected=D1:$local_expected actual=$(cat "$dir/native-paired.stdout")" >&2
          mark_file_failed
          return
        fi
        echo "::notice file=$file,title=SENS D3/D5 language::PASS native=SENS carrier=Zig/T5M result=D1:$local_expected"
        ;;
    esac
    # Свідки D11: кінцева мовна істина належить тільки виконанню SENS.
    case "$file" in
      tests/semantic/d11-srfi1-unfold-positive.lisp|tests/semantic/d11-srfi1-unfold-mutant.lisp)
        d11_unfold_expected=1
        [[ "$file" != *-mutant.lisp ]] || d11_unfold_expected=0
        printf '%s\n' "$d11_unfold_expected" > "$dir/d11-unfold.expected"
        if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-unfold.expected"; then
          echo "::error::SENS_D11_UNFOLD_WRONG_D1 source=$file expected=D1:$d11_unfold_expected actual=$(cat "$dir/native-paired.stdout")" >&2
          mark_file_failed
          return
        fi
        echo "SENS_D11_UNFOLD_EXECUTED_PASS source=$file result=D1:$d11_unfold_expected carrier=Zig/T5M"
        ;;
    esac
    # D6 UNION: підтвердження точних D1 свідків, не host-оракул.
    if [[ "$file" == "tests/semantic/d6-union-proper-law.lisp" ||
          "$file" == "tests/semantic/d6-union-proper-mutant.lisp" ]]; then
      d6_union_expected=1
      [[ "$file" != *-mutant.lisp ]] || d6_union_expected=0
      printf '%s\n' "$d6_union_expected" > "$dir/d6-union.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d6-union.expected"; then
        echo "::error::SENS_D6_UNION_WRONG_D1 source=$file expected=D1:$d6_union_expected actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "SENS_D6_UNION_EXECUTED_PASS source=$file result=D1:$d6_union_expected carrier=Zig/T5M"
    fi
    # Принцип 5: дві РІЗНІ фізичні форми того самого обчислення.
    # 1) живий український Lisp, без T5M; 2) точні байти Zig/T5M,
    # виконані SENS після контролю оборотності. Ніякого Python-оракула.
    if [[ "$file" == "tests/semantic/core1-gc-reachability-laws.lisp" ]]; then
      printf '1\n' > "$dir/core1-gc-d1.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/core1-gc-d1.expected"; then
        echo "::error::CORE1_GC_PAIRED_WRONG_D1 expected=1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      cat -- lib/core1.lisp "$file" > "$dir/core1-gc-direct.lisp"
      if ! timeout "$native_timeout" "$binary" "$dir/core1-gc-direct.lisp" \
          >"$dir/core1-gc-direct.stdout" 2>"$dir/core1-gc-direct.stderr"; then
        sed 's/^/Core1 direct SENS: /' "$dir/core1-gc-direct.stderr" >&2
        echo "::error::CORE1_GC_DIRECT_EXECUTION_FAIL" >&2
        mark_file_failed
        return
      fi
      if ! cmp -s "$dir/core1-gc-direct.stdout" "$dir/native-paired.stdout"; then
        echo "::error::CORE1_GC_TWO_CARRIERS_DIVERGED source=$file" >&2
        mark_file_failed
        return
      fi
      # Справжній негатив: змінимо фінальне Д1-питання, обидва SENS
      # шляхи мають повернути 0 (а не просто exit=0).
      sed '$c\(хибне? (атом? (як-є ())))' "$file" > "$dir/core1-gc-negative.lisp"
      if cmp -s "$file" "$dir/core1-gc-negative.lisp"; then
        echo "::error::CORE1_GC_MUTANT_NOT_CREATED" >&2
        mark_file_failed
        return
      fi
      cat -- lib/core1.lisp "$dir/core1-gc-negative.lisp" > "$dir/core1-gc-negative-direct.lisp"
      if ! timeout "$native_timeout" "$binary" "$dir/core1-gc-negative-direct.lisp" \
          >"$dir/core1-gc-negative-direct.stdout" 2>"$dir/core1-gc-negative-direct.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint-pair \
          "$dir/core1-gc-negative.lisp" "$dir/core1-gc-negative.sens" \
          --binding-source lib/core1.lisp >"$dir/core1-gc-negative-mint.stdout" 2>"$dir/core1-gc-negative-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view \
          "$dir/core1-gc-negative.sens" >"$dir/core1-gc-negative-view.stdout" 2>"$dir/core1-gc-negative-view.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-pair \
          "$dir/core1-gc-negative.lisp" "$dir/core1-gc-negative.sens" \
          --binding-source lib/core1.lisp >"$dir/core1-gc-negative-paired.stdout" 2>"$dir/core1-gc-negative-paired.stderr"; then
        echo "::error::CORE1_GC_NEGATIVE_EXECUTION_FAIL source=$file" >&2
        for diagnostic in "$dir"/core1-gc-negative*.stderr; do
          [[ -f "$diagnostic" ]] && sed 's/^/Core1 negative: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      printf '0\n' > "$dir/core1-gc-d0.expected"
      if ! cmp -s "$dir/core1-gc-negative-direct.stdout" "$dir/core1-gc-d0.expected" ||
         ! cmp -s "$dir/core1-gc-negative-paired.stdout" "$dir/core1-gc-d0.expected"; then
        echo "::error::CORE1_GC_NEGATIVE_D1_MISMATCH expected=0" >&2
        mark_file_failed
        return
      fi
      echo "CORE1_GC_TWO_CARRIERS_PASS source=$file direct=LISP physical=T5M native=SENS positive=D1:1 negative=D1:0 GC=SYMBOLIC_REACHABILITY_ONLY"
    fi
    native_paired_executed_paths["$file"]=1
    # Модульний Lisp-свідок має право звертатися до DEFINE лише після
    # їх завантаження. Source-only T5M є точним кодом свідка, але НЕ
    # самодостатньою програмою: у standalone немає його D10-зв'язувань.
    # Для двох D3-законів виконуємо окремий САМОДОСТАТНІЙ фізичний
    # носій із тим самим чинним джерелом визначень. Жодного mock/host oracle.
    local standalone_physical="$physical"
    if [[ "$file" == "tests/semantic/d6-any-all-first-class-law.lisp" ||
          "$file" == "tests/semantic/d6-any-all-first-class-mutant.lisp" ]]; then
      # Автономний фізичний носій повинен містити ДВА реальні DEFINE
      # з Core4 та власний SENS-свідок. Source-only D6 не є викличним.
      local d6_complete_source="$dir/d6-any-all-full.lisp"
      standalone_physical="$dir/d6-any-all-full.sens"
      if ! cat -- tests/fixtures/epistemic-d1-names.lisp "$local_d6_source" "$file" > "$d6_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$d6_complete_source" "$standalone_physical" >"$dir/d6-complete-mint.stdout" 2>"$dir/d6-complete-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d6-complete-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d6-complete-inverse.stdout" 2>"$dir/d6-complete-inverse.stderr"; then
        echo "::error::T5M_D6_DEPENDENCY_COMPLETE_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "lib/persistent-vector.lisp" ]]; then
      # Автономний SENS повинен одержати ті самі чинні Lisp-корені D24+,
      # що й парне виконання; source-only носій лишається для byte-parity.
      local vector_complete_source="$dir/vector-dependency-complete.lisp"
      standalone_physical="$dir/vector-dependency-complete.sens"
      if ! cat -- "$vector_math_roots" "$file" > "$vector_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$vector_complete_source" "$standalone_physical" \
           >"$dir/vector-complete-mint.stdout" 2>"$dir/vector-complete-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
           >"${standalone_physical%.sens}" 2>"$dir/vector-complete-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
           >"$dir/vector-complete-verify.stdout" 2>"$dir/vector-complete-verify.stderr"; then
        for diagnostic in "$dir/vector-complete-mint.stderr" "$dir/vector-complete-open.stderr" "$dir/vector-complete-verify.stderr"; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/SENS vector dependency bundle: /' "$diagnostic" >&2
        done
        echo "::error::T5M_VECTOR_DEPENDENCY_COMPLETE_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/language-law-epistemic-records.lisp" ||
          "$file" == "tests/semantic/language-mutant-epistemic-records.lisp" ]]; then
      local epistemic_complete_source="$dir/epistemic-dependency-complete.lisp"
      standalone_physical="$dir/epistemic-dependency-complete.sens"
      cat -- lib/unify.lisp lib/reason.lisp lib/forward.lisp lib/knowledge.lisp \
        lib/persistent-map.lisp lib/persistent-vector.lisp lib/time.lisp lib/epistemic.lisp \
        tests/fixtures/witness-runner.lisp tests/fixtures/epistemic-authority-witness.lisp "$file" > "$epistemic_complete_source"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$epistemic_complete_source" "$standalone_physical" \
          >"$dir/epistemic-mint.stdout" 2>"$dir/epistemic-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
          >"${standalone_physical%.sens}" 2>"$dir/epistemic-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
          >"$dir/epistemic-verify.stdout" 2>"$dir/epistemic-verify.stderr"; then
        for diagnostic in "$dir/epistemic-mint.stderr" "$dir/epistemic-open.stderr" "$dir/epistemic-verify.stderr"; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/SENS epistemic dependency bundle: /' "$diagnostic" >&2
        done
        echo "::error::T5M_EPISTEMIC_DEPENDENCY_BUNDLE_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/result-status-proper-list-d3-law.lisp" ||
          "$file" == "tests/semantic/result-status-proper-list-d3-mutant.lisp" ]]; then
      local complete_source="$dir/dependency-complete.lisp"
      standalone_physical="$dir/dependency-complete.sens"
      cat -- lib/result-status.lisp "$file" > "$complete_source"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$complete_source" "$standalone_physical" \
          >"$dir/dependency-mint.stdout" 2>"$dir/dependency-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
          >"$dir/dependency-complete" 2>"$dir/dependency-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
          >"$dir/dependency-verify.stdout" 2>"$dir/dependency-verify.stderr"; then
        for diagnostic in "$dir/dependency-mint.stderr" "$dir/dependency-open.stderr" "$dir/dependency-verify.stderr"; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/SENS dependency-complete: /' "$diagnostic" >&2
        done
        echo "::error::T5M_DEPENDENCY_COMPLETE_MINT_OR_ROUNDTRIP_FAIL source=$file" >&2
        mark_file_failed
        return
      fi
      local expected_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_d1" ]]; then
        echo "::error::T5M_DEPENDENCY_PAIRED_WRONG_D1 source=$file expected=$expected_d1" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-frequencies-key-order-law.lisp" ||
          "$file" == "tests/semantic/d11-frequencies-key-order-mutant.lisp" ]]; then
      # Повний standalone носій мусить містити ті самі SENS DEFINE,
      # що були передані paired evaluator; source-only файл ними не володіє.
      local frequencies_complete_source="$dir/d11-frequencies-full.lisp"
      standalone_physical="$dir/d11-frequencies-full.sens"
      if ! cat -- lib/d11-clojure-group-by.lisp lib/d11-clojure-frequencies-unary.lisp "$file" > "$frequencies_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$frequencies_complete_source" "$standalone_physical" \
             >"$dir/d11-frequencies-mint.stdout" 2>"$dir/d11-frequencies-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
             >"${standalone_physical%.sens}" 2>"$dir/d11-frequencies-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
             >"$dir/d11-frequencies-verify.stdout" 2>"$dir/d11-frequencies-verify.stderr"; then
        echo "::error::D11_FREQUENCIES_PHYSICAL_STANDALONE_MINT_FAILED source=$file layer=zig-t5m" >&2
        for diagnostic in "$dir"/d11-frequencies-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 FREQUENCIES: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_frequencies_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_frequencies_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_frequencies_d1" ]]; then
        echo "::error::D11_FREQUENCIES_WRONG_PAIRED_VERDICT source=$file expected=$expected_frequencies_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-find-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-presence-mutant.lisp" ]]; then
      # Самодостатній SENS-носій: ті самі DEFINE та той самий мовний свідок,
      # без вигаданого виконавця на Rust або повторної семантики на Zig.
      local presence_complete_source="$dir/d11-find-presence-full.lisp"
      standalone_physical="$dir/d11-find-presence-full.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp "$file" > "$presence_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$presence_complete_source" "$standalone_physical" \
              >"$dir/d11-find-presence-mint.stdout" 2>"$dir/d11-find-presence-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
              >"${standalone_physical%.sens}" 2>"$dir/d11-find-presence-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
              >"$dir/d11-find-presence-verify.stdout" 2>"$dir/d11-find-presence-verify.stderr"; then
        echo "::error::D11_FIND_PRESENCE_STANDALONE_MINT_FAILED source=$file layer=zig-t5m" >&2
        for diagnostic in "$dir"/d11-find-presence-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 FIND-PRESENCE: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_presence_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_presence_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_presence_d1" ]]; then
        echo "::error::D11_FIND_PRESENCE_WRONG_PAIRED_VERDICT source=$file expected=D1:$expected_presence_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-filter-map-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-filter-map-mutant.lisp" ]]; then
      # Повний фізичний носій має містити ті самі чинні SENS DEFINE,
      # що пройшли парний T5M. Інакше голий .sens виклик дає UnknownSymbol.
      local filter_map_complete_source="$dir/d11-filter-map-full.lisp"
      standalone_physical="$dir/d11-filter-map-full.sens"
      if ! cat -- lib/d11-srfi1-filter-map.lisp "$file" >"$filter_map_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$filter_map_complete_source" "$standalone_physical" \
              >"$dir/d11-filter-map-mint.stdout" 2>"$dir/d11-filter-map-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
              >"${standalone_physical%.sens}" 2>"$dir/d11-filter-map-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
              >"$dir/d11-filter-map-verify.stdout" 2>"$dir/d11-filter-map-verify.stderr"; then
        echo "::error::D11_FILTER_MAP_STANDALONE_MINT_FAILED source=$file layer=zig-t5m" >&2
        for diagnostic in "$dir"/d11-filter-map-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 FILTER-MAP: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_filter_map_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_filter_map_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_filter_map_d1" ]]; then
        echo "::error::D11_FILTER_MAP_WRONG_PAIRED_VERDICT source=$file expected=D1:$expected_filter_map_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-tree-equal-by-test-law.lisp" ||
          "$file" == "tests/semantic/d11-tree-equal-by-test-mutant.lisp" ]]; then
      # Фізична самодостатність: одна й та сама SENS-бібліотека + SENS-свідок.
      # Host тільки збирає джерело та звіряє точний D1; ніякого host-оракула.
      local tree_complete_source="$dir/d11-tree-test-full.lisp"
      standalone_physical="$dir/d11-tree-test-full.sens"
      if ! cat -- lib/d11-tree-equal-by-test.lisp "$file" >"$tree_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$tree_complete_source" "$standalone_physical" \
              >"$dir/d11-tree-test-mint.stdout" 2>"$dir/d11-tree-test-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
              >"${standalone_physical%.sens}" 2>"$dir/d11-tree-test-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
              >"$dir/d11-tree-test-verify.stdout" 2>"$dir/d11-tree-test-verify.stderr"; then
        echo "::error::D11_TREE_TEST_PHYSICAL_STANDALONE_MINT_FAILED source=$file layer=zig-t5m" >&2
        for diagnostic in "$dir"/d11-tree-test-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 TREE-TEST: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_tree_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_tree_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_tree_d1" ]]; then
        echo "::error::D11_TREE_TEST_WRONG_VERDICT source=$file layer=sens-paired expected=D1:$expected_tree_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if timeout "$native_timeout" "${standalone_runtime[@]}" "$standalone_physical" \
        >"$dir/native-standalone.stdout" 2>"$dir/native-standalone.stderr"; then
      if ! cmp -s "$dir/native-standalone.stdout" "$dir/native-paired.stdout"; then
        echo "::error::T5M_NATIVE_EXECUTION_OUTPUT_DRIFT source=$file" >&2
        mark_file_failed
        return
      fi
      # Lisp-свідок сам визначає кожен закон і завершує D1:1.
      # Хост звіряє лише точний фізичний результат після Zig/T5M + SENS.
      if [[ "$file" == "tests/semantic/lisp-d3-d4-list-self-verdict.lisp" ]]; then
        printf '1\n' > "$dir/lisp-d3-d4-self-verdict.expected"
        if ! cmp -s "$dir/native-standalone.stdout" "$dir/lisp-d3-d4-self-verdict.expected"; then
          echo "::error file=$file,title=SENS Lisp D3/D4::REGRESSION id=d3-d4-list-self-verdict layer=semantics expected=D1:1 actual=$(cat "$dir/native-standalone.stdout")" >&2
          mark_file_failed
          return
        fi
        echo "::notice file=$file,title=SENS Lisp D3/D4::PASS id=d3-d4-list-self-verdict physical=Zig/T5M semantic=SENS result=D1:1"
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
        # Нові аксіоми містять також свідки GC після текстового закону.
        # Заміна раннього прикладу не змінює останній результат: він лишається 1.
        # Запитати НЕГАТИВНИЙ закон у самому SENS останньою формою,
        # на тому самому джерелі з усіма нинішніми визначеннями.
        cat -- "$file" > "$negative_source"
        cat >> "$negative_source" <<'SENS_D1_NEGATIVE'
(перевірити-принцип-п'ять
 (принцип-п'ять-факт (як-є (earth was a planet))))
SENS_D1_NEGATIVE
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
      if [[ "$standalone_physical" == "$physical" ]]; then
        # eval-core4 виконує фізичні байти, але це НЕ голий CLI `sens FILE.sens`.
        # Зараховувати bare-паритет і передавати до бенчмарка можна лише
        # тоді, коли той самий committed носій запускав безпосередньо sens.
        if [[ "${standalone_runtime[0]}" == "$binary" ]]; then
          native_standalone_parity_paths["$file"]=1
          if [[ -f "$committed" && ! -L "$committed" ]] && cmp -s "$physical" "$committed"; then
            printf '%s\n' "$committed" >> "$benchmark_manifest"
          fi
          echo "T5M_NATIVE_STANDALONE_AND_PAIRED_PASS source=$file physical=ZIG_VERIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
        else
          native_explicit_core4_parity_paths["$file"]=1
          echo "T5M_NATIVE_EXPLICIT_CORE4_PAIRED_PASS source=$file runner=sens-trit/eval-core4 bare=NOT_TESTED physical=ZIG_VERIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
        fi
      else
        # Самодостатній носій містить Lisp-залежності, committed source-only — ні.
        # Не віддавати неперевірений source-only файл фізичному бенчмарку.
        echo "T5M_NATIVE_DEPENDENCY_COMPLETE_AND_PAIRED_PASS source=$file physical=ZIG_VERIFIED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
      fi
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
  if [[ "$file" == "lib/persistent-vector.lisp" ||
        "$file" == "lib/reason.lisp" || "$file" == "lib/knowledge.lisp" ]]; then
    # Вектор, міркування й знання використовують мовні корені D24+ з Core4.
    # Витягаємо рівно ці два DEFINE з канонічного джерела, без копії закону.
    vector_math_roots="$dir/core4-d24-roots.lisp"
    if ! awk '
      /^\(визначити число-нуль 0\)$/ { zero++; print; next }
      /^\(визначити число-один 1\)$/ { one++; print; next }
      END { if (zero != 1 || one != 1) exit 2 }
    ' lib/core4-parts/core4-language.lisp > "$vector_math_roots"; then
      echo "::error::VECTOR_D24_ROOTS_NOT_ISOLATABLE source=lib/core4-parts/core4-language.lisp expected=two-exact-definitions" >&2
      mark_file_failed
      continue
    fi
    binding_sources=(--binding-source "$vector_math_roots")
    if [[ "$file" == "lib/reason.lisp" ]]; then
      # Reason додатково потребує чинного мовного DEFINE уніфікатора.
      binding_sources+=(--binding-source lib/unify.lisp)
    fi
  elif [[ "$file" == "lib/forward.lisp" ]]; then
    # Чинний D9 уніфікатор визначено в українському Lisp, не в самій таблиці.
    binding_sources=(--binding-source lib/unify.lisp)
  elif [[ "$file" == "tests/semantic/result-status-d7-label-law.lisp" ||
          "$file" == "tests/semantic/result-status-d7-label-mutant.lisp" ||
          "$file" == "tests/semantic/result-status-dotted-law.lisp" ||
          "$file" == "tests/semantic/result-status-dotted-mutant.lisp" ||
          "$file" == "tests/semantic/result-status-proper-list-d3-law.lisp" ||
          "$file" == "tests/semantic/result-status-proper-list-d3-mutant.lisp" ||
          "$file" == "tests/semantic/result-status-goal-tags-law.lisp" ||
          "$file" == "tests/semantic/result-status-goal-tags-mutant.lisp" ]]; then
    # Мовний закон міток вимагає справжніх визначень Result Status.
    # SENS визначає D1, Zig пакує фізичні слова, Rust тільки запускає.
    binding_sources=(--binding-source lib/result-status.lisp)
  elif [[ "$file" == "tests/semantic/language-law-epistemic-records.lisp" ||
          "$file" == "tests/semantic/language-mutant-epistemic-records.lisp" ]]; then
    # Епістемічні закони належать Lisp; спершу завантажуються їхні реальні DEFINE-залежності.
    binding_sources=(--binding-source lib/unify.lisp
                     --binding-source lib/reason.lisp
                     --binding-source lib/forward.lisp
                     --binding-source lib/knowledge.lisp
                     --binding-source lib/persistent-map.lisp
                     --binding-source lib/persistent-vector.lisp
                     --binding-source lib/time.lisp
                     --binding-source lib/epistemic.lisp
                     --binding-source tests/fixtures/witness-runner.lisp
                     --binding-source tests/fixtures/epistemic-authority-witness.lisp)
  elif [[ "$file" == "tests/semantic/utf8-boundary-laws.lisp" ||
          "$file" == "tests/semantic/utf8-boundary-mutant.lisp" ||
          "$file" == "tests/semantic/utf8-quotient-laws.lisp" ||
          "$file" == "tests/semantic/utf8-quotient-mutant.lisp" ||
          "$file" == "tests/semantic/utf8-numeric-foundations-law.lisp" ||
          "$file" == "tests/semantic/utf8-numeric-foundations-mutant.lisp" ]]; then
    # Усі UTF-8 закони/мутанти викликають DEFINE зі справжньої Lisp-бібліотеки.
    # Без неї фізичний SENS бачить невизначену D7-голову, а не мовний закон.
    # Числові тотожності залишаються точними D24+ значеннями.
    binding_sources=(--binding-source lib/utf8.lisp)
  elif [[ "$file" == "tests/semantic/d3-structural-bench-law.lisp" ||
          "$file" == "tests/semantic/d3-structural-bench-mutant.lisp" ]]; then
    # D3 закон і мутант потребують точних Lisp DEFINE з відповідного бенчмарку.
    # Не дублюємо їх у Zig або Rust: фізичне виконання має бути SENS.
    binding_sources=(--binding-source benchmarks/d3-structural-bench.lisp)
  elif [[ "$file" == "tests/semantic/d3-proper-tail-hot-law.lisp" ||
          "$file" == "tests/semantic/d3-proper-tail-hot-mutant.lisp" ]]; then
    # Нові D3-свідки викликають ОБІЙТИ-ПОВНИЙ-СПИСОК з реального Lisp-бенчмарку.
    # Mint і paired мусять завантажити його чинне DEFINE, інакше отримуємо
    # хибний UnknownSymbol замість мовного D1:1 / D1:0. Rust/Zig не оракули.
    binding_sources=(--binding-source benchmarks/d3-proper-tail-hot.lisp)
  elif [[ "$file" == "tests/semantic/d11-frequencies-key-order-law.lisp" ||
          "$file" == "tests/semantic/d11-frequencies-key-order-mutant.lisp" ]]; then
    # D11 FREQUENCIES: той самий явний SENS-профіль, що й законодавчий раннер.
    # Без GROUP-BY/унарної FREQUENCIES парний evaluator бачить невідомий Text7.
    binding_sources=(--binding-source lib/d11-clojure-group-by.lisp
                     --binding-source lib/d11-clojure-frequencies-unary.lisp)
  elif [[ "$file" == "tests/semantic/d11-tree-equal-by-test-law.lisp" ||
          "$file" == "tests/semantic/d11-tree-equal-by-test-mutant.lisp" ||
          "$file" == "tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp" ]]; then
    # F11-TREE-TEST: точний D11-кандидат — викличне Lisp-визначення,
    # Zig транспортує слова, а SENS сам обчислює D1 позитив/мутант.
    binding_sources=(--binding-source lib/d11-tree-equal-by-test.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp" ]]; then
    # Джерело чинної D11-композиції: Zig транспортує, SENS виконує Type.
    binding_sources=(--binding-source lib/d11-srfi1-filter-map.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-find-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-presence-mutant.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp" ]]; then
    # Існуюче SENS-визначення ідентичне для direct, paired і повного файла.
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-filter-map-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-filter-map-mutant.lisp" ]]; then
    # Д11 FILTER-MAP: після зміни окремого свідка Mint/Pair мають
    # отримати ті самі чинні SENS DEFINE, що й повний semantic law runner.
    # Інакше UnknownSymbol D7 тестує відсутнє зв'язування, не D1/D3 закон.
    binding_sources=(--binding-source lib/d11-srfi1-filter-map.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-unfold-positive.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-unfold-mutant.lisp" ]]; then
    # SENS визначає UNFOLD/UNFOLD-RIGHT у бібліотеці, яку фізично
    # додаємо до mint/paired, замість допуску невідомого Text7 імені.
    binding_sources=(--binding-source lib/d11-srfi1-unfold.lisp)
  elif [[ "$file" == "tests/semantic/d6-union-proper-law.lisp" ||
          "$file" == "tests/semantic/d6-union-proper-mutant.lisp" ||
          "$file" == "tests/semantic/d6-union-improper-tail-negative.lisp" ||
          "$file" == "tests/semantic/d6-union-improper-root-negative.lisp" ]]; then
    # Д6 UNION: виділити чинні SENS-визначення, не створювати host-функцію.
    # Обидва маршрути mint/paired мусять отримати ту саму послідовність DEFINE.
    d6_union_binding="$dir/d6-union-exact-binding.lisp"
    : > "$d6_union_binding"
    for spec in 'lib/core4-parts/core4-language.lisp|значення-у-списку?' 'lib/core4-parts/core4-codec.lisp|об'"'"'єднання'; do
      d6_union_file="${spec%%|*}"
      d6_union_name="${spec#*|}"
      if ! awk -v target="(визначити $d6_union_name" '
        $0 == target { if (found++) exit 2; copying = 1 }
        copying && NF == 0 { copying = 0; complete++; next }
        copying { print }
        END { if (found != 1 || complete != 1 || copying) exit 2 }
      ' "$d6_union_file" >> "$d6_union_binding"; then
        echo "::error::T5M_D6_UNION_BINDING_NOT_ISOLATABLE source=$file definition=$d6_union_name" >&2
        mark_file_failed
        continue 2
      fi
      printf '\n' >> "$d6_union_binding"
    done
    binding_sources=(--binding-source "$d6_union_binding")
  elif [[ "$file" == "tests/semantic/d11-set-proper-d3-empty-law.lisp" ||
          "$file" == "tests/semantic/d11-set-proper-d3-empty-mutant.lisp" ]]; then
    # Форму списку визначає SENS-бібліотека, не транспорт і не хост.
    binding_sources=(--binding-source lib/d11-srfi1-set-relations.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-set-relations-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-set-relations-mutant.lisp" ]]; then
    # D11-множини: SENS-функції бере лише з чинного бібліотечного джерела.
    binding_sources=(--binding-source lib/d11-srfi1-set-relations.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-member-improper-hit-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp" ]]; then
    # Правильність структури множини доводять DEFINE із SENS-бібліотеки.
    binding_sources=(--binding-source lib/d11-srfi1-set-relations.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-find-tail-laws.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-tail-improper-tail-negative.lisp" ]]; then
    # Лише визначення із справжньої бібліотеки SENS, без host-оракула.
    binding_sources=(--binding-source lib/d11-srfi1-find-tail.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-span-break-laws.lisp" ]]; then
    # SENS визначає мову; Zig лише переносить біти фізичного T5M.
    binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp)
  elif [[ "$file" == "tests/semantic/d11-clojure-partition-by-laws.lisp" ||
          "$file" == "tests/semantic/d11-clojure-partition-by-d7-parity.lisp" ||
          "$file" == "tests/semantic/d11-clojure-dedupe-laws.lisp" ]]; then
    # Порядок DEFINE суттєвий: спочатку SPAN, потім Clojure-композиції.
    # Жодної семантики у shell, Rust або Zig.
    binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp
                     --binding-source lib/d11-clojure-partition-by.lisp)
  elif [[ "$file" == "lib/d11-clojure-partition-by.lisp" ]]; then
    # Partition-by викликає чинні DEFINE із SRFI-1 span/break.
    # Ті самі SENS-зв'язування вже використовують remint і нативний census.
    # Без цього парне виконання помилково відкидає коректний Text7 виклик.
    binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp)
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
  elif [[ "$file" == "tests/semantic/core1-gc-reachability-laws.lisp" ]]; then
    # Обхід коренів і циклів виконує лише наявний Core1 Lisp.
    binding_sources=(--binding-source lib/core1.lisp)
  elif [[ "$file" == "tests/semantic/d11-clojure-juxt-laws.lisp" || "$file" == "tests/semantic/d11-clojure-juxt-mutant.lisp" ]]; then
    # Реальні DEFINE мови, не дубль Rust-реалізації закону.
    binding_sources=(--binding-source lib/d11-clojure-juxt.lisp)
  elif [[ "$file" == "tests/semantic/meta-fc-predicates-d1-law.lisp" ||
          "$file" == "tests/semantic/meta-fc-predicates-d1-mutant.lisp" ]]; then
    binding_sources=(--binding-source lib/meta-eval-first-class.lisp)
  elif [[ "$file" == "tests/semantic/d11-meta-sixth-laws.lisp" ||
          "$file" == "tests/semantic/d11-meta-sixth-mutant.lisp" ||
          "$file" == "tests/semantic/d11-meta-last-define-laws.lisp" ||
          "$file" == "tests/semantic/d11-meta-last-define-mutant.lisp" ||
          "$file" == "tests/semantic/d11-meta-compare-laws.lisp" ||
          "$file" == "tests/semantic/d11-meta-compare-mutant.lisp" ]]; then
    # MetaEval містить незалежні DEFINE, але при повному завантаженні
    # першою виконується ще невиклична фізична D6 LENGTH (#5854).
    # Витягаємо лише точний чинний Lisp DEFINE потрібного свідка.
    # Shell не відтворює закон — він копіює справжній текст до SENS.
    case "$file" in
      tests/semantic/d11-meta-sixth-*)
        target='(визначити шосте-значення-групи' ;;
      tests/semantic/d11-meta-last-define-*)
        target="(визначити останнє-ім'я-визначення-лямбди" ;;
      tests/semantic/d11-meta-compare-*)
        target='(визначити порівняти-два-значення-мета' ;;
    esac
    exact_meta_definition="$dir/meta-eval-exact-definition.lisp"
    if ! awk -v target="$target" '
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
    ' lib/meta-eval.lisp > "$exact_meta_definition"; then
      echo "::error::T5M_META_DEFINE_NOT_ISOLATABLE source=$file target=$target" >&2
      mark_file_failed
      continue
    fi
    if [[ ! -s "$exact_meta_definition" ]]; then
      echo "::error::T5M_META_DEFINE_EMPTY source=$file target=$target" >&2
      mark_file_failed
      continue
    fi
    sha256sum lib/meta-eval.lisp "$exact_meta_definition" > "$dir/meta-eval-source.sha256"
    binding_sources=(--binding-source "$exact_meta_definition")
  elif [[ "$file" == "benchmarks/d11-families.lisp" ]]; then
    # Чисті сімейства D11 використовують DEFINE зі справжніх Lisp-бібліотек.
    # Частоти залежать також від D11 групування, а не від Rust-імітації.
    binding_sources=(--binding-source lib/d11-family-selection.lisp
                     --binding-source lib/d11-srfi1-alist-protocol.lisp
                     --binding-source lib/d11-clojure-group-by.lisp
                     --binding-source lib/d11-clojure-frequencies-unary.lisp)
  elif [[ "$file" == "tests/semantic/d6-any-all-first-class-law.lisp" ||
          "$file" == "tests/semantic/d6-any-all-first-class-mutant.lisp" ]]; then
    # Механічно витягаємо ДВІ чинні SENS-визначення з Core4.
    # Shell не вирішує істину, не відкриває решту D6 і не переписує код.
    local_d6_source="$dir/d6-any-all-core4-definitions.lisp"
    : > "$local_d6_source"
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
      ' lib/core4-parts/core4-d6b.lisp >> "$local_d6_source"; then
        echo "::error::D6_EXACT_DEFINITION_SOURCE_INVALID source=$file target=$quantifier" >&2
        mark_file_failed
        continue 2
      fi
      printf '\n' >> "$local_d6_source"
    done
    sha256sum lib/core4-parts/core4-d6b.lisp "$local_d6_source" > "$dir/d6-definition-provenance.sha256"
    binding_sources=(--binding-source tests/fixtures/epistemic-d1-names.lisp
                     --binding-source "$local_d6_source")
  elif [[ "$file" == "tests/semantic/d11-family-association-law.lisp" ||
          "$file" == "tests/semantic/d11-family-association-mutant.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-alist-protocol.lisp)
  elif [[ "$file" == "tests/semantic/d11-family-aggregation-law.lisp" ||
          "$file" == "tests/semantic/d11-family-aggregation-mutant.lisp" ]]; then
    # Частоти викликають чинне DEFINE групування: обидва кроки виконуються SENS.
    binding_sources=(--binding-source lib/d11-clojure-group-by.lisp
                     --binding-source lib/d11-clojure-frequencies-unary.lisp)
  elif [[ "$file" == "tests/semantic/d11-take-while-first-class-law.lisp" ||
          "$file" == "tests/semantic/d11-take-while-first-class-mutant.lisp" ||
          "$file" == "tests/semantic/d11-take-while-first-class-improper-tail-negative.lisp" ]]; then
    # Бібліотечна D11-композиція: SPAN і TAKE-WHILE виконує тільки SENS.
    binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp
                     --binding-source lib/d11-srfi1-take-while.lisp)
  elif [[ "$file" == "tests/semantic/d11-family-selection-law.lisp" ||
          "$file" == "tests/semantic/d11-family-selection-mutant.lisp" ||
          "$file" == "tests/semantic/d11-family-selection-d1-structural-law.lisp" ||
          "$file" == "tests/semantic/d11-family-selection-d1-structural-mutant.lisp" ]]; then
    # Ядро сімейства відбору Д11 — у lib/d11-family-selection.lisp.
    binding_sources=(--binding-source lib/d11-family-selection.lisp)
  elif [[ "$file" == "tests/semantic/d11-interlisp-dwim-laws.lisp" ||
          "$file" == "tests/semantic/d11-interlisp-dwim-mutant.lisp" ||
          "$file" == "tests/semantic/d11-interlisp-masterscope-laws.lisp" ||
          "$file" == "tests/semantic/d11-interlisp-masterscope-mutant.lisp" ]]; then
    # Rust не визначає істинність DWIM/Masterscope; первинний закон у Lisp.
    binding_sources=(--binding-source lib/d11-interlisp-safe-analysis.lisp)
  elif [[ "$file" == "tests/semantic/d4-lambda-application-law.lisp" ||
          "$file" == "tests/semantic/d4-lambda-application-mutant.lisp" ]]; then
    binding_sources=()
  elif [[ "$file" == "tests/semantic/unify-logic-law.lisp" ||
          "$file" == "tests/semantic/unify-logic-mutant.lisp" ]]; then
    # Ядро логіки (уніфікація, occurs-check, підстановка) — у lib/unify.lisp.
    binding_sources=(--binding-source lib/unify.lisp)
  elif [[ "$file" == "tests/semantic/domain-reuse-guard-law.lisp" ||
          "$file" == "tests/semantic/domain-reuse-guard-mutant.lisp" ||
          "$file" == "tests/semantic/domain-reuse-debt-law.lisp" ||
          "$file" == "tests/semantic/domain-reuse-debt-mutant.lisp" ]]; then
    # Ядро охоронця драбин (драбина-дублі/кандидати/вердикт) визначено
    # лише в lib/domain-function-reuse.lisp. Без цього SENS правильно
    # відхиляє невідомі D7 Text7-символи цих голів.
    binding_sources=(--binding-source lib/domain-function-reuse.lisp)
  fi
  run_native_t5m_program
done < "$manifest"
printf 'T5M_CHANGED_SUMMARY files_checked=%s files_failed=%s native_view_roundtrip=%s native_fragment_parity=%s native_paired_executed=%s native_standalone_parity=%s native_explicit_core4_parity=%s scope=changed_manifest semantic=NOT_CERTIFIED release=NOT_CERTIFIED\n' \
  "$checked_files" "$failed_files" \
  "${#native_view_roundtrip_paths[@]}" "${#native_fragment_parity_paths[@]}" "${#native_paired_executed_paths[@]}" "${#native_standalone_parity_paths[@]}" "${#native_explicit_core4_parity_paths[@]}"
if (( failed_files > 0 )); then
  exit 2
fi
