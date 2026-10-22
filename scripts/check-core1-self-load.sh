#!/usr/bin/env bash
# Живий Core1-закон: ратифіковані українські імена -> SENS -> Zig/T5M -> SENS.
# Історичний мікроінтерпретатор MCCARTHY_KERNEL більше не визначає істину.
set -euo pipefail
root_dir="$(git rev-parse --show-toplevel)"
cd "$root_dir"
sens="${SENS_BIN:-$root_dir/target/debug/sens}"
trit="${SENS_TRIT_BIN:-$root_dir/target/debug/sens-trit}"
[[ -x "$sens" && -x "$trit" ]] || {
  printf 'CORE1_NATIVE_MISSING sens=%s trit=%s\n' "$sens" "$trit" >&2
  exit 2
}
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
source=lib/core1.lisp
physical="$scratch/core1.sens"
view="$scratch/core1"
# Старі C1 викличні імена належали донорському виконавцю, не SENS.
# Якщо їх повернуть до живого Core1, CI мусить відмовити.
if LC_ALL=C grep -Eq '^[(]визначити[[:space:]]+C1-' "$source"; then
  echo 'CORE1_LEGACY_CALLABLE_RED: історичне C1 визначення в чинному SENS' >&2
  exit 1
fi
# Вихідні трьох-, чотирьох- й п'ятибітні SID-літерали не є
# викличними словами сучасної драбини. Тут читаємо лише текстову
# форму програми; істину виконання доводять SENS/Zig нижче.
if sed '/^[[:space:]]*;/d' "$source" |
   LC_ALL=C grep -Eq '(^|[[:space:](])0[01]{2,4}([[:space:])]|$)'; then
  echo 'CORE1_OLD_RAW_DOMAIN_WORD: замінити на повну укр проєкцію D3–D5' >&2
  exit 1
fi
"$sens" --t5m-mint "$source" "$physical"
"$trit" open "$physical" > "$view"
"$trit" verify-view "$physical" >/dev/null
"$sens" --t5m-pair "$source" "$physical" > "$scratch/paired.out"
"$sens" "$physical" > "$scratch/native.out"
cmp -s "$scratch/paired.out" "$scratch/native.out" || {
  echo 'CORE1_NATIVE_EXECUTION_DIVERGENCE' >&2
  exit 1
}
# Позитив: сам SENS виконав нативні слова. Негатив: джерело не можна
# непомітно змінити під незмінним фізичним T5M.
{ cat "$source"; printf '\n(як-є ())\n'; } > "$scratch/mutant.lisp"
if "$sens" --t5m-pair "$scratch/mutant.lisp" "$physical" > "$scratch/mutant.out" 2> "$scratch/mutant.err"; then
  echo 'CORE1_MUTANT_ACCEPTED' >&2
  exit 1
fi
grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$scratch/mutant.err" || {
  echo 'CORE1_MUTANT_WRONG_REJECTION' >&2
  cat "$scratch/mutant.err" >&2
  exit 1
}
echo 'CORE1_SELF_LOAD_NATIVE_OK authority=SENS_ZIG_T5M roundtrip=YES positive=EXECUTED negative=REJECTED'
