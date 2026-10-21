#!/usr/bin/env bash
# Ремонт чинної фізичної пари одним SENS reader та Zig/T5M.
# Не є семантичним сертифікатом усієї бібліотеки або релізним GO.
set -euo pipefail
if (( $# < 1 || $# > 3 )); then
  echo "usage: bash $0 SOURCE.lisp [SENS_BINARY] [SENS_TRIT_BINARY]" >&2
  exit 2
fi
source_file="$1"
binary="target/debug/sens"
reader="target/debug/sens-trit"
if (( $# >= 2 )); then binary="$2"; fi
if (( $# == 3 )); then reader="$3"; fi
if [[ "$source_file" != *.lisp || ! -f "$source_file" || -L "$source_file" ]]; then
  echo "T5M_REPAIR_SOURCE_INVALID path=$source_file" >&2
  exit 2
fi
for executable in "$binary" "$reader"; do
  if [[ ! -x "$executable" ]]; then
    echo "T5M_REPAIR_EXECUTABLE_MISSING path=$executable" >&2
    exit 2
  fi
done
base="$(dirname "$source_file")/$(basename "$source_file" .lisp)"
physical="$base.sens"
view="$base"
for target in "$physical" "$view"; do
  if [[ -L "$target" || ( -e "$target" && ! -f "$target" ) ]]; then
    echo "T5M_REPAIR_TARGET_NOT_REGULAR path=$target" >&2
    exit 2
  fi
done
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
snapshot="$(sha256sum "$source_file" | cut -d' ' -f1)"
staged="$scratch/program.sens"
staged_view="$scratch/view"
# SENS власноруч створює слова, Zig єдиний пакує T5M.
"$binary" --t5m-mint "$source_file" "$staged"
test -s "$staged"
"$reader" view "$staged" > "$staged_view"
test -s "$staged_view"
if ! "$binary" --t5m-pair "$source_file" "$staged" > "$scratch/out" 2> "$scratch/err"; then
  cat "$scratch/err" >&2
  echo "T5M_REPAIR_REAL_EVAL_FAILED path=$source_file" >&2
  exit 2
fi
# Негативна перевірка проводить іншу програму через той самий SENS.
{ cat "$source_file"; printf '\n(як-є ())\n'; } > "$scratch/mutant.lisp"
if "$binary" --t5m-pair "$scratch/mutant.lisp" "$staged" > "$scratch/no" 2> "$scratch/no.err"; then
  echo "T5M_REPAIR_MUTANT_WAS_ACCEPTED path=$source_file" >&2
  exit 2
fi
if ! grep -Fq 'T5M_PHYSICAL_PAIR_MISMATCH' "$scratch/no.err"; then
  cat "$scratch/no.err" >&2
  echo "T5M_REPAIR_MUTANT_WRONG_FAILURE path=$source_file" >&2
  exit 2
fi
if [[ "$snapshot" != "$(sha256sum "$source_file" | cut -d' ' -f1)" ]]; then
  echo "T5M_REPAIR_SOURCE_CHANGED path=$source_file" >&2
  exit 2
fi
# Перевірені байти публікуємо лише у фізичний .sens і його побітовий
# перегляд. Жоден інший .lisp або доменний закон не переписуємо.
# Єдина транзакція для фізичного T5M і точного перегляду. При збою
# друга операція відновлює попередню пару, не залишаючи напівпублікації.
# Тут лише файловий I/O: SENS вже виконав програму, Zig перевірив байти.
python3 - "$physical" "$staged" "$view" "$staged_view" <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, "scripts")
from migration_publish_pair import replace_pair

physical, staged, view, staged_view = (Path(p) for p in sys.argv[1:])
try:
    replace_pair(physical, staged.read_bytes(), view, staged_view.read_bytes())
except (OSError, ValueError) as exc:
    raise SystemExit(f"T5M_REPAIR_INSTALL_FAILED source={physical} error={exc}") from exc
PY
cmp "$staged" "$physical"
cmp "$staged_view" "$view"
echo "T5M_REPAIR_OK source=$source_file physical=$physical view=$view exact=ZIG_AND_SENS negative=REJECTED semantic_parity=NOT_CERTIFIED release=NOT_CERTIFIED"
