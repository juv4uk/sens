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
dir="$(dirname "$physical")"
tmp_pair="$(mktemp "$dir/.sens-t5m-XXXXXXXX")"
tmp_view="$(mktemp "$dir/.sens-view-XXXXXXXX")"
trap 'rm -f "$tmp_pair" "$tmp_view"; rm -rf "$scratch"' EXIT
cp "$staged" "$tmp_pair"
cp "$staged_view" "$tmp_view"
had_pair=0
if [[ -f "$physical" ]]; then
  cp "$physical" "$scratch/old.sens"
  had_pair=1
fi
if [[ -f "$view" ]]; then
  cp "$view" "$scratch/old.view"
fi
mv -f "$tmp_pair" "$physical"
if ! mv -f "$tmp_view" "$view"; then
  if (( had_pair )); then
    cp "$scratch/old.sens" "$physical"
  else
    rm -f "$physical"
  fi
  echo "T5M_REPAIR_INSTALL_FAILED source=$source_file" >&2
  exit 2
fi
cmp "$staged" "$physical"
cmp "$staged_view" "$view"
echo "T5M_REPAIR_OK source=$source_file physical=$physical view=$view exact=ZIG_AND_SENS negative=REJECTED semantic_parity=NOT_CERTIFIED release=NOT_CERTIFIED"
