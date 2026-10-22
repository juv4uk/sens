#!/usr/bin/env bash
# Конкурс -> рантайм: просунути переможця задачі й виключити старі варіанти.
#
# Активний набір рантайму — це benchmarks/contest-uk/*.sens: його беруть
# judge.sh, run-native.sh і CI (крок T5M CLI + Rust-тест
# crates/sens-cli/tests/physical_core4_sequence_cli.rs). Тому «підключити
# оптимізоване» = лишити в теці найменший за фізичним T5M варіант задачі,
# а решту перенести в superseded/, де жоден glob їх не бачить. Це не
# бутафорія: рантайм справді бере лише активні трійки.
set -euo pipefail
cd "$(dirname "$0")/../.."
dir=benchmarks/contest-uk
sup="$dir/superseded"

task_of() {
  case "$1" in
    факторіал|факторіал-*) task="факторіал";;
    сума-до-n|сума-до-n-*) task="сума-до-n";;
    довжина-списку|довжина-списку-*) task="довжина-списку";;
    *) return 1;;
  esac
  printf '%s' "$task"
}

# 1) Спершу — справжній суд: усі активні трійки мусять пройти.
# Зберігаємо його нативні метрики: не обчислюємо AST/visits із хостових евристик.
judge_output="$(bash "$dir/judge.sh")"

# 2) Точні правила конкурсу: найменший T5M, далі AST, далі visits.
# Дані отримані тільки зі справжнього виконання SENS/Zig у judge.sh.
declare -A best bestbytes bestnodes bestvisits
while IFS=
(( ${#best[@]} > 0 )) || { echo "PROMOTE_NO_ENTRIES" >&2; exit 2; }

# 3) Виключити не-переможців: перенести трійку (.sens/.lisp/в'ю) у superseded/.
mkdir -p "$sup"
excluded=0
for path in "$dir"/*.sens; do
  [[ -e "$path" ]] || continue
  name="${path##*/}"; name="${name%.sens}"
  task="$(task_of "$name")" || continue
  [[ "$path" == "${best[$task]}" ]] && continue
  for f in "$path" "${path%.sens}.lisp" "${path%.sens}"; do
    [[ -e "$f" ]] || continue
    mv -- "$f" "$sup/${f##*/}"
    echo "SUPERSEDED ${f#"$dir"/}"
  done
  excluded=$((excluded+1))
done

# 4) Стан визначають чинні фізичні файли, а не дубльований JSON-реєстр.
# Вихід нижче містить реальні шляхи й фізичні T5M-байти SENS/Zig.

for task in довжина-списку сума-до-n факторіал; do
  [[ -n "${best[$task]:-}" ]] || continue
  echo "PROMOTED $task ${best[$task]} T5M=${bestbytes[$task]}"
done
echo "CONTEST_PROMOTED excluded=$excluded active=${#best[@]}"
\t' read -r task bytes nodes visits path; do
  [[ "$path" == "$dir/"*.sens ]] || continue
  name="${path##*/}"; name="${name%.sens}"
  actual_task="$(task_of "$name")" || { echo "PROMOTE_UNKNOWN_TASK $name" >&2; exit 2; }
  [[ "$task" == "$actual_task" &&
     "$bytes" =~ ^[0-9]+$ && "$nodes" =~ ^[0-9]+$ && "$visits" =~ ^[0-9]+$ &&
     -f "$path" ]] || { echo "PROMOTE_INVALID_NATIVE_METRIC $path" >&2; exit 2; }
  [[ "$(wc -c < "$path" | tr -d ' ')" == "$bytes" ]] ||
    { echo "PROMOTE_BYTE_MISMATCH $path" >&2; exit 2; }
  if [[ -z "${best[$task]:-}" ]] ||
     (( bytes < bestbytes[$task] ||
        (bytes == bestbytes[$task] && nodes < bestnodes[$task]) ||
        (bytes == bestbytes[$task] && nodes == bestnodes[$task] && visits < bestvisits[$task]) )); then
    best[$task]="$path"
    bestbytes[$task]="$bytes"
    bestnodes[$task]="$nodes"
    bestvisits[$task]="$visits"
  fi
done <<< "$judge_output"
(( ${#best[@]} > 0 )) || { echo "PROMOTE_NO_ENTRIES" >&2; exit 2; }

# 3) Виключити не-переможців: перенести трійку (.sens/.lisp/в'ю) у superseded/.
mkdir -p "$sup"
excluded=0
for path in "$dir"/*.sens; do
  [[ -e "$path" ]] || continue
  name="${path##*/}"; name="${name%.sens}"
  task="$(task_of "$name")" || continue
  [[ "$path" == "${best[$task]}" ]] && continue
  for f in "$path" "${path%.sens}.lisp" "${path%.sens}"; do
    [[ -e "$f" ]] || continue
    mv -- "$f" "$sup/${f##*/}"
    echo "SUPERSEDED ${f#"$dir"/}"
  done
  excluded=$((excluded+1))
done

# 4) Стан визначають чинні фізичні файли, а не дубльований JSON-реєстр.
# Вихід нижче містить реальні шляхи й фізичні T5M-байти SENS/Zig.

for task in довжина-списку сума-до-n факторіал; do
  [[ -n "${best[$task]:-}" ]] || continue
  echo "PROMOTED $task ${best[$task]} T5M=${bestbytes[$task]}"
done
echo "CONTEST_PROMOTED excluded=$excluded active=${#best[@]}"
