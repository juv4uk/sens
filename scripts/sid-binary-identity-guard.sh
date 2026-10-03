#!/usr/bin/env bash
set -euo pipefail

# Domain-era identity guard (#2817/#2821).
#
# Canonical AST/runtime identity is CallableIdentity. Historical Sens8/Sid8
# survives only in explicitly named compatibility/backend modules; it must not
# re-enter the canonical carrier layer.

canonical_files=(
  crates/sens/src/callable_identity.rs
  crates/sens/src/domain_identity.rs
  crates/sens/src/domain_words.rs
  crates/sens/src/environment.rs
  crates/sens/src/parser.rs
  crates/sens/src/syntax.rs
  crates/sens/src/value.rs
)

fail=0

report_forbidden() {
  local description="$1"
  local pattern="$2"
  shift 2
  local output
  output="$(grep -En "$pattern" "$@" || true)"
  if [[ -n "$output" ]]; then
    printf 'DOMAIN-IDENTITY violation: %s\n%s\n' "$description" "$output" >&2
    fail=1
  fi
}

# Universal eight-bit identity types are forbidden in the canonical carrier.
report_forbidden   'Sens8/Sid8/Function8 re-entered canonical AST/runtime identity'   '\b(Sens8|Sid8|Function8)\b'   "${canonical_files[@]}"

# The temporary split AST from the migration must not return.
report_forbidden   'parallel DomainIdentity/DomainCall AST variant reintroduced'   'ExprKind::DomainIdentity|ExprKind::DomainCall|[[:space:]]DomainIdentity\(|[[:space:]]DomainCall\('   crates/sens/src/syntax.rs crates/sens/src/value.rs crates/sens/src/eval

# Old projection APIs made eight-bit compatibility look canonical.
report_forbidden   'old as_sens8/as_sid8 projection API reintroduced'   '\bas_(sens8|sid8)\b'   crates/sens/src/value.rs crates/sens/src/syntax.rs crates/sens/src/environment.rs

# Old u8-keyed code slots collapse equal payloads from different domains.
report_forbidden   'code slot keyed only by u8 payload'   'code_slots[[:space:]]*:[[:space:]]*HashMap<u8'   crates/sens/src/environment.rs

grep -q 'Sid(CallableIdentity)' crates/sens/src/syntax.rs || {
  echo 'DOMAIN-IDENTITY violation: ExprKind::Sid must carry CallableIdentity' >&2
  fail=1
}

grep -q 'Call(CallableIdentity' crates/sens/src/syntax.rs || {
  echo 'DOMAIN-IDENTITY violation: ExprKind::Call must carry CallableIdentity' >&2
  fail=1
}

grep -q 'Sid(CallableIdentity)' crates/sens/src/value.rs || {
  echo 'DOMAIN-IDENTITY violation: Value::Sid must carry CallableIdentity' >&2
  fail=1
}

grep -q 'code_slots: HashMap<CallableIdentity, Value>' crates/sens/src/environment.rs || {
  echo 'DOMAIN-IDENTITY violation: environment code slots must be keyed by CallableIdentity' >&2
  fail=1
}

grep -q 'Core(CoreDomainIdentity)' crates/sens/src/callable_identity.rs || {
  echo 'DOMAIN-IDENTITY violation: CallableIdentity must carry CoreDomainIdentity' >&2
  fail=1
}

grep -q 'Legacy8(u8)' crates/sens/src/callable_identity.rs || {
  echo 'DOMAIN-IDENTITY violation: historical exact-eight compatibility must remain explicit' >&2
  fail=1
}

if (( fail != 0 )); then
  exit 1
fi

printf 'DOMAIN-IDENTITY guard: PASS\n'
