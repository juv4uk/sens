#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: SENS-закон виконується інтерактивним REPL через Zig/T5M.
# Оболонка лише передає фікстури й порівнює видимі відповіді; закон живе у SENS.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
id=lisp-language-laws
law=tests/semantic/lisp-language-laws.lisp
negative=tests/semantic/lisp-language-negative.lisp
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION test_id=%s actual=executor-missing\n' "$id" >&2; exit 1
fi
if [[ ! -f "$law" ]]; then
  printf 'REGRESSION id=%s actual=fixture-absent\n' "$id" >&2; exit 1
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
run_repl_fixture() {
  local fixture="$1" expected="$2" label="$3"
  if ! printf ':завантажити %s\n' "$fixture" | "$cli" --surface=укр >"$tmp/$label.out" 2>"$tmp/$label.err"; then
    printf 'REGRESSION id=%s-%s layer=REPL/T5M actual=execution-error\n' "$id" "$label" >&2
    cat "$tmp/$label.err" >&2
    exit 1
  fi
  if grep -Eq 'Помилка REPL/T5M|Помилка завантаження' "$tmp/$label.err"; then
    printf 'REGRESSION id=%s-%s layer=REPL/T5M actual=language-error\n' "$id" "$label" >&2
    cat "$tmp/$label.err" >&2
    exit 1
  fi
  if ! grep -Fq "Завантажено: $fixture" "$tmp/$label.out" ||
     ! grep -Fqx "$expected" "$tmp/$label.out"; then
    printf 'REGRESSION id=%s-%s layer=REPL/T5M expected=%s actual=wrong-reply\n' "$id" "$label" "$expected" >&2
    cat "$tmp/$label.out" >&2
    exit 1
  fi
}

run_repl_fixture "$law" 'ТАК' positive
run_repl_fixture "$negative" 'НІ' negative
printf 'SENS_REPL_LANGUAGE_LAWS=OK path=REPL->Zig/T5M->SENS positive=ТАК negative=НІ\n'
