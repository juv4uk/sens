#!/usr/bin/env bash
# Перевірка реєстру ARCHIVE та заборона нових сторонніх test/benchmark runners.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
while (($#)); do
  case "$1" in
    --root) root="$2"; shift 2 ;;
    *) echo "LANGUAGE_POLICY_ARCHIVE=FAIL unknown_argument=$1"; exit 2 ;;
  esac
done
cd "$root"
# Ідентичність — джерельний шлях плюс точні байти, а не digest.
# Ці файли утворюють активний SENS/Zig T5M path; жоден з них не має
# створювати SHA-256 квитанції.
digest_free_paths=(
  "scripts/execute_changed_lisp_t5m.sh"
  "scripts/prove-lisp-semantic-t5m.sh"
  "scripts/prove-lisp-language-laws.sh"
  "scripts/ci-rust-mechanism-checks.sh"
  "scripts/refresh-verified-t5m-pair.sh"
  "scripts/refresh-executed-t5m-pair.sh"
  "benchmarks/contest-uk/judge.sh"
  "benchmarks/contest-uk/run-native.sh"
  "benchmarks/contest-uk/mint-pending.sh"
)
# Check executable carriers for hash generation. Workflow guards may mention
# forbidden tokens as policy text and are therefore not scanned as generators.
contains_digest_generator() {
  local candidate="$1"
  # У release-preflight є guard, який ЛИШЕ шукає заборонену callable-назву
  # sha256-hex. Це не створення квитанції. Відфільтровуємо тільки точний
  # рядок цього сканера, але лишаємо перевірку решти workflow на генератори.
  if [[ "$candidate" == ".github/workflows/release-preflight.yml" ]]; then
    local executable_source
    executable_source="$(grep -vF "if grep -nEi 'json-parse|sha256-hex|JSON-PARSE|SHA256-HEX'" "$candidate")"
    grep -qF sha256sum <<<"$executable_source" ||
      grep -qF sha256-hex <<<"$executable_source" ||
      grep -qF .sha256 <<<"$executable_source" ||
      grep -qF SHA256SUMS <<<"$executable_source"
  else
    grep -qF sha256sum "$candidate" ||
      grep -qF sha256-hex "$candidate" ||
      grep -qF .sha256 "$candidate" ||
      grep -qF SHA256SUMS "$candidate"
  fi
}

contains_foreign_semantic_runner() {
  local candidate="$1"
  # Канонічні носії не запускають зовнішні семантичні оракули.
  # Перевіряємо лише виконувальні рядки, не коментарі з описом політики.
  sed '/^[[:space:]]*#/d; s/[[:space:]]#.*$//' "$candidate" |
    grep -Eiq '^[[:space:]]*(env[[:space:]]+)?(python3?|pytest|jq)([[:space:]]|$)|[|;&][[:space:]]*(python3?|pytest|jq)([[:space:]]|$)|\$\((python3?|pytest|jq)([[:space:]]|$)'
}
for path in "${digest_free_paths[@]}"; do
  [[ -f "$path" ]] || continue
  if contains_digest_generator "$path"; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL digest_creation_forbidden path=$path" >&2
    exit 1
  fi
  if contains_foreign_semantic_runner "$path"; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL foreign_semantic_runner_forbidden path=$path" >&2
    exit 1
  fi
done
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
  [[ "$line" == *"| ARCHIVE |"* || "$line" == *"| ARCHIVE" ]] || continue
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
  commit_link_re='(/juv4uk/sens/commit/[0-9a-f]{7,40}|https://github\.com/juv4uk/sens/commit/[0-9a-f]{7,40})'
  if [[ ! "$reason" =~ $commit_link_re ]]; then
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
    *.py|*.pyi|*.js|*.mjs|*.cjs|*.ts|*.tsx|*.jsx|*.rb|*.go|*.php|*.rkt|*.lua|*.swift|*.java|*.kt|*.scala|*.pl|*.jl|*.sh|*.f90|*.clp|*.sbcl|*.fs|*.v) return 0 ;;
    *) return 1 ;;
  esac
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if is_foreign_testbench "$path" && [[ -z "${archived[$path]+x}" ]]; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL unregistered_exclusion=$path"
    bad=1
  fi
done <<<"$(git ls-files | grep -E '\.(py|pyi|js|mjs|cjs|ts|tsx|jsx|rb|go|php|rkt|lua|swift|java|kt|scala|pl|jl|sh|f90|clp|sbcl|fs|v)$' || true)"

for path in "${!archived[@]}"; do
  if ! is_foreign_testbench "$path"; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL row_not_excluded_artifact=$path"
    bad=1
  fi
done

added=()
if git rev-parse --verify HEAD^ >/dev/null 2>&1; then
  while IFS= read -r path; do
    [[ -n "$path" ]] && added+=("$path")
  done <<<"$(git diff --diff-filter=A --name-only HEAD^ HEAD || true)"
fi
for path in "${added[@]:-}"; do
  if is_testbench_location "$path"; then
    if [[ "$event_name" == "pull_request" && "$first_line" != SENS_SOURCE=* ]]; then
      bad=1
    fi
    # Never admit a newly added foreign-language test or benchmark runner.
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
echo "LANGUAGE_POLICY_ARCHIVE=VALID rows=$rows"
