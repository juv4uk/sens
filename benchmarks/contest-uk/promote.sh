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
    подвійний-факторіал|подвійний-факторіал-*) task="подвійний-факторіал";;
    сума-до-n|сума-до-n-*) task="сума-до-n";;
    довжина-списку|довжина-списку-*) task="довжина-списку";;
    фібоначчі|фібоначчі-*) task="фібоначчі";;
    степінь-двійки|степінь-двійки-*) task="степінь-двійки";;
    сума-квадратів|сума-квадратів-*) task="сума-квадратів";;
    сума-кубів|сума-кубів-*) task="сума-кубів";;
    сума-парних|сума-парних-*) task="сума-парних";;
    сума-непарних|сума-непарних-*) task="сума-непарних";;
    сума-трикутних|сума-трикутних-*) task="сума-трикутних";;
    нсд|нсд-*) task="нсд";;
    квадрат|квадрат-*) task="квадрат";;
    куб|куб-*) task="куб";;
    різниця-квадратів|різниця-квадратів-*) task="різниця-квадратів";;
    модуль|модуль-*) task="модуль";;
    максимум|максимум-*) task="максимум";;
    мінімум|мінімум-*) task="мінімум";;
    відстань|відстань-*) task="відстань";;
    різниця-кубів|різниця-кубів-*) task="різниця-кубів";;
    кількість-пар|кількість-пар-*) task="кількість-пар";;
    кількість-трійок|кількість-трійок-*) task="кількість-трійок";;
    центроване-квадратне|центроване-квадратне-*) task="центроване-квадратне";;
    *) return 1;;
  esac
  printf '%s' "$task"
}

# Після rebase паралельний remint іноді повертає фізичну пару вже
# архівованого конкурсанта до активної теки БЕЗ .lisp. Це не програма.
# Лише за наявності повної однойменної трійки в superseded/ прибрати
# саме осиротілий фізичний слід; усі інші порушення залишаються RED.
for stale in "$dir"/*.sens; do
  [[ -f "$stale" && ! -L "$stale" ]] || continue
  stem="${stale%.sens}"
  [[ ! -e "$stem.lisp" && ! -L "$stem.lisp" ]] || continue
  name="${stem##*/}"
  archive="$sup/$name"
  if [[ -f "$archive.lisp" && ! -L "$archive.lisp" &&
        -f "$archive.sens" && ! -L "$archive.sens" &&
        -f "$archive" && ! -L "$archive" &&
        -f "$stem" && ! -L "$stem" ]]; then
    if cmp -s "$stale" "$archive.sens" && cmp -s "$stem" "$archive"; then
      # Видаляємо лише побайтовий дублікат вже збереженої трійки.
      rm -- "$stale" "$stem"
      echo "CONTEST_PRUNED_SUPERSEDED_ORPHAN stem=$name identical=yes"
    else
      # Чужий/новий T5M без .lisp не стає програмою; його байти не губимо.
      # Повний SHA у назві: жодної підміни старого архівного варіанта.
      digest="$(sha256sum "$stale")"
      digest="${digest%% *}"
      orphan="$sup/$name-непарний-$digest"
      if [[ -e "$orphan.sens" || -L "$orphan.sens" ||
            -e "$orphan" || -L "$orphan" ]]; then
        # Повторний remint може принести ті самі фізичні байти ще раз.
        if [[ -f "$orphan.sens" && -f "$orphan" &&
              ! -L "$orphan.sens" && ! -L "$orphan" ]] &&
           cmp -s "$stale" "$orphan.sens" &&
           cmp -s "$stem" "$orphan"; then
          rm -- "$stale" "$stem"
          echo "CONTEST_PRUNED_DUPLICATE_UNPAIRED stem=$name sha256=$digest"
        else
          echo "CONTEST_ORPHAN_ARCHIVE_COLLISION stem=$name sha256=$digest" >&2
          exit 2
        fi
      else
        mkdir -p "$sup"
        mv -- "$stale" "$orphan.sens"
        mv -- "$stem" "$orphan"
        echo "CONTEST_PRESERVED_UNPAIRED stem=$name sha256=$digest"
      fi
    fi
  fi
done

# 1) Справжній SENS/Zig-суд — не хостова оцінка семантики.
judge_output="$(bash "$dir/judge.sh")"
# Лічильник тільки з реально виконаних і доведених SENS/Zig програм,
# не з кількості фізичних файлів або JSON.
if [[ "$judge_output" =~ CONTEST_NATIVE_PASS[[:space:]]count=([0-9]+) ]]; then
  judge_executed="${BASH_REMATCH[1]}"
else
  echo "PROMOTE_NO_NATIVE_EXECUTION_COUNT" >&2
  exit 2
fi

# 2) Ранжування за нативними (T5M, AST, visits), без Python/JSON.
declare -A best bestbytes bestnodes bestvisits seen
winner_count=0
while IFS= read -r line; do
  if [[ "$line" =~ ^CONTEST_EXECUTED_PASS[[:space:]]path=([^[:space:]]+)[[:space:]]T5M=([0-9]+)[[:space:]]AST=([0-9]+)[[:space:]]visits=([0-9]+)[[:space:]]result= ]]; then
    path="${BASH_REMATCH[1]}"
    bytes="${BASH_REMATCH[2]}"
    nodes="${BASH_REMATCH[3]}"
    visits="${BASH_REMATCH[4]}"
    [[ "$path" == "$dir/"*.sens && -f "$path" ]] || { echo "PROMOTE_INVALID_PATH $path" >&2; exit 2; }
    name="${path##*/}"; name="${name%.sens}"
    task="$(task_of "$name")" || { echo "PROMOTE_UNKNOWN_TASK $name" >&2; exit 2; }
    [[ -z "${seen[$path]+yes}" ]] || { echo "PROMOTE_DUPLICATE_METRICS $path" >&2; exit 2; }
    seen[$path]=1
    [[ "$(wc -c < "$path" | tr -d ' ')" == "$bytes" ]] || { echo "PROMOTE_BYTE_MISMATCH $path" >&2; exit 2; }
    replace=0
    if [[ -z "${best[$task]:-}" ]]; then
      replace=1
    elif (( bytes < bestbytes[$task] )); then
      replace=1
    elif (( bytes == bestbytes[$task] && nodes < bestnodes[$task] )); then
      replace=1
    elif (( bytes == bestbytes[$task] && nodes == bestnodes[$task] && visits < bestvisits[$task] )); then
      replace=1
    fi
    if (( replace )); then
      if [[ -z "${best[$task]:-}" ]]; then winner_count=$((winner_count + 1)); fi
      best[$task]="$path"
      bestbytes[$task]="$bytes"
      bestnodes[$task]="$nodes"
      bestvisits[$task]="$visits"
    fi
  fi
done <<< "$judge_output"
for path in "$dir"/*.sens; do
  [[ -f "$path" ]] || continue
  [[ -n "${seen[$path]+yes}" ]] || { echo "PROMOTE_UNJUDGED $path" >&2; exit 2; }
done
(( winner_count > 0 )) || { echo "PROMOTE_NO_ENTRIES" >&2; exit 2; }
# 3) Виключити не-переможців: перенести трійку (.sens/.lisp/в'ю) у superseded/.
# Усі цілі архівації перевіряємо перед першим move:
# ніколи не перезаписувати старі оптимізації або неповну трійку.
for path in "$dir"/*.sens; do
  [[ -f "$path" ]] || continue
  name="${path##*/}"; name="${name%.sens}"
  task="$(task_of "$name")" || continue
  [[ "$path" == "${best[$task]}" ]] && continue
  for f in "$path" "${path%.sens}.lisp" "${path%.sens}"; do
    [[ -f "$f" && ! -L "$f" ]] || { echo "PROMOTE_INCOMPLETE_TRIPLE $f" >&2; exit 2; }
    [[ ! -e "$sup/${f##*/}" && ! -L "$sup/${f##*/}" ]] || {
      echo "PROMOTE_ARCHIVE_COLLISION $sup/${f##*/}" >&2; exit 2;
    }
  done
done

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

# Усі категорії визначають виключно результати нативного судді,
# а не старий ручний список: нові переможці більше не зникають зі звіту.
while IFS= read -r task; do
  [[ -n "$task" ]] || continue
  echo "PROMOTED $task ${best[$task]} T5M=${bestbytes[$task]} AST=${bestnodes[$task]} visits=${bestvisits[$task]}"
done < <(printf '%s\n' "${!best[@]}" | LC_ALL=C sort)
echo "CONTEST_PROMOTED excluded=$excluded active=$winner_count"
# Архівні учасники виконані до promotion, але не належать до активної runtime.
if (( judge_executed != winner_count + excluded )); then
  echo "PROMOTE_ACCOUNTING_MISMATCH executed=$judge_executed active=$winner_count superseded=$excluded" >&2
  exit 2
fi
echo "CONTEST_NATIVE_VERIFIED_EXECUTABLES executed_before_promotion=$judge_executed active_winners=$winner_count superseded=$excluded native=SENS_ZIG_T5M"
