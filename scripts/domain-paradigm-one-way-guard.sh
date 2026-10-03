#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 BASE_SHA HEAD_SHA" >&2
  exit 2
fi

base_sha="$1"
head_sha="$2"
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

protected_paths=(
  crates/sens/src/bits.rs
  crates/sens/src/domain_words.rs
  crates/sens/src/source_words.rs
  crates/sens/src/source_packing.rs
  crates/sens/src/packed_bits.rs
  crates/sens/src/domain_identity.rs
  crates/sens/src/binary_framing.rs
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

is_exact_width_file() {
  local path="$1"

  is_protected_path "$path" && return 0
  case "$path" in
    crates/sens/src/*.rs|crates/sens/examples/*.rs|crates/sens/tests/*.rs) ;;
    *) return 1 ;;
  esac

  git cat-file -e "$head_sha:$path" 2>/dev/null || return 1
  git show "$head_sha:$path"     | grep -Eq 'Bits<|\bBit[1-8]\b|BinarySourceWord|PackedBitstream|PredicateBit|Racana2|Bija3|DomainWord|CoreDomainIdentity|DomainIdentity|DomainCall'
}

is_canonical_runtime_path() {
  local path="$1"
  case "$path" in
    crates/sens/src/eval/*.rs|crates/sens/src/environment.rs|crates/sens/src/domain_identity.rs|crates/sens/src/syntax.rs)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_surface_projection_boundary() {
  local path="$1"
  [[ "$path" == "crates/sens/src/eval/lower.rs" ]]
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

legacy_pattern='(^|[^[:alnum:]_])(Sid8|Sens8|Function8)([^[:alnum:]_]|$)|Value::Sid|sens!\([01]{8}\)'
byte_scatter_pattern='TAG_DOMAIN_IDENTITY|TAG_CALLABLE_DOMAIN|out\.push\([^)]*\.width\(\)[^)]*\)|out\.push\([^)]*\.packed_(bits|byte)\(\)[^)]*\)'
name_dispatch_pattern='semantic_id_for_surface|admitted_semantic_id_for_surface|registry_byte_for_surface|legacy_domain_identity_from_registry_byte|routed_sid_for_surface|surface_has_sid'
exact_domain_projection_pattern='domain_identity_for_surface|domain_identity_for_symbol'

failed=0
while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  is_exact_width_file "$path" || continue

  while IFS= read -r added; do
    is_executable_line "$added" || continue
    if printf '%s\n' "$added" | grep -Eq "$legacy_pattern"; then
      echo "PARADIGM-ONE-WAY violation: exact-width code adds legacy identity dependency" >&2
      echo "  file: $path" >&2
      echo "  line: $added" >&2
      failed=1
    fi
    if printf '%s\n' "$added" | grep -Eq "$byte_scatter_pattern"; then
      echo "PARADIGM-ONE-WAY violation: canonical domain identity is being scattered into byte fields" >&2
      echo "  file: $path" >&2
      echo "  line: $added" >&2
      failed=1
    fi
    if is_canonical_runtime_path "$path" \
      && printf '%s\n' "$added" | grep -Eq "$name_dispatch_pattern"; then
      echo "PARADIGM-ONE-WAY violation: canonical runtime adds name/legacy-driven semantic dispatch" >&2
      echo "  file: $path" >&2
      echo "  line: $added" >&2
      failed=1
    fi
    if is_canonical_runtime_path "$path" \
      && ! is_surface_projection_boundary "$path" \
      && printf '%s\n' "$added" | grep -Eq "$exact_domain_projection_pattern"; then
      echo "PARADIGM-ONE-WAY violation: runtime performs surface-to-domain projection after lowering boundary" >&2
      echo "  file: $path" >&2
      echo "  line: $added" >&2
      failed=1
    fi
  done < <(
    git -c core.quotePath=false diff --unified=0 "$base_sha" "$head_sha" -- "$path"       | awk '/^\+\+\+ / { next } /^\+/ { sub(/^\+/, ""); print }'
  )
done < <(git -c core.quotePath=false diff --name-only "$base_sha" "$head_sha")

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo "PARADIGM-ONE-WAY: PASS"
