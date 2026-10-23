#!/usr/bin/env bash
# Run the canonical T5 migration across N workers (#1675 / #4455 / #5141).
#
# The single-file driver is scripts/migrate-t5m-batch.py. This wrapper splits the
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

# Merged JSON is written AFTER the workers. Unlike their temporary receipts,
# its caller-provided --report path could overwrite a Zig-certified .sens!
# Resolve links and '..' before dispatch; no worker is allowed to start if
# the final report would live anywhere inside the physical output mirror.
python3 - "$OUT" "$REPORT" <<'PY'
import sys
from pathlib import Path

try:
    mirror = Path(sys.argv[1]).resolve(strict=False)
    receipt = Path(sys.argv[2]).resolve(strict=False)
except (OSError, RuntimeError) as exc:
    raise SystemExit(
        f"ZIG_PARALLEL_BLOCKED test_id=invalid-report-path "
        f"layer=transport reason={type(exc).__name__}:{exc}"
    ) from exc
if receipt == mirror or receipt.is_relative_to(mirror):
    raise SystemExit(
        f"ZIG_PARALLEL_BLOCKED test_id=report-output-collision "
        f"layer=transport report={receipt} mirror={mirror}"
    )
PY

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

# A spelling is not a filesystem identity: .. and symlinks can refer to
# one input and cause TWO workers to race to publish the same .sens.
# Resolve every actual path before launching any worker. Preserve original
# spelling in per-worker reports (the canonical driver owns those labels).
python3 - "$REPORT" "${FILES[@]}" <<'PY'
import sys
from pathlib import Path

try:
    receipt = Path(sys.argv[1]).resolve(strict=False)
    receipt_stat = receipt.stat()
    receipt_inode = (receipt_stat.st_dev, receipt_stat.st_ino)
except FileNotFoundError:
    receipt_inode = None
except (OSError, RuntimeError) as exc:
    raise SystemExit(
        f"ZIG_PARALLEL_BLOCKED test_id=invalid-report-path "
        f"layer=transport reason={type(exc).__name__}:{exc}"
    ) from exc

seen = {}
seen_inodes = {}
for raw in sys.argv[2:]:
    try:
        source = Path(raw).resolve(strict=True)
        if not source.is_file():
            raise ValueError("source is not a regular file")
        if source.suffix != ".lisp":
            raise ValueError("source is not a .lisp file")
        # Different hardlink names have distinct realpaths but identical
        # physical inode identities. Never dispatch one file twice.
        info = source.stat()
        inode = (info.st_dev, info.st_ino)
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(
            f"ZIG_PARALLEL_BLOCKED test_id=invalid-source layer=transport "
            f"path={raw} reason={type(exc).__name__}:{exc}"
        ) from exc
    # A JSON receipt must never replace the exact SENS source it audits.
    # .resolve() catches aliases/..; st_dev+st_ino also catches hardlinks.
    if source == receipt or (receipt_inode is not None and inode == receipt_inode):
        raise SystemExit(
            f"ZIG_PARALLEL_BLOCKED test_id=report-source-collision "
            f"layer=transport report={receipt} source={source} "
            f"same_inode={info.st_dev}:{info.st_ino}"
        )
    if source in seen or inode in seen_inodes:
        first = seen.get(source, seen_inodes.get(inode))
        raise SystemExit(
            f"ZIG_PARALLEL_BLOCKED test_id=duplicate-source layer=transport "
            f"path={raw} first={first} same_physical_source={source} "
            f"same_inode={info.st_dev}:{info.st_ino}"
        )
    seen[source] = raw
    seen_inodes[inode] = raw
PY
if (( JOBS > total )); then JOBS=$total; fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/sens-migrate-XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

echo "migrate-parallel: ${total} file(s) across ${JOBS} worker(s)"

declare -a PIDS=()
declare -a WORKER_REPORTS=()
declare -a WORKER_ARGS=()
rc=0
for (( w = 0; w < JOBS; w++ )); do
  # Round-robin the files so each worker's chunk is disjoint and balanced.
  chunk=()
  for (( i = w; i < total; i += JOBS )); do chunk+=("${FILES[$i]}"); done
  (( ${#chunk[@]} == 0 )) && continue
  wreport="$WORK/report.$w.json"
  WORKER_REPORTS+=("$wreport")
  winputs="$WORK/inputs.$w.paths"
  printf '%s\0' "${chunk[@]}" >"$winputs"
  WORKER_ARGS+=("$wreport" "$winputs")
  python3 scripts/migrate-t5m-batch.py --out "$OUT" --report "$wreport" \
    "${EXTRA[@]}" "${chunk[@]}" >"$WORK/worker.$w.log" 2>&1 &
  PIDS+=("$!")
done

for pid in "${PIDS[@]}"; do wait "$pid" || rc=1; done
for (( w = 0; w < ${#WORKER_REPORTS[@]}; w++ )); do
  echo "--- worker $w ---"; cat "$WORK/worker.$w.log"
done

# Merge the per-worker reports into one, preserving the canonical schema.
python3 - "$REPORT" "$rc" "${WORKER_ARGS[@]}" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
worker_rc = int(sys.argv[2])
pairs = sys.argv[3:]
if not pairs or len(pairs) % 2:
    raise SystemExit("ZIG_PARALLEL_REPORT_BLOCKED test_id=empty-worker-list layer=transport")

keys = ("files_seen", "files_admitted", "files_written",
        "files_would_write", "files_blocked")
summary = dict.fromkeys(keys, 0)
all_paths = set()
files = []
baseline = None
for report_path, input_path in zip(pairs[::2], pairs[1::2]):
    try:
        raw = Path(input_path).read_bytes().split(b"\0")
        if raw[-1] != b"":
            raise ValueError("unterminated input manifest")
        expected = [Path(p.decode("utf-8")).as_posix() for p in raw[:-1]]
        with Path(report_path).open(encoding="utf-8") as stream:
            report = json.load(stream)
        if not isinstance(report, dict) or report.get("schema") != "sens-t5-safe-batch/v1":
            raise ValueError("invalid report schema")
        entries = report.get("files")
        counts = report.get("summary")
        if not isinstance(entries, list) or not isinstance(counts, dict):
            raise ValueError("missing worker rows/summary")
        if not expected or len(set(expected)) != len(expected):
            raise ValueError("invalid worker inputs")
        got = []
        statuses = {"blocked": 0, "would-write": 0, "written": 0}
        for row in entries:
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                raise ValueError("invalid worker row")
            if row.get("status") not in statuses:
                raise ValueError("unknown worker status")
            statuses[row["status"]] += 1
            got.append(row["path"])
        if sorted(got) != sorted(expected) or set(got) & all_paths:
            raise ValueError("worker report paths are missing/duplicate/foreign")
        actual = {"files_seen": len(entries),
                  "files_admitted": statuses["would-write"] + statuses["written"],
                  "files_written": statuses["written"],
                  "files_would_write": statuses["would-write"],
                  "files_blocked": statuses["blocked"]}
        for key in keys:
            if type(counts.get(key)) is not int or counts[key] != actual[key]:
                raise ValueError(f"invalid summary {key}")
            summary[key] += counts[key]
        metadata = {k: report.get(k) for k in ("root", "output_mirror", "authority", "mode")}
        if baseline is None:
            baseline = metadata
        elif metadata != baseline:
            raise ValueError("inconsistent worker source/output/authority")
        all_paths.update(got)
        files.extend(entries)
    except (OSError, ValueError, UnicodeError, TypeError, KeyError) as err:
        raise SystemExit(
            f"ZIG_PARALLEL_REPORT_BLOCKED test_id=invalid-worker-report "
            f"layer=transport report={report_path} reason={err}"
        ) from err

files.sort(key=lambda e: e["path"])
status = "BLOCKED" if worker_rc or summary["files_blocked"] else "COMPLETE"
merged = {"schema": "sens-t5-safe-batch/v1", **(baseline or {}),
          "mode": "parallel-merged", "status": status,
          "files": files, "summary": summary}
out.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
               encoding="utf-8")
print("merged summary:", json.dumps(summary, ensure_ascii=False), "status:", status)
if status != "COMPLETE":
    raise SystemExit("ZIG_PARALLEL_REPORT_BLOCKED test_id=worker-rejected layer=transport")
PY

exit $rc
