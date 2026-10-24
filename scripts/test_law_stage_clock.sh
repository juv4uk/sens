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
# Два окремі нативні маршрути мають отримати різні назви етапів.
# /bin/true тут перевіряє лише механіку оболонки, не семантику SENS.
sens=/bin/false
trit=/bin/true
profile_stage clock-clean sens-standalone timeout 5s "$trit" eval fixture.sens
profile_stage clock-core4 sens-standalone timeout 5s "$trit" eval-core4 fixture.sens
unknown_code=0
profile_stage clock-unknown sens-standalone timeout 5s "$trit" decode fixture.sens || unknown_code=$?
if [[ "$unknown_code" != 2 ]]; then
  echo "LAW_CLOCK_UNKNOWN_EXECUTOR expected=2 actual=$unknown_code" >&2
  exit 1
fi
negative_code=0
profile_stage clock-negative direct /bin/false || negative_code=$?
if [[ "$negative_code" != 1 ]]; then
  echo "LAW_CLOCK_EXIT_MISMATCH expected=1 actual=$negative_code" >&2
  exit 1
fi

rows=0
while IFS=$'\t' read -r id stage exit_code elapsed_us; do
  [[ "$elapsed_us" =~ ^[0-9]+$ ]] || {
    echo "LAW_CLOCK_TSV_INVALID row=$rows" >&2
    exit 1
  }
  case "$id:$stage:$exit_code" in
    clock-positive:direct:0|clock-negative:direct:1|clock-clean:sens-standalone-trit-clean:0|clock-core4:sens-standalone-trit-core4:0) ;;
    *) echo "LAW_CLOCK_STATUS_INVALID id=$id actual=$exit_code" >&2; exit 1 ;;
  esac
  rows=$((rows + 1))
done < "$evidence/law-stage-timings.tsv"
[[ "$rows" == 4 ]] || {
  echo "LAW_CLOCK_ROW_COUNT expected=4 actual=$rows" >&2
  exit 1
}
echo "LAW_CLOCK_PASS stage_rows=4 failure_exit=1 profiles=clean,core4 source=$source_path"
