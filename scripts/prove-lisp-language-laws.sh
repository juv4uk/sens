#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: лише запуск SENS та порівняння вироків D1.
# Усі закони, входи, логічні умови й мутанти написані в .lisp.
set -euo pipefail
cd "$(dirname "$0")/.."
if (( $# > 1 )); then
  echo 'usage: bash scripts/prove-lisp-language-laws.sh [native-sens-path]' >&2
  exit 2
fi
cli="${1:-target/debug/sens}"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=lisp-language-laws layer=executor expected=native-sens actual=missing path=%s\n' "$cli" >&2
  exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
printf 'NATIVE_SENS_EXECUTOR test_id=lisp-language-laws path=%s version=%s\n' "$cli" "$("$cli" --version)"
for id in d1-not d2-cond-laziness d3-structure; do
  law="tests/semantic/$id-law.lisp"
  mutant="tests/semantic/$id-mutant.lisp"
  if [[ ! -f "$law" || ! -f "$mutant" ]] || cmp -s "$law" "$mutant"; then
    printf 'REGRESSION test_id=%s layer=fixture expected=distinct-pair actual=missing-or-identical\n' "$id" >&2
    exit 1
  fi
  for kind in law mutant; do
    file="tests/semantic/$id-$kind.lisp"
    expected=1
    [[ "$kind" == mutant ]] && expected=0
    printf '%s\n' "$expected" > "$tmp/expected"
    printf 'NATIVE_SENS_CASE test_id=%s kind=%s fixture=%s expected=D1:%s\n' "$id" "$kind" "$file" "$expected"
    sha256sum "$file"
    if ! "$cli" "$file" > "$tmp/actual" 2> "$tmp/stderr"; then
      printf 'REGRESSION test_id=%s layer=eval input=%s expected=D1:%s actual=execution-error\n' "$id" "$file" "$expected" >&2
      cat "$tmp/stderr" >&2
      exit 1
    fi
    if ! cmp -s "$tmp/expected" "$tmp/actual"; then
      printf 'REGRESSION test_id=%s layer=eval input=%s expected=D1:%s actual=%q\n' "$id" "$file" "$expected" "$(cat "$tmp/actual")" >&2
      exit 1
    fi
    printf 'NATIVE_SENS_PASS test_id=%s kind=%s expected=D1:%s executor=SENS\n' "$id" "$kind" "$expected"
  done
done
printf 'NATIVE_SENS_SUITE_PASS suite=lisp-language-laws laws=3 mutants=3 authority=SENS\n'
