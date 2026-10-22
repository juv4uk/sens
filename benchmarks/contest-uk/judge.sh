#!/usr/bin/env bash
# Нативний конкурс: SENS виконує, Zig звіряє T5M; Python/JSON не беруть участі.
set -euo pipefail
cd "$(dirname "$0")/../.."
sens="${SENS_BIN:-$PWD/target/debug/sens}"
trit="${SENS_TRIT_BIN:-$PWD/target/debug/sens-trit}"
[[ -x "$sens" && -x "$trit" ]] || { echo "Зберіть sens + sens-trit з --features benchmark-ast-visits" >&2; exit 2; }
error() { printf "КОНКУРС: ПОМИЛКА %s\n" "$*" >&2; exit 2; }
# Повний суд не приховує українські Lisp, для яких ще немає
# оберненої фізичної трійки. Реальний запуск лишається за SENS/Zig.
if (( $# == 0 )); then
  for source in benchmarks/contest-uk/*.lisp; do
    [[ -e "$source" || -L "$source" ]] || continue
    [[ -f "$source" && ! -L "$source" ]] || error "некоректне Lisp-джерело $source"
    physical="${source%.lisp}.sens"
    view="${source%.lisp}"
    [[ -s "$physical" && -f "$view" && ! -L "$physical" && ! -L "$view" ]] ||
      error "НЕПАРНЕ_ДЖЕРЕЛО $source: потрібні нативні SENS/Zig T5M mint + view"
  done
fi
# Автоматично включати нові реальні трійки до конкурсу:
# оптимізована програма не має залежати від ручної реєстрації.
if (( $# )); then
  # Явний одиничний виклик вимірює саме названого учасника.
  inputs=("$@")
else
  # Без аргументів усі нові трійки вступають автоматично.
  inputs=(benchmarks/contest-uk/*.sens)
  [[ -f "${inputs[0]}" ]] || error "немає жодного чинного фізичного T5M учасника"
fi
declare -A seen
rows=""
for path in "${inputs[@]}"; do
  [[ "$path" == benchmarks/contest-uk/*.sens && "$path" != *"/../"* ]] || error "некоректний шлях: $path"
  [[ -z "${seen[$path]+yes}" ]] || continue
  seen[$path]=1
  source="${path%.sens}.lisp"; view="${path%.sens}"
  [[ -s "$path" && -f "$source" && -f "$view" &&
     ! -L "$path" && ! -L "$source" && ! -L "$view" ]] || error "неповна трійка $path"
  name="${path##*/}"; name="${name%.sens}"
  case "$name" in
    факторіал|факторіал-*) task="факторіал"; expected="3628800";;
    сума-до-n|сума-до-n-*) task="сума-до-n"; expected="5050";;
    довжина-списку|довжина-списку-*) task="довжина-списку"; expected="8";;
    фібоначчі|фібоначчі-*) task="фібоначчі"; expected="55";;
    степінь-двійки|степінь-двійки-*) task="степінь-двійки"; expected="1024";;
    сума-квадратів|сума-квадратів-*) task="сума-квадратів"; expected="385";;
    сума-кубів|сума-кубів-*) task="сума-кубів"; expected="3025";;
    нсд|нсд-*) task="нсд"; expected="21";;
    квадрат|квадрат-*) task="квадрат"; expected="144";;
    куб|куб-*) task="куб"; expected="343";;
    різниця-квадратів|різниця-квадратів-*) task="різниця-квадратів"; expected="91";;
    *) error "невідома задача $name";;
  esac
  tmp="$(mktemp -d)"
  "$sens" --t5m-mint "$source" "$tmp/minted.sens" >/dev/null || error "mint $path"
  cmp -s "$path" "$tmp/minted.sens" || error "необоротний T5M $path"
  "$trit" open "$path" > "$tmp/view" || error "Zig open $path"
  cmp -s "$view" "$tmp/view" || error "необоротний вигляд $path"
  "$trit" verify-view "$path" >/dev/null || error "Zig verify-view $path"
  "$sens" --t5m-pair "$source" "$path" > "$tmp/paired" || error "SENS paired $path"
  "$sens" "$path" > "$tmp/standalone" || error "SENS standalone $path"
  cmp -s "$tmp/paired" "$tmp/standalone" || error "розбіжність виконання $path"
  { cat "$source"; printf "\n(як-є ())\n"; } > "$tmp/mutant.lisp"
  if "$sens" --t5m-pair "$tmp/mutant.lisp" "$path" >/dev/null 2>"$tmp/negative"; then error "мутант прийнято $path"; fi
  grep -Fq T5M_PHYSICAL_PAIR_MISMATCH "$tmp/negative" || error "некоректна негативна перевірка $path"
  "$sens" --benchmark-physical "$path" > "$tmp/bench.out" 2>"$tmp/bench.err" || error "нативні метрики $path"
  cmp -s "$tmp/standalone" "$tmp/bench.out" || error "бенчмарк змінив результат $path"
  line="$(grep "^SENS_BINARY_BENCH " "$tmp/bench.err")" || error "немає метрик $path"
  [[ "$line" =~ ^SENS_BINARY_BENCH[[:space:]]AST_NODES=([0-9]+)[[:space:]]EVAL_VISITS=([0-9]+)[[:space:]]RESULT=(.+)$ ]] || error "невірні метрики $path"
  nodes="${BASH_REMATCH[1]}"; visits="${BASH_REMATCH[2]}"; result="${BASH_REMATCH[3]}"
  [[ "$(tail -n 1 "$tmp/standalone")" == "$result" ]] || error "результат метрик відмінний $path"
  # Перевірені задачі мають незалежний числовий еталон. Перший
  # конкурсант НЕ може визначати правильність усіх наступних.
  [[ "$result" == "$expected" ]] || error "хибне значення $path: отримано=$result очікувано=$expected"
  # Повне байтове порівняння: command substitution відкидає кінцеві LF
  # і могло зарахувати зайві порожні рядки як коректний результат.
  printf '%s\n' "$expected" > "$tmp/expected"
  cmp -s "$tmp/standalone" "$tmp/expected" || error "хибний вивід $path: очікувано=$expected (зайві/відсутні байти)"
  # Справжні змінні входи: константа замість алгоритму не виграє.
  # Додаємо виклик до тієї самої програми у scratch (оригінал не чіпаємо).
  # Всі свідки проходять реальний SENS -> Zig/T5M -> SENS, без Python/JSON.
  final_call="$(grep -vE '^[[:space:]]*(;|$)' "$source" | tail -n 1)"
  if [[ "$final_call" =~ ^\(([^[:space:]()]+)[[:space:]] ]]; then
    function_name="${BASH_REMATCH[1]}"
  else
    error "не можна прочитати фінальний виклик конкурсанта $source"
  fi
  case "$task" in
    факторіал)
      # Порівнюємо однаковий факторіал для двох допустимих SENS API:
      # хвостовий (н а) та звичайний рекурсивний (н).
      # Рішення про істину приймає тільки нативне виконання SENS.
      if [[ "$final_call" =~ ^[(][^[:space:]()]+[[:space:]][^[:space:]()]+[)]$ ]]; then
        witnesses=("0|1" "5|120" "7|5040")
      else
        witnesses=("0 1|1" "5 1|120" "7 1|5040")
      fi;;
    сума-до-n)
      # Та сама задача суми 1..н: один аргумент н або н з нульовим
      # початковим накопичувачем. Обидва алгоритми перевіряє SENS
      # на кількох вхідних значеннях (не лише на 100).
      if [[ "$final_call" =~ ^[(][^[:space:]()]+[[:space:]][^[:space:]()]+[)]$ ]]; then
        witnesses=("0|0" "10|55" "20|210")
      else
        witnesses=("0 0|0" "10 0|55" "20 0|210")
      fi;;
    фібоначчі)
      # Унарне fib(н) та хвостове fib(н, а, б) конкурують за один
      # результат, але проходять власні живі змінні входи в SENS.
      if [[ "$final_call" =~ ^[(][^[:space:]()]+[[:space:]]+[^[:space:]()]+[)]$ ]]; then
        witnesses=("0|0" "5|5" "7|13")
      else
        witnesses=("0 0 1|0" "5 0 1|5" "7 0 1|13")
      fi;;
    сума-квадратів)
      # Справжня сума квадратів від 1 до н, а не підставлена 385.
      # Кожний вхід проходить SENS mint → Zig/T5M → парне/самостійне виконання.
      witnesses=("0|0" "1|1" "3|14" "7|140" "12|650");;
    нсд)
      # Евклід на незалежних парах: константа 21 не пройде.
      witnesses=("0 5|5" "54 24|6" "17 13|1" "48 18|6" "252 105|21");;
    сума-кубів)
      # Окремі числові еталони: константний вивід 3025 не пройде.
      witnesses=("0|0" "1|1" "3|36" "5|225" "8|1296");;
    степінь-двійки)
      # Одноаргументний степінь також допустимий; додатковий
      # акумулятор перевіряємо окремо, не змінюючи базової істини.
      if [[ "$final_call" =~ ^[(][^[:space:]()]+[[:space:]]+[^[:space:]()]+[)]$ ]]; then
        witnesses=("0|1" "1|2" "5|32" "8|256")
      else
        witnesses=("0 1|1" "1 1|2" "5 1|32" "8 3|768")
      fi;;
    квадрат) witnesses=("0|0" "5|25" "-7|49" "13|169");;
    куб) witnesses=("0|0" "2|8" "5|125" "-3|-27");;
    різниця-квадратів)
      # Дві математично рівні формули, різні AST і фізичний T5M.
      witnesses=("0 0|0" "5 2|21" "7 7|0" "-3 1|8" "12 5|119" "-7 -2|45");;
    довжина-списку)
      # Унарна рекурсія не повинна програвати лише через інший інтерфейс.
      # Порівнюємо однакові вхідні списки, не фіксуючи кількість параметрів.
      if [[ "$final_call" =~ [[:space:]]0\)$ ]]; then
        witnesses=("(як-є ()) 0|0" "(список 1) 0|1" "(список 1 2 3) 0|3")
      else
        witnesses=("(як-є ())|0" "(список 1)|1" "(список 1 2 3)|3")
      fi;;
  esac
  witness_index=0
  for witness in "${witnesses[@]}"; do
    witness_index=$((witness_index + 1))
    witness_args="${witness%%|*}"
    witness_expected="${witness#*|}"
    witness_source="$tmp/вхід-$witness_index.lisp"
    witness_binary="$tmp/вхід-$witness_index.sens"
    {
      cat "$source"
      printf '\n(%s %s)\n' "$function_name" "$witness_args"
    } > "$witness_source"
    "$sens" --t5m-mint "$witness_source" "$witness_binary" >/dev/null ||
      error "SENS не закодував змінний вхід $path №$witness_index"
    "$trit" open "$witness_binary" > "$tmp/вхід-$witness_index" ||
      error "Zig не відкрив змінний вхід $path №$witness_index"
    "$trit" verify-view "$witness_binary" >/dev/null ||
      error "необоротний змінний вхід $path №$witness_index"
    "$sens" --t5m-pair "$witness_source" "$witness_binary" > "$tmp/вхід-$witness_index.paired" ||
      error "не виконано парний змінний вхід $path №$witness_index"
    "$sens" "$witness_binary" > "$tmp/вхід-$witness_index.actual" ||
      error "не виконано автономний змінний вхід $path №$witness_index"
    printf '%s\n' "$witness_expected" > "$tmp/вхід-$witness_index.expected"
    cmp -s "$tmp/вхід-$witness_index.actual" "$tmp/вхід-$witness_index.expected" ||
      error "помилковий алгоритм $path на змінному вході №$witness_index: очікувано $witness_expected"
    cmp -s "$tmp/вхід-$witness_index.paired" "$tmp/вхід-$witness_index.actual" ||
      error "розходження SENS paired/standalone $path на змінному вході №$witness_index"
  done
  printf 'CONTEST_INPUT_WITNESSES_PASS path=%s cases=%s native=SENS_ZIG_T5M\n' "$path" "$witness_index"
  bytes="$(wc -c < "$path")"
  rows+="$task"$'\t'"$bytes"$'\t'"$nodes"$'\t'"$visits"$'\t'"$path"$'\n'
  printf "CONTEST_EXECUTED_PASS path=%s T5M=%s AST=%s visits=%s result=%s\n" "$path" "$bytes" "$nodes" "$visits" "$result"
  rm -- "$tmp/"*
  rmdir -- "$tmp"
done
printf "\nЗадача | T5M байти | AST | visits | Файл\n"
printf "%s" "$rows" | sort -t $'\t' -k1,1 -k2,2n -k3,3n -k4,4n
printf "CONTEST_NATIVE_PASS count=%s\n" "${#seen[@]}"
