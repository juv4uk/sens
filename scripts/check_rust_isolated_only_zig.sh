#!/usr/bin/env bash
# Ізоляцію Rust↔SENS перевіряє ЛИШЕ Zig (власник, 23.10.2026).
# Rust не має власного шляху до SENS: єдина точка входу/виходу — стерильний
# Zig-коридор. Фізичні перевірки — transport_abi.zig, перевірка обходу READ —
# zig_transport_root.zig; обидва набори виконуються Zig.
set -euo pipefail
zig test -O ReleaseSafe -lc research/zig-codecs/tests.zig
# Окремий source-route доказ для колишнього прямого stdin у ядрі READ.
zig test -lc zig_transport_root.zig --test-filter 'Rust core READ'
zig test -lc zig_transport_root.zig --test-filter 'Rust build domain projections'
zig test -lc zig_transport_root.zig --test-filter 'Rust bootstrap slot checks'
printf '%s\n' RUST_ISOLATED_ONLY_ZIG_OK
