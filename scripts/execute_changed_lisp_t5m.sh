#!/usr/bin/env bash
# Людський .lisp спершу пакує Zig/T5M; виконується тільки фізичний .sens.
# Відсутність допущеного механізму лишається явним боргом, не GO.
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
failed_files=0
checked_files=0
while IFS= read -r file || [[ -n "$file" ]]; do
  [[ -n "$file" ]] || continue
  checked_files=$((checked_files + 1))
  if [[ "$file" != *.lisp || ! -f "$file" || -L "$file" ]]; then
    echo "::error::T5M_CHANGED_SOURCE_INVALID path=$file" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  id="$(printf '%s' "$file" | sha256sum | cut -c1-16)"
  dir="$outdir/$id"
  mkdir -p "$dir"
  report="$dir/migration.json"
  echo "T5M_CHANGED_SOURCE path=$file"
  code=0
  python3 scripts/migrate-three-pass.py "$file" \
    --out "$dir" --report "$report" --codec t5m --source-surface укр \
    >"$dir/migration.log" 2>&1 || code=$?
  if [[ ! -s "$report" ]]; then
    cat "$dir/migration.log" >&2
    echo "::error::T5M_MIGRATION_NO_REPORT path=$file status=$code" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  report_status=0
  outcome="$(python3 - "$report" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
summary = report["summary"]
for row in report["files"]:
    if row["status"] == "blocked":
        print("T5M_MIGRATION_DEBT path=" + row["path"] + " reason=" + row["reason"], file=sys.stderr)
print(summary["files_written"], summary["files_blocked"], summary["files_not_program"])
PY
)" || report_status=$?
  if (( report_status != 0 )); then
    echo "::error::T5M_MIGRATION_REPORT_INVALID path=$file status=$report_status" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  read -r written blocked not_program <<< "$outcome"
  if (( code > 2 )); then
    echo "::error::T5M_MIGRATION_INTERNAL_FAILURE path=$file status=$code" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  if (( blocked > 0 )); then
    echo "::error::T5M_MIGRATION_UNPROVEN path=$file blocked=$blocked semantic=NOT_CERTIFIED" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  if (( not_program > 0 )); then
    echo "T5M_NOT_PROGRAM path=$file"
    continue
  fi
  if (( code != 0 || written != 1 )); then
    echo "::error::T5M_MIGRATION_INCONSISTENT path=$file status=$code written=$written" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  pair="$dir/$(basename "$file" .lisp).sens"
  if [[ ! -s "$pair" ]]; then
    echo "::error::T5M_MINTED_PAIR_MISSING path=$file" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  committed="$(dirname "$file")/$(basename "$file" .lisp).sens"
  staged_view="${pair%.sens}"
  committed_view="${committed%.sens}"
  if [[ ! -f "$staged_view" || -L "$staged_view" ]]; then
    echo "::error::T5M_MINTED_VIEW_MISSING source=$file expected=$staged_view" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
  if [[ -f "$committed" ]]; then
    if ! cmp -s "$pair" "$committed"; then
      echo "::error::T5M_COMMITTED_PAIR_DRIFT source=$file companion=$committed" >&2
      failed_files=$((failed_files + 1))
      continue
    fi
    if [[ ! -f "$committed_view" || -L "$committed_view" ]]; then
      echo "::error::T5M_COMMITTED_VIEW_MISSING source=$file expected=$committed_view" >&2
      failed_files=$((failed_files + 1))
      continue
    fi
    if ! cmp -s "$staged_view" "$committed_view"; then
      echo "::error::T5M_COMMITTED_VIEW_DRIFT source=$file companion=$committed_view" >&2
      failed_files=$((failed_files + 1))
      continue
    fi
  else
    echo "::notice::T5M_PAIR_NOT_COMMITTED path=$file release=NOT_CERTIFIED"
  fi
  stdout="$dir/runtime.stdout"
  stderr="$dir/runtime.stderr"
  if timeout 45s "$binary" "$pair" >"$stdout" 2>"$stderr"; then
    result_sha="$(sha256sum "$stdout" | cut -d ' ' -f 1)"
    echo "T5M_FILE_EXECUTION PASS path=$file pair=$pair result_sha256=$result_sha semantic=NOT_CERTIFIED"
  else
    status=$?
    # Фізичний T5M зберігає W24 без втрат. Проте W24 сам по собі
    # не позначає домен: старий BinarySourceWord приймає лише W1–W9.
    # Це НЕ дає права приписати байтам D24 та оголосити physical PASS.
    # Для саме цієї відомої межі пробуємо незалежний чинний маршрут:
    # український Lisp → доменна проєкція → Zig T5M → SENS.
    if grep -Fq 'точні ширини слів [24]' "$stderr" &&
       grep -Fq 'адаптер BinarySourceWord приймає лише W1–W9' "$stderr"; then
      echo "::warning::T5M_PHYSICAL_D24_NOT_EXECUTED source=$file pair=$pair status=$status release=NOT_CERTIFIED"
      if timeout 45s "$binary" --t5m-file "$file" >"$stdout" 2>"$stderr"; then
        result_sha="$(sha256sum "$stdout" | cut -d ' ' -f 1)"
        echo "T5M_DOMAIN_SOURCE_RUNTIME_PASS source=$file physical=NOT_SUPPORTED result_sha256=$result_sha release=NOT_CERTIFIED"
        continue
      fi
      status=$?
      sed 's/^/T5M source stderr: /' "$stderr" >&2
      echo "::error::T5M_DOMAIN_SOURCE_RUNTIME_FAIL source=$file status=$status" >&2
      failed_files=$((failed_files + 1))
      continue
    fi
    sed 's/^/T5M stderr: /' "$stderr" >&2
    echo "::error::T5M_FILE_EXECUTION_FAIL path=$file pair=$pair status=$status" >&2
    failed_files=$((failed_files + 1))
    continue
  fi
done < "$manifest"
printf 'T5M_CHANGED_SUMMARY files_checked=%s files_failed=%s release=NOT_CERTIFIED\n' "$checked_files" "$failed_files"
if (( failed_files > 0 )); then
  exit 2
fi
