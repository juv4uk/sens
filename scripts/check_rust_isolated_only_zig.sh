#!/usr/bin/env bash
# Ізоляцію Rust↔SENS перевіряє ЛИШЕ Zig (власник, 23.10.2026).
# Rust не має власного шляху до SENS: єдина точка входу/виходу — стерильний
# Zig-коридор. Перевірка живе в Zig-тесті transport_abi.zig, не в Python.
set -euo pipefail
zig test -lc research/zig-codecs/tests.zig
printf '%s\n' RUST_ISOLATED_ONLY_ZIG_OK
