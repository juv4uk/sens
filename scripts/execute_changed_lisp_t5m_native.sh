#!/usr/bin/env bash
# Основний CI: український Lisp -> SENS reader -> Zig/T5M -> SENS.
# Жодного Python/JSON посеред визначення фізичних слів або виконання.
set -euo pipefail
if (( $# != 3 )); then
  echo "usage: $0 SENS_BINARY CHANGED_LISP_LIST EVIDENCE_DIR" >&2
  exit 2
fi
binary="$1"
manifest="$2"
outdir="$3"
test -x "$binary"
test -f "$manifest"
mkdir -p "$outdir"
checked_files=0
failed_files=0
physical_d24_only=0
mark_file_failed() {
  if (( file_failed == 0 )); then
    failed_files=$((failed_files + 1))
    file_failed=1
  fi
}
while IFS= read -r file || [[ -n "$file" ]]; do
  [[ -n "$file" ]] || continue
  checked_files=$((checked_files + 1))
  file_failed=0
  if [[ "$file" != *.lisp || ! -f "$file" || -L "$file" ]]; then
    echo "::error::SENS_NATIVE_SOURCE_INVALID path=$file" >&2
    mark_file_failed
    continue
  fi
  id="$(printf '%s' "$file" | sha256sum | cut -c1-16)"
  dir="$outdir/$id"
  mkdir -p "$dir"
  pair="$dir/$(basename "$file" .lisp).sens"
  view="$(dirname "$pair")/$(basename "$pair" .sens)"
  echo "SENS_NATIVE_SOURCE path=$file"
  if timeout 45s "$binary" --t5m-mint "$file" "$pair" \
      >"$dir/mint.stdout" 2>"$dir/mint.stderr"; then
    :
  else
    status=$?
    cat "$dir/mint.stderr" >&2
    echo "::error::SENS_NATIVE_MINT_FAILED path=$file status=$status release=NOT_CERTIFIED" >&2
    mark_file_failed
    continue
  fi
  if [[ ! -s "$pair" || ! -f "$pair" || -L "$pair" ]]; then
    echo "::error::SENS_NATIVE_PHYSICAL_MISSING path=$file pair=$pair" >&2
    mark_file_failed
    continue
  fi
  if timeout 45s "$binary" --t5m-view "$file" "$pair" "$view" \
       >"$dir/view.stdout" 2>"$dir/view.stderr"; then
    :
  else
    status=$?
    cat "$dir/view.stderr" >&2
    echo "::error::SENS_NATIVE_VIEW_OR_INVERSE_FAILED path=$file physical=$pair status=$status" >&2
    mark_file_failed
    continue
  fi
  if [[ ! -s "$view" || ! -f "$view" || -L "$view" ]]; then
    echo "::error::SENS_NATIVE_VIEW_MISSING path=$file view=$view" >&2
    mark_file_failed
    continue
  fi
  physical_sha="$(sha256sum "$pair" | cut -d ' ' -f 1)"
  view_sha="$(sha256sum "$view" | cut -d ' ' -f 1)"
  echo "SENS_NATIVE_PHYSICAL_VERIFIED path=$file physical_sha256=$physical_sha view_sha256=$view_sha semantic=NOT_CERTIFIED"
  committed="$(dirname "$file")/$(basename "$file" .lisp).sens"
  committed_view="$(dirname "$file")/$(basename "$file" .lisp)"
  if [[ -e "$committed" || -L "$committed" ]]; then
    if [[ ! -f "$committed" || -L "$committed" ]]; then
      echo "::error::SENS_NATIVE_COMMITTED_NOT_REGULAR path=$file pair=$committed" >&2
      mark_file_failed
    elif ! cmp -s "$pair" "$committed"; then
      echo "::error::SENS_NATIVE_COMMITTED_DRIFT path=$file pair=$committed" >&2
      mark_file_failed
    fi
    if [[ ! -f "$committed_view" || -L "$committed_view" ]]; then
      echo "::error::SENS_NATIVE_COMMITTED_VIEW_MISSING path=$file view=$committed_view" >&2
      mark_file_failed
    elif ! cmp -s "$view" "$committed_view"; then
      echo "::error::SENS_NATIVE_COMMITTED_VIEW_DRIFT path=$file view=$committed_view" >&2
      mark_file_failed
    fi
  elif [[ -e "$committed_view" || -L "$committed_view" ]]; then
    echo "::error::SENS_NATIVE_ORPHAN_VIEW path=$file view=$committed_view" >&2
    mark_file_failed
  else
    echo "::notice::SENS_NATIVE_PAIR_NOT_COMMITTED path=$file release=NOT_CERTIFIED"
  fi
  standalone_ok=0
  if timeout 45s "$binary" "$pair" >"$dir/standalone.stdout" 2>"$dir/standalone.stderr"; then
    standalone_ok=1
  else
    status=$?
    if grep -Fq 'T5M requires exact source projection to D24+ before transport' "$dir/standalone.stderr" ||
       { grep -Fq 'Фізичне T5M-декодування зберегло точні ширини слів' "$dir/standalone.stderr" &&
         grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$dir/standalone.stderr"; }; then
      physical_d24_only=$((physical_d24_only + 1))
      echo "::notice::SENS_NATIVE_STANDALONE_D24_NOT_SUPPORTED path=$file status=$status"
    else
      cat "$dir/standalone.stderr" >&2
      echo "::error::SENS_NATIVE_STANDALONE_FAILED path=$file status=$status" >&2
      mark_file_failed
    fi
  fi
  if timeout 45s "$binary" --t5m-pair "$file" "$pair" \
       >"$dir/paired.stdout" 2>"$dir/paired.stderr"; then
    paired_sha="$(sha256sum "$dir/paired.stdout" | cut -d ' ' -f 1)"
    if (( standalone_ok )); then
      if cmp -s "$dir/standalone.stdout" "$dir/paired.stdout"; then
        echo "SENS_NATIVE_EXECUTION_PASS path=$file physical_sha256=$physical_sha output_sha256=$paired_sha semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
      else
        echo "::error::SENS_NATIVE_RESULT_MISMATCH path=$file physical=$pair" >&2
        mark_file_failed
      fi
    else
      echo "SENS_NATIVE_PAIRED_D24_PASS path=$file physical_sha256=$physical_sha paired_sha256=$paired_sha standalone=NOT_SUPPORTED semantic=NOT_CERTIFIED release=NOT_CERTIFIED"
    fi
  else
    status=$?
    cat "$dir/paired.stderr" >&2
    echo "::error::SENS_NATIVE_PAIRED_FAILED path=$file physical=$pair status=$status" >&2
    mark_file_failed
  fi
done < "$manifest"
echo "SENS_NATIVE_SUMMARY files_checked=$checked_files files_failed=$failed_files standalone_d24_only=$physical_d24_only release=NOT_CERTIFIED"
if (( failed_files > 0 )); then
  exit 2
fi
