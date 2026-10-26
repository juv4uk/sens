#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: закони мови Lisp/SENS. Без Python/JSON/SHA-256/квитанцій.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=lisp-language-laws
law=tests/semantic/lisp-language-laws.lisp
mutant=tests/semantic/lisp-language-laws-mutant.lisp
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
if "$cli" "$mutant" > "$tmp/m.out" 2>/dev/null; then
  if cmp -s "$tmp/expected" "$tmp/m.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2; exit 1
  fi
fi
# D5 MEMBER/ASSOC: звичайні закони та неправильні хвости виконуються самим SENS.
run_positive() {
  local test_id="$1" source="$2"
  if ! "$cli" "$source" > "$tmp/actual" 2> "$tmp/err"; then
    printf 'REGRESSION id=%s layer=SENS expected=D1:1 actual=execution-error\n' "$test_id" >&2
    cat "$tmp/err" >&2
    exit 1
  fi
  if ! cmp -s "$tmp/expected" "$tmp/actual"; then
    printf 'REGRESSION id=%s layer=SENS expected=D1:1 actual=wrong-verdict\n' "$test_id" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_PASS id=%s source=%s\n' "$test_id" "$source"
}
run_type_rejection() {
  local test_id="$1" source="$2"
  if "$cli" "$source" > "$tmp/actual" 2> "$tmp/err"; then
    printf 'REGRESSION id=%s layer=SENS expected=Type actual=unexpected-success\n' "$test_id" >&2
    exit 1
  fi
  if ! grep -Eq 'car expects a non-empty list|Помилка типу: перше очікує непорожній список|kind=Type' "$tmp/err"; then
    printf 'REGRESSION id=%s layer=SENS expected=Type actual=unclassified-error\n' "$test_id" >&2
    cat "$tmp/err" >&2
    exit 1
  fi
  printf 'NATIVE_SENS_PASS id=%s expected=Type source=%s\n' "$test_id" "$source"
}
run_positive d5-member-total-list tests/semantic/d5-member-total-list-law.lisp
run_positive d5-assoc-total-list tests/semantic/d5-assoc-total-list-law.lisp
run_type_rejection d5-member-hidden-tail tests/semantic/d5-member-hidden-tail-negative.lisp
run_type_rejection d5-assoc-hidden-tail tests/semantic/d5-assoc-hidden-tail-negative.lisp
run_type_rejection d5-assoc-late-record tests/semantic/d5-assoc-late-record-negative.lisp
echo "LISP_LANGUAGE_LAWS=OK authority=SENS_form"
