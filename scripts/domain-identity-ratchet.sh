#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 BASE_SHA HEAD_SHA" >&2
  exit 2
fi

base_sha="$1"
head_sha="$2"

canonical_paths=(
  crates/sens/src/syntax.rs
  crates/sens/src/value.rs
  crates/sens/src/environment.rs
  crates/sens/src/semantic_registry.rs
  crates/sens/src/language_items.rs
  crates/sens/src/eval/lower.rs
  crates/sens/src/eval/canon.rs
  crates/sens/src/eval/necessary_forms.rs
)

is_canonical_path() {
  local path="$1"
  local p
  for p in "${canonical_paths[@]}"; do
    [[ "$path" == "$p" ]] && return 0
  done
  return 1
}

is_executable_line() {
  local line="$1"
  local trimmed
  trimmed="$(printf '%s' "$line" | sed -E 's/^[[:space:]]+//')"
  [[ -n "$trimmed" ]] || return 1
  [[ "$trimmed" == //* ]] && return 1
  [[ "$trimmed" == '/*'* ]] && return 1
  [[ "${trimmed:0:1}" == "*" ]] && return 1
  return 0
}

legacy='(^|[^[:alnum:]_])(Sens8|Sid8|Function8)([^[:alnum:]_]|$)'
failed=0

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  is_canonical_path "$path" || continue

  while IFS= read -r added; do
    is_executable_line "$added" || continue
    if printf '%s\n' "$added" | grep -Eq "$legacy"; then
      echo "DOMAIN-IDENTITY-RATCHET violation: canonical semantic code adds bare legacy identity" >&2
      echo "  file: $path" >&2
      echo "  line: $added" >&2
      echo "Move compatibility conversion behind an explicit LegacySens8/adapter boundary." >&2
      failed=1
    fi
  done < <(
    git -c core.quotePath=false diff --unified=0 "$base_sha" "$head_sha" -- "$path" |
      awk '/^\+\+\+ / { next } /^\+/ { sub(/^\+/, ""); print }'
  )
done < <(git -c core.quotePath=false diff --name-only "$base_sha" "$head_sha")

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "DOMAIN-IDENTITY-RATCHET: PASS"
