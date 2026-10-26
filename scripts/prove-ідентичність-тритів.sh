#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: ідентичність тритів SENS. Без квитанцій, Python, JSON, SHA-256.
# Вирок — виконання форми; cmp лише звіряє D1-відповідь виконавця.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=ідентичність-тритів
law=tests/semantic/ідентичність-тритів-law.lisp
mutant=tests/semantic/ідентичність-тритів-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2; exit 1
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
printf '1\n' > "$tmp/expected"
if ! "$cli" --t5m-files lib/твердження.lisp "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2; cat "$tmp/err" >&2; exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2; exit 1
fi
if "$cli" --t5m-files lib/твердження.lisp "$mutant" > "$tmp/m.out" 2>/dev/null; then
  if cmp -s "$tmp/expected" "$tmp/m.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2; exit 1
  fi
fi
echo "ІДЕНТИЧНІСТЬ_ТРИТІВ=OK authority=SENS_form evidence=execution"
