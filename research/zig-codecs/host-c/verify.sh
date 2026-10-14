#!/usr/bin/env bash
# Manual Rust-free C host of the existing Zig ABI v2; no extra CI workflow.
set -Eeuo pipefail
root="$(cd "$(dirname "\${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$root"
zig_bin="\${ZIG:-zig}"
cc_bin="\${CC:-cc}"
pinned="$(cat .zig-version)"
if ! command -v "$zig_bin" >/dev/null 2>&1; then
    echo "SENS_C_CORRIDOR_UNVERIFIED layer=toolchain missing=zig" >&2
    exit 2
fi
if ! command -v "$cc_bin" >/dev/null 2>&1; then
    echo "SENS_C_CORRIDOR_UNVERIFIED layer=toolchain missing=cc" >&2
    exit 2
fi
actual="$("$zig_bin" version)"
if [[ "$actual" != "$pinned" ]]; then
    echo "SENS_C_CORRIDOR_UNVERIFIED layer=toolchain zig_pin=$pinned actual=$actual" >&2
    exit 2
fi
if [[ -n "\${SENS_C_HOST_OUT_DIR:-}" ]]; then
    mkdir -p "$SENS_C_HOST_OUT_DIR"
    out="$(cd "$SENS_C_HOST_OUT_DIR" && pwd)"
else
    out="$(mktemp -d -t sens-c-host-XXXXXXXX)"
    trap 'rm -rf "$out"' EXIT
fi
"$zig_bin" build-lib research/zig-codecs/transport_abi.zig \
    -O ReleaseFast -lc -fPIC \
    "-femit-bin=$out/libsens_zig_transport.a"
"$cc_bin" -std=c11 -Wall -Wextra -Werror -pedantic -O2 \
    research/zig-codecs/host-c/corridor_v2.c \
    "$out/libsens_zig_transport.a" -lm -ldl -pthread \
    -o "$out/sens-c-host-corridor"
"$out/sens-c-host-corridor"
echo "SENS_C_CORRIDOR_RECEIPT zig=$actual c_host_binary_sha256=$(sha256sum "$out/sens-c-host-corridor" | cut -d ' ' -f 1) semantic_verdict=NOT_TESTED"
