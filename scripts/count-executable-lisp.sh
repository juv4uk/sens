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
executable=0
paired_only=0
bad=0
missing=0

while IFS= read -r -d '' source; do
  if [[ -n "$scope" && "$source" != "$scope"* ]]; then
    continue
  fi
  # Архів конкурсу не є чинною виконуваною програмою: не занижувати
  # покриття main через superseded/ (історія зберігається окремо).
  if [[ "$source" == */superseded/* ]]; then
    continue
  fi
  # Історичні бенчмарки теж враховуються у знаменнику, але ніколи
  # не підмінюють підтверджене нативне виконання.
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
  # Нативний mint для великих бібліотек потребує того самого кінцевого
  # бюджету, що й справжній перевірений refresh; 30s -> 180s від 256 KiB.
  mint_seconds="$seconds"
  if (( $(wc -c < "$source") >= 262144 && mint_seconds < 180 )); then
    mint_seconds=180
  fi
  # DEFINE-залежності мають бути завантажені тим самим SENS, що виконує
  # програму. Без них помилково оголошували працюючий файл не-виконуваним.
  binding_sources=()
  case "$source" in
    lib/reason.lisp|lib/forward.lisp)
      binding_sources=(--binding-source lib/unify.lisp) ;;
    lib/narrate.lisp)
      binding_sources=(--binding-source lib/unify.lisp --binding-source lib/reason.lisp) ;;
    lib/result-status.lisp)
      binding_sources=(--binding-source lib/unify.lisp --binding-source lib/knowledge.lisp --binding-source lib/reason.lisp) ;;
    lib/translation.lisp)
      binding_sources=(--binding-source lib/unify.lisp --binding-source lib/knowledge.lisp --binding-source lib/reason.lisp --binding-source lib/world.lisp --binding-source lib/yantra.lisp --binding-source lib/result-status.lisp) ;;
    tests/fixtures/mechanism-selector-1047-witness.lisp)
      binding_sources=(--binding-source lib/surface/semantic-registry-api.lisp --binding-source lib/mechanism-selector.lisp) ;;
    tests/semantic/d9-world-shape-module-events-laws.lisp|tests/semantic/world-exact-arity-witness.lisp)
      binding_sources=(--binding-source lib/world.lisp) ;;
  esac
  mint_flag=--t5m-mint
  if (( ${#binding_sources[@]} )); then
    mint_flag=--t5m-mint-pair
  fi
  if ! timeout "${mint_seconds}s" "$sens" "$mint_flag" "$source" "$scratch/mint.sens" "${binding_sources[@]}" >"$scratch/mint.out" 2>"$scratch/mint.err" ||
     ! cmp -s "$physical" "$scratch/mint.sens" ||
     ! timeout "${seconds}s" "$trit" open "$physical" >"$scratch/view" 2>"$scratch/view.err" ||
     ! cmp -s "$view" "$scratch/view" ||
     ! timeout "${seconds}s" "$trit" verify-view "$physical" >"$scratch/verify.out" 2>"$scratch/verify.err"; then
    (( bad += 1 ))
    printf 'NATIVE_INVERSE_FAILED\t%s\n' "$source" >&2
    continue
  fi
  (( inverse += 1 ))
  if ! timeout "${mint_seconds}s" "$sens" --t5m-pair "$source" "$physical" "${binding_sources[@]}" >"$scratch/paired.out" 2>"$scratch/paired.err"; then
    (( bad += 1 ))
    printf 'NATIVE_PAIRED_FAILED\t%s\n' "$source" >&2
    continue
  fi
  if ! timeout "${mint_seconds}s" "$sens" "$physical" >"$scratch/standalone.out" 2>"$scratch/standalone.err"; then
    (( paired_only += 1 ))
    printf 'NATIVE_PAIRED_ONLY\t%s\n' "$source" >&2
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

printf 'NATIVE_LISP_RESULT scope=%s sources=%s complete_triplets=%s exact_inverse=%s paired_and_standalone=%s paired_only=%s failed=%s missing_triplet=%s\n' \
  "${scope:-all}" "$sources" "$complete" "$inverse" "$executable" "$paired_only" "$bad" "$missing"
