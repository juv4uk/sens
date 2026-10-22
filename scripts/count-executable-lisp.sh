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
  ""|lib/|tests/|benchmarks/|benchmarks/contest-uk/|research/|knowledge/|experiments/|scripts/) ;;
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
  if ! timeout "${seconds}s" "$sens" --t5m-mint "$source" "$scratch/mint.sens" >"$scratch/mint.out" 2>"$scratch/mint.err" ||
     ! cmp -s "$physical" "$scratch/mint.sens" ||
     ! timeout "${seconds}s" "$trit" open "$physical" >"$scratch/view" 2>"$scratch/view.err" ||
     ! cmp -s "$view" "$scratch/view" ||
     ! timeout "${seconds}s" "$trit" verify-view "$physical" >"$scratch/verify.out" 2>"$scratch/verify.err"; then
    (( bad += 1 ))
    printf 'NATIVE_INVERSE_FAILED\t%s\n' "$source" >&2
    continue
  fi
  (( inverse += 1 ))
  if ! timeout "${seconds}s" "$sens" --t5m-pair "$source" "$physical" >"$scratch/paired.out" 2>"$scratch/paired.err"; then
    (( bad += 1 ))
    printf 'NATIVE_PAIRED_FAILED\t%s\n' "$source" >&2
    continue
  fi
  if ! timeout "${seconds}s" "$sens" "$physical" >"$scratch/standalone.out" 2>"$scratch/standalone.err"; then
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
