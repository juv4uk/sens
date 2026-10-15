#!/usr/bin/env bash
# Run the canonical T5 migration across N workers (#1675 / #4455 / #5141).
#
# The single-file driver is scripts/migrate-t5-batch.py. This wrapper splits the
# explicit paths into N disjoint chunks, runs one worker per chunk concurrently,
# then merges the per-worker JSON reports. Nothing new is decided here: the
# canonical driver and the sterile Zig corridor stay the only path to a
# published .sens (--write requires --zig-codec; see
# scripts/check_migration_zig_only_path.py).
#
# Usage:
#   scripts/migrate-parallel.sh --jobs 5 --out OUT --report REPORT [--write] [--zig-codec] PATH...
#   scripts/migrate-parallel.sh --jobs 5 --out /tmp/t5out --report /tmp/lib.json lib/
#
# Exit: 0 iff every worker reported success; the merged report is written to --report.

set -euo pipefail

JOBS=5
OUT=""
REPORT=""
declare -a EXTRA=()
declare -a PATHS=()

while (( $# )); do
  case "$1" in
    --jobs) JOBS="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --report) REPORT="$2"; shift 2 ;;
    --write|--zig-codec) EXTRA+=("$1"); shift ;;
    --source-era) EXTRA+=("$1" "$2"); shift 2 ;;
    --) shift; PATHS+=("$@"); break ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) PATHS+=("$1"); shift ;;
  esac
done

if [[ -z "$OUT" || -z "$REPORT" || ${#PATHS[@]} -eq 0 ]]; then
  echo "usage: $0 --jobs N --out OUT --report REPORT [--write] [--zig-codec] PATH..." >&2
  exit 2
fi
if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then echo "--jobs must be >= 1" >&2; exit 2; fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Expand directories to their .lisp files (deterministic order), keep files as-is.
declare -a FILES=()
for p in "${PATHS[@]}"; do
  if [[ -d "$p" ]]; then
    while IFS= read -r f; do FILES+=("$f"); done < <(find "$p" -type f -name '*.lisp' | LC_ALL=C sort)
  else
    FILES+=("$p")
  fi
done
total=${#FILES[@]}
if (( total == 0 )); then echo "no .lisp sources under: ${PATHS[*]}" >&2; exit 2; fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/sens-migrate-XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

echo "migrate-parallel: ${total} file(s) across ${JOBS} worker(s)"

declare -a PIDS=()
declare -a WORKER_REPORTS=()
rc=0
for (( w = 0; w < JOBS; w++ )); do
  # Round-robin the files so each worker's chunk is disjoint and balanced.
  chunk=()
  for (( i = w; i < total; i += JOBS )); do chunk+=("${FILES[$i]}"); done
  (( ${#chunk[@]} == 0 )) && continue
  wreport="$WORK/report.$w.json"
  WORKER_REPORTS+=("$wreport")
  python3 scripts/migrate-t5-batch.py --out "$OUT" --report "$wreport" \
    "${EXTRA[@]}" "${chunk[@]}" >"$WORK/worker.$w.log" 2>&1 &
  PIDS+=("$!")
done

for pid in "${PIDS[@]}"; do wait "$pid" || rc=1; done
for (( w = 0; w < ${#WORKER_REPORTS[@]}; w++ )); do
  echo "--- worker $w ---"; cat "$WORK/worker.$w.log"
done

# Merge the per-worker reports into one, preserving the canonical schema.
python3 - "$REPORT" "${WORKER_REPORTS[@]}" <<'PY'
import json, sys
out_path, *reports = sys.argv[1:]
merged = None
files = []
summary = {"files_seen": 0, "files_admitted": 0, "files_written": 0,
           "files_would_write": 0, "files_blocked": 0}
for rp in reports:
    try:
        with open(rp, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        continue
    if merged is None:
        merged = {k: v for k, v in d.items() if k not in ("files", "summary")}
    files.extend(d.get("files", []))
    for k in summary:
        summary[k] += d.get("summary", {}).get(k, 0)
files.sort(key=lambda e: e.get("path", ""))
merged = merged or {"schema": "sens-t5-safe-batch/v1"}
merged["mode"] = "parallel-merged"
merged["files"] = files
merged["summary"] = summary
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(merged, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print("merged summary:", json.dumps(summary, ensure_ascii=False))
PY

exit $rc
