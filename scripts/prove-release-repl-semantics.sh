#!/usr/bin/env bash
# CI_GLUE_NO_SEMANTICS: джерело законів — SENS; shell перевіряє тільки
# спостережувані вердикти REPL, маршрутизацію відмов і стан процесу.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/debug/sens}"
if [[ ! -x "$cli" ]]; then
  printf 'REGRESSION id=release-repl layer=executor actual=missing\n' >&2
  exit 1
fi

# Справжні позитивний і негативний мовні закони виконуються в REPL.
bash scripts/prove-lisp-language-laws.sh "$cli"
bash scripts/prove-repl-environment.sh "$cli"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Наявні SENS-свідки викликають репл-крок/репл-крок-поверхні безпосередньо.
# Позитивна форма мусить повертати D1:YES; mutant — D1:NO.
# REPL тільки завантажує їх через Zig/T5M, а не визначає закон.
run_sens_repl_law() {
  local path="$1" expected="$2" label="$3"
  if [[ ! -f "$path" ]]; then
    printf 'REGRESSION id=release-repl-%s actual=fixture-missing\n' "$label" >&2
    exit 1
  fi
  if ! printf ':завантажити %s\n' "$path" |
    timeout 120s "$cli" --surface=укр >"$tmp/$label.out" 2>"$tmp/$label.err"; then
    printf 'REGRESSION id=release-repl-%s actual=process-failed\n' "$label" >&2
    cat "$tmp/$label.err" >&2
    exit 1
  fi
  if [[ -s "$tmp/$label.err" ]] ||
    ! grep -Fq "Завантажено: $path" "$tmp/$label.out" ||
    ! grep -Fqx "$expected" "$tmp/$label.out"; then
    printf 'REGRESSION id=release-repl-%s expected=%s actual=wrong-verdict\n' "$label" "$expected" >&2
    cat "$tmp/$label.out" "$tmp/$label.err" >&2
    exit 1
  fi
}

run_sens_repl_law tests/semantic/repl-uk-step-law.lisp 'ТАК' step-law
run_sens_repl_law tests/semantic/repl-uk-step-mutant.lisp 'НІ' step-mutant
run_sens_repl_law tests/semantic/repl-uk-loop-law.lisp 'ТАК' loop-law
run_sens_repl_law tests/semantic/repl-uk-loop-mutant.lisp 'НІ' loop-mutant

# Послідовність в ОДНІЙ сесії: невідоме ім'я, заборонений гліф,
# потім точна арифметика. Відмови не можуть ставати echo-успіхом,
# а друга відмова не повинна отруювати наступну коректну форму.
if ! printf 'мама\n(/ 1231 456)\n(поділити 2 3)\n' |
  timeout 90s "$cli" --surface=укр >"$tmp/recovery.out" 2>"$tmp/recovery.err"; then
  printf 'REGRESSION id=release-repl layer=EOF/recovery actual=process-failed\n' >&2
  cat "$tmp/recovery.err" >&2
  exit 1
fi
errors="$(grep -Fc 'Помилка REPL/T5M:' "$tmp/recovery.err" || true)"
if (( errors < 2 )); then
  printf 'REGRESSION id=release-repl layer=error-recovery expected=2-rejections actual=%s\n' "$errors" >&2
  cat "$tmp/recovery.err" >&2
  exit 1
fi
if ! grep -Fq '2/3' "$tmp/recovery.out"; then
  printf 'REGRESSION id=release-repl layer=SENS-arithmetic expected=2/3 actual=missing\n' >&2
  cat "$tmp/recovery.out" >&2
  exit 1
fi

# Окремий коректний вхід має дати той самий точний результат.
if ! printf '(поділити 2 3)\n' |
  timeout 90s "$cli" --surface=укр >"$tmp/exact.out" 2>"$tmp/exact.err"; then
  printf 'REGRESSION id=release-repl layer=exact-result actual=process-failed\n' >&2
  cat "$tmp/exact.err" >&2
  exit 1
fi
if [[ -s "$tmp/exact.err" ]] || ! grep -Fq '2/3' "$tmp/exact.out"; then
  printf 'REGRESSION id=release-repl layer=exact-result expected=2/3 actual=wrong-output\n' >&2
  cat "$tmp/exact.out" "$tmp/exact.err" >&2
  exit 1
fi

printf 'SENS_REPL_RELEASE_SMOKE=OK semantic_laws=SENS transport=Zig/T5M error_recovery=observed exact_arithmetic=2/3 eof=observed scope=smoke_only\n'
