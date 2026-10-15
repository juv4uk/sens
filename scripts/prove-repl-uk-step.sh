#!/usr/bin/env bash
# Лише запуск нативного SENS і звірка байтів результату.
# Усі семантичні рішення записано в Lisp-свідках; цей файл не є REPL.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ $# -gt 1 ]]; then
  echo 'Використання: bash scripts/prove-repl-uk-step.sh [шлях-до-sens]' >&2
  exit 2
fi

executor="${1:-target/debug/sens}"
test_id=repl-uk-step
positive=tests/semantic/repl-uk-step-law.lisp
mutant=tests/semantic/repl-uk-step-mutant.lisp
reproduce="bash scripts/prove-repl-uk-step.sh ${executor}"

if [[ ! -x "$executor" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=executor-missing reproduce=%q\n' "$test_id" "$reproduce" >&2
  exit 1
fi

# Перевірка механіки: рівно один 1→0 у двох ОДНАКОВОЇ довжини
# Lisp-файлах. Це не визначення логіки порівняння для SENS.
python3 - "$positive" "$mutant" <<'PY'
from pathlib import Path
import sys
positive, mutant = [Path(path).read_text(encoding="utf-8") for path in sys.argv[1:]]
changed = [(a, b) for a, b in zip(positive, mutant) if a != b]
if len(positive) != len(mutant) or changed != [("1", "0")]:
    raise SystemExit("REPL_UK_MUTANT_INVALID: expected one changed D1 source bit")
print("REPL_UK_MUTANT_BIT_PARITY_OK changes=1")
PY

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cat lib/meta-eval.lisp lib/repl-core.lisp "$positive" > "$tmpdir/positive.lisp"
cat lib/meta-eval.lisp lib/repl-core.lisp "$mutant" > "$tmpdir/mutant.lisp"
printf '1\n' > "$tmpdir/очікувано"

printf 'NATIVE_SENS_EXECUTOR test_id=%s path=%s reproduce=%q\n' "$test_id" "$executor" "$reproduce"
sha256sum "$executor" lib/meta-eval.lisp lib/repl-core.lisp "$positive" "$mutant"

if ! "$executor" "$tmpdir/positive.lisp" > "$tmpdir/результат" 2> "$tmpdir/помилка"; then
  printf 'REGRESSION test_id=%s layer=eval expected=D1:YES actual=execution-error reproduce=%q\n' "$test_id" "$reproduce" >&2
  cat "$tmpdir/помилка" >&2
  exit 1
fi
if ! cmp -s "$tmpdir/очікувано" "$tmpdir/результат"; then
  printf 'REGRESSION test_id=%s layer=eval expected=D1:YES actual=other first_diff=0 reproduce=%q\n' "$test_id" "$reproduce" >&2
  sha256sum "$tmpdir/очікувано" "$tmpdir/результат" >&2
  exit 1
fi

if "$executor" "$tmpdir/mutant.lisp" > "$tmpdir/негатив-вихід" 2> "$tmpdir/негатив-помилка"; then
  printf 'REGRESSION test_id=%s-mutant layer=eval expected=D1-noncallable actual=accepted reproduce=%q\n' "$test_id" "$reproduce" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$tmpdir/негатив-помилка"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant layer=eval expected=D1-noncallable actual=unrelated-failure reproduce=%q\n' "$test_id" "$reproduce" >&2
  cat "$tmpdir/негатив-помилка" >&2
  exit 1
fi
printf 'NATIVE_SENS_PASS test_id=%s positive_sha256=' "$test_id"
sha256sum "$tmpdir/результат"
printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant stderr_sha256=' "$test_id"
sha256sum "$tmpdir/негатив-помилка"
