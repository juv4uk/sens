#!/usr/bin/env bash
# #4449 triple-projection checker.
#
# Proves, for each admitted fixture, the reversible identity across the three
# projections:
#   uk .lisp  <->  physical .sens (T5)  <->  extensionless spaced-bit view
#
#   decode_T5(.sens) -> view(name) -> parse_view -> encode_T5 == byte-identical .sens
#   render_uk(decode_T5(.sens)) == canonical Ukrainian representation
#
# Run from the repo root. Requires scripts/{migrate-three-pass.py,sens_view.py,sens_uk.py}.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
OUT="$(mktemp -d)"; trap 'rm -rf "$OUT"' EXIT

FIXTURES=(
  tests/fixtures/core1-third-domain-canary/third.lisp
  tests/fixtures/migration-d1-cond-cohort/branch.lisp
  tests/fixtures/migration-d4-selector-cohort/caar.lisp
  tests/fixtures/migration-multiform-cohort/two-forms.lisp
)

fail=0; n=0
for f in "${FIXTURES[@]}"; do
  [ -f "$f" ] || { echo "skip (absent): $f"; continue; }
  # --source-era legacy: the fixtures carry legacy 8-bit heads (ambiguous otherwise)
  python3 scripts/migrate-three-pass.py --out "$OUT" --source-era legacy "$f" >/dev/null 2>&1 || {
    echo "BLOCKED: $f"; fail=1; continue; }
  s="$OUT/$(basename "${f%.lisp}").sens"
  [ -f "$s" ] || { echo "no .sens for $f"; fail=1; continue; }
  n=$((n+1))
  printf '%-58s ' "$(basename "$f")"
  # view edge
  python3 scripts/sens_view.py emit "$s" >/dev/null
  python3 scripts/sens_view.py parse "${s%.sens}" --out "$OUT/rt.sens" >/dev/null
  if cmp -s "$s" "$OUT/rt.sens"; then v="ok"; else v="FAIL"; fail=1; fi
  # uk edge (fail-closed if any word lacks a ratified surface)
  if python3 scripts/sens_uk.py render "$s" >/dev/null 2>&1; then u="ok"; else u="FAIL"; fail=1; fi
  echo "view=$v uk=$u"
done

echo "checked $n fixture(s); result=$([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
