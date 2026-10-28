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
  # Невідомі назви та мовні закони перевіряються SENS-судом вище;
  # цей скрипт вимірює лише фізичний носій і час виконання.
  # Побайтові знімки до суду: без генерації digest.
  source_snapshot="$scratch/$name.source.snapshot"
  pair_snapshot="$scratch/$name.sens.snapshot"
  view_snapshot="$scratch/$name.view.snapshot"
  cp -- "$source" "$source_snapshot"
  cp -- "$committed" "$pair_snapshot"
  cp -- "$committed_view" "$view_snapshot"
  # Справжній суд уже виконує SENS mint, Zig inverse, paired/standalone,
  # перевірку результату, негативного мутанта і змінних входів.
  # Не повторювати цей дорогий нативний доказ для того самого файлу.
  if ! SENS_CONTEST_PROOF_ONLY=true SENS_BIN="$sens" SENS_TRIT_BIN="$trit" bash "$here/judge.sh" \
      "benchmarks/contest-uk/$name.sens" >"$scratch/native-proof.out" 2>"$scratch/native-proof.err"; then
    printf '%s\t-\t-\t0\tНЕ_ДОВЕДЕНО_АЛГОРИТМ\n' "$name"
    sed 's|^|SENS/Zig суд: |' "$scratch/native-proof.err" >&2
    fail=1
    continue
  fi
  if ! cmp -s "$source_snapshot" "$source" ||
     ! cmp -s "$pair_snapshot" "$committed" ||
     ! cmp -s "$view_snapshot" "$committed_view"; then
    printf '%s\t-\t-\t0\tДЖЕРЕЛО_ЧИ_ПАРА_ЗМІНИЛИСЯ\n' "$name"
    fail=1
    continue
  fi
  # Після proof один автономний SENS запуск — тільки базова точка
  # виміру. Жодної сторонньої семантики чи Python/JSON.
  if ! "$trit" eval-core4 "$committed" >"$scratch/standalone.out" 2>"$scratch/error"; then
    printf '%s\t-\t-\t0\tПОМИЛКА_ВИКОНАННЯ_SENS\n' "$name"
    sed 's/^/SENS eval: /' "$scratch/error" >&2
    fail=1
    continue
  fi
  # Правильність уже перевіряє нативний judge.sh до старту вимірів.
  # Повторна таблиця очікуваних результатів у shell була стороннім оракулом.
  samples=()
  for ((i=0; i<repeats; i++)); do
    start="$(date +%s%N)"
    if ! "$trit" eval-core4 "$committed" >"$scratch/run.out" 2>"$scratch/error" ||
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
  if ! cmp -s "$source_snapshot" "$source" ||
     ! cmp -s "$pair_snapshot" "$committed" ||
     ! cmp -s "$view_snapshot" "$committed_view"; then
    printf '%s\t-\t-\t0\tДЖЕРЕЛО_ЧИ_ПАРА_ЗМІНИЛИСЯ\n' "$name"
    fail=1
    continue
  fi
  median="$(printf '%s\n' "${samples[@]}" | sort -n | sed -n "$((repeats/2+1))p")"
  printf '%s\t%s\t%s\t%s\tПІДТВЕРДЖЕНО\n' "$name" "$(wc -c < "$committed" | tr -d ' ')" "$median" "$repeats"
done
# Вимір: час окремого нативного CLI-процесу, включно із запуском.
# Це конкурс, а не релізний сертифікат чи час одного виклику evaluator.
exit "$fail"
