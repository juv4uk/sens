#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="${1:-/tmp/rust-packed-visible}"
mkdir -p "$OUT"



CARGO_BUILD_JOBS=2 cargo run --locked --profile ci-meta -p sens \
  --example packed_vs_visible_bench -- --samples 15 \
  > "$OUT/raw.tsv" 2> "$OUT/run.stderr"

samples="$(grep -c '^RUST_PACKED_VISIBLE_SAMPLE[[:space:]]' "$OUT/raw.tsv" || true)"
summaries="$(grep -c '^RUST_PACKED_VISIBLE_SUMMARY[[:space:]]' "$OUT/raw.tsv" || true)"
[[ "$samples" -eq 75 && "$summaries" -eq 5 ]] || {
  echo "RUST_PACKED_VISIBLE_EVIDENCE_INVALID samples=$samples expected=75 summaries=$summaries expected_summaries=5" >&2
  cat "$OUT/run.stderr" >&2
  exit 2
}
if grep -q '^{' "$OUT/raw.tsv"; then
  echo "RUST_PACKED_VISIBLE_EVIDENCE_INVALID unexpected JSON-formatted output" >&2
  exit 2
fi

{
  echo "# Rust exact-width visible/packed ingestion — measured output"
  echo
  echo 'The benchmark executes the Rust mechanism after a verified SENS runtime build in the parent workflow.'
  echo 'The raw TSV contains all alternating samples and per-case quantiles.'
  echo
  echo '## Raw measurements'
  echo
  echo '```text'
  cat "$OUT/raw.tsv"
  echo '```'
} > "$OUT/summary.md"

cat "$OUT/summary.md"
