#!/usr/bin/env bash
# Manual Rust-free C host of the existing Zig ABI v2; no extra CI workflow.
set -Eeuo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$root"

# C stdout proves transport fixtures ONLY, not build/link provenance.
# Rust symbol-name evidence is NOT full static dependency closure.
rust_marker() {
    local pattern='(__rust_|rust_eh_personality|rust_alloc|rust_dealloc|rust_realloc|rust_alloc_zeroed|\.rlib($|[^[:alnum:]_])|librust[^[:space:]]*|lib(std|core|alloc)-[[:xdigit:]]+\.(a|so|dylib)|(^|[[:space:]])_?RN[[:alnum:]_]+)'
    [[ "$1" =~ $pattern ]]
}
if [[ "${1:-}" == "--self-test" && "$#" -eq 1 ]]; then
    if rust_marker $'libc.so.6\nlibstdc++.so.6\ncrt1.o'; then
        echo 'SENS_C_CORRIDOR_SELFTEST_FAIL layer=dependency case=normal-libraries' >&2
        exit 1
    fi
    for injected in '__rust_alloc' 'rust_eh_personality' 'libcore-a1b2c3d4.rlib' '_RNvCs0_foo' $'0000000000000100 T rust_eh_personality' $'0000000000000200 T _RNvCs0_foo'; do
        if ! rust_marker "$injected"; then
            echo "SENS_C_CORRIDOR_SELFTEST_FAIL layer=dependency missed=$injected" >&2
            exit 1
        fi
    done
    if rust_marker $'0000000000000030 T sens_zig_codec_abi_version\n0000000000000040 T sens_zig_t5_encode_be3'; then
        echo 'SENS_C_CORRIDOR_SELFTEST_FAIL layer=dependency case=zig-ffi-symbols' >&2
        exit 1
    fi
    echo 'SENS_C_CORRIDOR_SELFTEST_PASS positive=2 negative=6 full_static_dependency_closure=NOT_VERIFIED'
    exit 0
fi
if [[ "$#" -ne 0 ]]; then
    echo 'usage: verify.sh [--self-test]' >&2
    exit 2
fi

zig_bin="${ZIG:-zig}"
cc_bin="${CC:-cc}"
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
if [[ -n "${SENS_C_HOST_OUT_DIR:-}" ]]; then
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
# The C witness checks real transport calls; it cannot inspect its own link.
# Do not repeat its legacy hardcoded rust_linked=false as independent proof.
witness="$("$out/sens-c-host-corridor")"
if [[ "$witness" != *'SENS_C_CORRIDOR_PASS'* ]]; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=transport missing=witness_pass' >&2
    exit 2
fi
if [[ "$witness" == *'rust_linked=false'* ]]; then
    witness=${witness//rust_linked=false/rust_dependency_proof=NOT_TESTED}
fi
printf '%s\n' "$witness"
# Scan the ACTUAL compiled ELF and archive, not only the written C source.
for tool in readelf ar nm sha256sum; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "SENS_C_CORRIDOR_UNVERIFIED layer=dependency missing=$tool" >&2
        exit 2
    fi
done
exe="$out/sens-c-host-corridor"
archive="$out/libsens_zig_transport.a"
if [[ ! -f "$exe" || -L "$exe" || ! -f "$archive" || -L "$archive" ]]; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency missing_or_symlink_artifact' >&2
    exit 2
fi
if ! dynamic="$(readelf --wide --dynamic "$exe")"; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency tool=readelf' >&2
    exit 2
fi
if [[ "$dynamic" != *'Dynamic section'* && "$dynamic" != *'There is no dynamic section'* ]]; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency malformed_elf_dynamic' >&2
    exit 2
fi
if ! members="$(ar t "$archive")" || [[ -z "$members" ]]; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency missing_archive_members' >&2
    exit 2
fi
if ! undefined="$(nm -u "$exe")"; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency tool=nm' >&2
    exit 2
fi
# Defined globals matter too: static Rust symbols need no unresolved imports.
if ! defined_exe="$(nm -g --defined-only "$exe")"; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency tool=nm-defined-executable' >&2
    exit 2
fi
if ! defined_archive="$(nm -g --defined-only "$archive")"; then
    echo 'SENS_C_CORRIDOR_UNVERIFIED layer=dependency tool=nm-defined-archive' >&2
    exit 2
fi
# Demand real FFI symbols in the linked Zig archive, not merely declarations.
for symbol in sens_zig_codec_abi_version sens_zig_t5_encode_be3 sens_zig_t5_decode_be3; do
    if [[ "$defined_archive" != *"$symbol"* ]]; then
        echo "SENS_C_CORRIDOR_UNVERIFIED layer=dependency missing_zig_export=$symbol" >&2
        exit 2
    fi
done
if rust_marker "$dynamic" || rust_marker "$members" || rust_marker "$undefined" ||
    rust_marker "$defined_exe" || rust_marker "$defined_archive"; then
    echo 'SENS_C_CORRIDOR_BLOCKED layer=dependency rust_marker_found' >&2
    exit 1
fi
echo "SENS_C_CORRIDOR_RECEIPT zig=$actual c_host_binary_sha256=$(sha256sum "$exe" | cut -d ' ' -f 1) zig_archive_sha256=$(sha256sum "$archive" | cut -d ' ' -f 1) dependencies=INSPECTED_NO_RUST_MARKERS exported_zig_ffi=VERIFIED nm_defined=INSPECTED full_static_dependency_closure=NOT_VERIFIED semantic_verdict=NOT_TESTED"
