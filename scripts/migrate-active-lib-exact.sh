#!/usr/bin/env bash
# #1675 completion driver — migrate the active authored Lisp library to exact
# domain codes using the CANONICAL converter, until the completion gate
# (crates/sens-cli/tests/active_lib_sens_completion.rs) is satisfied.
#
# The gate requires every active lib/**/*.lisp file — EXCEPT the explicit
# non-implementation set (lib/generated/, lib/surface/,
# lib/machine/encoding/coverage.lisp) — to report `convertible=0` from
# `sens-to-sens --check`. Files named lib/core*.lisp are inspected with
# --language so table-owned language definitions resolve correctly.
#
# This script mirrors those two predicates EXACTLY, so its verdict is the gate's.
#
# Usage:
#   scripts/migrate-active-lib-exact.sh            # check only (default, no writes)
#   scripts/migrate-active-lib-exact.sh --apply    # rewrite offending files in place
#
# Exit status: 0 iff every active file reports convertible=0.

set -euo pipefail

MODE="check"
case "${1:-}" in
  ""|--check) MODE="check" ;;
  --apply)    MODE="apply" ;;
  *) echo "usage: $0 [--check|--apply]" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- locate the canonical converter -------------------------------------------
if [[ -n "${SENS_TO_SENS:-}" ]]; then
  TOOL=($SENS_TO_SENS)
elif [[ -x target/release/sens-to-sens ]]; then
  TOOL=(target/release/sens-to-sens)
elif [[ -x target/debug/sens-to-sens ]]; then
  TOOL=(target/debug/sens-to-sens)
else
  TOOL=(cargo run --quiet -p sens-cli --bin sens-to-sens --)
fi

# --- predicates mirroring the gate (do not edit one without the other) --------
is_explicit_non_implementation() {
  case "$1" in
    lib/generated/*|lib/surface/*|lib/machine/encoding/coverage.lisp) return 0 ;;
    *) return 1 ;;
  esac
}
is_language_definition_file() {
  [[ "$1" =~ ^lib/core[^/]*\.lisp$ ]]
}

# --- collect the active set ----------------------------------------------------
active=()
while IFS= read -r f; do
  is_explicit_non_implementation "$f" || active+=("$f")
done < <(find lib -type f -name '*.lisp' | sed 's|^\./||' | LC_ALL=C sort)

lang=(); ordinary=()
for f in "${active[@]}"; do
  if is_language_definition_file "$f"; then lang+=("$f"); else ordinary+=("$f"); fi
done

echo "active authored lib: ${#active[@]} files (${#lang[@]} language, ${#ordinary[@]} ordinary)"

# --- check one group and record offenders -------------------------------------
offenders=()
check_group() {
  local flag="$1"; shift
  local -a group=("$@")
  (( ${#group[@]} )) || return 0
  local out line f
  out="$("${TOOL[@]}" --check $flag "${group[@]}" 2>&1 || true)"
  for f in "${group[@]}"; do
    line="$(grep -F "$f: convertible=" <<<"$out" | head -1 || true)"
    if [[ -z "$line" ]]; then
      echo "  ?? no verdict for $f"
      offenders+=("$f:$flag")
    elif [[ "$line" == *"convertible=0"* ]]; then
      : # clean
    else
      echo "  $line"
      offenders+=("$f:$flag")
    fi
  done
}

check_group "--language" "${lang[@]}"
check_group "" "${ordinary[@]}"

if (( ${#offenders[@]} == 0 )); then
  echo "OK: every active file reports convertible=0 — completion gate satisfied."
  exit 0
fi

echo "offenders: ${#offenders[@]} file(s)"
if [[ "$MODE" != "apply" ]]; then
  echo "re-run with --apply to rewrite them with the canonical converter."
  exit 1
fi

# --- apply per offender, then re-verify ---------------------------------------
for entry in "${offenders[@]}"; do
  f="${entry%:*}"; flag="${entry##*:}"
  echo "  applying: $f ${flag:-(ordinary)}"
  "${TOOL[@]}" $flag "$f"
done

offenders=()
check_group "--language" "${lang[@]}"
check_group "" "${ordinary[@]}"
if (( ${#offenders[@]} == 0 )); then
  echo "OK after --apply: completion gate satisfied."
  exit 0
fi
echo "STILL not clean after --apply: ${#offenders[@]} file(s) — needs human review:" >&2
for e in "${offenders[@]}"; do echo "  ${e%:*}" >&2; done
exit 1
