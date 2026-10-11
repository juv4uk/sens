#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="${1:-/tmp/rust-json-vs-sens-wire}"
N="${N_MESSAGES:-1000}"
CACHE_ROUNDS="${CACHEGRIND_ROUNDS:-20}"
WALL_ROUNDS="${WALL_CLOCK_ROUNDS:-200}"
WALL_REPS="${WALL_CLOCK_REPS:-7}"
mkdir -p "$OUT"

command -v cargo >/dev/null
command -v python3 >/dev/null
command -v valgrind >/dev/null || {
  echo "BLOCKED: valgrind/Cachegrind is required; install it before running this benchmark" >&2
  exit 2
}
[[ "$N" -gt 0 && "$CACHE_ROUNDS" -gt 0 && "$WALL_ROUNDS" -gt 0 && "$WALL_REPS" -ge 3 ]] || {
  echo "N and rounds must be positive; WALL_CLOCK_REPS must be at least 3" >&2
  exit 2
}

cargo --version > "$OUT/cargo-version.txt"
rustc --version > "$OUT/rustc-version.txt"
valgrind --version > "$OUT/valgrind-version.txt"
uname -a > "$OUT/host.txt"
cargo build --profile ci-meta -p sens --example agent_bench --example transport_decode_bench

python3 - "$OUT" "$N" <<'PY'
import importlib.util
import json
import random
import sys
from pathlib import Path

out = Path(sys.argv[1])
n = int(sys.argv[2])
spec = importlib.util.spec_from_file_location(
    "agent_messages", "benchmarks/agent-messages/run.py"
)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load deterministic agent-message corpus generator")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
rng = random.Random(1)
messages = [mod.gen_message(rng, i) for i in range(n)]
mod.write_records(
    out / "messages-sens-text.bin",
    [mod.lisp(m, mod.SENS).encode() for m in messages],
)
mod.write_records(
    out / "messages-json.bin",
    [json.dumps(mod.json_ast(m), separators=(",", ":")).encode() for m in messages],
)
PY

target/ci-meta/examples/agent_bench encode wire \
  "$OUT/messages-sens-text.bin" "$OUT/messages-sens-wire.bin"

BENCH="target/ci-meta/examples/transport_decode_bench"
for form in wire json; do
  if [[ "$form" == wire ]]; then
    input="$OUT/messages-sens-wire.bin"
  else
    input="$OUT/messages-json.bin"
  fi
  # Cachegrind counts the whole process, including file/record setup and warm-up.
  valgrind --tool=cachegrind --cache-sim=no \
    --cachegrind-out-file="$OUT/cachegrind-$form.out" \
    "$BENCH" "$form" "$input" "$CACHE_ROUNDS" \
    > "$OUT/$form.cachegrind.stdout" 2> "$OUT/$form.cachegrind.stderr"
  grep -E "I[[:space:]]+refs:" "$OUT/$form.cachegrind.stderr" \
    > "$OUT/$form.irefs.txt"
done

printf 'cycle,order_index,form,messages,elapsed_ns,ns_per_message,msg_per_sec\n' > "$OUT/wall-samples.csv"
for ((cycle=1; cycle<=WALL_REPS; cycle++)); do
  # Alternate ABBA and BAAB to reduce order/drift bias.
  if (( cycle % 2 == 1 )); then
    forms=(wire json json wire)
  else
    forms=(json wire wire json)
  fi
  order_index=0
  for form in "${forms[@]}"; do
    if [[ "$form" == wire ]]; then
      input="$OUT/messages-sens-wire.bin"
    else
      input="$OUT/messages-json.bin"
    fi
    sample="$OUT/wall-${cycle}-${order_index}-${form}.txt"
    "$BENCH" "$form" "$input" "$WALL_ROUNDS" > "$sample"
    python3 - "$sample" "$OUT/wall-samples.csv" "$cycle" "$order_index" <<'PY'
import csv
import re
import sys
from pathlib import Path

sample = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
match = re.fullmatch(
    r"form=(wire|json) messages=(\d+) elapsed_ns=(\d+) "
    r"ns_per_message=([0-9.]+) msg_per_sec=([0-9.]+)",
    sample,
)
if match is None:
    raise SystemExit(f"unrecognized benchmark output: {sample}")
with Path(sys.argv[2]).open("a", newline="", encoding="utf-8") as handle:
    csv.writer(handle).writerow([sys.argv[3], sys.argv[4], *match.groups()])
PY
    order_index=$((order_index + 1))
  done
done

python3 - "$OUT" "$N" "$CACHE_ROUNDS" "$WALL_ROUNDS" "$WALL_REPS" <<'PY'
import csv
import hashlib
import json
import math
import platform
import re
import statistics
import sys
from pathlib import Path

out = Path(sys.argv[1])
n, cache_rounds, wall_rounds, wall_reps = map(int, sys.argv[2:6])

def read_irefs(form):
    raw = (out / f"{form}.irefs.txt").read_text(encoding="utf-8")
    match = re.search(r"I\s+refs:\s*([\d,]+)", raw)
    if match is None:
        raise SystemExit(f"Cachegrind instruction-reference count missing for {form}")
    return int(match.group(1).replace(",", ""))

samples = {"wire": [], "json": []}
with (out / "wall-samples.csv").open(newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        samples[row["form"]].append({
            "cycle": int(row["cycle"]),
            "order_index": int(row["order_index"]),
            "messages": int(row["messages"]),
            "elapsed_ns": int(row["elapsed_ns"]),
            "ns_per_message": float(row["ns_per_message"]),
            "msg_per_sec": float(row["msg_per_sec"]),
        })

def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return values[low]
    return values[low] + (values[high] - values[low]) * (position - low)

summary = {
    "schema": "sens-rust-wire-vs-json-decode/v1",
    "scope": "decode-only wall-clock; Cachegrind I refs are whole-process context",
    "corpus": {
        "messages": n,
        "seed": 1,
        "sha256": {
            name: hashlib.sha256((out / name).read_bytes()).hexdigest()
            for name in ("messages-sens-text.bin", "messages-sens-wire.bin", "messages-json.bin")
        },
    },
    "cachegrind": {
        "rounds": cache_rounds,
        "instruction_references_scope": "whole process including startup, file and record parsing, one warm-up and measured rounds",
        "instruction_references": {form: read_irefs(form) for form in ("wire", "json")},
    },
    "wall_clock": {
        "rounds_per_sample": wall_rounds,
        "abba_baab_cycles": wall_reps,
        "sample_order": "wire,json,json,wire on odd cycles; json,wire,wire,json on even cycles",
        "raw_samples": samples,
        "summary": {
            form: {
                "sample_count": len(values),
                "median_ns_per_message": statistics.median(x["ns_per_message"] for x in values),
                "p95_ns_per_message": percentile([x["ns_per_message"] for x in values], 0.95),
                "median_messages_per_second": statistics.median(x["msg_per_sec"] for x in values),
            } for form, values in samples.items()
        },
    },
    "environment": {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cargo": (out / "cargo-version.txt").read_text().strip(),
        "rustc": (out / "rustc-version.txt").read_text().strip(),
        "valgrind": (out / "valgrind-version.txt").read_text().strip(),
        "host": (out / "host.txt").read_text().strip(),
    },
}
(out / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

def fmt(value):
    return f"{value:,.3f}"

lines = [
    "# Rust serde_json vs SENS wire — decode-only hosted benchmark",
    "",
    f"- Corpus: N={n}; deterministic seed=1.",
    f"- Cachegrind: {cache_rounds} rounds; counts cover the whole process, including setup and warm-up.",
    f"- Wall clock: {wall_rounds} rounds per sample, {wall_reps} alternating ABBA/BAAB cycles.",
    "- Timed wall-clock loops exclude file I/O, record parsing and process startup.",
    "- Transport decoding only; no whole-language or universal SENS-vs-JSON claim.",
    "",
    "| Decoder | Cachegrind I refs / process* | Wall samples | Median ns/message | p95 ns/message | Median messages/s |",
    "|---|---:|---:|---:|---:|---:|",
]
for form in ("wire", "json"):
    s = summary["wall_clock"]["summary"][form]
    lines.append(
        f"| {form} | {summary['cachegrind']['instruction_references'][form]:,} "
        f"| {s['sample_count']} | {fmt(s['median_ns_per_message'])} "
        f"| {fmt(s['p95_ns_per_message'])} | {fmt(s['median_messages_per_second'])} |"
    )
lines.extend([
    "",
    "* Cachegrind includes process startup, input reads, record splitting, one warm-up and measured rounds; do not treat these as isolated decoder instruction counts.",
    "",
    "Corpus hashes and raw paired samples are recorded in results.json and wall-samples.csv; the artifact retains corpus files, outputs, Cachegrind raw files, and toolchain provenance.",
    "",
])
(out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
print((out / "summary.md").read_text(encoding="utf-8"))
PY
