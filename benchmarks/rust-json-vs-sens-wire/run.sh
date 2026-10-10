#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="${1:-/tmp/rust-json-vs-sens-wire}"
N="${N_MESSAGES:-1000}"
CACHE_ROUNDS="${CACHEGRIND_ROUNDS:-20}"
WALL_ROUNDS="${WALL_CLOCK_ROUNDS:-200}"
mkdir -p "$OUT"

command -v cargo >/dev/null
command -v python3 >/dev/null
command -v valgrind >/dev/null || {
  echo "BLOCKED: valgrind/Cachegrind is required; install it before running this benchmark" >&2
  exit 2
}

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
  valgrind --tool=cachegrind --cache-sim=no \
    --cachegrind-out-file="$OUT/cachegrind-$form.out" \
    "$BENCH" "$form" "$input" "$CACHE_ROUNDS" \
    > "$OUT/$form.cachegrind.stdout" 2> "$OUT/$form.cachegrind.stderr"
  grep -E "I[[:space:]]+refs:" "$OUT/$form.cachegrind.stderr" \
    > "$OUT/$form.irefs.txt" || true
  "$BENCH" "$form" "$input" "$WALL_ROUNDS" > "$OUT/$form.wall.txt"
done

{
  echo "# Rust serde_json vs SENS wire — decode only"
  echo
  echo "- Corpus: N=$N; deterministic seed=1; records identical by construction."
  echo "- Cachegrind rounds: $CACHE_ROUNDS; wall-clock rounds: $WALL_ROUNDS."
  echo "- Timed loops exclude corpus file I/O and process startup."
  echo "- Scope is transport decoding only; this is not a whole-language speed claim."
  echo
  for form in wire json; do
    echo "## $form"
    echo
    echo '~~~text'
    cat "$OUT/$form.cachegrind.stdout"
    cat "$OUT/$form.irefs.txt" || true
    cat "$OUT/$form.wall.txt"
    echo '~~~'
    echo
  done
} > "$OUT/summary.md"

cat "$OUT/summary.md"
