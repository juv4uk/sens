#!/usr/bin/env bash
# Ремонт чинної фізичної пари одним SENS reader та Zig/T5M.
# Не є семантичним сертифікатом усієї бібліотеки або релізним GO.
set -euo pipefail
if (( $# < 1 )); then
  echo "usage: bash $0 SOURCE.lisp [SENS_BINARY] [SENS_TRIT_BINARY] [--binding-source SOURCE.lisp ...] [--core4-runtime]" >&2
  exit 2
fi
source_file="$1"
shift
binary="target/debug/sens"
reader="target/debug/sens-trit"
if (( $# > 0 )) && [[ "$1" != --binding-source && "$1" != --expect-error && "$1" != --core4-runtime ]]; then
  binary="$1"
  shift
fi
if (( $# > 0 )) && [[ "$1" != --binding-source && "$1" != --expect-error && "$1" != --core4-runtime ]]; then
  reader="$1"
  shift
fi
# Залежності — чинні українські DEFINE у SENS, не хостова семантика.
# Очікувана помилка є частиною негативного свідка, а не успішним виконанням.
binding_args=()
binding_sources=()
expected_error=""
core4_runtime=0
while (( $# > 0 )); do
  case "${1:-}" in
    --core4-runtime)
      if (( core4_runtime )); then
        echo "T5M_REPAIR_CORE4_PROFILE_DUPLICATE source=$source_file" >&2
        exit 2
      fi
      core4_runtime=1
      shift
      ;;
    --binding-source)
      if (( $# < 2 )) || [[ "$2" != *.lisp || ! -f "$2" || -L "$2" ]]; then
        echo "T5M_REPAIR_BINDING_SOURCE_INVALID argument=${2:-missing}" >&2
        exit 2
      fi
      binding_args+=(--binding-source "$2")
      binding_sources+=("$2")
      shift 2
      ;;
    --expect-error)
      if (( $# < 2 )) || [[ -z "$2" || -n "$expected_error" ]]; then
        echo "T5M_REPAIR_EXPECTED_ERROR_ARGUMENT_INVALID" >&2
        exit 2
      fi
      expected_error="$2"
      shift 2
      ;;
    *)
      echo "T5M_REPAIR_ARGUMENT_INVALID argument=${1:-missing}" >&2
      exit 2
      ;;
  esac
done
# Core4 потрібний лише під час SENS eval, а не mint чи фізичного Zig-перегляду.
# Не допускати тихої зміни профілю решти джерел або неперевірених комбінацій.
if (( core4_runtime )); then
  case "$source_file" in
    tests/semantic/exact-arithmetic-laws.lisp|tests/semantic/exact-arithmetic-mutant.lisp|tests/semantic/d5-arithmetic-native-t5m-law.lisp|tests/semantic/d5-arithmetic-native-t5m-mutant.lisp|lib/lisp-fs.lisp|lib/unify.lisp|tests/fixtures/wsm-fs-record-producer.lisp|tests/semantic/meta-eval-graph-d1-law.lisp|tests/semantic/meta-eval-graph-d1-mutant.lisp|tests/semantic/d6-derived-research-batch-01.lisp|tests/semantic/d8-rassq-until-batch.lisp|scripts/check-domain-logic-laws.lisp) ;;
    *) echo "T5M_REPAIR_CORE4_PROFILE_UNREGISTERED source=$source_file" >&2; exit 2 ;;
  esac
  if (( ${#binding_args[@]} != 0 )) || [[ -n "$expected_error" ]]; then
    # The F6 producer fixture is a Core4 consumer AND needs the exact same
    # SENS-owned dependency stack as its WRITE→READ semantic laws. Keep this
    # one combination closed; do not generalize arbitrary Core4+binding runs.
    if [[ -n "$expected_error" ]]; then
      echo "T5M_REPAIR_CORE4_PROFILE_INCOMPATIBLE source=$source_file" >&2
      exit 2
    fi
    case "$source_file|${binding_sources[*]}" in
      'tests/fixtures/wsm-fs-record-producer.lisp|lib/persistent-map.lisp lib/world.lisp lib/content-store.lisp lib/lisp-fs.lisp'|'tests/semantic/meta-eval-graph-d1-law.lisp|lib/meta-eval.lisp'|'tests/semantic/meta-eval-graph-d1-mutant.lisp|lib/meta-eval.lisp') ;;
      *)
        echo "T5M_REPAIR_CORE4_PROFILE_INCOMPATIBLE source=$source_file" >&2
        exit 2
        ;;
    esac
  fi
fi
if [[ "$source_file" != *.lisp || ! -f "$source_file" || -L "$source_file" ]]; then
  echo "T5M_REPAIR_SOURCE_INVALID path=$source_file" >&2
  exit 2
fi
source_bytes=$(wc -c < "$source_file")
total_input_bytes=$source_bytes
# Під час --t5m-mint-pair SENS насправді читає й українські binding-source.
# Бюджет тільки за розміром малого witness помилково давав timeout
# для чинного 300 KiB Core4, хоч виконання мусить залишитися нативним.
for ((i=1; i<${#binding_args[@]}; i+=2)); do
  dependency_bytes=$(wc -c < "${binding_args[i]}")
  (( total_input_bytes += dependency_bytes ))
done
native_timeout=45s
if (( total_input_bytes >= 262144 )); then
  native_timeout=180s
fi
echo "T5M_REPAIR_BUDGET source=$source_file bytes=$source_bytes inputs_bytes=$total_input_bytes timeout=$native_timeout"
for executable in "$binary" "$reader"; do
  if [[ ! -x "$executable" ]]; then
    echo "T5M_REPAIR_EXECUTABLE_MISSING path=$executable" >&2
    exit 2
  fi
done
base="$(dirname "$source_file")/$(basename "$source_file" .lisp)"
physical="$base.sens"
view="$base"
for target in "$physical" "$view"; do
  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    echo "T5M_REPAIR_TARGET_NOT_REGULAR path=$target" >&2
    exit 2
  fi
done
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
cp -- "$source_file" "$scratch/source.snapshot"
staged="$scratch/program.sens"
staged_view="$scratch/program"
direct_source="$source_file"
if (( ${#binding_sources[@]} != 0 )); then
  direct_source="$scratch/direct-bundle.lisp"
  : > "$direct_source"
  for dependency in "${binding_sources[@]}"; do
    cat -- "$dependency" >> "$direct_source"
    printf '\n' >> "$direct_source"
  done
  cat -- "$source_file" >> "$direct_source"
fi
# SENS власноруч створює слова, Zig єдиний пакує T5M.
mint_flag=--t5m-mint
if (( ${#binding_args[@]} != 0 )); then
  mint_flag=--t5m-mint-pair
fi
if timeout "$native_timeout" "$binary" "$mint_flag" "$source_file" "$staged" "${binding_args[@]}"; then
  :
else
  mint_status=$?
  echo "T5M_REPAIR_MINT_FAILED source=$source_file status=$mint_status timeout=$native_timeout" >&2
  exit 2
fi
test -s "$staged"
timeout "$native_timeout" "$reader" view "$staged" > "$staged_view"
test -s "$staged_view"
# Відновити рівно ті самі слова та байти через справжній Zig/T5M.
# Гарантія фізичного обернення не підміняє SENS-парне виконання нижче.
if ! timeout "$native_timeout" "$reader" verify-view "$staged" > "$scratch/inverse.out" 2> "$scratch/inverse.err"; then
  cat "$scratch/inverse.err" >&2
  echo "T5M_REPAIR_VIEW_ROUNDTRIP_FAILED path=$source_file" >&2
  exit 2
fi
paired_runtime_args=()
standalone_runtime=("$binary")
if (( core4_runtime )); then
  paired_runtime_args=(--core4-runtime)
  standalone_runtime=("$reader" eval-core4)
fi
if [[ -n "$expected_error" ]]; then
  if timeout "$native_timeout" "$binary" "$direct_source" > "$scratch/direct.out" 2> "$scratch/direct.err"; then
    echo "T5M_REPAIR_EXPECTED_ERROR_DIRECT_ACCEPTED source=$source_file expected=$expected_error" >&2
    exit 2
  else
    direct_status=$?
  fi
  if (( direct_status == 124 || direct_status == 137 )) ||
     ! grep -Fq "$expected_error" "$scratch/direct.err"; then
    cat "$scratch/direct.err" >&2
    echo "T5M_REPAIR_EXPECTED_ERROR_DIRECT_MISMATCH source=$source_file status=$direct_status expected=$expected_error" >&2
    exit 2
  fi
  if timeout "$native_timeout" "$binary" --t5m-pair "$source_file" "$staged" "${binding_args[@]}" > "$scratch/paired.out" 2> "$scratch/paired.err"; then
    echo "T5M_REPAIR_EXPECTED_ERROR_PAIRED_ACCEPTED source=$source_file expected=$expected_error" >&2
    exit 2
  else
    paired_status=$?
  fi
  if (( paired_status == 124 || paired_status == 137 )) ||
     ! grep -Fq "$expected_error" "$scratch/paired.err"; then
    cat "$scratch/paired.err" >&2
    echo "T5M_REPAIR_EXPECTED_ERROR_PAIRED_MISMATCH source=$source_file status=$paired_status expected=$expected_error" >&2
    exit 2
  fi
  mode=expected-error-paired-only
  if (( ${#binding_sources[@]} == 0 )); then
    if timeout "$native_timeout" "$binary" "$staged" > "$scratch/standalone.out" 2> "$scratch/standalone.err"; then
      echo "T5M_REPAIR_EXPECTED_ERROR_STANDALONE_ACCEPTED source=$source_file expected=$expected_error" >&2
      exit 2
    else
      standalone_status=$?
    fi
    if (( standalone_status == 124 || standalone_status == 137 )) ||
       ! grep -Fq "$expected_error" "$scratch/standalone.err"; then
      cat "$scratch/standalone.err" >&2
      echo "T5M_REPAIR_EXPECTED_ERROR_STANDALONE_MISMATCH source=$source_file status=$standalone_status expected=$expected_error" >&2
      exit 2
    fi
    mode=expected-error-paired-and-standalone
  fi
else
if ! timeout "$native_timeout" "$binary" --t5m-pair "$source_file" "$staged" "${binding_args[@]}" "${paired_runtime_args[@]}" > "$scratch/out" 2> "$scratch/err"; then
  cat "$scratch/err" >&2
  echo "T5M_REPAIR_REAL_EVAL_FAILED path=$source_file" >&2
  exit 2
fi
# Тільки арифметичні SENS-свідки повертають точний D1;
# файлові DEFINE можуть повертати замикання або структуру.
if (( core4_runtime )) &&
   { [[ "$source_file" == tests/semantic/exact-arithmetic-*.lisp ]] ||
     [[ "$source_file" == tests/semantic/d5-arithmetic-native-t5m-*.lisp ]]; }; then
  expected_d1=1
  [[ "$source_file" != *-mutant.lisp ]] || expected_d1=0
  if [[ "$(cat "$scratch/out")" != "$expected_d1" ]]; then
    echo "T5M_REPAIR_CORE4_WRONG_D1 source=$source_file expected=$expected_d1 actual=$(cat "$scratch/out")" >&2
    exit 2
  fi
fi
# Якщо голий фізичний носій також виконується, звіряємо справжні
# результати SENS, а не тільки код виходу та правильність пакування.
# Для D7/D24+ standalone може ще не мати контексту джерельних зв'язувань;
# це НЕ забороняє реальний парний шлях і НЕ означає semantic GO.
mode=paired-only
# Source-only T5M із зовнішніми DEFINE перевіряємо через окремий повний носій.
# Важливо: виконувати його тим самим runtime-профілем, що й pair (зокрема
# `eval-core4` для F6/Core4), інакше D6 closures зникнуть у Session::bare.
# Опублікована пара лишається source-only, самодостатній свідок — тимчасовий.
if (( ${#binding_sources[@]} != 0 )); then
  complete="$scratch/dependency-complete.sens"
  if ! timeout "$native_timeout" "$binary" --t5m-mint "$direct_source" "$complete" > "$scratch/complete-mint.out" 2> "$scratch/complete-mint.err" ||
     ! timeout "$native_timeout" "$reader" open "$complete" > "${complete%.sens}" 2> "$scratch/complete-open.err" ||
     ! timeout "$native_timeout" "$reader" verify-view "$complete" > "$scratch/complete-verify.out" 2> "$scratch/complete-verify.err" ||
     ! timeout "$native_timeout" "${standalone_runtime[@]}" "$complete" > "$scratch/complete.out" 2> "$scratch/complete.err"; then
    for diagnostic in "$scratch/complete-mint.err" "$scratch/complete-open.err" "$scratch/complete-verify.err" "$scratch/complete.err"; do
      if [[ -f "$diagnostic" ]]; then sed "s/^/SENS dependency-complete: /" "$diagnostic" >&2; fi
    done
    echo "T5M_REPAIR_DEPENDENCY_COMPLETE_FAILED source=$source_file physical=NOT_CERTIFIED" >&2
    exit 2
  fi
  if ! cmp -s "$scratch/out" "$scratch/complete.out"; then
    echo "T5M_REPAIR_DEPENDENCY_COMPLETE_DIVERGENCE source=$source_file paired_bytes=$(wc -c < "$scratch/out") complete_bytes=$(wc -c < "$scratch/complete.out")" >&2
    exit 2
  fi
  mode=paired-and-dependency-complete
else
if timeout "$native_timeout" "${standalone_runtime[@]}" "$staged" > "$scratch/standalone.out" 2> "$scratch/standalone.err"; then
  if ! cmp -s "$scratch/out" "$scratch/standalone.out"; then
    echo "T5M_REPAIR_EXECUTION_DIVERGENCE source=$source_file paired_bytes=$(wc -c < "$scratch/out") standalone_bytes=$(wc -c < "$scratch/standalone.out")" >&2
    exit 2
  fi
  if (( core4_runtime )); then
    # Це успішний фізичний Core4, але не запуск через голий `sens FILE.sens`.
    mode=paired-and-explicit-core4
  else
    mode=paired-and-standalone
  fi
else
  status=$?
  # Явний Core4 повинен виконуватися фізично самостійно; paired-only не доказ.
  if (( core4_runtime )); then
    cat "$scratch/standalone.err" >&2
    echo "T5M_REPAIR_CORE4_STANDALONE_FAILED source=$source_file status=$status" >&2
    exit 2
  fi
  # Парне виконання не виправдовує довільну аварію незалежного
  # фізичного виконавця. Відомі межі D7/D24+ допускають лише paired,
  # а panic, timeout і невідома помилка зупиняють ремонт без запису пари.
  if (( status != 124 && status != 137 )) &&
     { grep -Fq 'T5M requires exact source projection to D24+ before transport' "$scratch/standalone.err" ||
       grep -Fq 'unknown Text7 binding:' "$scratch/standalone.err" ||
       { grep -Fq 'Фізичне T5M-декодування зберегло точні ширини слів' "$scratch/standalone.err" &&
         grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$scratch/standalone.err"; }; }; then
    echo "T5M_REPAIR_STANDALONE_KNOWN_LIMIT source=$source_file status=$status; paired SENS execution verified, standalone not certified" >&2
  else
    cat "$scratch/standalone.err" >&2
    echo "T5M_REPAIR_STANDALONE_UNEXPECTED_FAIL source=$source_file status=$status physical=NOT_CERTIFIED" >&2
    exit 2
  fi
fi
fi
fi
# Негативна перевірка проводить іншу програму через той самий SENS.
{ cat "$source_file"; printf '\n(як-є ())\n'; } > "$scratch/mutant.lisp"
if timeout "$native_timeout" "$binary" --t5m-pair "$scratch/mutant.lisp" "$staged" "${binding_args[@]}" "${paired_runtime_args[@]}" > "$scratch/no" 2> "$scratch/no.err"; then
  echo "T5M_REPAIR_MUTANT_WAS_ACCEPTED path=$source_file" >&2
  exit 2
fi
if ! grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$scratch/no.err"; then
  cat "$scratch/no.err" >&2
  echo "T5M_REPAIR_MUTANT_WRONG_FAILURE path=$source_file" >&2
  exit 2
fi
if ! cmp -s "$scratch/source.snapshot" "$source_file"; then
  echo "T5M_REPAIR_SOURCE_CHANGED path=$source_file" >&2
  exit 2
fi
# Механічний файловий запис НЕ є частиною семантики SENS.
# Після SENS → Zig → SENS позитиву і негативу для публікації
# користуємося Bash/coreutils, БЕЗ Python, JSON чи іншого Lisp-оракула.
# Обидві нові проєкції та резервні копії готуємо на тому самому томі.
publish_dir="$(mktemp -d "$(dirname "$physical")/.sens-pair.XXXXXXXX")"
installed_physical=0
installed_view=0
had_physical=0
had_view=0
physical_stamp=""
view_stamp=""
rollback_one() {
  local target="$1" original="$2" expected="$3" stamp="$4" had="$5"
  if [[ -L "$target" || ! -f "$target" ]] ||
     [[ "$(stat -c '%d:%i' "$target")" != "$stamp" ]] ||
     ! cmp -s "$target" "$expected"; then
    echo "T5M_REPAIR_ROLLBACK_CONFLICT path=$target action=manual-review" >&2
    return 1
  fi
  if (( had )); then
    mv -fT -- "$original" "$target"
  else
    rm -- "$target"
  fi
}
cleanup_publish() {
  local status=$?
  trap - EXIT
  if (( status != 0 )); then
    local rollback_failed=0
    if (( installed_view )); then
      rollback_one "$view" "$publish_dir/old.view" "$publish_dir/expected.view" "$view_stamp" "$had_view" || rollback_failed=1
    fi
    if (( installed_physical )); then
      rollback_one "$physical" "$publish_dir/old.sens" "$publish_dir/expected.sens" "$physical_stamp" "$had_physical" || rollback_failed=1
    fi
    if (( rollback_failed )); then
      echo "T5M_REPAIR_ROLLBACK_FAILED source=$source_file" >&2
      # Зберігаємо копії для ручного відновлення, не маскуємо конфлікт.
      echo "T5M_REPAIR_BACKUPS path=$publish_dir" >&2
      exit 2
    fi
    echo "T5M_REPAIR_INSTALL_FAILED source=$source_file status=$status" >&2
  fi
  rm -rf -- "$publish_dir" "$scratch"
  exit "$status"
}
trap cleanup_publish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
cp -- "$staged" "$publish_dir/new.sens"
cp -- "$staged" "$publish_dir/expected.sens"
cp -- "$staged_view" "$publish_dir/new.view"
cp -- "$staged_view" "$publish_dir/expected.view"
for target in "$physical" "$view"; do
  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    echo "T5M_REPAIR_TARGET_NOT_REGULAR path=$target" >&2
    exit 2
  fi
done
if [[ -f "$physical" ]]; then
  had_physical=1
  cp -p -- "$physical" "$publish_dir/old.sens"
  chmod --reference="$physical" "$publish_dir/new.sens"
fi
if [[ -f "$view" ]]; then
  had_view=1
  cp -p -- "$view" "$publish_dir/old.view"
  chmod --reference="$view" "$publish_dir/new.view"
fi
# Перевірити, що існуючі виходи не змінено під час підготовки.
if (( had_physical )); then
  [[ ! -L "$physical" && -f "$physical" ]] &&
    cmp -s "$physical" "$publish_dir/old.sens" || {
      echo "T5M_REPAIR_CONCURRENT_CHANGE path=$physical" >&2; exit 2;
    }
elif [[ -e "$physical" || -L "$physical" ]]; then
  echo "T5M_REPAIR_CONCURRENT_CHANGE path=$physical" >&2; exit 2
fi
if (( had_view )); then
  [[ ! -L "$view" && -f "$view" ]] &&
    cmp -s "$view" "$publish_dir/old.view" || {
      echo "T5M_REPAIR_CONCURRENT_CHANGE path=$view" >&2; exit 2;
    }
elif [[ -e "$view" || -L "$view" ]]; then
  echo "T5M_REPAIR_CONCURRENT_CHANGE path=$view" >&2; exit 2
fi
if ! cmp -s "$scratch/source.snapshot" "$source_file"; then
  echo "T5M_REPAIR_SOURCE_CHANGED path=$source_file" >&2; exit 2
fi
# Новий шлях створюється no-clobber; існуючий замінюється rename.
# У разі збою другого файла відновлюємо перший лише якщо він наш.
if (( had_physical )); then
  mv -fT -- "$publish_dir/new.sens" "$physical"
else
  ln -- "$publish_dir/new.sens" "$physical"
fi
# З нової цілі вже відповідаємо за rollback; rm stage може завершитися RED.
installed_physical=1
physical_stamp="$(stat -c '%d:%i' "$physical")"
if (( ! had_physical )); then rm -- "$publish_dir/new.sens"; fi
cmp "$publish_dir/expected.sens" "$physical"
if (( had_view )); then
  mv -fT -- "$publish_dir/new.view" "$view"
else
  ln -- "$publish_dir/new.view" "$view"
fi
installed_view=1
view_stamp="$(stat -c '%d:%i' "$view")"
if (( ! had_view )); then rm -- "$publish_dir/new.view"; fi
cmp "$publish_dir/expected.view" "$view"
# Джерело могло змінитися між двома записами пари. Поки EXIT trap
# активний, відкидаємо тільки власні inode, а не чужі паралельні зміни.
if ! cmp -s "$scratch/source.snapshot" "$source_file"; then
  echo "T5M_REPAIR_SOURCE_CHANGED_AFTER_INSTALL path=$source_file; фізичну пару відкочено" >&2
  exit 2
fi
trap - EXIT INT TERM
rm -rf -- "$publish_dir" "$scratch"
if [[ -n "$expected_error" ]]; then
  echo "T5M_REPAIR_EXPECTED_ERROR_OK source=$source_file physical=$physical view=$view mode=$mode expected=$expected_error exact=ZIG_AND_SENS semantic_parity=NEGATIVE_WITNESS_RELEASE=NOT_CERTIFIED"
else
  echo "T5M_REPAIR_OK source=$source_file physical=$physical view=$view mode=$mode exact=ZIG_AND_SENS negative=REJECTED semantic_parity=NOT_CERTIFIED release=NOT_CERTIFIED"
fi
