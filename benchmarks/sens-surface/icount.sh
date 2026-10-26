#!/bin/sh
# Legacy entry point delegates to the canonical native SENS/Zig physical judge.
# No alternate-language oracle, generated receipt, or benchmark sidecar.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
export SENS_BIN="${SENS_BIN:-$ROOT/target/debug/sens}"
export SENS_TRIT_BIN="${SENS_TRIT_BIN:-$ROOT/target/debug/sens-trit}"
exec bash "$ROOT/benchmarks/contest-uk/judge.sh" "$@"
