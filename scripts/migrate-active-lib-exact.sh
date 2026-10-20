#!/usr/bin/env bash
# #1675 exact-domain active-library migration driver.
# Owner directive 2026-10-14: NO agent-imposed file HOLD/FREEZE. A failed
# consumer means WORK TO REPAIR, not a ban on migrating that source.
#
# Check mode reports exact convertible sites. Apply mode keeps attempted
# rewrites in the working tree, even if a consumer fails, for direct repair.
# It NEVER runs 'git checkout --' to discard migration work and NEVER returns
# success on an unresolved conversion or failing consumer.
#
# WARNING: run --apply only in a dedicated, clean worktree. Every source is
# checked for existing staged/unstaged changes before the rewrite, so an
# unrelated agent's modifications are not overwritten.
#
# Usage:
#   scripts/migrate-active-lib-exact.sh            # check only (default)
#   scripts/migrate-active-lib-exact.sh --apply    # attempt all + report fixes
#
# Exit: --check=0 means only exact source scan PASS (NOT runtime/release GO).
#       --apply=0 means all conversions and one consumer sweep PASS; it is
#       still not a physical T5M or independent semantic roundtrip certificate.

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
    elif [[ "$line" == *"convertible=0 "* && "$line" == *"blocked-unratified=0"* ]]; then :
    else echo "  $line"; offenders+=("$f:$flag"); fi
  done
}
check_group "--language" "${lang[@]}"
check_group "" "${ordinary[@]}"

# --- consumer verification: failing consumers are repair tasks, NOT file holds ---
# A rewrite is not DONE until consumers pass. Keep it visible when red so
# the correct domain mapping can be repaired without discarding the attempt.
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
  if [[ "$MODE" == "check" ]]; then
    echo "EXACT_SOURCE_SCAN_PASS: convertible=0; consumers=NOT_CHECKED; SENS/T5M=NOT_CERTIFIED"
    exit 0
  fi
  # Even a source with zero pending rewrites needs one actual consumer check.
  if verify_consumers; then
    echo "MIGRATION_SOURCE_CONSUMERS_PASS: no pending rewrites; SENS/T5M=NOT_CERTIFIED"
    exit 0
  fi
  echo "MIGRATION_INCOMPLETE: consumer failures above; no source freeze"
  exit 1
fi
echo "offenders: ${#offenders[@]} file(s)"
if [[ "$MODE" != "apply" ]]; then
  echo "re-run with --apply to rewrite + self-verify."
  exit 1
fi

# --- attempt every source; NEVER discard work or freeze a file ------------
needs_repair=(); applied=()
for entry in "${offenders[@]}"; do
  f="${entry%:*}"; flag="${entry##*:}"
  echo "  migrating: $f ${flag:-(ordinary)}"

  # Another agent's changes are not the migrator's to overwrite.
  if ! git diff --quiet -- "$f" || ! git diff --cached --quiet -- "$f"; then
    needs_repair+=("$f:existing-worktree-changes")
    echo "    REPAIR_REQUIRED: existing changes; coordinate edits, no automatic overwrite"
    continue
  fi

  if ! "${TOOL[@]}" $flag "$f"; then
    needs_repair+=("$f:converter-error")
    echo "    REPAIR_REQUIRED: converter error; source stays available, no file ban"
    continue
  fi
  applied+=("$f")
  echo "    SOURCE_REWRITTEN: $f; consumers await one shared verification"
done

# Many source files must not trigger many identical heavy cargo suites.
# Check consumers once, after ALL intended rewrites, never per source.
if (( ${#applied[@]} > 0 )); then
  if verify_consumers; then
    echo "CONSUMERS_PASS: one shared run for ${#applied[@]} rewritten file(s)"
  else
    needs_repair+=("consumer-sweep:failed")
    echo "REPAIR_REQUIRED: consumer failure; preserve migrated sources for repair"
  fi
fi

echo
echo "source-rewritten: ${#applied[@]}   needs-repair: ${#needs_repair[@]}"
for item in "${needs_repair[@]}"; do echo "  REPAIR_REQUIRED: $item"; done

# A report is not a semantic pass. Show every remaining convertible source,
# whether it was attempted, changed, or already in the caller's worktree.
offenders=()
check_group "--language" "${lang[@]}"
check_group "" "${ordinary[@]}"
echo "remaining convertible offenders: ${#offenders[@]}"
if (( ${#needs_repair[@]} != 0 || ${#offenders[@]} != 0 )); then
  echo "MIGRATION_INCOMPLETE: actionable diagnostics above; NO FILE HOLD"
  exit 1
fi
echo "MIGRATION_SOURCE_CONSUMERS_PASS: exact-domain source+consumers; SENS/T5M=NOT_CERTIFIED"
exit 0
