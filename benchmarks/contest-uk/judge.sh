#!/usr/bin/env bash
# Нативний конкурс: SENS виконує, Zig звіряє T5M; Python/JSON не беруть участі.
set -euo pipefail
cd "$(dirname "$0")/../.."
sens="${SENS_BIN:-$PWD/target/debug/sens}"
trit="${SENS_TRIT_BIN:-$PWD/target/debug/sens-trit}"
[[ -x "$sens" && -x "$trit" ]] || { echo "Зберіть sens + sens-trit з --features benchmark-ast-visits" >&2; exit 2; }
error() { printf "КОНКУРС: ПОМИЛКА %s\n" "$*" >&2; exit 2; }
inputs=("benchmarks/contest-uk/факторіал.sens" "benchmarks/contest-uk/сума-до-n.sens" "benchmarks/contest-uk/довжина-списку.sens")
inputs+=("$@")
declare -A seen baseline
rows=""
for path in "${inputs[@]}"; do
  [[ "$path" == benchmarks/contest-uk/*.sens && "$path" != *"/../"* ]] || error "некоректний шлях: $path"
  [[ -z "${seen[$path]+yes}" ]] || continue
  seen[$path]=1
  source="${path%.sens}.lisp"; view="${path%.sens}"
  [[ -s "$path" && -f "$source" && -f "$view" && ! -L "$path" ]] || error "неповна трійка $path"
  name="${path##*/}"; name="${name%.sens}"
  case "$name" in факторіал*) task="факторіал";; сума-до-n*) task="сума-до-n";; довжина-списку*) task="довжина-списку";; *) error "невідома задача $name";; esac
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
  if [[ -z "${baseline[$task]+yes}" ]]; then baseline[$task]="$result"; fi
  [[ "$result" == "${baseline[$task]}" ]] || error "результат не дорівнює еталону $path"
  bytes="$(wc -c < "$path")"
  rows+="$task"$'\t'"$bytes"$'\t'"$nodes"$'\t'"$visits"$'\t'"$path"$'\n'
  printf "CONTEST_EXECUTED_PASS path=%s T5M=%s AST=%s visits=%s result=%s\n" "$path" "$bytes" "$nodes" "$visits" "$result"
  rm -- "$tmp/"*
  rmdir -- "$tmp"
done
printf "\nЗадача | T5M байти | AST | visits | Файл\n"
printf "%s" "$rows" | sort -t $'\t' -k1,1 -k2,2n -k3,3n -k4,4n
printf "CONTEST_NATIVE_PASS count=%s\n" "${#seen[@]}"
