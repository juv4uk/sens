#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: SENS mutual D4. Без Python, JSON, SHA-256.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=meta-eval-mutual-d4
lib=lib/meta-eval.lisp
law=tests/semantic/meta-eval-mutual-d4-law.lisp
mutant=tests/semantic/meta-eval-mutual-d4-mutant.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
if [[ -f "$lib" ]]; then
  cat "$lib" "$law" > "$tmp/positive.lisp"
  cat "$lib" "$mutant" > "$tmp/mutant.lisp"
else
  cp "$law" "$tmp/positive.lisp"
  cp "$mutant" "$tmp/mutant.lisp"
fi
printf '1\n' > "$tmp/expected"
printf 'NATIVE_SENS_EXECUTOR id=%s\n' "$id"
if ! "$cli" "$tmp/positive.lisp" > "$tmp/actual" 2>"$tmp/err"; then
  printf 'REGRESSION id=%s actual=execution-error\n' "$id" >&2
  cat "$tmp/err" >&2
  exit 1
fi
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
  printf 'REGRESSION id=%s actual=wrong-verdict\n' "$id" >&2
  exit 1
fi
if "$cli" "$tmp/mutant.lisp" > "$tmp/mutant.out" 2>"$tmp/mutant.err"; then
  if cmp -s "$tmp/expected" "$tmp/mutant.out"; then
    printf 'REGRESSION id=%s-mutant actual=false-positive\n' "$id" >&2
    exit 1
  fi
fi
printf 'NATIVE_SENS_PASS id=%s semantic_authority=SENS evidence=cmp\n' "$id"
