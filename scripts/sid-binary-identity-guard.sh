#!/usr/bin/env bash
set -euo pipefail

# #1098: active semantic Rust code must treat SID as exact Sid8 identity.
# Raw bytes are allowed only behind explicit pack/unpack or generated
# projection boundaries; they must not reappear as normative SID constructors.

files=(
  crates/sens/src/eval/canon.rs
  crates/sens/src/eval/necessary_forms.rs
  crates/sens/src/eval/mod.rs
  crates/sens/src/eval/closures.rs
  crates/sens/src/language_items.rs
  crates/sens/src/lib.rs
  crates/sens/src/parser.rs
  crates/sens/src/presentation.rs
  crates/sens/src/semantic_registry.rs
  crates/sens/src/syntax.rs
  crates/sens/src/value.rs
)

# Keep this guard fail-closed if its active-source inventory drifts.
for current_file in "${files[@]}"; do
  if [[ ! -f "$current_file" ]]; then
    printf 'SID-BINARY-IDENTITY guard: missing active source %s\n' "$current_file" >&2
    exit 1
  fi
done

fail=0

report_forbidden() {
  local description="$1"
  local pattern="$2"
  shift 2
  local output
  output="$(grep -En "$pattern" "$@" || true)"
  if [[ -n "$output" ]]; then
    printf 'SID-BINARY-IDENTITY violation: %s\n%s\n' "$description" "$output" >&2
    fail=1
  fi
}

report_forbidden \
  'raw Sid=u8 alias reintroduced' \
  'type[[:space:]]+Sid[[:space:]]*=[[:space:]]*u8' \
  "${files[@]}"

report_forbidden \
  'semantic SID constant uses Rust 0b numeric literal instead of sens!(........)' \
  'SEMANTIC_ID[^=]*=[[:space:]]*0b[01_]+' \
  "${files[@]}"

report_forbidden \
  'Value::Sid / ExprKind::Sid constructed through alternate decimal, prefixed, or quoted wrappers' \
  '(Value|ExprKind)::Sid\((0b[01_]+|[0-9]+|"[^"]*")\)' \
  "${files[@]}"

direct_sid8="$(grep -REn '(Sid8|Sens8)\((0b[01_]+|[0-9]+|"[^"]*")\)' crates/sens/src \
  --exclude=sid.rs --exclude=sens.rs || true)"
if [[ -n "$direct_sid8" ]]; then
  printf 'SID-BINARY-IDENTITY violation: direct Sid8/Sens8 constructor outside sid.rs/sens.rs\n%s\n' \
    "$direct_sid8" >&2
  fail=1
fi

report_forbidden \
  'function SID wrapped in quoted String' \
  '\(sid[[:space:]]*\.[[:space:]]*"[01]{8}"\)' \
  contracts/primitive-budget-audit-734.lisp

if (( fail != 0 )); then
  exit 1
fi

printf 'SID-BINARY-IDENTITY guard: PASS\n'
