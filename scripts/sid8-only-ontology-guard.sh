#!/usr/bin/env bash
set -euo pipefail

# #1325/#1331: current language ontology is exactly 256 eight-bit functions.
# This guard protects active normative/current prose from reintroducing
# word-named functions or an alternate identity layer.

normative_files=(
  language-contract.lisp
  docs/language-core.md
  README.md
  AGENTS.md
  CURRENT.md
  docs/semantic-authority-map.md
)

implementation_boundary_files=(
  crates/my-lisp/src/sid.rs
  crates/my-lisp/src/parser.rs
  lib/macro.lisp
  scripts/generate-function-table.lisp
  scripts/check-island-math-evidence.lisp
)

for file in "${normative_files[@]}" "${implementation_boundary_files[@]}"; do
  [[ -f "$file" ]] || { echo "SID8-ONLY guard: missing $file" >&2; exit 1; }
done

common_forbidden=(
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
  'Canon 0\\+7'
  'McCarthy-7'
)

normative_forbidden=(
  '\\bCanon\\b'
  'semantic identit(y|ies)'
  '(^|[^[:alnum:]_-])(atom|eq|cons|car|cdr|cond|quote|lambda|define)([^[:alnum:]_-]|$)'
)

failed=0
for pattern in "${common_forbidden[@]}"; do
  if grep -Ein -- "$pattern" "${normative_files[@]}" "${implementation_boundary_files[@]}"; then
    echo "SID8-ONLY violation: forbidden alternate function ontology: $pattern" >&2
    failed=1
  fi
done

for pattern in "${normative_forbidden[@]}"; do
  if grep -Ein -- "$pattern" "${normative_files[@]}"; then
    echo "SID8-ONLY violation in active normative prose: $pattern" >&2
    failed=1
  fi
done

grep -Fq 'ExprKind::Sid(crate::sid!(00000001))' crates/my-lisp/src/parser.rs || {
  echo 'SID8-ONLY violation: apostrophe reader no longer emits 00000001 directly' >&2
  failed=1
}

grep -Fq 'All 256 slots are reserved exclusively for functions.' language-contract.lisp || {
  echo 'SID8-ONLY violation: Contract 9 function-space law missing' >&2
  failed=1
}

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

echo 'SID8-ONLY ontology guard: PASS'
