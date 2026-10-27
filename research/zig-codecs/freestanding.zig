//! A freestanding physical transport boundary: Zig 0.16.
//! All buffers/lengths explicit; no OS or libc, no semantic domain assignment.
//! The F3C rank tables also consume stack: an object build is not MCU stack proof.
const std = @import("std");
const t5 = @import("t5/t5.zig");
const f3c = @import("f3c/f3c.zig");
const fields = @import("transport/fields.zig");

/// 0 = physically valid; positive = bytes written; -1 = invalid input;
/// -2 = caller buffer too small; -3 = F3C cannot save space.
pub export fn sens_zig_free_t5_validate(src: [*]const u8, len: u32) i32 {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    t5.validatePhysical(src[0..@as(usize, len)]) catch return -1;
    return 0;
}

pub export fn sens_zig_free_t5_encode_be3(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
) i32 {
    if (len == 0 or len % 3 != 0) return -1;
    const count = t5.encodeTripletsInto(
        dst[0..@as(usize, capacity)], src[0..@as(usize, len)],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1;
    return @intCast(count); // Physical output <= 4 MiB.
}

/// Inverse physical T5 ingress for a Rust-free C/MCU host. All storage is
/// caller-owned: no heap, no semantic lookup, no D10 callable admission.
/// Returns exact BE3 byte count, -1 on malformed/aliased input, -2 if small.
pub export fn sens_zig_free_t5_decode_be3(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
) i32 {
    if (len == 0 or len > t5.MAX_PHYSICAL_BYTES) return -1;
    const written = t5.decodeTripletsInto(
        dst[0..@as(usize, capacity)], src[0..@as(usize, len)],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1;
    return @intCast(written); // Bounded by T5 physical max and exact BE3.
}

fn overlaps(a_ptr: usize, a_len: usize, b_ptr: usize, b_len: usize) bool {
    if (a_len == 0 or b_len == 0) return false;
    return if (a_ptr <= b_ptr) b_ptr - a_ptr < a_len
        else a_ptr - b_ptr < b_len;
}

fn scratchValid(src: []const u8, dst: []u8, arena: []u8) bool {
    if (arena.len < f3c.ABI_SCRATCH_BYTES) return false;
    const work = arena[0..f3c.ABI_SCRATCH_BYTES];
    return !overlaps(@intFromPtr(src.ptr), src.len, @intFromPtr(work.ptr), work.len) and
        !overlaps(@intFromPtr(dst.ptr), dst.len, @intFromPtr(work.ptr), work.len);
}

/// Explicit carrier pack. F3C stages output before writing, supporting
/// in-place input/output. Scratch must not overlap either logical buffer.
pub export fn sens_zig_free_f3c_pack(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
    scratch: [*]u8, scratch_capacity: u32,
) i32 {
    if (len == 0 or len > f3c.MAX_TINY_T5_BYTES) return -1;
    const input = src[0..@as(usize, len)];
    const output = dst[0..@as(usize, capacity)];
    const work = scratch[0..@as(usize, scratch_capacity)];
    if (work.len < f3c.ABI_SCRATCH_BYTES) return -2;
    if (!scratchValid(input, output, work)) return -1;
    const count = (f3c.encodeInto(
        input, output, work[0..f3c.ABI_SCRATCH_BYTES],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1) orelse return -3;
    return @intCast(count);
}

/// Strict F3C decode; malformed .senc never falls back to .sens T5.
pub export fn sens_zig_free_f3c_unpack(
    src: [*]const u8, len: u32, dst: [*]u8, capacity: u32,
    scratch: [*]u8, scratch_capacity: u32,
) i32 {
    if (len < 2 or len >= f3c.MAX_TINY_T5_BYTES) return -1;
    const input = src[0..@as(usize, len)];
    const output = dst[0..@as(usize, capacity)];
    const work = scratch[0..@as(usize, scratch_capacity)];
    if (work.len < f3c.ABI_SCRATCH_BYTES) return -2;
    if (!scratchValid(input, output, work)) return -1;
    const count = f3c.decodeInto(
        input, output, work[0..f3c.ABI_SCRATCH_BYTES],
    ) catch |e| return if (e == error.BufferTooSmall) -2 else -1;
    return @intCast(count);
}

/// CRC32 detects physical corruption, never authenticates program meaning.
pub export fn sens_zig_free_crc32(
    src: [*]const u8, len: u32, output: *u32,
) i32 {
    if (len > t5.MAX_PHYSICAL_BYTES) return -1;
    // CRC is a physical receipt, never permission to mutate source bytes.
    // The host owns both ranges; reject a result pointer inside the input.
    if (overlaps(@intFromPtr(src), @as(usize, len),
        @intFromPtr(output), @sizeOf(u32))) return -1;
    output.* = fields.crc32(src[0..@as(usize, len)]);
    return 0;
}


/// Source-level physical memory components, NOT full stack usage.
/// FixedBufferAllocator scratch is caller-owned; suffix counts are immutable
/// data. Nested calls, spills, compiler helpers and other local arrays remain
/// unmeasured and must be assessed on actual hardware.
pub const F3C_SCRATCH_BYTES: usize = f3c.ABI_SCRATCH_BYTES;
pub const F3C_RANK_TABLE_BYTES: usize = 0;
pub const F3C_SUFFIX_ROM_BYTES: usize = f3c.SUFFIX_ROM_BYTES;

