#!/usr/bin/env sh
# Native SENS physical benchmark entry point.
# The former EN-text/SENS-text/FASL comparison is obsolete after M8:
# admitted human surfaces lower to canonical SENS calls.
# This wrapper delegates execution and judging; it creates no receipts or JSON.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
export SENS_BIN="${SENS_BIN:-$ROOT/target/debug/sens}"
export SENS_TRIT_BIN="${SENS_TRIT_BIN:-$ROOT/target/debug/sens-trit}"
exec bash "$ROOT/benchmarks/contest-uk/judge.sh" "$@"
