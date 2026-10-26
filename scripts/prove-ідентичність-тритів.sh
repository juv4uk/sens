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
printf '1\n' > "$tmp/expected-positive"
printf '0\n' > "$tmp/expected-negative"
if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$law" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s layer=positive actual=execution-error\n' "$id" >&2
  cat "$tmp/err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-positive" "$tmp/actual"; then
  printf 'REGRESSION id=%s layer=positive expected=D1:так actual=divergent\n' "$id" >&2
  exit 1
fi
if ! timeout 45s "$cli" --t5m-files lib/твердження.lisp "$mutant" > "$tmp/m.out" 2>"$tmp/m.err"; then
  printf 'REGRESSION id=%s-mutant layer=negative actual=execution-error\n' "$id" >&2
  cat "$tmp/m.err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected-negative" "$tmp/m.out"; then
  printf 'REGRESSION id=%s-mutant layer=negative expected=D1:ні actual=divergent\n' "$id" >&2
  exit 1
fi
echo "ІДЕНТИЧНІСТЬ_ТРИТІВ=OK authority=SENS_form positive=D1:так negative=D1:ні evidence=cmp carrier=Zig/T5M"
