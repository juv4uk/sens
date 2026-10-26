#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: D1 заперечення. Без Python/JSON/SHA-256/квитанцій.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=d1-not
law=tests/semantic/d1-not-law.lisp
mutant=tests/semantic/d1-not-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2; exit 1
fi
if [[ ! -f "$law" ]]; then
  printf 'REGRESSION id=%s actual=fixture-absent\n' "$id" >&2; exit 1
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"
if ! "$cli" "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2; cat "$tmp/err" >&2; exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2; exit 1
fi
if [[ -f "$mutant" ]] && "$cli" "$mutant" > "$tmp/m.out" 2>/dev/null; then
  if cmp -s "$tmp/expected" "$tmp/m.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2; exit 1
  fi
fi
echo "D1_NOT=OK authority=SENS_form"
