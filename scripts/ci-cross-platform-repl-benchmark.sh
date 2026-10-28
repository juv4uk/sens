#!/usr/bin/env bash
# CI glue only: time the SAME SENS-owned D5 positive witness through real REPL.
# No host-language implementation of D5, no semantic fallback, no cross-CPU ranking.
set -euo pipefail
cd "$(dirname "$0")/.."
cli="${1:-target/release/sens}"
outdir="${2:-.ci-metrics}"
if [[ ! -x "$cli" ]]; then
  printf 'REPL_BENCH_BLOCKED reason=missing-sens-cli path=%s\n' "$cli" >&2
  exit 1
fi
mkdir -p "$outdir"
outdir="$(cd "$outdir" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

# The workload is already proven by scripts/prove-repl-semantic-corpus.sh.
# This script measures only time and verifies the emitted existing D1 verdict.
witness=tests/semantic/d5-arithmetic-native-t5m-law.lisp
if [[ ! -f "$witness" || -L "$witness" ]]; then
  printf 'REPL_BENCH_BLOCKED missing-fixture=%s\n' "$witness" >&2
  exit 1
fi

{
  printf 'head_sha\t%s\n' "$(git rev-parse HEAD)"
  printf 'runner_os\t%s\n' "${RUNNER_OS:-unknown}"
  printf 'runner_arch\t%s\n' "${RUNNER_ARCH:-unknown}"
  printf 'machine\t%s\n' "$(uname -a)"
  printf 'rustc\t%s\n' "$(rustc --version)"
  printf 'zig\t%s\n' "$(zig version)"
  printf 'scope\tSENS_REPL_D5_existing_positive_witness\n'
} > "$outdir/environment.tsv"

# Single load = cold REPL per process, batch = 10 loads inside one process.
# Both are measured over 11 launches; samples are not normalized across CPUs.
for workload in single-load batch-10-loads; do
  request="$tmp/$workload.input"
  : > "$request"
  loads=1
  if [[ "$workload" == batch-10-loads ]]; then loads=10; fi
  for ((n=1; n<=loads; n++)); do
    printf ':завантажити %s\n' "$witness" >> "$request"
  done
  samples="$outdir/$workload.tsv"
  printf 'sample\telapsed_seconds\n' > "$samples"
  for iteration in {1..11}; do
    TIMEFORMAT='%3R'
    if ! measured="$( { time "$cli" --surface=укр < "$request" > "$tmp/reply.out" 2> "$tmp/reply.err"; } 2>&1 )"; then
      printf 'REPL_BENCH_FAIL case=%s iteration=%s reason=executor\n' "$workload" "$iteration" >&2
      cat "$tmp/reply.err" >&2
      exit 1
    fi
    if [[ -s "$tmp/reply.err" ]] || grep -Eq 'Помилка (REPL/T5M|завантаження|виконання)' "$tmp/reply.out"; then
      printf 'REPL_BENCH_FAIL case=%s iteration=%s reason=unexpected-error\n' "$workload" "$iteration" >&2
      cat "$tmp/reply.err" "$tmp/reply.out" >&2
      exit 1
    fi
    if ! awk -v marker="Завантажено: $witness" '
       { sub(/\r$/, "", $0); sub(/[ \t]+$/, "", $0) }
       index($0,marker) { found=1; last=""; next }
       found && NF { last=$0 }
       END { exit !(found && (last=="ТАК" || last=="sens[укр]> ТАК")) }
    ' "$tmp/reply.out"; then
      printf 'REPL_BENCH_FAIL case=%s iteration=%s reason=wrong-SENS-D1\n' "$workload" "$iteration" >&2
      cat "$tmp/reply.out" >&2
      exit 1
    fi
    elapsed="$(printf '%s\n' "$measured" | tr -d '\r' | tail -n 1)"
    if ! printf '%s\n' "$elapsed" | grep -Eq '^[0-9]+([.][0-9]+)?$'; then
      printf 'REPL_BENCH_FAIL case=%s iteration=%s reason=missing-elapsed value=%s\n' "$workload" "$iteration" "$elapsed" >&2
      exit 1
    fi
    printf '%s\t%s\n' "$iteration" "$elapsed" >> "$samples"
  done
  median="$(tail -n +2 "$samples" | cut -f2 | sort -n | sed -n '6p')"
  p90="$(tail -n +2 "$samples" | cut -f2 | sort -n | sed -n '10p')"
  printf 'SENS_REPL_BENCH workload=%s samples=11 p50_s=%s p90_s=%s target=D5 platform=%s/%s sha=%s\n' \
    "$workload" "$median" "$p90" "${RUNNER_OS:-unknown}" "${RUNNER_ARCH:-unknown}" "$(git rev-parse HEAD)"
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    printf '%s: 11 samples; p50=%s s, p90=%s s (not cross-platform normalized)\n' \
      "$workload" "$median" "$p90" >> "$GITHUB_STEP_SUMMARY"
  fi
done
