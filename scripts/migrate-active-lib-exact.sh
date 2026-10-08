#!/usr/bin/env bash
# #1675 completion driver v2 — migrate the active authored Lisp library to exact
# domain codes with the CANONICAL converter, then VERIFY the migration against
# its consumers. Any file whose migration breaks a consumer is HELD (reverted),
# so a non-identity-preserving rewrite can never land.
#
# Why v2: a bare rewrite is not a migration. A migrated source has derived
# consumers — tests that `include_str!` the file, generated reports, generated
# registries. The canonical tool rewrites heads only; it does not know whether a
# head was a call or context-sensitive. v2 closes that gap by executing the
# consumers after each file and holding any file that fails them.
#
# Usage:
#   scripts/migrate-active-lib-exact.sh            # check only (default)
#   scripts/migrate-active-lib-exact.sh --apply    # rewrite + self-verify (holds bad files)
#
# Exit: 0 iff every active file reports convertible=0 OR is held with a reason.

set -euo pipefail

MODE="check"
case "${1:-}" in
  ""|--check) MODE="check" ;;
  --apply)    MODE="apply" ;;
  *) echo "usage: $0 [--check|--apply]" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "${SENS_TO_SENS:-}" ]]; then TOOL=($SENS_TO_SENS)
elif [[ -x target/release/sens-to-sens ]]; then TOOL=(target/release/sens-to-sens)
elif [[ -x target/debug/sens-to-sens ]]; then TOOL=(target/debug/sens-to-sens)
else TOOL=(cargo run --quiet -p sens-cli --bin sens-to-sens --); fi

# --- gate predicates (mirror crates/sens-cli/tests/active_lib_sens_completion.rs) ---
is_explicit_non_implementation() {
  case "$1" in
    lib/generated/*|lib/surface/*|lib/machine/encoding/coverage.lisp) return 0 ;;
    *) return 1 ;;
  esac
}
is_language_definition_file() { [[ "$1" =~ ^lib/core[^/]*\.lisp$ ]]; }

active=()
while IFS= read -r f; do is_explicit_non_implementation "$f" || active+=("$f"); done \
  < <(find lib -type f -name '*.lisp' | sed 's|^\./||' | LC_ALL=C sort)
lang=(); ordinary=()
for f in "${active[@]}"; do if is_language_definition_file "$f"; then lang+=("$f"); else ordinary+=("$f"); fi; done
echo "active authored lib: ${#active[@]} files (${#lang[@]} language, ${#ordinary[@]} ordinary)"

offenders=()
check_group() {
  local flag="$1"; shift; local -a group=("$@"); (( ${#group[@]} )) || return 0
  local out f line; out="$("${TOOL[@]}" --check $flag "${group[@]}" 2>&1 || true)"
  for f in "${group[@]}"; do
    line="$(grep -F "$f: convertible=" <<<"$out" | head -1 || true)"
    if [[ -z "$line" ]]; then echo "  ?? no verdict for $f"; offenders+=("$f:$flag")
    elif [[ "$line" == *"convertible=0"* ]]; then :
    else echo "  $line"; offenders+=("$f:$flag"); fi
  done
}
check_group "--language" "${lang[@]}"
check_group "" "${ordinary[@]}"

# --- consumer verification: the migration must not change behaviour ----------
# These are the consumers that embed or depend on active lib sources. A rewrite
# that breaks any of them is not identity-preserving and must be held.
verify_consumers() {
  local rc=0
  # derived artifacts must stay fresh after any rewrite
  python3 scripts/public_api_inventory.py --check >/dev/null 2>&1 || { echo "    consumer FAIL: public-api-discovery stale"; rc=1; }
  python3 scripts/generate-encoder-coverage-input.py --check >/dev/null 2>&1 || { echo "    consumer FAIL: encoder-coverage input stale"; rc=1; }
  # tests that include_str! active lib sources
  if ! cargo test -q -p sens \
        --test compiler_l1_l5_role --test compiler_nucleus_sens --test compiler_nucleus_diff \
        --test compiler_role_cutover --test compiler_domain_shape --test compiler_selfhost_role_closure \
        >/tmp/consumer.log 2>&1; then
    echo "    consumer FAIL: compiler nucleus/role tests"; tail -5 /tmp/consumer.log | sed 's/^/      /'; rc=1
  fi
  return $rc
}

if (( ${#offenders[@]} == 0 )); then
  echo "OK: every active file reports convertible=0 — completion gate satisfied."
  exit 0
fi
echo "offenders: ${#offenders[@]} file(s)"
if [[ "$MODE" != "apply" ]]; then
  echo "re-run with --apply to rewrite + self-verify."
  exit 1
fi

# --- apply one file at a time; hold any file whose rewrite breaks a consumer --
held=(); applied=()
for entry in "${offenders[@]}"; do
  f="${entry%:*}"; flag="${entry##*:}"
  echo "  trying: $f ${flag:-(ordinary)}"
  "${TOOL[@]}" $flag "$f"
  if verify_consumers; then
    applied+=("$f"); echo "    OK (identity preserved)"
  else
    git checkout -- "$f" 2>/dev/null || true
    held+=("$f"); echo "    HELD (reverted — rewrite not identity-preserving; needs tool fix)"
  fi
done

echo
echo "applied: ${#applied[@]}   held: ${#held[@]}"
for h in "${held[@]}"; do echo "  HELD: $h"; done

# re-check: held files stay offenders by design
offenders=(); check_group "--language" "${lang[@]}"; check_group "" "${ordinary[@]}"
echo "remaining convertible offenders (incl. held): ${#offenders[@]}"
# success = every non-held file is clean
(( ${#held[@]} == 0 )) && exit 0 || exit 1
