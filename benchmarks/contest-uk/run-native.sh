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
for source in "$here"/*.lisp; do
  [[ -f "$source" && ! -L "$source" ]] || continue
  name="$(basename -- "$source" .lisp)"
  case "$name" in
    довжина-списку|довжина-списку-*) expected=8 ;;
    сума-до-n|сума-до-n-*) expected=5050 ;;
    факторіал|факторіал-*) expected=3628800 ;;
    *) echo "CONTEST_SKIP: немає перевіреного очікуваного результату: $source" >&2; continue ;;
  esac
  physical="$scratch/$name.sens"
  view="$scratch/$name"
  committed="$here/$name.sens"
  committed_view="$here/$name"
  if [[ ! -f "$committed" || -L "$committed" ||
        ! -f "$committed_view" || -L "$committed_view" ]]; then
    printf '%s\t-\t-\t0\tНЕМАЄ_ОБЕРНЕНОЇ_ПАРИ\n' "$name"
    fail=1
    continue
  fi
  source_sha="$(sha256sum "$source" | cut -d' ' -f1)"
  if ! "$sens" --t5m-mint-pair "$source" "$physical" >"$scratch/mint.out" 2>"$scratch/error" ||
     [[ ! -s "$physical" || ! -s "$view" ]]; then
    printf '%s\t-\t-\t0\tПОМИЛКА_НАТИВНОГО_MINT\n' "$name"
    sed 's/^/SENS mint: /' "$scratch/error" >&2
    fail=1
    continue
  fi
  if ! "$trit" verify-view "$physical" >"$scratch/verify.out" 2>"$scratch/error" ||
     ! "$trit" open "$physical" >"$scratch/opened.view" 2>"$scratch/error" ||
     ! cmp -s "$view" "$scratch/opened.view"; then
    printf '%s\t-\t-\t0\tПОМИЛКА_ОБЕРНЕНОСТІ_T5M\n' "$name"
    sed 's/^/Zig/T5M: /' "$scratch/error" >&2
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
  if ! cmp -s "$scratch/paired.out" "$scratch/standalone.out" ||
     [[ "$(cat "$scratch/standalone.out")" != "$expected" ]]; then
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
