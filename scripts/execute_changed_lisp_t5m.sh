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
    tests/semantic/exact-arithmetic-laws.lisp|tests/semantic/exact-arithmetic-mutant.lisp|tests/semantic/d5-arithmetic-native-t5m-law.lisp|tests/semantic/d5-arithmetic-native-t5m-mutant.lisp|tests/semantic/d5-quotient-mod-gcd-laws.lisp|tests/semantic/d8-div-quotient-remainder-native-laws.lisp|tests/semantic/d8-floor-divide-rem-logbitp-laws.lisp|tests/semantic/d9-d10-defined-functions-law.lisp|tests/semantic/d11-frequencies-key-order-law.lisp|tests/semantic/d11-frequencies-key-order-mutant.lisp|tests/semantic/d10-empty-queue-law.lisp|tests/semantic/d10-empty-queue-mutant.lisp|lib/lisp-fs.lisp)
      paired_runtime_args=(--core4-runtime)
      standalone_runtime=("$native_open" eval-core4)
      ;;
  esac
  # Ці фізичні Type-свідки використовують ту саму чинну Core4-сесію,
  # що і прямі D8 закони; не змішувати профілі clean і Core4.
  if [[ "$file" == "tests/fixtures/d8-right-fold-improper-before-action-negative.lisp" ||
        "$file" == "tests/fixtures/d8-right-scan-improper-before-action-negative.lisp" ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
  # D11 APPEND-MAP використовує вже визначений D10 MAPPEND із Core4.
  if [[ "$file" == "tests/semantic/d11-srfi1-append-map-law.lisp" ||
        "$file" == "tests/semantic/d11-srfi1-append-map-mutant.lisp" ||
        "$file" == "tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp" ||
        "$file" == "tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp" ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
  # Д11 ZIP-WITH: обидва входи перевіряються мовою SENS перед callback.
  if [[ "$file" == tests/semantic/d11-srfi1-zip-with-*.lisp ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
  # Д11 LIST=: позитив, мутант і Type-відмови мають один Core4 профіль.
  if [[ "$file" == "tests/semantic/d11-srfi1-list-equality-law.lisp" ||
        "$file" == "tests/semantic/d11-srfi1-list-equality-structure-law.lisp" ||
        "$file" == "tests/semantic/d11-srfi1-list-equality-structure-mutant.lisp" ||
        "$file" == tests/fixtures/d11-srfi1-list-equality-*-negative.lisp ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
  # Д11 APPEND-REVERSE: Core4 через справжні SENS D3 / D8 композиції.
  if [[ "$file" == tests/semantic/d11-srfi1-append-reverse-*.lisp ||
        "$file" == tests/fixtures/d11-srfi1-append-reverse-*-negative.lisp ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
  # Д11 LIST-TABULATE: точні числа D24+ та SENS-замикання.
  if [[ "$file" == tests/semantic/d11-srfi1-list-tabulate-*.lisp ||
        "$file" == tests/fixtures/d11-srfi1-list-tabulate-*-negative.lisp ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
  # Д11 LIST-INDEX використовує Д24+ числовий накопичувач:
  # direct, paired та standalone мають той самий SENS Core4.
  if [[ "$file" == tests/semantic/d11-srfi1-list-index-presence-*.lisp ||
        "$file" == tests/fixtures/d11-srfi1-list-index-*-negative.lisp ]]; then
    paired_runtime_args=(--core4-runtime)
    standalone_runtime=("$native_open" eval-core4)
  fi
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
    tests/semantic/d11-srfi1-zip-with-improper-*-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d11-frequencies-extra-group-field-negative.lisp|tests/fixtures/d11-frequencies-missing-group-field-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d11-srfi1-append-reverse-*-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d11-srfi1-list-tabulate-*-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d11-srfi1-list-equality-*-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d11-srfi1-list-index-nonpredicate-negative.lisp)
      negative_type_diagnostic='D3:110 COND expects exact D1:1 / D1:0' ;;
    tests/fixtures/d11-srfi1-list-index-*-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d11-form-presence-deep-improper-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp|tests/fixtures/d11-unfold-right-priority-atomic-tail-must-error.lisp|tests/fixtures/d11-unfold-right-priority-deep-tail-must-error.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/fixtures/d8-right-fold-improper-before-action-negative.lisp|tests/fixtures/d8-right-scan-improper-before-action-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp|tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp|tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp)
      negative_type_diagnostic='domain identity is not callable under its ratified law: D1 ' ;;
    tests/semantic/d11-srfi1-unary-count-improper-tail-negative.lisp|tests/semantic/d11-srfi1-unary-count-improper-right-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-find-last-presence-improper-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-split-before-last-improper-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-find-last-tail-improper-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-find-first-tail-presence-improper-negative.lisp|tests/semantic/d11-find-first-tail-presence-helper-atom-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d3-eq-nonatom-type-negative.lisp)
      negative_type_diagnostic='eq expects two atoms' ;;
    tests/semantic/d4-not-nonpredicate-type-negative.lisp)
      negative_type_diagnostic='NOT requires an exact D1 PredicateBit' ;;
    tests/semantic/d3-cond-nil-condition-type-negative.lisp|tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp)
      negative_type_diagnostic='D3:110 COND expects exact D1:1 / D1:0' ;;
    tests/semantic/d4-second-improper-d1-tail-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d3-car-empty-list-type-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/core-d3-car-cdr-cons-mutant.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-member-improper-hit-negative.lisp|tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-srfi1-find-tail-improper-tail-negative.lisp|tests/semantic/d11-family-aggregation-mutant.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-drop-while-first-class-atomic-root-negative.lisp|tests/semantic/d11-drop-while-first-class-predicate-precedence-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-take-while-first-class-improper-tail-negative.lisp|tests/semantic/d11-take-while-first-class-atomic-root-negative.lisp|tests/semantic/d11-take-while-first-class-late-improper-negative.lisp|tests/semantic/d11-take-while-first-class-predicate-precedence-negative.lisp)
      negative_type_diagnostic='car expects a non-empty list' ;;
    tests/semantic/d11-family-association-late-record-negative.lisp|tests/semantic/d11-family-association-invalid-update-negative.lisp)
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
    if [[ "$file" == tests/semantic/d11-srfi1-zip-with-improper-*-negative.lisp ]]; then
      direct_source="$dir/d11-zip-with-bound-negative.lisp"
      cat -- lib/d11-srfi1-zip-with.lisp "$file" > "$direct_source"
    elif [[ "$file" == tests/fixtures/d11-srfi1-append-reverse-*-negative.lisp ]]; then
      direct_source="$dir/d11-append-reverse-negative-complete.lisp"
      cat -- lib/d11-srfi1-append-reverse.lisp "$file" > "$direct_source"
    elif [[ "$file" == tests/fixtures/d11-srfi1-list-tabulate-*-negative.lisp ]]; then
      direct_source="$dir/d11-tabulate-negative-complete.lisp"
      cat -- lib/d11-srfi1-list-tabulate.lisp "$file" > "$direct_source"
    elif [[ "$file" == tests/fixtures/d11-srfi1-list-equality-*-negative.lisp ]]; then
      direct_source="$dir/d11-list-equality-bound-negative.lisp"
      cat -- lib/d11-srfi1-list-equality.lisp "$file" > "$direct_source"
    elif [[ "$file" == tests/fixtures/d11-srfi1-list-index-*-negative.lisp ]]; then
      direct_source="$dir/d11-list-index-bound-negative.lisp"
      cat -- lib/d11-srfi1-list-index-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/fixtures/d11-form-presence-deep-improper-negative.lisp" ]]; then
      direct_source="$dir/d11-form-presence-deep-improper-complete.lisp"
      cat -- lib/d11-form-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp" ]]; then
      direct_source="$dir/d11-partition-direct-helper-complete-negative.lisp"
      cat -- lib/d11-srfi1-span-break.lisp lib/d11-clojure-partition-by.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/fixtures/d11-unfold-right-priority-atomic-tail-must-error.lisp" ||
            "$file" == "tests/fixtures/d11-unfold-right-priority-deep-tail-must-error.lisp" ]]; then
      direct_source="$dir/d11-unfold-right-priority-complete-negative.lisp"
      cat -- lib/d11-srfi1-unfold.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-member-improper-hit-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-subset-improper-empty-negative.lisp" ]]; then
      direct_source="$dir/d11-set-relations-bound-negative.lisp"
      cat -- lib/d11-srfi1-set-relations.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp" ||
            "$file" == "tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp" ]]; then
      direct_source="$dir/d11-append-map-bound-negative.lisp"
      cat -- lib/d11-srfi1-append-map.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-filter-map-improper-root-negative.lisp" ||
            "$file" == "tests/semantic/d11-srfi1-filter-map-improper-tail-negative.lisp" ]]; then
      direct_source="$dir/d11-filter-map-bound-negative.lisp"
      cat -- lib/d11-srfi1-filter-map.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-tree-equal-by-test-nonpredicate-negative.lisp" ]]; then
      direct_source="$dir/d11-tree-test-bound-negative.lisp"
      cat -- lib/d11-tree-equal-by-test.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-unary-count-improper-tail-negative.lisp" ||
            "$file" == "tests/semantic/d11-srfi1-unary-count-improper-right-negative.lisp" ]]; then
      direct_source="$dir/d11-unary-count-bound-negative.lisp"
      cat -- lib/d11-srfi1-unary-count.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-find-last-presence-improper-negative.lisp" ]]; then
      direct_source="$dir/d11-find-last-presence-complete-negative.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-find-last-tail-improper-negative.lisp" ]]; then
      direct_source="$dir/d11-last-tail-negative-bound.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-find-first-tail-presence-improper-negative.lisp" ||
            "$file" == "tests/semantic/d11-find-first-tail-presence-helper-atom-negative.lisp" ]]; then
      direct_source="$dir/d11-first-tail-presence-negative-bound.lisp"
      cat -- lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-split-before-last-improper-negative.lisp" ]]; then
      direct_source="$dir/d11-split-last-negative-bound.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp" ]]; then
      direct_source="$dir/d11-find-presence-bound-negative.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-drop-while-first-class-atomic-root-negative.lisp" ||
            "$file" == "tests/semantic/d11-drop-while-first-class-predicate-precedence-negative.lisp" ]]; then
      direct_source="$dir/d11-drop-while-bound-negative.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-take-while-first-class-improper-tail-negative.lisp" ||
            "$file" == "tests/semantic/d11-take-while-first-class-atomic-root-negative.lisp" ||
            "$file" == "tests/semantic/d11-take-while-first-class-late-improper-negative.lisp" ||
            "$file" == "tests/semantic/d11-take-while-first-class-predicate-precedence-negative.lisp" ]]; then
      direct_source="$dir/d11-take-while-bound-negative.lisp"
      cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp "$file" > "$direct_source"
    elif [[ "$file" == "tests/semantic/d11-family-association-late-record-negative.lisp" ||
            "$file" == "tests/semantic/d11-family-association-invalid-update-negative.lisp" ]]; then
      # Прямий SENS Type-свідок має ту ж саму чинну alist-бібліотеку.
      direct_source="$dir/d11-family-association-bound-negative.lisp"
      cat -- lib/d11-srfi1-alist-protocol.lisp "$file" > "$direct_source"
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
    if timeout "$native_timeout" "$binary" --t5m-pair "$file" "$physical" "${paired_runtime_args[@]}" "${binding_sources[@]}" \
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
    # Для окремого D11-негативу самодостатній фізичний носій містить
    # точні SENS DEFINE. Перевіряємо Type, не списуємо відмову на D7 ім'я.
    local negative_standalone_physical="$physical"
    if [[ "$file" == tests/semantic/d11-srfi1-zip-with-improper-*-negative.lisp ]]; then
      negative_standalone_physical="$dir/d11-zip-with-bound-negative.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-zip-mint.stdout" 2>"$dir/d11-zip-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-zip-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-zip-verify.stdout" 2>"$dir/d11-zip-verify.stderr"; then
        echo "::error::D11_ZIP_WITH_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == tests/fixtures/d11-srfi1-append-reverse-*-negative.lisp ]]; then
      negative_standalone_physical="$dir/d11-append-reverse-negative-complete.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-ar-mint.out" 2>"$dir/d11-ar-mint.err" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-ar-open.err" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-ar-verify.out" 2>"$dir/d11-ar-verify.err"; then
        echo "::error::D11_APPEND_REVERSE_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == tests/fixtures/d11-srfi1-list-tabulate-*-negative.lisp ]]; then
      negative_standalone_physical="$dir/d11-tabulate-negative-complete.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-tab-mint.out" 2>"$dir/d11-tab-mint.err" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-tab-open.err" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-tab-verify.out" 2>"$dir/d11-tab-verify.err"; then
        echo "::error::D11_TABULATE_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == tests/fixtures/d11-srfi1-list-equality-*-negative.lisp ]]; then
      negative_standalone_physical="$dir/d11-list-equality-bound-negative.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-eq-mint.stdout" 2>"$dir/d11-eq-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-eq-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-eq-verify.stdout" 2>"$dir/d11-eq-verify.stderr"; then
        echo "::error::D11_LIST_EQUALITY_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == tests/fixtures/d11-srfi1-list-index-*-negative.lisp ]]; then
      # Самодостатній негатив: фізичний T5M містить справжні DEFINE SENS.
      negative_standalone_physical="$dir/d11-list-index-bound-negative.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-idx-mint.stdout" 2>"$dir/d11-idx-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-idx-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-idx-verify.stdout" 2>"$dir/d11-idx-verify.stderr"; then
        echo "::error::D11_LIST_INDEX_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/fixtures/d11-form-presence-deep-improper-negative.lisp" ]]; then
      # Mint реальних SENS DEFINE + свідок, без UnknownSymbol-сурогата.
      negative_standalone_physical="$dir/d11-form-presence-deep-improper-complete.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-form-deep-mint.stdout" 2>"$dir/d11-form-deep-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-form-deep-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-form-deep-verify.stdout" 2>"$dir/d11-form-deep-verify.stderr"; then
        echo "::error::D11_FORM_DEEP_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp" ]]; then
      # Самостійний SENS-чек має містити ті самі DEFINE, що прямий.
      negative_standalone_physical="$dir/d11-append-map-bound-negative.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-append-map-neg-mint.stdout" 2>"$dir/d11-append-map-neg-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-append-map-neg-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-append-map-neg-verify.stdout" 2>"$dir/d11-append-map-neg-verify.stderr"; then
        echo "::error::D11_APPEND_MAP_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp" ||
          "$file" == "tests/fixtures/d11-unfold-right-priority-atomic-tail-must-error.lisp" ||
          "$file" == "tests/fixtures/d11-unfold-right-priority-deep-tail-must-error.lisp" ]]; then
      # Автономний негатив виконує ТОЧНО ТІ SENS DEFINE, що були на прямому
      # та парному шляхах. UnknownSymbol НЕ є дозволеною підміною CAR Type.
      negative_standalone_physical="$dir/d11-priority-bound-negative.sens"
      if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$negative_standalone_physical" >"$dir/d11-priority-mint.stdout" 2>"$dir/d11-priority-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-priority-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-priority-verify.stdout" 2>"$dir/d11-priority-verify.stderr"; then
        echo "::error::D11_PRIORITY_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-split-before-last-improper-negative.lisp" ]]; then
      local split_bad_source="$dir/d11-split-last-bad-complete.lisp"
      negative_standalone_physical="$dir/d11-split-last-bad-complete.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp "$file" > "$split_bad_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$split_bad_source" "$negative_standalone_physical" >"$dir/d11-split-bad-mint.stdout" 2>"$dir/d11-split-bad-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-split-bad-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-split-bad-verify.stdout" 2>"$dir/d11-split-bad-verify.stderr"; then
        echo "::error::D11_SPLIT_LAST_NEGATIVE_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
    fi

    if [[ "$file" == "tests/semantic/d11-find-last-presence-improper-negative.lisp" ]]; then
      local complete_last_source="$dir/d11-last-complete-negative.lisp"
      negative_standalone_physical="$dir/d11-last-complete-negative.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-presence.lisp "$file" > "$complete_last_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$complete_last_source" "$negative_standalone_physical" >"$dir/d11-last-mint.stdout" 2>"$dir/d11-last-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"$dir/d11-last-complete-negative" 2>"$dir/d11-last-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-last-verify.stdout" 2>"$dir/d11-last-verify.stderr"; then
        echo "::error::T5M_D11_LAST_COMPLETE_NEGATIVE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-find-first-tail-presence-improper-negative.lisp" ||
          "$file" == "tests/semantic/d11-find-first-tail-presence-helper-atom-negative.lisp" ]]; then
      local full_bad_source="$dir/d11-first-tail-presence-complete-negative.lisp"
      negative_standalone_physical="$dir/d11-first-tail-presence-complete-negative.sens"
      if ! cat -- lib/d11-srfi1-find-tail.lisp lib/d11-srfi1-find-tail-presence.lisp "$file" > "$full_bad_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$full_bad_source" "$negative_standalone_physical" >"$dir/d11-first-tail-bad-mint.stdout" 2>"$dir/d11-first-tail-bad-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-first-tail-bad-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-first-tail-bad-verify.stdout" 2>"$dir/d11-first-tail-bad-verify.stderr"; then
        echo "::error::D11_FIRST_TAIL_BAD_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-drop-while-first-class-atomic-root-negative.lisp" ||
            "$file" == "tests/semantic/d11-drop-while-first-class-predicate-precedence-negative.lisp" ]]; then
      local full_bad_source="$dir/d11-drop-while-full-negative.lisp"
      negative_standalone_physical="$dir/d11-drop-while-$(basename "$file" .lisp)-full-negative.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-drop-while.lisp "$file" > "$full_bad_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$full_bad_source" "$negative_standalone_physical" >"$dir/d11-drop-while-mint.stdout" 2>"$dir/d11-drop-while-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-drop-while-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-drop-while-verify.stdout" 2>"$dir/d11-drop-while-verify.stderr"; then
        echo "::error::D11_DROP_WHILE_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-find-last-tail-improper-negative.lisp" ]]; then
      local full_bad_source="$dir/d11-last-tail-complete-negative.lisp"
      negative_standalone_physical="$dir/d11-last-tail-complete-negative.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp "$file" > "$full_bad_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$full_bad_source" "$negative_standalone_physical" >"$dir/d11-tail-bad-mint.stdout" 2>"$dir/d11-tail-bad-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-tail-bad-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-tail-bad-verify.stdout" 2>"$dir/d11-tail-bad-verify.stderr"; then
        echo "::error::D11_LAST_TAIL_BAD_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-take-while-first-class-predicate-precedence-negative.lisp" ]]; then
      # Same SENS definitions as direct and paired. Zig only mints the carrier.
      local full_source="$dir/d11-take-while-precedence-complete.lisp"
      negative_standalone_physical="$dir/d11-take-while-precedence-complete.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-span-break.lisp lib/d11-srfi1-take-while.lisp "$file" > "$full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$full_source" "$negative_standalone_physical" >"$dir/d11-precedence-mint.stdout" 2>"$dir/d11-precedence-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$negative_standalone_physical" >"${negative_standalone_physical%.sens}" 2>"$dir/d11-precedence-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$negative_standalone_physical" >"$dir/d11-precedence-verify.stdout" 2>"$dir/d11-precedence-verify.stderr"; then
        echo "::error::D11_TAKE_WHILE_PRECEDENCE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
    fi
    if timeout "$native_timeout" "${standalone_runtime[@]}" "$negative_standalone_physical" \
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
    # ALIST-VALUE-PRESENCE: точна відповідь D1, закон не підміняється хостом.
    if [[ "$file" == "tests/semantic/d11-alist-value-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-alist-value-presence-mutant.lisp" ]]; then
      local d11_value_expected=1
      [[ "$file" != *-mutant.lisp ]] || d11_value_expected=0
      printf '%s\n' "$d11_value_expected" > "$dir/d11-alist-value.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-alist-value.expected"; then
        echo "::error::D11_ALIST_VALUE_D1_MISMATCH source=$file expected=$d11_value_expected actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "D11_ALIST_VALUE_PHYSICAL_PASS source=$file native=SENS result=D1:$d11_value_expected"
    fi
    # Останнє значення: точний D1 закон та хибний D1 мутант.
    if [[ "$file" == "tests/semantic/d11-find-last-value-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-find-last-value-presence-mutant.lisp" ]]; then
      local last_value_expected=1
      [[ "$file" != *-mutant.lisp ]] || last_value_expected=0
      printf '%s\n' "$last_value_expected" > "$dir/d11-last-value.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-last-value.expected"; then
        echo "::error::SENS_D11_LAST_VALUE_WRONG_D1 source=$file expected=D1:$last_value_expected actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "SENS_D11_LAST_VALUE_PASS source=$file result=D1:$last_value_expected native=SENS carrier=Zig/T5M"
    fi
    # Окремий мутант TAKE-UNTIL — хибний закон повертає саме D1:ні.
    # Shell перевіряє тільки фізичний результат SENS, не обчислює списки.
    if [[ "$file" == "tests/semantic/d11-srfi1-span-break-mutant.lisp" ]]; then
      printf '%s\n' 0 > "$dir/d11-break-mutant.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-break-mutant.expected"; then
        echo "::error::SENS_D11_BREAK_MUTANT_WRONG_D1 source=$file expected=D1:0 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
      echo "SENS_D11_BREAK_MUTANT_PASS source=$file result=D1:0 native=SENS carrier=Zig/T5M"
    fi
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
    if [[ "$file" == "tests/semantic/d11-srfi1-lset-diff-intersection-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-lset-diff-intersection-mutant.lisp" ]]; then
      # Окремий самодостатній фізичний SENS-носій з тим самим DEFINE.
      # Так SENS сам перевіряє всі перенесені закони, а Zig — лише байти.
      local lset_full_source="$dir/d11-lset-diff-intersection-full.lisp"
      standalone_physical="$dir/d11-lset-diff-intersection-full.sens"
      if ! cat -- lib/d11-srfi1-lset-diff-intersection.lisp "$file" > "$lset_full_source" ||
         ! timeout "$native_timeout" "$binary" "$lset_full_source" \
              >"$dir/d11-lset-direct.stdout" 2>"$dir/d11-lset-direct.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$lset_full_source" "$standalone_physical" \
              >"$dir/d11-lset-mint.stdout" 2>"$dir/d11-lset-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
              >"${standalone_physical%.sens}" 2>"$dir/d11-lset-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
              >"$dir/d11-lset-verify.stdout" 2>"$dir/d11-lset-verify.stderr"; then
        echo "::error::D11_LSET_COMPLETE_SENS_FAILED source=$file layer=direct-or-zig-t5m" >&2
        for diagnostic in "$dir"/d11-lset-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 LSET: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_lset_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_lset_d1=0
      printf '%s\n' "$expected_lset_d1" > "$dir/d11-lset.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-lset.expected" ||
         ! cmp -s "$dir/d11-lset-direct.stdout" "$dir/d11-lset.expected"; then
        echo "::error::D11_LSET_INCORRECT_SENS_VERDICT source=$file expected=D1:$expected_lset_d1 paired=$(cat "$dir/native-paired.stdout") direct=$(cat "$dir/d11-lset-direct.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-zip-with-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-zip-with-mutant.lisp" ]]; then
      local zip_complete="$dir/d11-zip-with-complete.lisp"
      standalone_physical="$dir/d11-zip-with-complete.sens"
      if ! cat -- lib/d11-srfi1-zip-with.lisp "$file" > "$zip_complete" ||
         ! timeout "$native_timeout" "$binary" "$zip_complete" >"$dir/d11-zip-direct.stdout" 2>"$dir/d11-zip-direct.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$zip_complete" "$standalone_physical" >"$dir/d11-zip-mint.stdout" 2>"$dir/d11-zip-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-zip-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-zip-verify.stdout" 2>"$dir/d11-zip-verify.stderr"; then
        echo "::error::D11_ZIP_WITH_BOUND_EXECUTION_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
      local zip_expected=1
      [[ "$file" != *-mutant.lisp ]] || zip_expected=0
      printf '%s\n' "$zip_expected" > "$dir/d11-zip.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-zip.expected" ||
         ! cmp -s "$dir/d11-zip-direct.stdout" "$dir/d11-zip.expected"; then
        echo "::error::D11_ZIP_WITH_WRONG_D1 source=$file expected=$zip_expected" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == tests/semantic/d11-srfi1-append-reverse-*.lisp ]]; then
      local complete_ar="$dir/d11-append-reverse-complete.lisp"
      standalone_physical="$dir/d11-append-reverse-complete.sens"
      if ! cat -- lib/d11-srfi1-append-reverse.lisp "$file" > "$complete_ar" ||
         ! timeout "$native_timeout" "$binary" "$complete_ar" >"$dir/d11-ar-direct.out" 2>"$dir/d11-ar-direct.err" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$complete_ar" "$standalone_physical" >"$dir/d11-ar-mint.out" 2>"$dir/d11-ar-mint.err" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-ar-open.err" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-ar-verify.out" 2>"$dir/d11-ar-verify.err"; then
        echo "::error::D11_APPEND_REVERSE_BOUND_EXECUTION_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
      local expected_ar=1
      [[ "$file" != *-mutant.lisp ]] || expected_ar=0
      printf '%s\n' "$expected_ar" > "$dir/d11-ar.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-ar.expected" ||
         ! cmp -s "$dir/d11-ar-direct.out" "$dir/d11-ar.expected"; then
        echo "::error::D11_APPEND_REVERSE_WRONG_D1 source=$file expected=$expected_ar" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == tests/semantic/d11-srfi1-list-tabulate-*.lisp ]]; then
      local complete_tab="$dir/d11-tabulate-complete.lisp"
      standalone_physical="$dir/d11-tabulate-complete.sens"
      if ! cat -- lib/d11-srfi1-list-tabulate.lisp "$file" > "$complete_tab" ||
         ! timeout "$native_timeout" "$binary" "$complete_tab" >"$dir/d11-tab-direct.out" 2>"$dir/d11-tab-direct.err" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$complete_tab" "$standalone_physical" >"$dir/d11-tab-mint.out" 2>"$dir/d11-tab-mint.err" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-tab-open.err" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-tab-verify.out" 2>"$dir/d11-tab-verify.err"; then
        echo "::error::D11_TABULATE_BOUND_EXECUTION_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
      local expected_tab=1
      [[ "$file" != *-mutant.lisp ]] || expected_tab=0
      printf '%s\n' "$expected_tab" > "$dir/d11-tab.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-tab.expected" ||
         ! cmp -s "$dir/d11-tab-direct.out" "$dir/d11-tab.expected"; then
        echo "::error::D11_TABULATE_WRONG_D1 source=$file expected=$expected_tab" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-list-equality-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-list-equality-structure-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-list-equality-structure-mutant.lisp" ]]; then
      local eq_complete="$dir/d11-list-equality-complete.lisp"
      standalone_physical="$dir/d11-list-equality-complete.sens"
      if ! cat -- lib/d11-srfi1-list-equality.lisp "$file" > "$eq_complete" ||
         ! timeout "$native_timeout" "$binary" "$eq_complete" >"$dir/d11-eq-direct.stdout" 2>"$dir/d11-eq-direct.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$eq_complete" "$standalone_physical" >"$dir/d11-eq-mint.stdout" 2>"$dir/d11-eq-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-eq-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-eq-verify.stdout" 2>"$dir/d11-eq-verify.stderr"; then
        echo "::error::D11_LIST_EQUALITY_BOUND_EXECUTION_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
      local eq_expected=1
      [[ "$file" != *-mutant.lisp ]] || eq_expected=0
      printf '%s\n' "$eq_expected" > "$dir/d11-eq.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-eq.expected" ||
         ! cmp -s "$dir/d11-eq-direct.stdout" "$dir/d11-eq.expected"; then
        echo "::error::D11_LIST_EQUALITY_WRONG_D1 source=$file expected=$eq_expected" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-list-index-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-list-index-presence-mutant.lisp" ]]; then
      # Єдина самодостатня SENS-програма для прямого й автономного доказу.
      local idx_complete="$dir/d11-list-index-complete.lisp"
      standalone_physical="$dir/d11-list-index-complete.sens"
      if ! cat -- lib/d11-srfi1-list-index-presence.lisp "$file" > "$idx_complete" ||
         ! timeout "$native_timeout" "$binary" "$idx_complete" >"$dir/d11-idx-direct.stdout" 2>"$dir/d11-idx-direct.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$idx_complete" "$standalone_physical" >"$dir/d11-idx-mint.stdout" 2>"$dir/d11-idx-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-idx-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-idx-verify.stdout" 2>"$dir/d11-idx-verify.stderr"; then
        echo "::error::D11_LIST_INDEX_BOUND_EXECUTION_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
      local idx_expected=1
      [[ "$file" != *-mutant.lisp ]] || idx_expected=0
      printf '%s\n' "$idx_expected" > "$dir/d11-idx.expected"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-idx.expected" ||
         ! cmp -s "$dir/d11-idx-direct.stdout" "$dir/d11-idx.expected"; then
        echo "::error::D11_LIST_INDEX_WRONG_D1 source=$file expected=$idx_expected" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-form-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-form-presence-mutant.lisp" ]]; then
      # Справжня самодостатня SENS-програма: визначення + один закон.
      local form_presence_complete="$dir/d11-form-presence-full.lisp"
      standalone_physical="$dir/d11-form-presence-full.sens"
      if ! cat -- lib/d11-form-presence.lisp "$file" > "$form_presence_complete" ||
         ! timeout "$native_timeout" "$binary" "$form_presence_complete" \
             >"$dir/d11-form-presence-direct.stdout" 2>"$dir/d11-form-presence-direct.stderr" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$form_presence_complete" "$standalone_physical" \
             >"$dir/d11-form-presence-mint.stdout" 2>"$dir/d11-form-presence-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
             >"${standalone_physical%.sens}" 2>"$dir/d11-form-presence-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
             >"$dir/d11-form-presence-verify.stdout" 2>"$dir/d11-form-presence-verify.stderr"; then
        echo "::error::D11_FORM_PRESENCE_NATIVE_EXECUTION_FAILED source=$file" >&2
        for diagnostic in "$dir"/d11-form-presence-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 FORM-PRESENCE: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local form_expected=1
      [[ "$file" != *-mutant.lisp ]] || form_expected=0
      printf '%s\n' "$form_expected" > "$dir/d11-form-presence-expected.d1"
      if ! cmp -s "$dir/native-paired.stdout" "$dir/d11-form-presence-expected.d1" ||
         ! cmp -s "$dir/d11-form-presence-direct.stdout" "$dir/d11-form-presence-expected.d1"; then
        echo "::error::D11_FORM_PRESENCE_INCORRECT_D1 source=$file expected=$form_expected" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-split-before-last-law.lisp" ||
          "$file" == "tests/semantic/d11-split-before-last-mutant.lisp" ]]; then
      # Повна SENS-програма, а не самостійний D7 виклик без DEFINE.
      local split_source="$dir/d11-split-last-complete.lisp"
      standalone_physical="$dir/d11-split-last-complete.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-split-before-last-presence.lisp "$file" > "$split_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$split_source" "$standalone_physical" >"$dir/d11-split-mint.stdout" 2>"$dir/d11-split-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-split-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-split-verify.stdout" 2>"$dir/d11-split-verify.stderr"; then
        echo "::error::D11_SPLIT_LAST_PHYSICAL_INVALID source=$file" >&2
        mark_file_failed
        return
      fi
      local split_expected=1
      [[ "$file" != *-mutant.lisp ]] || split_expected=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$split_expected" ]]; then
        echo "::error::D11_SPLIT_LAST_PAIRED_MISMATCH source=$file expected=$split_expected" >&2
        mark_file_failed
        return
      fi
    fi

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
    if [[ "$file" == "tests/semantic/d8-quantifier-composition-law.lisp" ||
          "$file" == "tests/semantic/d8-quantifier-composition-mutant.lisp" ]]; then
      # Фізичний standalone має містити ту саму повну SENS-програму.
      # Zig переносить бітові слова; підсумковий вердикт належить SENS.
      local d8_complete_source="$dir/d8-quantifier-complete.lisp"
      standalone_physical="$dir/d8-quantifier-complete.sens"
      if ! cat -- tests/fixtures/epistemic-d1-names.lisp "$d8_quantifier_source" "$file" > "$d8_complete_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$d8_complete_source" "$standalone_physical" >"$dir/d8-quantifier-mint.stdout" 2>"$dir/d8-quantifier-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d8-quantifier-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d8-quantifier-verify.stdout" 2>"$dir/d8-quantifier-verify.stderr"; then
        echo "::error::Окреме фізичне виконання D8-квантора не підтверджено: source=$file" >&2
        mark_file_failed
        return
      fi
      local expected_d8=1
      [[ "$file" != *-mutant.lisp ]] || expected_d8=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_d8" ]]; then
        echo "::error::D8_QUANTIFIER_WRONG_D1 source=$file expected=$expected_d8 actual=$(cat "$dir/native-paired.stdout")" >&2
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
    if [[ "$file" == "tests/semantic/d11-srfi1-unary-count-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-unary-count-mutant.lisp" ]]; then
      # Повний SENS-носій використовує визначення з живої бібліотеки.
      local unary_count_full_source="$dir/d11-unary-count-full.lisp"
      standalone_physical="$dir/d11-unary-count-full.sens"
      if ! cat -- lib/d11-srfi1-unary-count.lisp "$file" > "$unary_count_full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$unary_count_full_source" "$standalone_physical" \
              >"$dir/d11-unary-count-mint.stdout" 2>"$dir/d11-unary-count-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
              >"${standalone_physical%.sens}" 2>"$dir/d11-unary-count-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
              >"$dir/d11-unary-count-verify.stdout" 2>"$dir/d11-unary-count-verify.stderr"; then
        echo "::error::D11_UNARY_COUNT_STANDALONE_MINT_FAILED source=$file layer=zig-t5m" >&2
        for diagnostic in "$dir"/d11-unary-count-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 UNARY COUNT: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_unary_count_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_unary_count_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_unary_count_d1" ]]; then
        echo "::error::D11_UNARY_COUNT_WRONG_PAIRED_VERDICT source=$file expected=D1:$expected_unary_count_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-list-terminator-law.lisp" ||
          "$file" == "tests/semantic/d11-list-terminator-mutant.lisp" ||
          "$file" == "tests/semantic/d11-list-terminator-nested-mutant.lisp" ]]; then
      # Самодостатній T5M-носій без підміни функції зовнішнім хостом.
      local terminator_full_source="$dir/d11-list-terminator-full.lisp"
      standalone_physical="$dir/d11-list-terminator-full.sens"
      if ! cat -- lib/d11-list-terminator-evidence.lisp "$file" > "$terminator_full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$terminator_full_source" "$standalone_physical" \
              >"$dir/d11-list-terminator-mint.stdout" 2>"$dir/d11-list-terminator-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" \
              >"${standalone_physical%.sens}" 2>"$dir/d11-list-terminator-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" \
              >"$dir/d11-list-terminator-verify.stdout" 2>"$dir/d11-list-terminator-verify.stderr"; then
        echo "::error::D11_LIST_TERMINATOR_STANDALONE_MINT_FAILED source=$file layer=zig-t5m" >&2
        for diagnostic in "$dir"/d11-list-terminator-*.stderr; do
          [[ ! -f "$diagnostic" ]] || sed 's/^/D11 LIST-TERMINATOR: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_terminator_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_terminator_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_terminator_d1" ]]; then
        echo "::error::D11_LIST_TERMINATOR_WRONG_PAIRED_VERDICT source=$file expected=D1:$expected_terminator_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
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
    if [[ "$file" == "tests/semantic/d11-find-last-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-find-last-presence-mutant.lisp" ]]; then
      # Повний фізичний носій виконує ті самі чинні SENS DEFINE, що
      # парне виконання. Залежності не підмінюються Zig чи Rust.
      local last_full_source="$dir/d11-find-last-presence-full.lisp"
      standalone_physical="$dir/d11-find-last-presence-full.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp \
          lib/d11-srfi1-find-last-presence.lisp "$file" > "$last_full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint \
          "$last_full_source" "$standalone_physical" \
          >"$dir/d11-last-mint.stdout" 2>"$dir/d11-last-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open \
          "$standalone_physical" >"${standalone_physical%.sens}" \
          2>"$dir/d11-last-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view \
          "$standalone_physical" >"$dir/d11-last-verify.stdout" \
          2>"$dir/d11-last-verify.stderr"; then
        echo "::error::D11_FIND_LAST_STANDALONE_MINT_FAILED source=$file" >&2
        for diagnostic in "$dir"/d11-last-*.stderr; do
          [[ ! -f "$diagnostic" ]] ||
            sed 's/^/SENS FIND-LAST-PRESENCE: /' "$diagnostic" >&2
        done
        mark_file_failed
        return
      fi
      local expected_last_d1=1
      [[ "$file" != *-mutant.lisp ]] || expected_last_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_last_d1" ]]; then
        echo "::error::D11_FIND_LAST_WRONG_PAIRED_D1 source=$file expected=$expected_last_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-find-last-tail-law.lisp" ||
          "$file" == "tests/semantic/d11-find-last-tail-mutant.lisp" ]]; then
      # Повне SENS-джерело: той самий валідатор і останній суфікс.
      local full_tail_source="$dir/d11-last-tail-complete.lisp"
      standalone_physical="$dir/d11-last-tail-complete.sens"
      if ! cat -- lib/d11-srfi1-find-presence.lisp lib/d11-srfi1-find-last-tail-presence.lisp "$file" > "$full_tail_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$full_tail_source" "$standalone_physical" >"$dir/d11-tail-mint.stdout" 2>"$dir/d11-tail-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-tail-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-tail-verify.stdout" 2>"$dir/d11-tail-verify.stderr"; then
        echo "::error::D11_LAST_TAIL_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
      local expected_tail_result=1
      [[ "$file" != *-mutant.lisp ]] || expected_tail_result=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$expected_tail_result" ]]; then
        echo "::error::D11_LAST_TAIL_PAIRED_MISMATCH source=$file expected=$expected_tail_result actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/d11-srfi1-append-map-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-append-map-mutant.lisp" ]]; then
      # Повний фізичний потік містить D11 DEFINE і чинну SENS Core4.
      local append_map_full_source="$dir/d11-append-map-full.lisp"
      standalone_physical="$dir/d11-append-map-full.sens"
      if ! cat -- lib/d11-srfi1-append-map.lisp "$file" > "$append_map_full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$append_map_full_source" "$standalone_physical" >"$dir/d11-append-map-mint.stdout" 2>"$dir/d11-append-map-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/d11-append-map-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/d11-append-map-verify.stdout" 2>"$dir/d11-append-map-verify.stderr"; then
        echo "::error::D11_APPEND_MAP_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
      local append_map_expected_d1=1
      [[ "$file" != *-mutant.lisp ]] || append_map_expected_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$append_map_expected_d1" ]]; then
        echo "::error::D11_APPEND_MAP_WRONG_D1 source=$file expected=$append_map_expected_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
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
    if [[ "$file" == "tests/semantic/бенчмарк-медіана-law.lisp" ||
          "$file" == "tests/semantic/бенчмарк-медіана-mutant.lisp" ]]; then
      # M3: очікуваний вердикт саме D1 із живого SENS, не host-медіана.
      local benchmark_expected_d1=1
      [[ "$file" != *-mutant.lisp ]] || benchmark_expected_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$benchmark_expected_d1" ]]; then
        echo "::error::SENS_BENCHMARK_MEDIAN_WRONG_D1 source=$file expected=$benchmark_expected_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
        mark_file_failed
        return
      fi
    fi
    if [[ "$file" == "tests/semantic/assertion-library-law.lisp" ||
          "$file" == "tests/semantic/assertion-library-mutant.lisp" ||
          "$file" == "tests/semantic/assertion-library-bad-tail-negative.lisp" ]]; then
      local assertion_full_source="$dir/assertion-library-full.lisp"
      standalone_physical="$dir/assertion-library-full.sens"
      if ! cat -- lib/твердження.lisp "$file" > "$assertion_full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$assertion_full_source" "$standalone_physical" >"$dir/assertion-mint.stdout" 2>"$dir/assertion-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/assertion-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/assertion-verify.stdout" 2>"$dir/assertion-verify.stderr"; then
        echo "::error::SENS_ASSERTION_LIBRARY_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
      if [[ "$file" != tests/semantic/assertion-library-bad-tail-negative.lisp ]]; then
        local assertion_expected_d1=1
        [[ "$file" != *-mutant.lisp ]] || assertion_expected_d1=0
        if [[ "$(cat "$dir/native-paired.stdout")" != "$assertion_expected_d1" ]]; then
          echo "::error::SENS_ASSERTION_LIBRARY_WRONG_D1 source=$file expected=$assertion_expected_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
          mark_file_failed
          return
        fi
      fi
    fi
    if [[ "$file" == "tests/semantic/бенчмарк-медіана-law.lisp" ||
          "$file" == "tests/semantic/бенчмарк-медіана-mutant.lisp" ]]; then
      local median_full_source="$dir/benchmark-median-full.lisp"
      standalone_physical="$dir/benchmark-median-full.sens"
      if ! cat -- lib/бенчмарк.lisp "$file" > "$median_full_source" ||
         ! timeout "$native_timeout" "$binary" --t5m-mint "$median_full_source" "$standalone_physical" >"$dir/benchmark-median-mint.stdout" 2>"$dir/benchmark-median-mint.stderr" ||
         ! timeout "$native_timeout" "$native_open" open "$standalone_physical" >"${standalone_physical%.sens}" 2>"$dir/benchmark-median-open.stderr" ||
         ! timeout "$native_timeout" "$native_open" verify-view "$standalone_physical" >"$dir/benchmark-median-verify.stdout" 2>"$dir/benchmark-median-verify.stderr"; then
        echo "::error::SENS_BENCHMARK_MEDIAN_STANDALONE_MINT_FAILED source=$file" >&2
        mark_file_failed
        return
      fi
      local median_expected_d1=1
      [[ "$file" != *-mutant.lisp ]] || median_expected_d1=0
      if [[ "$(cat "$dir/native-paired.stdout")" != "$median_expected_d1" ]]; then
        echo "::error::SENS_BENCHMARK_MEDIAN_WRONG_D1 source=$file expected=$median_expected_d1 actual=$(cat "$dir/native-paired.stdout")" >&2
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
  id="$checked_files"
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
  elif [[ "$file" == "tests/semantic/assertion-library-law.lisp" ||
          "$file" == "tests/semantic/assertion-library-mutant.lisp" ||
          "$file" == "tests/semantic/assertion-library-bad-tail-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/твердження.lisp)
  elif [[ "$file" == "lib/бенчмарк.lisp" ]]; then
    binding_sources=(--binding-source lib/core4.lisp)
  elif [[ "$file" == "tests/semantic/бенчмарк-медіана-law.lisp" ||
          "$file" == "tests/semantic/бенчмарк-медіана-mutant.lisp" ]]; then
    binding_sources=(--binding-source lib/core4.lisp --binding-source lib/бенчмарк.lisp)
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
  elif [[ "$file" == "tests/semantic/d11-srfi1-unary-count-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-unary-count-mutant.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-unary-count-improper-tail-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-unary-count-improper-right-negative.lisp" ]]; then
    # Усі чотири носії викликають ті самі чинні SENS DEFINE.
    binding_sources=(--binding-source lib/d11-srfi1-unary-count.lisp)
  elif [[ "$file" == "tests/semantic/d11-list-terminator-law.lisp" ||
          "$file" == "tests/semantic/d11-list-terminator-mutant.lisp" ||
          "$file" == "tests/semantic/d11-list-terminator-nested-mutant.lisp" ]]; then
    # Повторно використовуємо лише справжній SENS DEFINE, Zig переносить форму.
    binding_sources=(--binding-source lib/d11-list-terminator-evidence.lisp)
  elif [[ "$file" == "tests/semantic/d11-find-last-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-find-last-presence-mutant.lisp" ||
          "$file" == "tests/semantic/d11-find-last-presence-improper-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp
                     --binding-source lib/d11-srfi1-find-last-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-find-last-tail-law.lisp" ||
          "$file" == "tests/semantic/d11-find-last-tail-mutant.lisp" ||
          "$file" == "tests/semantic/d11-find-last-tail-improper-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp
                     --binding-source lib/d11-srfi1-find-last-tail-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-find-first-tail-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-find-first-tail-presence-mutant.lisp" ||
          "$file" == "tests/semantic/d11-find-first-tail-presence-improper-negative.lisp" ||
          "$file" == "tests/semantic/d11-find-first-tail-presence-helper-atom-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-find-tail.lisp
                     --binding-source lib/d11-srfi1-find-tail-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-split-before-last-law.lisp" ||
          "$file" == "tests/semantic/d11-split-before-last-mutant.lisp" ||
          "$file" == "tests/semantic/d11-split-before-last-improper-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp
                     --binding-source lib/d11-split-before-last-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-find-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-presence-mutant.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-presence-improper-tail-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-find-presence-early-hit-improper-negative.lisp" ]]; then
    # Існуюче SENS-визначення ідентичне для direct, paired і повного файла.
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-lset-diff-intersection-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-lset-diff-intersection-mutant.lisp" ]]; then
    # У DIFF/XOR семантика виключно в сімох чинних DEFINE SENS.
    # Після перенесення законів не можна mint/pair голий Text7 виклик.
    binding_sources=(--binding-source lib/d11-srfi1-lset-diff-intersection.lisp)
  elif [[ "$file" == tests/fixtures/d11-frequencies-exact-group-pair-*.lisp ||
          "$file" == tests/fixtures/d11-frequencies-extra-group-field-negative.lisp ||
          "$file" == tests/fixtures/d11-frequencies-missing-group-field-negative.lisp ]]; then
    # Ті самі два канонічні DEFINE у прямому, парному та фізичному SENS.
    binding_sources=(--binding-source lib/d11-clojure-group-by.lisp --binding-source lib/d11-clojure-frequencies-unary.lisp)
  elif [[ "$file" == tests/semantic/d11-srfi1-zip-with-*.lisp ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-zip-with.lisp)
  elif [[ "$file" == tests/semantic/d11-srfi1-append-reverse-*.lisp ||
          "$file" == tests/fixtures/d11-srfi1-append-reverse-*-negative.lisp ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-append-reverse.lisp)
  elif [[ "$file" == tests/semantic/d11-srfi1-list-tabulate-*.lisp ||
          "$file" == tests/fixtures/d11-srfi1-list-tabulate-*-negative.lisp ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-list-tabulate.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-list-equality-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-list-equality-structure-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-list-equality-structure-mutant.lisp" ||
          "$file" == tests/fixtures/d11-srfi1-list-equality-*-negative.lisp ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-list-equality.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-list-index-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-list-index-presence-mutant.lisp" ||
          "$file" == tests/fixtures/d11-srfi1-list-index-*-negative.lisp ]]; then
    # Д11 LIST-INDEX: реальні DEFINE в усіх носіях.
    binding_sources=(--binding-source lib/d11-srfi1-list-index-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-form-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-form-presence-mutant.lisp" ||
          "$file" == "tests/fixtures/d11-form-presence-deep-improper-negative.lisp" ]]; then
    # Усі свідки поділяють одне чинне джерело DEFINE мовою SENS.
    binding_sources=(--binding-source lib/d11-form-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-srfi1-append-map-law.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-append-map-mutant.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-append-map-improper-input-negative.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-append-map-improper-output-negative.lisp" ]]; then
    # Спільне визначення і D10 MAPPEND в одному парному Core4-сеансі.
    binding_sources=(--binding-source lib/d11-srfi1-append-map.lisp)
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
    for spec in 'lib/core4-parts/core4-d6.lisp|значення-у-списку?' \
      'lib/core4-parts/core4-d6b.lisp|об'"'"'єднання-перевірити-правий' \
      'lib/core4-parts/core4-d6b.lisp|об'"'"'єднання'; do
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
  elif [[ "$file" == "tests/semantic/d11-srfi1-span-break-laws.lisp" ||
          "$file" == "tests/semantic/d11-srfi1-span-break-mutant.lisp" ]]; then
    # SENS визначає мову; Zig лише переносить біти фізичного T5M.
    binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp)
  elif [[ "$file" == "tests/semantic/d11-clojure-partition-by-laws.lisp" ||
          "$file" == "tests/semantic/d11-clojure-partition-by-d7-parity.lisp" ||
          "$file" == "tests/semantic/d11-clojure-dedupe-laws.lisp" ||
          "$file" == "tests/semantic/d11-clojure-partition-singleton-key-law.lisp" ||
          "$file" == "tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp" ]]; then
    # Порядок DEFINE суттєвий: спочатку SPAN, потім Clojure-композиції.
    # Жодної семантики у shell, Rust або Zig.
    binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp
                     --binding-source lib/d11-clojure-partition-by.lisp)
  elif [[ "$file" == "tests/fixtures/d11-unfold-right-priority-atomic-tail-must-error.lisp" ||
          "$file" == "tests/fixtures/d11-unfold-right-priority-deep-tail-must-error.lisp" ]]; then
    # D11 UNFOLD-RIGHT: для парного SENS потрібний реальний DEFINE ядра.
    binding_sources=(--binding-source lib/d11-srfi1-unfold.lisp)
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
    binding_sources=(--binding-source tests/fixtures/epistemic-d1-names.lisp
                     --binding-source "$local_d6_source")
  elif [[ "$file" == "tests/semantic/d8-quantifier-composition-law.lisp" ||
          "$file" == "tests/semantic/d8-quantifier-composition-mutant.lisp" ]]; then
    # Відтворюємо рівно п'ять чинних мовних DEFINE, а не host-семантику.
    # Голий змінений файл не містить D6/D8-зв'язувань: UnknownSymbol
    # не є свідком правильності чи хибності кванторного закону.
    d8_quantifier_source="$dir/d8-quantifiers-exact-sens.lisp"
    : > "$d8_quantifier_source"
    for quantifier in будь-яке? усі? є-що-не-задовольняє? усі-не-задовольняють? жодне-не-задовольняє?; do
      if ! awk -v target="(визначити $quantifier" '
        $0 == target { if (found++) exit 2; copying = 1 }
        copying && NF == 0 { copying = 0; complete++; next }
        copying { print }
        END { if (found != 1 || complete != 1 || copying) exit 2 }
      ' lib/core4-parts/core4-d6b.lisp >> "$d8_quantifier_source"; then
        echo "::error::D8_QUANTIFIER_SENS_DEFINITION_MISSING source=$file target=$quantifier" >&2
        mark_file_failed
        continue 2
      fi
      printf '\n' >> "$d8_quantifier_source"
    done
    binding_sources=(--binding-source tests/fixtures/epistemic-d1-names.lisp
                     --binding-source "$d8_quantifier_source")
  elif [[ "$file" == "tests/semantic/d11-family-association-law.lisp" ||
          "$file" == "tests/semantic/d11-family-association-mutant.lisp" ||
          "$file" == "tests/semantic/d11-family-association-late-record-negative.lisp" ||
          "$file" == "tests/semantic/d11-family-association-invalid-update-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-alist-protocol.lisp)
  elif [[ "$file" == "tests/semantic/d11-alist-value-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-alist-value-presence-mutant.lisp" ]]; then
    # Мовний результат формує SENS, транспорт бере тільки точні байти T5M.
    binding_sources=(--binding-source lib/d11-srfi1-alist-protocol.lisp)
  elif [[ "$file" == "tests/semantic/d11-find-last-value-presence-law.lisp" ||
          "$file" == "tests/semantic/d11-find-last-value-presence-mutant.lisp" ]]; then
    # Всі три перевірені SENS DEFINE; Zig переносить лише фізичні слова.
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp
                     --binding-source lib/d11-srfi1-find-last-tail-presence.lisp
                     --binding-source lib/d11-srfi1-find-last-value-presence.lisp)
  elif [[ "$file" == "tests/semantic/d11-family-aggregation-law.lisp" ||
          "$file" == "tests/semantic/d11-family-aggregation-mutant.lisp" ]]; then
    # Частоти викликають чинне DEFINE групування: обидва кроки виконуються SENS.
    binding_sources=(--binding-source lib/d11-clojure-group-by.lisp
                     --binding-source lib/d11-clojure-frequencies-unary.lisp)
  elif [[ "$file" == "tests/semantic/d11-drop-while-first-class-law.lisp" ||
          "$file" == "tests/semantic/d11-drop-while-first-class-mutant.lisp" ||
          "$file" == "tests/semantic/d11-drop-while-first-class-atomic-root-negative.lisp" ||
          "$file" == "tests/semantic/d11-drop-while-first-class-predicate-precedence-negative.lisp" ]]; then
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp
                     --binding-source lib/d11-srfi1-span-break.lisp
                     --binding-source lib/d11-srfi1-drop-while.lisp)
  elif [[ "$file" == "tests/semantic/d11-take-while-first-class-law.lisp" ||
          "$file" == "tests/semantic/d11-take-while-first-class-mutant.lisp" ||
          "$file" == "tests/semantic/d11-take-while-first-class-improper-tail-negative.lisp" ||
          "$file" == "tests/semantic/d11-take-while-first-class-atomic-root-negative.lisp" ||
          "$file" == "tests/semantic/d11-take-while-first-class-late-improper-negative.lisp" ||
            "$file" == "tests/semantic/d11-take-while-first-class-predicate-precedence-negative.lisp" ]]; then
    # Бібліотечна D11-композиція: SPAN і TAKE-WHILE виконує тільки SENS.
    binding_sources=(--binding-source lib/d11-srfi1-find-presence.lisp
                     --binding-source lib/d11-srfi1-span-break.lisp
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
