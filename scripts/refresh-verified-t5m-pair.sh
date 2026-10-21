#!/usr/bin/env bash
# Ремонт чинної фізичної пари одним SENS reader та Zig/T5M.
# Не є семантичним сертифікатом усієї бібліотеки або релізним GO.
set -euo pipefail
if (( $# < 1 || $# > 3 )); then
  echo "usage: bash $0 SOURCE.lisp [SENS_BINARY] [SENS_TRIT_BINARY]" >&2
  exit 2
fi
source_file="$1"
binary="target/debug/sens"
reader="target/debug/sens-trit"
if (( $# >= 2 )); then binary="$2"; fi
if (( $# == 3 )); then reader="$3"; fi
if [[ "$source_file" != *.lisp || ! -f "$source_file" || -L "$source_file" ]]; then
  echo "T5M_REPAIR_SOURCE_INVALID path=$source_file" >&2
  exit 2
fi
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
snapshot="$(sha256sum "$source_file" | cut -d' ' -f1)"
staged="$scratch/program.sens"
staged_view="$scratch/program"
# SENS власноруч створює слова, Zig єдиний пакує T5M.
timeout 45s "$binary" --t5m-mint "$source_file" "$staged"
test -s "$staged"
timeout 45s "$reader" view "$staged" > "$staged_view"
test -s "$staged_view"
# Відновити рівно ті самі слова та байти через справжній Zig/T5M.
# Гарантія фізичного обернення не підміняє SENS-парне виконання нижче.
if ! timeout 45s "$reader" verify-view "$staged" > "$scratch/inverse.out" 2> "$scratch/inverse.err"; then
  cat "$scratch/inverse.err" >&2
  echo "T5M_REPAIR_VIEW_ROUNDTRIP_FAILED path=$source_file" >&2
  exit 2
fi
if ! timeout 45s "$binary" --t5m-pair "$source_file" "$staged" > "$scratch/out" 2> "$scratch/err"; then
  cat "$scratch/err" >&2
  echo "T5M_REPAIR_REAL_EVAL_FAILED path=$source_file" >&2
  exit 2
fi
# Якщо голий фізичний носій також виконується, звіряємо справжні
# результати SENS, а не тільки код виходу та правильність пакування.
# Для D7/D24+ standalone може ще не мати контексту джерельних зв'язувань;
# це НЕ забороняє реальний парний шлях і НЕ означає semantic GO.
mode=paired-only
if timeout 45s "$binary" "$staged" > "$scratch/standalone.out" 2> "$scratch/standalone.err"; then
  if ! cmp -s "$scratch/out" "$scratch/standalone.out"; then
    echo "T5M_REPAIR_EXECUTION_DIVERGENCE source=$source_file paired_sha256=$(sha256sum "$scratch/out" | cut -d' ' -f1) standalone_sha256=$(sha256sum "$scratch/standalone.out" | cut -d' ' -f1)" >&2
    exit 2
  fi
  mode=paired-and-standalone
else
  status=$?
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
# Негативна перевірка проводить іншу програму через той самий SENS.
{ cat "$source_file"; printf '\n(як-є ())\n'; } > "$scratch/mutant.lisp"
if timeout 45s "$binary" --t5m-pair "$scratch/mutant.lisp" "$staged" > "$scratch/no" 2> "$scratch/no.err"; then
  echo "T5M_REPAIR_MUTANT_WAS_ACCEPTED path=$source_file" >&2
  exit 2
fi
if ! grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$scratch/no.err"; then
  cat "$scratch/no.err" >&2
  echo "T5M_REPAIR_MUTANT_WRONG_FAILURE path=$source_file" >&2
  exit 2
fi
if [[ "$snapshot" != "$(sha256sum "$source_file" | cut -d' ' -f1)" ]]; then
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
if [[ "$snapshot" != "$(sha256sum "$source_file" | cut -d' ' -f1)" ]]; then
  echo "T5M_REPAIR_SOURCE_CHANGED path=$source_file" >&2; exit 2
fi
# Новий шлях створюється no-clobber; існуючий замінюється rename.
# У разі збою другого файла відновлюємо перший лише якщо він наш.
if (( had_physical )); then
  mv -fT -- "$publish_dir/new.sens" "$physical"
else
  ln -- "$publish_dir/new.sens" "$physical"
  rm -- "$publish_dir/new.sens"
fi
installed_physical=1
physical_stamp="$(stat -c '%d:%i' "$physical")"
cmp "$publish_dir/expected.sens" "$physical"
if (( had_view )); then
  mv -fT -- "$publish_dir/new.view" "$view"
else
  ln -- "$publish_dir/new.view" "$view"
  rm -- "$publish_dir/new.view"
fi
installed_view=1
view_stamp="$(stat -c '%d:%i' "$view")"
cmp "$publish_dir/expected.view" "$view"
trap - EXIT INT TERM
rm -rf -- "$publish_dir" "$scratch"
echo "T5M_REPAIR_OK source=$source_file physical=$physical view=$view mode=$mode exact=ZIG_AND_SENS negative=REJECTED semantic_parity=NOT_CERTIFIED release=NOT_CERTIFIED"
