#!/usr/bin/env bash
# Manual H1: real Zig ABI v2 -> Rust-free C D1-D3 subset evaluator.
# Does NOT establish complete cross-host semantic parity. No auto workflow.
set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$root"
zig_bin="${ZIG:-zig}"
cc_bin="${CC:-cc}"
pinned="$(cat .zig-version)"
if ! command -v "$cc_bin" >/dev/null 2>&1; then
  echo "C_D3_SUBSET_UNVERIFIED layer=toolchain missing=cc" >&2
  exit 2
fi
"$cc_bin" -std=c11 -Wall -Wextra -Werror -pedantic -O2 -fsyntax-only \
  research/zig-codecs/host-c/d3_subset.c
if ! command -v "$zig_bin" >/dev/null 2>&1; then
  echo "C_D3_SUBSET_UNVERIFIED layer=toolchain missing=zig C_syntax=PASS" >&2
  exit 2
fi
actual="$("$zig_bin" version)"
if [[ "$actual" != "$pinned" ]]; then
  echo "C_D3_SUBSET_UNVERIFIED layer=toolchain zig_pin=$pinned actual=$actual" >&2
  exit 2
fi
if [[ -n "${SENS_C_HOST_OUT_DIR:-}" ]]; then
  mkdir -p "$SENS_C_HOST_OUT_DIR"
  out="$(cd "$SENS_C_HOST_OUT_DIR" && pwd)"
else
  out="$(mktemp -d -t sens-c-d3-XXXXXXXX)"
  trap 'rm -rf "$out"' EXIT
fi
"$zig_bin" build-lib research/zig-codecs/transport_abi.zig \
  -O ReleaseFast -lc -fPIC "-femit-bin=$out/libsens_zig_transport.a"
"$cc_bin" -std=c11 -Wall -Wextra -Werror -pedantic -O2 \
  research/zig-codecs/host-c/d3_subset.c \
  "$out/libsens_zig_transport.a" -lm -ldl -pthread \
  -o "$out/sens-c-host-d3"
for name in retired-d3-cond retired-d3-eq retired-quote-inert-d3; do
  for variant in law mutant; do
    fixture="tests/semantic/$name-$variant.bits"
    printf 'C_D3_SUBSET_FIXTURE path=%s sha256=' "$fixture"
    sha256sum "$fixture" | cut -d ' ' -f 1
  done
done
"$out/sens-c-host-d3"
if command -v ldd >/dev/null 2>&1; then
  if ldd "$out/sens-c-host-d3" | grep -i rust; then
    echo "C_D3_SUBSET_FAIL layer=dependency category=RUST_IN_C_LINK" >&2
    exit 1
  fi
fi
printf 'C_D3_SUBSET_RECEIPT zig=%s c_binary_sha256=' "$actual"
sha256sum "$out/sens-c-host-d3" | cut -d ' ' -f 1
echo 'C_D3_SUBSET_H1_SOURCE_READY runtime_subset=D1-D3 cross_host_parity=NOT_VERIFIED semantic_authority=SENS'
