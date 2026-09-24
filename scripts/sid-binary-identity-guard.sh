#!/usr/bin/env bash
set -euo pipefail

# #1098: active semantic Rust code must treat SID as exact Sid8 identity.
# Raw bytes are allowed only behind explicit pack/unpack or generated
# projection boundaries; they must not reappear as normative SID constructors.

files=(
  crates/my-lisp/src/eval/canon.rs
  crates/my-lisp/src/eval/necessary_forms.rs
  crates/my-lisp/src/eval/mod.rs
  crates/my-lisp/src/eval/closures.rs
  crates/my-lisp/src/ir.rs
  crates/my-lisp/src/language_items.rs
  crates/my-lisp/src/lib.rs
  crates/my-lisp/src/parser.rs
  crates/my-lisp/src/presentation.rs
  crates/my-lisp/src/semantic_registry.rs
  crates/my-lisp/src/syntax.rs
  crates/my-lisp/src/value.rs
)

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
  'semantic SID constant uses Rust 0b numeric literal instead of sid!(........)' \
  'SEMANTIC_ID[^=]*=[[:space:]]*0b[01_]+' \
  "${files[@]}"

report_forbidden \
  'Value::Sid / ExprKind::Sid constructed directly from decimal, 0b, or quoted text' \
  '(Value|ExprKind)::Sid\((0b[01_]+|[0-9]+|"[^"]*")\)' \
  "${files[@]}"

direct_sid8="$(grep -REn 'Sid8\((0b[01_]+|[0-9]+|"[^"]*")\)' crates/my-lisp/src \
  --exclude=sid.rs || true)"
if [[ -n "$direct_sid8" ]]; then
  printf 'SID-BINARY-IDENTITY violation: direct Sid8 constructor outside sid.rs\n%s\n' \
    "$direct_sid8" >&2
  fail=1
fi

report_forbidden \
  'primitive-budget SID identity stored as quoted String' \
  '\(sid[[:space:]]*\.[[:space:]]*"[01]{8}"\)' \
  contracts/primitive-budget-audit-734.lisp

if (( fail != 0 )); then
  exit 1
fi

printf 'SID-BINARY-IDENTITY guard: PASS\n'
