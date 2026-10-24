#!/usr/bin/env bash
# Негативний контроль: частковий список із git ls-files не означає повний корпус.
set -euo pipefail
cd "$(dirname "$0")/.."

git() {
  if [[ "${1:-}" == "ls-files" ]]; then
    printf '%s\0' 'tests/semantic/d1-not-law.lisp'
    return 17
  fi
  command git "$@"
}
export -f git

set +e
output="$(SENS_BIN=/bin/true SENS_TRIT_BIN=/bin/true bash scripts/count-executable-lisp.sh 2>&1)"
status=$?
set -e

if [[ "$status" != 2 || "$output" != *"NATIVE_COUNT_GIT_FILES_FAILED layer=inventory"* ]]; then
  printf 'NATIVE_GIT_INVENTORY_MUTANT_UNDETECTED exit=%s output=%s\n' "$status" "$output" >&2
  exit 1
fi
echo 'NATIVE_GIT_INVENTORY_REJECTED: partial git ls-files failure cannot certify full corpus'
