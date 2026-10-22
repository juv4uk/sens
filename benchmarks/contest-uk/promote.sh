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
bash "$dir/judge.sh" >/dev/null

# 2) Переможець задачі — найменший фізичний .sens серед активних.
declare -A best bestbytes
for path in "$dir"/*.sens; do
  [[ -e "$path" ]] || continue
  name="${path##*/}"; name="${name%.sens}"
  task="$(task_of "$name")" || { echo "PROMOTE_UNKNOWN_TASK $name" >&2; exit 2; }
  bytes="$(wc -c < "$path" | tr -d ' ')"
  if [[ -z "${best[$task]:-}" || "$bytes" -lt "${bestbytes[$task]}" ]]; then
    best[$task]="$path"; bestbytes[$task]="$bytes"
  fi
done
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

# 4) Записати чинний набір переможців (стабільний порядок ключів).
{
  printf '{\n  "schema": "sens-contest-winners/v1",\n  "active": {\n'
  first=1
  for task in довжина-списку сума-до-n факторіал; do
    [[ -n "${best[$task]:-}" ]] || continue
    [[ $first == 1 ]] || printf ',\n'
    first=0
    printf '    "%s": {"path": "%s", "t5m_bytes": %s}' \
      "$task" "${best[$task]}" "${bestbytes[$task]}"
  done
  printf '\n  }\n}\n'
} > "$dir/winners.json"

for task in довжина-списку сума-до-n факторіал; do
  [[ -n "${best[$task]:-}" ]] || continue
  echo "PROMOTED $task ${best[$task]} T5M=${bestbytes[$task]}"
done
echo "CONTEST_PROMOTED excluded=$excluded active=${#best[@]}"
