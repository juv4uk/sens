#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
OUT="${2:-/tmp/sens-binary-out}"
rm -rf "$OUT"
mkdir -p "$OUT"
cargo run -q -p sens --example binary_master_export -- "$ROOT" "$OUT"
