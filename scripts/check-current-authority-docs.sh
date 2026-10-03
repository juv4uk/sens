#!/usr/bin/env bash
set -euo pipefail

# #1466: перевіряємо лише чинні/normative entry-points.
# Архіви навмисно не входять до цього списку: історичні назви там є evidence,
# а не помилкою, яку треба переписувати заднім числом.
docs=(
  README.md
  CURRENT.md
  docs/semantic-authority-map.md
  docs/semantic-authority-map.uk.md
)

for path in "${docs[@]}"; do
  test -f "$path" || {
    printf 'current-authority-doc-missing: %s\n' "$path" >&2
    exit 1
  }
done

require_literal() {
  local path="$1"
  local literal="$2"
  if ! grep -Fq -- "$literal" "$path"; then
    printf 'current-authority-required-text-missing: %s: %s\n' "$path" "$literal" >&2
    exit 1
  fi
}

forbid_literal() {
  local path="$1"
  local literal="$2"
  if grep -Fq -- "$literal" "$path"; then
    printf 'current-authority-stale-text: %s: %s\n' "$path" "$literal" >&2
    exit 1
  fi
}

# Поточний Rust reference path має бути sens, не історичний crate path.
for path in CURRENT.md docs/semantic-authority-map.md docs/semantic-authority-map.uk.md; do
  forbid_literal "$path" 'crates/my-lisp'
  require_literal "$path" 'crates/sens'
done

# Чинна онтологія: exact bits + exact domain + admitted/proved law.
require_literal CURRENT.md 'SENS no longer has one universal 256-slot function ontology'
require_literal CURRENT.md 'exact binary number'
require_literal docs/semantic-authority-map.md 'Canonical semantic identity is domain-qualified'
require_literal docs/semantic-authority-map.md 'Historical exact-eight-bit Sens8/Sid8/Function8 values remain bounded compatibility'
require_literal docs/semantic-authority-map.uk.md 'Канонічна семантична ідентичність є доменно-кваліфікованою'
require_literal docs/semantic-authority-map.uk.md 'Історичні exact-eight-bit Sens8/Sid8/Function8 лишаються обмеженими compatibility'

# Старий flat-256 текст більше не може з'являтися у чинних authority docs.
forbid_literal CURRENT.md 'Those exact eight-bit forms are the 256 SENS functions'
forbid_literal docs/semantic-authority-map.md 'SENS has exactly 256 functions'
forbid_literal docs/semantic-authority-map.md 'outside the 256-function space'
forbid_literal docs/semantic-authority-map.uk.md 'У СЕНС є рівно 256 функцій'
forbid_literal docs/semantic-authority-map.uk.md 'поза простором 256 функцій'

# Structural empty is an exact D3 resident, not a legacy eight-bit/numeric alias.
require_literal CURRENT.md 'Core.D3 `000`'
require_literal docs/semantic-authority-map.md 'Core.D3 `000`'
require_literal docs/semantic-authority-map.uk.md 'Core.D3 `000`'

# Surface — routing/UI metadata, а не друга identity.
require_literal CURRENT.md 'source/UI routing metadata'
require_literal docs/semantic-authority-map.md 'source/UI routing metadata'
require_literal docs/semantic-authority-map.uk.md 'source/UI routing metadata'

# McCarthy/Lisp лишаються історичним/Core1 provenance, а не active ontology.
forbid_literal docs/semantic-authority-map.md 'Canon 0 + McCarthy-7 remain the stable historical/minimal root'
forbid_literal docs/semantic-authority-map.uk.md 'Закритий семантичний набір — рівно сім операцій'
forbid_literal CURRENT.md 'Canon 0+7 and DEFINE/LAMBDA evaluator meaning'
require_literal docs/semantic-authority-map.md 'Core1'
require_literal docs/semantic-authority-map.uk.md 'Core1'

# Проєкт справді перейменовано з my-lisp у sens; README не має перевертати історію.
require_literal README.md 'робочою назвою `my-lisp`'
forbid_literal README.md 'робочою назвою `sens`'

printf 'current-authority-docs-ok\n'
