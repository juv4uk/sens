#!/usr/bin/env bash
# Підрахунок дійсно виконуваних українських Lisp у SENS, а не кількості файлів.
# Єдині оракули: SENS (mint / pair / standalone) та Zig (T5M view).
# Не додається до кожного CI commit: ручний адресний вимір за потреби.
set -euo pipefail
cd "$(dirname "$0")/.."

scope="${1:-}"
sens="${SENS_BIN:-$PWD/target/debug/sens}"
trit="${SENS_TRIT_BIN:-$PWD/target/debug/sens-trit}"
seconds="${SENS_NATIVE_TIMEOUT_SECONDS:-30}"
[[ "$seconds" =~ ^[1-9][0-9]*$ ]] || {
  echo "NATIVE_COUNT_INVALID_TIMEOUT value=$seconds" >&2
  exit 2
}
[[ -x "$sens" && -x "$trit" ]] || {
  echo "NATIVE_COUNT_BUILD_REQUIRED sens=$sens trit=$trit" >&2
  exit 2
}
case "$scope" in
  ""|lib/|tests/|benchmarks/|benchmarks/contest-uk/|research/|knowledge/|experiments/|scripts/|examples/|fixtures/|tools/) ;;
  *) echo "NATIVE_COUNT_INVALID_SCOPE value=$scope" >&2; exit 2 ;;
esac

scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
sources=0
complete=0
inverse=0
paired_executable=0
executable=0
paired_only=0
bad=0
missing=0
nonprogram_data=0

while IFS= read -r -d '' source; do
  if [[ -n "$scope" && "$source" != "$scope"* ]]; then
    continue
  fi
  # Архів конкурсу не є чинною виконуваною програмою: не занижувати
  # покриття main через superseded/ (історія зберігається окремо).
  if [[ "$source" == */superseded/* ]]; then
    continue
  fi
  # Канонічні таблиці D1..D11 - дані, не програми. Їх спеціально
  # НЕ можна mint у .sens: це був би вигаданий executable та хибний
  # NATIVE_MISSING_TRIPLE. Читаємо назви напряму, без Python/JSON.
  case "$source" in
    lib/domains/d[1-9].lisp|lib/domains/d10.lisp|lib/domains/d11.lisp)
      (( nonprogram_data += 1 ))
      printf 'NATIVE_DATA_ONLY\t%s\tclassification=DOMAIN_TABLE\n' "$source" >&2
      continue ;;
    knowledge/meta-eval-evidence.lisp)
      # (schema ...)/(row ...)/(claim ...) — реєстр доказів, не виклики SENS.
      # Не вигадувати виконання чи фізичну пару для metadata.
      (( nonprogram_data += 1 ))
      printf 'NATIVE_DATA_ONLY\t%s\tclassification=EVIDENCE_INVENTORY\n' "$source" >&2
      continue ;;
  esac
  # Прямо позначений інвентар сайтів є схемними даними, не викликом.
  # Якщо файл перетвориться на програму, без точної кореневої форми
  # автоматичного виключення не буде: його перевірить SENS/Zig.
  if [[ "$source" == knowledge/silent-fallback-inventory.lisp &&
        -f "$source" && ! -L "$source" ]] &&
     LC_ALL=C grep -Eq '^[[:space:]]*\(silent-fallback-inventory([[:space:]]|$)' -- "$source"; then
    (( nonprogram_data += 1 ))
    printf 'NATIVE_DATA_ONLY\t%s\tclassification=SCHEMA_INVENTORY\n' "$source" >&2
    continue
  fi
  # Джерело лише з коментарів/порожніх рядків не має Lisp-програми.
  # Воно НЕ мусить мати вигадану фізичну трійку, тому не є missing.
  # Наявність хоча б одного некоментарного рядка залишає незмінними
  # обов'язкові SENS/Zig mint, inverse та виконання. Без Python/JSON.
  # Symlink навмисно не класифікуємо як безпечні дані.
  if [[ -f "$source" && ! -L "$source" ]] &&
     ! LC_ALL=C grep -Eq '^[[:space:]]*[^[:space:];]' -- "$source"; then
    (( nonprogram_data += 1 ))
    printf 'NATIVE_DATA_ONLY\t%s\tclassification=COMMENT_ONLY\n' "$source" >&2
    continue
  fi
  # Точно розпізнаний реєстр/профіль є ДАНИМИ, не виконуваним
  # Lisp. Не плодити помилкові missing-triple, які не допомагають SENS.
  # Це не виключення за шляхом: якщо схема зміниться на програму,
  # вона знову піде до справжнього SENS/Zig mint, inverse та eval.
  data_schema=""
  case "$source" in
    lib/generated/function-table.lisp) data_schema="ft-2" ;;
    lib/generated/uk-surface-audit.lisp) data_schema="uk-surface-audit-2" ;;
    lib/surface/uk-sa-coverage.lisp) data_schema="uk-sa-coverage" ;;
    lib/machine/intel-core-i5-6400.lisp) data_schema="machine-profile-1" ;;
    lib/machine/profile/current-domain-x86-64.lisp) data_schema="machine-domain-profile-2" ;;
  esac
  if [[ -n "$data_schema" && -f "$source" && ! -L "$source" ]] &&
     LC_ALL=C grep -Eq "^[[:space:]]*\\($data_schema([[:space:]]|$)" -- "$source"; then
    (( nonprogram_data += 1 ))
    printf 'NATIVE_DATA_ONLY\t%s\tclassification=EXACT_SCHEMA:%s\n' "$source" "$data_schema" >&2
    continue
  fi
  # Історичні бенчмарки входять до діагностики, не у підтверджені PASS.
  (( sources += 1 ))
  physical="${source%.lisp}.sens"
  view="${source%.lisp}"
  if [[ ! -s "$physical" || ! -f "$view" ||
        -L "$source" || -L "$physical" || -L "$view" ]]; then
    (( missing += 1 ))
    printf 'NATIVE_MISSING_TRIPLE\t%s\n' "$source" >&2
    continue
  fi
  (( complete += 1 ))
  # DEFINE-залежності мають бути завантажені тим самим SENS, що виконує
  # програму. Без них помилково оголошували працюючий файл не-виконуваним.
  binding_sources=()
  case "$source" in
    lib/reason.lisp|lib/forward.lisp)
      binding_sources=(--binding-source lib/unify.lisp) ;;
    lib/d11-clojure-partition-by.lisp)
      binding_sources=(--binding-source lib/d11-srfi1-span-break.lisp) ;;
    lib/narrate.lisp)
      binding_sources=(--binding-source lib/unify.lisp --binding-source lib/reason.lisp) ;;
    lib/result-status.lisp)
      binding_sources=(--binding-source lib/unify.lisp --binding-source lib/knowledge.lisp --binding-source lib/reason.lisp) ;;
    lib/translation.lisp)
      binding_sources=(--binding-source lib/unify.lisp --binding-source lib/knowledge.lisp --binding-source lib/reason.lisp --binding-source lib/world.lisp --binding-source lib/yantra.lisp --binding-source lib/result-status.lisp) ;;
    tests/fixtures/mechanism-selector-1047-witness.lisp)
      binding_sources=(--binding-source lib/mechanism-selector.lisp) ;;
    tests/fixtures/island-lowering-1048-witness.lisp)
      # СЕНС завантажує чинні визначення в порядку залежностей;
      # жодного стороннього LOAD або Python/JSON-семантики.
      binding_sources=(--binding-source lib/mechanism-selector.lisp --binding-source lib/island-lowering.lisp) ;;
    tests/semantic/d9-world-shape-module-events-laws.lisp|tests/semantic/world-exact-arity-witness.lisp)
      binding_sources=(--binding-source lib/world.lisp) ;;
    tests/semantic/meta-fc-predicates-d1-law.lisp)
      # Д11 предикат оголошено в SENS, не у D11 таблиці й не в Rust-хості.
      # Облік виконує той самий native binding-source, що й парний CLI.
      binding_sources=(--binding-source lib/meta-eval-first-class.lisp) ;;
    tests/semantic/meta-fc-predicates-d1-law.lisp)
      # Живий SENS D11 DEFINE, не зовнішній семантичний оракул.
      binding_sources=(--binding-source lib/meta-eval-first-class.lisp) ;;
  esac
  # Часовий бюджет визначає повний SENS-вхід, а не тільки файл-
  # споживач: --binding-source може завантажувати великий Core4.
  # Така сама межа, як у refresh-verified-t5m-pair.sh; семантика
  # та вердикт залишаються винятково за нативним SENS/Zig.
  total_input_bytes=$(wc -c < "$source")
  for ((i=1; i<${#binding_sources[@]}; i+=2)); do
    (( total_input_bytes += $(wc -c < "${binding_sources[i]}") ))
  done
  mint_seconds="$seconds"
  if (( total_input_bytes >= 262144 && mint_seconds < 180 )); then
    mint_seconds=180
  fi
  mint_flag=--t5m-mint
  if (( ${#binding_sources[@]} )); then
    mint_flag=--t5m-mint-pair
  fi
  # create_new у SENS --t5m-mint-pair: старі scratch-байти і view
  # не можуть лишатися під тим самим шляхом для наступної програми.
  rm -f -- "$scratch/mint.sens" "$scratch/mint"
  # Точна причина RED, а не загальний INVERSE_FAILED для всіх шарів.
  # Позитивний шлях не виконує нічого зайвого: ті самі SENS/Zig команди.
  if timeout "${mint_seconds}s" "$sens" "$mint_flag" "$source" "$scratch/mint.sens" "${binding_sources[@]}" >"$scratch/mint.out" 2>"$scratch/mint.err"; then
    :
  else
    status=$?
    (( bad += 1 ))
    printf 'NATIVE_MINT_FAILED\t%s\tstatus=%s\n' "$source" "$status" >&2
    sed 's/^/SENS mint: /' "$scratch/mint.err" >&2
    continue
  fi
  if ! cmp -s "$physical" "$scratch/mint.sens"; then
    (( bad += 1 ))
    printf 'NATIVE_COMMITTED_PAIR_DRIFT\t%s\t' "$source" >&2
    cmp "$physical" "$scratch/mint.sens" 2>&1 | head -n 1 >&2 || true
    continue
  fi
  if timeout "${seconds}s" "$trit" open "$physical" >"$scratch/view" 2>"$scratch/view.err"; then
    :
  else
    status=$?
    (( bad += 1 ))
    printf 'NATIVE_ZIG_OPEN_FAILED\t%s\tstatus=%s\n' "$source" "$status" >&2
    sed 's/^/Zig open: /' "$scratch/view.err" >&2
    continue
  fi
  if ! cmp -s "$view" "$scratch/view"; then
    (( bad += 1 ))
    printf 'NATIVE_COMMITTED_VIEW_DRIFT\t%s\t' "$source" >&2
    cmp "$view" "$scratch/view" 2>&1 | head -n 1 >&2 || true
    continue
  fi
  if timeout "${seconds}s" "$trit" verify-view "$physical" >"$scratch/verify.out" 2>"$scratch/verify.err"; then
    :
  else
    status=$?
    (( bad += 1 ))
    printf 'NATIVE_ZIG_VERIFY_FAILED\t%s\tstatus=%s\n' "$source" "$status" >&2
    sed 's/^/Zig verify: /' "$scratch/verify.err" >&2
    continue
  fi
  (( inverse += 1 ))
  if timeout "${mint_seconds}s" "$sens" --t5m-pair "$source" "$physical" "${binding_sources[@]}" >"$scratch/paired.out" 2>"$scratch/paired.err"; then
    :
  else
    status=$?
    (( bad += 1 ))
    printf 'NATIVE_PAIRED_FAILED\t%s\tstatus=%s\n' "$source" "$status" >&2
    sed 's/^/SENS paired: /' "$scratch/paired.err" >&2
    continue
  fi
  # Цей фізичний файл вже успішно виконав SENS-парний шлях.
  # Не плутати парне виконання з незалежним standalone admission.
  (( paired_executable += 1 ))
  if timeout "${mint_seconds}s" "$sens" "$physical" >"$scratch/standalone.out" 2>"$scratch/standalone.err"; then
    :
  else
    status=$?
    # Парний шлях доведений, але standalone має лише вузькі відомі
    # обмеження D7/D24+. Panic, timeout і довільний RED не є paired-only.
    # Та сама перевірювана межа, що у refresh-verified-t5m-pair.sh.
    if (( status != 124 && status != 137 )) &&
       { grep -Fq 'T5M requires exact source projection to D24+ before transport' "$scratch/standalone.err" ||
         grep -Fq 'unknown Text7 binding:' "$scratch/standalone.err" ||
         { grep -Fq 'Фізичне T5M-декодування зберегло точні ширини слів' "$scratch/standalone.err" &&
           grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$scratch/standalone.err"; }; }; then
      (( paired_only += 1 ))
      printf 'NATIVE_PAIRED_ONLY\t%s\tstatus=%s reason=KNOWN_STANDALONE_LIMIT\n' "$source" "$status" >&2
    else
      (( bad += 1 ))
      printf 'NATIVE_STANDALONE_FAILED\t%s\tstatus=%s reason=UNEXPECTED\n' "$source" "$status" >&2
      sed 's/^/SENS standalone: /' "$scratch/standalone.err" >&2
    fi
    continue
  fi
  if ! cmp -s "$scratch/paired.out" "$scratch/standalone.out"; then
    (( bad += 1 ))
    printf 'NATIVE_OUTPUT_DIVERGENCE\t%s\n' "$source" >&2
    continue
  fi
  (( executable += 1 ))
  printf 'NATIVE_EXECUTED\t%s\n' "$source"
done < <(git ls-files -z -- '*.lisp')

# Цифра самостійно виконаних файлів є достовірною лише для тих,
# які пройшли нативне pair/standalone SENS і побайтовий Zig inverse.
# Підсумковий printf раніше завжди повертав 0 навіть за реального RED.
# Відсутня трійка/paired-only — неповне покриття, не доведений реліз.
status=COMPLETE
if (( sources == 0 )); then
  # Порожня вибірка НЕ може засвідчувати виконання SENS.
  status=EMPTY
elif (( bad != 0 || missing != 0 || paired_only != 0 )); then
  status=PARTIAL
fi
printf 'NATIVE_LISP_RESULT scope=%s sources=%s complete_triplets=%s exact_inverse=%s paired_executed=%s paired_and_standalone=%s paired_only=%s failed=%s missing_triplet=%s nonprogram_data=%s status=%s\n' \
  "${scope:-all}" "$sources" "$complete" "$inverse" "$paired_executable" "$executable" "$paired_only" "$bad" "$missing" "$nonprogram_data" "$status"
if (( bad != 0 )); then
  echo "NATIVE_LISP_EXECUTION_RED failed=$bad: справжню помилку не приховує статус обліку" >&2
  exit 1
fi
