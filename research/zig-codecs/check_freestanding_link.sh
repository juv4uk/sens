#!/usr/bin/env bash
# Manual Zig 0.16 freestanding ABI link audit; NOT a SENS semantic oracle.
# Usage: bash research/zig-codecs/check_freestanding_link.sh [output-directory]
# Requires: Zig 0.16.0, readelf, nm, size, sha256sum, awk, grep.
set -Eeuo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo"
zig_bin="${ZIG:-zig}"
version="$("$zig_bin" version)"
if [[ "$version" != "0.16.0" ]]; then
    echo "ZIG_FREESTANDING_FAIL phase=toolchain expected=0.16.0 actual=$version" >&2
    exit 1
fi
for tool in readelf nm size sha256sum awk grep; do
    command -v "$tool" >/dev/null || {
        echo "ZIG_FREESTANDING_FAIL phase=toolchain missing=$tool" >&2
        exit 1
    }
done
if [[ $# -gt 1 ]]; then
    echo "Usage: bash research/zig-codecs/check_freestanding_link.sh [output-directory]" >&2
    exit 2
fi
output="${1:-$(mktemp -d -t sens-zig-freestanding.XXXXXXXX)}"
mkdir -p "$output"
output="$(cd "$output" && pwd)"
echo "ZIG_FREESTANDING_BEGIN zig=$version git_sha=$(git rev-parse HEAD 2>/dev/null || echo UNKNOWN) output=$output"
echo "F3C_MEMORY_COMPONENTS scratch_bytes=8192 rank_table_stack_bytes=0 suffix_rom_bytes=4000 total_stack_bound=NOT_MEASURED"
echo "semantic_authority=SENS transport_only=true esp32_s3_cpu=NOT_TESTED"

# The same manual command verifies exact physical byte behavior before linking.
# Zig tests prove transport mechanics only; semantic authority remains SENS.
for suite in research/zig-codecs/tests.zig research/zig-codecs/freestanding.zig; do
    label="$(basename "$suite" .zig)"
    if ! "$zig_bin" test "$suite" -lc > "$output/$label-host-tests.log" 2>&1; then
        cat "$output/$label-host-tests.log" >&2
        echo "ZIG_FREESTANDING_FAIL phase=host-physical-tests suite=$suite" >&2
        exit 1
    fi
    echo "ZIG_FREESTANDING_HOST_TEST_PASS suite=$suite"
done

names=(
    sens_zig_free_t5_validate
    sens_zig_free_t5_encode_be3
    sens_zig_free_t5_decode_be3
    sens_zig_free_f3c_pack
    sens_zig_free_f3c_unpack
    sens_zig_free_crc32
)

# A no-entry freestanding ELF is a library-like LINK proof, not bootable firmware.
for target in x86_64-freestanding thumb-freestanding-eabi; do
    obj="$output/sens-zig-$target.o"
    elf="$output/sens-zig-$target.elf"
    echo "ZIG_FREESTANDING_TARGET_BEGIN target=$target"
    if ! "$zig_bin" build-obj research/zig-codecs/freestanding.zig \
        -target "$target" -O ReleaseSmall -fno-unwind-tables \
        -femit-bin="$obj" > "$output/$target-compile.log" 2>&1; then
        cat "$output/$target-compile.log" >&2
        echo "ZIG_FREESTANDING_FAIL target=$target phase=compile log=$output/$target-compile.log" >&2
        exit 1
    fi

    # Without link roots LLD discards all code, producing a hollow ELF.
    force=()
    for symbol in "${names[@]}"; do force+=(--force_undefined "$symbol"); done
    if ! "$zig_bin" build-exe research/zig-codecs/freestanding.zig \
        -target "$target" -O ReleaseSmall -fno-entry -fno-strip \
        -fcompiler-rt -fno-unwind-tables \
        "${force[@]}" -femit-bin="$elf" > "$output/$target-link.log" 2>&1; then
        cat "$output/$target-link.log" >&2
        echo "ZIG_FREESTANDING_FAIL target=$target phase=link log=$output/$target-link.log" >&2
        exit 1
    fi

    readelf -h "$elf" > "$output/$target-elf-header.txt"
    readelf -W -S "$elf" > "$output/$target-sections.txt"
    readelf -W -l "$elf" > "$output/$target-program-headers.txt"
    readelf -W -r "$elf" > "$output/$target-relocations.txt"
    size -A "$elf" > "$output/$target-size.txt"
    nm -u "$elf" > "$output/$target-undefined.txt"
    nm -g --defined-only "$elf" > "$output/$target-global-symbols.txt"

    if ! grep -Eq '[[:space:]]\.text[[:space:]]+PROGBITS' "$output/$target-sections.txt"; then
        echo "ZIG_FREESTANDING_FAIL target=$target phase=sections reason=no_real_text" >&2
        exit 1
    fi
    if [[ -s "$output/$target-undefined.txt" ]]; then
        cat "$output/$target-undefined.txt" >&2
        echo "ZIG_FREESTANDING_FAIL target=$target phase=link reason=unresolved_symbols" >&2
        exit 1
    fi
    if grep -Eq '[[:space:]](INTERP|DYNAMIC)[[:space:]]' "$output/$target-program-headers.txt"; then
        echo "ZIG_FREESTANDING_FAIL target=$target phase=link reason=dynamic_loader" >&2
        exit 1
    fi
    for symbol in "${names[@]}"; do
        if ! awk -v name="$symbol" '$2 == "T" && $3 == name { found=1 } END { exit !found }' \
            "$output/$target-global-symbols.txt"; then
            echo "ZIG_FREESTANDING_FAIL target=$target phase=exports missing=$symbol" >&2
            exit 1
        fi
    done
    echo "ZIG_FREESTANDING_LINK_PASS target=$target ABI_exports=${#names[@]} entry=NONE"
    sha256sum "$obj" "$elf" | tee "$output/$target-SHA256.txt"
    grep -E 'Class:|Machine:|Type:' "$output/$target-elf-header.txt"
    grep -E '^\.text[[:space:]]' "$output/$target-size.txt"
done

# Hosted x86_64 observation of Zig's *actual linked freestanding object*.
# This C-only probe adds pthread/libc measurement scaffolding, not to Zig.
# Canary checks count the touched region for four golden calls; they do not
# establish a worst-case frame bound, guaranteed stack pointer usage or
# an ESP32-S3/Xtensa firmware budget.
if [[ "$(uname -m)" == "x86_64" ]]; then
    command -v cc >/dev/null || {
        echo "ZIG_F3C_STACK_SAMPLE_FAIL phase=toolchain missing=cc" >&2
        exit 1
    }
    probe="$output/sens-zig-f3c-host-stack-probe"
    cc -std=c11 -Wall -Wextra -Werror -O2 -fno-omit-frame-pointer \
        -no-pie -pthread research/zig-codecs/transport/f3c_stack_probe.c \
        "$output/sens-zig-x86_64-freestanding.o" -o "$probe"
    sha256sum "$probe" | tee "$output/f3c-stack-host-probe-SHA256.txt"
    "$probe" | tee "$output/f3c-stack-host-samples.txt"
else
    echo "ZIG_F3C_STACK_SAMPLE_UNSUPPORTED reason=host_not_x86_64 host=$(uname -m)"
fi

echo "ZIG_FREESTANDING_BOTH_TARGETS_PASS semantic_authority=SENS actual_ESP32_S3=NOT_TESTED stack_bound=NOT_MEASURED"
