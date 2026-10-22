#!/usr/bin/env bash
# Конкурс реальних українських SENS-програм без Python/JSON і хостового оракула.
# Зараховується тільки результат, відтворений самостійним фізичним SENS.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$here/../.." && pwd)"
sens="${SENS_BINARY:-$root/target/debug/sens}"
trit="${SENS_TRIT_BINARY:-$root/target/debug/sens-trit}"
repeats="${SENS_CONTEST_REPEATS:-5}"
if [[ ! -x "$sens" || ! -x "$trit" ]]; then
  echo 'CONTEST_BLOCKED: потрібні нативні target/debug/sens та sens-trit (Zig/T5M)' >&2
  exit 2
fi
if [[ ! "$repeats" =~ ^[13579]$|^[1-9][0-9]*$ ]] || (( repeats > 99 || repeats % 2 == 0 )); then
  echo 'CONTEST_BLOCKED: SENS_CONTEST_REPEATS має бути непарним 1..99' >&2
  exit 2
fi
scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
printf 'програма\tбайти_T5M\tмедіана_нс\tповторів\tстан\n'
fail=0
# Навіть без окремого Rust-тесту суддя не має пропускати осиротілий
# фізичний носій: кожен активний T5M зобов'язаний мати власний Lisp.
# Нові source-only кандидати нижче залишаються чесним NOT_EXECUTED,
# але байти без джерела не можуть отримати успішний verdict.
for physical_peer in "$here"/*.sens; do
  [[ -e "$physical_peer" || -L "$physical_peer" ]] || continue
  stem="${physical_peer%.sens}"
  if [[ ! -s "$physical_peer" || -L "$physical_peer" ||
        ! -f "$stem.lisp" || -L "$stem.lisp" ]]; then
    echo "CONTEST_ORPHAN_PHYSICAL path=$physical_peer source=$stem.lisp" >&2
    fail=1
  fi
done
for source in "$here"/*.lisp; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    echo "CONTEST_INVALID_SOURCE path=$source" >&2
    fail=1
    continue
  fi
  name="$(basename -- "$source" .lisp)"

  physical="$scratch/$name.sens"
  view="$scratch/$name"
  committed="$here/$name.sens"
  committed_view="$here/$name"
  # Джерело без ОБОХ фізичних супутників — кандидат у черзі Zig/SENS
  # remint, а не зламана активна програма. Воно не входить до метрик.
  # Неповна або підмінена трійка (symlink/тільки один супутник) — RED.
  if [[ ! -e "$committed" && ! -L "$committed" &&
        ! -e "$committed_view" && ! -L "$committed_view" ]]; then
    echo "CONTEST_PENDING_NATIVE_PAIR source=$source status=NOT_EXECUTED" >&2
    continue
  fi
  if [[ ! -f "$committed" || -L "$committed" ||
        ! -f "$committed_view" || -L "$committed_view" ]]; then
    printf '%s\t-\t-\t0\tНЕПОВНА_ФІЗИЧНА_ПАРА\n' "$name"
    fail=1
    continue
  fi
  # Для source-only кандидата немає нативного результату: не вимагати
  # реєстрації задачі до появи повної фізичної трійки SENS/Zig.
  case "$name" in
    акерман|акерман-*) expected=61 ;;
    довжина-списку|довжина-списку-*) expected=8 ;;
    сума-до-n|сума-до-n-*) expected=5050 ;;
    факторіал|факторіал-*) expected=3628800 ;;
    подвійний-факторіал|подвійний-факторіал-*) expected=945 ;;
    фібоначчі|фібоначчі-*) expected=55 ;;
    степінь-двійки|степінь-двійки-*) expected=1024 ;;
    сума-квадратів|сума-квадратів-*) expected=385 ;;
    сума-кубів|сума-кубів-*) expected=3025 ;;
    сума-четвертих-степенів|сума-четвертих-степенів-*) expected=25333 ;;
    сума-парних|сума-парних-*) expected=10100 ;;
    сума-непарних-квадратів|сума-непарних-квадратів-*) expected=1330 ;;
    сума-непарних|сума-непарних-*) expected=289 ;;
    сума-трикутних|сума-трикутних-*) expected=220 ;;
    нсд|нсд-*) expected=21 ;;
    квадрат|квадрат-*) expected=144 ;;
    куб|куб-*) expected=343 ;;
    різниця-квадратів|різниця-квадратів-*) expected=91 ;;
    модуль|модуль-*) expected=17 ;;
    максимум|максимум-*) expected=17 ;;
    мінімум|мінімум-*) expected=-17 ;;
    відстань|відстань-*) expected=29 ;;
    різниця-кубів|різниця-кубів-*) expected=279 ;;
    кількість-пар|кількість-пар-*) expected=45 ;;
    кількість-атомів|кількість-атомів-*) expected=2 ;;
    кількість-трійок|кількість-трійок-*) expected=120 ;;
    центроване-квадратне|центроване-квадратне-*) expected=85 ;;
    центроване-трикутне|центроване-трикутне-*) expected=136 ;;
    центроване-шестикутне|центроване-шестикутне-*) expected=271 ;;
    пентагональне|пентагональне-*) expected=145 ;;
    семикутне|семикутне-*) expected=235 ;;
    шестикутне|шестикутне-*) expected=190 ;;
    добуток-сусідів|добуток-сусідів-*) expected=156 ;;
    перевернути|перевернути-*) expected="(5 4 3 2 1)" ;;
    лише-атоми|лише-атоми-*) expected="(1 3)" ;;
    розгорнути-один|розгорнути-один-*) expected="(4 3 2 1)" ;;
    збільшити-всі|збільшити-всі-*) expected="(4 3 2)" ;;
    *) echo "CONTEST_UNKNOWN_TASK: немає перевіреного очікуваного результату: $source" >&2; fail=1; continue ;;
  esac
  # Справжній нативний суд перевіряє змінні входи, негативного мутанта,
  # точний T5M roundtrip і paired/standalone SENS. Фіксований результат
  # сам по собі не доводить алгоритму і не може отримати «ПІДТВЕРДЖЕНО».
  if ! SENS_CONTEST_PROOF_ONLY=true SENS_BIN="$sens" SENS_TRIT_BIN="$trit" bash "$here/judge.sh" \
      "benchmarks/contest-uk/$name.sens" >"$scratch/native-proof.out" 2>"$scratch/native-proof.err"; then
    printf '%s\t-\t-\t0\tНЕ_ДОВЕДЕНО_АЛГОРИТМ\n' "$name"
    sed 's|^|SENS/Zig суд: |' "$scratch/native-proof.err" >&2
    fail=1
    continue
  fi
  source_sha="$(sha256sum "$source" | cut -d' ' -f1)"
  # SENS створює фізичний T5M; його бітовий вигляд відновлює Zig.
  # Раніше тут перевіряли "$view" ДО створення: кожен внесок помилково FAIL.
  if ! "$sens" --t5m-mint "$source" "$physical" >"$scratch/mint.out" 2>"$scratch/error" ||
     [[ ! -s "$physical" ]]; then
    printf '%s\t-\t-\t0\tПОМИЛКА_НАТИВНОГО_MINT\n' "$name"
    sed 's/^/SENS mint: /' "$scratch/error" >&2
    fail=1
    continue
  fi
  # «view» та «open» — один і той самий Zig-декодер.
  # Одного проходу досить; verify-view окремо перевіряє оберненість.
  if ! "$trit" open "$physical" > "$view" 2>"$scratch/error" ||
     [[ ! -s "$view" ]]; then
    printf '%s\t-\t-\t0\tПОМИЛКА_ZIG_VIEW\n' "$name"
    sed 's|^|Zig/T5M open: |' "$scratch/error" >&2
    fail=1
    continue
  fi
  if ! "$trit" verify-view "$physical" >"$scratch/verify.out" 2>"$scratch/error"; then
    printf '%s\t-\t-\t0\tПОМИЛКА_ОБЕРНЕНОСТІ_T5M\n' "$name"
    sed 's|^|Zig/T5M: |' "$scratch/error" >&2
    fail=1
    continue
  fi
  if ! cmp -s "$physical" "$committed" || ! cmp -s "$view" "$committed_view"; then
    printf '%s\t-\t-\t0\tЗАСТАРІЛА_ФІЗИЧНА_ПАРА\n' "$name"
    echo "CONTEST_PAIR_DRIFT source=$source action=refresh-executed-t5m-pair" >&2
    fail=1
    continue
  fi
  if [[ "$source_sha" != "$(sha256sum "$source" | cut -d' ' -f1)" ]]; then
    printf '%s\t-\t-\t0\tДЖЕРЕЛО_ЗМІНЕНО\n' "$name"
    fail=1
    continue
  fi
  if ! "$sens" --t5m-pair "$source" "$physical" >"$scratch/paired.out" 2>"$scratch/error" ||
     ! "$sens" "$physical" >"$scratch/standalone.out" 2>"$scratch/error"; then
    printf '%s\t-\t-\t0\tПОМИЛКА_ВИКОНАННЯ_SENS\n' "$name"
    sed 's/^/SENS eval: /' "$scratch/error" >&2
    fail=1
    continue
  fi
  # Порівнюємо байти результату, а не command substitution, яке
  # непомітно відкидає зайві LF і може зарахувати некоректний друк.
  printf '%s\n' "$expected" >"$scratch/expected.out"
  if ! cmp -s "$scratch/paired.out" "$scratch/standalone.out" ||
     ! cmp -s "$scratch/standalone.out" "$scratch/expected.out"; then
    printf '%s\t-\t-\t0\tНЕ_ЗБІГАЄТЬСЯ_РЕЗУЛЬТАТ\n' "$name"
    echo "CONTEST_OUTPUT_MISMATCH name=$name expected=$expected paired=$(cat "$scratch/paired.out") physical=$(cat "$scratch/standalone.out")" >&2
    fail=1
    continue
  fi
  samples=()
  for ((i=0; i<repeats; i++)); do
    start="$(date +%s%N)"
    if ! "$sens" "$physical" >"$scratch/run.out" 2>"$scratch/error" ||
       ! cmp -s "$scratch/run.out" "$scratch/standalone.out"; then
      echo "CONTEST_NONDETERMINISTIC name=$name repeat=$i" >&2
      sed 's/^/SENS: /' "$scratch/error" >&2
      fail=1
      samples=()
      break
    fi
    end="$(date +%s%N)"
    samples+=("$((end-start))")
  done
  if (( ${#samples[@]} != repeats )); then
    printf '%s\t-\t-\t0\tНЕСТАБІЛЬНЕ_ВИКОНАННЯ\n' "$name"
    continue
  fi
  if [[ "$source_sha" != "$(sha256sum "$source" | cut -d' ' -f1)" ]] ||
     ! cmp -s "$physical" "$committed" || ! cmp -s "$view" "$committed_view"; then
    printf '%s\t-\t-\t0\tДЖЕРЕЛО_ЧИ_ПАРА_ЗМІНИЛИСЯ\n' "$name"
    fail=1
    continue
  fi
  median="$(printf '%s\n' "${samples[@]}" | sort -n | sed -n "$((repeats/2+1))p")"
  printf '%s\t%s\t%s\t%s\tПІДТВЕРДЖЕНО\n' "$name" "$(wc -c < "$physical" | tr -d ' ')" "$median" "$repeats"
done
# Вимір: час окремого нативного CLI-процесу, включно із запуском.
# Це конкурс, а не релізний сертифікат чи час одного виклику evaluator.
exit "$fail"
