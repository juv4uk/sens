#!/usr/bin/env bash
set -euo pipefail

# #1325/#1331: current normative identity vocabulary must stay SID8-only.
# This phase guards the active contract/core/readme/Sid8/reader/bootstrap slice.
# The protected set expands as #1327/#1328/#1330 retire remaining runtime debt.

files=(
  language-contract.lisp
  docs/language-core.md
  README.md
  crates/sens/src/sid.rs
  crates/sens/src/parser.rs
  lib/macro.lisp
)

for file in "${files[@]}"; do
  [[ -f "$file" ]] || { echo "SID8-ONLY guard: missing $file" >&2; exit 1; }
done

forbidden=(
  'SID[ -]text'
  'SID[ -]literal'
  'SID[ -]spelling'
  'canonical SID spelling'
  'CanonicalIdentity'
  'NecessaryFormIdentity'
  'CANON_EMPTY_LIST'
  'PRIM_QUOTE'
  'PRIM_ATOM'
  'PRIM_EQ'
  'PRIM_CONS'
  'PRIM_CAR'
  'PRIM_CDR'
  'PRIM_COND'
  'Canon 0\+7'
  'McCarthy-7'
)

failed=0
for pattern in "${forbidden[@]}"; do
  if grep -Ein -- "$pattern" "${files[@]}"; then
    echo "SID8-ONLY violation: forbidden named/alternate function ontology: $pattern" >&2
    failed=1
  fi
done

# Reader sugar must materialize the eight-bit head directly.
grep -Fq 'ExprKind::Sid(crate::sid!(00000001))' crates/sens/src/parser.rs || {
  echo 'SID8-ONLY violation: apostrophe reader no longer emits SID 00000001 directly' >&2
  failed=1
}

# Contract must state the complete exclusive function-ID budget.
grep -Fq 'All 256 slots are reserved exclusively for functions.' language-contract.lisp || {
  echo 'SID8-ONLY violation: Contract 9 function-space law missing' >&2
  failed=1
}

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo 'SID8-ONLY ontology guard: PASS'
