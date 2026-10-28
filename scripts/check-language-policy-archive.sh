#!/usr/bin/env bash
# Перевірка історичного реєстру ARCHIVE; всі мови дозволені з 2026-10-28.
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

for path in "${digest_free_paths[@]}"; do
  [[ -f "$path" ]] || continue
  if contains_digest_generator "$path"; then
    echo "LANGUAGE_POLICY_ARCHIVE=FAIL digest_creation_forbidden path=$path" >&2
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

# 2026-10-28: archive is a historical registry, not a denylist for languages.
# Keep evidence/row consistency, but allow new research code in any language.
echo "ARCHIVE (поза мовним коридором): $rows артефактів — $registry"
if (( bad != 0 )); then
  echo "LANGUAGE_POLICY_ARCHIVE=FAIL rows=$rows"
  exit 1
fi
echo "LANGUAGE_POLICY_ARCHIVE=VALID rows=$rows"
