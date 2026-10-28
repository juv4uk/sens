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
if [[ ! -f "$law" || ! -f "$negative" || -L "$law" || -L "$negative" ]]; then
  printf 'REGRESSION id=%s actual=fixture-absent-or-symlink\n' "$id" >&2; exit 1
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
run_repl_fixture() {
  local fixture="$1" expected="$2" label="$3"
  if [[ ! -f "$fixture" || -L "$fixture" ]]; then
    printf 'REGRESSION id=%s-%s layer=source actual=missing-or-symlink path=%s\n' "$id" "$label" "$fixture" >&2
    exit 1
  fi
  if ! printf ':завантажити %s\n' "$fixture" | timeout 45s "$cli" --surface=укр >"$tmp/$label.out" 2>"$tmp/$label.err"; then
    printf 'REGRESSION id=%s-%s layer=REPL/T5M actual=execution-error\n' "$id" "$label" >&2
    cat "$tmp/$label.err" >&2
    exit 1
  fi
  if grep -Eq 'Помилка REPL/T5M|Помилка завантаження|Помилка читання файла|Помилка: :завантажити' "$tmp/$label.err" ||
     grep -Eq 'Помилка REPL/T5M|Помилка завантаження' "$tmp/$label.out"; then
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

run_repl_rejects_d3_pair_eq() {
  local label=d3-eq-pair
  printf '%s\n' \
    '(тотожне? (сполучити (як-є а) (як-є ())) (сполучити (як-є а) (як-є ())))' |
    timeout 45s "$cli" --surface=укр >"$tmp/$label.out" 2>&1 || true
  if ! grep -Fq 'тотожне? очікує два атоми' "$tmp/$label.out"; then
    printf 'REGRESSION id=%s-%s layer=REPL/T5M expected=atomic-eq-type-error actual=wrong-result\n' "$id" "$label" >&2
    cat "$tmp/$label.out" >&2
    exit 1
  fi
}

run_repl_rejects_improper_apply_list() {
  local label=d4-apply-improper-list
  printf '%s\n' \
    '(застосувати (функція (х) х) (сполучити (як-є а) (як-є 7)))' |
    timeout 45s "$cli" --surface=укр >"$tmp/$label.out" 2>&1 || true
  if ! grep -Fq 'D4:0000 застосувати очікує правильний список аргументів' "$tmp/$label.out"; then
    printf 'REGRESSION id=%s-%s layer=REPL/T5M expected=proper-list-type-error actual=wrong-result\n' "$id" "$label" >&2
    cat "$tmp/$label.out" >&2
    exit 1
  fi
}

run_repl_rejects_d3_pair_eq
run_repl_rejects_improper_apply_list
run_repl_fixture "$law" 'ТАК' core-positive
run_repl_fixture "$negative" 'НІ' core-negative
# These are existing SENS-authored programs, not formulas reimplemented in shell.
# REPL -> Zig/T5M -> SENS evaluates the D1, D2 and D3 semantics itself.
for domain in d1-not d2-cond-laziness d3-structure; do
  run_repl_fixture "tests/semantic/${domain}-law.lisp" 'ТАК' "${domain}-law"
  run_repl_fixture "tests/semantic/${domain}-mutant.lisp" 'НІ' "${domain}-mutant"
done
# Рекурсивний закон належить SENS і оцінюється тим самим REPL/Zig/T5M шляхом.
run_repl_fixture tests/semantic/d5-recursive-list-law.lisp 'ТАК' d5-recursive-law
run_repl_fixture tests/semantic/d5-recursive-list-mutant.lisp 'НІ' d5-recursive-mutant
printf 'SENS_REPL_LANGUAGE_LAWS=OK path=REPL->Zig/T5M->SENS positive=ТАК negative=НІ domains=D1,D2,D3,D4,D5 witness_pairs=5 runs=12\n'
