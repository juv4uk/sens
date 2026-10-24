#!/usr/bin/env bash
# Механічна самоперевірка годинника профілю; вердикти Lisp визначає лише SENS.
set -euo pipefail

source_path="scripts/prove-lisp-semantic-t5m.sh"
test -f "$source_path"
# Беремо ту саму функцію, що викликає нативний закон, без дублювання її механізму.
source <(sed -n '/^profile_stage() {/,/^}/p' "$source_path")
declare -F profile_stage >/dev/null
evidence="$(mktemp -d)"
trap 'rm -f -- "$evidence/law-stage-timings.tsv"; rmdir -- "$evidence"' EXIT

date() {
  echo "LAW_CLOCK_UNEXPECTED_DATE" >&2
  return 91
}
profile_stage clock-positive direct /bin/true
negative_code=0
profile_stage clock-negative direct /bin/false || negative_code=$?
if [[ "$negative_code" != 1 ]]; then
  echo "LAW_CLOCK_EXIT_MISMATCH expected=1 actual=$negative_code" >&2
  exit 1
fi

rows=0
while IFS=$'\t' read -r id stage exit_code elapsed_us; do
  [[ "$stage" == direct && "$elapsed_us" =~ ^[0-9]+$ ]] || {
    echo "LAW_CLOCK_TSV_INVALID row=$rows" >&2
    exit 1
  }
  case "$id:$exit_code" in
    clock-positive:0|clock-negative:1) ;;
    *) echo "LAW_CLOCK_STATUS_INVALID id=$id actual=$exit_code" >&2; exit 1 ;;
  esac
  rows=$((rows + 1))
done < "$evidence/law-stage-timings.tsv"
[[ "$rows" == 2 ]] || {
  echo "LAW_CLOCK_ROW_COUNT expected=2 actual=$rows" >&2
  exit 1
}
echo "LAW_CLOCK_PASS stage_rows=2 failure_exit=1 source=$source_path"
