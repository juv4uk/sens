#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: the SENS REPL executes each source fixture through Zig/T5M.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

run_repl_form() {
  local label="$1" form="$2"
  if ! printf '%s\n' "$form" | "$cli" --surface=укр >"$tmp/out" 2>"$tmp/err"; then
    printf 'REGRESSION case=%s layer=SENS-REPL actual=execution-error\n' "$label" >&2
    cat "$tmp/err" >&2
    exit 1
  fi
  if grep -Eq 'Помилка REPL/T5M|Помилка завантаження' "$tmp/err"; then
    printf 'REGRESSION case=%s layer=SENS-REPL actual=language-error\n' "$label" >&2
    cat "$tmp/err" >&2
    exit 1
  fi
  # A piped (non-TTY) REPL prints the D1 answer without an interactive
  # prompt. A terminal may prefix the same *exact* line with 'sens[укр]>'.
  # Neither case authorizes a partial substring or an error banner.
  if ! grep -Fqx 'НІ' "$tmp/out" &&
     ! grep -Fqx 'sens[укр]> НІ' "$tmp/out"; then
    printf 'REGRESSION case=%s expected=НІ actual=wrong-reply\n' "$label" >&2
    cat "$tmp/out" >&2
    exit 1
  fi
}

run_repl_form D10 '(атом? (середовище))'
run_repl_form D8 '(атом? (відобразити-середовище))'
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
