#!/usr/bin/env bash
# Перевірка реєстру ARCHIVE та межі SENS_SOURCE. Це механізм гейту, не мовний оракул.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
first_field="${SENS_PR_FIRST_FIELD:-}"
while (($#)); do
  case "$1" in
    --root) root="$2"; shift 2 ;;
    --first-field) first_field="$2"; shift 2 ;;
    *) echo "LANGUAGE_POLICY_ARCHIVE=FAIL unknown_argument=$1"; exit 2 ;;
  esac
done
cd "$root"
registry="docs/language-policy-archive.md"
if [[ ! -f "$registry" ]]; then
  echo "LANGUAGE_POLICY_ARCHIVE=FAIL missing_registry=$registry"
  exit 1
fi
trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}
declare -A archived=()
rows=0
bad=0
while IFS= read -r line || [[ -n "$line" ]]; do
  # Only table body rows that end with ARCHIVE (pipe-separated).
  case "$line" in
    *'|' *ARCHIVE*) ;;
    *'|'*ARCHIVE*) ;;
    *) continue ;;
  esac
  case "$line" in
    *'---'*) continue ;;
  esac
  case "$line" in
    \|*) line="${line#|}" ;;
  esac
  IFS='|' read -r artifact location reason status _ <<<"$line"
  artifact="$(trim "$artifact")"
  location="$(trim "$location")"
  reason="$(trim "$reason")"
  status="$(trim "$status")"
  artifact="${artifact//\`/}"
  location="${location//\`/}"
  status="${status//\`/}"
  [[ "$artifact" == "Артефакт" || -z "$artifact" ]] && continue
  if [[ -z "$location" || "$status" != "ARCHIVE" ]]; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL malformed_row artifact=$artifact location=$location status=$status"
    bad=1
    continue
  fi
  if [[ ! "$reason" =~ (/juv4uk/sens/commit/[0-9a-f]{7,40}|https://github\.com/juv4uk/sens/commit/[0-9a-f]{7,40}) ]]; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL missing_commit_link artifact=$artifact"
    bad=1
  fi
  if [[ -n "${archived[$location]+x}" ]]; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL duplicate_location=$location"
    bad=1
  fi
  archived["$location"]=1
  if ! git ls-files --error-unmatch -- "$location" >/dev/null 2>&1; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL not_tracked=$location"
    bad=1
  fi
  rows=$((rows + 1))
done < "$registry"

is_testbench_location() {
  case "$1" in
    tests/*|benchmarks/*|packaging/tests/*|*/tests/*|*/benches/*|*/benchmarks/*|scripts/test_*.py|.github/scripts/test_*.py) return 0 ;;
    *) return 1 ;;
  esac
}
is_foreign_testbench() {
  is_testbench_location "$1" || return 1
  case "$1" in
    *.py|*.pyi|*.js|*.mjs|*.cjs|*.ts|*.tsx|*.jsx|*.rb|*.go|*.php|*.rkt|*.lua|*.swift|*.java|*.kt|*.scala|*.pl|*.jl) return 0 ;;
    *) return 1 ;;
  esac
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if is_foreign_testbench "$path" && [[ -z "${archived[$path]+x}" ]]; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL unregistered_exclusion=$path"
    bad=1
  fi
done <<<"$(git ls-files | grep -E '\.(py|pyi|js|mjs|cjs|ts|tsx|jsx|rb|go|php|rkt|lua|swift|java|kt|scala|pl|jl)$' || true)"

for path in "${!archived[@]}"; do
  if ! is_foreign_testbench "$path"; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL row_not_excluded_artifact=$path"
    bad=1
  fi
done

first_line="${first_field%%$'\n'*}"
added=()
if git rev-parse --verify HEAD^ >/dev/null 2>&1; then
  while IFS= read -r path; do
    [[ -n "$path" ]] && added+=("$path")
  done <<<"$(git diff --diff-filter=A --name-only HEAD^ HEAD || true)"
fi
for path in "${added[@]:-}"; do
  if is_testbench_location "$path"; then
    if [[ "$first_line" != SENS_SOURCE=* ]]; then
      echo "LANGUAGE_POLICY_ARCHIVE=FAIL SENS_SOURCE_FIRST_FIELD_REQUIRED path=$path"
      bad=1
    fi
    if is_foreign_testbench "$path"; then
      echo "LANGUAGE_POLICY_ARCHIVE=FAIL NEW_FOREIGN_TEST_ARCHIVE_FORBIDDEN path=$path"
      bad=1
    fi
  fi
done

echo "ARCHIVE (поза мовним коридором): $rows артефактів — $registry"
if (( bad != 0 )); then
  echo "LANGUAGE_POLICY_ARCHIVE=FAIL rows=$rows"
  exit 1
fi
echo "LANGUAGE_POLICY_ARCHIVE=VALID rows=$rows evidence=NOT_VERIFIED"
