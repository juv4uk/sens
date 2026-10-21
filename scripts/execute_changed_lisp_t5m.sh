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
while IFS= read -r file || [[ -n "$file" ]]; do
  [[ -n "$file" ]] || continue
  if [[ "$file" != *.lisp || ! -f "$file" || -L "$file" ]]; then
    echo "::error::T5M_CHANGED_SOURCE_INVALID path=$file" >&2
    exit 2
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
    exit 1
  fi
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
)"
  read -r written blocked not_program <<< "$outcome"
  if (( code > 2 )); then
    echo "::error::T5M_MIGRATION_INTERNAL_FAILURE path=$file status=$code" >&2
    exit "$code"
  fi
  if (( blocked > 0 )); then
    echo "::warning::T5M_MIGRATION_UNPROVEN path=$file blocked=$blocked semantic=NOT_CERTIFIED"
    continue
  fi
  if (( not_program > 0 )); then
    echo "T5M_NOT_PROGRAM path=$file"
    continue
  fi
  if (( code != 0 || written != 1 )); then
    echo "::error::T5M_MIGRATION_INCONSISTENT path=$file status=$code written=$written" >&2
    exit 1
  fi
  pair="$dir/$(basename "$file" .lisp).sens"
  if [[ ! -s "$pair" ]]; then
    echo "::error::T5M_MINTED_PAIR_MISSING path=$file" >&2
    exit 1
  fi
  committed="$(dirname "$file")/$(basename "$file" .lisp).sens"
  if [[ -f "$committed" ]]; then
    if ! cmp -s "$pair" "$committed"; then
      echo "::error::T5M_COMMITTED_PAIR_DRIFT source=$file companion=$committed" >&2
      exit 1
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
    sed 's/^/T5M stderr: /' "$stderr" >&2
    echo "::error::T5M_FILE_EXECUTION_FAIL path=$file pair=$pair status=$status" >&2
    exit "$status"
  fi
done < "$manifest"
