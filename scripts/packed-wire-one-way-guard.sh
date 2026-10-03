#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 <base-sha> <head-sha>" >&2
  exit 2
fi

base_sha="$1"
head_sha="$2"

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

protected_paths=(
  crates/sens/src/source_words.rs
  crates/sens/src/source_packing.rs
  crates/sens/src/packed_bits.rs
  crates/sens/src/domain_identity.rs
  crates/sens/src/syntax.rs
)

is_protected_path() {
  local path="$1"
  local item
  for item in "${protected_paths[@]}"; do
    [[ "$path" == "$item" ]] && return 0
  done
  return 1
}

is_executable_line() {
  local line="$1"
  local trimmed
  trimmed=$(printf '%s' "$line" | sed -E 's/^[[:space:]]+//')

  [[ -z "$trimmed" ]] && return 1
  [[ "$trimmed" == //* ]] && return 1
  [[ "$trimmed" == '/*'* ]] && return 1
  [[ "${trimmed:0:1}" == "*" ]] && return 1
  return 0
}

inflation_pattern='TAG_DOMAIN_IDENTITY|put_domain_identity|out\.push\([^)]*\.width\(\)[^)]*u8[^)]*\)|out\.push\([^)]*\.packed_bits\(\)[^)]*\)|width[[:space:]]*:[[:space:]]*u8'

failed=0
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  is_protected_path "$path" || continue

  while IFS= read -r added; do
    is_executable_line "$added" || continue
    if printf '%s\n' "$added" | grep -Eq "$inflation_pattern"; then
      echo "PACKED-WIRE-ONE-WAY violation: canonical exact-width path adds byte-inflation machinery" >&2
      echo "  file: $path" >&2
      echo "  line: $added" >&2
      echo "  law: Dn contributes exactly n semantic payload bits; per-word tag/width bytes are non-canonical" >&2
      failed=1
    fi
  done < <(
    git -c core.quotePath=false diff --unified=0 "$base_sha" "$head_sha" -- "$path" \
      | awk '/^\+\+\+ / { next } /^\+/ { sub(/^\+/, ""); print }'
  )
done < <(git -c core.quotePath=false diff --name-only "$base_sha" "$head_sha")

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "PACKED-WIRE-ONE-WAY: PASS"
