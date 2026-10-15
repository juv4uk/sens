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
  if sed '/^[[:space:]]*;/d' "$source" | grep -nE '\\([[:space:]]*[01]{3,24}([[:space:]]|\\))'; then
    printf 'UKRAINIAN_SURFACE_SOURCE_RED file=%s reason=binary-call-head-in-Lisp reproduce=%s\n' "$source" "bash scripts/prove-repl-uk-step.sh" >&2
    exit 1
  fi
done
echo 'UKRAINIAN_SURFACE_SOURCE_OK machine_heads=0 semantic_pass=NOT_INFERRED'

id=repl-uk-native
reproduce="bash scripts/prove-repl-uk-step.sh"
for kind in step loop queue define-function; do
  law="tests/semantic/repl-uk-${kind}-law.lisp"
  mutant="tests/semantic/repl-uk-${kind}-mutant.lisp"
  python3 - "$law" "$mutant" <<'PY'
from pathlib import Path
import sys
a, b = (Path(p).read_text(encoding="utf-8") for p in sys.argv[1:])
changes = [(x, y) for x, y in zip(a, b) if x != y]
if len(a) != len(b) or changes != [("1", "0")]:
    raise SystemExit("UNINFORMATIVE-INPUT: require exactly one D1 bit 1->0")
print("REPL_UK_MUTANT_BIT_PARITY_OK changes=1 semantic_pass=NOT_INFERRED")
PY
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
