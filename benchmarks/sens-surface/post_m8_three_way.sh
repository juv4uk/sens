#!/bin/sh
# #1665: post-M8 three-way instruction benchmark.
#
# Compares the same emitted workload in three transport/source forms:
#   en-text    — English human surface, text parse;
#   sens-text  — exact eight-bit SENS reader spelling, text parse;
#   sens-fasl  — exact SENS binary FASL, one-byte function transport.
#
# Usage:
#   sh post_m8_three_way.sh CI_BENCH_BINARY [OUT_DIR] [REPS] [REPEAT_N]
#
# The ci_bench binary is the existing crates/sens/examples/ci_bench.rs built
# from the exact commit being measured. This script changes no evaluator law.
set -eu

BIN=${1:?path to release ci_bench example is required}
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$HERE/../.." && pwd)
OUT=${2:-"$HERE/results/$(date -u +%Y%m%d)-post-m8"}
REPS=${3:-3}
REPEAT_N=${4:-5}
PROGRAMS="$OUT/programs"
RAW="$OUT/instructions.tsv"
ENV="$OUT/environment.tsv"
REPORT="$OUT/report.md"
SUMMARY="$OUT/summary.json"

case "$REPS:$REPEAT_N" in
  *[!0-9:]*|0:*|*:0) echo "REPS and REPEAT_N must be positive integers" >&2; exit 2 ;;
esac

command -v valgrind >/dev/null 2>&1 || {
  echo "valgrind is required for #1665" >&2
  exit 2
}
command -v python3 >/dev/null 2>&1 || {
  echo "python3 is required for #1665" >&2
  exit 2
}

mkdir -p "$PROGRAMS"

# Emit one semantic workload in EN text and exact-SENS text.
python3 "$HERE/run.py" --sens "$BIN" --emit "$PROGRAMS" --small --forms en,sens

paramsof() {
  awk -F '\t' -v n="$1" '$1 == n { print $2; found = 1; exit }
    END { if (!found) print "-" }' "$PROGRAMS/params.tsv"
}

measure() {
  value=$(
    valgrind --tool=cachegrind --cache-sim=no --cachegrind-out-file=/dev/null \
      "$BIN" "$PROGRAMS" "$@" 2>&1 >/dev/null |
      sed -n 's/.*I *refs: *//p' | tr -d ','
  )
  case "$value" in
    ''|*[!0-9]*)
      echo "failed to read Cachegrind I refs for: $*" >&2
      exit 3
      ;;
  esac
  printf '%s' "$value"
}

# ci_bench treats every non-"sens" form as text. Create an explicit alias
# whose bytes are identical to the exact-SENS text emitted above. "sens"
# itself remains the binary-FASL path and is encoded before measurement.
for expected in "$PROGRAMS"/*.expected; do
  name=$(basename "$expected" .expected)
  cp "$PROGRAMS/$name-sens.setup.lisp" "$PROGRAMS/$name-sens-text.setup.lisp"
  cp "$PROGRAMS/$name-sens.call.lisp" "$PROGRAMS/$name-sens-text.call.lisp"

  "$BIN" "$PROGRAMS" "$name" sens encode

  # Correctness is a prerequisite, never inferred from timing.
  "$BIN" "$PROGRAMS" "$name" en full
  "$BIN" "$PROGRAMS" "$name" sens-text full
  "$BIN" "$PROGRAMS" "$name" sens full
done

# Exact-run environment/provenance. Values are evidence only.
sanitize() { printf '%s' "$1" | tr '\t\n\r' '   '; }
fact() { printf '%s\t%s\n' "$1" "$(sanitize "$2")" >> "$ENV"; }
: > "$ENV"
fact key value
fact date_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fact git_sha "$(git -C "$REPO" rev-parse HEAD)"
fact git_dirty "$(test -n "$(git -C "$REPO" status --porcelain --untracked-files=no)" && echo yes || echo no)"
fact binary "$(realpath "$BIN")"
fact binary_sha256 "$(sha256sum "$BIN" | awk '{print $1}')"
fact valgrind "$(valgrind --version | head -n1)"
fact rustc "$(rustc --version 2>/dev/null || echo unavailable)"
fact guix "$(guix --version 2>/dev/null | head -n1 || echo unavailable)"
fact channels_sha256 "$(sha256sum "$REPO/channels.scm" | awk '{print $1}')"
fact manifest_sha256 "$(sha256sum "$REPO/manifest.scm" | awk '{print $1}')"
fact bench_manifest_sha256 "$(sha256sum "$HERE/manifest.scm" | awk '{print $1}')"
fact kernel "$(uname -srmo)"
fact cpu "$(awk -F: '/^model name/ { sub(/^[ \t]+/, "", $2); print $2; exit }' /proc/cpuinfo 2>/dev/null || echo unknown)"
fact nproc "$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo unknown)"
fact loadavg "$(cat /proc/loadavg 2>/dev/null || echo unknown)"
fact reps "$REPS"
fact repeat_n "$REPEAT_N"

printf 'workload\tparams\ttransport\tmode\trep\trepeat_n\tinstructions\n' > "$RAW"

rep=1
while [ "$rep" -le "$REPS" ]; do
  printf 'empty\t-\t-\tempty\t%s\t-\t%s\n' "$rep" "$(measure empty -)" >> "$RAW"
  rep=$((rep + 1))
done

for expected in "$PROGRAMS"/*.expected; do
  name=$(basename "$expected" .expected)
  params=$(paramsof "$name")

  for transport in en-text sens-text sens-fasl; do
    case "$transport" in
      en-text) form=en ;;
      sens-text) form=sens-text ;;
      sens-fasl) form=sens ;;
    esac

    rep=1
    while [ "$rep" -le "$REPS" ]; do
      for mode in load ready full; do
        printf '%s\t%s\t%s\t%s\t%s\t-\t%s\n' \
          "$name" "$params" "$transport" "$mode" "$rep" \
          "$(measure "$name" "$form" "$mode")" >> "$RAW"
      done
      printf '%s\t%s\t%s\trepeat\t%s\t%s\t%s\n' \
        "$name" "$params" "$transport" "$rep" "$REPEAT_N" \
        "$(measure "$name" "$form" repeat "$REPEAT_N")" >> "$RAW"
      rep=$((rep + 1))
    done
  done
done

python3 "$HERE/post_m8_three_way.py" "$RAW" \
  --environment "$ENV" --markdown-out "$REPORT" --json-out "$SUMMARY"

cat "$REPORT"
printf '\nraw: %s\nenvironment: %s\nsummary: %s\n' "$RAW" "$ENV" "$SUMMARY"
