#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: межа атома D3. Без Python/JSON/SHA-256/квитанцій.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=d3-атом-межа
law=tests/semantic/d3-атом-межа-law.lisp
mutant=tests/semantic/d3-атом-межа-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2; exit 1
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"
if ! "$cli" "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2; cat "$tmp/err" >&2; exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2; exit 1
fi
if [[ ! -f "$mutant" || -L "$mutant" ]]; then
  printf 'REGRESSION id=%s-mutant actual=source-missing-or-symlink\n' "$id" >&2
  exit 1
fi
if ! timeout 45s "$cli" "$mutant" > "$tmp/m.out" 2>"$tmp/m.err"; then
  printf 'REGRESSION id=%s-mutant actual=execution-error\n' "$id" >&2
  cat "$tmp/m.err" >&2
  exit 1
fi
printf '0\n' > "$tmp/expected-mutant"
if ! cmp -s "$tmp/expected-mutant" "$tmp/m.out"; then
  printf 'REGRESSION id=%s-mutant expected=D1:0 actual=wrong-verdict\n' "$id" >&2
  cat "$tmp/m.out" >&2
  exit 1
fi
echo "D3_АТОМ_МЕЖА=OK authority=SENS_form"
