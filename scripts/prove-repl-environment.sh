#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: the SENS REPL executes each source fixture through Zig/T5M.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

run_fixture() {
  local fixture="$1"
  if [[ ! -f "$fixture" ]]; then
    printf 'REGRESSION fixture=%s actual=absent\n' "$fixture" >&2
    exit 1
  fi
  if ! printf ':завантажити %s\n' "$fixture" | "$cli" --surface=укр >"$tmp/out" 2>"$tmp/err"; then
    printf 'REGRESSION fixture=%s layer=SENS-REPL actual=execution-error\n' "$fixture" >&2
    cat "$tmp/err" >&2
    exit 1
  fi
  if grep -Eq 'Помилка REPL/T5M|Помилка завантаження' "$tmp/err"; then
    printf 'REGRESSION fixture=%s layer=SENS-REPL actual=language-error\n' "$fixture" >&2
    cat "$tmp/err" >&2
    exit 1
  fi
  if ! grep -Fq "Завантажено: $fixture" "$tmp/out" || ! grep -Fqx 'НІ' "$tmp/out"; then
    printf 'REGRESSION fixture=%s expected=НІ actual=wrong-reply\n' "$fixture" >&2
    cat "$tmp/out" >&2
    exit 1
  fi
}

run_fixture tests/semantic/repl-environment-d10.lisp
run_fixture tests/semantic/repl-environment-d8.lisp
if ! printf '(відобразити-середовище)\n' | "$cli" --surface=укр >"$tmp/reflection.out" 2>"$tmp/reflection.err"; then
  printf 'REGRESSION identity=D8:11100111 layer=SENS-REPL actual=execution-error\n' >&2
  cat "$tmp/reflection.err" >&2
  exit 1
fi
if grep -Fq '#t7:' "$tmp/reflection.out" || ! grep -Fq 'БУДЬ-ЯКЕ?' "$tmp/reflection.out"; then
  printf 'REGRESSION identity=D8:11100111 expected=surface-names actual=wire-tokens\n' >&2
  exit 1
fi
printf 'SENS_REPL_ENVIRONMENT=OK route=Zig/T5M->SENS D10=1 D8=1\n'
