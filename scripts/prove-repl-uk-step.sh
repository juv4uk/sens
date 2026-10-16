#!/usr/bin/env bash
# Цей сценарій лише викликає нативний SENS із чинним точнодоменним
# метациркулярним loader-ом. Уся семантика і самовердикти — у Lisp.
# Звичайне "sens file.lisp" НЕ є допустимим шляхом для
# lib/meta-eval.lisp: воно читає точну голову 0011 як десяткову.
set -euo pipefail
cd "$(dirname "$0")/.."

# Кодові голови є машинними ідентичностями драбини, а не
# редакційним синтаксисом наших Lisp-джерел. Вихідний текст — ук.
# Це МЕХАНІЧНИЙ доказ стилю; він не підтверджує семантику або Zig FFI.
for source in lib/repl-core.lisp tests/semantic/repl-uk-*.lisp; do
  if sed '/^[[:space:]]*;/d' "$source" | grep -nE '[(][[:space:]]*[01]{1,24}([[:space:]]|[)])'; then
    printf 'UKRAINIAN_SURFACE_SOURCE_RED file=%s reason=binary-call-head-in-Lisp reproduce=%s\n' "$source" "bash scripts/prove-repl-uk-step.sh" >&2
    exit 1
  fi
done
echo 'UKRAINIAN_SURFACE_SOURCE_OK machine_heads=0 semantic_pass=NOT_INFERRED'

# Звіряємо назви D1 із ЄДИНОЮ ратифікованою таблицею;
# заміна слів у тесті сама по собі не призначає нових D1 кодів.
if ! grep -Eq '^[[:space:]]*[(]0[[:space:]]+[(]ук[[:space:]]+ні[)]' lib/domains/d1.lisp ||
   ! grep -Eq '^[[:space:]]*[(]1[[:space:]]+[(]ук[[:space:]]+так[)]' lib/domains/d1.lisp; then
  echo 'REPL_D1_PROJECTION_RED reason=ratified-D1-uk-row-mismatch' >&2
  exit 1
fi
if grep -nE '#d[1-9][0-9]*:[01]+' lib/repl-core.lisp tests/semantic/repl-uk-*.lisp; then
  echo 'REPL_DOMAIN_LITERAL_RED reason=forbidden-textual-domain-sigil-D1-through-D10' >&2
  exit 1
fi
echo 'REPL_D1_PROJECTION_OK from=lib/domains/d1.lisp names=ні,так'

# Один справжній READ-loop для всіх шести поверхонь та D1–D10.
# Ця перевірка суто структурна; семантика доводиться свідками SENS.
if [[ $(grep -Ec '^[[:space:]]*[(]прочитати[)][[:space:]]*[)]?' lib/repl-core.lisp) != 1 ]] ||
   ! grep -Fq '(визначити репл-цикл репл-цикл-поверхонь)' lib/repl-core.lisp ||
   ! grep -Fq '(визначити репл-цикл-доменів репл-запустити-поверхні)' lib/repl-core.lisp; then
  echo 'REPL_SINGLE_LOOP_RED reason=parallel-reader-loop-or-unchecked-alias' >&2
  exit 1
fi
if sed -n '/^(визначити репл-крок-поверхні/,/^(визначити репл-команда-мови?/p' lib/repl-core.lisp |
   grep -F '((текст? форма)' >/dev/null; then
  echo 'REPL_LITERAL_INGRESS_RED reason=implicit-bit-string-to-domain' >&2
  exit 1
fi
echo 'REPL_SINGLE_LOOP_OK readers=1 surfaces=ук,укр,san,en,LISP,sym implicit-bit-literals=FORBIDDEN semantic_pass=NOT_INFERRED'
# Старий тестовий alias також не має права піднімати рядок 0/1
# до доменного коду. Доменне читання тільки через явні команди SENS.
if sed -n '/^(визначити репл-крок-з-доменами/,/^(визначити репл-доменна-черга/p' lib/repl-core.lisp |
   grep -Fq '(текст? форма)'; then
  echo 'REPL_LEGACY_IMPLICIT_BIT_RED layer=read reason=automatic-literal-domain-lift' >&2
  exit 1
fi
echo 'REPL_LITERAL_FIREWALL_OK step=uk-repl implicit-domain-lift=FORBIDDEN'



id=repl-uk-native
reproduce="bash scripts/prove-repl-uk-step.sh"
for kind in step loop queue define-function; do
  law="tests/semantic/repl-uk-${kind}-law.lisp"
  mutant="tests/semantic/repl-uk-${kind}-mutant.lisp"
  # Файли автора містять лише українські імена, а не D1-літерали.
  # Єдина дозволена мутація тут: одна проєкція D1:так → D1:ні.
  # Бітову однозначність засвідчує авторитетна таблиця D1 нижче,
  # а семантичний результат вирішує сам SENS під час нативного тесту.
  law_text=$(cat "$law")
  mutant_text=$(cat "$mutant")
  cursor=0
  while (( cursor < ${#law_text} && cursor < ${#mutant_text} )) &&
        [[ "${law_text:cursor:1}" == "${mutant_text:cursor:1}" ]]; do
    cursor=$((cursor + 1))
  done
  if [[ "${law_text:cursor:3}" != "так" ||
        "${mutant_text:cursor:2}" != "ні" ||
        "${law_text:$((cursor + 3))}" != "${mutant_text:$((cursor + 2))}" ]]; then
    echo "UNINFORMATIVE-INPUT: expected exactly one D1:так→ні change $law" >&2
    exit 1
  fi
  echo 'REPL_UK_MUTANT_BIT_PARITY_OK one=D1:так→ні semantic_pass=NOT_INFERRED'
done
sha256sum lib/meta-eval.lisp lib/repl-core.lisp \
  tests/semantic/repl-uk-step-law.lisp \
  tests/semantic/repl-uk-step-mutant.lisp \
  tests/semantic/repl-uk-loop-law.lisp \
  tests/semantic/repl-uk-loop-mutant.lisp \
  tests/semantic/repl-uk-queue-law.lisp \
  tests/semantic/repl-uk-queue-mutant.lisp \
  tests/semantic/repl-uk-define-function-law.lisp \
  tests/semantic/repl-uk-define-function-mutant.lisp \
  crates/sens/tests/repl_uk_semantic.rs

echo "NATIVE_SENS_EXECUTOR test_id=$id layer=eval pinned_meta_reader=yes semantic_authority=SENS reproduce=$reproduce"
# Єдина роль Rust тестового harness — виклик метациркулярного
# SENS і спостереження за його D1-вердиктом, НЕ реалізація REPL.
cargo test --locked -p sens --test repl_uk_semantic -- --nocapture
echo "NATIVE_SENS_COMPLETE test_id=$id positives=4 one_bit_negatives=4 semantic_authority=SENS"
