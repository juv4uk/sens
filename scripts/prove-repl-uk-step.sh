#!/usr/bin/env bash
# Лише запуск нативного SENS і звірка байтів результату.
# Усі семантичні рішення записано в Lisp-свідках; цей файл не є REPL.
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ $# -gt 1 ]]; then
  echo 'Використання: bash scripts/prove-repl-uk-step.sh [шлях-до-sens]' >&2
  exit 2
fi

виконавець="${1:-target/debug/sens}"
назва=repl-uk-step
позитивний=tests/semantic/repl-uk-step-law.lisp
негативний=tests/semantic/repl-uk-step-mutant.lisp
відтворити="bash scripts/prove-repl-uk-step.sh ${виконавець}"

if [[ ! -x "$виконавець" ]]; then
  printf 'REGRESSION test_id=%s layer=eval actual=executor-missing reproduce=%q\n' "$назва" "$відтворити" >&2
  exit 1
fi

# Перевірка механіки: рівно один 1→0 у двох ОДНАКОВОЇ довжини
# Lisp-файлах. Це не визначення логіки порівняння для SENS.
python3 - "$позитивний" "$негативний" <<'PY'
from pathlib import Path
import sys
positive, mutant = [Path(path).read_text(encoding="utf-8") for path in sys.argv[1:]]
changed = [(a, b) for a, b in zip(positive, mutant) if a != b]
if len(positive) != len(mutant) or changed != [("1", "0")]:
    raise SystemExit("REPL_UK_MUTANT_INVALID: expected one changed D1 source bit")
print("REPL_UK_MUTANT_BIT_PARITY_OK changes=1")
PY

тимчасово="$(mktemp -d)"
trap 'rm -rf "$тимчасово"' EXIT

cat lib/meta-eval.lisp lib/repl-core.lisp "$позитивний" > "$тимчасово/позитивний.lisp"
cat lib/meta-eval.lisp lib/repl-core.lisp "$негативний" > "$тимчасово/негативний.lisp"
printf '1\n' > "$тимчасово/очікувано"

printf 'NATIVE_SENS_EXECUTOR test_id=%s path=%s reproduce=%q\n' "$назва" "$виконавець" "$відтворити"
sha256sum "$виконавець" lib/meta-eval.lisp lib/repl-core.lisp "$позитивний" "$негативний"

if ! "$виконавець" "$тимчасово/позитивний.lisp" > "$тимчасово/результат" 2> "$тимчасово/помилка"; then
  printf 'REGRESSION test_id=%s layer=eval expected=D1:YES actual=execution-error reproduce=%q\n' "$назва" "$відтворити" >&2
  cat "$тимчасово/помилка" >&2
  exit 1
fi
if ! cmp -s "$тимчасово/очікувано" "$тимчасово/результат"; then
  printf 'REGRESSION test_id=%s layer=eval expected=D1:YES actual=other first_diff=0 reproduce=%q\n' "$назва" "$відтворити" >&2
  sha256sum "$тимчасово/очікувано" "$тимчасово/результат" >&2
  exit 1
fi

if "$виконавець" "$тимчасово/негативний.lisp" > "$тимчасово/негатив-вихід" 2> "$тимчасово/негатив-помилка"; then
  printf 'REGRESSION test_id=%s-mutant layer=eval expected=D1-noncallable actual=accepted reproduce=%q\n' "$назва" "$відтворити" >&2
  exit 1
fi
if ! grep -Fq 'domain identity is not callable under its ratified law: D1' "$тимчасово/негатив-помилка"; then
  printf 'UNINFORMATIVE-NEGATIVE test_id=%s-mutant layer=eval expected=D1-noncallable actual=unrelated-failure reproduce=%q\n' "$назва" "$відтворити" >&2
  cat "$тимчасово/негатив-помилка" >&2
  exit 1
fi
printf 'NATIVE_SENS_PASS test_id=%s positive_sha256=' "$назва"
sha256sum "$тимчасово/результат"
printf 'NATIVE_SENS_NEGATIVE test_id=%s-mutant stderr_sha256=' "$назва"
sha256sum "$тимчасово/негатив-помилка"
